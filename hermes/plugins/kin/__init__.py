"""Kin plugin for Hermes: identity, inbound routing, tools and the outbound check.

See docs/05-architecture.md (Hermes ↔ Kin).
Thin by design: every decision is made by the kin service. The caller (Telegram user, chat, chat
type) always comes from the gateway — the session context for tools and replies, the message
source for inbound — and never from a model's arguments. Standard library only.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

logger = logging.getLogger("kin.plugin")

KIN_API_URL = os.environ.get("KIN_API_URL", "http://kin:8765").rstrip("/")
MAX_UPLOAD = 15 * 1024 * 1024
UNAVAILABLE = "Kin is restarting. Please try again in a minute."
OUTBOUND_TIMEOUT = 10  # well inside Hermes' 30 s hook limit, after which a reply would go unchecked


def post(path: str, payload: dict[str, Any], timeout: float = 20) -> dict[str, Any]:
    req = urllib.request.Request(
        f"{KIN_API_URL}{path}",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ.get('KIN_API_TOKEN', '')}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as exc:
        try:
            detail = json.loads(exc.read() or b"{}").get("detail")
        except ValueError:
            detail = None
        return {"error": detail or f"HTTP {exc.code}", "status": exc.code}
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        return {"error": f"kin unavailable: {type(exc).__name__}", "status": 0}


def session_caller() -> dict[str, str]:
    """Caller for tool calls: the gateway's per-turn session context (never tool arguments)."""
    from gateway.session_context import get_session_env

    return {
        "platform": get_session_env("HERMES_SESSION_PLATFORM"),
        "user_id": get_session_env("HERMES_SESSION_USER_ID"),
        "chat_id": get_session_env("HERMES_SESSION_CHAT_ID"),
        "chat_type": get_session_env("HERMES_SESSION_CHAT_TYPE"),
        "message_id": get_session_env("HERMES_SESSION_MESSAGE_ID") or None,
    }


def _tool(path: str, arg: str):
    def handler(args: dict[str, Any], **_: Any) -> str:
        caller = session_caller()
        if caller["platform"] != "telegram" or not caller["user_id"]:
            return json.dumps({"error": "Kin's tools work only in the family's Telegram chats."})
        return json.dumps(post(path, {"caller": caller, arg: str(args.get(arg, ""))}))

    return handler


ASK_SCHEMA = {
    "name": "kin_ask",
    "description": (
        "Look up the family's care records (medicines, appointments, care instructions, notes) "
        "for the person asking. Returns only what this person may see in this chat, with "
        "sources. Use it for every question about the person being cared for; answer only from "
        "what it returns."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "The question, in the asker's words."}
        },
        "required": ["question"],
    },
}
LOOKUP_SCHEMA = {
    "name": "kin_lookup",
    "description": (
        "Look up a public government scheme (grants, subsidies, schemes such as the Home "
        "Caregiving Grant or CHAS) on official websites. Pass only the scheme's name; never "
        "names, ages or anything from the family's records. Returns public pages with links."
    ),
    "parameters": {
        "type": "object",
        "properties": {"topic": {"type": "string", "description": "The scheme's name."}},
        "required": ["topic"],
    },
}
NOTE_SCHEMA = {
    "name": "kin_note",
    "description": (
        "Save a private note for the person asking (visible to them and the family admin)."
    ),
    "parameters": {
        "type": "object",
        "properties": {"text": {"type": "string", "description": "The note to save."}},
        "required": ["text"],
    },
}


def inbound_payload(event: Any) -> dict[str, Any] | None:
    """What the kin service needs from a gateway MessageEvent; None for non-Telegram events."""
    source = getattr(event, "source", None)
    platform = getattr(getattr(source, "platform", None), "value", getattr(source, "platform", ""))
    if source is None or str(platform) != "telegram":
        return None
    kind = getattr(getattr(event, "message_type", None), "value", "text") or "text"
    payload: dict[str, Any] = {
        "caller": {
            "platform": "telegram",
            "user_id": str(source.user_id or ""),
            "chat_id": str(source.chat_id or ""),
            "chat_type": source.chat_type or "",
            "message_id": str(getattr(event, "message_id", "") or "") or None,
        },
        "kind": kind,
        "text": getattr(event, "text", "") or "",
        "reply_to_kin": bool(getattr(event, "reply_to_is_own_message", False)),
    }
    media = list(getattr(event, "media_urls", None) or [])
    if kind in ("photo", "document") and media:
        path = Path(media[0])
        if path.is_file() and path.stat().st_size <= MAX_UPLOAD:
            payload["file_b64"] = base64.b64encode(path.read_bytes()).decode()
            payload["filename"] = path.name
    return payload


async def pre_gateway_dispatch(
    event: Any, gateway: Any = None, session_store: Any = None, **_: Any
):
    payload = inbound_payload(event)
    if payload is None:
        return None
    result = await asyncio.to_thread(post, "/inbound", payload)
    if result.get("reset"):
        _reset_sessions(session_store, payload["caller"]["user_id"])
    if result.get("action") == "pass":
        return {"action": "allow"}
    if "error" in result:
        # Fail closed: without kin there are no boundaries, so Hermes must not answer.
        logger.warning("kin inbound failed: %s", result["error"])
        await _notify(gateway, payload["caller"]["chat_id"], payload["caller"]["chat_type"])
        return {"action": "skip", "reason": "kin unavailable"}
    return {"action": "skip", "reason": result.get("reason", "handled by kin")}


def transform_llm_output(response_text: str = "", platform: str = "", **_: Any) -> str | None:
    """Every final reply goes past Kin before Hermes sends it: Kin withholds anything this chat
    may not see and adds the approved excerpts and sources. None leaves the reply as it is."""
    caller = session_caller()
    if not response_text or "telegram" not in (str(platform), caller["platform"]):
        return None
    if caller["platform"] != "telegram" or not caller["user_id"]:
        logger.warning("Telegram reply without a session caller; not sent")
        return UNAVAILABLE
    result = post(
        "/outbound", {"caller": caller, "text": response_text}, timeout=OUTBOUND_TIMEOUT
    )
    if "error" in result:
        logger.warning("kin outbound check failed: %s", result["error"])
        return UNAVAILABLE  # fail closed: an unchecked reply is not sent
    text = result.get("text") or ""
    return text if text and text != response_text else None


def _reset_sessions(session_store: Any, user_id: str) -> int:
    """Start fresh conversations for this user (DM and group): the judge demo switched role, so
    nothing said as one family member may carry into another. Keys end in ":<user id>"."""
    if session_store is None or not user_id:
        return 0
    done = 0
    try:
        keys = [k for k in list(getattr(session_store, "_entries", {})) if ":telegram:" in k]
        for key in keys:
            if key.endswith(f":{user_id}") and session_store.reset_session(key) is not None:
                done += 1
    except Exception:  # noqa: BLE001 - Kin's reply check still withholds what this role can't see
        logger.warning("could not reset the conversations of a demo tester")
    return done


async def _notify(gateway: Any, chat_id: str, chat_type: str) -> None:
    if chat_type != "dm" or gateway is None:
        return
    try:
        from gateway.config import Platform

        await gateway.adapters[Platform.TELEGRAM].send(chat_id, UNAVAILABLE)
    except Exception:  # noqa: BLE001 - best effort only
        logger.warning("could not tell the user that kin is unavailable")


def register(ctx: Any) -> None:
    ctx.register_tool(
        name="kin_ask", toolset="kin", schema=ASK_SCHEMA, handler=_tool("/tools/ask", "question")
    )
    ctx.register_tool(
        name="kin_note", toolset="kin", schema=NOTE_SCHEMA, handler=_tool("/tools/note", "text")
    )
    ctx.register_tool(
        name="kin_lookup",
        toolset="kin",
        schema=LOOKUP_SCHEMA,
        handler=_tool("/tools/lookup", "topic"),
    )
    ctx.register_hook("pre_gateway_dispatch", pre_gateway_dispatch)
    ctx.register_hook("transform_llm_output", transform_llm_output)
