"""Department -> Category -> Subcategory taxonomy and SKU allocation targets."""

from typing import Literal

Department = Literal[
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

TAXONOMY: dict[Department, dict[str, list[str]]] = {
    "Fresh Produce": {
        "Fruit": ["Tropical Fruit", "Stone Fruit", "Berries", "Pome Fruit", "Citrus"],
        "Vegetables": [
            "Leafy Greens",
            "Root Vegetables",
            "Cruciferous",
            "Salad Vegetables",
            "Squash & Pumpkin",
        ],
        "Herbs & Specialty": ["Fresh Herbs", "Asian Vegetables", "Pre-cut Salads"],
    },
    "Bakery": {
        "Bread": ["Sliced Bread", "Rolls", "Specialty Loaves", "Wraps & Flatbreads"],
        "Sweet Baked": ["Cakes", "Pastries", "Doughnuts"],
        "Savoury Baked": ["Pies & Pasties", "Sausage Rolls", "Quiche"],
    },
    "Dairy": {
        "Milk": ["Full Cream", "Reduced Fat", "Plant-Based", "Flavoured"],
        "Cheese": ["Block Cheese", "Sliced Cheese", "Specialty Cheese"],
        "Yoghurt & Eggs": ["Yoghurt", "Eggs", "Cream"],
    },
    "Meat & Seafood": {
        "Beef & Lamb": ["Mince", "Steaks", "Roasts", "Lamb Cuts"],
        "Poultry": ["Chicken Breast", "Chicken Whole", "Turkey"],
        "Pork & Smallgoods": ["Pork Cuts", "Bacon", "Ham", "Sausages"],
        "Seafood": ["Fresh Fish", "Prawns", "Shellfish"],
    },
    "Pantry": {
        "Pasta & Rice": ["Dried Pasta", "Fresh Pasta", "Rice", "Noodles"],
        "Cooking Essentials": [
            "Oils & Vinegars",
            "Sauces & Condiments",
            "Spices & Seasonings",
            "Stock & Broth",
        ],
        "Baking": ["Flour & Sugar", "Baking Mixes", "Decorating"],
        "Breakfast": ["Cereals", "Spreads", "Muesli & Granola"],
        "Snacks": ["Chips & Crisps", "Biscuits", "Confectionery", "Nuts & Seeds"],
    },
    "Frozen": {
        "Frozen Meals": ["Ready Meals", "Pizza", "Frozen Asian"],
        "Frozen Veg & Fruit": ["Frozen Vegetables", "Frozen Berries"],
        "Ice Cream & Desserts": ["Ice Cream Tubs", "Ice Cream Sticks", "Frozen Desserts"],
    },
    "Beverages": {
        "Soft Drinks": ["Cola", "Lemonade", "Energy Drinks", "Mixers"],
        "Hot Drinks": ["Coffee", "Tea", "Hot Chocolate"],
        "Juice & Water": ["Fruit Juice", "Bottled Water", "Sparkling Water"],
    },
    "Alcohol": {
        "Beer": ["Premium Lager", "Mainstream Lager", "Craft", "Cider"],
        "Wine": ["Red Wine", "White Wine", "Sparkling", "Cask"],
        "Spirits": ["Whisky", "Vodka", "Gin", "Rum"],
    },
    "Health & Beauty": {
        "Personal Care": ["Hair Care", "Skin Care", "Oral Care", "Deodorant"],
        "Health": ["Vitamins", "Pain Relief", "First Aid"],
        "Baby": ["Nappies", "Baby Food", "Baby Toiletries"],
    },
    "Household": {
        "Cleaning": ["Surface Cleaners", "Laundry", "Dishwashing"],
        "Paper": ["Toilet Paper", "Paper Towel", "Tissues"],
        "Kitchen": ["Foil & Wraps", "Storage Bags", "Bin Liners"],
    },
}

SKU_ALLOCATION: dict[Department, int] = {
    "Pantry": 500,
    "Health & Beauty": 240,
    "Beverages": 240,
    "Fresh Produce": 200,
    "Frozen": 160,
    "Dairy": 160,
    "Household": 160,
    "Bakery": 120,
    "Meat & Seafood": 120,
    "Alcohol": 100,
}

assert sum(SKU_ALLOCATION.values()) == 2000
