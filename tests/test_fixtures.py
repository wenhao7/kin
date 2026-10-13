import json
import re
from pathlib import Path

import pytest
import yaml

from kin.fixtures import load_documents, load_expected, strings
from kin.members import load_roster
from kin.policy import load_policy

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "fixtures"
DOCS = load_documents(FIX)
BY_ID = {d["id"]: d for d in DOCS}
LOCALE = yaml.safe_load((ROOT / "locale" / "sg" / "locale.yaml").read_text(encoding="utf-8"))
POLICY = load_policy(ROOT / "config" / "policy.yaml")


def test_minimum_fixture_is_complete():
    types = LOCALE["document_types"]
    assert len(DOCS) == 8 and len(BY_ID) == 8
    assert sum(d["photograph"] for d in DOCS) == 4
    assert sum(d["type"] == "medication_label" for d in DOCS) == 3
    for d in DOCS:
        assert d["type"] in types, d["id"]
        assert set(types[d["type"]]) <= set(d["fields"]), d["id"]
        assert d["categories"] and set(d["categories"]) <= set(POLICY.categories), d["id"]


def test_every_field_and_excerpt_is_printed():
    pytest.importorskip("jinja2")
    from kin.fixtures import printed_text, render_html

    for d in DOCS:
        text = printed_text(render_html(d, FIX))
        for value in [*strings(d["fields"]), *d["excerpts"].values()]:
            assert " ".join(value.split()) in text, f"{d['id']}: {value!r} not printed"


def test_only_placeholder_identifiers():
    blob = "\n".join(
        p.read_text(encoding="utf-8")
        for p in [*FIX.glob("documents/*.json"), FIX / "expected.json", *FIX.glob("templates/*")]
    )
    assert not re.search(r"\b[STFGM]\d{7}[A-Z]\b", blob), "NRIC-like identifier"
    assert not re.search(r"\b[3689]\d{3}[ -]?\d{4}\b", blob), "dialable Singapore phone number"
    for code in re.findall(r"Singapore (\d{6})", blob):
        assert code.startswith("000"), f"real-looking postal code {code}"
    for ref in re.findall(r"\b[A-Z]+-[A-Z]+-\d{4}\b", blob):
        assert ref.startswith("DEMO-"), ref


def test_views_follow_policy_and_originals_stay_admin_only():
    for d in DOCS:
        assert "original" in d["views"]["admin"]
        for role in ("family", "carer"):
            view = d["views"][role]
            assert "original" not in view, f"{d['id']}: original visible to {role}"
            if all(POLICY.level(role, c)[0] == "none" for c in d["categories"]):
                assert view == [], f"{d['id']}: {role} has no access to {d['categories']}"
            for item in view:
                name = item.removeprefix("excerpt:")
                pool = (
                    d["excerpts"] if item.startswith("excerpt:") else {**d["fields"], "fields": 1}
                )
                assert name in pool, f"{d['id']}: unknown view item {item!r}"


def test_expected_outcomes_reference_the_fixture():
    expected = load_expected(FIX)
    member_ids = {m.id for m in load_roster(ROOT / "config" / "members.yaml").members}
    seed_ids = {r["id"] for r in expected["seed"]["records"]}
    blob = json.dumps(expected)
    for doc_id, excerpt in re.findall(r'"([a-z-]+)#([a-z_\-\[\]0-9]+)"', blob):
        assert doc_id in BY_ID, doc_id
        name = excerpt.split("[")[0]
        assert name in BY_ID[doc_id]["excerpts"] or name in BY_ID[doc_id]["fields"], excerpt
    for case in expected["intake"]:
        assert case["document"] in BY_ID and case["sender"] in member_ids
        for s in case.get("result", {}).get("supersedes", []):
            assert s["old"] in seed_ids
    for case in [*expected["recall"], *expected["denied"], expected["share"], expected["lookup"]]:
        assert case["asker"] in member_ids | {"unknown"}
    assert len(expected["privacy_tests"]) == 9
