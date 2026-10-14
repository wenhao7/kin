"""D4: the Monday skill. Seeded as Admin-confirmed, fires once across restarts, re-authorised."""

from dataclasses import replace
from datetime import datetime
from zoneinfo import ZoneInfo

from kin import schedule, skills
from kin.members import Member, Roster
from kin.retrieve import Principal
from kin.store import Store
from tests.test_api import ADMIN, CARER, FAMILY, GROUP
from tests.test_intake import TZ, kin, send, to  # noqa: F401

MONDAY = datetime(2026, 10, 26, 8, 0, 20, tzinfo=ZoneInfo(TZ))
SKILL = "Every Monday 08:00, remind Siti to refill the pill organiser and tell Mei Ling when done."


def restart(kin):  # noqa: F811
    return replace(kin.ctx, store=Store(kin.store.db_path, kin.store.originals_dir))


def test_skills_lists_what_each_member_may_see_in_dm_only(kin):  # noqa: F811
    for user in (ADMIN, FAMILY, CARER):
        send(kin, user, "/skills", kind="command")
        assert to(kin, user)[-1].startswith(f"Skills Kin runs:\n• {SKILL}")
    send(kin, FAMILY, "/skills", kind="command", chat_type="group")
    assert to(kin, GROUP)[-1] == "Ask me that in our direct chat."
    viewer = Member("respite", "Respite carer", "viewer", "en", "444")
    p = Principal(member=viewer, chat_type="dm", chat_id="444")
    assert skills.describe(kin.ctx, p) == "No skills are set up for you."  # not assigned to them


def test_monday_skill_fires_once_after_a_restart_and_done_reaches_the_admin(kin):  # noqa: F811
    assert schedule.tick(restart(kin), MONDAY) == 2  # the 08:00 medicines, and the skill apart
    message = next(t for t in to(kin, CARER) if "pill organiser" in t)
    assert message == (
        "Reminder (08:00):\n• Refill the pill organiser for the week.\n"
        "Tap Done when it's finished and I'll tell Mei Ling."
    )
    assert kin.sender.keyboards[kin.sender.sent.index((CARER, message))] == ["Done"]
    assert schedule.tick(restart(kin), MONDAY.replace(minute=4)) == 0  # claimed: never twice
    assert send(kin, CARER, "Done")["reason"] == "prompt answer"
    assert to(kin, CARER)[-1] == "Thanks, I've told Mei Ling."
    done = "Siti has done it: Refill the pill organiser for the week."
    assert to(kin, ADMIN)[-1].startswith(done)
    assert send(kin, CARER, "Done")["action"] == "pass"  # answered once; now ordinary chat
    send(kin, ADMIN, "/skills", kind="command")
    assert "last run: Mon 26 Oct" in to(kin, ADMIN)[-1]
    assert schedule.tick(restart(kin), MONDAY.replace(day=27)) == 1  # Tuesday: medicines only


def test_recipients_are_reauthorised_when_the_skill_fires(kin):  # noqa: F811
    roster = kin.ctx.roster
    members = [m for m in roster.members if m.id != "siti"]  # Siti has left the roster
    left = Roster(members, roster.default_role, roster.default_language, roster.household)
    assert schedule.tick(replace(kin.ctx, roster=left), MONDAY) == 0
    assert to(kin, CARER) == []
    notice = to(kin, ADMIN)[-1]
    assert notice.startswith("I didn't send this to Siti Rahmah, who no longer has access to it")
    assert "Refill the pill organiser for the week." in notice
