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

"""Gold fact_wastage — resolves dimension natural keys to surrogate keys.

Mirrors gold_fact_sales.Notebook exactly (see its docstring for the full
reasoning on why this joins Gold dimensions rather than Silver, why the
referential-integrity check is a hard failure here, and why date_key is
computed rather than looked up — DR-011).

Reads lh_silver.conformed.wastage + lh_gold.conformed.dim_product +
lh_gold.conformed.dim_store, writes lh_gold.conformed.fact_wastage.

Returns: row count as the notebook exit value (used by run_gold dispatcher).
"""

from pyspark.sql.functions import col, date_format

WASTAGE_TABLE = "lh_silver.conformed.wastage"
TARGET_TABLE = "conformed.fact_wastage"  # default lakehouse = lh_gold

wastage = spark.table(WASTAGE_TABLE)
dim_product = spark.table("conformed.dim_product").select(
    col("product_id").alias("_product_id"), col("product_sk")
)
dim_store = spark.table("conformed.dim_store").select(
    col("store_id").alias("_store_id"), col("store_sk")
)

joined = (
    wastage.join(dim_product, wastage.product_id == dim_product._product_id, how="left")
    .join(dim_store, wastage.store_id == dim_store._store_id, how="left")
    .drop("_product_id", "_store_id")
)

missing = joined.filter(col("product_sk").isNull() | col("store_sk").isNull()).count()
if missing:
    raise ValueError(
        f"{missing} fact_wastage row(s) have no matching dim_product/dim_store — "
        "referential integrity violation (see DR-011)"
    )

df_gold = (
    joined
    .drop("_silver_loaded_at_utc")
    .withColumn("date_key", date_format(col("date"), "yyyyMMdd").cast("int"))
)

(
    df_gold.write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(TARGET_TABLE)
)

row_count = df_gold.count()
print(f"Gold fact_wastage: {row_count} rows -> lh_gold.{TARGET_TABLE}")

mssparkutils.notebook.exit(str(row_count))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
