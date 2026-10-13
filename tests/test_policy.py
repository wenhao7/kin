from pathlib import Path

from kin.policy import load_policy
from kin.setup_check import _b64_ok

ROOT = Path(__file__).resolve().parents[1]


def test_default_policy_is_complete():
    p = load_policy(ROOT / "config" / "policy.yaml")
    assert p.validate() == []
    assert p.level("family", "finance") == ("none", None)
    assert p.level("carer", "tasks") == ("write", "own")
    assert p.level("admin", "legal") == ("write", None)
    assert "finance" in p.share_request_on_none


def test_group_level_is_lowest_member_level():
    p = load_policy(ROOT / "config" / "policy.yaml")
    roster = ["admin", "family", "carer"]
    assert p.group_level("medical", roster) == "summary"
    assert p.group_level("medication", roster) == "read"
    assert p.group_level("finance", roster) == "none"
    assert p.group_level("tasks", roster) == "none"  # carer's write:own counts as none
    assert p.group_level("medication", roster + ["viewer"]) == "read"
    assert p.group_level("medical", roster + ["viewer"]) == "none"
    assert p.group_level("medical", []) == "none"
    assert p.group_level("medical", ["stranger"]) == "none"


def test_unknown_qualifier_is_reported():
    p = load_policy(ROOT / "config" / "policy.yaml")
    p.matrix["notes"]["family"] = "read:everyone"
    assert any("unknown qualifier" in m for m in p.validate())


def test_embedded_png_is_valid():
    assert _b64_ok()
