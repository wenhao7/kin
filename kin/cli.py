"""Kin command-line interface.

`serve` (the kin API used by the Hermes plugin, plus the scheduler) is implemented in ROADMAP D2;
until then it exits with code 2.
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


@app.command()
def serve() -> None:
    """Run the kin API used by the Kin plugin in Hermes (compose network only)."""
    import uvicorn
    import yaml
    from openai import OpenAI

    from kin import schedule
    from kin.api import create_app
    from kin.context import Context
    from kin.telegram import TelegramSender

    s, roster, policy, store = _runtime()
    if not s.api_token.get_secret_value():
        console.print("[red]KIN_API_TOKEN is empty; the API would refuse every call.[/red]")
        raise typer.Exit(code=1)
    tz = yaml.safe_load(s.locale_file.read_text(encoding="utf-8")).get("timezone", "UTC")
    key = s.nebius_api_key.get_secret_value()
    ctx = Context(
        store=store,
        policy=policy,
        roster=roster,
        sender=TelegramSender(s.telegram_bot_token.get_secret_value()),
        group_chat_id=s.group_chat_id,
        tz=tz,
        client=OpenAI(api_key=key, base_url=s.nebius_base_url) if key else None,
        model_vision=s.model_vision,
        model_super=s.model_super,
    )
    schedule.start(store, roster, ctx.sender, tz)
    uvicorn.run(create_app(ctx, s.api_token.get_secret_value()), host=s.api_host, port=s.api_port)


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
