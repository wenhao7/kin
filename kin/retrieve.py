"""`retrieve(query, principal)`: the only read path to the family's records (docs/03).

The principal is built from the caller the gateway supplied (Telegram user, chat, chat type) and
the roster; nothing a model says can change it. Policy is applied before any record leaves the
store: categories are filtered in SQL, `own` qualifiers per row, fields by projection, excerpts by
approved audience. In the group, every category is capped at the group's computed level.
Originals are never returned. Every call is audited, including empty and refused ones.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from kin.members import Member, Roster
from kin.policy import RANK, Policy
from kin.store import Store


@dataclass(frozen=True)
class Caller:
    """Identity as supplied by the gateway; never by a model."""

    user_id: str
    chat_id: str
    chat_type: str  # "dm" | "group"


@dataclass(frozen=True)
class Principal:
    member: Member
    chat_type: str
    chat_id: str


@dataclass
class Retrieved:
    records: list[dict[str, Any]] = field(default_factory=list)
    decision: str = "allowed"


class Refused(Exception):
    """The caller or chat carries no authority."""


def principal_for(caller: Caller, roster: Roster, group_chat_id: str) -> Principal:
    """Resolve a gateway caller; raise Refused for chats Kin does not serve."""
    member = roster.by_telegram_id(caller.user_id)
    if caller.chat_type == "group":
        if not group_chat_id or str(caller.chat_id) != str(group_chat_id):
            raise Refused("not the family group")
    elif caller.chat_type == "dm":
        if str(caller.chat_id) != str(caller.user_id):
            raise Refused("DM chat does not match the sender")
    else:
        raise Refused(f"unsupported chat type {caller.chat_type!r}")
    return Principal(member=member, chat_type=caller.chat_type, chat_id=str(caller.chat_id))


def effective_level(policy: Policy, principal: Principal, category: str, group_roles: list[str]):
    """(level, qualifier) for this principal in this chat; unknown role → none."""
    role = principal.member.role
    if role is None or role not in policy.roles or category not in policy.categories:
        return "none", None
    level, qualifier = policy.level(role, category)
    if principal.chat_type == "group":
        cap = policy.group_level(category, group_roles)
        if RANK.get(cap, 0) < RANK.get(level, 0):
            level, qualifier = cap, None
    return level, qualifier


def _fields_for_all(policy: Policy, roles: list[str], category: str, level: str):
    """Intersection of the roles' projections at `level`: None = every field, [] = nothing."""
    allowed: set[str] | None = None
    for role in set(roles):
        names = policy.fields_for(role, category, level) if role in policy.roles else []
        if names is None:
            continue
        allowed = set(names) if allowed is None else allowed & set(names)
    return None if allowed is None else sorted(allowed)


def _relevance(query: str, fields: dict[str, Any]) -> int:
    words = {w for w in re.findall(r"[a-z0-9]+", query.lower()) if len(w) > 2}
    text = json.dumps(fields, ensure_ascii=False).lower()
    return sum(1 for w in words if w in text)


def retrieve(
    store: Store, policy: Policy, principal: Principal, query: str, limit: int = 20
) -> Retrieved:
    member = principal.member
    group_roles = store.member_roles()
    levels = {c: effective_level(policy, principal, c, group_roles) for c in policy.categories}
    permitted = [c for c, (level, _) in levels.items() if level != "none"]
    out: list[dict[str, Any]] = []
    shown: dict[str, list[str]] = {}
    for row in store.active_records(permitted):
        level, qualifier = levels[row["category"]]
        if qualifier == "own" and member.id not in (row["created_by"], row["assignee"]):
            continue
        if qualifier and qualifier != "own":
            continue  # other qualifiers (emergency_contacts) are not served yet: fail closed
        # In the group every member reads the answer: fields and excerpts must suit every role.
        readers = group_roles if principal.chat_type == "group" else [member.role]
        names = _fields_for_all(policy, readers, row["category"], level)
        fields = json.loads(row["fields"])
        visible = {k: v for k, v in fields.items() if names is None or k in names}
        if not visible:
            continue
        excerpts = [
            {"text": e["text"], "source": e["document_id"]}
            for e in store.excerpts(json.loads(row["excerpt_ids"]))
            if set(readers) <= set(json.loads(e["audience"]))
            and levels.get(e["category"], ("none", None))[0] != "none"
        ]
        out.append(
            {
                "id": row["id"],
                "version": row["version"],
                "category": row["category"],
                "fields": visible,
                "excerpts": excerpts,
                "_score": _relevance(query, visible),
            }
        )
        shown[row["id"]] = sorted(visible)
    # Standing grants: in the grantee's own DM only, the approved excerpt and source, no fields.
    if principal.chat_type == "dm" and member.role is not None:
        seen = {r["id"] for r in out}
        for g in store.standing_grants(member.id):
            row = store.record(g["record_id"])
            if row is None or row["id"] in seen:
                continue
            fields = json.loads(row["fields"])
            excerpts = [
                {"text": e["text"], "source": e["document_id"]}
                for e in store.excerpts(json.loads(row["excerpt_ids"]))
            ]
            if not excerpts:
                continue
            out.append(
                {
                    "id": row["id"],
                    "version": row["version"],
                    "category": row["category"],
                    "fields": {"source": fields.get("source", "")},
                    "excerpts": excerpts,
                    "shared_by": g["approved_by"],
                    "_score": _relevance(query, fields),
                }
            )
            shown[row["id"]] = ["source", "excerpt"]
    out.sort(key=lambda r: -r["_score"])
    out = out[:limit]
    for r in out:
        r.pop("_score")
    decision = "unknown_member" if member.role is None else ("allowed" if out else "empty")
    store.audit(
        principal=member.id,
        action="retrieve",
        decision=decision,
        chat_type=principal.chat_type,
        chat_id=principal.chat_id,
        query=query,
        records=[r["id"] for r in out],
        fields={r["id"]: shown[r["id"]] for r in out},
        destination=principal.chat_id,
    )
    return Retrieved(records=out, decision=decision)
