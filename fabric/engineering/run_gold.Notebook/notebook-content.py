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

For each output in the requested group, invokes its Gold notebook via
mssparkutils.notebook.run(). Dispatched from config.gold_metadata — a
separate table from config.table_metadata because Gold is a different
grain: one Gold output can consume multiple Silver sources, and one Silver
source can feed multiple Gold outputs (many-to-many), which doesn't fit as
a column on the entity-grain table_metadata.

Outputs run in depends_on order, not table order: a Delta table's
.collect() row order isn't guaranteed to match insertion order, and facts
resolving dimension surrogate keys (fact_sales, fact_wastage — DR-011) need
their dimensions already written to Gold. A small repeated-pass topological
sort is enough here — a handful of outputs, not a real DAG scheduler.
"""

# === Parameters (overridden by pipeline) ===
group = "conformed_dims"
run_id = new_run_id()

# Cross-workspace: three-part names only resolve within a single workspace,
# so gold_metadata (in lh_orchestration) is read via its ABFSS path. Default
# lakehouse here is lh_gold — must match gold_dim_product's default, since
# mssparkutils.notebook.run() disallows calling a notebook with a different
# default lakehouse than the caller.
GOLD_METADATA_PATH = (
    "abfss://832c353e-3226-4e92-9ea7-66ffa2f4660e@onelake.dfs.fabric.microsoft.com/"
    "a2f1aba8-3d5e-4482-9dce-475ef81832fa/Tables/config/gold_metadata"
)
all_metadata = spark.read.format("delta").load(GOLD_METADATA_PATH).collect()
outputs_to_process = [row for row in all_metadata if row["group"] == group]

by_name = {t["name"]: t for t in outputs_to_process}
resolved_names: list[str] = []
remaining = list(outputs_to_process)
while remaining:
    ready = [
        t for t in remaining
        if all(d in resolved_names or d not in by_name for d in (t["depends_on"] or []))
    ]
    if not ready:
        raise ValueError(
            f"Unresolvable gold_metadata depends_on among: {[t['name'] for t in remaining]}"
        )
    for t in ready:
        resolved_names.append(t["name"])
        remaining.remove(t)
outputs_to_process = [by_name[name] for name in resolved_names]

print(f"Gold dispatcher: group={group}, run_id={run_id}, "
      f"outputs={[t['name'] for t in outputs_to_process]}")

for table in outputs_to_process:
    activity_id = new_activity_id()
    started_at = log_run_start(run_id, activity_id, table["name"], "gold")

    try:
        notebook_name = table["gold_notebook"]
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
