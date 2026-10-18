from pathlib import Path

from kin.members import load_roster, parse_member_ids
from kin.policy import load_policy

ROOT = Path(__file__).resolve().parents[1]


def test_default_roster_is_valid():
    roster = load_roster(ROOT / "config" / "members.yaml", "111", "wei_jie:222")
    roles = load_policy(ROOT / "config" / "policy.yaml").roles
    assert roster.validate(roles, ["en", "zh"]) == []
    assert roster.by_telegram_id("111").role == "admin"
    assert roster.by_telegram_id("222").id == "wei_jie"


def test_unknown_user_gets_no_role_and_never_admin():
    roster = load_roster(ROOT / "config" / "members.yaml", "111", "")
    guest = roster.by_telegram_id("999")
    assert guest.role is None and guest.id == "guest:999"
    assert load_roster(ROOT / "config" / "members.yaml", "", "").by_telegram_id("").role != "admin"


def test_member_ids_parsing_and_duplicate_mapping():
    assert parse_member_ids(" wei_jie:222, siti:333 ,bad,") == {"wei_jie": "222", "siti": "333"}
    roster = load_roster(ROOT / "config" / "members.yaml", "111", "wei_jie:111")
    roles = load_policy(ROOT / "config" / "policy.yaml").roles
    assert any("more than one member" in p for p in roster.validate(roles, ["en", "zh"]))


def test_a_telegram_account_can_move_between_members(tmp_path):
    from kin.store import Store

    store = Store(tmp_path / "kin.sqlite3", tmp_path / "originals")
    for mapping in ("wei_jie:555", "siti:555", "wei_jie:555"):  # re-mapped between demo takes
        store.sync_roster(load_roster(ROOT / "config" / "members.yaml", "111", mapping))
        ids = {m["id"]: m["telegram_id"] for m in store.members()}
        assert ids[mapping.split(":")[0]] == "555" and list(ids.values()).count("555") == 1
