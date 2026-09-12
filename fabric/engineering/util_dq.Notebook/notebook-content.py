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
# META         }
# META       ]
# META     },
# META     "environment": {}
# META   }
# META }

# CELL ********************

# The engineering workspace has no custom environment (DR-008: none of its
# notebooks needed grocery_gen, so none was provisioned), so great-expectations
# is installed inline rather than via a pre-built environment/wheel.
%pip install great-expectations

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

"""Shared DQ checks for runner notebooks. Included via %run util_dq.

DR-005: an actual Great Expectations checkpoint, not hand-rolled asserts.
Rules are declarative — derived from a table's primary_key in
config.table_metadata rather than hand-written per-notebook asserts. Checks
filter out violating rows (not fail-fast): the point is to demonstrate a
Silver layer that actually cleans deliberately-messy Bronze data, not one
that halts the whole pipeline on rows it could reasonably drop.

Mirrors packages/grocery-gen/src/grocery_gen/quality/silver.py, duplicated
rather than imported because the engineering workspace can't install this
repo's own wheel (see DR-008 — only orchestration's seed_metadata notebook
does). Validates via pandas after a driver-side collect rather than
natively in Spark: at this project's data volumes (thousands of rows) that's
a reasonable trade-off for a real GX checkpoint over hand-rolled asserts; a
genuinely large table would need Spark-native GX
(context.data_sources.add_spark(...)) instead.
"""

import great_expectations as gx


def _bad_indices(context, pdf, suite):
    data_source = context.data_sources.add_pandas(f"util_dq_{suite.name}_{id(pdf)}")
    asset = data_source.add_dataframe_asset(name="asset")
    batch_definition = asset.add_batch_definition_whole_dataframe("batch")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": pdf})
    result = batch.validate(suite, result_format={"result_format": "COMPLETE"})
    bad = set()
    for r in result.results:
        bad.update(r["result"].get("unexpected_index_list", []))
    return bad


def run_primary_key_checks(df, primary_key: list[str], table_name: str):
    """Applies not-null then uniqueness checks on primary_key via a GX
    checkpoint, printing what was caught. Returns the cleaned DataFrame.
    """
    pdf = df.toPandas()
    context = gx.get_context(mode="ephemeral")

    null_suite = gx.ExpectationSuite(name=f"{table_name}_pk_not_null")
    for pk_col in primary_key:
        null_suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column=pk_col))
    null_bad = _bad_indices(context, pdf, null_suite)
    if null_bad:
        print(f"  [dq] {table_name}: dropped {len(null_bad)} row(s) with null primary key {primary_key}")
    pdf = pdf.drop(index=list(null_bad))

    unique_suite = gx.ExpectationSuite(name=f"{table_name}_pk_unique")
    if len(primary_key) == 1:
        unique_suite.add_expectation(gx.expectations.ExpectColumnValuesToBeUnique(column=primary_key[0]))
    else:
        unique_suite.add_expectation(
            gx.expectations.ExpectCompoundColumnsToBeUnique(column_list=primary_key)
        )
    dup_flagged = _bad_indices(context, pdf, unique_suite)
    keepers = set(pdf.loc[list(dup_flagged)].groupby(primary_key).head(1).index)
    dup_bad = dup_flagged - keepers
    if dup_bad:
        print(f"  [dq] {table_name}: dropped {len(dup_bad)} duplicate row(s) on primary key {primary_key}")
    pdf = pdf.drop(index=list(dup_bad))

    return spark.createDataFrame(pdf, schema=df.schema)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
