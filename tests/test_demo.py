"""The judge demo: one Telegram account plays the whole synthetic family (KIN_DEMO)."""

from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from kin import demo
from kin.api import create_app
from kin.context import Context
from kin.members import load_roster
from kin.policy import load_policy
from kin.seed import load_week0
from kin.store import Store
from tests.test_api import ADMIN, GROUP, TOKEN, FakeSender
from tests.test_intake import TZ, FakeModels, send, to

ROOT = Path(__file__).resolve().parents[1]
JUDGE, OTHER = "555", "666"


@pytest.fixture()
def kin(tmp_path):
    base = load_roster(ROOT / "config" / "members.yaml")  # no Telegram IDs: seats come from /demo
    store = Store(tmp_path / "kin.sqlite3", tmp_path / "originals")
    store.sync_roster(base)
    load_week0(store, tz=TZ)
    inner = FakeSender()
    ctx = Context(
        store=store,
        policy=load_policy(ROOT / "config" / "policy.yaml"),
        roster=base,
        sender=inner,
        group_chat_id=GROUP,
        tz=TZ,
        client=FakeModels(),
        model_vision="vision",
        model_super="super",
        demo=True,
        base_roster=base,
    )
    ctx.sender = demo.DemoSender(inner, ctx)
    demo.apply(ctx)
    client = TestClient(create_app(ctx, TOKEN))
    client.headers["Authorization"] = f"Bearer {TOKEN}"
    return SimpleNamespace(client=client, store=store, sender=inner, ctx=ctx)


def cmd(kin, user, text):
    return send(kin, user, text, kind="command")


def test_a_new_tester_sees_the_demo_intro_and_nothing_else(kin):
    assert cmd(kin, JUDGE, "/start")["reason"] == "/start (demo)"
    assert to(kin, JUDGE)[-1] == demo.INTRO
    assert send(kin, JUDGE, "What medicines is she on?")["reason"] == "unknown sender"
    assert send(kin, JUDGE, "Kin, what medicines?", chat_type="group")["reason"] == "unknown sender"
    assert cmd(kin, JUDGE, "/demo monday")["reason"] == "/demo"
    assert to(kin, JUDGE)[-1].startswith("Start with /demo admin")


def test_one_account_plays_the_whole_family(kin):
    out = cmd(kin, JUDGE, "/demo admin")
    assert out["reset"] is True and to(kin, JUDGE)[-1].startswith("You're Mei Ling now")
    assert "who_saw" in kin.sender.menus[JUDGE] and "demo" in kin.sender.menus[JUDGE]
    cmd(kin, JUDGE, "/demo photos")
    assert [t for c, t in kin.sender.sent if c == JUDGE and t.startswith("[photo")][:2] == [
        "[photo discharge-summary-p1.jpg] Discharge summary, page 1",
        "[photo discharge-summary-p2.jpg] Discharge summary, page 2",
    ]
    send(kin, JUDGE, photo="p1")
    assert "Draft from the Discharge summary" in to(kin, JUDGE)[-1]  # the member played: no label
    send(kin, JUDGE, photo="p2")
    send(kin, JUDGE, "Glipizide")
    send(kin, JUDGE, "Confirm")
    assert any(t.startswith("For Siti (Carer):\nNew schedule") for t in to(kin, JUDGE))
    send(kin, JUDGE, "Post to group")
    assert len(to(kin, GROUP)) == 2  # English and Mandarin

    cmd(kin, JUDGE, "/demo family")
    send(kin, JUDGE, "Kin, has the insurance claim gone through?", chat_type="group")
    assert to(kin, GROUP)[-1] == "I've asked Mei Ling to share that."
    assert to(kin, JUDGE)[-1].startswith("For Mei Ling (Admin):\nWei Jie asked in the group")
    send(kin, JUDGE, "Just this once")  # answered for Mei Ling while playing Wei Jie
    shared = [t for t in to(kin, JUDGE) if t.startswith("Mei Ling shared this with you")]
    assert shared and "4,820" not in shared[0]
    assert to(kin, JUDGE)[-1] == "For Mei Ling (Admin):\nShared once."


def test_demo_monday_runs_once_and_done_reaches_the_admin(kin):
    cmd(kin, JUDGE, "/demo carer")
    cmd(kin, JUDGE, "/demo monday")
    messages = to(kin, JUDGE)
    assert messages[-1].startswith("It's Monday 26 Oct, 08:00 in the demo family")
    assert any("Refill the pill organiser" in t for t in messages)
    cmd(kin, JUDGE, "/demo family")
    send(kin, JUDGE, "Done")  # the skill's question was Siti's
    assert to(kin, JUDGE)[-2].startswith("For Mei Ling (Admin):\nSiti has done it")
    assert to(kin, JUDGE)[-1] == "For Siti (Carer):\nThanks, I've told Mei Ling."
    cmd(kin, JUDGE, "/demo monday")
    assert "has already run" in to(kin, JUDGE)[-1]


def test_another_tester_takes_over_and_reset_restores_week0(kin):
    cmd(kin, JUDGE, "/demo admin")
    cmd(kin, OTHER, "/demo family")
    assert "signed out" in to(kin, OTHER)[-1]
    assert send(kin, JUDGE, "hello")["reason"] == "unknown sender"
    send(kin, OTHER, photo="label-metformin")
    assert to(kin, OTHER)[-1].startswith("In the demo, documents come in as Mei Ling")
    cmd(kin, OTHER, "/demo admin")
    send(kin, OTHER, photo="label-metformin")
    before = len(kin.store.active_records(["medication"]))
    send(kin, OTHER, "Confirm")
    assert len(kin.store.active_records(["medication"])) > before
    assert cmd(kin, OTHER, "/demo reset")["reset"] is True
    assert len(kin.store.active_records(["medication"])) == before and not kin.store.open_drafts(
        "mei_ling"
    )
    assert "You're still Mei Ling" in to(kin, OTHER)[-1]


def test_demo_needs_the_demo_mode(tmp_path):
    roster = load_roster(ROOT / "config" / "members.yaml", ADMIN)
    store = Store(tmp_path / "k.sqlite3", tmp_path / "o")
    store.sync_roster(roster)
    sender = FakeSender()
    ctx = Context(store, load_policy(ROOT / "config" / "policy.yaml"), roster, sender, GROUP)
    client = TestClient(create_app(ctx, TOKEN))
    client.headers["Authorization"] = f"Bearer {TOKEN}"
    env = SimpleNamespace(client=client, sender=sender)
    assert send(env, ADMIN, "/demo admin", kind="command")["reason"] == "/demo"
    assert sender.sent[-1][1] == "That command only works in the judge demo."
    assert send(env, "777", "/demo admin", kind="command")["reason"] == "unknown sender"
