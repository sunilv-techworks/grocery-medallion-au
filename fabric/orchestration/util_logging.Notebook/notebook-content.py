# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse_name": "lh_orchestration"
# META     },
# META     "environment": {
# META       "environmentName": "env_grocery_orchestration"
# META     }
# META   }
# META }

# CELL ********************

"""Shared logging helpers for runner notebooks. Included via %run util_logging.

RUNS_LOG_TABLE uses the fully-qualified three-part name because callers will
have different default lakehouses (run_bronze: lh_bronze; run_silver: lh_silver;
run_gold: lh_orchestration). Using the three-part name means logging works
regardless of the caller's default lakehouse.
"""

from datetime import datetime, timezone
from uuid import uuid4

RUNS_LOG_TABLE = "lh_orchestration.runs.pipeline_runs"
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
    ).write.mode("append").saveAsTable(RUNS_LOG_TABLE)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
