"""Brand pools and private-label rates per department."""

from grocery_gen.reference.taxonomy import Department

PRIVATE_LABEL_NAME: str = "Generic"

BRAND_POOLS: dict[Department, list[str]] = {
    "Fresh Produce": ["Sunrise Farms", "Valley Fresh", "Green Leaf Co", "NaturePick"],
    "Bakery": [
        "Millstone Bakery",
        "Golden Crust",
        "Hearth & Grain",
        "Breadsmith",
        "Morning Bake",
    ],
    "Dairy": ["Greenfield", "Morning Pail", "Riverbend", "Clover Plains", "Southern Pastures"],
    "Meat & Seafood": [
        "Stockman's Choice",
        "Coastal Catch",
        "Inland Plains Meat",
        "Harbour Fresh",
        "Outback Select",
    ],
    "Pantry": [
        "Pantry Pride",
        "Saxon Mills",
        "Harvest Lane",
        "Ridge Valley",
        "Goldwheat",
        "Blue Mountains Foods",
    ],
    "Frozen": [
        "Frostbite Meals",
        "Alpine Frozen",
        "Polar Peak",
        "Snowfield Foods",
        "Chill & Serve",
    ],
    "Beverages": [
        "Crystal Springs",
        "Sunpeak",
        "Black Ridge Coffee",
        "Verdant Tea",
        "Breezebrook",
        "Summit Refresh",
    ],
    "Alcohol": [
        "Rocky Cape",
        "Old Settler",
        "Three Hills",
        "Coastal Reserve",
        "Iron Bark Brewing",
        "Red Gum Distillery",
    ],
    "Health & Beauty": [
        "Wellness Works",
        "ClearSkin AU",
        "VitalPlus",
        "Nature's Best",
        "PureShield",
    ],
    "Household": [
        "SparkClean",
        "Homekeeper",
        "BrightHome",
        "FreshSpace",
        "EcoHouse",
    ],
}

PRIVATE_LABEL_RATE: dict[Department, float] = {
    "Pantry": 0.35,
    "Household": 0.40,
    "Frozen": 0.32,
    "Health & Beauty": 0.18,
    "Beverages": 0.20,
    "Bakery": 0.30,
    "Dairy": 0.30,
    "Meat & Seafood": 0.15,
    "Fresh Produce": 0.05,
    "Alcohol": 0.05,
}
