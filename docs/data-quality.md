# Data Quality

Data quality is enforced using Great Expectations (GX Core 1.x) with expectation suites defined under `packages/grocery-gen/src/grocery_gen/quality/` and shared between the local generator test pipeline and the Fabric Silver-layer notebooks; Microsoft Purview is used for data catalogue metadata and column-level lineage across the medallion layers. Purview integration will be added in Phase 6.

## Silver: primary-key conformance (DR-005/DR-007)

`grocery_gen.quality.silver.validate_primary_key` runs a real GX `ExpectationSuite` — not-null on every primary-key column, then a uniqueness expectation over them — against a pandas DataFrame, and drops violating rows (null keys, then all but the first row of any duplicate key) rather than failing the run. It's generic, driven by a table's `primary_key` from `config.table_metadata`, not hand-written per entity — Silver proves conformance; entity-specific logic (joins, derived columns, referential-integrity checks) belongs at Gold per DR-007.

`fabric/engineering/util_dq.Notebook` mirrors this same two-expectation checkpoint for the Fabric Silver notebook (`run_silver.Notebook`, via `%run util_dq`). It's a duplicate rather than an import of the package above: the `ws-grocery-engineering-dev` workspace has no environment set up to install this repo's wheel (DR-008 — only orchestration's `seed_metadata` notebook does), so `great-expectations` is installed inline via `%pip install`, and the Spark DataFrame is collected to pandas for validation (`.toPandas()` / `spark.createDataFrame(...)`). At this project's row counts (thousands, not billions) that driver-side collect is a reasonable trade-off for a real checkpoint instead of hand-rolled asserts; a genuinely large table would need Spark-native GX (`context.data_sources.add_spark(...)`) instead.

Tested locally with pytest, including directly against the generator's deliberately-messy Bronze output (`to_raw_product_rows`) — see `packages/grocery-gen/tests/test_quality_silver.py`. Not yet verified via a live Fabric pipeline run.

## Gold: referential integrity (DR-006/DR-010)

`gold_dim_product.Notebook` fails the run if any `conformed.product` row has no matching `conformed.category` row on `(department, category)` — a real assertion, not a GX expectation, since it's a one-off join-integrity check specific to this Gold output rather than a reusable per-entity rule. This is correct here because the relationship is guaranteed by construction (both derive from the same `TAXONOMY`), so a mismatch is a genuine bug.

`gold_dim_customer.Notebook` takes the opposite stance for `preferred_store_id` → `dim_store` (DR-010): `NULL` is a legitimate "no preference" value, and a non-null orphan is realistic, expected messiness on a non-critical attribute rather than a bug — so it logs a count and keeps the row (raw invalid ID intact) instead of failing or nulling it out. Same relationship shape as DR-006, deliberately different response, because the two FKs don't carry the same guarantee.
