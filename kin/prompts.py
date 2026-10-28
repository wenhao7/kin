"""Kin's questions to a member, one at a time and none lost.

Draft checks, group-post approvals, share requests and a skill's Done are answered by tapping a
reply-keyboard option, which arrives as ordinary DM text, so only one question can be open per
member. A question that arrives while another is open waits in a queue (the member is told one is
waiting) and is sent once the open one is answered. The next question about the same thing (the
next issue of one draft) replaces it in place. A picker the member asked for (a command's
choices) goes first: the open question is put back at the front of the queue.
"""

from __future__ import annotations

import json

WAITING = "One more question is waiting. First, finish the open one ({what})."
OPEN = {
    "draft": "the document you're checking",
    "summary": "whether to post the update to the group",
    "share": "a request to share something",
    "who_saw": "which document",
    "revoke": "which share to end",
    "skill": "this week's task",
}


def ask(
    store,
    sender,
    member,
    kind: str,
    ref: str,
    text: str,
    options: list[str],
    first: bool = False,
) -> None:
    current = store.current_prompt(member.id)
    if current is not None and first and (current["kind"], current["ref"]) != (kind, ref):
        store.requeue(current["id"])
        current = None
    if current is None or (current["kind"], current["ref"]) == (kind, ref):
        store.open_prompt(member.id, kind, ref, options, text)
        sender.send(member.telegram_id, text, keyboard=options or None)
        return
    store.open_prompt(member.id, kind, ref, options, text, queued=True)
    # Name the open question and give its buttons back, so it is clear what to answer first.
    open_options = json.loads(current["options"])
    note = WAITING.format(what=OPEN.get(current["kind"], "the one above"))
    if not open_options:
        note += " I'm waiting for the value you were typing."
    sender.send(member.telegram_id, note, keyboard=open_options or None)


def advance(store, sender, member, redraft=None) -> None:
    """Send the next waiting question if none is open. A waiting draft is shown afresh through
    `redraft(draft id)`: what was filed meanwhile can raise a new question (a time clash)."""
    if store.current_prompt(member.id) is not None:
        return
    row = store.next_queued(member.id)
    if row is None:
        return
    if row["kind"] == "draft" and redraft is not None:
        redraft(row["ref"])
        return
    sender.send(member.telegram_id, row["text"], keyboard=json.loads(row["options"]) or None)
