"""Tests for reference data integrity."""

from grocery_gen.reference.fresh_goods import FRESH_GOODS_REFERENCE
from grocery_gen.reference.taxonomy import SKU_ALLOCATION, TAXONOMY


def test_sku_allocation_sums_to_2000() -> None:
    assert sum(SKU_ALLOCATION.values()) == 2000


def test_every_department_has_categories() -> None:
    for department in SKU_ALLOCATION:
        assert department in TAXONOMY
        assert len(TAXONOMY[department]) >= 3


def test_fresh_goods_reference_has_20_entries() -> None:
    assert len(FRESH_GOODS_REFERENCE) == 20


def test_fresh_goods_seasonality_vectors_valid() -> None:
    for spec in FRESH_GOODS_REFERENCE:
        assert len(spec.seasonality_vector) == 12
        assert all(value >= 0 for value in spec.seasonality_vector)


def test_fresh_goods_have_realistic_shelf_lives() -> None:
    for spec in FRESH_GOODS_REFERENCE:
        assert 1 <= spec.shelf_life_days <= 90


def test_fresh_goods_wastage_in_range() -> None:
    for spec in FRESH_GOODS_REFERENCE:
        assert 0.0 < spec.wastage_rate_baseline <= 0.30
