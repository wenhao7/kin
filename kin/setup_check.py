"""Environment and access checks for `kin check` / `kin models`."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path

import httpx
import yaml
from openai import OpenAI
from rich.console import Console
from rich.table import Table

from kin.config import Settings
from kin.policy import load_policy

console = Console()

# 2×2 red PNG, used for a one-token Omni vision call.
_TINY_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAD0lEQVR4nGP4z8DwHwYBAB2lA/9m"
    "k8OgAAAAAElFTkSuQmCC"
)


@dataclass
class Check:
    name: str
    status: str  # PASS | FAIL | SKIP
    detail: str = ""


def _mask(value: str) -> str:
    return f"{value[:4]}…{value[-4:]}" if len(value) > 12 else "set"


def _client(settings: Settings) -> OpenAI:
    return OpenAI(
        base_url=settings.nebius_base_url, api_key=settings.nebius_api_key.get_secret_value()
    )


def check_env(settings: Settings) -> list[Check]:
    out: list[Check] = []
    for label, value, required in (
        ("NEBIUS_API_KEY", settings.nebius_api_key.get_secret_value(), True),
        ("TELEGRAM_BOT_TOKEN", settings.telegram_bot_token.get_secret_value(), True),
        ("TAVILY_API_KEY", settings.tavily_api_key.get_secret_value(), True),
        ("KIN_ADMIN_TELEGRAM_ID", settings.admin_telegram_id, False),
    ):
        if value:
            out.append(Check(label, "PASS", _mask(value)))
        else:
            out.append(Check(label, "FAIL" if required else "SKIP", "missing"))
    return out


def check_files(settings: Settings) -> list[Check]:
    out: list[Check] = []
    try:
        policy = load_policy(settings.policy_file)
        problems = policy.validate()
        out.append(
            Check(
                f"policy {settings.policy_file}",
                "PASS" if not problems else "FAIL",
                f"{len(policy.roles)} roles × {len(policy.categories)} categories"
                if not problems
                else "; ".join(problems)[:300],
            )
        )
    except Exception as exc:  # noqa: BLE001
        out.append(Check(f"policy {settings.policy_file}", "FAIL", str(exc)[:200]))
    try:
        loc = yaml.safe_load(Path(settings.locale_file).read_text(encoding="utf-8"))
        langs = loc["languages"]["supported"]
        out.append(Check(f"locale {settings.locale_file}", "PASS", f"languages={langs}"))
    except Exception as exc:  # noqa: BLE001
        out.append(Check(f"locale {settings.locale_file}", "FAIL", str(exc)[:200]))
    d = Path(settings.data_dir)
    out.append(
        Check(
            f"data dir {d}",
            "PASS" if d.exists() else "FAIL",
            "exists" if d.exists() else "missing (mkdir -p data)",
        )
    )
    return out


def fetch_models(settings: Settings) -> list[str]:
    return sorted(m.id for m in _client(settings).models.list().data)


def fetch_models_verbose(settings: Settings) -> list[dict]:
    """Model records with modality, via `GET /v1/models?verbose=true`."""
    base = settings.nebius_base_url.rstrip("/")
    r = httpx.get(
        f"{base}/models",
        params={"verbose": "true"},
        headers={"Authorization": f"Bearer {settings.nebius_api_key.get_secret_value()}"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("data", [])


def check_models(settings: Settings, spend: bool) -> list[Check]:
    out: list[Check] = []
    try:
        ids = fetch_models(settings)
    except Exception as exc:  # noqa: BLE001
        return [Check("Token Factory /v1/models", "FAIL", str(exc)[:200])]
    out.append(Check("Token Factory /v1/models", "PASS", f"{len(ids)} models visible"))
    lowered = {i.lower(): i for i in ids}
    for tier, model_id in settings.models.items():
        if model_id in ids:
            out.append(Check(f"model:{tier}", "PASS", model_id))
        elif model_id.lower() in lowered:
            out.append(
                Check(
                    f"model:{tier}",
                    "FAIL",
                    f"case mismatch; catalog has {lowered[model_id.lower()]}",
                )
            )
        else:
            hint = [i for i in ids if "nemotron" in i.lower()]
            out.append(
                Check(f"model:{tier}", "FAIL", f"{model_id} not found; nemotron ids: {hint}")
            )
    if not settings.model_vision:
        out.append(
            Check("vision:image", "FAIL", "KIN_MODEL_VISION not set; pick one from `kin models`")
        )
        return out
    if not spend:
        out.append(Check("vision:image", "SKIP", "--no-spend"))
        return out
    try:
        resp = _client(settings).chat.completions.create(
            model=settings.model_vision,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "One word: what colour is this image?"},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{_TINY_PNG}"},
                        },
                    ],
                }
            ],
            max_tokens=64,
            temperature=0,
        )
        text = (resp.choices[0].message.content or "").strip()
        status = "PASS" if text else "FAIL"
        out.append(Check("vision:image", status, f"{settings.model_vision} reply={text!r}"))
    except Exception as exc:  # noqa: BLE001
        out.append(Check("vision:image", "FAIL", str(exc)[:200]))
    return out


def check_telegram(settings: Settings) -> list[Check]:
    token = settings.telegram_bot_token.get_secret_value()
    if not token:
        return [Check("Telegram getMe", "SKIP", "no token")]
    try:
        r = httpx.get(f"https://api.telegram.org/bot{token}/getMe", timeout=15)
        data = r.json()
        if data.get("ok"):
            bot = data["result"]
            can_read = bot.get("can_read_all_group_messages", False)
            detail = f"@{bot.get('username')} · can_read_all_group_messages={can_read}"
            status = "PASS" if can_read else "FAIL"
            if not can_read:
                detail += " — disable Group Privacy in @BotFather, then remove/re-add the bot"
            return [Check("Telegram getMe", status, detail)]
        return [Check("Telegram getMe", "FAIL", str(data)[:200])]
    except Exception as exc:  # noqa: BLE001
        return [Check("Telegram getMe", "FAIL", str(exc)[:200])]


def check_tavily(settings: Settings, spend: bool) -> list[Check]:
    if not settings.tavily_api_key.get_secret_value():
        return [Check("Tavily search", "SKIP", "no key")]
    if not spend:
        return [Check("Tavily search", "SKIP", "--no-spend")]
    try:
        from tavily import TavilyClient

        loc = yaml.safe_load(Path(settings.locale_file).read_text(encoding="utf-8"))
        res = TavilyClient(api_key=settings.tavily_api_key.get_secret_value()).search(
            "Home Caregiving Grant eligibility",
            max_results=1,
            include_domains=loc.get("lookup_allow_domains", []),
        )
        n = len(res.get("results", []))
        return [Check("Tavily search (allow-listed)", "PASS", f"{n} result(s)")]
    except Exception as exc:  # noqa: BLE001
        return [Check("Tavily search (allow-listed)", "FAIL", str(exc)[:200])]


def run_checks(settings: Settings, spend: bool = True) -> bool:
    checks: list[Check] = []
    checks += check_env(settings)
    checks += check_files(settings)
    if settings.nebius_api_key.get_secret_value():
        checks += check_models(settings, spend)
    checks += check_telegram(settings)
    checks += check_tavily(settings, spend)

    table = Table(title="kin check")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail", overflow="fold")
    colour = {"PASS": "green", "FAIL": "red", "SKIP": "yellow"}
    for c in checks:
        table.add_row(c.name, f"[{colour[c.status]}]{c.status}[/{colour[c.status]}]", c.detail)
    console.print(table)
    return all(c.status != "FAIL" for c in checks)


def list_nemotron_models(settings: Settings) -> None:
    """Nemotron models plus every model whose modality accepts images (vision candidates)."""
    configured = {v: k for k, v in settings.models.items()}
    table = Table(title="Token Factory: Nemotron and image-capable models")
    table.add_column("Model ID")
    table.add_column("Modality")
    table.add_column("Configured as")
    try:
        records = fetch_models_verbose(settings)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[yellow]verbose listing failed ({str(exc)[:120]}); falling back[/yellow]")
        records = [{"id": i, "architecture": {}} for i in fetch_models(settings)]
    for m in sorted(records, key=lambda r: r.get("id", "")):
        mid = m.get("id", "")
        modality = (m.get("architecture") or {}).get("modality", "") or ""
        if "nemotron" in mid.lower() or "image" in modality.lower():
            table.add_row(mid, modality, configured.get(mid, ""))
    console.print(table)


def _b64_ok() -> bool:  # sanity for the embedded PNG
    return base64.b64decode(_TINY_PNG)[:8] == b"\x89PNG\r\n\x1a\n"
