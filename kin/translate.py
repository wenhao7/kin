"""Mandarin versions of Admin-confirmed group posts (Super on Token Factory).

Translation may not add, drop or alter facts. Medicine and people's names are swapped for
placeholder tokens before translating and restored after, so they stay exactly as written (the
model otherwise translates them, sometimes into a different drug or other characters). The
result is discarded, and only English is posted, unless every token and every number of the
English text survives.
"""

from __future__ import annotations

import re
from typing import Any

PROMPT = (
    "Translate this family care update into Simplified Chinese for an older family member. "
    "Translate the instructions fully. Keep every token like ⟦M1⟧ exactly as it is (they stand "
    "for names) and copy every number exactly. Do not add, drop or explain anything. "
    "Reply with only the translation."
)


def numbers(text: str) -> list[str]:
    return sorted(re.findall(r"\d+(?:[.:]\d+)?", text))


def to_mandarin(client: Any, model: str, text: str, protect: list[str] = ()) -> str | None:
    """The Mandarin version, or None when it fails a check or the call fails."""
    names = sorted({n for n in protect if n}, key=len, reverse=True)
    masked = text
    for i, name in enumerate(names, 1):
        masked = re.sub(rf"\b{re.escape(name)}\b", f"⟦M{i}⟧", masked, flags=re.IGNORECASE)
    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0,
            max_tokens=1500,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
            messages=[{"role": "system", "content": PROMPT}, {"role": "user", "content": masked}],
        )
        zh = (resp.choices[0].message.content or "").strip()
    except Exception:  # noqa: BLE001 - English stands on its own
        return None
    zh = re.sub(r"(?s)<think>.*?</think>", "", zh).strip()
    tokens = [f"⟦M{i}⟧" for i in range(1, len(names) + 1) if f"⟦M{i}⟧" in masked]
    if not zh or any(t not in zh for t in tokens):
        return None
    for i, name in enumerate(names, 1):
        zh = zh.replace(f"⟦M{i}⟧", name)
    if any(n not in zh for n in numbers(text)):
        return None
    return zh
