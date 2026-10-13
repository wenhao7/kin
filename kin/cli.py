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


@app.command()
def serve() -> None:
    """Run the kin API (used by the Kin plugin in Hermes) and the scheduler."""
    console.print("[yellow]Not implemented yet — see ROADMAP.md D2.[/yellow]")
    raise typer.Exit(code=2)


if __name__ == "__main__":
    app()
