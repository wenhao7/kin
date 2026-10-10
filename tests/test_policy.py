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


def test_embedded_png_is_valid():
    assert _b64_ok()
