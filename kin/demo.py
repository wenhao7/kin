"""The judge demo (docs/07-demo-plan.md, Judge access): one person plays the whole family.

Only with KIN_DEMO=true, on a store that holds the synthetic fixture. `/demo admin|family|carer`
gives the sender's Telegram account every member's seat and picks who they speak as. Messages Kin
sends to any member then arrive in that account's DM, labelled ("For Mei Ling (Admin):") when they
are for someone other than the member being played, and a tap on any of their buttons answers
for whoever was asked. The next tester to claim the seats signs the previous one out. A role
switch resets the tester's Hermes conversations, so nothing said as one member carries into
another. Reminders don't follow the clock in the demo (a judge abroad would get them at night):
`/demo monday` runs Monday 08:00 on the fixture's demo day.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from kin import admin, schedule
from kin.fixtures import ROOT as FIXTURES
from kin.fixtures import load_expected
from kin.members import Roster, account_of
from kin.seed import load_week0

ROLE_NAMES = {"admin": "Admin", "family": "Family", "carer": "Carer", "viewer": "Viewer"}
ABOUT = {
    "admin": "the daughter who keeps the family's records",
    "family": "her brother, overseas",
    "carer": "the live-in helper",
}
NEXT = {
    "admin": "Try /demo photos and send them back to me here. /reminders, /who_saw, /revoke and "
    "/skills work in this chat.",
    "family": "In the group, try “Kin, what did Dr Tan change at the last visit?” or “Kin, has "
    "the insurance claim gone through?”",
    "carer": "Try /demo monday for Siti's reminders, or ask me “What are the morning medicines "
    "now?”",
}
INTRO = (
    "This is Kin's judge demo: a made-up family, so nothing here is real. Your Telegram account "
    "can play all of them:\n"
    "/demo admin: Mei Ling, who keeps the family's records\n"
    "/demo family: Wei Jie, her brother overseas\n"
    "/demo carer: Siti, the live-in helper\n"
    "/demo photos: sample documents to send me as Mei Ling\n"
    "/demo monday: run Monday 08:00 (reminders and the weekly skill)\n"
    "/demo reset: start the family over\n"
    "Messages for someone you aren't playing are labelled with their name."
)
PHOTOS = [
    ("discharge-summary-p1.jpg", "Discharge summary, page 1"),
    ("discharge-summary-p2.jpg", "Discharge summary, page 2"),
    ("appointment-slip.jpg", "Appointment slip (send it after confirming the summary)"),
]


def roster(base: Roster, accounts: dict[str, str]) -> Roster:
    """The base roster with every seat held by the (single) tester's account."""
    if not accounts:
        return replace(base, acting={})
    account = next(iter(accounts))
    members = [replace(m, telegram_id=f"{account}#{m.id}") for m in base.members]
    return replace(base, members=members, acting=dict(accounts))


def apply(ctx) -> None:
    ctx.roster = roster(ctx.base_roster, ctx.store.demo_accounts())
    ctx.store.sync_roster(ctx.roster)


def _member_for(ctx, word: str):
    for m in ctx.roster.members:
        if word in (m.id, m.short.lower(), m.name.lower()):
            return m
    role = {"family": "family", "carer": "carer", "admin": "admin"}.get(word)
    return next((m for m in ctx.roster.members if role and m.role == role), None)


def command(ctx, account: str, args: str) -> tuple[str, bool]:
    """(reply, reset the tester's conversations) for `/demo <args>` in the tester's DM."""
    word = args.strip().lower()
    store = ctx.store
    held = account in store.demo_accounts()
    if word in ("", "help"):
        playing = ctx.roster.by_telegram_id(account) if held else None
        status = f"You're playing {playing.short}.\n\n" if playing and playing.role else ""
        return status + INTRO, False
    if word in ("off", "leave", "stop"):
        store.demo_release(account)
        apply(ctx)
        return "Signed out of the demo. /demo admin, family or carer to come back.", True
    member = _member_for(ctx, word)
    if member is not None and member.role:
        took = store.demo_claim(account, member.id)
        apply(ctx)
        admin.install_menus(ctx)
        text = f"You're {member.short} now, {ABOUT.get(member.role, member.role)}."
        text += " " + NEXT.get(member.role, "")
        if took:
            text += "\n(Another tester was using the demo and has been signed out.)"
        return text, True
    if not held:
        return "Start with /demo admin, /demo family or /demo carer.", False
    if word == "reset":
        store.reset()
        load_week0(store, tz=ctx.tz)
        apply(ctx)
        playing = ctx.roster.by_telegram_id(account)
        return (
            "The demo family is back where it started: the clinic memo, a pharmacy label, the "
            f"insurance letter and the Monday skill. You're still {playing.short}.",
            True,
        )
    if word == "monday":
        day = load_expected(FIXTURES)["demo_day"]
        now = datetime.fromisoformat(f"{day}T08:00:20").replace(tzinfo=ZoneInfo(ctx.tz))
        sent = schedule.tick(ctx, now)
        if not sent:
            return (
                f"{now:%A %d %b}, 08:00 has already run in this demo. /demo reset starts over.",
                False,
            )
        return (
            f"It's {now:%A %d %b}, 08:00 in the demo family: Siti got the morning medicines and "
            "the weekly pill-organiser skill (above). Tap Done on it to tell Mei Ling.",
            False,
        )
    if word == "photos":
        for name, caption in PHOTOS:
            ctx.sender.send_photo(account, FIXTURES / "photos" / name, caption)
        return (
            "Send these back to me as Mei Ling (/demo admin), page 1 then page 2: forward them or "
            "save and send. I'll read each page and ask you to check what I found.",
            False,
        )
    return "I don't know that one.\n\n" + INTRO, False


class DemoSender:
    """Delivers "<account>#<member>" seats to the tester's real chat, labelled when needed."""

    def __init__(self, inner: Any, ctx: Any):
        self.inner, self.ctx = inner, ctx

    def _route(self, chat_id: str, text: str) -> tuple[str, str]:
        account, _, member_id = str(chat_id).partition("#")
        if member_id and member_id != self.ctx.roster.acting.get(account):
            m = self.ctx.roster.by_id(member_id)
            if m is not None:
                text = f"For {m.short} ({ROLE_NAMES.get(m.role or '', '')}):\n{text}"
        return account, text

    def send(self, chat_id, text, reply_to=None, keyboard=None, remove_keyboard=False):
        chat, text = self._route(chat_id, text)
        return self.inner.send(
            chat, text, reply_to=reply_to, keyboard=keyboard, remove_keyboard=remove_keyboard
        )

    def send_photo(self, chat_id, path: Path, caption: str = ""):
        return self.inner.send_photo(account_of(str(chat_id)), path, caption)

    def set_commands(self, commands, chat_id):
        return self.inner.set_commands(commands, account_of(str(chat_id)))

    def username(self) -> str:
        return self.inner.username()
