"""Tests for customer dimension generation."""

from grocery_gen.dimensions.customers import generate_customers, to_raw_customer_rows


def test_generates_requested_count() -> None:
    customers = generate_customers(n=500, seed=42, num_stores=150)
    assert len(customers) == 500


def test_customer_ids_are_unique() -> None:
    customers = generate_customers(n=2000, seed=42, num_stores=150)
    ids = [c.customer_id for c in customers]
    assert len(ids) == len(set(ids))


def test_reproducible() -> None:
    a = generate_customers(n=500, seed=42, num_stores=150)
    b = generate_customers(n=500, seed=42, num_stores=150)
    assert a == b


def test_preferred_store_id_mix_has_valid_none_and_orphan() -> None:
    """Deliberate FK mix for Gold's referential-integrity check to catch:
    mostly valid STR-#### ids within num_stores, some None (no preference,
    a legitimate business value — not a DQ issue), and a fixed orphan id
    that matches no real store (a genuine RI violation).
    """
    customers = generate_customers(n=2000, seed=42, num_stores=150)
    store_ids = [c.preferred_store_id for c in customers]

    valid_ids = {f"STR-{i:04d}" for i in range(1, 151)}
    assert any(sid in valid_ids for sid in store_ids)
    assert any(sid is None for sid in store_ids)
    assert any(sid == "STR-9999" for sid in store_ids)
    assert all(sid is None or sid in valid_ids or sid == "STR-9999" for sid in store_ids)


def test_raw_rows_reproducible() -> None:
    customers = generate_customers(n=500, seed=42, num_stores=150)
    a = to_raw_customer_rows(customers, seed=42)
    b = to_raw_customer_rows(customers, seed=42)
    assert a == b


def test_raw_rows_have_null_keys_and_duplicates() -> None:
    customers = generate_customers(n=500, seed=42, num_stores=150)
    raw = to_raw_customer_rows(customers, seed=42)
    assert len(raw) > len(customers)
    assert sum(1 for r in raw if r.member_id is None) > 0
