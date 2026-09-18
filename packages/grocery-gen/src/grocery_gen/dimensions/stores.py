"""Store dimension generator for a fictional AU grocery retailer."""

from datetime import date, timedelta
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict

from grocery_gen.reference.geography import SUBURBS, State

RETAILER_NAME = "FreshCo"

StoreFormat = Literal["Supermarket", "Metro", "Express"]

FORMAT_WEIGHTS: dict[StoreFormat, float] = {"Supermarket": 0.50, "Metro": 0.35, "Express": 0.15}
FORMAT_SIZE_SQM_RANGE: dict[StoreFormat, tuple[int, int]] = {
    "Supermarket": (2000, 4500),
    "Metro": (600, 1500),
    "Express": (150, 500),
}
FORMAT_CHECKOUT_RANGE: dict[StoreFormat, tuple[int, int]] = {
    "Supermarket": (10, 24),
    "Metro": (4, 8),
    "Express": (1, 3),
}

# Relative foot-traffic/throughput by format, relative to Metro=1.0 — used
# by facts/sales.py and facts/wastage.py to scale daily volume per store.
STORE_FORMAT_VELOCITY_MULTIPLIER: dict[StoreFormat, float] = {
    "Supermarket": 1.6,
    "Metro": 1.0,
    "Express": 0.4,
}

# Fixed anchor for opened_date so generation stays deterministic across runs
# (no date.today() — same reasoning as every other seeded generator here).
_REFERENCE_DATE = date(2026, 1, 1)
_MAX_STORE_AGE_DAYS = 365 * 20


class StoreRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    store_id: str
    store_name: str
    store_format: StoreFormat
    state: State
    suburb: str
    postcode: str
    store_size_sqm: int
    num_checkouts: int
    opened_date: date
    has_bakery: bool
    has_deli: bool
    has_pharmacy: bool


def generate_stores(n: int = 150, seed: int = 42) -> list[StoreRow]:
    """Deterministic, seeded store list. Format mix and size/checkout ranges
    are hand-tuned to look like a real supermarket/metro/express estate
    rather than uniformly random.
    """
    rng = np.random.default_rng(seed)
    formats = list(FORMAT_WEIGHTS)
    format_p = [FORMAT_WEIGHTS[f] for f in formats]

    rows: list[StoreRow] = []
    for i in range(n):
        store_format: StoreFormat = rng.choice(formats, p=format_p)
        state, suburb, postcode = SUBURBS[rng.integers(0, len(SUBURBS))]

        size_lo, size_hi = FORMAT_SIZE_SQM_RANGE[store_format]
        checkout_lo, checkout_hi = FORMAT_CHECKOUT_RANGE[store_format]
        opened_date = _REFERENCE_DATE - timedelta(days=int(rng.integers(30, _MAX_STORE_AGE_DAYS)))

        rows.append(
            StoreRow(
                store_id=f"STR-{i + 1:04d}",
                store_name=f"{RETAILER_NAME} {suburb}",
                store_format=store_format,
                state=state,
                suburb=suburb,
                postcode=postcode,
                store_size_sqm=int(rng.integers(size_lo, size_hi)),
                num_checkouts=int(rng.integers(checkout_lo, checkout_hi + 1)),
                opened_date=opened_date,
                has_bakery=store_format != "Express" and rng.random() < 0.7,
                has_deli=store_format == "Supermarket" and rng.random() < 0.6,
                has_pharmacy=store_format == "Supermarket" and rng.random() < 0.3,
            )
        )

    return rows


class RawStoreRow(BaseModel):
    """Source-shaped store extract, as a site-master/POS feed would hand it
    over — different column names, plus the same deliberate, deterministic
    quality issues (missing keys, duplicate rows) as to_raw_product_rows.
    """

    model_config = ConfigDict(frozen=True)

    site_code: str | None
    site_name: str
    format_code: str
    state_code: str
    suburb_name: str
    postal_code: str
    size_sqm: int
    checkout_count: int
    open_dt: date
    bakery_flag: bool
    deli_flag: bool
    pharmacy_flag: bool


def _to_raw_row(row: StoreRow) -> RawStoreRow:
    return RawStoreRow(
        site_code=row.store_id,
        site_name=row.store_name,
        format_code=row.store_format,
        state_code=row.state,
        suburb_name=row.suburb,
        postal_code=row.postcode,
        size_sqm=row.store_size_sqm,
        checkout_count=row.num_checkouts,
        open_dt=row.opened_date,
        bakery_flag=row.has_bakery,
        deli_flag=row.has_deli,
        pharmacy_flag=row.has_pharmacy,
    )


def to_raw_store_rows(
    rows: list[StoreRow], seed: int = 42, messy_rate: float = 0.01
) -> list[RawStoreRow]:
    """Rename to source-shaped columns and inject deterministic quality
    issues: a null key on ~messy_rate of rows, and an equal share of exact
    duplicate rows appended. Mirrors to_raw_product_rows exactly.
    """
    rng = np.random.default_rng(seed * 13 + 5)
    raw_rows = [_to_raw_row(r) for r in rows]

    n = len(raw_rows)
    n_messy = max(1, int(n * messy_rate))

    null_key_idx = set(rng.choice(n, size=n_messy, replace=False).tolist())
    for idx in null_key_idx:
        raw_rows[idx] = raw_rows[idx].model_copy(update={"site_code": None})

    dup_source_idx = rng.choice(n, size=n_messy, replace=False).tolist()
    duplicates = [raw_rows[idx] for idx in dup_source_idx]

    return raw_rows + duplicates
