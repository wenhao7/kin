"""The Hermes plugin's code path against the real kin API (no Hermes, no Telegram)."""

import asyncio
import importlib.util
import json
import sys
import types
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import pytest

from tests.test_api import ADMIN, CARER, FAMILY, GROUP, STRANGER, api  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]


def load_plugin(monkeypatch, client, session):
    ctx = types.ModuleType("gateway.session_context")
    ctx.get_session_env = lambda name, default="": session.get(name, default)
    monkeypatch.setitem(sys.modules, "gateway", types.ModuleType("gateway"))
    monkeypatch.setitem(sys.modules, "gateway.session_context", ctx)
    spec = importlib.util.spec_from_file_location(
        "kin_plugin", ROOT / "hermes/plugins/kin/__init__.py"
    )
    plugin = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(plugin)
    plugin.post = lambda path, payload, timeout=20: client.post(path, json=payload).json()
    return plugin


class Kind(Enum):
    TEXT = "text"
    PHOTO = "photo"
    VOICE = "voice"


@dataclass
class Source:
    user_id: str
    chat_id: str
    chat_type: str
    platform: str = "telegram"


@dataclass
class Event:
    source: Source
    text: str = ""
    message_type: Kind = Kind.TEXT
    message_id: str = "42"
    reply_to_is_own_message: bool = False
    media_urls: list = field(default_factory=list)


def session(user, chat_type="dm"):
    return {
        "HERMES_SESSION_PLATFORM": "telegram",
        "HERMES_SESSION_USER_ID": user,
        "HERMES_SESSION_CHAT_ID": GROUP if chat_type == "group" else user,
        "HERMES_SESSION_CHAT_TYPE": chat_type,
    }


@pytest.fixture()
def registered(monkeypatch, api):  # noqa: F811
    client, store, sender = api

    def make(sess):
        plugin = load_plugin(monkeypatch, client, sess)
        tools, hooks = {}, {}
        ctx = types.SimpleNamespace(
            register_tool=lambda name, toolset, schema, handler: tools.__setitem__(name, handler),
            register_hook=lambda name, fn: hooks.__setitem__(name, fn),
        )
        plugin.register(ctx)
        return plugin, tools, hooks

    return make, store, sender


def dispatch(hooks, event):
    return asyncio.run(hooks["pre_gateway_dispatch"](event, gateway=None, session_store=None))


def test_tool_ignores_identity_in_arguments(registered):
    make, _, _ = registered
    _, tools, _ = make(session(FAMILY))
    out = json.loads(
        tools["kin_ask"]({"question": "insurance claim", "user_id": ADMIN, "as": "mei_ling"})
    )
    assert out["records"] and all(r["category"] != "finance" for r in out["records"])
    _, tools, _ = make(session(ADMIN))
    admin = json.loads(tools["kin_ask"]({"question": "insurance claim"}))
    assert any(r["category"] == "finance" for r in admin["records"])


def test_tool_refuses_outside_telegram(registered):
    make, _, _ = registered
    _, tools, _ = make({"HERMES_SESSION_PLATFORM": "cli"})
    assert "error" in json.loads(tools["kin_ask"]({"question": "medicines"}))


def test_hook_routes_before_the_model(registered, tmp_path):
    make, store, sender = registered
    _, _, hooks = make({})
    assert dispatch(hooks, Event(Source(FAMILY, GROUP, "group"), "lunch?")) == {
        "action": "skip",
        "reason": "group chatter not addressed to Kin",
    }
    assert dispatch(hooks, Event(Source(FAMILY, GROUP, "group"), "Kin, lunch?")) == {
        "action": "allow"
    }
    assert dispatch(hooks, Event(Source(STRANGER, STRANGER, "dm"), "hi"))["action"] == "skip"
    assert (
        dispatch(hooks, Event(Source(CARER, CARER, "dm"), message_type=Kind.VOICE))["action"]
        == "skip"
    )
    photo = tmp_path / "photo.jpg"
    photo.write_bytes(b"\xff\xd8jpeg")
    out = dispatch(
        hooks, Event(Source(ADMIN, ADMIN, "dm"), message_type=Kind.PHOTO, media_urls=[str(photo)])
    )
    assert out == {"action": "skip", "reason": "original stored"}


def test_hook_fails_closed_when_kin_is_down(registered):
    make, _, _ = registered
    plugin, _, hooks = make({})
    plugin.post = lambda path, payload, timeout=20: {"error": "kin unavailable", "status": 0}
    hooks["pre_gateway_dispatch"] = plugin.pre_gateway_dispatch
    assert dispatch(hooks, Event(Source(ADMIN, ADMIN, "dm"), "hi"))["action"] == "skip"
