"""Policy matrix loader and validator (docs/03-privacy-boundaries.md).

Enforcement (`retrieve(query, principal)`) is implemented in ROADMAP D3; this module only
loads and validates the configuration so `kin check` can catch mistakes early.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

LEVELS = {"read", "write", "summary", "none"}


@dataclass
class Policy:
    roles: list[str]
    categories: list[str]
    matrix: dict[str, dict[str, str]]
    share_request_on_none: list[str] = field(default_factory=list)
    delivery: dict = field(default_factory=dict)

    def level(self, role: str, category: str) -> tuple[str, str | None]:
        """Return (level, qualifier) for a role/category, e.g. ("write", "own")."""
        raw = self.matrix[category][role]
        level, _, qualifier = raw.partition(":")
        return level, (qualifier or None)

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
                level, _, _ = str(row[role]).partition(":")
                if level not in LEVELS:
                    problems.append(f"matrix[{cat}][{role}] has unknown level {level!r}")
        for cat in self.matrix:
            if cat not in self.categories:
                problems.append(f"matrix has unknown category {cat!r}")
        for cat in self.share_request_on_none:
            if cat not in self.categories:
                problems.append(f"share_request_on_none has unknown category {cat!r}")
        return problems


def load_policy(path: Path) -> Policy:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return Policy(
        roles=list(data["roles"]),
        categories=list(data["categories"]),
        matrix={k: {r: str(v) for r, v in row.items()} for k, row in data["matrix"].items()},
        share_request_on_none=list(data.get("share_request_on_none", [])),
        delivery=dict(data.get("delivery", {})),
    )
