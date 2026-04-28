"""Tests for dim_product generation."""

from collections import Counter

import pytest

from grocery_gen.dimensions.products import ProductRow, generate_products
from grocery_gen.reference.taxonomy import SKU_ALLOCATION


def test_exact_count() -> None:
    products = generate_products(n=2000, seed=42)
    assert len(products) == 2000


def test_reproducibility() -> None:
    a = generate_products(n=500, seed=42)
    b = generate_products(n=500, seed=42)
    assert a == b


def test_different_seeds_differ() -> None:
    a = generate_products(n=500, seed=42)
    b = generate_products(n=500, seed=99)
    assert a != b


def test_department_distribution_within_tolerance() -> None:
    products = generate_products(n=2000, seed=42)
    counts = Counter(p.department for p in products)
    for department, target in SKU_ALLOCATION.items():
        assert abs(counts[department] - target) <= max(2, int(target * 0.05))


def test_fresh_produce_has_perishability_fields() -> None:
    products = generate_products(n=2000, seed=42)
    fresh = [p for p in products if p.department == "Fresh Produce"]
    assert fresh, "Expected fresh produce SKUs"
    for product in fresh:
        assert product.shelf_life_days is not None
        assert product.shelf_life_days > 0
        assert product.wastage_rate_baseline is not None
        assert 0.0 <= product.wastage_rate_baseline <= 1.0
        assert product.peak_season_months is not None


def test_fresh_produce_is_gst_free() -> None:
    products = generate_products(n=2000, seed=42)
    for product in products:
        if product.department == "Fresh Produce":
            assert product.gst_applicable is False


def test_alcohol_is_gst_applicable() -> None:
    products = generate_products(n=2000, seed=42)
    for product in products:
        if product.department == "Alcohol":
            assert product.gst_applicable is True


def test_seasonality_vectors_are_valid() -> None:
    products = generate_products(n=2000, seed=42)
    for product in products:
        assert len(product.seasonality_vector) == 12
        assert all(value >= 0 for value in product.seasonality_vector)


def test_retail_above_cost() -> None:
    products = generate_products(n=2000, seed=42)
    for product in products:
        assert product.retail_price_aud > product.cost_price_aud


def test_charm_pricing_endings() -> None:
    products = generate_products(n=2000, seed=42)
    valid_endings = {0.49, 0.79, 0.95, 0.99}
    for product in products:
        cents = round(product.retail_price_aud - int(product.retail_price_aud), 2)
        assert cents in valid_endings, f"{product.name}: ${product.retail_price_aud}"


def test_product_ids_unique_and_sorted() -> None:
    products = generate_products(n=2000, seed=42)
    ids = [p.product_id for p in products]
    assert len(set(ids)) == len(ids)
    assert ids == sorted(ids)


def test_supplier_ids_well_formed() -> None:
    products = generate_products(n=2000, seed=42)
    for product in products:
        assert product.supplier_id.startswith("SUP")
        assert len(product.supplier_id) == 7


def test_private_label_rate_in_pantry() -> None:
    products = generate_products(n=2000, seed=42)
    pantry = [p for p in products if p.department == "Pantry"]
    private = sum(1 for p in pantry if p.is_private_label)
    rate = private / len(pantry)
    assert 0.25 <= rate <= 0.45  # target 0.35, generous tolerance


@pytest.mark.parametrize("count", [50, 500, 2000])
def test_scales_to_arbitrary_count(count: int) -> None:
    products = generate_products(n=count, seed=42)
    assert len(products) == count
    assert all(isinstance(p, ProductRow) for p in products)
