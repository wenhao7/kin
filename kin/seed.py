"""Load fixture documents into the store as confirmed records (tests, Week 0 state, demo reset).

Records come from `kin.intake.records_for`, the same mapping a confirmed intake uses, applied to
each document's ground truth (fixtures/expected.json describes the same outcome). Approved
excerpts take their audience from the document's `views`. Originals are stored Admin-only. Week 0
also holds the Monday skill the Admin confirmed (`seed.skills`).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from kin.fixtures import ROOT as FIXTURES
from kin.fixtures import load_documents, load_expected
from kin.intake import med_label, records_for
from kin.skills import add_skill
from kin.store import Store

# Week 0: what the family's Kin already held before the discharge paperwork arrived.
WEEK0 = ["clinic-memo", "label-losartan", "insurance-letter"]

# Category of excerpts that come from mixed documents; otherwise the document's category.
EXCERPT_CATEGORY = {
    "medication-changes": "medication",
    "return-advice": "medical",
    "plan": "medication",
}


def _household() -> dict[str, Any]:
    from kin.members import load_roster

    return load_roster(Path("config") / "members.yaml").household


def _active_schedule_drugs(store: Store) -> set[str]:
    return {
        json.loads(r["fields"]).get("drug", "").lower()
        for r in store.active_records(["medication"])
        if r["assignee"]
    }


def load_fixture_documents(
    store: Store, ids: list[str] | None = None, root: Path = FIXTURES, admin: str = "mei_ling"
) -> dict[str, list[str]]:
    """Store originals, approved excerpts and confirmed records; return {doc id: record ids}."""
    docs = {d["id"]: d for d in load_documents(root)}
    household = _household()
    out: dict[str, list[str]] = {}
    for doc_id in ids or list(docs):
        doc = docs[doc_id]
        render = Path(root) / "renders" / f"{doc_id}-p1.png"
        store.add_document(
            doc_id=doc_id,
            kind="photo",
            title=doc["title"],
            categories=doc["categories"],
            uploaded_by=admin,
            content=render.read_bytes() if render.exists() else None,
            suffix=".png",
        )
        excerpt_ids: dict[str, str] = {}
        for name, text in doc["excerpts"].items():
            audience = ["admin"] + [
                role for role, view in doc["views"].items() if f"excerpt:{name}" in view
            ]
            excerpt_ids[name] = store.add_excerpt(
                excerpt_id=f"{doc_id}#{name}",
                document_id=doc_id,
                text=text,
                category=EXCERPT_CATEGORY.get(name, doc["categories"][0]),
                audience=sorted(set(audience)),
                approved_by=admin,
            )
        out[doc_id] = [
            store.add_record(
                category=r["category"],
                fields=r["fields"],
                created_by=r.get("created_by", admin),
                document_id=doc_id,
                excerpt_ids=[excerpt_ids[n] for n in r["excerpts"] if n in excerpt_ids],
                assignee=r.get("assignee"),
            )
            for r in records_for(
                doc["type"],
                doc["fields"],
                household,
                _active_schedule_drugs(store),
                extra={"doctor": doc["render"].get("doctor"), "author": doc.get("author")},
            )
        ]
    return out


def load_week0(
    store: Store, root: Path = FIXTURES, admin: str = "mei_ling", tz: str = "Asia/Singapore"
) -> dict[str, list[str]]:
    """Week 0: the WEEK0 documents, the pre-admission schedule and the Monday skill.

    Seed medication records keep their expected IDs (e.g. `seed:metformin-850`) so intake can
    supersede them; Losartan and the memo come from the clinic-memo document itself.
    """
    out = load_fixture_documents(store, WEEK0, root, admin)
    seeded = []
    for r in load_expected(root)["seed"]["records"]:
        if r["category"] != "medication" or r["source"] == "clinic-memo":
            continue
        fields = {k: r[k] for k in ("drug", "strength", "directions")}
        fields["source"] = "Medications before admission (pharmacy labels)"
        seeded.append(
            store.add_record(
                record_id=r["id"],
                category="medication",
                fields=fields,
                created_by=admin,
                assignee="siti",
            )
        )
    out["seed"] = seeded
    by_drug = {
        json.loads(r["fields"]).get("drug", "").lower(): r["id"]
        for r in store.active_records(["medication"])
        if r["assignee"]
    }
    seed_drug = {r["id"]: r.get("drug", "").lower() for r in load_expected(root)["seed"]["records"]}
    for e in load_expected(root)["seed"]["events"]:
        for rid in e["records"]:
            record_id = rid if store.record(rid) else by_drug.get(seed_drug.get(rid, ""))
            row = store.record(record_id) if record_id else None
            if row is None:
                continue
            f = json.loads(row["fields"])
            store.add_event(
                event_id=f"{e['id']}:{row['id']}",
                record_id=row["id"],
                record_version=row["version"],
                assignee=e["assignee"],
                kind="daily",
                at=e["time"],
                tz=tz,
                label=med_label(f),
            )
    out["skills"] = [add_skill(store, s, tz) for s in load_expected(root)["seed"].get("skills", [])]
    return out
