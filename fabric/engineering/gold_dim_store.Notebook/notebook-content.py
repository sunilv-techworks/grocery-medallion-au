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

"""Gold dim_store — single source, same shape of business logic as
gold_dim_product: surrogate key plus derived columns that make this a
dimension rather than a straight-through copy of Silver.

Reads lh_silver.conformed.store, writes lh_gold.conformed.dim_store.

Returns: row count as the notebook exit value (used by run_gold dispatcher).
"""

from pyspark.sql.functions import col, current_date, datediff, monotonically_increasing_id, when

SOURCE_TABLE = "lh_silver.conformed.store"
TARGET_TABLE = "conformed.dim_store"  # default lakehouse = lh_gold

store = spark.table(SOURCE_TABLE)

df_gold = (
    store
    .drop("_silver_loaded_at_utc")
    .withColumn("store_sk", monotonically_increasing_id())
    .withColumn(
        "size_tier",
        when(col("store_size_sqm") < 600, "Small")
        .when(col("store_size_sqm") < 2000, "Medium")
        .otherwise("Large"),
    )
    .withColumn(
        "store_age_years",
        (datediff(current_date(), col("opened_date")) / 365).cast("decimal(5,1)"),
    )
)

(
    df_gold.write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(TARGET_TABLE)
)

row_count = df_gold.count()
print(f"Gold dim_store: {row_count} rows -> lh_gold.{TARGET_TABLE}")

mssparkutils.notebook.exit(str(row_count))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
