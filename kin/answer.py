"""Kin's last look at an answer before Hermes sends it (docs/05-architecture.md, Ask).

The plugin's `transform_llm_output` hook posts every final reply here with the gateway's caller.
Kin re-checks the destination first: a reply that contains anything this chat may not see now
(a hidden field, another member's record, an excerpt not approved for every reader) is withheld,
whatever the model picked up earlier in the session. Otherwise Kin appends the approved excerpts
of the records the reply cites and the source of a public lookup, so neither depends on the model
quoting them.
"""

from __future__ import annotations

import re
import threading
from typing import Any

from kin.retrieve import Caller, Principal, hidden_values, norm, visible

WITHHELD = "I can't share that here."
# Citation markers some models add, e.g. 【{"id":"rec-18551cb6ff"}】: record IDs mean nothing to
# the family, so they never reach the chat.
MARKERS = re.compile(r"\s*【[^】]*】|\s*\[\{\s*\"id\"\s*:\s*\"[^\"]*\"\s*\}\]")
MAX_EXCERPTS = 3
ANCHORS = ("drug", "department", "clinic", "title", "insurer")
ANSWER_RULES = (
    "Answer only from these records, which are all this person may see in this chat. "
    "Name the source (document and date) for every statement. If nothing here answers the "
    "question, say you don't know. Never mention or guess at anything not listed. A medicine can "
    "have more than one record (its schedule and its pharmacy label): mention each medicine once. "
    "Kin adds the approved excerpts below your answer, so don't repeat them, and never show "
    "record IDs. Organise, never "
    "advise: no diagnosis, dosing or interpretation."
)


def rules(household: dict[str, Any], admin: str = "") -> str:
    who = household.get("care_recipient") or {}
    about = ""
    if who.get("name"):
        call = f", whom the family calls {who['call']}" if who.get("call") else ""
        about = f"These records are about {who['name']}{call}. "
    documents = (
        f" Documents reach Kin only through {admin}, by direct message: if one would answer the "
        f"question, say {admin} can send it; never ask anyone else for documents."
        if admin
        else ""
    )
    return about + ANSWER_RULES + documents


class Turns:
    """What Kin's tools returned in each caller's current turn: record IDs and lookup sources."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._turns: dict[tuple[str, str], dict[str, list]] = {}

    @staticmethod
    def key(caller: Caller) -> tuple[str, str]:
        return (str(caller.user_id), str(caller.chat_id))

    def begin(self, caller: Caller, question: str = "") -> None:
        with self._lock:
            self._turns[self.key(caller)] = {"records": [], "sources": [], "question": question}

    def add(self, caller: Caller, records: list[str] = (), sources: list[dict] = ()) -> None:
        with self._lock:
            turn = self._turns.setdefault(self.key(caller), {"records": [], "sources": []})
            turn["records"] += list(records)
            turn["sources"] += list(sources)

    def pop(self, caller: Caller) -> dict[str, list]:
        with self._lock:
            return self._turns.pop(self.key(caller), {"records": [], "sources": []})


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z]{5,}", norm(text)))


def cites(text: str, record: dict[str, Any]) -> bool:
    """Whether a reply is about this record: it names it, or shares words with its excerpt."""
    low = norm(text)
    names = [norm(v) for k in ANCHORS if isinstance(v := record["fields"].get(k), str) and v]
    if any(re.search(rf"\b{re.escape(n)}\b", low) for n in names):
        return True
    return any(len(_words(e["text"]) & _words(low)) >= 3 for e in record["excerpts"])


def finish(ctx, caller: Caller, principal: Principal, text: str) -> tuple[str, str]:
    """(reply to send, decision). The reply is the model's text, withheld or with sources added."""
    store, policy = ctx.store, ctx.policy
    turn = ctx.turns.pop(caller)
    text = MARKERS.sub("", text)
    shown = visible(store, policy, principal)
    low = norm(text)
    # Repeating the asker's own words reveals nothing; withholding them would ("Does she have
    # hypertension?" refused only when it is on file), so they don't count.
    asked = norm(turn.get("question", ""))
    hidden = hidden_values(store, policy, principal, shown)
    leaked = [v for v in hidden if v in low and v not in asked]
    if leaked:
        store.audit(
            principal=principal.member.id,
            action="answer",
            decision="withheld",
            chat_type=principal.chat_type,
            chat_id=principal.chat_id,
            destination=principal.chat_id,
        )
        return WITHHELD, "withheld"
    by_id = {r["id"]: r for r in shown}
    cited = [by_id[i] for i in dict.fromkeys(turn["records"]) if i in by_id]
    cited = [r for r in cited if cites(text, r)]
    lines, used = [], set()
    for r in cited:
        for e in r["excerpts"]:
            if e["id"] in used or norm(e["text"]) in low or len(used) >= MAX_EXCERPTS:
                continue
            used.add(e["id"])
            lines.append(f"“{e['text']}” ({r['fields'].get('source') or 'source on file'})")
    sources = turn["sources"]
    if sources and not any(s["url"] in text for s in sources):
        lines.append(f"Source: {sources[0]['title']}, {sources[0]['url']}")
    store.audit(
        principal=principal.member.id,
        action="answer",
        decision="sent",
        chat_type=principal.chat_type,
        chat_id=principal.chat_id,
        records=[r["id"] for r in cited],
        fields={r["id"]: ["excerpt"] for r in cited if r["excerpts"]},
        destination=principal.chat_id,
    )
    return (text.rstrip() + "\n\n" + "\n".join(lines) if lines else text), "sent"
