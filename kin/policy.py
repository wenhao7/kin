"""Policy matrix loader and validator (docs/03-privacy-boundaries.md).

Enforcement (`retrieve(query, principal)`) is implemented in ROADMAP D3; this module only
loads and validates the configuration so `kin check` can catch mistakes early.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

LEVELS = {"read", "write", "summary", "none"}
QUALIFIERS = {"own", "emergency_contacts"}
# Order used to compute what a group may see: the lowest level among its members.
RANK = {"none": 0, "summary": 1, "read": 2, "write": 3}


@dataclass
class Policy:
    roles: list[str]
    categories: list[str]
    matrix: dict[str, dict[str, str]]
    share_request_on_none: list[str] = field(default_factory=list)
    delivery: dict = field(default_factory=dict)
    projections: dict[str, dict[str, list[str]]] = field(default_factory=dict)

    def level(self, role: str, category: str) -> tuple[str, str | None]:
        """Return (level, qualifier) for a role/category, e.g. ("write", "own")."""
        raw = self.matrix[category][role]
        level, _, qualifier = raw.partition(":")
        return level, (qualifier or None)

    def fields_for(self, role: str, category: str, level: str) -> list[str] | None:
        """Fields a role may see at `level`: a list, None for every field, [] for nothing."""
        if level not in ("summary", "read", "write"):
            return []
        projection = self.projections.get(category, {}).get(role)
        if level == "summary":
            return list(projection or [])
        return None if projection is None else list(projection)

    def group_level(self, category: str, roles: list[str]) -> str:
        """Level a group may see for a category: the lowest among its members' roles.

        Qualified levels (`own`, `emergency_contacts`) count as `none` for a group, and an empty
        or unknown roster fails closed.
        """
        if not roles or any(r not in self.roles for r in roles):
            return "none"
        levels = []
        for role in roles:
            level, qualifier = self.level(role, category)
            levels.append("none" if qualifier else level)
        return min(levels, key=RANK.__getitem__)

    def validate(self) -> list[str]:
        problems: list[str] = []
        for cat in self.categories:
            row = self.matrix.get(cat)
            if row is None:
                problems.append(f"matrix missing category {cat!r}")
                continue
            for role in self.roles:
                if role not in row:
                    problems.append(f"matrix[{cat}] missing role {role!r}")
                    continue
                level, _, qualifier = str(row[role]).partition(":")
                if level not in LEVELS:
                    problems.append(f"matrix[{cat}][{role}] has unknown level {level!r}")
                if qualifier and qualifier not in QUALIFIERS:
                    problems.append(f"matrix[{cat}][{role}] has unknown qualifier {qualifier!r}")
        for cat in self.matrix:
            if cat not in self.categories:
                problems.append(f"matrix has unknown category {cat!r}")
        for cat in self.share_request_on_none:
            if cat not in self.categories:
                problems.append(f"share_request_on_none has unknown category {cat!r}")
        for cat, by_role in self.projections.items():
            if cat not in self.categories:
                problems.append(f"projections has unknown category {cat!r}")
            for role in by_role:
                if role not in self.roles:
                    problems.append(f"projections[{cat}] has unknown role {role!r}")
        return problems


def load_policy(path: Path) -> Policy:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return Policy(
        roles=list(data["roles"]),
        categories=list(data["categories"]),
        matrix={k: {r: str(v) for r, v in row.items()} for k, row in data["matrix"].items()},
        share_request_on_none=list(data.get("share_request_on_none", [])),
        delivery=dict(data.get("delivery", {})),
        projections={
            c: {r: list(fs) for r, fs in by_role.items()}
            for c, by_role in (data.get("projections") or {}).items()
        },
    )
