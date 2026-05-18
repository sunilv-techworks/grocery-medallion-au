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
# META     }
# META   }
# META }

# CELL ********************

"""Gold: read lh_silver.conformed.dim_product, derive analytics-friendly
columns, write lh_gold.conformed.dim_product.
"""

from pyspark.sql.functions import col, size, when

SOURCE_TABLE = "lh_silver.conformed.dim_product"
TARGET_TABLE = "conformed.dim_product"

spark.sql("CREATE SCHEMA IF NOT EXISTS conformed")

df = spark.table(SOURCE_TABLE)

df_gold = (
    df
    .drop("_silver_loaded_at_utc")
    .withColumn("is_perishable", col("shelf_life_days").isNotNull())
    .withColumn(
        "is_seasonal",
        col("peak_season_months").isNotNull() & (size(col("peak_season_months")) > 0)
    )
    .withColumn(
        "price_tier",
        when(col("retail_price_aud") < 5, "Budget")
        .when(col("retail_price_aud") < 20, "Mid")
        .otherwise("Premium")
    )
    .withColumn(
        "margin_pct",
        ((col("retail_price_aud") - col("cost_price_aud")) / col("retail_price_aud") * 100)
        .cast("decimal(5,2)")
    )
)

(
    df_gold.write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(TARGET_TABLE)
)

print(f"Gold: {df_gold.count()} rows")
print(f"Perishable: {df_gold.filter(col('is_perishable')).count()}")
print(f"Seasonal: {df_gold.filter(col('is_seasonal')).count()}")

display(spark.table(TARGET_TABLE).limit(10))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
