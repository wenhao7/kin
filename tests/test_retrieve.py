import json
from pathlib import Path

import pytest

from kin.members import load_roster
from kin.policy import load_policy
from kin.retrieve import Caller, Refused, principal_for, retrieve
from kin.seed import load_fixture_documents
from kin.store import Store

ROOT = Path(__file__).resolve().parents[1]
GROUP = "-100777"
ADMIN, FAMILY, CARER, STRANGER = "111", "222", "333", "999"


@pytest.fixture()
def env(tmp_path):
    roster = load_roster(ROOT / "config" / "members.yaml", ADMIN, f"wei_jie:{FAMILY},siti:{CARER}")
    store = Store(tmp_path / "kin.sqlite3", tmp_path / "originals")
    store.sync_roster(roster)
    load_fixture_documents(store)
    return store, load_policy(ROOT / "config" / "policy.yaml"), roster


def ask(env, user, question="", chat_type="dm", chat_id=None):
    store, policy, roster = env
    chat_id = chat_id or (GROUP if chat_type == "group" else user)
    principal = principal_for(Caller(user, chat_id, chat_type), roster, GROUP)
    return retrieve(store, policy, principal, question)


def by_category(result):
    out = {}
    for r in result.records:
        out.setdefault(r["category"], []).append(r)
    return out


def field_names(result, category):
    return {k for r in by_category(result).get(category, []) for k in r["fields"]}


def test_admin_sees_everything(env):
    res = ask(env, ADMIN)
    assert {"finance", "medical", "medication", "appointments", "observations"} <= set(
        by_category(res)
    )
    assert "diagnoses" in field_names(res, "medical")


def test_family_gets_summary_and_medication_never_finance(env):
    res = ask(env, FAMILY)
    cats = by_category(res)
    assert "finance" not in cats
    assert field_names(res, "medical") <= {"summary", "care_instructions", "source"}
    assert "diagnoses" not in json.dumps(res.records)
    memo = next(
        r for r in cats["medication"] if r["fields"].get("drug") == "Losartan" and r["excerpts"]
    )
    assert memo["excerpts"][0]["text"] == "Plan: start losartan 50 mg once a day in the morning."


def test_carer_gets_schedule_care_instructions_and_own_notes(env):
    res = ask(env, CARER)
    cats = by_category(res)
    assert "finance" not in cats
    assert field_names(res, "medical") <= {"care_instructions", "source"}
    assert field_names(res, "medication") <= {
        "drug",
        "strength",
        "directions",
        "change",
        "times",
        "source",
    }
    assert "pharmacy" not in field_names(res, "medication")
    assert [r["fields"]["date"] for r in cats["observations"]] == ["Sun 25/10"]  # authored by Siti
    advice = [e["text"] for r in cats["medical"] for e in r["excerpts"]]
    assert advice == [
        "Return to the Emergency Department if breathless, chest pain or fever above 38.5°C"
    ]


def test_unknown_sender_gets_nothing(env):
    res = ask(env, STRANGER)
    assert res.records == [] and res.decision == "unknown_member"
    group = ask(env, STRANGER, chat_type="group")
    assert group.records == [] and group.decision == "unknown_member"


def test_spoofed_chats_are_refused(env):
    with pytest.raises(Refused):
        ask(env, FAMILY, chat_type="dm", chat_id=ADMIN)  # "DM" whose chat is someone else's
    with pytest.raises(Refused):
        ask(env, ADMIN, chat_type="group", chat_id="-100123")  # a group Kin doesn't serve
    with pytest.raises(Refused):
        ask(env, ADMIN, chat_type="channel", chat_id="-100777")


def test_group_answers_suit_every_member(env):
    res = ask(env, ADMIN, chat_type="group")  # even the Admin is capped in the group
    cats = by_category(res)
    assert "finance" not in cats and "observations" not in cats
    assert field_names(res, "medical") <= {"care_instructions", "source"}  # carer is in the group
    assert all(not r["excerpts"] or r["category"] != "finance" for r in res.records)
    family = ask(env, FAMILY, chat_type="group")
    assert field_names(family, "medical") <= {"care_instructions", "source"}  # not the summary
    shared = {e["id"] for r in family.records for e in r["excerpts"]}
    assert shared == {"clinic-memo#plan", "discharge-summary#return-advice"}  # approved for all


def test_originals_are_never_returned(env):
    blob = json.dumps(ask(env, CARER, "send me the discharge letter").records)
    assert (
        "originals" not in blob and "storage_ref" not in blob and "Community-acquired" not in blob
    )


def test_every_call_is_audited(env):
    store = env[0]
    ask(env, FAMILY, "what changed?")
    ask(env, STRANGER, "anything?")
    rows = store.audit_for("clinic-memo")
    assert any(r["principal"] == "wei_jie" and r["decision"] == "allowed" for r in rows)
    with store._db() as db:
        assert (
            db.execute("SELECT COUNT(*) FROM audit WHERE decision='unknown_member'").fetchone()[0]
            == 1
        )


def test_week0_seed_holds_the_pre_admission_schedule(tmp_path):
    from kin.seed import load_week0

    roster = load_roster(ROOT / "config" / "members.yaml", ADMIN, f"wei_jie:{FAMILY},siti:{CARER}")
    store = Store(tmp_path / "kin.sqlite3", tmp_path / "originals")
    store.sync_roster(roster)
    loaded = load_week0(store)
    assert loaded["seed"] == [
        "seed:amlodipine",
        "seed:metformin-850",
        "seed:glipizide",
        "seed:atorvastatin",
    ]
    drugs = {
        r["fields"].get("drug")
        for r in retrieve(
            store,
            load_policy(ROOT / "config" / "policy.yaml"),
            principal_for(Caller(CARER, CARER, "dm"), roster, GROUP),
            "",
        ).records
    }
    assert {"Amlodipine", "Losartan", "Metformin", "Glipizide", "Atorvastatin"} <= drugs
