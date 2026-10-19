"""What the kin service's handlers share: store, policy, roster, sender, model and search."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from kin.answer import Turns
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
        remove_keyboard: bool = False,
    ) -> dict[str, Any]: ...

    def set_commands(self, commands: list[tuple[str, str]], chat_id: str) -> dict[str, Any]: ...

    def send_photo(self, chat_id: str, path: Any, caption: str = "") -> dict[str, Any]: ...

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
    locale: dict[str, Any] = field(default_factory=dict)  # locale/<id>/locale.yaml
    search: Any = None  # Tavily client; None disables public lookups
    turns: Turns = field(default_factory=Turns)
    demo: bool = False  # judge demo (kin.demo): seats come from /demo, roster rebuilt on claims
    base_roster: Roster | None = None

    @property
    def household(self) -> dict[str, Any]:
        return self.roster.household
