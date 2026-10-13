"""Load fixture documents into the store as confirmed records (tests, Week 0 state, demo reset).

`records_from_fixture` maps one document's ground truth to the records an Admin-confirmed intake
would produce (fixtures/expected.json describes the same outcome). Approved excerpts take their
audience from the document's `views`. Originals are stored Admin-only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from kin.fixtures import ROOT as FIXTURES
from kin.fixtures import load_documents, load_expected
from kin.store import Store

# Week 0: what the family's Kin already held before the discharge paperwork arrived.
WEEK0 = ["clinic-memo", "label-losartan", "insurance-letter"]

# Category of excerpts that come from mixed documents; otherwise the document's category.
EXCERPT_CATEGORY = {
    "medication-changes": "medication",
    "return-advice": "medical",
    "plan": "medication",
}


def _source(doc: dict[str, Any]) -> str:
    return f"{doc['title']}, {doc['date']}"


def records_from_fixture(doc: dict[str, Any]) -> list[dict[str, Any]]:
    f, src, t = doc["fields"], _source(doc), doc["type"]
    if t == "discharge_summary":
        meds = [
            {
                "category": "medication",
                "fields": {
                    "drug": m["drug"],
                    "strength": m["strength"],
                    "directions": m["directions"],
                    "change": m["change"],
                    "source": src,
                },
                "excerpts": ["medication-changes"],
                "assignee": "siti",
            }
            for m in f["medications_after"]
        ]
        medical = {
            "category": "medical",
            "fields": {
                "summary": f"Hospital stay {f['admission_date']} to {f['discharge_date']}; "
                "medication changes on discharge.",
                "diagnoses": f["diagnoses"],
                "care_instructions": [f["follow_up"][2]],
                "source": src,
            },
            "excerpts": ["return-advice"],
        }
        return [medical, *meds]
    if t == "medication_label":
        return [
            {
                "category": "medication",
                "fields": {**{k: f[k] for k in ("drug", "strength", "directions")}, "source": src},
                "excerpts": [],
                "assignee": "siti",
            },
            {
                "category": "medication",
                "fields": {
                    "drug": f["drug"],
                    "quantity": f["quantity"],
                    "dispensed": f["dispensed_date"],
                    "pharmacy": f["pharmacy"],
                    "source": src,
                },
                "excerpts": [],
            },
        ]
    if t == "appointment_slip":
        return [
            {
                "category": "appointments",
                "fields": {**f, "doctor": doc["render"]["doctor"], "source": src},
                "excerpts": [],
                "assignee": "mei_ling",
            }
        ]
    if t == "clinic_memo":
        change = f["medication_changes"][0]
        return [
            {
                "category": "medical",
                "fields": {
                    "summary": f"Cardiology review, {f['date']}.",
                    "notes": f["notes"],
                    "source": src,
                },
                "excerpts": [],
            },
            {
                "category": "medication",
                "fields": {
                    "drug": change["drug"],
                    "change": f"{change['change']} on {f['date']} ({f['clinician']})",
                    "directions": change["dose"],
                    "source": src,
                },
                "excerpts": ["plan"],
            },
        ]
    if t == "insurance_letter":
        return [{"category": "finance", "fields": {**f, "source": src}, "excerpts": ["status"]}]
    if t == "carer_note":
        return [
            {
                "category": "observations",
                "fields": {"date": f["date"], "observations": f["observations"], "source": src},
                "excerpts": [],
                "created_by": doc.get("author", "siti"),
            }
        ]
    raise ValueError(f"no mapping for {t}")


def load_fixture_documents(
    store: Store, ids: list[str] | None = None, root: Path = FIXTURES, admin: str = "mei_ling"
) -> dict[str, list[str]]:
    """Store originals, approved excerpts and confirmed records; return {doc id: record ids}."""
    docs = {d["id"]: d for d in load_documents(root)}
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
                excerpt_ids=[excerpt_ids[n] for n in r["excerpts"]],
                assignee=r.get("assignee"),
            )
            for r in records_from_fixture(doc)
        ]
    return out


def load_week0(
    store: Store, root: Path = FIXTURES, admin: str = "mei_ling"
) -> dict[str, list[str]]:
    """Week 0: the WEEK0 documents plus the pre-admission schedule from fixtures/expected.json.

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
    return out
