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

"""Generic Silver runner.

Reads Bronze, applies DQ gates, writes Silver. Branches on the scd2 flag
in metadata. Phase 3.5 only exercises the non-SCD2 path; Phase 4c will
implement the SCD2 merge logic.
"""

from pyspark.sql.functions import col, current_timestamp

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
tables_to_process = [row for row in all_metadata if row["group"] == group]

print(f"Silver runner: group={group}, run_id={run_id}, "
      f"tables={[t['name'] for t in tables_to_process]}")


def silver_transform_non_scd2(df, table):
    return (
        df
        .drop("_source_file", "_ingestion_batch_id", "_ingested_at_utc")
        .withColumn("_silver_loaded_at_utc", current_timestamp())
    )


def silver_transform_scd2(df, table):
    raise NotImplementedError("SCD2 merge — Phase 4c")


spark.sql("CREATE SCHEMA IF NOT EXISTS conformed")

for table in tables_to_process:
    activity_id = new_activity_id()
    started_at = log_run_start(run_id, activity_id, table["name"], "silver")

    try:
        bronze_table = f"lh_bronze.{table['domain']}.{table['name']}"
        silver_table = f"{table['domain']}.{table['name']}"  # writes to default lh_silver

        df = spark.table(bronze_table)
        df_silver = (
            silver_transform_scd2(df, table) if table["scd2"]
            else silver_transform_non_scd2(df, table)
        )

        total = df_silver.count()
        pk_cols = list(table["primary_key"])
        nulls = df_silver.filter(col(pk_cols[0]).isNull()).count()
        duplicates = total - df_silver.select(*pk_cols).distinct().count()
        assert nulls == 0, f"{table['name']}: {nulls} null primary key values"
        assert duplicates == 0, f"{table['name']}: {duplicates} duplicate keys"

        (
            df_silver.write
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .saveAsTable(silver_table)
        )

        log_run_success(run_id, activity_id, table["name"], "silver", started_at, total)
        print(f"  ✓ {table['name']}: {total} rows -> lh_silver.{silver_table}")

    except Exception as e:
        log_run_failure(run_id, activity_id, table["name"], "silver", started_at, e)
        print(f"  ✗ {table['name']}: {e}")
        raise

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
