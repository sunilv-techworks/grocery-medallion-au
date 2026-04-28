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
    output = tmp_path / "dim_product.parquet"
    assert output.exists()
    frame = pd.read_parquet(output)
    assert len(frame) == 100
    assert "product_id" in frame.columns
    assert "seasonality_vector" in frame.columns
    assert frame["product_id"].is_unique
