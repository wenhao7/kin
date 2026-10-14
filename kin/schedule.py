"""Reminders from active events, sent by DM in the locale's timezone.

Each event is claimed in the store before it is sent (a `last_sent` stamp per day, or per due
time for one-off events), so a restart or a second tick never sends it twice. Events due at the
same time for the same person go out as one message.
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from kin.members import Roster
from kin.store import Store

logger = logging.getLogger("kin.schedule")
WINDOW = timedelta(minutes=10)  # a late tick (restart, sleep) still sends within this window


def due(store: Store, now: datetime) -> list[tuple[Any, str]]:
    """(event, stamp) pairs due at local time `now`; claiming happens in `tick`."""
    out = []
    today = now.date().isoformat()
    for e in store.active_events():
        if e["kind"] == "daily":
            if e["until"] and today > e["until"]:
                store.finish_event(e["id"])
                continue
            hh, mm = map(int, e["at"].split(":"))
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


def tick(store: Store, roster: Roster, sender, tz: str, now: datetime | None = None) -> int:
    """Send what is due now; returns the number of messages sent."""
    now = now or datetime.now(ZoneInfo(tz))
    groups: dict[tuple[str, str], list[Any]] = {}
    for event, stamp in due(store, now):
        if store.claim_event(event["id"], stamp):
            groups.setdefault((event["assignee"], event["at"]), []).append(event)
            if event["kind"] == "once":
                store.finish_event(event["id"])
    sent = 0
    for (assignee, at), events in groups.items():
        member = roster.by_id(assignee)
        label = "\n".join(f"• {e['label']}" for e in events)
        when = at if len(at) == 5 else at[11:16]
        text = f"Reminder ({when}):\n{label}"
        delivery = "no account"
        if member and member.telegram_id:
            result = sender.send(member.telegram_id, text)
            delivery = "sent" if result.get("ok") else f"failed: {result.get('error')}"
            sent += int(bool(result.get("ok")))
        store.audit(
            principal=assignee,
            action="reminder",
            decision="due",
            records=[e["record_id"] for e in events],
            destination=member.telegram_id if member else None,
            delivery=delivery,
        )
    return sent


def start(store: Store, roster: Roster, sender, tz: str, interval: float = 30) -> threading.Thread:
    def loop() -> None:
        while True:
            try:
                tick(store, roster, sender, tz)
            except Exception:  # noqa: BLE001 - keep the scheduler alive
                logger.exception("reminder tick failed")
            time.sleep(interval)

    thread = threading.Thread(target=loop, name="kin-reminders", daemon=True)
    thread.start()
    return thread
