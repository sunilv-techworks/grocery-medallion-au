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

"""Initialise lh_orchestration.runs.pipeline_runs (run once)."""

from pyspark.sql.types import (
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

schema = StructType([
    StructField("run_id", StringType(), nullable=False),
    StructField("activity_id", StringType(), nullable=False),
    StructField("table_name", StringType(), nullable=False),
    StructField("layer", StringType(), nullable=False),
    StructField("started_at_utc", TimestampType(), nullable=True),
    StructField("ended_at_utc", TimestampType(), nullable=True),
    StructField("status", StringType(), nullable=False),
    StructField("row_count", LongType(), nullable=True),
    StructField("error_message", StringType(), nullable=True),
    StructField("metadata_version", StringType(), nullable=False),
])

spark.sql("CREATE SCHEMA IF NOT EXISTS runs")

empty = spark.createDataFrame([], schema=schema)
(
    empty.write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable("runs.pipeline_runs")
)
print("Initialised runs.pipeline_runs")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
