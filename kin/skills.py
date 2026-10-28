"""Reusable skills: Admin-confirmed instructions run by Kin's scheduler (docs/02, Reusable skill).

A skill is a `tasks` record, so who may see it follows the policy like any task, plus a weekly
event. Running it is a reminder to the assignee, re-authorised when it fires (kin.schedule), with
a Done button; the assignee's Done goes to the person the skill reports to. Hermes' own skills
and cron stay off: they run as agent turns without a caller identity.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from kin.retrieve import Principal, visible
from kin.store import Store

DONE = "Done"
DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def add_skill(store: Store, spec: dict[str, Any], tz: str) -> str:
    """Store a confirmed skill and its weekly event (stable IDs, so reseeding never doubles)."""
    day = spec["day"].lower()[:3]
    record_id = store.add_record(
        record_id=spec["id"],
        category="tasks",
        fields={
            "kind": "skill",
            "title": spec["title"],
            "instruction": spec["instruction"],
            "message": spec["message"],
            "schedule": f"Every {DAY_NAMES[DAYS.index(day)]} {spec['time']}",
            "report_to": spec["report_to"],
            "source": spec["source"],
        },
        created_by=spec["confirmed_by"],
        assignee=spec["assignee"],
    )
    store.add_event(
        event_id=f"{spec['id']}:weekly",
        record_id=record_id,
        record_version=store.record(record_id)["version"],
        assignee=spec["assignee"],
        kind="weekly",
        at=f"{day} {spec['time']}",
        tz=tz,
        label=spec["message"],
    )
    return record_id


def is_skill(row: Any) -> bool:
    return row is not None and json.loads(row["fields"]).get("kind") == "skill"


def next_run(at: str, now: datetime) -> datetime:
    day, hhmm = at.split()
    hh, mm = map(int, hhmm.split(":"))
    start = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    ahead = (DAYS.index(day) - now.weekday()) % 7
    when = start + timedelta(days=ahead)
    return when if when > now else when + timedelta(days=7)


def describe(ctx, principal: Principal) -> str:
    """`/skills`: the skills this member may see, with their next and last run."""
    found = visible(ctx.store, ctx.policy, principal) if principal.member.role else []
    mine = [r for r in found if r["category"] == "tasks" and r["fields"].get("kind") == "skill"]
    ctx.store.audit(
        principal=principal.member.id,
        action="skills",
        decision="allowed" if mine else "empty",
        chat_type=principal.chat_type,
        chat_id=principal.chat_id,
        records=[r["id"] for r in mine],
        destination=principal.chat_id,
    )
    if not mine:
        return "No skills are set up for you."
    now = datetime.now(ZoneInfo(ctx.tz))
    events = {e["record_id"]: e for e in ctx.store.active_events() if e["kind"] == "weekly"}
    lines = ["Skills Kin runs:"]
    for r in mine:
        f, e = r["fields"], events.get(r["id"])
        line = f"• {f.get('instruction') or f.get('title')}"
        if e is not None:
            line += f"\n  Next: {next_run(e['at'], now):%a %d %b, %H:%M}"
            if e["last_sent"]:
                line += f" · last run: {datetime.fromisoformat(e['last_sent']):%a %d %b}"
        if f.get("source"):
            line += f"\n  {f['source']}"
        lines.append(line)
    return "\n".join(lines)


def done(ctx, member, prompt: Any) -> str:
    """The assignee tapped Done: tell the person the skill reports to."""
    ctx.store.close_prompt(prompt["id"])
    row = ctx.store.record(prompt["ref"])
    f = json.loads(row["fields"]) if row is not None else {}
    to = ctx.roster.by_id(f.get("report_to", ""))
    when = datetime.now(ZoneInfo(ctx.tz))
    result = {"ok": False}
    if to is not None and to.telegram_id:
        stamp = "" if getattr(ctx, "demo", False) else f" ({when:%a %H:%M})"  # demo: not "now"
        result = ctx.sender.send(
            to.telegram_id, f"{member.short} has done it: {f.get('message', '')}{stamp}"
        )
    ctx.store.audit(
        principal=member.id,
        action="skill_done",
        decision="done",
        records=[prompt["ref"]],
        destination=to.telegram_id if to else None,
        delivery="sent" if result.get("ok") else "failed",
    )
    if not result.get("ok"):
        return "Thanks. I couldn't pass it on just now, so it's noted here."
    return f"Thanks, I've told {to.short}."
