"""Kin's store: SQLite rows plus a private file store for originals (docs/05-architecture.md, Data).

The store only persists. Policy decisions live in `kin.retrieve`; nothing here returns records
by itself to anyone. Originals are written under `<data>/originals/` and are Admin-only.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from kin.members import Roster

SCHEMA = """
CREATE TABLE IF NOT EXISTS members (
  id TEXT PRIMARY KEY, telegram_id TEXT UNIQUE, name TEXT NOT NULL, role TEXT NOT NULL,
  language TEXT NOT NULL, dm_opened INTEGER NOT NULL DEFAULT 0, expires_at TEXT);
CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY, kind TEXT NOT NULL, title TEXT NOT NULL, storage_ref TEXT,
  categories TEXT NOT NULL, uploaded_by TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS excerpts (
  id TEXT PRIMARY KEY, document_id TEXT NOT NULL, text TEXT NOT NULL, category TEXT NOT NULL,
  audience TEXT NOT NULL, approved_by TEXT NOT NULL, approved_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS records (
  id TEXT NOT NULL, version INTEGER NOT NULL, category TEXT NOT NULL, status TEXT NOT NULL,
  fields TEXT NOT NULL, document_id TEXT, excerpt_ids TEXT NOT NULL DEFAULT '[]',
  created_by TEXT NOT NULL, assignee TEXT, created_at TEXT NOT NULL, superseded_by TEXT,
  PRIMARY KEY (id, version));
CREATE INDEX IF NOT EXISTS records_category ON records (category, status);
CREATE TABLE IF NOT EXISTS events (
  id TEXT PRIMARY KEY, record_id TEXT NOT NULL, record_version INTEGER NOT NULL,
  assignee TEXT NOT NULL, due_at TEXT NOT NULL, tz TEXT NOT NULL, status TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS grants (
  id INTEGER PRIMARY KEY AUTOINCREMENT, record_id TEXT NOT NULL, record_version INTEGER NOT NULL,
  grantee TEXT NOT NULL, scope TEXT NOT NULL, approved_by TEXT NOT NULL, at TEXT NOT NULL,
  consumed_at TEXT, revoked_at TEXT);
CREATE TABLE IF NOT EXISTS audit (
  id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL, principal TEXT NOT NULL,
  chat_type TEXT, chat_id TEXT, action TEXT NOT NULL, query TEXT, records TEXT NOT NULL,
  fields TEXT NOT NULL, decision TEXT NOT NULL, destination TEXT, delivery TEXT);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


class Store:
    def __init__(self, db_path: Path, originals_dir: Path):
        self.db_path = Path(db_path)
        self.originals_dir = Path(originals_dir)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.originals_dir.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.executescript(SCHEMA)

    @contextmanager
    def _db(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # --- members -------------------------------------------------------------------------
    def sync_roster(self, roster: Roster) -> None:
        """Make the members table match the roster (roles and IDs come only from the roster)."""
        with self._db() as db:
            keep = [m.id for m in roster.members]
            db.execute(f"DELETE FROM members WHERE id NOT IN ({','.join('?' * len(keep))})", keep)
            for m in roster.members:
                db.execute(
                    "INSERT INTO members (id, telegram_id, name, role, language) VALUES (?,?,?,?,?)"
                    " ON CONFLICT(id) DO UPDATE SET telegram_id=excluded.telegram_id,"
                    " name=excluded.name, role=excluded.role, language=excluded.language",
                    (m.id, m.telegram_id, m.name, m.role, m.language),
                )

    def member_roles(self) -> list[str]:
        with self._db() as db:
            return [r["role"] for r in db.execute("SELECT role FROM members")]

    def mark_dm_opened(self, member_id: str) -> None:
        with self._db() as db:
            db.execute("UPDATE members SET dm_opened=1 WHERE id=?", (member_id,))

    def admin(self) -> sqlite3.Row | None:
        with self._db() as db:
            return db.execute("SELECT * FROM members WHERE role='admin'").fetchone()

    def members(self) -> list[sqlite3.Row]:
        with self._db() as db:
            return list(db.execute("SELECT * FROM members ORDER BY role, name"))

    # --- documents and excerpts ----------------------------------------------------------
    def add_document(
        self,
        *,
        kind: str,
        title: str,
        categories: list[str],
        uploaded_by: str,
        content: bytes | None = None,
        suffix: str = "",
        doc_id: str | None = None,
    ) -> str:
        doc_id = doc_id or new_id("doc")
        ref = None
        if content is not None:
            path = self.originals_dir / f"{doc_id}{suffix}"
            path.write_bytes(content)
            ref = path.name
        with self._db() as db:
            db.execute(
                "INSERT INTO documents VALUES (?,?,?,?,?,?,?)",
                (doc_id, kind, title, ref, json.dumps(categories), uploaded_by, now()),
            )
        return doc_id

    def document(self, doc_id: str) -> sqlite3.Row | None:
        with self._db() as db:
            return db.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()

    def add_excerpt(
        self,
        *,
        document_id: str,
        text: str,
        category: str,
        audience: list[str],
        approved_by: str,
        excerpt_id: str | None = None,
    ) -> str:
        excerpt_id = excerpt_id or new_id("ex")
        with self._db() as db:
            db.execute(
                "INSERT INTO excerpts VALUES (?,?,?,?,?,?,?)",
                (excerpt_id, document_id, text, category, json.dumps(audience), approved_by, now()),
            )
        return excerpt_id

    def excerpts(self, ids: list[str]) -> list[sqlite3.Row]:
        if not ids:
            return []
        with self._db() as db:
            return list(
                db.execute(f"SELECT * FROM excerpts WHERE id IN ({','.join('?' * len(ids))})", ids)
            )

    # --- records -------------------------------------------------------------------------
    def add_record(
        self,
        *,
        category: str,
        fields: dict[str, Any],
        created_by: str,
        status: str = "active",
        document_id: str | None = None,
        excerpt_ids: list[str] | None = None,
        assignee: str | None = None,
        record_id: str | None = None,
    ) -> str:
        record_id = record_id or new_id("rec")
        with self._db() as db:
            row = db.execute(
                "SELECT MAX(version) AS v FROM records WHERE id=?", (record_id,)
            ).fetchone()
            version = (row["v"] or 0) + 1
            db.execute(
                "INSERT INTO records VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    record_id,
                    version,
                    category,
                    status,
                    json.dumps(fields, ensure_ascii=False),
                    document_id,
                    json.dumps(excerpt_ids or []),
                    created_by,
                    assignee,
                    now(),
                    None,
                ),
            )
        return record_id

    def active_records(self, categories: list[str]) -> list[sqlite3.Row]:
        """Latest active version of records in the given categories only (SQL-filtered)."""
        if not categories:
            return []
        marks = ",".join("?" * len(categories))
        with self._db() as db:
            return list(
                db.execute(
                    f"SELECT r.* FROM records r WHERE r.status='active' AND r.category IN ({marks})"
                    " AND r.version=(SELECT MAX(version) FROM records WHERE id=r.id)"
                    " ORDER BY r.created_at",
                    categories,
                )
            )

    # --- audit ---------------------------------------------------------------------------
    def audit(
        self,
        *,
        principal: str,
        action: str,
        decision: str,
        chat_type: str | None = None,
        chat_id: str | None = None,
        query: str | None = None,
        records: list[str] | None = None,
        fields: dict[str, list[str]] | None = None,
        destination: str | None = None,
        delivery: str | None = None,
    ) -> None:
        with self._db() as db:
            db.execute(
                "INSERT INTO audit (at, principal, chat_type, chat_id, action, query, records,"
                " fields, decision, destination, delivery) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    now(),
                    principal,
                    chat_type,
                    chat_id,
                    action,
                    query,
                    json.dumps(records or []),
                    json.dumps(fields or {}),
                    decision,
                    destination,
                    delivery,
                ),
            )

    def audit_for(self, ref: str, limit: int = 20) -> list[sqlite3.Row]:
        """Audit entries that exposed a record (or any record of a document)."""
        with self._db() as db:
            ids = [ref] + [
                r["id"]
                for r in db.execute("SELECT DISTINCT id FROM records WHERE document_id=?", (ref,))
            ]
            clauses = " OR ".join("records LIKE ?" for _ in ids)
            return list(
                db.execute(
                    f"SELECT * FROM audit WHERE {clauses} ORDER BY id DESC LIMIT ?",
                    [f'%"{i}"%' for i in ids] + [limit],
                )
            )
