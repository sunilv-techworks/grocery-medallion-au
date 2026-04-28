"""Seasonality vector helpers and pre-built patterns for AU grocery categories."""

import numpy as np

from grocery_gen.reference.taxonomy import Department

ICE_CREAM_VECTOR: list[float] = [1.6, 1.6, 1.4, 1.0, 0.7, 0.5, 0.5, 0.6, 0.9, 1.2, 1.4, 1.7]
SOUP_VECTOR: list[float] = [0.6, 0.7, 0.9, 1.2, 1.5, 1.7, 1.7, 1.5, 1.2, 1.0, 0.7, 0.6]
BBQ_VECTOR: list[float] = [1.6, 1.5, 1.3, 1.0, 0.7, 0.6, 0.6, 0.7, 0.9, 1.2, 1.4, 1.7]
EASTER_CHOC_VECTOR: list[float] = [0.8, 0.9, 1.6, 2.2, 1.0, 0.9, 0.9, 0.9, 0.9, 1.0, 1.0, 1.4]
CHRISTMAS_VECTOR: list[float] = [0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 1.0, 1.1, 1.2, 1.4, 2.2]


def flat_vector() -> list[float]:
    return [1.0] * 12


def wobble_vector(rng: np.random.Generator, amplitude: float = 0.1) -> list[float]:
    return [round(float(v), 2) for v in rng.uniform(1.0 - amplitude, 1.0 + amplitude, 12)]


def vector_to_peak_months(vector: list[float], threshold: float = 1.2) -> list[int]:
    return [i + 1 for i, v in enumerate(vector) if v >= threshold]


def validate_vector(vector: list[float]) -> None:
    if len(vector) != 12:
        raise ValueError(f"Seasonality vector must have 12 elements, got {len(vector)}")
    if any(v < 0 for v in vector):
        raise ValueError("Seasonality vector contains negative values")


def category_seasonality(
    department: Department,
    category: str,
    subcategory: str,
    rng: np.random.Generator,
) -> list[float]:
    sub_lower = subcategory.lower()
    cat_lower = category.lower()
    if "ice cream" in sub_lower or "frozen dessert" in sub_lower:
        return list(ICE_CREAM_VECTOR)
    if "soup" in sub_lower or "soup" in cat_lower:
        return list(SOUP_VECTOR)
    if "bbq" in sub_lower or "sausage" in sub_lower or subcategory == "Bacon":
        return list(BBQ_VECTOR)
    if "confectionery" in sub_lower or "chocolate" in sub_lower:
        return list(EASTER_CHOC_VECTOR)
    if department == "Alcohol" and "sparkling" in sub_lower:
        return list(CHRISTMAS_VECTOR)
    return wobble_vector(rng)
