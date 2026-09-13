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

"""Gold dim_customer — two Silver sources, joined on preferred_store_id.

DR-010: unlike gold_dim_product's product+category join (every product is
guaranteed a matching category by construction, so a miss is a real bug and
fails the run), a customer's preferred_store_id can legitimately be NULL
(no preference — not a DQ issue) or a genuine orphan (a store code the
loyalty system has that Bronze/Silver never resolved — expected messiness on
a non-critical attribute, not a run-stopping bug). So this only *logs* a
referential-integrity count rather than failing, and keeps the raw
preferred_store_id value on orphaned rows for investigation instead of
nulling it out.

Reads lh_silver.conformed.customer + lh_silver.conformed.store,
writes lh_gold.conformed.dim_customer.

Returns: row count as the notebook exit value (used by run_gold dispatcher).
"""

from pyspark.sql.functions import col, current_date, datediff, monotonically_increasing_id

CUSTOMER_TABLE = "lh_silver.conformed.customer"
STORE_TABLE = "lh_silver.conformed.store"
TARGET_TABLE = "conformed.dim_customer"  # default lakehouse = lh_gold

customer = spark.table(CUSTOMER_TABLE)
store = spark.table(STORE_TABLE).select(
    col("store_id").alias("_store_id"),
    col("state").alias("preferred_store_state"),
    col("store_format").alias("preferred_store_format"),
)

joined = customer.join(store, customer.preferred_store_id == store._store_id, how="left").drop(
    "_store_id"
)

# Referential integrity: a non-null preferred_store_id with no matching
# store is a real orphan (see DR-010 above for why this logs, not fails).
orphaned = joined.filter(
    col("preferred_store_id").isNotNull() & col("preferred_store_state").isNull()
).count()
if orphaned:
    print(
        f"  [dq] dim_customer: {orphaned} row(s) have a preferred_store_id "
        "with no matching store (orphan FK, not null-by-choice) — kept, not dropped"
    )

df_gold = (
    joined
    .drop("_silver_loaded_at_utc")
    .withColumn("customer_sk", monotonically_increasing_id())
    .withColumn(
        "tenure_years",
        (datediff(current_date(), col("join_date")) / 365).cast("decimal(5,1)"),
    )
)

(
    df_gold.write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(TARGET_TABLE)
)

row_count = df_gold.count()
print(f"Gold dim_customer: {row_count} rows -> lh_gold.{TARGET_TABLE}")

mssparkutils.notebook.exit(str(row_count))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
