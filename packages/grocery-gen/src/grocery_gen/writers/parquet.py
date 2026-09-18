"""Parquet writer utilities."""

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
from pydantic import BaseModel


def write_rows(rows: Sequence[BaseModel], output_path: Path) -> Path:
    """Write a list of Pydantic rows to a Parquet file.

    Creates parent directories as needed. Returns the resolved output path.
    """
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = [row.model_dump() for row in rows]
    frame = pd.DataFrame.from_records(records)
    frame.to_parquet(output_path, index=False, engine="pyarrow")
    return output_path


def write_dataframe(frame: pd.DataFrame, output_path: Path) -> Path:
    """Write a pandas DataFrame to a Parquet file directly — for the
    fact generators (facts/), which build a DataFrame via vectorised
    numpy rather than a list of pydantic rows (see DR-011).

    Creates parent directories as needed. Returns the resolved output path.
    """
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output_path, index=False, engine="pyarrow")
    return output_path
