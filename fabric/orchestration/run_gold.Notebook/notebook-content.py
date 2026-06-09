# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {"name": "synapse_pyspark"},
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse_name": "lh_orchestration"
# META     },
# META     "environment": {"environmentName": "env_grocery_orchestration"}
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

all_metadata = spark.table("config.table_metadata").collect()
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
            timeoutSeconds=900,
            arguments={"run_id": run_id, "activity_id": activity_id},
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
