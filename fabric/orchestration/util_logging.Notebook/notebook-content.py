# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "a2f1aba8-3d5e-4482-9dce-475ef81832fa",
# META       "default_lakehouse_name": "lh_orchestration",
# META       "default_lakehouse_workspace_id": "832c353e-3226-4e92-9ea7-66ffa2f4660e",
# META       "known_lakehouses": [
# META         {
# META           "id": "a2f1aba8-3d5e-4482-9dce-475ef81832fa"
# META         }
# META       ]
# META     },
# META     "environment": {}
# META   }
# META }

# CELL ********************

"""Shared logging helpers for runner notebooks. Included via %run util_logging.

pipeline_runs lives in lh_orchestration, but callers default to lh_bronze or
lh_silver (a different workspace) — three-part names only resolve within a
single workspace, so writes go via the ABFSS path (RUNS_LOG_PATH) instead.
"""

from datetime import datetime, timezone
from uuid import uuid4

# Cross-workspace: three-part names only resolve within a single workspace,
# so pipeline_runs (in lh_orchestration) is written via its ABFSS path —
# callers may default to lh_bronze/lh_silver/lh_orchestration.
RUNS_LOG_PATH = (
    "abfss://832c353e-3226-4e92-9ea7-66ffa2f4660e@onelake.dfs.fabric.microsoft.com/"
    "a2f1aba8-3d5e-4482-9dce-475ef81832fa/Tables/runs/pipeline_runs"
)
# Bumped when the pipeline_runs schema changes, so old rows can be told apart from new.
METADATA_VERSION = "v1"


def new_run_id() -> str:
    return str(uuid4())


def new_activity_id() -> str:
    return str(uuid4())


def log_run_start(run_id, activity_id, table_name, layer):
    started_at = datetime.now(timezone.utc)
    _insert_log_row(run_id, activity_id, table_name, layer, "running",
                    started_at=started_at)
    return started_at


def log_run_success(run_id, activity_id, table_name, layer, started_at, row_count):
    _insert_log_row(run_id, activity_id, table_name, layer, "success",
                    started_at=started_at, ended_at=datetime.now(timezone.utc),
                    row_count=row_count)


def log_run_failure(run_id, activity_id, table_name, layer, started_at, error):
    _insert_log_row(run_id, activity_id, table_name, layer, "failed",
                    started_at=started_at, ended_at=datetime.now(timezone.utc),
                    error_message=str(error)[:500])


def _insert_log_row(run_id, activity_id, table_name, layer, status,
                    started_at=None, ended_at=None, row_count=None, error_message=None):
    spark.createDataFrame(
        [(run_id, activity_id, table_name, layer, started_at, ended_at, status,
          row_count, error_message, METADATA_VERSION)],
        schema=("run_id string, activity_id string, table_name string, layer string, "
                "started_at_utc timestamp, ended_at_utc timestamp, status string, "
                "row_count bigint, error_message string, metadata_version string"),
    ).write.format("delta").mode("append").save(RUNS_LOG_PATH)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
