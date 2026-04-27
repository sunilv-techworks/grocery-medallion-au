"""Product dimension generator for AU grocery SKUs."""

from typing import Literal

from pydantic import BaseModel


class ProductRow(BaseModel):
    product_id: str
    sku: str
    name: str
    department: Literal[
        "Fresh Produce",
        "Bakery",
        "Dairy",
        "Meat & Seafood",
        "Pantry",
        "Frozen",
        "Beverages",
        "Alcohol",
        "Health & Beauty",
        "Household",
    ]
    category: str
    subcategory: str
    brand: str
    is_private_label: bool
    unit_of_measure: Literal["each", "kg", "g", "L", "mL", "pack"]
    pack_size: float
    cost_price_aud: float
    retail_price_aud: float
    gst_applicable: bool  # False for fresh food under Australian GST law
    shelf_life_days: int | None  # None for non-perishables
    peak_season_months: list[int] | None  # e.g. [12, 1, 2] for mangoes (summer)
    wastage_rate_baseline: float | None  # 0.0-1.0 fraction for fresh departments
    supplier_id: str


def generate_products(n: int, seed: int) -> list[ProductRow]:
    """Generate n synthetic product dimension rows.

    Realism rules to implement in Phase 2:
    - GST exemption: gst_applicable=False for all Fresh Produce, Bakery, and Dairy lines
      per the A New Tax System (Goods and Services Tax) Act 1999 basic food exemption.
    - Seasonal produce: peak_season_months populated from AU seasonal calendar
      (e.g. mangoes Dec-Feb, strawberries Sep-Nov, stone fruit Nov-Feb).
    - Wastage rates: Fresh Produce 8-15%, Meat & Seafood 3-6%, Bakery 10-20%,
      None for shelf-stable categories.
    - Private label ratio: ~25% of SKUs flagged is_private_label=True.
    - Price margin: retail_price_aud derived from cost_price_aud with realistic
      category-specific margins (Fresh ~30%, Pantry ~20%, Alcohol ~40%).
    """
    raise NotImplementedError("Product generation will be implemented in Phase 2.")
