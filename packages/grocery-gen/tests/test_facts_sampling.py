from grocery_gen.dimensions.products import generate_products
from grocery_gen.facts.sampling import sample_products


def test_samples_requested_count() -> None:
    products = generate_products(n=500, seed=42)
    sampled = sample_products(products, n=50, seed=42)
    assert len(sampled) == 50


def test_sample_is_unique_subset() -> None:
    products = generate_products(n=500, seed=42)
    sampled = sample_products(products, n=50, seed=42)
    ids = [p.product_id for p in sampled]
    assert len(ids) == len(set(ids))
    all_ids = {p.product_id for p in products}
    assert set(ids).issubset(all_ids)


def test_reproducible() -> None:
    products = generate_products(n=500, seed=42)
    a = sample_products(products, n=50, seed=42)
    b = sample_products(products, n=50, seed=42)
    assert [p.product_id for p in a] == [p.product_id for p in b]


def test_n_greater_than_population_returns_all() -> None:
    products = generate_products(n=20, seed=42)
    sampled = sample_products(products, n=100, seed=42)
    assert len(sampled) == 20


def test_sample_spans_multiple_departments() -> None:
    """Guards against the 'first N products' trap: product_id is assigned
    sequentially per department, so without real sampling a naive slice
    would be all one department.
    """
    products = generate_products(n=2000, seed=42)
    sampled = sample_products(products, n=50, seed=42)
    departments = {p.department for p in sampled}
    assert len(departments) > 1
