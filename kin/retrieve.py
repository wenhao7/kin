"""`retrieve(query, principal)`: the only read path to the family's records (docs/03).

The principal is built from the caller the gateway supplied (Telegram user, chat, chat type) and
the roster; nothing a model says can change it. Policy is applied before any record leaves the
store: categories are filtered in SQL, `own` qualifiers per row, fields by projection, excerpts by
approved audience. In the group, every category is capped at the group's computed level.
Originals are never returned. Every call is audited, including empty and refused ones.
`visible` is the same view without the audit; `hidden_values` is what a reply to this chat must
not contain (kin.answer).
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


def fields_for_all(policy: Policy, roles: list[str], category: str):
    """Fields every one of these roles may see, each at its own level (the group's cap decides
    only whether the category is shown): None = every field, [] = nothing."""
    allowed: set[str] | None = None
    for role in set(roles):
        known = role in policy.roles and category in policy.categories
        names = policy.fields_for(role, category, policy.level(role, category)[0]) if known else []
        if names is None:
            continue
        allowed = set(names) if allowed is None else allowed & set(names)
    return None if allowed is None else sorted(allowed)


def _relevance(query: str, record: dict[str, Any]) -> int:
    words = {w for w in re.findall(r"[a-z0-9]+", query.lower()) if len(w) > 2}
    text = json.dumps([record["fields"], record["excerpts"]], ensure_ascii=False).lower()
    return sum(1 for w in words if w in text)


def visible(store: Store, policy: Policy, principal: Principal) -> list[dict[str, Any]]:
    """Every active record this principal may see in this chat, projected. Not audited."""
    member = principal.member
    group_roles = store.member_roles()
    levels = {c: effective_level(policy, principal, c, group_roles) for c in policy.categories}
    permitted = [c for c, (level, _) in levels.items() if level != "none"]
    # In the group every member reads the answer: fields and excerpts must suit every role.
    readers = group_roles if principal.chat_type == "group" else [member.role]
    out: list[dict[str, Any]] = []
    for row in store.active_records(permitted):
        qualifier = levels[row["category"]][1]
        if qualifier == "own" and member.id not in (row["created_by"], row["assignee"]):
            continue
        if qualifier and qualifier != "own":
            continue  # other qualifiers (emergency_contacts) are not served yet: fail closed
        names = fields_for_all(policy, readers, row["category"])
        fields = json.loads(row["fields"])
        shown = {k: v for k, v in fields.items() if names is None or k in names}
        if not shown:
            continue
        excerpts = [
            {"id": e["id"], "text": e["text"], "source": e["document_id"]}
            for e in store.excerpts(json.loads(row["excerpt_ids"]))
            if set(readers) <= set(json.loads(e["audience"]))
            and levels.get(e["category"], ("none", None))[0] != "none"
        ]
        out.append(_entry(row, shown, excerpts))
    # Standing grants: in the grantee's own DM only, the approved excerpt and source, no fields.
    if principal.chat_type == "dm" and member.role is not None:
        seen = {r["id"] for r in out}
        for g in store.standing_grants(member.id):
            row = store.record(g["record_id"])
            if row is None or row["id"] in seen:
                continue
            excerpts = [
                {"id": e["id"], "text": e["text"], "source": e["document_id"]}
                for e in store.excerpts(json.loads(row["excerpt_ids"]))
            ]
            if excerpts:
                source = json.loads(row["fields"]).get("source", "")
                out.append(_entry(row, {"source": source}, excerpts, shared_by=g["approved_by"]))
                seen.add(row["id"])
    return out


def _entry(row: Any, fields: dict[str, Any], excerpts: list, **extra: Any) -> dict[str, Any]:
    return {
        "id": row["id"],
        "version": row["version"],
        "category": row["category"],
        "fields": fields,
        "excerpts": excerpts,
        **extra,
    }


def retrieve(
    store: Store, policy: Policy, principal: Principal, query: str, limit: int = 20
) -> Retrieved:
    member = principal.member
    found = visible(store, policy, principal) if member.role is not None else []
    out = sorted(found, key=lambda r: -_relevance(query, r))[:limit]
    decision = "unknown_member" if member.role is None else ("allowed" if out else "empty")
    store.audit(
        principal=member.id,
        action="retrieve",
        decision=decision,
        chat_type=principal.chat_type,
        chat_id=principal.chat_id,
        query=query,
        records=[r["id"] for r in out],
        fields={r["id"]: shown_fields(r) for r in out},
        destination=principal.chat_id,
    )
    return Retrieved(records=out, decision=decision)


def shown_fields(record: dict[str, Any]) -> list[str]:
    return sorted(record["fields"]) + (["excerpt"] if record["excerpts"] else [])


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip().lower()


def _strings(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [s for v in value.values() for s in _strings(v)]
    if isinstance(value, list):
        return [s for v in value for s in _strings(v)]
    return [str(value)] if isinstance(value, str) else []


_MONTHS = "jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec"
_PLAIN = re.compile(rf"^[\d\s:./,-]*(am|pm|{_MONTHS})?[\d\s:./,-]*$")  # dates, times, numbers


def hidden_values(
    store: Store, policy: Policy, principal: Principal, shown: list[dict[str, Any]]
) -> list[str]:
    """Distinctive text this chat may not see now: values of hidden fields and records, and
    excerpts not approved for it. Short values, dates and anything also shown are left out."""
    by_id = {r["id"]: r for r in shown}
    shown_excerpts = {e["id"] for r in shown for e in r["excerpts"]}
    seen = norm(json.dumps([[r["fields"], r["excerpts"]] for r in shown], ensure_ascii=False))
    values: set[str] = set()
    for row in store.active_records(list(policy.categories)):
        fields = json.loads(row["fields"])
        visible_fields = by_id.get(row["id"], {}).get("fields", {})
        for name, value in fields.items():
            if name not in visible_fields and name != "source":  # titles like "Carer note"
                values.update(norm(v) for v in _strings(value))
        for e in store.excerpts(json.loads(row["excerpt_ids"])):
            if e["id"] not in shown_excerpts:
                values.add(norm(e["text"]))
    return sorted(v for v in values if len(v) >= 8 and not _PLAIN.match(v) and v not in seen)
