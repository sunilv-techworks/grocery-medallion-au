# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "7e76a1e6-dacf-4e41-b5f0-6be7ecd0f0ca",
# META       "default_lakehouse_name": "lh_silver",
# META       "default_lakehouse_workspace_id": "5b41ba82-6075-49aa-90d8-94835e822115",
# META       "known_lakehouses": [
# META         {
# META           "id": "fc6df3ce-1604-4c8d-9926-f3957ecb6ad5"
# META         },
# META         {
# META           "id": "7e76a1e6-dacf-4e41-b5f0-6be7ecd0f0ca"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

"""Silver cleanse: read lh_bronze.conformed.dim_product, apply type casts and
DQ gates, write lh_silver.conformed.dim_product.
"""

from pyspark.sql.functions import col, current_timestamp

SOURCE_TABLE = "lh_bronze.conformed.dim_product"
TARGET_TABLE = "conformed.dim_product"

spark.sql("CREATE SCHEMA IF NOT EXISTS conformed")

df = spark.table(SOURCE_TABLE)

df_silver = (
    df
    .drop("_source_file", "_ingestion_batch_id", "_ingested_at_utc")
    .withColumn("_silver_loaded_at_utc", current_timestamp())
    .withColumn("cost_price_aud", col("cost_price_aud").cast("decimal(10,2)"))
    .withColumn("retail_price_aud", col("retail_price_aud").cast("decimal(10,2)"))
    .withColumn("pack_size", col("pack_size").cast("decimal(10,3)"))
)

total = df_silver.count()
nulls = df_silver.filter(col("product_id").isNull()).count()
duplicates = total - df_silver.select("product_id").distinct().count()

assert nulls == 0, f"Found {nulls} null product_ids in Silver"
assert duplicates == 0, f"Found {duplicates} duplicate product_ids in Silver"
assert total == 2000, f"Expected 2000 rows, got {total}"

(
    df_silver.write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(TARGET_TABLE)
)

print(f"Silver: {total} rows, 0 nulls, 0 duplicates")
display(spark.table(TARGET_TABLE).limit(5))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
