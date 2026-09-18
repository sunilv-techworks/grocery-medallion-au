"""Sales fact generator — daily grain per (date, store, product).

DR-011: at even a deliberately small scale (50 products x 150 stores x 2
years), the dense date x store x product grid is ~5.5M cells, so this is
vectorised with numpy/pandas rather than the per-row pydantic style
dimensions/ uses — a pydantic-per-row loop at this size is minutes, not
seconds. Sparsity (no fact row for a day/store/product with zero sales)
falls out of the Poisson quantity draw itself rather than a separate
"did it sell" step.
"""

from datetime import date

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from grocery_gen.dimensions.products import ProductRow
from grocery_gen.dimensions.stores import STORE_FORMAT_VELOCITY_MULTIPLIER, StoreRow
from grocery_gen.reference.taxonomy import Department

# Expected units sold per store per day for a "typical" product in this
# department, at a Metro-format store, on an average (non-seasonal,
# weekday) day. Hand-tuned by department character — matches the rest of
# the codebase's hand-crafted-not-simulated reference data.
BASE_DAILY_UNITS_BY_DEPARTMENT: dict[Department, float] = {
    "Dairy": 9.0,
    "Bakery": 10.0,
    "Fresh Produce": 7.0,
    "Pantry": 4.0,
    "Beverages": 5.0,
    "Frozen": 3.5,
    "Meat & Seafood": 3.5,
    "Household": 1.8,
    "Health & Beauty": 1.5,
    "Alcohol": 2.0,
}

WEEKEND_MULTIPLIER = 1.35
PROMO_DAILY_PROBABILITY = 0.05
PROMO_DISCOUNT_RANGE = (0.10, 0.30)

SALES_FACT_COLUMNS = [
    "date",
    "store_id",
    "product_id",
    "quantity_sold",
    "unit_price_aud",
    "is_promo",
    "revenue_aud",
    "cost_aud",
    "gst_amount_aud",
]


def generate_sales_facts(
    products: list[ProductRow],
    stores: list[StoreRow],
    start: date,
    end: date,
    seed: int = 42,
) -> pd.DataFrame:
    """One row per (date, store, product) that sold at least one unit.

    Rate combines: department base velocity x store-format multiplier x
    weekend bump x the product's own seasonality_vector for that month —
    reusing the exact vector dim_product/DR-005 already generates and
    DQ-checks, rather than inventing a separate seasonality model for
    facts. Promotions apply the same discount to every store selling a
    given product on a given date (a catalogue promo, not a per-store one).
    """
    if not products or not stores:
        return pd.DataFrame(columns=SALES_FACT_COLUMNS)

    rng = np.random.default_rng(seed)

    dates = pd.date_range(start, end, freq="D")
    n_days = len(dates)

    weekend_mult = np.where(dates.weekday.to_numpy() >= 5, WEEKEND_MULTIPLIER, 1.0)  # (n_days,)
    month_idx = dates.month.to_numpy() - 1  # (n_days,)

    base = np.array([BASE_DAILY_UNITS_BY_DEPARTMENT[p.department] for p in products])
    format_mult = np.array([STORE_FORMAT_VELOCITY_MULTIPLIER[s.store_format] for s in stores])
    seasonality = np.array([p.seasonality_vector for p in products])  # (n_products, 12)
    season_mult = seasonality[:, month_idx].T  # (n_days, n_products)

    lam = (
        base[None, None, :]
        * format_mult[None, :, None]
        * weekend_mult[:, None, None]
        * season_mult[:, None, :]
    )  # (n_days, n_stores, n_products)

    quantity = rng.poisson(lam)

    promo_mask = (
        rng.random((n_days, len(products))) < PROMO_DAILY_PROBABILITY
    )  # (n_days, n_products)
    discount_pct = np.where(
        promo_mask,
        rng.uniform(*PROMO_DISCOUNT_RANGE, size=(n_days, len(products))),
        0.0,
    )

    day_idx, store_idx, prod_idx = np.nonzero(quantity)
    if len(day_idx) == 0:
        return pd.DataFrame(columns=SALES_FACT_COLUMNS)

    qty_flat = quantity[day_idx, store_idx, prod_idx]

    retail_price = np.array([p.retail_price_aud for p in products])
    cost_price = np.array([p.cost_price_aud for p in products])
    gst_applicable = np.array([p.gst_applicable for p in products])
    product_ids = np.array([p.product_id for p in products])
    store_ids = np.array([s.store_id for s in stores])

    unit_price = np.round(retail_price[prod_idx] * (1 - discount_pct[day_idx, prod_idx]), 2)
    is_promo = promo_mask[day_idx, prod_idx]
    revenue = np.round(qty_flat * unit_price, 2)
    cost = np.round(qty_flat * cost_price[prod_idx], 2)
    gst_amount = np.where(gst_applicable[prod_idx], np.round(revenue / 11, 2), 0.0)

    return pd.DataFrame(
        {
            "date": dates.values[day_idx],
            "store_id": store_ids[store_idx],
            "product_id": product_ids[prod_idx],
            "quantity_sold": qty_flat.astype(int),
            "unit_price_aud": unit_price,
            "is_promo": is_promo,
            "revenue_aud": revenue,
            "cost_aud": cost,
            "gst_amount_aud": gst_amount,
        }
    )


RAW_SALES_COLUMN_MAPPING: dict[str, str] = {
    "date": "txn_date",
    "store_id": "site_code",
    "product_id": "sku_id",
    "quantity_sold": "qty",
    "unit_price_aud": "unit_price",
    "is_promo": "promo_flag",
    "revenue_aud": "line_revenue",
    "cost_aud": "line_cost",
    "gst_amount_aud": "gst_amt",
}


def to_raw_sales_rows(df: pd.DataFrame, seed: int = 42, messy_rate: float = 0.001) -> pd.DataFrame:
    """Rename to source-shaped columns and inject deterministic quality
    issues at fact scale: a null sku_id on ~messy_rate of rows (the natural
    key Silver's compound-primary-key check catches), and an equal share of
    exact duplicate rows appended. Same idea as to_raw_product_rows, done
    with pandas ops instead of per-row model_copy — millions of rows, not
    thousands.
    """
    rng = np.random.default_rng(seed * 19 + 11)
    raw = df.rename(columns=RAW_SALES_COLUMN_MAPPING).reset_index(drop=True)

    n = len(raw)
    n_messy = max(1, int(n * messy_rate))

    null_key_idx = rng.choice(n, size=n_messy, replace=False)
    raw.loc[null_key_idx, "sku_id"] = None

    dup_idx = rng.choice(n, size=n_messy, replace=False)
    duplicates = raw.loc[dup_idx]

    return pd.concat([raw, duplicates], ignore_index=True)
