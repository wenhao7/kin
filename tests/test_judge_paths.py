"""Paths a judge (or a family) can take off the script: each one once went wrong."""

from types import SimpleNamespace

from kin import flows
from tests.test_api import (
    ADMIN,
    CARER,
    FAMILY,
    GROUP,
    api,  # noqa: F401
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
    assert "Not on the pages so far: Follow-up, Medications before admission." in (
        to(kin, ADMIN)[-1]
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
