from datetime import date

import pandas as pd

from grocery_gen.dimensions.products import generate_products
from grocery_gen.dimensions.stores import generate_stores
from grocery_gen.facts.sampling import sample_products
from grocery_gen.facts.wastage import generate_wastage_facts, to_raw_wastage_rows


def _sample() -> tuple[list, list]:
    products = sample_products(generate_products(n=300, seed=42), n=30, seed=42)
    stores = generate_stores(n=5, seed=42)
    return products, stores


def test_generates_rows_only_for_perishable_products() -> None:
    products, stores = _sample()
    df = generate_wastage_facts(products, stores, date(2024, 1, 1), date(2024, 3, 31), seed=43)
    perishable_ids = {p.product_id for p in products if p.shelf_life_days is not None}
    assert len(df) > 0
    assert set(df["product_id"]).issubset(perishable_ids)


def test_no_wastage_for_non_perishables() -> None:
    products, stores = _sample()
    df = generate_wastage_facts(products, stores, date(2024, 1, 1), date(2024, 3, 31), seed=43)
    non_perishable_ids = {p.product_id for p in products if p.shelf_life_days is None}
    assert not set(df["product_id"]) & non_perishable_ids


def test_reproducible() -> None:
    products, stores = _sample()
    a = generate_wastage_facts(products, stores, date(2024, 1, 1), date(2024, 1, 31), seed=43)
    b = generate_wastage_facts(products, stores, date(2024, 1, 1), date(2024, 1, 31), seed=43)
    pd.testing.assert_frame_equal(a, b)


def test_positive_quantities_and_costs() -> None:
    products, stores = _sample()
    df = generate_wastage_facts(products, stores, date(2024, 1, 1), date(2024, 3, 31), seed=43)
    assert (df["wastage_qty"] > 0).all()
    assert (df["wastage_cost_aud"] > 0).all()


def test_reason_codes_are_from_known_set() -> None:
    products, stores = _sample()
    df = generate_wastage_facts(products, stores, date(2024, 1, 1), date(2024, 3, 31), seed=43)
    assert set(df["wastage_reason"]).issubset(
        {"Spoilage", "Damaged in Handling", "Expired on Shelf"}
    )


def test_no_perishables_returns_empty_frame() -> None:
    products = [p for p in generate_products(n=300, seed=42) if p.shelf_life_days is None][:10]
    stores = generate_stores(n=5, seed=42)
    df = generate_wastage_facts(products, stores, date(2024, 1, 1), date(2024, 1, 31), seed=43)
    assert len(df) == 0


def test_raw_rows_have_null_keys_and_duplicates() -> None:
    products, stores = _sample()
    df = generate_wastage_facts(products, stores, date(2024, 1, 1), date(2024, 3, 31), seed=43)
    raw = to_raw_wastage_rows(df, seed=43, messy_rate=0.01)
    assert len(raw) > len(df)
    assert raw["sku_id"].isna().sum() > 0
