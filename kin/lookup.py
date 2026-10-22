"""Public scheme lookups through Tavily (docs/02-product.md, Public lookup).

Kin builds the query from a scheme named in the locale pack (`lookup_topics`), never from the
asker's or the model's words, so family names, IDs and record content cannot reach Tavily. The
search is limited to the locale's allow-listed domains, and results from anywhere else are
dropped. Kin returns the public pages with their links; it does not decide eligibility.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

LOOKUP_RULES = (
    "Say what these public pages say about the scheme, in plain words, with the link. Don't say "
    "whether anyone in the family qualifies: the agency decides, so say how to apply or check, "
    "and don't offer to check the family's records. If pages give different figures, use the "
    "scheme's own page and say the agency confirms current amounts. If the pages don't answer "
    "the question, say so."
)


def topics(locale: dict[str, Any]) -> list[dict[str, Any]]:
    return list(locale.get("lookup_topics") or [])


def match(locale: dict[str, Any], text: str) -> dict[str, Any] | None:
    """The locale scheme the text names, longest name first; None when it names none."""
    low = text.lower()
    names = [(n, t) for t in topics(locale) for n in [t["name"], *t.get("aliases", [])]]
    for name, topic in sorted(names, key=lambda p: -len(p[0])):
        if re.search(rf"(?<!\w){re.escape(name.lower())}(?!\w)", low):
            return topic
    return None


def query_for(topic: dict[str, Any]) -> str:
    return f"{topic['name']}: eligibility, amount and how to apply"


def allowed(url: str, domains: list[str]) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in domains)


def search(client: Any, locale: dict[str, Any], topic: dict[str, Any]) -> list[dict[str, str]]:
    """Allow-listed results, without dated pages such as press releases (`lookup_skip_paths`):
    they describe a scheme as announced, often with figures since changed."""
    domains = list(locale.get("lookup_allow_domains") or [])
    skip = [s.lower() for s in locale.get("lookup_skip_paths") or []]
    res = client.search(
        query_for(topic), max_results=5, include_domains=domains, search_depth="basic"
    )
    kept = [
        {"title": r.get("title", ""), "url": r["url"], "content": (r.get("content") or "")[:800]}
        for r in res.get("results", [])
        if allowed(r.get("url", ""), domains)
        and not any(s in (urlparse(r["url"]).path or "").lower() for s in skip)
    ]
    return kept[:3]
