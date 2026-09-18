"""Wastage fact generator — daily grain per (date, store, perishable product).

Only products with a shelf_life_days and wastage_rate_baseline (i.e. the
_PERISHABLE_DEPARTMENTS products.py already flags) can waste at all — a
long-life pantry item doesn't spoil, so it never appears here.

The inverse-seasonality relationship is the actual "fresh-goods"
differentiator: in-season, a perishable sells through fast, so less of what
gets stocked has time to go stale before it sells; off-season, turnover
slows and more of the same stock level spoils. Reusing sales.py's own
seasonality_vector for this — inverted, not a separate wastage-seasonality
model — is what makes that relationship real rather than asserted.
"""

from datetime import date

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from grocery_gen.dimensions.products import ProductRow
from grocery_gen.dimensions.stores import STORE_FORMAT_VELOCITY_MULTIPLIER, StoreRow

# Expected units of *stock on hand* per store per day for a "typical"
# perishable product in this department, at a Metro-format store — the
# base wastage_rate_baseline on the product is applied against this, not
# against units sold (a store can waste stock it never sold).
STOCK_UNITS_BY_DEPARTMENT: dict[str, float] = {
    "Fresh Produce": 7.0,
    "Bakery": 10.0,
    "Dairy": 9.0,
    "Meat & Seafood": 3.5,
    "Frozen": 3.5,
}

WASTAGE_REASON_WEIGHTS: dict[str, float] = {
    "Spoilage": 0.55,
    "Damaged in Handling": 0.25,
    "Expired on Shelf": 0.20,
}

WASTAGE_FACT_COLUMNS = [
    "date",
    "store_id",
    "product_id",
    "wastage_qty",
    "wastage_cost_aud",
    "wastage_reason",
]


def generate_wastage_facts(
    products: list[ProductRow],
    stores: list[StoreRow],
    start: date,
    end: date,
    seed: int = 43,
) -> pd.DataFrame:
    perishable = [
        p for p in products if p.shelf_life_days is not None and p.wastage_rate_baseline is not None
    ]
    if not perishable or not stores:
        return pd.DataFrame(columns=WASTAGE_FACT_COLUMNS)

    rng = np.random.default_rng(seed)

    dates = pd.date_range(start, end, freq="D")
    month_idx = dates.month.to_numpy() - 1

    stock = np.array([STOCK_UNITS_BY_DEPARTMENT[p.department] for p in perishable])
    format_mult = np.array([STORE_FORMAT_VELOCITY_MULTIPLIER[s.store_format] for s in stores])
    wastage_rate = np.array([p.wastage_rate_baseline for p in perishable])
    seasonality = np.array([p.seasonality_vector for p in perishable])  # (n_products, 12)
    season_mult = seasonality[:, month_idx].T  # (n_days, n_products)

    # Inverse relationship: divide by season_mult rather than multiply.
    lam = (
        stock[None, None, :]
        * format_mult[None, :, None]
        * wastage_rate[None, None, :]
        / season_mult[:, None, :]
    )  # (n_days, n_stores, n_products)

    quantity = rng.poisson(lam)

    day_idx, store_idx, prod_idx = np.nonzero(quantity)
    if len(day_idx) == 0:
        return pd.DataFrame(columns=WASTAGE_FACT_COLUMNS)

    qty_flat = quantity[day_idx, store_idx, prod_idx]

    cost_price = np.array([p.cost_price_aud for p in perishable])
    product_ids = np.array([p.product_id for p in perishable])
    store_ids = np.array([s.store_id for s in stores])

    wastage_cost = np.round(qty_flat * cost_price[prod_idx], 2)

    reasons = list(WASTAGE_REASON_WEIGHTS)
    reason_p = [WASTAGE_REASON_WEIGHTS[r] for r in reasons]
    wastage_reason = rng.choice(reasons, size=len(day_idx), p=reason_p)

    return pd.DataFrame(
        {
            "date": dates.values[day_idx],
            "store_id": store_ids[store_idx],
            "product_id": product_ids[prod_idx],
            "wastage_qty": qty_flat.astype(int),
            "wastage_cost_aud": wastage_cost,
            "wastage_reason": wastage_reason,
        }
    )


RAW_WASTAGE_COLUMN_MAPPING: dict[str, str] = {
    "date": "txn_date",
    "store_id": "site_code",
    "product_id": "sku_id",
    "wastage_qty": "qty",
    "wastage_cost_aud": "cost_amt",
    "wastage_reason": "reason_code",
}


def to_raw_wastage_rows(
    df: pd.DataFrame, seed: int = 43, messy_rate: float = 0.001
) -> pd.DataFrame:
    """Same deterministic messiness mechanism as to_raw_sales_rows: a null
    sku_id on ~messy_rate of rows, plus an equal share of duplicate rows.
    """
    rng = np.random.default_rng(seed * 23 + 13)
    raw = df.rename(columns=RAW_WASTAGE_COLUMN_MAPPING).reset_index(drop=True)

    n = len(raw)
    n_messy = max(1, int(n * messy_rate))

    null_key_idx = rng.choice(n, size=n_messy, replace=False)
    raw.loc[null_key_idx, "sku_id"] = None

    dup_idx = rng.choice(n, size=n_messy, replace=False)
    duplicates = raw.loc[dup_idx]

    return pd.concat([raw, duplicates], ignore_index=True)
