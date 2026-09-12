"""Category reference dimension — surfaces the taxonomy + GST rules already
used internally by the product generator as an actual dataset, rather than
leaving them as hidden Python constants only the generator itself can see.
"""

from pydantic import BaseModel, ConfigDict

from grocery_gen.reference.pricing import is_gst_applicable
from grocery_gen.reference.taxonomy import TAXONOMY, Department


class CategoryRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    department: Department
    category: str
    gst_exempt: bool


def generate_categories() -> list[CategoryRow]:
    """One row per (department, category) pair in TAXONOMY.

    Deterministic and exhaustive — every department/category combination a
    product can be assigned is guaranteed to appear here, since both derive
    from the same TAXONOMY source of truth.
    """
    rows: list[CategoryRow] = []
    for department, categories in TAXONOMY.items():
        for category in categories:
            rows.append(
                CategoryRow(
                    department=department,
                    category=category,
                    gst_exempt=not is_gst_applicable(department, category),
                )
            )
    rows.sort(key=lambda r: (r.department, r.category))
    return rows
