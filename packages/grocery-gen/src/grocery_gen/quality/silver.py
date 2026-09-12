"""Silver-layer data quality: primary-key conformance via Great Expectations.

DR-005/DR-007: Silver runs an actual GX checkpoint — not hand-rolled asserts
— enforcing not-null then uniqueness on each entity's primary key, and drops
violating rows rather than failing the run. The point is a Silver layer that
demonstrably cleans deliberately-messy Bronze data, not one that halts on
rows it could reasonably drop.

This suite is generic (driven by config.table_metadata's primary_key, not
per-entity), matching DR-007: entity-specific logic belongs at Gold, Silver
only proves conformance. fabric/engineering/util_dq.Notebook mirrors this
same expectation logic for the Fabric Silver notebook, since the engineering
workspace has no environment set up to import this package directly (see
DR-008) — only orchestration's seed_metadata notebook does.
"""

from typing import Any

import great_expectations as gx
import pandas as pd  # type: ignore[import-untyped]
from great_expectations.expectations import (  # type: ignore[attr-defined]
    ExpectColumnValuesToBeUnique,
    ExpectColumnValuesToNotBeNull,
    ExpectCompoundColumnsToBeUnique,
)


def build_primary_key_suite(primary_key: list[str]) -> Any:
    """Not-null on every primary-key column, then a uniqueness expectation
    over the combination of all of them (a single ExpectColumnValuesToBeUnique
    when there's just one column, ExpectCompoundColumnsToBeUnique otherwise).

    Requires an active GX context (call gx.get_context() first) — GX's
    ExpectationSuite.add_expectation needs one to check whether the suite
    has already been persisted.
    """
    suite = gx.ExpectationSuite(name="silver_primary_key_conformance")
    for column in primary_key:
        suite.add_expectation(ExpectColumnValuesToNotBeNull(column=column))
    if len(primary_key) == 1:
        suite.add_expectation(ExpectColumnValuesToBeUnique(column=primary_key[0]))
    else:
        suite.add_expectation(ExpectCompoundColumnsToBeUnique(column_list=primary_key))
    return suite


def _bad_indices(context: Any, df: pd.DataFrame, suite: Any) -> set[int]:
    data_source = context.data_sources.add_pandas(f"grocery_gen_pandas_{suite.name}")
    asset = data_source.add_dataframe_asset(name="asset")
    batch_definition = asset.add_batch_definition_whole_dataframe("batch")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})
    result = batch.validate(suite, result_format={"result_format": "COMPLETE"})
    bad: set[int] = set()
    for r in result.results:
        bad.update(r["result"].get("unexpected_index_list", []))
    return bad


def validate_primary_key(
    df: pd.DataFrame, primary_key: list[str]
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Runs the primary-key suite against df, returns (clean_df, violations).

    Two passes, mirroring the pre-GX hand-rolled checks this replaces:
    1. Drop rows with a null in any primary-key column.
    2. Among rows sharing a duplicate primary-key value, keep the first
       (by original row order) and drop the rest.

    violations = {"null": rows dropped for a null key, "duplicate": rows
    dropped for being an extra copy of a key already seen}.
    """
    context = gx.get_context(mode="ephemeral")

    null_suite = gx.ExpectationSuite(name="silver_pk_not_null")
    for column in primary_key:
        null_suite.add_expectation(ExpectColumnValuesToNotBeNull(column=column))
    null_bad_idx = _bad_indices(context, df, null_suite)
    clean_df = df.drop(index=list(null_bad_idx))

    unique_suite = gx.ExpectationSuite(name="silver_pk_unique")
    if len(primary_key) == 1:
        unique_suite.add_expectation(ExpectColumnValuesToBeUnique(column=primary_key[0]))
    else:
        unique_suite.add_expectation(ExpectCompoundColumnsToBeUnique(column_list=primary_key))
    dup_flagged_idx = _bad_indices(context, clean_df, unique_suite)

    keepers = set(clean_df.loc[list(dup_flagged_idx)].groupby(primary_key).head(1).index)
    dup_bad_idx = dup_flagged_idx - keepers
    clean_df = clean_df.drop(index=list(dup_bad_idx))

    return clean_df, {"null": len(null_bad_idx), "duplicate": len(dup_bad_idx)}
