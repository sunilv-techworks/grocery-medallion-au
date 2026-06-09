# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {"name": "synapse_pyspark"},
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse_name": "lh_gold",
# META       "known_lakehouses": [
# META         {"name": "lh_silver"},
# META         {"name": "lh_gold"}
# META       ]
# META     },
# META     "environment": {"environmentName": "env_grocery_orchestration"}
# META   }
# META }

# CELL ********************

"""Gold dim_product — bespoke business logic.

Reads lh_silver.conformed.dim_product, derives analytics-friendly columns,
writes lh_gold.conformed.dim_product.

Returns: row count as the notebook exit value (used by run_gold dispatcher).
"""

from pyspark.sql.functions import col, size, when

SOURCE_TABLE = "lh_silver.conformed.dim_product"
TARGET_TABLE = "conformed.dim_product"  # default lakehouse = lh_gold

df = spark.table(SOURCE_TABLE)

df_gold = (
    df
    .drop("_silver_loaded_at_utc")
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
