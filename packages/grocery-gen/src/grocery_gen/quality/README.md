# Data Quality

Expectation suites are organised by medallion layer (bronze/silver/gold) and reused by both the local generator's test pipeline and the Fabric notebooks.

- `silver.py` — primary-key conformance (not-null, then uniqueness), generic across entities. Mirrored (not imported) by `fabric/engineering/util_dq.Notebook` — see [`docs/data-quality.md`](../../../../../docs/data-quality.md) and DR-005/DR-007 in the decision register for why.

See [`docs/decision-register.md`](../../../../../docs/decision-register.md) DR-005/DR-006/DR-007 for the full rationale.
