"""Product dimension generator for AU grocery SKUs."""

from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict

from grocery_gen.reference.brands import BRAND_POOLS, PRIVATE_LABEL_NAME, PRIVATE_LABEL_RATE
from grocery_gen.reference.fresh_goods import FRESH_GOODS_REFERENCE
from grocery_gen.reference.pricing import (
    COST_DISTRIBUTION_BY_DEPARTMENT,
    MARGIN_BY_DEPARTMENT,
    apply_charm_pricing,
    is_gst_applicable,
)
from grocery_gen.reference.seasonality import category_seasonality, vector_to_peak_months
from grocery_gen.reference.taxonomy import SKU_ALLOCATION, TAXONOMY, Department

_PERISHABLE_DEPARTMENTS = {"Fresh Produce", "Bakery", "Dairy", "Meat & Seafood", "Frozen"}
_PERISHABLE_CATEGORIES = {
    "Bread",
    "Sweet Baked",
    "Savoury Baked",
    "Milk",
    "Yoghurt & Eggs",
    "Cheese",
    "Beef & Lamb",
    "Poultry",
    "Pork & Smallgoods",
    "Seafood",
    "Ice Cream & Desserts",
}

_SHELF_LIFE_DEFAULTS: dict[str, int] = {
    "Bread": 3,
    "Sweet Baked": 4,
    "Savoury Baked": 3,
    "Milk": 10,
    "Yoghurt & Eggs": 14,
    "Cheese": 30,
    "Beef & Lamb": 5,
    "Poultry": 4,
    "Pork & Smallgoods": 7,
    "Seafood": 3,
    "Ice Cream & Desserts": 180,
}

_WASTAGE_DEFAULTS: dict[str, float] = {
    "Bread": 0.08,
    "Sweet Baked": 0.12,
    "Savoury Baked": 0.10,
    "Milk": 0.05,
    "Yoghurt & Eggs": 0.04,
    "Cheese": 0.03,
    "Beef & Lamb": 0.04,
    "Poultry": 0.04,
    "Pork & Smallgoods": 0.05,
    "Seafood": 0.06,
    "Ice Cream & Desserts": 0.02,
}

_NAME_TEMPLATES: dict[str, list[str]] = {
    "Dried Pasta": ["Spaghetti #5", "Penne Rigate", "Fusilli", "Fettuccine", "Linguine"],
    "Rice": ["Jasmine Rice", "Basmati Rice", "Medium Grain Rice", "Brown Rice"],
    "Noodles": ["Rice Noodles", "Egg Noodles", "Udon", "Soba"],
    "Oils & Vinegars": [
        "Extra Virgin Olive Oil",
        "Vegetable Oil",
        "Balsamic Vinegar",
        "Rice Vinegar",
    ],
    "Sauces & Condiments": ["Tomato Sauce", "Soy Sauce", "BBQ Sauce", "Mayonnaise", "Mustard"],
    "Spices & Seasonings": ["Mixed Herbs", "Garlic Powder", "Cumin Ground", "Paprika", "Sea Salt"],
    "Stock & Broth": ["Chicken Stock", "Beef Stock", "Vegetable Stock", "Fish Stock"],
    "Flour & Sugar": ["Plain Flour", "Self Raising Flour", "Caster Sugar", "Brown Sugar"],
    "Baking Mixes": ["Pancake Mix", "Banana Bread Mix", "Brownie Mix", "Scone Mix"],
    "Cereals": ["Wheat Flakes", "Corn Flakes", "Oat Flakes", "Bran Flakes", "Puffed Rice"],
    "Spreads": ["Peanut Butter", "Almond Butter", "Honey", "Vegemite-style Spread", "Jam"],
    "Muesli & Granola": ["Natural Muesli", "Toasted Granola", "Bircher Muesli"],
    "Chips & Crisps": ["Potato Chips Original", "Corn Chips", "Rice Crackers", "Pretzels"],
    "Biscuits": ["Butter Biscuits", "Choc Chip Cookies", "Digestives", "Shortbread"],
    "Confectionery": ["Milk Chocolate Block", "Dark Chocolate Block", "Jelly Beans", "Licorice"],
    "Nuts & Seeds": ["Roasted Almonds", "Cashews", "Trail Mix", "Sunflower Seeds"],
    "Cola": ["Cola Original", "Diet Cola", "Zero Sugar Cola"],
    "Lemonade": ["Classic Lemonade", "Pink Lemonade", "Sparkling Lemon"],
    "Energy Drinks": ["Blue Energy", "Green Energy", "Sugar-Free Energy"],
    "Mixers": ["Tonic Water", "Ginger Ale", "Soda Water", "Dry Ginger"],
    "Coffee": ["Ground Coffee", "Instant Coffee", "Coffee Pods", "Decaf Coffee"],
    "Tea": ["Black Tea", "Green Tea", "Chamomile Tea", "Peppermint Tea"],
    "Hot Chocolate": ["Drinking Chocolate", "Malted Hot Chocolate"],
    "Fruit Juice": ["Orange Juice", "Apple Juice", "Tropical Juice", "Cranberry Juice"],
    "Bottled Water": ["Still Spring Water", "Mineral Water"],
    "Sparkling Water": ["Sparkling Mineral Water", "Flavoured Sparkling Water"],
    "Premium Lager": ["Pale Lager 6-Pack", "Premium Lager Bottle"],
    "Mainstream Lager": ["Full Strength Lager 24-Pack", "Mid Strength Lager"],
    "Craft": ["IPA 4-Pack", "Pale Ale", "Stout 4-Pack"],
    "Cider": ["Apple Cider 6-Pack", "Pear Cider 4-Pack"],
    "Red Wine": ["Shiraz 750mL", "Cabernet Sauvignon 750mL", "Merlot 750mL"],
    "White Wine": ["Sauvignon Blanc 750mL", "Chardonnay 750mL", "Pinot Grigio 750mL"],
    "Sparkling": ["Sparkling Brut 750mL", "Prosecco 750mL"],
    "Cask": ["Red Wine Cask 4L", "White Wine Cask 2L"],
    "Whisky": ["Blended Scotch Whisky 700mL", "Bourbon 700mL"],
    "Vodka": ["Vodka 700mL", "Flavoured Vodka 700mL"],
    "Gin": ["London Dry Gin 700mL", "Australian Gin 700mL"],
    "Rum": ["Dark Rum 700mL", "White Rum 700mL"],
    "Full Cream": ["Full Cream Milk 2L", "Full Cream Milk 1L"],
    "Reduced Fat": ["Reduced Fat Milk 2L", "Lite Milk 1L"],
    "Plant-Based": ["Oat Milk 1L", "Almond Milk 1L", "Soy Milk 1L"],
    "Flavoured": ["Chocolate Milk 1L", "Strawberry Milk 600mL"],
    "Block Cheese": ["Tasty Cheese 500g", "Colby Cheese 500g", "Parmesan Block 200g"],
    "Sliced Cheese": ["Tasty Slices 500g", "Swiss Slices 200g"],
    "Specialty Cheese": ["Brie 125g", "Feta 200g", "Blue Cheese 150g"],
    "Yoghurt": ["Greek Yoghurt 500g", "Natural Yoghurt 1kg", "Flavoured Yoghurt 150g"],
    "Eggs": ["Free Range Eggs 12pk", "Cage Free Eggs 12pk", "Organic Eggs 6pk"],
    "Cream": ["Thickened Cream 300mL", "Sour Cream 200g", "Light Cream 300mL"],
    "Sliced Bread": ["White Sandwich Bread", "Wholemeal Sandwich Bread", "Multigrain Bread"],
    "Rolls": ["Dinner Rolls 6pk", "Burger Buns 4pk", "Bread Rolls 4pk"],
    "Specialty Loaves": ["Sourdough Loaf", "Rye Bread", "Ciabatta"],
    "Wraps & Flatbreads": ["Flour Tortillas 8pk", "Wholemeal Wraps 8pk", "Lebanese Bread 5pk"],
    "Cakes": ["Chocolate Mud Cake", "Carrot Cake Slice", "Lamington 6pk"],
    "Pastries": ["Croissant 2pk", "Danish Pastry 4pk", "Pain au Chocolat 2pk"],
    "Doughnuts": ["Glazed Doughnuts 6pk", "Jam Doughnuts 4pk"],
    "Pies & Pasties": ["Beef Pie", "Chicken & Mushroom Pie", "Vegetable Pasty"],
    "Sausage Rolls": ["Sausage Rolls 4pk", "Mini Sausage Rolls 12pk"],
    "Quiche": ["Lorraine Quiche", "Spinach & Feta Quiche"],
    "Mince": ["Beef Mince 500g", "Lamb Mince 500g", "Premium Beef Mince 500g"],
    "Steaks": ["Rump Steak 400g", "Sirloin Steak 300g", "Eye Fillet 250g"],
    "Roasts": ["Beef Roast 1kg", "Lamb Leg 1.5kg"],
    "Lamb Cuts": ["Lamb Chops 500g", "Lamb Shoulder 1kg", "Lamb Cutlets 300g"],
    "Chicken Breast": ["Chicken Breast 500g", "Chicken Tenderloins 500g"],
    "Chicken Whole": ["Whole Chicken 1.6kg", "Chicken Thighs 500g"],
    "Turkey": ["Turkey Breast Roast 1kg"],
    "Pork Cuts": ["Pork Chops 500g", "Pork Belly 500g"],
    "Bacon": ["Streaky Bacon 500g", "Short Cut Bacon 200g", "Middle Bacon 500g"],
    "Ham": ["Leg Ham 200g", "Double Smoked Ham 200g"],
    "Sausages": ["Beef Sausages 500g", "Pork Sausages 500g", "Cheese Kransky 500g"],
    "Fresh Fish": ["Atlantic Salmon Fillet 300g", "Barramundi Fillet 300g", "Bream 400g"],
    "Prawns": ["Raw King Prawns 500g", "Cooked Prawns 500g"],
    "Shellfish": ["Mussels 500g", "Oysters 12pk", "Scallops 300g"],
    "Ready Meals": ["Beef Lasagne 400g", "Chicken Curry 400g", "Butter Chicken 400g"],
    "Pizza": ["Margherita Pizza", "BBQ Chicken Pizza", "Pepperoni Pizza"],
    "Frozen Asian": ["Dumplings 600g", "Spring Rolls 600g", "Fried Rice 800g"],
    "Frozen Vegetables": ["Mixed Vegetables 500g", "Peas 500g", "Corn Kernels 500g"],
    "Frozen Berries": ["Mixed Berries 500g", "Blueberries 500g", "Raspberries 300g"],
    "Ice Cream Tubs": ["Vanilla Ice Cream 2L", "Chocolate Ice Cream 2L", "Strawberry Ice Cream 1L"],
    "Ice Cream Sticks": ["Vanilla Choc Dip 4pk", "Mango Sorbet Stick 4pk"],
    "Frozen Desserts": ["Cheesecake Slice 400g", "Pavlova Shell 450g"],
    "Hair Care": ["Shampoo 400mL", "Conditioner 400mL", "2-in-1 Shampoo 400mL", "Dry Shampoo"],
    "Skin Care": ["Moisturising Lotion 200mL", "Sunscreen SPF50 200mL", "Facial Wash 150mL"],
    "Oral Care": ["Toothpaste 110g", "Toothbrush 2pk", "Mouthwash 500mL", "Dental Floss"],
    "Deodorant": ["Deodorant Stick 50g", "Deodorant Spray 150mL", "Roll-On Deodorant 50mL"],
    "Vitamins": ["Vitamin C 60pk", "Multivitamin 60pk", "Vitamin D3 60pk", "Fish Oil 60pk"],
    "Pain Relief": ["Paracetamol 20pk", "Ibuprofen 24pk", "Aspirin 100pk"],
    "First Aid": ["Bandages 20pk", "Antiseptic Cream 50g", "Disposable Gloves 10pk"],
    "Nappies": ["Nappies Size 2 40pk", "Nappies Size 3 34pk", "Nappies Size 4 30pk"],
    "Baby Food": ["Baby Puree Apple 120g", "Baby Puree Mixed Veg 120g"],
    "Baby Toiletries": ["Baby Wash 400mL", "Baby Shampoo 400mL", "Nappy Cream 100g"],
    "Surface Cleaners": ["Multi-Surface Spray 500mL", "Bathroom Cleaner 500mL", "Bleach 750mL"],
    "Laundry": ["Laundry Liquid 2L", "Laundry Powder 2kg", "Fabric Softener 1L"],
    "Dishwashing": ["Dishwashing Liquid 1L", "Dishwasher Tablets 60pk", "Dishwasher Powder 1kg"],
    "Toilet Paper": ["Toilet Paper 12pk", "Toilet Paper 24pk", "Jumbo Roll 6pk"],
    "Paper Towel": ["Paper Towel 6pk", "Kitchen Towel 3pk"],
    "Tissues": ["Facial Tissues 200pk", "Pocket Tissues 10pk"],
    "Foil & Wraps": ["Aluminium Foil 30m", "Cling Wrap 30m", "Baking Paper 10m"],
    "Storage Bags": ["Zip Lock Bags 30pk", "Sandwich Bags 50pk", "Freezer Bags 25pk"],
    "Bin Liners": ["Bin Liners 20pk", "Tall Bin Liners 15pk"],
}

_PACK_WORDS: dict[str, str] = {
    "each": "",
    "kg": "kg",
    "g": "g",
    "L": "L",
    "mL": "mL",
    "pack": "pk",
}

_SUPPLIER_CACHE: dict[tuple[Department, str], list[int]] = {}


def _get_suppliers(department: Department, category: str) -> list[int]:
    key = (department, category)
    if key not in _SUPPLIER_CACHE:
        det_rng = np.random.default_rng(hash(key) % 2**32)
        count = int(det_rng.integers(1, 4))
        pool = det_rng.choice(np.arange(1, 61), size=count, replace=False)
        _SUPPLIER_CACHE[key] = [int(x) for x in pool]
    return _SUPPLIER_CACHE[key]


def _format_supplier(supplier_num: int) -> str:
    return f"SUP{supplier_num:04d}"


def _pack_label(uom: str, pack_size: float) -> str:
    if uom == "each":
        return ""
    suffix = _PACK_WORDS.get(uom, uom)
    if pack_size == int(pack_size):
        return f"{int(pack_size)}{suffix}"
    return f"{pack_size}{suffix}"


def _generate_product_name(
    department: Department,
    category: str,
    subcategory: str,
    brand: str,
    uom: str,
    pack_size: float,
    rng: np.random.Generator,
) -> str:
    templates = _NAME_TEMPLATES.get(subcategory, [])
    base = str(rng.choice(np.array(templates))) if templates else subcategory
    label = _pack_label(uom, pack_size)
    parts = [p for p in [brand, base, label] if p]
    return " ".join(parts)


def _pick_uom_and_pack(
    department: Department, subcategory: str, rng: np.random.Generator
) -> tuple[Literal["each", "kg", "g", "L", "mL", "pack"], float]:
    if department in ("Beverages", "Alcohol", "Dairy"):
        if "Water" in subcategory or "Juice" in subcategory or "Milk" in subcategory:
            uom: Literal["each", "kg", "g", "L", "mL", "pack"] = "L"
            size = float(rng.choice(np.array([0.5, 1.0, 1.25, 2.0])))
            return uom, size
        if "Spirits" in subcategory or "Wine" in subcategory or "Whisky" in subcategory:
            uom = "mL"
            return uom, 700.0
    if department == "Meat & Seafood":
        uom = "kg"
        size = round(float(rng.choice(np.array([0.3, 0.4, 0.5, 1.0, 1.5]))), 1)
        return uom, size
    if department == "Health & Beauty" or department == "Household":
        uom = "mL"
        size = float(rng.choice(np.array([100.0, 150.0, 200.0, 400.0, 500.0, 750.0, 1000.0])))
        return uom, size
    if department == "Pantry":
        uom = "g"
        size = float(rng.choice(np.array([200.0, 250.0, 375.0, 500.0, 750.0, 1000.0])))
        return uom, size
    if department == "Frozen":
        uom = "g"
        size = float(rng.choice(np.array([300.0, 400.0, 500.0, 600.0, 800.0])))
        return uom, size
    if department == "Bakery":
        uom = "each"
        return uom, 1.0
    uom = "each"
    return uom, 1.0


def _allocate_skus(n: int) -> dict[Department, int]:
    total = sum(SKU_ALLOCATION.values())
    departments: list[Department] = list(SKU_ALLOCATION.keys())
    raw: list[float] = [SKU_ALLOCATION[d] * n / total for d in departments]
    floored = [int(x) for x in raw]
    remainder = n - sum(floored)
    fracs = [(raw[i] - floored[i], i) for i in range(len(departments))]
    fracs.sort(key=lambda x: -x[0])
    for i in range(remainder):
        floored[fracs[i][1]] += 1
    return {departments[i]: floored[i] for i in range(len(departments))}


class ProductRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    product_id: str
    sku: str
    name: str
    department: Department
    category: str
    subcategory: str
    brand: str
    is_private_label: bool
    unit_of_measure: Literal["each", "kg", "g", "L", "mL", "pack"]
    pack_size: float
    cost_price_aud: float
    retail_price_aud: float
    gst_applicable: bool
    shelf_life_days: int | None
    peak_season_months: list[int] | None
    seasonality_vector: list[float]
    wastage_rate_baseline: float | None
    supplier_id: str


def _make_fresh_row(
    idx: int,
    spec_name: str,
    category: str,
    subcategory: str,
    uom: Literal["each", "kg", "g", "L", "mL", "pack"],
    pack_size: float,
    cost: float,
    shelf_life: int,
    wastage: float,
    seasonality_vec: list[float],
    rng: np.random.Generator,
) -> ProductRow:
    margin = MARGIN_BY_DEPARTMENT["Fresh Produce"]
    jitter = float(rng.uniform(0.95, 1.05))
    raw_retail = cost * (1 + margin) * jitter
    retail = apply_charm_pricing(raw_retail, rng)
    if retail <= cost:
        # Ensure retail > cost by picking the smallest valid charm ending above cost
        valid = [e for e in (0.49, 0.79, 0.95, 0.99) if e > cost]
        retail = round(valid[0], 2) if valid else round(int(cost) + 1 + 0.49, 2)

    suppliers = _get_suppliers("Fresh Produce", category)
    supplier_idx = int(rng.integers(0, len(suppliers)))
    supplier = _format_supplier(suppliers[supplier_idx])

    peak = vector_to_peak_months(seasonality_vec)

    sku_digits = str(2_000_000 + idx).zfill(13)

    return ProductRow(
        product_id=f"P{idx:06d}",
        sku=sku_digits,
        name=spec_name,
        department="Fresh Produce",
        category=category,
        subcategory=subcategory,
        brand=PRIVATE_LABEL_NAME
        if rng.random() < PRIVATE_LABEL_RATE["Fresh Produce"]
        else "Sunrise Farms",
        is_private_label=False,
        unit_of_measure=uom,
        pack_size=pack_size,
        cost_price_aud=round(cost, 2),
        retail_price_aud=retail,
        gst_applicable=False,
        shelf_life_days=shelf_life,
        peak_season_months=peak,
        seasonality_vector=seasonality_vec,
        wastage_rate_baseline=wastage,
        supplier_id=supplier,
    )


def generate_products(n: int = 2000, seed: int = 42) -> list[ProductRow]:
    rng = np.random.default_rng(seed)
    allocation = _allocate_skus(n)

    rows: list[ProductRow] = []
    product_counter = 1

    departments_order: list[Department] = [
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

    for department in departments_order:
        dept_count = allocation[department]
        if dept_count == 0:
            continue

        if department == "Fresh Produce":
            ref_count = min(len(FRESH_GOODS_REFERENCE), dept_count)
            for _i, spec in enumerate(FRESH_GOODS_REFERENCE[:ref_count]):
                uom: Literal["each", "kg", "g", "L", "mL", "pack"] = spec.unit_of_measure
                row = _make_fresh_row(
                    idx=product_counter,
                    spec_name=spec.name,
                    category=spec.category,
                    subcategory=spec.subcategory,
                    uom=uom,
                    pack_size=spec.pack_size,
                    cost=spec.cost_price_aud,
                    shelf_life=spec.shelf_life_days,
                    wastage=spec.wastage_rate_baseline,
                    seasonality_vec=spec.seasonality_vector,
                    rng=rng,
                )
                rows.append(row)
                product_counter += 1

            extra = dept_count - ref_count
            ref_list = list(FRESH_GOODS_REFERENCE)
            for _ in range(extra):
                base_spec = ref_list[int(rng.integers(0, len(ref_list)))]
                pack_variants: list[float] = [0.5, 1.0, 1.5, 2.0]
                new_pack = float(rng.choice(np.array(pack_variants)))
                pack_label = (
                    f"{int(new_pack)}kg bag" if new_pack >= 1.0 else f"{int(new_pack * 1000)}g bag"
                )
                new_name = f"{base_spec.name} {pack_label}"
                cost_jitter = float(rng.uniform(0.90, 1.10))
                new_cost = round(base_spec.cost_price_aud * new_pack * cost_jitter, 2)
                new_cost = max(0.50, new_cost)
                row = _make_fresh_row(
                    idx=product_counter,
                    spec_name=new_name,
                    category=base_spec.category,
                    subcategory=base_spec.subcategory,
                    uom="kg",
                    pack_size=new_pack,
                    cost=new_cost,
                    shelf_life=base_spec.shelf_life_days,
                    wastage=base_spec.wastage_rate_baseline,
                    seasonality_vec=base_spec.seasonality_vector,
                    rng=rng,
                )
                rows.append(row)
                product_counter += 1

        else:
            cats = list(TAXONOMY[department].keys())
            cat_arr = np.array(cats)
            margin = MARGIN_BY_DEPARTMENT[department]
            pl_rate = PRIVATE_LABEL_RATE[department]
            cost_dist = COST_DISTRIBUTION_BY_DEPARTMENT[department]
            brands = BRAND_POOLS[department]
            brand_arr = np.array(brands)

            for _ in range(dept_count):
                category = str(rng.choice(cat_arr))
                subcats = TAXONOMY[department][category]
                subcat_arr = np.array(subcats)
                subcategory = str(rng.choice(subcat_arr))

                is_pl = bool(rng.random() < pl_rate)
                brand = PRIVATE_LABEL_NAME if is_pl else str(rng.choice(brand_arr))

                uom2, pack_size = _pick_uom_and_pack(department, subcategory, rng)
                uom = uom2

                cost = round(float(rng.triangular(cost_dist[0], cost_dist[1], cost_dist[2])), 2)
                jitter = float(rng.uniform(0.97, 1.03))
                raw_retail = cost * (1 + margin) * jitter
                retail = apply_charm_pricing(raw_retail, rng)
                if retail <= cost:
                    valid_endings = [e for e in (0.49, 0.79, 0.95, 0.99) if e > cost]
                    retail = round(valid_endings[0], 2) if valid_endings else round(int(cost) + 1 + 0.49, 2)

                gst = is_gst_applicable(department, category)
                name = _generate_product_name(
                    department, category, subcategory, brand, uom, pack_size, rng
                )

                is_perishable = (
                    department in _PERISHABLE_DEPARTMENTS and category in _PERISHABLE_CATEGORIES
                )
                shelf_life: int | None = (
                    _SHELF_LIFE_DEFAULTS.get(category) if is_perishable else None
                )
                wastage_rate: float | None = (
                    _WASTAGE_DEFAULTS.get(category) if is_perishable else None
                )

                svec = category_seasonality(department, category, subcategory, rng)
                peak_months_val = vector_to_peak_months(svec)
                peak_months: list[int] | None = peak_months_val if peak_months_val else None

                suppliers = _get_suppliers(department, category)
                supplier_idx = int(rng.integers(0, len(suppliers)))
                supplier = _format_supplier(suppliers[supplier_idx])

                sku_digits = str(3_000_000 + product_counter).zfill(13)

                rows.append(
                    ProductRow(
                        product_id=f"P{product_counter:06d}",
                        sku=sku_digits,
                        name=name,
                        department=department,
                        category=category,
                        subcategory=subcategory,
                        brand=brand,
                        is_private_label=is_pl,
                        unit_of_measure=uom,
                        pack_size=pack_size,
                        cost_price_aud=cost,
                        retail_price_aud=retail,
                        gst_applicable=gst,
                        shelf_life_days=shelf_life,
                        peak_season_months=peak_months,
                        seasonality_vector=svec,
                        wastage_rate_baseline=wastage_rate,
                        supplier_id=supplier,
                    )
                )
                product_counter += 1

    rows.sort(key=lambda r: r.product_id)
    return rows
