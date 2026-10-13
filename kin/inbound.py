"""What happens to an inbound message before any model runs (docs/05-architecture.md, Hermes ↔ Kin).

The Kin plugin in Hermes forwards every Telegram message here with the gateway's caller. Kin
answers `pass` (let Hermes run an agent turn with Kin's tools) or `skip` (handled or ignored),
plus an optional reply that Kin sends itself. Unknown chats and senders are skipped silently, so
Hermes never runs for them; every slash command is Kin's, so Hermes' own are not reachable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from kin.members import Roster
from kin.retrieve import Caller, Refused, principal_for
from kin.store import Store

VOICE_REPLY = "I can't listen to voice notes yet. Could you type it instead?"
OTHER_MEDIA_REPLY = "I can read text, photos and documents, but not this kind of message."
HELP = (
    "I keep the family's care records, schedule and reminders.\n"
    'Ask me in plain words, e.g. "Kin, what are the morning medicines now?" '
    'In the group, start with "Kin" or reply to one of my messages.\n'
    "Documents go to {admin} by direct message, who checks them before anything is filed."
)
ADMIN_COMMANDS = {"roles", "who_saw", "skills", "export"}


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


def addressed_to_kin(text: str, bot_username: str) -> bool:
    if re.search(r"\bkin\b", text, re.IGNORECASE):
        return True
    return bool(bot_username) and f"@{bot_username}".lower() in text.lower()


def decide(
    store: Store, roster: Roster, group_chat_id: str, msg: Inbound, bot_username: str = ""
) -> Decision:
    try:
        principal = principal_for(msg.caller, roster, group_chat_id)
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
            store.add_document(
                kind=msg.kind,
                title=msg.filename or "Photo",
                categories=[],
                uploaded_by=member.id,
                content=msg.content,
                suffix=_suffix(msg.filename, msg.kind),
            )
            return Decision(
                "skip",
                "original stored",
                "Saved privately. I'll read documents and draft the records once intake is on.",
            )
        reply = (
            "Please send documents to me by direct message, so the original stays private."
            if member.role == "admin"
            else f"Please send documents to {admin_name} by direct message; "
            "they are checked before anything is filed."
        )
        return Decision("skip", "documents go through the Admin", reply)

    if msg.kind == "command" or msg.text.startswith("/"):
        return _command(store, roster, member, msg, admin_name, bot_username)

    if msg.kind != "text":
        return Decision("skip", "unsupported media", None if not in_dm else OTHER_MEDIA_REPLY)

    if not in_dm and not (msg.reply_to_kin or addressed_to_kin(msg.text, bot_username)):
        return Decision("skip", "group chatter not addressed to Kin")
    return Decision("pass", "agent turn")


def _suffix(filename: str | None, kind: str) -> str:
    if filename and "." in filename:
        return "." + filename.rsplit(".", 1)[1].lower()[:5]
    return ".jpg" if kind == "photo" else ""


def _command(store, roster, member, msg: Inbound, admin_name: str, bot_username: str) -> Decision:
    head, _, args = msg.text.strip().partition(" ")
    name = head.lstrip("/").split("@", 1)[0].lower()
    if "@" in head and bot_username and head.split("@", 1)[1].lower() != bot_username.lower():
        return Decision("skip", "command for another bot")
    if name in ("start", "help"):
        return Decision("skip", f"/{name}", HELP.format(admin=admin_name))
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
    if name in ("skills", "export"):
        return Decision("skip", f"/{name}", "Not available yet.")
    if name == "demo":
        return Decision("skip", "/demo", "That command only works in the judge demo.")
    return Decision("skip", "unknown command", "I don't know that command. Try /help.")
