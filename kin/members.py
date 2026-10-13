"""Member roster loader (config/members.yaml + Telegram IDs from the environment).

Roles and languages come from the roster file; Telegram user IDs come from `.env` so the file
stays free of real account data. Resolution of a Telegram user to a member is used by every
policy decision, so an unknown ID gets no role (fail closed) unless the roster names a
non-admin `default_role`, and never admin.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Member:
    id: str
    name: str
    role: str | None
    language: str
    telegram_id: str | None = None


@dataclass
class Roster:
    members: list[Member]
    default_role: str | None
    default_language: str

    def by_telegram_id(self, telegram_id: str) -> Member:
        """The member for a Telegram user ID, or a guest with `default_role` (usually none)."""
        for m in self.members:
            if m.telegram_id and m.telegram_id == str(telegram_id):
                return m
        return Member(
            id=f"guest:{telegram_id}",
            name="Guest",
            role=self.default_role,
            language=self.default_language,
            telegram_id=str(telegram_id),
        )

    def validate(self, roles: list[str], languages: list[str]) -> list[str]:
        problems: list[str] = []
        admins = [m for m in self.members if m.role == "admin"]
        if len(admins) != 1:
            problems.append(f"expected exactly one admin, found {len(admins)}")
        for m in self.members:
            if m.role not in roles:
                problems.append(f"member {m.id!r} has unknown role {m.role!r}")
            if m.language not in languages:
                problems.append(f"member {m.id!r} has unsupported language {m.language!r}")
        if self.default_role is not None and (
            self.default_role not in roles or self.default_role == "admin"
        ):
            problems.append(f"default_role {self.default_role!r} must be a non-admin role")
        ids = [m.telegram_id for m in self.members if m.telegram_id]
        if len(ids) != len(set(ids)):
            problems.append("a Telegram ID is mapped to more than one member")
        return problems


def parse_member_ids(raw: str) -> dict[str, str]:
    """Parse `KIN_MEMBER_IDS` (`id:telegram_id,...`)."""
    out: dict[str, str] = {}
    for part in filter(None, (p.strip() for p in raw.split(","))):
        member_id, _, telegram_id = part.partition(":")
        if member_id.strip() and telegram_id.strip():
            out[member_id.strip()] = telegram_id.strip()
    return out


def load_roster(path: Path, admin_telegram_id: str = "", member_ids: str = "") -> Roster:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    mapped = parse_member_ids(member_ids)
    members = []
    for m in data["members"]:
        telegram_id = admin_telegram_id if m["role"] == "admin" else mapped.get(m["id"])
        members.append(
            Member(
                id=m["id"],
                name=m["name"],
                role=m["role"],
                language=m["language"],
                telegram_id=str(telegram_id) if telegram_id else None,
            )
        )
    return Roster(
        members=members,
        default_role=data.get("default_role"),
        default_language=data.get("default_language", "en"),
    )
