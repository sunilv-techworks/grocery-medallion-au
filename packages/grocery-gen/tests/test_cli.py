"""Tests for the grocery-gen CLI."""

from typer.testing import CliRunner

from grocery_gen.cli import app

runner = CliRunner()


def test_backfill_runs() -> None:
    result = runner.invoke(app, ["backfill", "--end", "2024-12-31"])
    assert result.exit_code == 0
    assert "Would backfill" in result.stdout


def test_daily_runs() -> None:
    result = runner.invoke(app, ["daily", "--date", "2026-04-25"])
    assert result.exit_code == 0
    assert "Would generate daily data" in result.stdout


def test_help_exits_cleanly() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
