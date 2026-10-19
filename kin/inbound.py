"""What happens to an inbound message before any model runs (docs/05-architecture.md, Hermes ↔ Kin).

The Kin plugin in Hermes forwards every Telegram message here with the gateway's caller. Kin
answers `pass` (let Hermes run an agent turn with Kin's tools) or `skip` (handled or ignored),
plus an optional reply that Kin sends itself. Unknown chats and senders are skipped silently, so
Hermes never runs for them; every slash command is Kin's, so Hermes' own are not reachable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from kin import admin, demo, flows, share, skills
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
HELP_ADMIN = (
    "\n\nIn our chat you can also use /reminders, /who_saw (who has been shown a document), "
    "/revoke (stop sharing something), /skills and /roles. Tap / to see them."
)
HELP_MEMBER = "\n\n/skills shows what I do for you on a schedule."
ADMIN_COMMANDS = {"roles", "who_saw", "reminders", "revoke", "export"}
# Button labels that only ever answer one of Kin's questions; with none open they are stale.
STALE_BUTTONS = {"post to group", "don't post", "just this once", "cancel"}
ANSWERED = "That question has already been answered."
# Asking for a document or photo itself: originals never leave Kin, so the reply is fixed rather
# than left to the model (which twice answered "Here is the discharge letter…" with nothing).
_DOCS = (
    r"(letter|document|summary|memo|label|slip|scan|pdf|photo|picture|original|file|copy|report)"
)
ORIGINAL_REQUEST = re.compile(
    rf"\b(send|forward|e-?mail)\b[^.?!]{{0,40}}\b{_DOCS}s?\b|\b(copy|scan|pdf|photo|picture)\s+of\b",
    re.IGNORECASE,
)
ORIGINALS_REPLY = (
    "I can't send documents or photos: the originals stay private. Ask me what you'd like to know "
    "from it, for example the medicines, the next appointment or the care instructions."
)


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
    remove_keyboard: bool = False
    reset_sessions: bool = False  # judge demo: the tester switched role


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
    if ctx.demo and principal.chat_type == "dm" and msg.text.startswith("/"):
        name = msg.text.strip().partition(" ")[0].lstrip("/").split("@", 1)[0].lower()
        if name == "demo":
            reply, reset = demo.command(ctx, str(msg.caller.user_id), msg.text.partition(" ")[2])
            return Decision("skip", "/demo", reply, reset_sessions=reset)
        if member.role is None and name in ("start", "help"):
            return Decision("skip", f"/{name} (demo)", demo.INTRO)
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
        if ctx.demo and member.role != "admin":
            reply = f"In the demo, documents come in as {admin_name}: send /demo admin first."
        return Decision("skip", "documents go through the Admin", reply)

    if msg.kind == "command" or msg.text.startswith("/"):
        return _command(ctx, principal, msg, admin_name, bot_username)

    if msg.kind != "text":
        return Decision("skip", "unsupported media", None if not in_dm else OTHER_MEDIA_REPLY)

    if not in_dm and not (msg.reply_to_kin or addressed_to_kin(msg.text, bot_username)):
        return Decision("skip", "group chatter not addressed to Kin")
    if in_dm:
        for seat in roster.seats(member):  # in the demo one account answers for every member
            handled = flows.handle_prompt(ctx, seat, msg.text)
            if handled is not None:
                return Decision("skip", "prompt answer", handled or None)
        if msg.text.strip().lower() in STALE_BUTTONS:  # a tap on an old keyboard: never the model's
            return Decision("skip", "stale button", ANSWERED, remove_keyboard=True)
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
    if ORIGINAL_REQUEST.search(msg.text):
        return Decision("skip", "original requested", ORIGINALS_REPLY)
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
        extra = ""
        if msg.caller.chat_type == "dm":
            extra = HELP_ADMIN if member.role == "admin" else HELP_MEMBER
            if ctx.demo:
                extra += f"\n\nJudge demo: you're playing {member.short}. /demo to switch."
        return Decision("skip", f"/{name}", HELP.format(admin=admin_name) + extra)
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
        return Decision("skip", "/who_saw", admin.who_saw(ctx, member, args) or None)
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
        return Decision("skip", "/revoke", admin.revoke(ctx, member, args) or None)
    if name == "export":
        return Decision("skip", "/export", "Not available yet.")
    if name == "demo":
        return Decision("skip", "/demo", "That command only works in the judge demo.")
    return Decision("skip", "unknown command", "I don't know that command. Try /help.")
