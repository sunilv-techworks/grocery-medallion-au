"""Pricing parameters, GST rules, and charm-pricing helpers per department."""

import numpy as np

from grocery_gen.reference.taxonomy import Department

MARGIN_BY_DEPARTMENT: dict[Department, float] = {
    "Fresh Produce": 0.30,
    "Meat & Seafood": 0.28,
    "Bakery": 0.32,
    "Dairy": 0.25,
    "Pantry": 0.25,
    "Beverages": 0.30,
    "Frozen": 0.28,
    "Alcohol": 0.20,
    "Health & Beauty": 0.40,
    "Household": 0.30,
}

COST_DISTRIBUTION_BY_DEPARTMENT: dict[Department, tuple[float, float, float]] = {
    "Fresh Produce": (1.00, 3.00, 12.00),
    "Bakery": (2.00, 4.50, 10.00),
    "Dairy": (1.50, 5.00, 18.00),
    "Meat & Seafood": (5.00, 12.00, 45.00),
    "Pantry": (1.00, 4.00, 25.00),
    "Frozen": (2.50, 7.00, 18.00),
    "Beverages": (1.00, 3.50, 15.00),
    "Alcohol": (8.00, 18.00, 80.00),
    "Health & Beauty": (2.00, 8.00, 40.00),
    "Household": (1.50, 6.00, 25.00),
}

GST_FREE_DEPARTMENTS: set[Department] = {"Fresh Produce", "Meat & Seafood"}

GST_FREE_CATEGORIES: set[tuple[Department, str]] = {
    ("Bakery", "Bread"),
    ("Dairy", "Milk"),
    ("Dairy", "Yoghurt & Eggs"),
    ("Pantry", "Breakfast"),
}


def is_gst_applicable(department: Department, category: str) -> bool:
    if department in GST_FREE_DEPARTMENTS:
        return False
    return (department, category) not in GST_FREE_CATEGORIES


CHARM_PRICE_ENDINGS: tuple[float, ...] = (0.49, 0.79, 0.95, 0.99)


def apply_charm_pricing(price: float, rng: np.random.Generator) -> float:
    ending = float(rng.choice(np.array(CHARM_PRICE_ENDINGS)))
    if price < 1.0:
        return round(ending, 2)
    dollar_floor = int(price)
    return round(dollar_floor + ending, 2)
