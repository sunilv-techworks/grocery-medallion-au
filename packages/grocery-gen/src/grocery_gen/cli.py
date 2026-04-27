"""Command-line interface for the grocery data generator."""

from datetime import date
from pathlib import Path

import typer
from rich import print as rprint

app = typer.Typer(
    name="grocery-gen",
    help="Synthetic Australian grocery data generator.",
    no_args_is_help=True,
)


@app.command()
def backfill(
    start: str = typer.Option("2024-01-01", help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option(..., help="End date (YYYY-MM-DD)"),
    seed: int = typer.Option(42, help="Random seed for reproducibility"),
    output_dir: Path = typer.Option(Path("./data"), "--out", help="Output directory"),
) -> None:
    """Generate historical data for the given date range."""
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    rprint(f"[green]Would backfill[/green] from {start_date} to {end_date}")
    rprint(f"  seed={seed}, output_dir={output_dir}")
    rprint("[yellow]Implementation pending — Phase 2[/yellow]")


@app.command()
def daily(
    target_date: str = typer.Option(..., "--date", help="Target date (YYYY-MM-DD)"),
    output_dir: Path = typer.Option(Path("./data"), "--out", help="Output directory"),
) -> None:
    """Generate one day of incremental data."""
    parsed = date.fromisoformat(target_date)
    rprint(f"[green]Would generate daily data[/green] for {parsed}")
    rprint(f"  output_dir={output_dir}")
    rprint("[yellow]Implementation pending — Phase 8[/yellow]")


if __name__ == "__main__":
    app()
