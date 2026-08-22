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
# META         },
# META         {
# META           "id": "a2f1aba8-3d5e-4482-9dce-475ef81832fa",
# META           "workspaceId": "832c353e-3226-4e92-9ea7-66ffa2f4660e"
# META         }
# META       ]
# META     },
# META     "environment": {}
# META   }
# META }

# CELL ********************

%run util_logging

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

"""Generic Bronze runner.

Parameters (passed by pipeline):
    group: str  — which group of tables to process
    run_id: str — pipeline-level run ID (carried across activities)

For each table in the group with a non-null bronze_landing_pattern,
reads the landing file (resolved against default lh_bronze lakehouse)
and writes the Bronze table with lineage columns.
"""

from pyspark.sql.functions import current_timestamp, lit

# === Parameters (overridden by pipeline) ===
group = "conformed_dims"
run_id = new_run_id()

# Cross-workspace: three-part names only resolve within a single workspace,
# so table_metadata (in lh_orchestration) is read via its ABFSS path.
TABLE_METADATA_PATH = (
    "abfss://832c353e-3226-4e92-9ea7-66ffa2f4660e@onelake.dfs.fabric.microsoft.com/"
    "a2f1aba8-3d5e-4482-9dce-475ef81832fa/Tables/config/table_metadata"
)
all_metadata = spark.read.format("delta").load(TABLE_METADATA_PATH).collect()
tables_to_process = [
    row for row in all_metadata
    if row["group"] == group and row["bronze_landing_pattern"] is not None
]

print(f"Bronze runner: group={group}, run_id={run_id}, "
      f"tables={[t['name'] for t in tables_to_process]}")

spark.sql("CREATE SCHEMA IF NOT EXISTS conformed")

for table in tables_to_process:
    activity_id = new_activity_id()
    started_at = log_run_start(run_id, activity_id, table["name"], "bronze")

    try:
        landing_path = table["bronze_landing_pattern"]
        bronze_table = f"{table['domain']}.{table['name']}"  # writes to default lh_bronze

        # Files/ resolves against the default lakehouse (lh_bronze)
        df_raw = spark.read.parquet(landing_path)

        df_bronze = (
            df_raw
            .withColumn("_ingested_at_utc", current_timestamp())
            .withColumn("_ingestion_batch_id", lit(run_id))
            .withColumn("_source_file", lit(landing_path))
        )

        (
            df_bronze.write
            .mode("overwrite")
            .option("mergeSchema", "true")
            .saveAsTable(bronze_table)
        )

        row_count = df_bronze.count()
        log_run_success(run_id, activity_id, table["name"], "bronze",
                        started_at, row_count)
        print(f"  ✓ {table['name']}: {row_count} rows -> lh_bronze.{bronze_table}")

    except Exception as e:
        log_run_failure(run_id, activity_id, table["name"], "bronze", started_at, e)
        print(f"  ✗ {table['name']}: {e}")
        raise

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
