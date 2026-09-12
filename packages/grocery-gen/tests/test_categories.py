"""Tests for category_master generation."""

from grocery_gen.dimensions.categories import generate_categories
from grocery_gen.reference.taxonomy import TAXONOMY


def test_covers_every_taxonomy_entry() -> None:
    categories = generate_categories()
    pairs = {(c.department, c.category) for c in categories}
    expected = {(dept, cat) for dept, cats in TAXONOMY.items() for cat in cats}
    assert pairs == expected


def test_no_duplicate_pairs() -> None:
    categories = generate_categories()
    pairs = [(c.department, c.category) for c in categories]
    assert len(pairs) == len(set(pairs))


def test_fresh_produce_categories_are_gst_exempt() -> None:
    categories = generate_categories()
    for c in categories:
        if c.department == "Fresh Produce":
            assert c.gst_exempt is True


def test_bakery_bread_is_gst_exempt_but_bakery_generally_is_not() -> None:
    categories = {(c.department, c.category): c for c in generate_categories()}
    assert categories[("Bakery", "Bread")].gst_exempt is True
    assert categories[("Bakery", "Sweet Baked")].gst_exempt is False


def test_reproducible() -> None:
    assert generate_categories() == generate_categories()
