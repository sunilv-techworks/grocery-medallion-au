"""Tests for the `grocery-gen products` CLI command."""

from pathlib import Path

import pandas as pd
from typer.testing import CliRunner

from grocery_gen.cli import app

runner = CliRunner()


def test_products_command_writes_parquet(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["products", "--count", "100", "--seed", "42", "--out", str(tmp_path)],
    )
    assert result.exit_code == 0, result.stdout
    output = tmp_path / "product_catalog.parquet"
    assert output.exists()
    frame = pd.read_parquet(output)
    assert len(frame) > 100  # duplicates are injected on top of the 100 base rows
    assert "sku_id" in frame.columns
    assert "season_vec" in frame.columns
    assert frame["sku_id"].isna().sum() > 0  # deliberate null-key rows present
    assert frame["sku_id"].duplicated().sum() > 0  # deliberate duplicate rows present


def test_categories_command_writes_parquet(tmp_path: Path) -> None:
    result = runner.invoke(app, ["categories", "--out", str(tmp_path)])
    assert result.exit_code == 0, result.stdout
    output = tmp_path / "category_master.parquet"
    assert output.exists()
    frame = pd.read_parquet(output)
    assert len(frame) > 0
    assert {"department", "category", "gst_exempt"}.issubset(frame.columns)
    assert not frame.duplicated(subset=["department", "category"]).any()
