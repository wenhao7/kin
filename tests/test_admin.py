"""The Admin's commands without IDs: pickers, plain-language /who_saw, /revoke and chat menus."""

import re

from kin import admin
from kin.telegram import TelegramSender
from tests.test_api import ADMIN, CARER, FAMILY, GROUP, caller
from tests.test_intake import kin, send, to  # noqa: F401

MEMO = "Clinic memo, 26 Jun 2026"
LETTER = "Insurance letter, 24 Oct 2026"


def command(kin, user, text, chat_type="dm"):  # noqa: F811
    return send(kin, user, text, kind="command", chat_type=chat_type)


def keyboard(kin):  # noqa: F811
    return kin.sender.keyboards[-1]


def recall(kin, user, chat_type):  # noqa: F811
    send(kin, user, "Kin, what did Dr Tan change?", chat_type=chat_type)
    body = {"caller": caller(user, chat_type), "question": "what did Dr Tan change?"}
    kin.client.post("/tools/ask", json=body)
    text = "Dr Tan started Losartan 50 mg (Clinic memo, 26 Jun 2026)."
    kin.client.post("/outbound", json={"caller": caller(user, chat_type), "text": text})


def test_each_chat_gets_its_own_command_menu(kin):  # noqa: F811
    assert admin.install_menus(kin.ctx) == []
    menus = kin.sender.menus
    assert menus[ADMIN] == ["reminders", "who_saw", "revoke", "skills", "roles", "help"]
    assert menus[FAMILY] == menus[CARER] == ["skills", "help"]
    assert menus[GROUP] == ["help"]
    command(kin, ADMIN, "/help")
    assert "/who_saw (who has been shown a document)" in to(kin, ADMIN)[-1]
    command(kin, FAMILY, "/help", "group")
    assert "/who_saw" not in to(kin, GROUP)[-1]


def test_who_saw_offers_documents_and_reports_in_plain_words(kin):  # noqa: F811
    recall(kin, FAMILY, "group")
    recall(kin, FAMILY, "dm")
    command(kin, ADMIN, "/who_saw")
    assert to(kin, ADMIN)[-1] == "Which document?"
    assert MEMO in keyboard(kin) and LETTER in keyboard(kin) and keyboard(kin)[-1] == "Cancel"
    send(kin, ADMIN, MEMO)
    report = to(kin, ADMIN)[-1].splitlines()
    assert report[:2] == [MEMO, "The original stays with you; Kin never sends it."]
    assert report[2].startswith("• The group (asked by Wei Jie): ")
    assert report[3].startswith("• Wei Jie, in a direct message: ")
    assert "wei_jie" not in "\n".join(report)
    assert re.match(r"\w{3} \d{2} \w{3} \d{2}:\d{2}$", report[2].split(": ", 1)[1])  # local time
    assert report[-1].startswith("Kin also read it while answering Wei Jie (2)")


def test_who_saw_matches_typed_titles_and_lists_shares(kin):  # noqa: F811
    send(kin, FAMILY, "Has the insurance claim gone through?")
    send(kin, ADMIN, "Just this once")
    command(kin, ADMIN, "/who_saw insurance")
    report = to(kin, ADMIN)[-1]
    assert report.startswith(LETTER) and "• Wei Jie, shared once: " in report
    command(kin, ADMIN, "/who_saw clinic-memo")  # IDs still work
    assert to(kin, ADMIN)[-1].startswith(MEMO)


def test_revoke_lists_active_shares_as_buttons(kin):  # noqa: F811
    command(kin, ADMIN, "/revoke")
    assert to(kin, ADMIN)[-1].startswith("Nothing is shared right now.")
    send(kin, FAMILY, "Was the insurance paid?")
    send(kin, ADMIN, "Yes")
    command(kin, ADMIN, "/revoke")
    assert keyboard(kin) == [f"Wei Jie · {LETTER}", "Cancel"]
    send(kin, ADMIN, "Cancel")
    assert to(kin, ADMIN)[-1] == "Nothing changed." and kin.store.standing_grants("wei_jie")
    command(kin, ADMIN, "/revoke")
    send(kin, ADMIN, f"Wei Jie · {LETTER}")
    assert to(kin, ADMIN)[-1] == f"Done: Kin won't answer Wei Jie from the {LETTER} any more."
    assert not kin.store.standing_grants("wei_jie")


def test_a_picker_goes_first_and_the_waiting_question_comes_back(kin):  # noqa: F811
    send(kin, FAMILY, "How much was the hospital bill?")  # a share question for the Admin
    command(kin, ADMIN, "/who_saw")
    assert to(kin, ADMIN)[-1] == "Which document?"  # not "one more question is waiting"
    send(kin, ADMIN, "Cancel")
    assert to(kin, ADMIN)[-2] == "OK." and "hospital bill" in to(kin, ADMIN)[-1]
    command(kin, ADMIN, "/who_saw")
    assert send(kin, ADMIN, "When is the next appointment?")["action"] == "pass"  # not an option
    send(kin, ADMIN, "No")  # the share question is open again, not lost
    assert to(kin, FAMILY)[-1] == "Mei Ling has decided not to share that."


def test_long_options_get_a_row_each():
    sender, payloads = TelegramSender("token"), []
    sender._call = lambda method, payload: payloads.append(payload) or {"ok": True}
    sender.send("1", "Choose", keyboard=["Yes", "No"])
    sender.send("1", "Choose", keyboard=[MEMO, LETTER, "Cancel"])
    rows = [p["reply_markup"]["keyboard"] for p in payloads]
    assert rows[0] == [[{"text": "Yes"}, {"text": "No"}]]
    assert rows[1] == [[{"text": MEMO}], [{"text": LETTER}], [{"text": "Cancel"}]]
