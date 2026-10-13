"""Render hermes/config.yaml as `hermes config set` commands (`make hermes-config`).

The template is copied only on a container's first start; this re-applies every key to an
existing Hermes home, so the repo stays the source of truth for Kin's Hermes settings.
"""

from __future__ import annotations

import json
import shlex
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import yaml


def flatten(data: dict[str, Any], prefix: str = "") -> Iterator[tuple[str, Any]]:
    """Yield (dotted.key, value) for every leaf; lists stay whole."""
    for key, value in data.items():
        path = f"{prefix}{key}"
        if isinstance(value, dict) and value:
            yield from flatten(value, path + ".")
        else:
            yield path, value


def render(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    return str(value)


def hermes_config_script(template: Path) -> str:
    """A bash script for the hermes container: set each key, drop MCP, install SOUL.md."""
    items = list(flatten(yaml.safe_load(Path(template).read_text(encoding="utf-8"))))
    lines = ["set -e"]
    lines += [
        f"hermes config set {shlex.quote(k)} {shlex.quote(render(v))} >/dev/null" for k, v in items
    ]
    # Superseded by the Kin plugin (Hermes passes no caller identity to MCP servers).
    lines.append("hermes config unset mcp_servers >/dev/null 2>&1 || true")
    lines.append('cp /seed/SOUL.md "$HERMES_HOME/SOUL.md"')
    lines.append(f'echo "applied {len(items)} keys and SOUL.md"')
    return "\n".join(lines) + "\n"
