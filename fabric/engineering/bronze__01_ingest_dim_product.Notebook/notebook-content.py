# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "fc6df3ce-1604-4c8d-9926-f3957ecb6ad5",
# META       "default_lakehouse_name": "lh_bronze",
# META       "default_lakehouse_workspace_id": "5b41ba82-6075-49aa-90d8-94835e822115",
# META       "known_lakehouses": [
# META         {
# META           "id": "fc6df3ce-1604-4c8d-9926-f3957ecb6ad5"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

# Welcome to your new notebook
# Type here in the cell editor to add code!
"""Bronze ingest: land dim_product.parquet from lh_bronze/Files/landing/
into lh_bronze.conformed.dim_product.

Bronze rules:
- Preserve raw data as-is, only add lineage columns.
- Use mergeSchema=true so additive schema changes from upstream are captured
  automatically. Schema enforcement happens in Silver, not here.
- Bronze is the boundary with the outside world; landing files live in this
  same lakehouse to keep that boundary self-contained.

  # Round-trip test 2026-04-27

"""

from datetime import datetime, timezone

from pyspark.sql.functions import current_timestamp, lit

LANDING_PATH = "Files/landing/dim_product.parquet"
BRONZE_TABLE = "conformed.dim_product"

INGESTION_BATCH_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

df_raw = spark.read.parquet(LANDING_PATH)

df_bronze = (
    df_raw
    .withColumn("_ingested_at_utc", current_timestamp())
    .withColumn("_ingestion_batch_id", lit(INGESTION_BATCH_ID))
    .withColumn("_source_file", lit(LANDING_PATH))
)
spark.sql("CREATE SCHEMA IF NOT EXISTS conformed")
(
    df_bronze.write
    .mode("overwrite")
    .option("mergeSchema", "true")
    .saveAsTable(BRONZE_TABLE)
)

print(f"Wrote {df_bronze.count()} rows to {BRONZE_TABLE}")

print(f"Batch ID: {INGESTION_BATCH_ID}")

display(spark.table(BRONZE_TABLE).limit(5))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
