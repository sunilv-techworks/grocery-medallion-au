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

"""Gold fact_sales — resolves dimension natural keys to surrogate keys.

DR-011: unlike dim_product/dim_customer (which join other Silver tables),
a fact's Gold-layer job is star-schema surrogate-key resolution, so this
joins against Gold dimensions directly (dim_product, dim_store), not
Silver — those surrogate keys (product_sk, store_sk) only exist in Gold.
config.gold_metadata's depends_on ensures the dispatcher runs dim_product
and dim_store first (see run_gold.Notebook).

DR-013 (correction to DR-011): referential integrity here logs and drops
orphaned rows rather than hard-failing. DR-011 assumed a miss would always
mean a real bug, on the theory that every product_id/store_id was drawn
from the same lists used to generate this fact — but a live run proved
that wrong: dim_store's own Bronze-messiness injection (DR-005's pattern,
applied independently when site_master.parquet was generated) legitimately
dropped one store's natural key at Silver, while this fact was generated
from the full, clean store list and has no way to know that. The two
generation runs are independent, so a dimension-side DQ drop can orphan
otherwise-valid fact rows — a real, if narrow, cross-entity inconsistency,
not a bug. Unlike DR-010's dim_customer (where the row itself is still
useful without a resolved preferred store), a fact row with no resolvable
product_sk/store_sk can't be placed in the star schema at all, so it's
dropped rather than kept with nulls.

date_key is computed directly (yyyyMMdd), the same formula
gold_dim_calendar.Notebook uses to define it — an algorithmic join key,
not looked up, so no dependency on dim_calendar.

Reads lh_silver.conformed.sales + lh_gold.conformed.dim_product +
lh_gold.conformed.dim_store, writes lh_gold.conformed.fact_sales.

Returns: row count as the notebook exit value (used by run_gold dispatcher).
"""

from pyspark.sql.functions import col, date_format

SALES_TABLE = "lh_silver.conformed.sales"
TARGET_TABLE = "conformed.fact_sales"  # default lakehouse = lh_gold

sales = spark.table(SALES_TABLE)
dim_product = spark.table("conformed.dim_product").select(
    col("product_id").alias("_product_id"), col("product_sk")
)
dim_store = spark.table("conformed.dim_store").select(
    col("store_id").alias("_store_id"), col("store_sk")
)

joined = (
    sales.join(dim_product, sales.product_id == dim_product._product_id, how="left")
    .join(dim_store, sales.store_id == dim_store._store_id, how="left")
    .drop("_product_id", "_store_id")
)

missing = joined.filter(col("product_sk").isNull() | col("store_sk").isNull()).count()
if missing:
    print(
        f"  [dq] fact_sales: dropped {missing} row(s) with no matching "
        "dim_product/dim_store (see DR-013)"
    )

df_gold = (
    joined
    .filter(col("product_sk").isNotNull() & col("store_sk").isNotNull())
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
print(f"Gold fact_sales: {row_count} rows -> lh_gold.{TARGET_TABLE}")

mssparkutils.notebook.exit(str(row_count))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
