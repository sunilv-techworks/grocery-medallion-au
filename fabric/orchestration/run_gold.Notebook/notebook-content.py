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
# META           "id": "108b9665-7225-4145-8fd6-acbc0115fa73"
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

"""Gold dispatcher.

For each table in the requested group, invokes the per-table Gold notebook
via mssparkutils.notebook.run(). Per-table notebooks must follow the naming
convention gold_<table_name>.
"""

# === Parameters (overridden by pipeline) ===
group = "conformed_dims"
run_id = new_run_id()

# Cross-workspace: three-part names only resolve within a single workspace,
# so table_metadata (in lh_orchestration) is read via its ABFSS path. Default
# lakehouse here is lh_gold — must match gold_dim_product's default, since
# mssparkutils.notebook.run() disallows calling a notebook with a different
# default lakehouse than the caller.
TABLE_METADATA_PATH = (
    "abfss://832c353e-3226-4e92-9ea7-66ffa2f4660e@onelake.dfs.fabric.microsoft.com/"
    "a2f1aba8-3d5e-4482-9dce-475ef81832fa/Tables/config/table_metadata"
)
all_metadata = spark.read.format("delta").load(TABLE_METADATA_PATH).collect()
tables_to_process = [row for row in all_metadata if row["group"] == group]

print(f"Gold dispatcher: group={group}, run_id={run_id}, "
      f"tables={[t['name'] for t in tables_to_process]}")

for table in tables_to_process:
    activity_id = new_activity_id()
    started_at = log_run_start(run_id, activity_id, table["name"], "gold")

    try:
        notebook_name = f"gold_{table['name']}"
        result = mssparkutils.notebook.run(
            notebook_name,
            900,
            {"run_id": run_id, "activity_id": activity_id},
        )

        try:
            row_count = int(result)
        except (TypeError, ValueError):
            row_count = None

        log_run_success(run_id, activity_id, table["name"], "gold",
                        started_at, row_count)
        print(f"  ✓ {table['name']}: dispatched → {notebook_name} (rows: {row_count})")

    except Exception as e:
        log_run_failure(run_id, activity_id, table["name"], "gold", started_at, e)
        print(f"  ✗ {table['name']}: {e}")
        raise

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
