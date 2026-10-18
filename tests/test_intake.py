"""D3: photo → draft → Admin checks → records, reminders, group post; and sharing."""

import base64
import json
import re
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from kin import intake, schedule
from kin.api import create_app
from kin.context import Context
from kin.fixtures import load_documents
from kin.members import load_roster
from kin.policy import load_policy
from kin.retrieve import Caller, principal_for, retrieve
from kin.seed import load_week0
from kin.store import Store
from tests.test_api import ADMIN, CARER, FAMILY, GROUP, TOKEN, FakeSender

ROOT = Path(__file__).resolve().parents[1]
TZ = "Asia/Singapore"
DOCS = {d["id"]: d for d in load_documents(ROOT / "fixtures")}
HEADINGS = {
    "p1": "Diagnoses; Discharge medications",
    "p2": "Medications before admission; Follow-up",
}


def page(key):
    """What a correct extraction of each fixture photo returns (p1 with the Glipizide misread)."""
    ds = DOCS["discharge-summary"]["fields"]
    if key == "p1":
        after = json.loads(json.dumps(ds["medications_after"]))
        after[3]["drug"] = "Glibpizide"
        fields = {k: ds[k] for k in ("hospital", "admission_date", "discharge_date", "diagnoses")}
        return "discharge_summary", {**fields, "medications_after": after}
    if key == "p2":
        fields = {k: ds[k] for k in ("hospital", "medications_before", "follow_up")}
        return "discharge_summary", fields
    doc = DOCS[key]
    extra = {"doctor": doc["render"]["doctor"]} if key == "appointment-slip" else {}
    return doc["type"], {**doc["fields"], **extra}


class FakeModels:
    """Answers classify / headings / extract / translate calls like the real models would."""

    def __init__(self):
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
        self.translations = 0

    def create(self, model, messages, **kwargs):
        content = messages[-1]["content"]
        if isinstance(content, str):  # translation: system prompt + English text
            self.translations += 1
            kept = re.findall(r"⟦M\d+⟧|\d+(?:[.:]\d+)?", content)
            return _reply("家庭护理更新 " + " ".join(kept))
        prompt = content[0]["text"]
        key = base64.b64decode(content[1]["image_url"]["url"].split(",", 1)[1]).decode()
        doc_type, fields = page(key)
        if prompt.startswith("What kind of document"):
            return _reply(doc_type)
        if prompt.startswith("Which of these section headings"):
            return _reply(HEADINGS.get(key, "none"))
        return _reply(json.dumps({**fields, "uncertain": []}))


def _reply(text):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])


@pytest.fixture()
def kin(tmp_path):
    roster = load_roster(ROOT / "config" / "members.yaml", ADMIN, f"wei_jie:{FAMILY},siti:{CARER}")
    store = Store(tmp_path / "kin.sqlite3", tmp_path / "originals")
    store.sync_roster(roster)
    load_week0(store, tz=TZ)
    sender, models = FakeSender(), FakeModels()
    ctx = Context(
        store=store,
        policy=load_policy(ROOT / "config" / "policy.yaml"),
        roster=roster,
        sender=sender,
        group_chat_id=GROUP,
        tz=TZ,
        client=models,
        model_vision="vision",
        model_super="super",
    )
    client = TestClient(create_app(ctx, TOKEN))
    client.headers["Authorization"] = f"Bearer {TOKEN}"
    return SimpleNamespace(client=client, store=store, sender=sender, ctx=ctx, models=models)


def send(kin, user, text="", kind="text", chat_type="dm", photo=None):
    caller = {
        "platform": "telegram",
        "user_id": user,
        "chat_type": chat_type,
        "chat_id": GROUP if chat_type == "group" else user,
        "message_id": "7",
    }
    body = {"caller": caller, "kind": "photo" if photo else kind, "text": text}
    if photo:
        body |= {"file_b64": base64.b64encode(photo.encode()).decode(), "filename": "photo.jpg"}
    return kin.client.post("/inbound", json=body).json()


def to(kin, chat):
    return [t for c, t in kin.sender.sent if c == chat]


def schedule_drugs(kin):
    return sorted(
        e["label"].split(":")[0] for e in kin.store.active_events() if e["kind"] == "daily"
    )


def test_discharge_intake_end_to_end(kin):
    assert schedule_drugs(kin) == [
        "Amlodipine 5 mg",
        "Atorvastatin 20 mg",
        "Glipizide 5 mg",
        "Losartan",
        "Metformin 850 mg",
        "Metformin 850 mg",
    ]
    send(kin, ADMIN, photo="p1")
    draft_msg = to(kin, ADMIN)[-1]
    assert "Draft from the Discharge summary, 23 Oct 2026" in draft_msg
    assert "“Glibpizide”, which matches no record. Did you mean Glipizide?" in draft_msg
    send(kin, ADMIN, photo="p2")  # page 2 joins the same draft
    assert len(kin.store.open_drafts("mei_ling")) == 1
    assert send(kin, ADMIN, "Glipizide")["reason"] == "prompt answer"
    assert to(kin, ADMIN)[-1].endswith("Confirm to file it and set the reminders?")
    send(kin, ADMIN, "Confirm")

    # Supersession: 850 mg metformin and glipizide reminders stop; the new schedule starts.
    drugs = schedule_drugs(kin)
    assert "Metformin 850 mg" not in drugs and "Glipizide 5 mg" not in drugs
    assert (
        drugs.count("Metformin 500 mg") == 2 and drugs.count("Amoxicillin-clavulanate 625 mg") == 3
    )
    amox = [e for e in kin.store.active_events() if e["label"].startswith("Amoxicillin")]
    assert {e["until"] for e in amox} == {"2026-10-27"}
    carer = to(kin, CARER)[-1]
    assert carer.startswith(
        "New schedule from the Discharge summary, 23 Oct 2026, confirmed by Mei Ling"
    )
    assert "Stop Glipizide" in carer and "Return to the Emergency Department" in carer
    assert "pneumonia" not in carer.lower()

    # Group post only after the Admin approves the exact text.
    assert to(kin, GROUP) == []
    preview = to(kin, ADMIN)[-1]
    assert preview.startswith("Post this to the group?") and "家庭护理更新" in preview
    send(kin, ADMIN, "Post to group")
    en, zh = to(kin, GROUP)
    assert "Metformin 500 mg" in en and "Glipizide: stopped" in en and "Unchanged:" in en
    assert "Return to the Emergency Department" in en  # care instructions suit every member
    for secret in ("pneumonia", "Orchidline", "DEMO-NOT-A-REAL-ID", "Hypertension"):
        assert secret not in en and secret not in zh
    assert zh.startswith("家庭护理更新") and "Metformin" in zh and "⟦" not in zh


def test_slip_conflict_and_appointment_reminder(kin):
    send(kin, ADMIN, photo="p2")
    send(kin, ADMIN, "Confirm")
    send(kin, ADMIN, photo="appointment-slip")
    question = to(kin, ADMIN)[-1]
    assert "2 Nov 2026: this says 10:30 am, the Discharge summary says 9:30 am" in question
    send(kin, ADMIN, "10:30 am (this document)")
    send(kin, ADMIN, "Confirm")
    reminder = next(e for e in kin.store.active_events() if e["kind"] == "once")
    assert reminder["at"] == "2026-11-01T19:00" and reminder["assignee"] == "mei_ling"
    assert reminder["label"].startswith("Tomorrow 10:30 am: Cardiology")


def test_reminders_send_once_even_after_a_restart(kin, tmp_path):
    send(kin, ADMIN, photo="p1")
    send(kin, ADMIN, "Glipizide")
    send(kin, ADMIN, "Confirm")
    eight = datetime(2026, 10, 27, 8, 0, 20, tzinfo=ZoneInfo(TZ))  # a Tuesday: no skill
    before = len(to(kin, CARER))
    assert schedule.tick(kin.ctx, eight) == 1
    message = to(kin, CARER)[-1]
    assert message.startswith("Reminder (08:00):") and "Metformin 500 mg" in message
    assert "Glipizide" not in message
    restarted = replace(kin.ctx, store=Store(kin.store.db_path, kin.store.originals_dir))
    later = eight.replace(minute=3)
    assert schedule.tick(restarted, later) == 0
    assert len(to(kin, CARER)) == before + 1
    after_course = datetime(2026, 10, 28, 8, 30, 5, tzinfo=ZoneInfo(TZ))
    schedule.tick(restarted, after_course)
    events = restarted.store.active_events()
    assert not [e for e in events if e["label"].startswith("Amoxicillin")]


def test_discarded_draft_files_nothing(kin):
    before = len(kin.store.active_records(["medication"]))
    send(kin, ADMIN, photo="label-metformin")
    send(kin, ADMIN, "Discard")
    assert len(kin.store.active_records(["medication"])) == before
    assert to(kin, ADMIN)[-1].startswith("Discarded.")


def test_refill_is_a_labelled_calculation():
    rf = {
        "drug": "Losartan",
        "strength": "50 mg",
        "directions": "Take ONE tablet ONCE a day",
        "quantity": "30 tablets",
        "dispensed": "28 Sep 2026",
    }
    at, label = intake.refill_event(rf, {"refill_days_ahead": 3}, today=date(2026, 10, 1))
    assert at == "2026-10-24T19:00"
    assert "runs out on 27 Oct 2026" in label and "not dispensing advice" in label


def ask(kin, user, chat_type="dm"):
    p = principal_for(
        Caller(user, GROUP if chat_type == "group" else user, chat_type), kin.ctx.roster, GROUP
    )
    return retrieve(kin.store, kin.ctx.policy, p, "insurance claim").records


def test_share_flow_once_standing_revoke_and_no(kin):
    reply = send(kin, FAMILY, "Kin, has the insurance claim gone through?", chat_type="group")
    assert reply["reason"] == "share request: finance"
    assert to(kin, GROUP)[-1] == "I've asked Mei Ling to share that."
    request = to(kin, ADMIN)[-1]
    assert "Wei Jie asked in the group" in request and "Your claim is under assessment" in request

    send(kin, ADMIN, "Just this once")
    answer = to(kin, FAMILY)[-1]
    assert "Your claim is under assessment" in answer
    assert "4,820" not in answer and "DEMO-CLAIM" not in answer  # excerpt, never the original
    assert all(r["category"] != "finance" for r in ask(kin, FAMILY))  # once = one answer

    send(kin, FAMILY, "How much was the hospital bill?")
    send(kin, ADMIN, "Yes")
    shared = [r for r in ask(kin, FAMILY) if r["category"] == "finance"]
    assert shared and set(shared[0]["fields"]) == {"source"} and shared[0]["excerpts"]
    assert all(r["category"] != "finance" for r in ask(kin, FAMILY, "group"))  # never in group
    assert send(kin, FAMILY, "What did the insurer say?")["action"] == "pass"  # no new request
    group = send(kin, FAMILY, "Kin, what did the insurer say?", chat_type="group")
    assert group["reason"] == "share request: finance"
    send(kin, ADMIN, "No")

    send(kin, ADMIN, "/revoke wei_jie insurance-letter", kind="command")
    assert to(kin, ADMIN)[-1] == "Revoked 1 grant(s) for Wei Jie."
    assert all(r["category"] != "finance" for r in ask(kin, FAMILY))

    send(kin, FAMILY, "Was the insurance paid?")
    send(kin, ADMIN, "No")
    assert to(kin, FAMILY)[-1] == "Mei Ling has decided not to share that."


def test_share_reply_is_the_same_without_a_matching_record(kin):
    with kin.store._db() as db:
        db.execute("UPDATE records SET status='superseded' WHERE category='finance'")
    send(kin, FAMILY, "Kin, what did the LPA lawyer say?", chat_type="group")
    assert to(kin, GROUP)[-1] == "I've asked Mei Ling to share that."
    assert "No matching record" in to(kin, ADMIN)[-1]


def test_admin_questions_still_reach_the_agent(kin):
    assert send(kin, ADMIN, "What is the claim status?")["action"] == "pass"  # admin may see it
    send(kin, ADMIN, photo="label-metformin")  # an open draft prompt does not swallow questions
    assert send(kin, ADMIN, "When is the next appointment?")["action"] == "pass"
