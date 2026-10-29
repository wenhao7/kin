"""Paths a judge (or a family) can take off the script: each one once went wrong."""

import json
from types import SimpleNamespace

from kin import flows
from kin.intake import parse_date
from tests.test_api import (
    ADMIN,
    CARER,
    FAMILY,
    GROUP,
    api,  # noqa: F401
    caller,
)
from tests.test_demo import JUDGE, cmd
from tests.test_demo import kin as demo_kin  # noqa: F401
from tests.test_intake import kin, send, to  # noqa: F401
from tests.test_plugin import Event, Kind, Source, dispatch, registered  # noqa: F401


def test_every_photo_sent_together_is_read(registered, tmp_path):  # noqa: F811
    make, store, _ = registered
    _, _, hooks = make({})
    pages = []
    for name in ("p1.jpg", "p2.jpg"):
        page = tmp_path / name
        page.write_bytes(b"\xff\xd8" + name.encode())
        pages.append(str(page))
    album = Event(Source(ADMIN, ADMIN, "dm"), message_type=Kind.PHOTO, media_urls=pages)
    assert dispatch(hooks, album)["action"] == "skip"
    assert len(list(store.originals_dir.glob("doc-*.jpg"))) == 2  # not just the first page


def test_replying_to_kin_in_the_group_reaches_kin(registered):  # noqa: F811
    make, _, _ = registered
    _, _, hooks = make({})
    kin_said = SimpleNamespace(from_user=SimpleNamespace(is_bot=True, username="KinAgentBot"))
    reply = Event(Source(FAMILY, GROUP, "group"), "is that the new dose?")
    reply.raw_message = SimpleNamespace(reply_to_message=kin_said)
    assert dispatch(hooks, reply) == {"action": "allow"}
    other = SimpleNamespace(from_user=SimpleNamespace(is_bot=True, username="SomeOtherBot"))
    reply.raw_message = SimpleNamespace(reply_to_message=other)
    assert dispatch(hooks, reply)["action"] == "skip"


def test_will_as_a_verb_is_not_a_legal_question(kin):  # noqa: F811
    assert send(kin, FAMILY, "When will Ah Ma see the cardiologist?")["action"] == "pass"
    assert send(kin, CARER, "What will I give her tonight?")["action"] == "pass"
    assert send(kin, FAMILY, "Where is her will kept?")["reason"] == "share request: legal"


def test_a_waiting_document_is_checked_against_what_was_filed_meanwhile(kin):  # noqa: F811
    send(kin, ADMIN, photo="p2")  # the summary's follow-up says 9:30 am
    send(kin, ADMIN, photo="appointment-slip")  # 10:30 am; waits behind the summary
    waiting = to(kin, ADMIN)[-1]
    assert waiting.startswith("One more question is waiting. First, finish the open one")
    assert kin.sender.keyboards[-1] == ["Confirm", "Discard"]  # the open question's buttons
    send(kin, ADMIN, "Confirm")
    send(kin, ADMIN, "Don't post")
    assert "this says 10:30 am, the Discharge summary says 9:30 am" in to(kin, ADMIN)[-1]


def test_old_buttons_never_reach_the_model(kin):  # noqa: F811
    send(kin, ADMIN, photo="p1")
    send(kin, ADMIN, "Glipizide")
    assert send(kin, ADMIN, "Glipizide")["reason"] == "stale button"  # the same tap again
    send(kin, ADMIN, "Discard")
    assert send(kin, ADMIN, "Confirm")["reason"] == "stale button"


def test_a_draft_says_when_a_page_is_missing(kin):  # noqa: F811
    send(kin, ADMIN, photo="p1")
    assert (
        "Not on the pages so far: Follow-up, Medications before admission." in (to(kin, ADMIN)[-1])
    )
    send(kin, ADMIN, photo="p2")
    assert "Not on the pages so far" not in to(kin, ADMIN)[-1]


def test_a_reset_mid_reading_is_quiet(kin):  # noqa: F811
    assert flows.run_intake(kin.ctx, "doc-gone") is None


def test_only_the_member_played_can_type_an_answer(demo_kin):  # noqa: F811
    cmd(demo_kin, JUDGE, "/demo family")
    demo_kin.store.open_prompt("mei_ling", "draft", "draft-x", [], "Type the correct value.")
    question = "What are the morning medicines now?"
    assert send(demo_kin, JUDGE, question)["action"] == "pass"  # not typed into Mei Ling's draft
    assert demo_kin.store.current_prompt("mei_ling") is not None


def test_demo_monday_says_what_it_sent(demo_kin):  # noqa: F811
    cmd(demo_kin, JUDGE, "/demo admin")
    cmd(demo_kin, JUDGE, "/demo monday")
    assert "pill-organiser skill" in to(demo_kin, JUDGE)[-1]
    send(demo_kin, JUDGE, photo="p1")
    send(demo_kin, JUDGE, "Glipizide")
    send(demo_kin, JUDGE, "Confirm")
    send(demo_kin, JUDGE, "Don't post")
    cmd(demo_kin, JUDGE, "/demo monday")  # the new schedule's 08:00 medicines, no second skill
    assert to(demo_kin, JUDGE)[-1].endswith("Siti got the morning medicines (above).")


def _file(kin, photos, pick="(this document)"):  # noqa: F811
    """Send the pages, answer each question (the name check, or a clash with `pick`), confirm."""
    for p in photos:
        send(kin, ADMIN, photo=p)
    while (options := kin.sender.keyboards[-1]) != ["Confirm", "Discard"]:
        send(kin, ADMIN, next(o for o in options if o == "Glipizide" or o.endswith(pick)))
    send(kin, ADMIN, "Confirm")
    send(kin, ADMIN, "Don't post")


def _ask(kin, user, question):  # noqa: F811
    body = {"caller": caller(user), "question": question}
    return kin.client.post("/tools/ask", json=body).json()["records"]


def _visits(kin):  # noqa: F811
    rows = [json.loads(r["fields"]) for r in kin.store.active_records(["appointments"])]
    return [(str(parse_date(f["date"])), f["time"]) for f in rows]


def test_the_june_plan_outlives_the_discharge_summary(kin):  # noqa: F811
    _file(kin, ["p1", "p2"])  # its "Losartan · Unchanged" replaces the memo's schedule
    memo = next(
        r
        for r in _ask(kin, FAMILY, "What happened at Ah Ma's June review with Dr Tan?")
        if r["category"] == "medical" and r["fields"]["source"].startswith("Clinic memo")
    )
    assert memo["fields"]["medication_changes"][0]["drug"] == "Losartan"
    assert "notes" not in memo["fields"]  # the clinical notes stay with the Admin
    reply = "Dr Tan started Losartan 50 mg at the review (Clinic memo, 26 Jun 2026)."
    text = kin.client.post("/outbound", json={"caller": caller(FAMILY), "text": reply}).json()
    assert "“Plan: start losartan 50 mg once a day in the morning.” (Clinic memo" in text["text"]
    assert "Discharge summary" not in text["text"]  # not a quote from another document
    _ask(kin, ADMIN, "What happened at Ah Ma's June review with Dr Tan?")
    reply = (
        "In June\u202f2026 her blood pressure was 152/88 on amlodipine 5 mg; Losartan was started."
    )
    text = kin.client.post("/outbound", json={"caller": caller(ADMIN), "text": reply}).json()
    assert "Amlodipine · 5 mg" not in text["text"] and "Plan: start losartan" in text["text"]


def test_a_follow_up_is_an_appointment_the_family_can_see(kin):  # noqa: F811
    _file(kin, ["p1", "p2"])
    seen = [r["fields"] for r in _ask(kin, FAMILY, "When is the next appointment?")]
    assert [(f["date"], f["time"]) for f in seen if "follow_up" in f] == [("2 Nov 2026", "9:30 am")]
    _file(kin, ["appointment-slip"])  # 10:30 am, the slip's own time
    assert "Replaced 1 earlier appointment; its reminder stops." in "\n".join(to(kin, ADMIN))
    assert _visits(kin) == [("2026-11-02", "10:30 am")]  # one visit, not two
    reminders = [e["label"] for e in kin.store.active_events() if e["label"].startswith("Tomorrow")]
    assert len(reminders) == 1 and "10:30 am" in reminders[0]


def test_a_summary_after_the_slip_adds_no_second_appointment(kin):  # noqa: F811
    _file(kin, ["appointment-slip"])
    _file(kin, ["p1", "p2"], pick="(Appointment slip)")  # keep the slip's 10:30 am
    assert _visits(kin) == [("2026-11-02", "10:30 am")]
