"""`kin measure`: real calls, timed and priced, for the README's "How we use Nebius and NVIDIA".

Runs one intake of the two photographed discharge pages (classify, section headings, extract on
the vision model), the Mandarin version of the resulting group post and one grounded answer on
Super, and one allow-listed Tavily lookup. Token counts come from each response's `usage`; cost
uses the list prices below. It spends a few cents of Token Factory credit and one Tavily credit.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

# List prices per 1M input / output tokens (Token Factory price list, 14 Oct 2026).
PRICES = {
    "openbmb/MiniCPM-V-4_5": (0.66, 1.11),
    "nvidia/nemotron-3-super-120b-a12b": (0.30, 0.90),
    "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B": (0.06, 0.24),
}


@dataclass
class Call:
    task: str
    model: str
    seconds: float
    tokens_in: int
    tokens_out: int

    @property
    def cost(self) -> float:
        price_in, price_out = PRICES.get(self.model, (0.0, 0.0))
        return (self.tokens_in * price_in + self.tokens_out * price_out) / 1e6


@dataclass
class Recorder:
    """An OpenAI-compatible client that records every chat completion under the current task."""

    inner: Any
    calls: list[Call] = field(default_factory=list)
    task: str = ""

    def __post_init__(self) -> None:
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs: Any) -> Any:
        start = time.perf_counter()
        resp = self.inner.chat.completions.create(**kwargs)
        usage = getattr(resp, "usage", None)
        self.calls.append(
            Call(
                self.task,
                kwargs.get("model", ""),
                time.perf_counter() - start,
                getattr(usage, "prompt_tokens", 0) or 0,
                getattr(usage, "completion_tokens", 0) or 0,
            )
        )
        return resp


def run(client: Any, settings: Any, search: Any, locale: dict[str, Any]) -> list[Call]:
    from kin import extract, intake, lookup
    from kin.answer import rules
    from kin.fixtures import ROOT
    from kin.members import load_roster
    from kin.policy import load_policy
    from kin.translate import to_mandarin

    rec = Recorder(client)
    roster = load_roster(settings.members_file)
    pages = []
    for name in ("discharge-summary-p1.jpg", "discharge-summary-p2.jpg"):
        image = (ROOT / "photos" / name).read_bytes()
        rec.task = f"Intake: {name}"
        doc_type = extract.classify(rec, settings.model_vision, image, "image/jpeg")
        pages.append(extract.extract(rec, settings.model_vision, image, "image/jpeg", doc_type))
    fields: dict[str, Any] = {}
    for page in pages:  # what the draft holds once both pages are in
        fields.update({k: v for k, v in page.fields.items() if v})
    records = intake.records_for("discharge_summary", fields, roster.household)
    rows = [{"category": r["category"], "fields": json.dumps(r["fields"])} for r in records]
    policy = load_policy(settings.policy_file)
    view = intake.household_view(policy, [m.role for m in roster.members], rows)
    title = intake.source_of("discharge_summary", fields)
    english = intake.group_summary(view, title, roster.admin().short) or ""
    rec.task = "Mandarin group post"
    drugs = [r["fields"].get("drug", "") for r in records]
    to_mandarin(rec, settings.model_super, english, drugs + [m.short for m in roster.members])
    rec.task = "Grounded answer"
    soul = Path("hermes/SOUL.md").read_text(encoding="utf-8")
    rec.chat.completions.create(
        model=settings.model_super,
        temperature=0,
        max_tokens=600,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        messages=[
            {"role": "system", "content": soul},
            {"role": "user", "content": "What are the morning medicines now?"},
            {
                "role": "user",
                "content": json.dumps(
                    {"records": [r["fields"] for r in records], "rules": rules(roster.household)}
                ),
            },
        ],
    )
    if search is not None:
        topic = lookup.match(locale, "Home Caregiving Grant")
        start = time.perf_counter()
        lookup.search(search, locale, topic)
        elapsed = time.perf_counter() - start
        rec.calls.append(Call("Tavily lookup (1 credit)", "tavily search", elapsed, 0, 0))
    return rec.calls


def table(calls: list[Call]) -> str:
    tasks: dict[str, list[Call]] = {}
    for c in calls:
        tasks.setdefault(c.task, []).append(c)
    lines = [
        "| Task | Model | Calls | Seconds | Tokens in / out | Cost (USD) |",
        "|---|---|---|---|---|---|",
    ]
    for task, cs in tasks.items():
        lines.append(
            f"| {task} | `{cs[0].model}` | {len(cs)} | {sum(c.seconds for c in cs):.1f} | "
            f"{sum(c.tokens_in for c in cs):,} / {sum(c.tokens_out for c in cs):,} | "
            f"{sum(c.cost for c in cs):.4f} |"
        )
    return "\n".join(lines)
