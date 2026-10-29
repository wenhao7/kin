"""Kin command-line interface.

`serve` runs the kin API used by the Hermes plugin, plus the scheduler; the other commands seed,
measure, tick and check the deployment (`kin --help`).
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from kin import __version__
from kin.config import get_settings

app = typer.Typer(help="Private, always-on family care coordinator.", no_args_is_help=True)
console = Console()


@app.command()
def version() -> None:
    """Print the version."""
    console.print(f"kin {__version__}")


@app.command()
def check(
    no_spend: bool = typer.Option(
        False, "--no-spend", help="Skip calls that consume Token Factory or Tavily credits."
    ),
) -> None:
    """Verify keys, policy/locale files, models (incl. one vision call), Telegram bot and Tavily."""
    from kin.setup_check import run_checks

    ok = run_checks(get_settings(), spend=not no_spend)
    raise typer.Exit(code=0 if ok else 1)


@app.command()
def models() -> None:
    """List Nemotron and configured models visible to this API key."""
    from kin.setup_check import list_nemotron_models

    list_nemotron_models(get_settings())


@app.command()
def policy() -> None:
    """Print the loaded policy matrix."""
    from rich.table import Table

    from kin.policy import load_policy

    s = get_settings()
    p = load_policy(s.policy_file)
    table = Table(title=f"policy: {s.policy_file}")
    table.add_column("category")
    for r in p.roles:
        table.add_column(r)
    for cat in p.categories:
        table.add_row(cat, *(p.matrix[cat][r] for r in p.roles))
    console.print(table)
    problems = p.validate()
    if problems:
        console.print("[red]" + "\n".join(problems) + "[/red]")
        raise typer.Exit(code=1)


@app.command("hermes-config")
def hermes_config(
    template: Path = typer.Option(Path("hermes/config.yaml"), help="Hermes config template."),
) -> None:
    """Print the shell script that applies the Hermes template (used by `make hermes-config`)."""
    from kin.hermes_config import hermes_config_script

    typer.echo(hermes_config_script(template), nl=False)


@app.command()
def measure() -> None:
    """Time and price real calls for the README (one intake, translation, answer, lookup)."""
    import yaml
    from openai import OpenAI

    from kin.measure import run, table

    s = get_settings()
    key = s.nebius_api_key.get_secret_value()
    if not key:
        console.print("[red]NEBIUS_API_KEY is empty.[/red]")
        raise typer.Exit(code=1)
    locale = yaml.safe_load(s.locale_file.read_text(encoding="utf-8"))
    search = None
    if s.tavily_api_key.get_secret_value():
        from tavily import TavilyClient

        search = TavilyClient(api_key=s.tavily_api_key.get_secret_value())
    calls = run(OpenAI(api_key=key, base_url=s.nebius_base_url), s, search, locale)
    typer.echo(table(calls))
    total = sum(c.cost for c in calls)
    typer.echo(f"\nTotal: {total:.4f} USD at list prices, plus Tavily credits.")


@app.command("hermes-clear-sessions")
def hermes_clear_sessions() -> None:
    """Print the script that deletes every Telegram conversation (used by `make demo-reset`)."""
    from kin.hermes_config import clear_sessions_script

    typer.echo(clear_sessions_script(), nl=False)


@app.command("render-fixtures")
def render_fixtures() -> None:
    """Render the synthetic fixture to fixtures/renders (needs `make setup-data`)."""
    try:
        from kin.fixtures import render_all
    except ImportError as exc:  # pragma: no cover - depends on the optional extra
        console.print(f"[red]{exc}; run `make setup-data`[/red]")
        raise typer.Exit(code=1) from exc
    for path in render_all():
        console.print(str(path))


def _runtime():
    from kin.members import load_roster
    from kin.policy import load_policy
    from kin.store import Store

    s = get_settings()
    roster = load_roster(s.members_file, s.admin_telegram_id, s.member_ids)
    policy = load_policy(s.policy_file)
    import yaml

    languages = yaml.safe_load(s.locale_file.read_text(encoding="utf-8"))["languages"]["supported"]
    problems = policy.validate() + roster.validate(policy.roles, languages)
    if problems:
        console.print("[red]" + "\n".join(problems) + "[/red]")
        raise typer.Exit(code=1)
    store = Store(s.db_path, s.originals_dir)
    store.sync_roster(roster)
    return s, roster, policy, store


def _context():
    """Settings and the Context `serve` runs with (also used by `tick`)."""
    import yaml
    from openai import OpenAI

    from kin.context import Context
    from kin.members import load_roster
    from kin.telegram import TelegramSender

    s, roster, policy, store = _runtime()
    if s.demo:  # judge demo: seats come from /demo, never from the environment
        roster = load_roster(s.members_file)
    locale = yaml.safe_load(s.locale_file.read_text(encoding="utf-8"))
    key = s.nebius_api_key.get_secret_value()
    tavily_key = s.tavily_api_key.get_secret_value()
    search = None
    if tavily_key:
        from tavily import TavilyClient

        search = TavilyClient(api_key=tavily_key)
    ctx = Context(
        store=store,
        policy=policy,
        roster=roster,
        sender=TelegramSender(s.telegram_bot_token.get_secret_value()),
        group_chat_id=s.group_chat_id,
        tz=locale.get("timezone", "UTC"),
        client=OpenAI(api_key=key, base_url=s.nebius_base_url) if key else None,
        model_vision=s.model_vision,
        model_super=s.model_super,
        locale=locale,
        search=search,
        demo=s.demo,
        base_roster=roster,
    )
    if s.demo:
        from kin.demo import DemoSender, apply

        ctx.sender = DemoSender(ctx.sender, ctx)
        apply(ctx)
    return s, ctx


@app.command()
def serve() -> None:
    """Run the kin API used by the Kin plugin in Hermes (compose network only)."""
    import uvicorn

    from kin import admin, schedule
    from kin.api import create_app

    s, ctx = _context()
    if not s.api_token.get_secret_value():
        console.print("[red]KIN_API_TOKEN is empty; the API would refuse every call.[/red]")
        raise typer.Exit(code=1)
    if s.demo:
        console.print("[yellow]Judge demo: /demo assigns roles; reminders run on /demo monday.")
    failed = admin.install_menus(ctx)
    if failed:
        console.print(f"[yellow]Command menus not set for: {', '.join(failed)}[/yellow]")
    if not s.demo:  # in the demo, reminders run on /demo monday, not at a judge's 3 am
        schedule.start(ctx)
    uvicorn.run(create_app(ctx, s.api_token.get_secret_value()), host=s.api_host, port=s.api_port)


@app.command()
def tick(
    at: str = typer.Option(..., help="Local time to run, e.g. 2026-10-26T08:00 (a Monday)."),
) -> None:
    """Send what is due at a given local time, now: reminders and skills for a video take.
    Each is still sent only once per day (the same claim the scheduler uses)."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from kin import schedule

    _, ctx = _context()
    now = datetime.fromisoformat(at).replace(second=20, tzinfo=ZoneInfo(ctx.tz))
    sent = schedule.tick(ctx, now)
    console.print(f"{now:%a %d %b %H:%M}: {sent} message(s) sent.")


@app.command()
def seed(
    everything: bool = typer.Option(False, "--all", help="Load all eight fixture documents."),
    reset: bool = typer.Option(
        False, "--reset", help="Wipe the store first (synthetic data only)."
    ),
) -> None:
    """Load the synthetic fixture into the store: Week 0 history, or --all documents."""
    import shutil

    from kin.seed import load_fixture_documents, load_week0

    s = get_settings()
    if s.db_path.exists() and not reset:
        console.print(f"[red]{s.db_path} exists; pass --reset to wipe it and reseed.[/red]")
        raise typer.Exit(code=1)
    if reset:
        for p in (
            s.db_path,
            s.db_path.with_suffix(".sqlite3-wal"),
            s.db_path.with_suffix(".sqlite3-shm"),
        ):
            p.unlink(missing_ok=True)
        shutil.rmtree(s.originals_dir, ignore_errors=True)
    _, _, _, store = _runtime()
    loaded = load_fixture_documents(store) if everything else load_week0(store)
    for doc_id, records in loaded.items():
        console.print(f"{doc_id}: {len(records)} records")


if __name__ == "__main__":
    app()
