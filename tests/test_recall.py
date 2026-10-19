"""D4: recall with approved excerpts, the outbound re-check, and the public-only lookup."""

import json
from pathlib import Path

import yaml

from kin.answer import WITHHELD
from kin.fixtures import load_expected
from kin.seed import load_fixture_documents
from tests.test_api import ADMIN, CARER, FAMILY, GROUP, STRANGER, caller
from tests.test_intake import kin, send, to  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = load_expected(ROOT / "fixtures")
LOCALE = yaml.safe_load((ROOT / "locale/sg/locale.yaml").read_text(encoding="utf-8"))
PLAN = "“Plan: start losartan 50 mg once a day in the morning.” (Clinic memo, 26 Jun 2026)"
HCG = "https://www.aic.sg/Financial-Assistance/Home-Caregiving-Grant"


def turn(kin, user, question, chat_type="dm"):  # noqa: F811
    """One agent turn: the message passes to Hermes, which calls kin_ask."""
    assert send(kin, user, question, chat_type=chat_type)["action"] == "pass"
    body = {"caller": caller(user, chat_type), "question": question}
    return kin.client.post("/tools/ask", json=body).json()


def reply(kin, user, text, chat_type="dm"):  # noqa: F811
    body = {"caller": caller(user, chat_type), "text": text}
    return kin.client.post("/outbound", json=body).json()


def test_group_recall_gets_the_month_minus_4_change_with_its_excerpt(kin):  # noqa: F811
    case = EXPECTED["recall"][0]
    found = turn(kin, FAMILY, case["question"], "group")
    assert "Ah Ma" in found["rules"] and "Mdm Tan Siew Lan" in found["rules"]
    assert "Mei Ling can send it" in found["rules"]
    assert "152/88" not in json.dumps(found["records"])
    answer = "Dr Tan started Losartan 50 mg once a day in the morning (Clinic memo, 26 Jun 2026)."
    out = reply(kin, FAMILY, answer, "group")
    assert out["decision"] == "sent" and out["text"] == f"{answer}\n\n{PLAN}"
    for word in case["answer_includes"]:
        assert word.lower() in out["text"].lower()
    shown = kin.store.audit_for("clinic-memo")  # /who_saw clinic-memo lists the answer
    assert shown[0]["action"] == "answer" and shown[0]["chat_type"] == "group"


def test_citation_markers_never_reach_the_chat(kin):  # noqa: F811
    turn(kin, FAMILY, "Kin, what did Dr Tan change?", "group")
    marked = 'Dr Tan started Losartan 50 mg【{"id":"rec-18551cb6ff"}】 (Clinic memo, 26 Jun 2026).'
    out = reply(kin, FAMILY, marked, "group")["text"]
    assert out.startswith("Dr Tan started Losartan 50 mg (Clinic memo, 26 Jun 2026).")
    assert "rec-" not in out and "【" not in out


def test_quoted_excerpts_are_not_repeated_and_uncited_ones_not_added(kin):  # noqa: F811
    turn(kin, FAMILY, "Kin, what did Dr Tan change?", "group")
    quoted = "The memo says: “Plan: start losartan 50 mg once a day in the morning.”"
    assert reply(kin, FAMILY, quoted, "group")["text"] == quoted
    turn(kin, FAMILY, "Kin, when is the next appointment?", "group")
    plain = "I don't know: no appointment is on file yet."
    assert reply(kin, FAMILY, plain, "group")["text"] == plain


def test_excerpts_come_only_from_this_turns_records(kin):  # noqa: F811
    turn(kin, FAMILY, "What did Dr Tan change?")
    send(kin, FAMILY, "thanks")  # a new turn begins; it called no tool
    text = "You're welcome. Losartan was started in June."
    assert reply(kin, FAMILY, text)["text"] == text


def test_reply_with_something_this_chat_may_not_see_is_withheld(kin):  # noqa: F811
    note = "The memo also says: Blood pressure 152/88 on amlodipine 5 mg."
    turn(kin, FAMILY, "What else did the memo say?")
    assert reply(kin, FAMILY, note) == {"text": WITHHELD, "decision": "withheld"}
    turn(kin, ADMIN, "What else did the memo say?")
    assert reply(kin, ADMIN, note)["text"].startswith(note)  # the Admin may see the notes
    insurer = "Kin, Orchidline Assurance is still assessing it."
    assert reply(kin, ADMIN, insurer, "group")["text"] == WITHHELD  # the group may not
    assert reply(kin, CARER, "Return to the Emergency Department if breathless")["decision"] == (
        "sent"
    )  # shown to the carer as a care instruction
    assert reply(kin, STRANGER, "anything")["text"] == WITHHELD


def test_echoing_the_question_does_not_reveal_a_hidden_record(kin):  # noqa: F811
    load_fixture_documents(kin.store, ["discharge-summary"])  # diagnoses: Admin-only fields
    turn(kin, FAMILY, "Does Ah Ma have hypertension?")
    echo = "I don't know whether Ah Ma has hypertension; her doctor can tell you."
    assert reply(kin, FAMILY, echo)["text"] == echo  # same reply as for a condition not on file
    turn(kin, FAMILY, "What did the doctor say?")
    assert reply(kin, FAMILY, "She has hypertension.")["text"] == WITHHELD


def test_intake_records_carry_their_printed_lines_as_excerpts(kin):  # noqa: F811
    send(kin, ADMIN, photo="p1")
    send(kin, ADMIN, photo="p2")
    send(kin, ADMIN, "Glipizide")
    send(kin, ADMIN, "Confirm")
    turn(kin, FAMILY, "Kin, what is the metformin dose now?", "group")
    out = reply(kin, FAMILY, "Metformin is now 500 mg twice a day (Discharge summary).", "group")
    assert out["text"].endswith(
        "“Metformin · 500 mg · 1 tablet twice a day with breakfast and dinner · "
        "Dose reduced from 850 mg” (Discharge summary, 23 Oct 2026)"
    )


class FakeSearch:
    def __init__(self):
        self.calls = []

    def search(self, query, **kwargs):
        self.calls.append((query, kwargs))
        return {
            "results": [
                {"title": "Home Caregiving Grant (HCG) | AIC", "url": HCG, "content": "Up to $600"},
                {"title": "Elsewhere", "url": "https://example.com/hcg", "content": "Not listed"},
            ]
        }


def lookup(kin, user, topic, chat_type="dm"):  # noqa: F811
    body = {"caller": caller(user, chat_type), "topic": topic}
    return kin.client.post("/tools/lookup", json=body).json()


def test_lookup_sends_only_the_scheme_name_to_allow_listed_sites(kin):  # noqa: F811
    kin.ctx.locale, kin.ctx.search = LOCALE, FakeSearch()
    case = EXPECTED["lookup"]
    assert send(kin, FAMILY, case["question"], chat_type="group")["action"] == "pass"
    topic = "Home Caregiving Grant for Ah Ma, Tan Siew Lan, DEMO-NOT-A-REAL-ID, Bedok"
    found = lookup(kin, FAMILY, topic, "group")
    query, kwargs = kin.ctx.search.calls[0]
    assert query == "Home Caregiving Grant: eligibility, amount and how to apply"
    assert not any(secret in query for secret in case["query_excludes"])
    assert kwargs["include_domains"] == LOCALE["lookup_allow_domains"]
    assert [r["url"] for r in found["results"]] == [HCG]  # other domains are dropped
    assert "Don't say whether anyone in the family qualifies" in found["rules"]
    text = "The Home Caregiving Grant pays up to $600 a month; AIC decides who qualifies."
    out = reply(kin, FAMILY, text, "group")
    assert out["text"] == f"{text}\n\nSource: Home Caregiving Grant (HCG) | AIC, {HCG}"
    with kin.store._db() as db:
        logged = db.execute("SELECT query FROM audit WHERE action='lookup'").fetchall()
    assert [r["query"] for r in logged] == [query]  # the audit shows exactly what left Kin


def test_lookup_refuses_anything_but_a_listed_scheme(kin):  # noqa: F811
    kin.ctx.locale, kin.ctx.search = LOCALE, FakeSearch()
    found = lookup(kin, FAMILY, "Ah Ma's blood pressure readings")
    assert "error" in found and "Home Caregiving Grant" in found["schemes"]
    assert lookup(kin, STRANGER, "CHAS")["error"].startswith("Kin answers only")
    assert kin.ctx.search.calls == []
    assert lookup(kin, CARER, "Is the helper levy lower?")["scheme"] == (
        "Migrant Domestic Worker Levy Concession"
    )


def test_asking_for_an_original_gets_a_fixed_reply(kin):  # noqa: F811
    from kin.inbound import ORIGINALS_REPLY

    for user, text, chat_type in [
        (CARER, "Please send me the discharge letter.", "dm"),
        (CARER, "Kin, can you send a photo of the medicine label?", "group"),
        (ADMIN, "Forward me the discharge summary pdf", "dm"),
    ]:
        assert send(kin, user, text, chat_type=chat_type)["reason"] == "original requested"
        assert to(kin, user if chat_type == "dm" else GROUP)[-1] == ORIGINALS_REPLY
    for text in ("Can you send me the schedule?", "What does the discharge summary say?"):
        assert send(kin, CARER, text)["action"] == "pass"  # questions about it still go to Kin
    family = send(kin, FAMILY, "Send me the insurance letter")  # a share request comes first
    assert family["reason"] == "share request: finance"
