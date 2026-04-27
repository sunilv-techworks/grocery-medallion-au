# Data Quality

Data quality is enforced using Great Expectations (GX Core 1.x) with expectation suites defined under `packages/grocery-gen/src/grocery_gen/quality/` and shared between the local generator test pipeline and the Fabric Silver-layer notebooks; Microsoft Purview is used for data catalogue metadata and column-level lineage across the medallion layers. Full suite definitions, checkpoint configurations, and Purview integration details will be added in Phase 4 and Phase 6 respectively.
