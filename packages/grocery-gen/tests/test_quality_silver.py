import pandas as pd

from grocery_gen.dimensions.products import generate_products, to_raw_product_rows
from grocery_gen.quality.silver import validate_primary_key


def test_drops_null_key_rows() -> None:
    df = pd.DataFrame(
        {"id": ["a", "b", None, "d"], "val": [1, 2, 3, 4]},
    )
    clean_df, violations = validate_primary_key(df, ["id"])
    assert violations == {"null": 1, "duplicate": 0}
    assert clean_df["id"].tolist() == ["a", "b", "d"]


def test_keeps_first_of_duplicate_key_rows() -> None:
    df = pd.DataFrame(
        {"id": ["a", "b", "b", "c", "b"], "val": [1, 2, 3, 4, 5]},
    )
    clean_df, violations = validate_primary_key(df, ["id"])
    assert violations == {"null": 0, "duplicate": 2}
    assert clean_df["id"].tolist() == ["a", "b", "c"]
    assert clean_df["val"].tolist() == [1, 2, 4]  # first "b" (val=2) kept


def test_clean_dataframe_has_no_violations() -> None:
    df = pd.DataFrame({"id": ["a", "b", "c"], "val": [1, 2, 3]})
    clean_df, violations = validate_primary_key(df, ["id"])
    assert violations == {"null": 0, "duplicate": 0}
    assert len(clean_df) == 3


def test_compound_primary_key() -> None:
    df = pd.DataFrame(
        {
            "department": ["Grocery", "Grocery", "Grocery", "Dairy"],
            "category": ["Snacks", "Snacks", "Drinks", "Milk"],
            "gst_exempt": [False, False, True, True],
        }
    )
    clean_df, violations = validate_primary_key(df, ["department", "category"])
    assert violations == {"null": 0, "duplicate": 1}
    assert len(clean_df) == 3


def test_against_real_generator_bronze_output() -> None:
    """Proves the suite catches exactly the deliberate issues to_raw_product_rows
    injects into Bronze-shaped product data — the same conformance check the
    Fabric Silver notebook's util_dq.Notebook mirrors for run_silver.Notebook.
    """
    products = generate_products(n=500, seed=42)
    raw = to_raw_product_rows(products, seed=42)
    df = pd.DataFrame([r.model_dump() for r in raw])

    clean_df, violations = validate_primary_key(df, ["sku_id"])

    assert violations["null"] == (df["sku_id"].isna()).sum()
    assert violations["null"] > 0
    assert violations["duplicate"] > 0
    assert clean_df["sku_id"].is_unique
    assert clean_df["sku_id"].notna().all()
