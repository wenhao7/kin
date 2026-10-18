"""Kin's questions to a member, one at a time and none lost.

Draft checks, group-post approvals, share requests and a skill's Done are answered by tapping a
reply-keyboard option, which arrives as ordinary DM text, so only one question can be open per
member. A question that arrives while another is open waits in a queue (the member is told one is
waiting) and is sent once the open one is answered. The next question about the same thing (the
next issue of one draft) replaces it in place.
"""

from __future__ import annotations

import json

WAITING = "One more question is waiting. I'll ask it once you've answered this one."


def ask(store, sender, member, kind: str, ref: str, text: str, options: list[str]) -> None:
    current = store.current_prompt(member.id)
    if current is None or (current["kind"], current["ref"]) == (kind, ref):
        store.open_prompt(member.id, kind, ref, options, text)
        sender.send(member.telegram_id, text, keyboard=options or None)
        return
    store.open_prompt(member.id, kind, ref, options, text, queued=True)
    sender.send(member.telegram_id, WAITING)


def advance(store, sender, member) -> None:
    """Send the next waiting question if none is open."""
    if store.current_prompt(member.id) is not None:
        return
    row = store.next_queued(member.id)
    if row is not None:
        sender.send(member.telegram_id, row["text"], keyboard=json.loads(row["options"]) or None)
