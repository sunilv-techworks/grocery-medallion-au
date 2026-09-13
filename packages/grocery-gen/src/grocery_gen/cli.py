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


@app.command()
def products(
    count: int = typer.Option(2000, "--count", help="Number of SKUs to generate"),
    seed: int = typer.Option(42, "--seed", help="Random seed"),
    output_dir: Path = typer.Option(Path("./data"), "--out", help="Output directory"),
) -> None:
    """Generate the raw product_catalog Bronze extract and write it to Parquet."""
    from grocery_gen.dimensions.products import generate_products, to_raw_product_rows
    from grocery_gen.writers.parquet import write_rows

    rprint(f"[cyan]Generating[/cyan] {count} products with seed={seed}...")
    rows = generate_products(n=count, seed=seed)
    raw_rows = to_raw_product_rows(rows, seed=seed)
    output_path = output_dir / "product_catalog.parquet"
    written = write_rows(raw_rows, output_path)
    rprint(f"[green]Wrote[/green] {len(raw_rows)} product_catalog rows to {written}")


@app.command()
def categories(
    output_dir: Path = typer.Option(Path("./data"), "--out", help="Output directory"),
) -> None:
    """Generate the category_master Bronze extract and write it to Parquet."""
    from grocery_gen.dimensions.categories import generate_categories
    from grocery_gen.writers.parquet import write_rows

    rprint("[cyan]Generating[/cyan] category master...")
    rows = generate_categories()
    output_path = output_dir / "category_master.parquet"
    written = write_rows(rows, output_path)
    rprint(f"[green]Wrote[/green] {len(rows)} categories to {written}")


@app.command()
def calendar(
    start: str = typer.Option("2024-01-01", "--start", help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option("2026-12-31", "--end", help="End date (YYYY-MM-DD)"),
    output_dir: Path = typer.Option(Path("./data"), "--out", help="Output directory"),
) -> None:
    """Generate the dim_calendar date dimension and write it to Parquet."""
    from grocery_gen.dimensions.calendar import generate_calendar_dates
    from grocery_gen.writers.parquet import write_rows

    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    rprint(f"[cyan]Generating[/cyan] calendar from {start_date} to {end_date}...")
    rows = generate_calendar_dates(start_date, end_date)
    output_path = output_dir / "dim_calendar.parquet"
    written = write_rows(rows, output_path)
    rprint(f"[green]Wrote[/green] {len(rows)} calendar rows to {written}")


@app.command()
def stores(
    count: int = typer.Option(150, "--count", help="Number of stores to generate"),
    seed: int = typer.Option(42, "--seed", help="Random seed"),
    output_dir: Path = typer.Option(Path("./data"), "--out", help="Output directory"),
) -> None:
    """Generate the raw site_master Bronze extract and write it to Parquet."""
    from grocery_gen.dimensions.stores import generate_stores, to_raw_store_rows
    from grocery_gen.writers.parquet import write_rows

    rprint(f"[cyan]Generating[/cyan] {count} stores with seed={seed}...")
    rows = generate_stores(n=count, seed=seed)
    raw_rows = to_raw_store_rows(rows, seed=seed)
    output_path = output_dir / "site_master.parquet"
    written = write_rows(raw_rows, output_path)
    rprint(f"[green]Wrote[/green] {len(raw_rows)} site_master rows to {written}")


@app.command()
def customers(
    count: int = typer.Option(5000, "--count", help="Number of customers to generate"),
    seed: int = typer.Option(42, "--seed", help="Random seed"),
    num_stores: int = typer.Option(
        150, "--num-stores", help="Store ID space for preferred_store_id (match `stores --count`)"
    ),
    output_dir: Path = typer.Option(Path("./data"), "--out", help="Output directory"),
) -> None:
    """Generate the raw loyalty_members Bronze extract and write it to Parquet."""
    from grocery_gen.dimensions.customers import generate_customers, to_raw_customer_rows
    from grocery_gen.writers.parquet import write_rows

    rprint(f"[cyan]Generating[/cyan] {count} customers with seed={seed}...")
    rows = generate_customers(n=count, seed=seed, num_stores=num_stores)
    raw_rows = to_raw_customer_rows(rows, seed=seed)
    output_path = output_dir / "loyalty_members.parquet"
    written = write_rows(raw_rows, output_path)
    rprint(f"[green]Wrote[/green] {len(raw_rows)} loyalty_members rows to {written}")


if __name__ == "__main__":
    app()
