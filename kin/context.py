"""What the kin service's handlers share: store, policy, roster, Telegram sender, model client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from kin.members import Roster
from kin.policy import Policy
from kin.store import Store


class Sender(Protocol):
    def send(
        self,
        chat_id: str,
        text: str,
        reply_to: str | None = None,
        keyboard: list[str] | None = None,
    ) -> dict[str, Any]: ...

    def username(self) -> str: ...


@dataclass
class Context:
    store: Store
    policy: Policy
    roster: Roster
    sender: Sender  # kin.telegram.TelegramSender or a test double
    group_chat_id: str
    tz: str = "Asia/Singapore"
    client: Any = None  # OpenAI-compatible Token Factory client; None disables model calls
    model_vision: str = ""
    model_super: str = ""

    @property
    def household(self) -> dict[str, Any]:
        return self.roster.household
