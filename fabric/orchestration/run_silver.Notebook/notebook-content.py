# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse_name": "lh_silver",
# META       "default_lakehouse_workspace_id": "",
# META       "known_lakehouses": [
# META         {
# META           "name": "lh_bronze"
# META         },
# META         {
# META           "name": "lh_silver"
# META         },
# META         {
# META           "name": "lh_orchestration"
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

all_metadata = spark.table("lh_orchestration.config.table_metadata").collect()
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
