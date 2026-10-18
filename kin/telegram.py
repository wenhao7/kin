"""Messages Kin starts itself, sent through the Telegram Bot API (Hermes only polls).

Sending with the same bot token alongside Hermes' `getUpdates` is allowed by Telegram.
"""

from __future__ import annotations

from typing import Any

import httpx


class TelegramSender:
    def __init__(self, token: str, timeout: float = 15):
        self._base = f"https://api.telegram.org/bot{token}"
        self._timeout = timeout
        self._username: str | None = None

    def _call(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            r = httpx.post(f"{self._base}/{method}", json=payload, timeout=self._timeout)
            data = r.json()
        except (httpx.HTTPError, ValueError) as exc:
            return {"ok": False, "description": type(exc).__name__}
        return data

    def send(
        self,
        chat_id: str,
        text: str,
        reply_to: str | None = None,
        keyboard: list[str] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
        if reply_to:
            payload["reply_parameters"] = {
                "message_id": int(reply_to),
                "allow_sending_without_reply": True,
            }
        if keyboard:
            short = len(keyboard) <= 3 and all(len(k) <= 20 for k in keyboard)
            rows = [keyboard] if short else [[k] for k in keyboard]  # long labels: one per row
            payload["reply_markup"] = {
                "keyboard": [[{"text": k} for k in row] for row in rows],
                "one_time_keyboard": True,
                "resize_keyboard": True,
            }
        data = self._call("sendMessage", payload)
        return {"ok": bool(data.get("ok")), "error": data.get("description")}

    def set_commands(self, commands: list[tuple[str, str]], chat_id: str) -> dict[str, Any]:
        """This chat's command menu; it outranks the broader menus Hermes registers."""
        data = self._call(
            "setMyCommands",
            {
                "commands": [{"command": c, "description": d} for c, d in commands],
                "scope": {"type": "chat", "chat_id": int(chat_id)},
            },
        )
        return {"ok": bool(data.get("ok")), "error": data.get("description")}

    def username(self) -> str:
        if self._username is None:
            data = self._call("getMe", {})
            self._username = (
                (data.get("result") or {}).get("username", "") if data.get("ok") else ""
            )
        return self._username
