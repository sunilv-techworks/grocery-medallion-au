# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "a2f1aba8-3d5e-4482-9dce-475ef81832fa",
# META       "default_lakehouse_name": "lh_orchestration",
# META       "default_lakehouse_workspace_id": "832c353e-3226-4e92-9ea7-66ffa2f4660e",
# META       "known_lakehouses": [
# META         {
# META           "id": "a2f1aba8-3d5e-4482-9dce-475ef81832fa"
# META         }
# META       ]
# META     },
# META     "environment": {}
# META   }
# META }

# CELL ********************

"""Seed lh_orchestration.config.table_metadata and config.gold_metadata.

This notebook is the source of truth for table metadata. Edit TABLES/
GOLD_TABLES below to add or change tables; run this notebook (or include it
in the pipeline) to materialise the changes into the Fabric config tables
that runners read.

Two tables, not one, because they're different grains: table_metadata is
one row per entity (Bronze/Silver stay 1:1 with entities), gold_metadata is
one row per Gold output (a many-to-many relationship with Silver sources —
one output can join multiple Silver tables, one Silver table can feed
multiple outputs — that doesn't fit as a column on an entity-grain table).
"""

# Smoke-test the grocery_gen wheel via env_grocery_orchestration.
# If this import fails, the environment didn't publish correctly.
from grocery_gen.dimensions.products import generate_products  # noqa: F401
print("grocery_gen wheel imported successfully via env_grocery_orchestration")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# === ENTITY DEFINITIONS (Bronze/Silver) — source of truth ===

TABLES = [
    {
        "name": "product",
        "layer": "dim",
        "group": "conformed_dims",
        "bronze_landing_pattern": "Files/landing/product_catalog.parquet",
        "column_mapping": {
            "sku_id": "product_id",
            "prod_desc": "name",
            "dept_name": "department",
            "cat_name": "category",
            "subcat_name": "subcategory",
            "brand_name": "brand",
            "uom": "unit_of_measure",
            "pack_qty": "pack_size",
            "cost_price": "cost_price_aud",
            "sell_price": "retail_price_aud",
            "gst_flag": "gst_applicable",
            "shelf_life_d": "shelf_life_days",
            "peak_months": "peak_season_months",
            "season_vec": "seasonality_vector",
            "wastage_pct": "wastage_rate_baseline",
            "supplier_code": "supplier_id",
        },
        "scd2": False,
        "primary_key": ["product_id"],
        "grain_description": "One row per product SKU, raw source-shaped in Bronze",
    },
    {
        "name": "category",
        "layer": "reference",
        "group": "conformed_dims",
        "bronze_landing_pattern": "Files/landing/category_master.parquet",
        "column_mapping": {},
        "scd2": False,
        "primary_key": ["department", "category"],
        "grain_description": "One row per (department, category); reference data, no standalone Gold output",
    },
    # Phase 4 will add dim_store, dim_customer, dim_calendar, fact_sales, fact_wastage here.
]

# === GOLD OUTPUT DEFINITIONS — source of truth ===

GOLD_TABLES = [
    {
        "name": "dim_product",
        "group": "conformed_dims",
        "sources": ["product", "category"],
        "gold_notebook": "gold_dim_product",
        "grain_description": "One row per product SKU, enriched with category attributes (gst_exempt)",
    },
]

from pyspark.sql.types import (  # noqa: E402
    ArrayType,
    BooleanType,
    MapType,
    StringType,
    StructField,
    StructType,
)

table_schema = StructType([
    StructField("name", StringType(), nullable=False),
    StructField("layer", StringType(), nullable=False),
    StructField("group", StringType(), nullable=False),
    StructField("bronze_landing_pattern", StringType(), nullable=True),
    StructField("column_mapping", MapType(StringType(), StringType()), nullable=False),
    StructField("scd2", BooleanType(), nullable=False),
    StructField("primary_key", ArrayType(StringType()), nullable=False),
    StructField("grain_description", StringType(), nullable=False),
])

table_rows = [
    (t["name"], t["layer"], t["group"], t.get("bronze_landing_pattern"),
     dict(t["column_mapping"]), t["scd2"], list(t["primary_key"]), t["grain_description"])
    for t in TABLES
]

gold_schema = StructType([
    StructField("name", StringType(), nullable=False),
    StructField("group", StringType(), nullable=False),
    StructField("sources", ArrayType(StringType()), nullable=False),
    StructField("gold_notebook", StringType(), nullable=False),
    StructField("grain_description", StringType(), nullable=False),
])

gold_rows = [
    (t["name"], t["group"], list(t["sources"]), t["gold_notebook"], t["grain_description"])
    for t in GOLD_TABLES
]

spark.sql("CREATE SCHEMA IF NOT EXISTS config")

df = spark.createDataFrame(table_rows, schema=table_schema)
(
    df.write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable("config.table_metadata")
)
print(f"Seeded {len(table_rows)} table spec(s) into config.table_metadata")
df.show(truncate=False)

gold_df = spark.createDataFrame(gold_rows, schema=gold_schema)
(
    gold_df.write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable("config.gold_metadata")
)
print(f"Seeded {len(gold_rows)} gold output spec(s) into config.gold_metadata")
gold_df.show(truncate=False)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
