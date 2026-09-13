"""Tests for store dimension generation."""

from grocery_gen.dimensions.stores import generate_stores, to_raw_store_rows


def test_generates_requested_count() -> None:
    stores = generate_stores(n=50, seed=42)
    assert len(stores) == 50


def test_store_ids_are_unique() -> None:
    stores = generate_stores(n=200, seed=42)
    ids = [s.store_id for s in stores]
    assert len(ids) == len(set(ids))


def test_reproducible() -> None:
    assert generate_stores(n=100, seed=42) == generate_stores(n=100, seed=42)


def test_express_stores_have_no_deli_or_pharmacy() -> None:
    stores = generate_stores(n=300, seed=42)
    for s in stores:
        if s.store_format == "Express":
            assert s.has_deli is False
            assert s.has_pharmacy is False


def test_store_size_within_format_range() -> None:
    stores = generate_stores(n=300, seed=42)
    for s in stores:
        if s.store_format == "Supermarket":
            assert 2000 <= s.store_size_sqm < 4500


def test_raw_rows_reproducible() -> None:
    stores = generate_stores(n=150, seed=42)
    a = to_raw_store_rows(stores, seed=42)
    b = to_raw_store_rows(stores, seed=42)
    assert a == b


def test_raw_rows_have_null_keys_and_duplicates() -> None:
    stores = generate_stores(n=150, seed=42)
    raw = to_raw_store_rows(stores, seed=42)
    assert len(raw) > len(stores)
    assert sum(1 for r in raw if r.site_code is None) > 0
