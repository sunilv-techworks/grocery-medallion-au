from datetime import date

import pandas as pd

from grocery_gen.dimensions.products import generate_products
from grocery_gen.dimensions.stores import generate_stores
from grocery_gen.facts.sales import generate_sales_facts, to_raw_sales_rows
from grocery_gen.facts.sampling import sample_products


def _sample() -> tuple[list, list]:
    products = sample_products(generate_products(n=200, seed=42), n=10, seed=42)
    stores = generate_stores(n=5, seed=42)
    return products, stores


def test_generates_rows_within_date_range() -> None:
    products, stores = _sample()
    df = generate_sales_facts(products, stores, date(2024, 1, 1), date(2024, 1, 31), seed=42)
    assert len(df) > 0
    assert (df["date"] >= "2024-01-01").all()
    assert (df["date"] <= "2024-01-31").all()


def test_no_zero_or_negative_quantity_rows() -> None:
    products, stores = _sample()
    df = generate_sales_facts(products, stores, date(2024, 1, 1), date(2024, 1, 31), seed=42)
    assert (df["quantity_sold"] > 0).all()


def test_reproducible() -> None:
    products, stores = _sample()
    a = generate_sales_facts(products, stores, date(2024, 1, 1), date(2024, 1, 31), seed=42)
    b = generate_sales_facts(products, stores, date(2024, 1, 1), date(2024, 1, 31), seed=42)
    pd.testing.assert_frame_equal(a, b)


def test_only_known_store_and_product_ids_appear() -> None:
    products, stores = _sample()
    df = generate_sales_facts(products, stores, date(2024, 1, 1), date(2024, 3, 31), seed=42)
    valid_products = {p.product_id for p in products}
    valid_stores = {s.store_id for s in stores}
    assert set(df["product_id"]).issubset(valid_products)
    assert set(df["store_id"]).issubset(valid_stores)


def test_gst_amount_zero_when_not_applicable() -> None:
    products, stores = _sample()
    df = generate_sales_facts(products, stores, date(2024, 1, 1), date(2024, 6, 30), seed=42)
    gst_free_ids = {p.product_id for p in products if not p.gst_applicable}
    gst_free_rows = df[df["product_id"].isin(gst_free_ids)]
    assert (gst_free_rows["gst_amount_aud"] == 0.0).all()


def test_empty_inputs_return_empty_frame() -> None:
    df = generate_sales_facts([], [], date(2024, 1, 1), date(2024, 1, 2), seed=42)
    assert len(df) == 0


def test_raw_rows_have_null_keys_and_duplicates() -> None:
    products, stores = _sample()
    df = generate_sales_facts(products, stores, date(2024, 1, 1), date(2024, 3, 31), seed=42)
    raw = to_raw_sales_rows(df, seed=42, messy_rate=0.01)
    assert len(raw) > len(df)
    assert raw["sku_id"].isna().sum() > 0
    assert "txn_date" in raw.columns
