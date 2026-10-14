import base64
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from kin.api import create_app
from kin.context import Context
from kin.inbound import VOICE_REPLY
from kin.members import load_roster
from kin.policy import load_policy
from kin.seed import load_fixture_documents
from kin.store import Store

ROOT = Path(__file__).resolve().parents[1]
GROUP, ADMIN, FAMILY, CARER, STRANGER = "-100777", "111", "222", "333", "999"
TOKEN = "test-token"


class FakeSender:
    def __init__(self):
        self.sent = []

    def send(self, chat_id, text, reply_to=None, keyboard=None):
        self.sent.append((chat_id, text))
        return {"ok": True, "error": None}

    def username(self):
        return "KinAgentBot"


@pytest.fixture()
def api(tmp_path):
    roster = load_roster(ROOT / "config" / "members.yaml", ADMIN, f"wei_jie:{FAMILY},siti:{CARER}")
    store = Store(tmp_path / "kin.sqlite3", tmp_path / "originals")
    store.sync_roster(roster)
    load_fixture_documents(store)
    sender = FakeSender()
    ctx = Context(
        store=store,
        policy=load_policy(ROOT / "config" / "policy.yaml"),
        roster=roster,
        sender=sender,
        group_chat_id=GROUP,
    )
    app = create_app(ctx, TOKEN)
    client = TestClient(app)
    client.headers["Authorization"] = f"Bearer {TOKEN}"
    return client, store, sender


def caller(user, chat_type="dm", chat_id=None):
    return {
        "platform": "telegram",
        "user_id": user,
        "chat_id": chat_id or (GROUP if chat_type == "group" else user),
        "chat_type": chat_type,
        "message_id": "42",
    }


def inbound(client, user, kind="text", text="", chat_type="dm", **extra):
    body = {"caller": caller(user, chat_type), "kind": kind, "text": text, **extra}
    return client.post("/inbound", json=body).json()


def test_token_is_required(api):
    client, _, _ = api
    body = {"caller": caller(ADMIN), "question": "medicines?"}
    assert (
        client.post("/tools/ask", json=body, headers={"Authorization": "Bearer wrong"}).status_code
        == 401
    )
    assert client.post("/tools/ask", json=body, headers={"Authorization": ""}).status_code == 401


def test_group_chatter_is_ignored_and_addressed_text_passes(api):
    client, _, sender = api
    assert inbound(client, FAMILY, text="see you at lunch", chat_type="group")["action"] == "skip"
    assert inbound(client, FAMILY, text="Kin, what changed?", chat_type="group")["action"] == "pass"
    assert (
        inbound(client, FAMILY, text="thanks @KinAgentBot", chat_type="group")["action"] == "pass"
    )
    assert (
        inbound(client, FAMILY, text="ok", chat_type="group", reply_to_kin=True)["action"] == "pass"
    )
    assert inbound(client, FAMILY, text="what changed?")["action"] == "pass"  # DMs always reach Kin
    assert sender.sent == []


def test_unknown_senders_and_chats_are_skipped_silently(api):
    client, _, sender = api
    assert inbound(client, STRANGER, text="hello")["action"] == "skip"
    assert inbound(client, STRANGER, text="Kin, medicines?", chat_type="group")["action"] == "skip"
    other_group = {"caller": caller(ADMIN, "group", "-100123"), "kind": "text", "text": "Kin?"}
    assert client.post("/inbound", json=other_group).json()["action"] == "skip"
    assert sender.sent == []


def test_voice_notes_get_the_fixed_reply(api):
    client, _, sender = api
    assert inbound(client, CARER, kind="voice")["action"] == "skip"
    assert sender.sent == [(CARER, VOICE_REPLY)]


def test_only_the_admin_dm_stores_documents(api):
    client, store, sender = api
    photo = base64.b64encode(b"\xff\xd8fake-jpeg").decode()
    r = inbound(
        client, FAMILY, kind="photo", file_b64=photo, filename="label.jpg", chat_type="group"
    )
    assert (
        r["reason"] == "documents go through the Admin" and "to Mei Ling by" in sender.sent[-1][1]
    )
    r = inbound(client, ADMIN, kind="photo", file_b64=photo, filename="label.jpg")
    assert r["reason"] == "original stored" and sender.sent[-1][1] == "Saved privately."
    stored = list((store.originals_dir).glob("doc-*.jpg"))
    assert len(stored) == 1 and stored[0].read_bytes() == b"\xff\xd8fake-jpeg"


def test_commands_belong_to_kin_and_admin_ones_are_refused(api):
    client, _, sender = api
    inbound(client, FAMILY, kind="command", text="/who_saw clinic-memo")
    assert sender.sent[-1][1].startswith("That command is for")
    inbound(
        client, FAMILY, kind="command", text="/model gpt"
    )  # a Hermes command never reaches Hermes
    assert "/help" in sender.sent[-1][1]
    client.post("/tools/ask", json={"caller": caller(FAMILY), "question": "what changed?"})
    inbound(client, ADMIN, kind="command", text="/who_saw clinic-memo", chat_type="group")
    assert sender.sent[-1] == (GROUP, "Ask me that in our direct chat.")  # never in the group
    inbound(client, ADMIN, kind="command", text="/who_saw clinic-memo")
    assert "wei_jie" in sender.sent[-1][1]


def test_tool_identity_comes_only_from_caller(api):
    client, _, _ = api
    forged = {
        "caller": caller(FAMILY),
        "question": "insurance claim",
        "principal": "mei_ling",
        "as": ADMIN,
    }
    records = client.post("/tools/ask", json=forged).json()["records"]
    assert records and all(r["category"] != "finance" for r in records)
    spoofed = {
        "caller": caller(FAMILY, "dm", ADMIN),
        "question": "claim",
    }  # DM chat of someone else
    assert client.post("/tools/ask", json=spoofed).status_code == 403
    not_telegram = {"caller": {**caller(ADMIN), "platform": "cli"}, "question": "claim"}
    assert client.post("/tools/ask", json=not_telegram).status_code == 403


def test_notes_are_own_and_viewers_cannot_write(api):
    client, _, _ = api
    saved = client.post(
        "/tools/note", json={"caller": caller(CARER), "text": "Bought more strips"}
    ).json()
    assert saved["saved"]
    family = client.post("/tools/ask", json={"caller": caller(FAMILY), "question": "strips"}).json()
    assert "Bought more strips" not in str(family["records"])
    carer = client.post("/tools/ask", json={"caller": caller(CARER), "question": "strips"}).json()
    assert "Bought more strips" in str(carer["records"])
    stranger = client.post("/tools/note", json={"caller": caller(STRANGER), "text": "hi"}).json()
    assert stranger["saved"] is False
