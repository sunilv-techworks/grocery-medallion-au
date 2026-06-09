# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse_name": "lh_orchestration",
# META       "default_lakehouse_workspace_id": ""
# META     },
# META     "environment": {}
# META   }
# META }

# CELL ********************

"""Seed lh_orchestration.config.table_metadata.

This notebook is the source of truth for table metadata. Edit TABLES below
to add or change tables; run this notebook (or include it in the pipeline)
to materialise the changes into the Fabric config table that runners read.
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

# === TABLE DEFINITIONS — source of truth ===

TABLES = [
    {
        "name": "dim_product",
        "layer": "dim",
        "group": "conformed_dims",
        "domain": "conformed",
        "bronze_landing_pattern": "Files/landing/dim_product.parquet",
        "upstream_silver": [],
        "scd2": False,
        "primary_key": ["product_id"],
        "grain_description": "One row per product SKU",
    },
    # Phase 4 will add dim_store, dim_customer, dim_calendar, fact_sales, fact_wastage here.
]

from pyspark.sql.types import ArrayType, BooleanType, StringType, StructField, StructType  # noqa: E402

schema = StructType([
    StructField("name", StringType(), nullable=False),
    StructField("layer", StringType(), nullable=False),
    StructField("group", StringType(), nullable=False),
    StructField("domain", StringType(), nullable=False),
    StructField("bronze_landing_pattern", StringType(), nullable=True),
    StructField("upstream_silver", ArrayType(StringType()), nullable=False),
    StructField("scd2", BooleanType(), nullable=False),
    StructField("primary_key", ArrayType(StringType()), nullable=False),
    StructField("grain_description", StringType(), nullable=False),
])

rows = [
    (t["name"], t["layer"], t["group"], t["domain"],
     t.get("bronze_landing_pattern"), list(t["upstream_silver"]),
     t["scd2"], list(t["primary_key"]), t["grain_description"])
    for t in TABLES
]

df = spark.createDataFrame(rows, schema=schema)
(
    df.write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable("config.table_metadata")
)

print(f"Seeded {len(rows)} table spec(s) into config.table_metadata")
df.show(truncate=False)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
