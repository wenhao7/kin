"""The Admin's commands in plain language: `/who_saw`, `/revoke`, and each chat's command menu.

`/who_saw` and `/revoke` work without IDs: on their own they offer the documents or the active
shares as buttons; typed text is matched against names and titles. Reports read the audit log,
list only what reached someone (answers, shared excerpts, reminders, group posts), in local time
and by name, and count separately how often Kin read a document to answer questions.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from kin import prompts
from kin.members import account_of

CANCEL = "Cancel"
PICKERS = ("who_saw", "revoke")  # a reply that is not an option closes them (see flows)
MENUS = {
    "admin": [
        ("reminders", "What's scheduled, for whom"),
        ("who_saw", "Who has been shown a document"),
        ("revoke", "Stop sharing something"),
        ("skills", "What Kin does on a schedule"),
        ("roles", "Who is in the family and their roles"),
        ("help", "What Kin does"),
    ],
    "member": [("skills", "What Kin does for you on a schedule"), ("help", "What Kin does")],
    "group": [("help", "What Kin does")],
}
DEMO_ENTRY = ("demo", "Judge demo: switch role, sample photos, Monday 08:00")


def install_menus(ctx) -> list[str]:
    """Per-chat command menus (they outrank Hermes' broader menus); returns any failures.
    One menu per Telegram account: the Admin's when the account holds the Admin's seat."""
    menus: dict[str, str] = {}
    for m in ctx.roster.members:
        account = account_of(m.telegram_id)
        if account and menus.get(account) != "admin":
            menus[account] = "admin" if m.role == "admin" else "member"
    if ctx.group_chat_id:
        menus[ctx.group_chat_id] = "group"
    failed = []
    for chat_id, menu in menus.items():
        demo = getattr(ctx, "demo", False) and menu != "group"  # /demo works in DMs only
        commands = MENUS[menu] + ([DEMO_ENTRY] if demo else [])
        if not ctx.sender.set_commands(commands, chat_id).get("ok"):
            failed.append(f"{menu}:{chat_id}")
    return failed


# --- names and times ----------------------------------------------------------------------------
def _name(ctx, member_id: str | None) -> str:
    m = ctx.roster.by_id(member_id or "")
    if m is not None:
        return m.short
    known = {r["id"]: r["name"] for r in ctx.store.members()}
    return known.get(member_id or "", "someone not on the roster")


def _by_telegram(ctx, telegram_id: str | None) -> str:
    m = next((m for m in ctx.roster.members if m.telegram_id == str(telegram_id)), None)
    return m.short if m else "someone"


def _when(ctx, at: str) -> str:
    return f"{datetime.fromisoformat(at).astimezone(ZoneInfo(ctx.tz)):%a %d %b %H:%M}"


def _times(ctx, ats: list[str]) -> str:
    """Up to three times, newest last, the date written once per day."""
    shown, day = [], None
    for at in sorted(ats)[-3:]:
        when = _when(ctx, at)
        shown.append(when if when[:10] != day else when[11:])
        day = when[:10]
    more = len(ats) - len(shown)
    return ", ".join(shown) + (f" and {more} earlier" if more else "")


# --- documents ---------------------------------------------------------------------------------
def documents(ctx) -> list[tuple[str, str]]:
    """(document id, title) for documents with records, newest first; titles from the records."""
    with ctx.store._db() as db:
        rows = db.execute(
            "SELECT d.id, d.title, (SELECT r.fields FROM records r WHERE r.document_id=d.id"
            " ORDER BY r.version DESC LIMIT 1) AS fields FROM documents d"
            " WHERE EXISTS (SELECT 1 FROM records r WHERE r.document_id=d.id)"
            " ORDER BY d.created_at DESC"
        ).fetchall()
    out = []
    for r in rows:
        source = json.loads(r["fields"] or "{}").get("source") or r["title"]
        out.append((r["id"], source))
    return out


def _find_document(ctx, text: str) -> str | None:
    text = text.strip().lower()
    if not text:
        return None
    row = ctx.store.record(text)  # a record ID resolves to its document
    if row is not None and row["document_id"]:
        return row["document_id"]
    matches = [d for d, title in documents(ctx) if text in (d.lower(), title.lower())]
    matches = matches or [d for d, title in documents(ctx) if text in title.lower()]
    return matches[0] if len(matches) == 1 else None


def who_saw(ctx, member, args: str) -> str:
    doc = _find_document(ctx, args)
    if doc is not None:
        return report(ctx, doc)
    titles = [t for _, t in documents(ctx)][:8]
    if not titles:
        return "No documents are filed yet."
    question = f"Which document did you mean by “{args}”?" if args.strip() else "Which document?"
    prompts.ask(
        ctx.store, ctx.sender, member, "who_saw", "picker", question, titles + [CANCEL], first=True
    )
    return ""


def report(ctx, doc_id: str) -> str:
    """Who has been shown anything from this document, by name and local time."""
    title = dict(documents(ctx)).get(doc_id, doc_id)
    rows = ctx.store.audit_for(doc_id, limit=1000)[::-1]  # oldest first
    seen: dict[str, list[str]] = {}
    reads: dict[str, int] = {}
    for r in rows:
        action, decision = r["action"], r["decision"]
        if action == "answer" and decision == "sent":
            who = _name(ctx, r["principal"])
            key = (
                f"The group (asked by {who})" if r["chat_type"] == "group"
                else f"{who}, in a direct message"
            )
            seen.setdefault(key, []).append(r["at"])
        elif action == "share_decision" and decision in ("once", "yes", "no"):
            admin = ctx.roster.admin()
            older = admin is not None and r["principal"] == admin.id  # logged by Telegram ID
            who = _by_telegram(ctx, r["destination"]) if older else _name(ctx, r["principal"])
            how = {"once": "shared once", "yes": "shared until revoked", "no": "asked; not shared"}
            seen.setdefault(f"{who}, {how[decision]}", []).append(r["at"])
        elif action in ("reminder", "skill", "schedule") and r["delivery"] == "sent":
            label = "the new schedule" if action == "schedule" else "reminders"
            seen.setdefault(f"{_name(ctx, r['principal'])}, {label} by direct message", []).append(
                r["at"]
            )
        elif action == "group_post" and r["delivery"] == "sent":
            seen.setdefault("The group, in the update you approved", []).append(r["at"])
        elif action == "retrieve" and decision == "allowed":
            who = _name(ctx, r["principal"])
            reads[who] = reads.get(who, 0) + 1
    lines = [title, "The original stays with you; Kin never sends it."]
    lines += [f"• {key}: {_times(ctx, ats)}" for key, ats in seen.items()]
    if not seen:
        lines.append("Nothing from it has been sent to anyone yet.")
    if reads:
        counts = ", ".join(f"{who} ({n})" for who, n in reads.items())
        lines.append(f"Kin also read it while answering {counts}; only the lines above were sent.")
    return "\n".join(lines)


# --- shares ------------------------------------------------------------------------------------
def shares(ctx) -> list[tuple[str, str, list[str]]]:
    """(label, grantee, record IDs) for each active standing share, one per person and document."""
    out: dict[str, tuple[str, list[str]]] = {}
    for m in ctx.roster.members:
        for g in ctx.store.standing_grants(m.id):
            row = ctx.store.record(g["record_id"])
            source = json.loads(row["fields"]).get("source", "") if row else ""
            label = f"{m.short} · {source or g['record_id']}"
            out.setdefault(label, (m.id, []))[1].append(g["record_id"])
    return [(label, grantee, ids) for label, (grantee, ids) in out.items()]


def revoke(ctx, member, args: str) -> str:
    active = shares(ctx)
    if not active:
        return "Nothing is shared right now. What you share with “Yes” shows up here."
    words = _words(args)
    if words:
        matches = [s for s in active if all(w in _words(_haystack(ctx, s)) for w in words)]
        if len(matches) == 1:
            return _end(ctx, matches[0])
    question = (
        "Which share should end? They keep what was already sent, "
        "but Kin won't answer from it again."
    )
    options = [label for label, _, _ in active] + [CANCEL]
    prompts.ask(ctx.store, ctx.sender, member, "revoke", "picker", question, options, first=True)
    return ""


def _words(text: str) -> list[str]:
    return re.sub(r"[_\-·,]+", " ", text.lower()).split()


def _haystack(ctx, share: tuple[str, str, list[str]]) -> str:
    """What a typed /revoke may name: the label, the member's ID, the document and record IDs."""
    label, grantee, ids = share
    docs = [r["document_id"] or "" for r in map(ctx.store.record, ids) if r is not None]
    return " ".join([label, grantee, *ids, *docs])


def _end(ctx, share: tuple[str, str, list[str]]) -> str:
    label, grantee, ids = share
    ctx.store.revoke_grants(grantee, ids)
    who, _, what = label.partition(" · ")
    return f"Done: Kin won't answer {who} from the {what} any more."


def answer_picker(ctx, prompt: Any, text: str) -> str | None:
    """The Admin's tap on a picker; None (and the picker closed) for anything else."""
    choice = text.strip()
    ctx.store.close_prompt(prompt["id"])
    if choice == CANCEL:
        return "Nothing changed." if prompt["kind"] == "revoke" else "OK."
    if prompt["kind"] == "who_saw":
        doc = next((d for d, title in documents(ctx) if title == choice), None)
        return report(ctx, doc) if doc else None
    share = next((s for s in shares(ctx) if s[0] == choice), None)
    return _end(ctx, share) if share else None
