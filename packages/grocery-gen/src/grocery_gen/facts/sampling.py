"""Shared product sampling for fact generation.

Facts run against a deliberately small slice of the full 2000-SKU catalogue
(DR-011) rather than the whole thing — a uniform random sample rather than
the first N, since product_id is assigned sequentially per department
(products.py sorts by product_id after generation), so "first 50" would
mean "50 Pantry products and nothing else." A uniform sample preserves
each department's share of the catalogue in expectation.
"""

import numpy as np

from grocery_gen.dimensions.products import ProductRow


def sample_products(products: list[ProductRow], n: int, seed: int) -> list[ProductRow]:
    if n >= len(products):
        return list(products)
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(products), size=n, replace=False)
    sampled = [products[i] for i in sorted(idx.tolist())]
    return sampled
