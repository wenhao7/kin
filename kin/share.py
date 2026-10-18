"""Share requests: a question about a category the asker cannot see goes to the Admin.

Detection is by keywords (config/policy.yaml `share_keywords`), never by a model, and the asker
gets the same neutral reply whether or not a matching record exists. The Admin answers Yes
(standing grant for the matched records), Just this once (one answer) or No; the answer goes to
the asker's DM as the approved excerpt only, never the original. With a standing grant the
member's later questions in DM go to the agent, which sees only the shared excerpts.
"""

from __future__ import annotations

import json
import re
from typing import Any

from kin import prompts
from kin.members import Member, Roster
from kin.policy import Policy
from kin.store import Store

YES, NO, ONCE = "Yes", "No", "Just this once"
OPTIONS = [YES, NO, ONCE]


def blocked_category(policy: Policy, member: Member, text: str) -> str | None:
    """The share-request category a question is about, if the member has no access to it."""
    if member.role is None:
        return None
    lowered = text.lower()
    for category in policy.share_request_on_none:
        if policy.level(member.role, category)[0] != "none":
            continue
        words = policy.share_keywords.get(category, [])
        if any(re.search(rf"\b{re.escape(w)}\b", lowered) for w in words):
            return category
    return None


def granted(store: Store, member: Member, category: str) -> bool:
    """Whether the member holds a standing grant on an active record of this category."""
    rows = (store.record(g["record_id"]) for g in store.standing_grants(member.id))
    return any(r is not None and r["category"] == category for r in rows)


def _matching(store: Store, category: str, question: str) -> list[Any]:
    words = {w for w in re.findall(r"[a-z0-9]+", question.lower()) if len(w) > 3}
    rows = store.active_records([category])
    scored = [(sum(w in r["fields"].lower() for w in words), r) for r in rows]
    best = max((s for s, _ in scored), default=0)
    return [r for s, r in scored if s == best and s > 0] or rows[:1]


def start(
    store: Store,
    policy: Policy,
    roster: Roster,
    sender,
    member: Member,
    category: str,
    question: str,
    chat_id: str,
    chat_type: str,
) -> str:
    """Open a request, tell the Admin, and return the neutral reply for the asker."""
    admin = roster.admin()
    rows = _matching(store, category, question)
    request_id = store.add_share_request(
        asker=member.id,
        category=category,
        question=question,
        record_ids=[r["id"] for r in rows],
        chat_id=chat_id,
    )
    where = " in the group" if chat_type == "group" else ""
    lines = [f"{member.short} asked{where}: “{question}”"]
    for r in rows:
        f = json.loads(r["fields"])
        excerpts = store.excerpts(json.loads(r["excerpt_ids"]))
        lines.append(f"Matching record: {f.get('source', r['id'])}")
        lines += [f"Would share: “{e['text']}”" for e in excerpts]
    if not rows:
        lines.append("No matching record; answering Yes shares nothing.")
    lines.append(f"Share with {member.short}?")
    if admin and admin.telegram_id:
        prompts.ask(store, sender, admin, "share", str(request_id), "\n".join(lines), OPTIONS)
    store.audit(
        principal=member.id,
        action="share_request",
        decision="pending",
        chat_type=chat_type,
        chat_id=chat_id,
        query=question,
        records=[r["id"] for r in rows],
    )
    return f"I've asked {admin.short if admin else 'the family admin'} to share that."


def decide(
    store: Store, roster: Roster, sender, request_id: int, choice: str, group_chat_id: str
) -> str:
    """Apply the Admin's answer; returns a confirmation for the Admin."""
    req = store.share_request(request_id)
    status = {YES: "yes", NO: "no", ONCE: "once"}[choice]
    if req is None or not store.decide_share(request_id, status):
        return "That request was already answered."
    asker = roster.by_id(req["asker"])
    admin = roster.admin()
    record_ids = json.loads(req["record_ids"])
    if status == "no":
        text = f"{admin.short} has decided not to share that."
        grants: list[int] = []
    else:
        parts, grants = [], []
        for rid in record_ids:
            row = store.record(rid)
            if row is None:
                continue
            grants.append(
                store.add_grant(
                    record_id=rid,
                    record_version=row["version"],
                    grantee=asker.id,
                    scope="standing" if status == "yes" else "once",
                    approved_by=admin.id,
                )
            )
            f = json.loads(row["fields"])
            for e in store.excerpts(json.loads(row["excerpt_ids"])):
                parts.append(f"“{e['text']}” ({f.get('source', '')})")
        text = (
            (f"{admin.short} shared this with you:\n" + "\n".join(parts))
            if parts
            else (f"{admin.short} agreed, but there is no record to share on that.")
        )
    result = sender.send(asker.telegram_id, text) if asker and asker.telegram_id else {"ok": False}
    if status == "once":
        for g in grants:
            store.consume_grant(g)  # one answer, now delivered
    if not result.get("ok") and req["chat_id"] == str(group_chat_id) and asker:
        sender.send(
            group_chat_id,
            f"{asker.short}, please open a chat with me and tap Start so I can reply privately.",
        )
    store.audit(
        principal=admin.id,
        action="share_decision",
        decision=status,
        records=record_ids,
        destination=asker.telegram_id if asker else None,
        delivery="sent" if result.get("ok") else "failed",
    )
    outcome = {
        "yes": "Shared, and they can ask again later.",
        "once": "Shared once.",
        "no": "Not shared.",
    }
    return outcome[status] + (
        "" if result.get("ok") else f" (I couldn't reach {asker.short} by DM yet.)"
    )
