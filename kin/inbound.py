"""What happens to an inbound message before any model runs (docs/05-architecture.md, Hermes ↔ Kin).

The Kin plugin in Hermes forwards every Telegram message here with the gateway's caller. Kin
answers `pass` (let Hermes run an agent turn with Kin's tools) or `skip` (handled or ignored),
plus an optional reply that Kin sends itself. Unknown chats and senders are skipped silently, so
Hermes never runs for them; every slash command is Kin's, so Hermes' own are not reachable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from kin import flows, share, skills
from kin.context import Context
from kin.retrieve import Caller, Principal, Refused, principal_for

VOICE_REPLY = "I can't listen to voice notes yet. Could you type it instead?"
OTHER_MEDIA_REPLY = "I can read text, photos and documents, but not this kind of message."
HELP = (
    "I keep the family's care records, schedule and reminders.\n"
    'Ask me in plain words, e.g. "Kin, what are the morning medicines now?" '
    'In the group, start with "Kin" or reply to one of my messages.\n'
    "Documents go to {admin} by direct message, who checks them before anything is filed."
)
ADMIN_COMMANDS = {"roles", "who_saw", "reminders", "revoke", "export"}


@dataclass
class Inbound:
    caller: Caller
    kind: str  # text | command | photo | document | voice | audio | video | sticker | location
    text: str = ""
    message_id: str | None = None
    reply_to_kin: bool = False
    content: bytes | None = None
    filename: str | None = None


@dataclass
class Decision:
    action: str  # "pass" | "skip"
    reason: str
    reply: str | None = None
    intake: str | None = None  # document ID to read in the background


def addressed_to_kin(text: str, bot_username: str) -> bool:
    if re.search(r"\bkin\b", text, re.IGNORECASE):
        return True
    return bool(bot_username) and f"@{bot_username}".lower() in text.lower()


def decide(ctx: Context, msg: Inbound, bot_username: str = "") -> Decision:
    store, roster = ctx.store, ctx.roster
    try:
        principal = principal_for(msg.caller, roster, ctx.group_chat_id)
    except Refused as exc:
        return Decision("skip", f"refused: {exc}")
    member = principal.member
    if member.role is None:
        return Decision("skip", "unknown sender")
    admin = next((m for m in roster.members if m.role == "admin"), None)
    admin_name = admin.short if admin else "the family admin"
    in_dm = principal.chat_type == "dm"
    if in_dm:
        store.mark_dm_opened(member.id)

    if msg.kind in ("voice", "audio"):
        return Decision("skip", "audio not processed", VOICE_REPLY)

    if msg.kind in ("photo", "document"):
        if member.role == "admin" and in_dm and msg.content:
            doc_id = store.add_document(
                kind=msg.kind,
                title=msg.filename or "Photo",
                categories=[],
                uploaded_by=member.id,
                content=msg.content,
                suffix=_suffix(msg.filename, msg.kind),
            )
            reading = ctx.client is not None and bool(ctx.model_vision)
            reply = "Saved privately. Reading it now…" if reading else "Saved privately."
            return Decision("skip", "original stored", reply, intake=doc_id if reading else None)
        reply = (
            "Please send documents to me by direct message, so the original stays private."
            if member.role == "admin"
            else f"Please send documents to {admin_name} by direct message; "
            "they are checked before anything is filed."
        )
        return Decision("skip", "documents go through the Admin", reply)

    if msg.kind == "command" or msg.text.startswith("/"):
        return _command(ctx, principal, msg, admin_name, bot_username)

    if msg.kind != "text":
        return Decision("skip", "unsupported media", None if not in_dm else OTHER_MEDIA_REPLY)

    if not in_dm and not (msg.reply_to_kin or addressed_to_kin(msg.text, bot_username)):
        return Decision("skip", "group chatter not addressed to Kin")
    if in_dm:
        handled = flows.handle_prompt(ctx, member, msg.text)
        if handled is not None:
            return Decision("skip", "prompt answer", handled or None)
    category = share.blocked_category(ctx.policy, member, msg.text)
    if category and in_dm and share.granted(store, member, category):
        category = None  # already shared: answered from the approved excerpts, DM only
    if category:
        reply = share.start(
            ctx.store,
            ctx.policy,
            roster,
            ctx.sender,
            member,
            category,
            msg.text,
            principal.chat_id,
            principal.chat_type,
        )
        return Decision("skip", f"share request: {category}", reply)
    return Decision("pass", "agent turn")


def _suffix(filename: str | None, kind: str) -> str:
    if filename and "." in filename:
        return "." + filename.rsplit(".", 1)[1].lower()[:5]
    return ".jpg" if kind == "photo" else ""


def _command(
    ctx: Context, principal: Principal, msg: Inbound, admin_name: str, bot_username: str
) -> Decision:
    store, roster, member = ctx.store, ctx.roster, principal.member
    head, _, args = msg.text.strip().partition(" ")
    name = head.lstrip("/").split("@", 1)[0].lower()
    if "@" in head and bot_username and head.split("@", 1)[1].lower() != bot_username.lower():
        return Decision("skip", "command for another bot")
    if name in ("start", "help"):
        return Decision("skip", f"/{name}", HELP.format(admin=admin_name))
    if name == "skills":
        if msg.caller.chat_type != "dm":
            return Decision("skip", "/skills in group", "Ask me that in our direct chat.")
        return Decision("skip", "/skills", skills.describe(ctx, principal))
    if name in ADMIN_COMMANDS and member.role != "admin":
        return Decision("skip", f"/{name} refused", f"That command is for {admin_name}.")
    if name in ADMIN_COMMANDS and msg.caller.chat_type != "dm":
        # Roster and audit details are Admin-only: never answer them where the group can read.
        return Decision("skip", f"/{name} in group", "Ask me that in our direct chat.")
    if name == "roles":
        lines = [
            f"{m['name']}: {m['role']}, {m['language']}"
            + (" (no Telegram account)" if not m["telegram_id"] else "")
            for m in store.members()
        ]
        return Decision("skip", "/roles", "Roster:\n" + "\n".join(lines))
    if name == "who_saw":
        ref = args.strip()
        if not ref:
            return Decision("skip", "/who_saw", "Usage: /who_saw <record or document id>")
        rows = store.audit_for(ref)
        if not rows:
            return Decision("skip", "/who_saw", f"No one has been shown {ref}.")
        lines = [
            f"{r['at'][:16]} {r['principal']} ({r['chat_type']}): {r['decision']}" for r in rows
        ]
        return Decision("skip", "/who_saw", f"Shown {ref}:\n" + "\n".join(lines))
    if name == "reminders":
        events = store.active_events()
        if not events:
            return Decision("skip", "/reminders", "No reminders are scheduled.")
        lines = []
        for e in events:
            who = roster.by_id(e["assignee"])
            when = f"daily {e['at']}" if e["kind"] == "daily" else e["at"].replace("T", " ")
            until = f" until {e['until']}" if e["until"] else ""
            lines.append(f"{when}{until} → {who.short if who else e['assignee']}: {e['label']}")
        return Decision("skip", "/reminders", "Scheduled reminders:\n" + "\n".join(lines))
    if name == "revoke":
        target, _, ref = args.strip().partition(" ")
        member_to = roster.by_id(target.strip()) or next(
            (m for m in roster.members if m.short.lower() == target.strip().lower()), None
        )
        if member_to is None or not ref.strip():
            return Decision("skip", "/revoke", "Usage: /revoke <member id> <record or document id>")
        ids = [ref.strip()] + [r["id"] for r in store.records_of_document(ref.strip())]
        n = store.revoke_grants(member_to.id, ids)
        return Decision("skip", "/revoke", f"Revoked {n} grant(s) for {member_to.short}.")
    if name == "export":
        return Decision("skip", "/export", "Not available yet.")
    if name == "demo":
        return Decision("skip", "/demo", "That command only works in the judge demo.")
    return Decision("skip", "unknown command", "I don't know that command. Try /help.")
