"""Configuration for the grocery data generator, loadable from environment variables."""

from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class GeneratorConfig(BaseSettings):
    start_date: date = Field(default=date(2024, 1, 1))
    end_date: date = Field(default_factory=date.today)
    seed: int = Field(default=42)
    output_dir: Path = Field(default=Path("./data"))
    num_stores: int = Field(default=150)
    num_customers: int = Field(default=50_000)
    num_products: int = Field(default=2000)
    country: Literal["AU"] = Field(default="AU")

    model_config = {"env_prefix": "GROCERY_GEN_"}
