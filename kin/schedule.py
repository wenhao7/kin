"""Reminders and skills from active events, sent by DM in the locale's timezone.

Each event is claimed in the store before it is sent (a `last_sent` stamp per day, or per due
time for one-off events), so a restart or a second tick never sends it twice. Events due at the
same time for the same person go out as one message. Recipients are re-authorised when an event
fires: someone who left the roster or lost access to the record's category gets nothing, and the
Admin is told.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from kin import skills
from kin.store import Store

logger = logging.getLogger("kin.schedule")
WINDOW = timedelta(minutes=10)  # a late tick (restart, sleep) still sends within this window


def due(store: Store, now: datetime) -> list[tuple[Any, str]]:
    """(event, stamp) pairs due at local time `now`; claiming happens in `tick`."""
    out = []
    today = now.date().isoformat()
    for e in store.active_events():
        if e["kind"] in ("daily", "weekly"):
            if e["until"] and today > e["until"]:
                store.finish_event(e["id"])
                continue
            hhmm = e["at"]
            if e["kind"] == "weekly":
                day, hhmm = e["at"].split()
                if skills.DAYS.index(day) != now.weekday():
                    continue
            hh, mm = map(int, hhmm.split(":"))
            at = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
            if at <= now < at + WINDOW and e["last_sent"] != today:
                out.append((e, today))
        elif e["kind"] == "once":
            at = datetime.fromisoformat(e["at"]).replace(tzinfo=now.tzinfo)
            if at <= now:
                if now < at + WINDOW * 6:
                    out.append((e, e["at"]))
                else:
                    store.finish_event(e["id"])  # long past: never send late
    return out


def authorised(policy, member, row) -> bool:
    """May this member still receive this record's reminder? Checked when it fires."""
    if member is None or member.role is None or row is None:
        return False
    level, qualifier = policy.level(member.role, row["category"])
    if level == "none" or (qualifier and qualifier != "own"):
        return False
    return qualifier != "own" or member.id in (row["created_by"], row["assignee"])


def tick(ctx, now: datetime | None = None) -> int:
    """Send what is due now; returns the number of messages sent."""
    store, roster, sender = ctx.store, ctx.roster, ctx.sender
    now = now or datetime.now(ZoneInfo(ctx.tz))
    groups: dict[tuple[str, str], list[Any]] = {}
    for event, stamp in due(store, now):
        if store.claim_event(event["id"], stamp):
            groups.setdefault((event["assignee"], event["at"]), []).append(event)
            if event["kind"] == "once":
                store.finish_event(event["id"])
    sent = 0
    for (assignee, at), events in groups.items():
        member = roster.by_id(assignee)
        rows = {e["id"]: store.record(e["record_id"]) for e in events}
        refused = [e for e in events if not authorised(ctx.policy, member, rows[e["id"]])]
        events = [e for e in events if e not in refused]
        if refused:
            _refused(ctx, assignee, member, refused)
        if not events:
            continue
        skill = next((rows[e["id"]] for e in events if skills.is_skill(rows[e["id"]])), None)
        text = f"Reminder ({at[11:16] if 'T' in at else at[-5:]}):\n" + "\n".join(
            f"• {e['label']}" for e in events
        )
        if skill is not None:
            to = roster.by_id(json.loads(skill["fields"]).get("report_to", ""))
            text += f"\nTap {skills.DONE} when it's finished" + (
                f" and I'll tell {to.short}." if to else "."
            )
        delivery = "no account"
        if member and member.telegram_id:
            keyboard = [skills.DONE] if skill is not None else None
            result = sender.send(member.telegram_id, text, keyboard=keyboard)
            delivery = "sent" if result.get("ok") else f"failed: {result.get('error')}"
            sent += int(bool(result.get("ok")))
            if skill is not None and result.get("ok"):
                store.open_prompt(member.id, "skill", skill["id"], [skills.DONE])
        store.audit(
            principal=assignee,
            action="skill" if skill is not None else "reminder",
            decision="due",
            records=[e["record_id"] for e in events],
            destination=member.telegram_id if member else None,
            delivery=delivery,
        )
    return sent


def _refused(ctx, assignee: str, member, events: list[Any]) -> None:
    known = {m["id"]: m["name"] for m in ctx.store.members()}  # who they were, if they left
    name = member.short if member else known.get(assignee, assignee)
    for e in events:
        ctx.store.audit(
            principal=assignee,
            action="reminder",
            decision="refused: not authorised",
            records=[e["record_id"]],
        )
    admin = ctx.roster.admin()
    if admin and admin.telegram_id:
        labels = "\n".join(f"• {e['label']}" for e in events)
        ctx.sender.send(
            admin.telegram_id,
            f"I didn't send this to {name}, who no longer has access to it:\n{labels}",
        )


def start(ctx, interval: float = 30) -> threading.Thread:
    def loop() -> None:
        while True:
            try:
                tick(ctx)
            except Exception:  # noqa: BLE001 - keep the scheduler alive
                logger.exception("reminder tick failed")
            time.sleep(interval)

    thread = threading.Thread(target=loop, name="kin-reminders", daemon=True)
    thread.start()
    return thread
