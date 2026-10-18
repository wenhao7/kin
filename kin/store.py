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
  assignee TEXT NOT NULL, kind TEXT NOT NULL, at TEXT NOT NULL, until TEXT, tz TEXT NOT NULL,
  label TEXT NOT NULL, status TEXT NOT NULL, last_sent TEXT);
CREATE TABLE IF NOT EXISTS drafts (
  id TEXT PRIMARY KEY, admin TEXT NOT NULL, document_ids TEXT NOT NULL, doc_type TEXT NOT NULL,
  fields TEXT NOT NULL, issues TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS prompts (
  id INTEGER PRIMARY KEY AUTOINCREMENT, member TEXT NOT NULL, kind TEXT NOT NULL, ref TEXT NOT NULL,
  options TEXT NOT NULL, status TEXT NOT NULL, at TEXT NOT NULL, text TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS share_requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT, asker TEXT NOT NULL, category TEXT NOT NULL,
  question TEXT NOT NULL, record_ids TEXT NOT NULL, chat_id TEXT NOT NULL, status TEXT NOT NULL,
  at TEXT NOT NULL, decided_at TEXT);
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
            columns = {r["name"] for r in db.execute("PRAGMA table_info(prompts)")}
            if "text" not in columns:  # stores created before prompts were queued
                db.execute("ALTER TABLE prompts ADD COLUMN text TEXT NOT NULL DEFAULT ''")

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
            db.execute("UPDATE members SET telegram_id=NULL")  # IDs may move between members
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

    def record(self, record_id: str) -> sqlite3.Row | None:
        """Latest version of a record, whatever its status."""
        with self._db() as db:
            return db.execute(
                "SELECT * FROM records WHERE id=? ORDER BY version DESC LIMIT 1", (record_id,)
            ).fetchone()

    def supersede(self, old_id: str, new_id: str) -> None:
        """Mark a record superseded and cancel its pending events, in one transaction."""
        with self._db() as db:
            db.execute(
                "UPDATE records SET status='superseded', superseded_by=?"
                " WHERE id=? AND status='active'",
                (new_id, old_id),
            )
            db.execute(
                "UPDATE events SET status='cancelled' WHERE record_id=? AND status='active'",
                (old_id,),
            )

    # --- events --------------------------------------------------------------------------
    def add_event(
        self,
        *,
        event_id: str,
        record_id: str,
        record_version: int,
        assignee: str,
        kind: str,
        at: str,
        tz: str,
        label: str,
        until: str | None = None,
    ) -> bool:
        """Insert an event once; a stable ID makes re-activation idempotent. True if new."""
        with self._db() as db:
            cur = db.execute(
                "INSERT OR IGNORE INTO events (id, record_id, record_version, assignee, kind, at,"
                " until, tz, label, status) VALUES (?,?,?,?,?,?,?,?,?, 'active')",
                (event_id, record_id, record_version, assignee, kind, at, until, tz, label),
            )
            return cur.rowcount == 1

    def active_events(self) -> list[sqlite3.Row]:
        with self._db() as db:
            return list(db.execute("SELECT * FROM events WHERE status='active' ORDER BY at"))

    def claim_event(self, event_id: str, stamp: str) -> bool:
        """Atomically mark an event sent for `stamp` (local date or datetime); False if it was."""
        with self._db() as db:
            cur = db.execute(
                "UPDATE events SET last_sent=? WHERE id=? AND status='active'"
                " AND (last_sent IS NULL OR last_sent<>?)",
                (stamp, event_id, stamp),
            )
            return cur.rowcount == 1

    def finish_event(self, event_id: str) -> None:
        with self._db() as db:
            db.execute("UPDATE events SET status='done' WHERE id=?", (event_id,))

    # --- drafts and prompts --------------------------------------------------------------
    def save_draft(self, draft: dict[str, Any]) -> None:
        with self._db() as db:
            db.execute(
                "INSERT INTO drafts VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET"
                " document_ids=excluded.document_ids, doc_type=excluded.doc_type,"
                " fields=excluded.fields, issues=excluded.issues, status=excluded.status,"
                " updated_at=excluded.updated_at",
                (
                    draft["id"],
                    draft["admin"],
                    json.dumps(draft["document_ids"]),
                    draft["doc_type"],
                    json.dumps(draft["fields"], ensure_ascii=False),
                    json.dumps(draft["issues"], ensure_ascii=False),
                    draft["status"],
                    draft.get("created_at") or now(),
                    now(),
                ),
            )

    def draft(self, draft_id: str) -> dict[str, Any] | None:
        with self._db() as db:
            row = db.execute("SELECT * FROM drafts WHERE id=?", (draft_id,)).fetchone()
        return None if row is None else _draft(row)

    def open_drafts(self, admin: str) -> list[dict[str, Any]]:
        with self._db() as db:
            rows = db.execute(
                "SELECT * FROM drafts WHERE admin=? AND status='open' ORDER BY created_at", (admin,)
            ).fetchall()
        return [_draft(r) for r in rows]

    def open_prompt(
        self,
        member: str,
        kind: str,
        ref: str,
        options: list[str],
        text: str = "",
        queued: bool = False,
    ) -> int:
        """Record a question (open, or queued behind the open one); a newer question about the
        same thing (kind and ref) replaces the older one. See kin.prompts."""
        with self._db() as db:
            db.execute(
                "UPDATE prompts SET status='done' WHERE member=? AND kind=? AND ref=?"
                " AND status IN ('open','queued')",
                (member, kind, ref),
            )
            cur = db.execute(
                "INSERT INTO prompts (member, kind, ref, options, status, at, text)"
                " VALUES (?,?,?,?,?,?,?)",
                (
                    member,
                    kind,
                    ref,
                    json.dumps(options, ensure_ascii=False),
                    "queued" if queued else "open",
                    now(),
                    text,
                ),
            )
            return int(cur.lastrowid)

    def requeue(self, prompt_id: int) -> None:
        """Put an open question back in the queue; its age keeps it first in line."""
        with self._db() as db:
            db.execute("UPDATE prompts SET status='queued' WHERE id=?", (prompt_id,))

    def next_queued(self, member: str) -> sqlite3.Row | None:
        """The oldest waiting question, now marked open; None when nothing waits."""
        with self._db() as db:
            row = db.execute(
                "SELECT * FROM prompts WHERE member=? AND status='queued' ORDER BY id LIMIT 1",
                (member,),
            ).fetchone()
            if row is not None:
                db.execute("UPDATE prompts SET status='open' WHERE id=?", (row["id"],))
            return row

    def current_prompt(self, member: str) -> sqlite3.Row | None:
        with self._db() as db:
            return db.execute(
                "SELECT * FROM prompts WHERE member=? AND status='open' ORDER BY id DESC LIMIT 1",
                (member,),
            ).fetchone()

    def close_prompt(self, prompt_id: int) -> None:
        with self._db() as db:
            db.execute("UPDATE prompts SET status='done' WHERE id=?", (prompt_id,))

    # --- sharing -------------------------------------------------------------------------
    def add_share_request(
        self, *, asker: str, category: str, question: str, record_ids: list[str], chat_id: str
    ) -> int:
        with self._db() as db:
            cur = db.execute(
                "INSERT INTO share_requests (asker, category, question, record_ids, chat_id,"
                " status, at) VALUES (?,?,?,?,?,'pending',?)",
                (asker, category, question, json.dumps(record_ids), chat_id, now()),
            )
            return int(cur.lastrowid)

    def share_request(self, request_id: int) -> sqlite3.Row | None:
        with self._db() as db:
            return db.execute("SELECT * FROM share_requests WHERE id=?", (request_id,)).fetchone()

    def decide_share(self, request_id: int, status: str) -> bool:
        with self._db() as db:
            cur = db.execute(
                "UPDATE share_requests SET status=?, decided_at=? WHERE id=? AND status='pending'",
                (status, now(), request_id),
            )
            return cur.rowcount == 1

    def add_grant(
        self, *, record_id: str, record_version: int, grantee: str, scope: str, approved_by: str
    ) -> int:
        with self._db() as db:
            cur = db.execute(
                "INSERT INTO grants (record_id, record_version, grantee, scope, approved_by, at)"
                " VALUES (?,?,?,?,?,?)",
                (record_id, record_version, grantee, scope, approved_by, now()),
            )
            return int(cur.lastrowid)

    def consume_grant(self, grant_id: int) -> None:
        with self._db() as db:
            db.execute(
                "UPDATE grants SET consumed_at=? WHERE id=? AND consumed_at IS NULL",
                (now(), grant_id),
            )

    def standing_grants(self, grantee: str) -> list[sqlite3.Row]:
        """Unrevoked standing grants whose record version is still the active one."""
        with self._db() as db:
            return list(
                db.execute(
                    "SELECT g.* FROM grants g JOIN records r ON r.id=g.record_id"
                    " AND r.version=g.record_version WHERE g.grantee=? AND g.scope='standing'"
                    " AND g.revoked_at IS NULL AND r.status='active'",
                    (grantee,),
                )
            )

    def revoke_grants(self, grantee: str, record_ids: list[str]) -> int:
        if not record_ids:
            return 0
        marks = ",".join("?" * len(record_ids))
        with self._db() as db:
            cur = db.execute(
                f"UPDATE grants SET revoked_at=? WHERE grantee=? AND revoked_at IS NULL"
                f" AND consumed_at IS NULL"
                f" AND record_id IN ({marks})",
                [now(), grantee, *record_ids],
            )
            return cur.rowcount

    def records_of_document(self, document_id: str) -> list[sqlite3.Row]:
        with self._db() as db:
            return list(
                db.execute(
                    "SELECT r.* FROM records r WHERE r.document_id=? AND r.status='active'"
                    " AND r.version=(SELECT MAX(version) FROM records WHERE id=r.id)",
                    (document_id,),
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


def _draft(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "admin": row["admin"],
        "document_ids": json.loads(row["document_ids"]),
        "doc_type": row["doc_type"],
        "fields": json.loads(row["fields"]),
        "issues": json.loads(row["issues"]),
        "status": row["status"],
        "created_at": row["created_at"],
    }
