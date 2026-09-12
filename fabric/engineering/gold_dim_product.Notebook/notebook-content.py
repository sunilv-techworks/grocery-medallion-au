# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "108b9665-7225-4145-8fd6-acbc0115fa73",
# META       "default_lakehouse_name": "lh_gold",
# META       "default_lakehouse_workspace_id": "5b41ba82-6075-49aa-90d8-94835e822115",
# META       "known_lakehouses": [
# META         {
# META           "id": "7e76a1e6-dacf-4e41-b5f0-6be7ecd0f0ca"
# META         },
# META         {
# META           "id": "108b9665-7225-4145-8fd6-acbc0115fa73"
# META         }
# META       ]
# META     },
# META     "environment": {}
# META   }
# META }

# CELL ********************

"""Gold dim_product — bespoke business logic.

Two Silver sources (DR-006/DR-007): joins product to category on
(department, category) to pull through gst_exempt, then does the
column selection, surrogate key, and derived columns that make this
actually a dimension rather than a straight-through copy of Silver.

Reads lh_silver.conformed.product + lh_silver.conformed.category,
writes lh_gold.conformed.dim_product.

Returns: row count as the notebook exit value (used by run_gold dispatcher).
"""

from pyspark.sql.functions import col, monotonically_increasing_id, size, when

PRODUCT_TABLE = "lh_silver.conformed.product"
CATEGORY_TABLE = "lh_silver.conformed.category"
TARGET_TABLE = "conformed.dim_product"  # default lakehouse = lh_gold

product = spark.table(PRODUCT_TABLE)
category = spark.table(CATEGORY_TABLE)

joined = product.join(category, on=["department", "category"], how="left")

# Referential integrity: product and category both derive from the same
# TAXONOMY source of truth in the generator, so every product's category
# should always match — an unmatched row here is a real bug, not expected
# messiness, so it fails the run rather than being silently dropped.
unmatched = joined.filter(col("gst_exempt").isNull()).count()
if unmatched:
    raise ValueError(
        f"{unmatched} product row(s) have no matching category — "
        "referential integrity violation between conformed.product and conformed.category"
    )

df_gold = (
    joined
    .drop("_silver_loaded_at_utc")
    .withColumn("product_sk", monotonically_increasing_id())
    .withColumn("is_perishable", col("shelf_life_days").isNotNull())
    .withColumn(
        "is_seasonal",
        col("peak_season_months").isNotNull() & (size(col("peak_season_months")) > 0),
    )
    .withColumn(
        "price_tier",
        when(col("retail_price_aud") < 5, "Budget")
        .when(col("retail_price_aud") < 20, "Mid")
        .otherwise("Premium"),
    )
    .withColumn(
        "margin_pct",
        ((col("retail_price_aud") - col("cost_price_aud")) / col("retail_price_aud") * 100)
        .cast("decimal(5,2)"),
    )
)

(
    df_gold.write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(TARGET_TABLE)
)

row_count = df_gold.count()
print(f"Gold dim_product: {row_count} rows -> lh_gold.{TARGET_TABLE}")

mssparkutils.notebook.exit(str(row_count))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
