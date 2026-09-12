# Decision Register

This project is built collaboratively with an AI assistant. That doesn't remove
the need for human judgement on tradeoffs — it changes where that judgement
shows up. This register is where it's recorded: the issue or question, what
was considered, what was chosen, and why. Not every decision below is
implemented yet — some are deliberately parked as backlog, with the reason for
deferring stated alongside the decision.

**How to read this:** each entry is dated, has a status (`Decided` or
`Backlog`), and follows the same shape — Issue → Options considered →
Decision → Rationale.

---

## DR-001 — Author the orchestration pipeline as git-native `DataPipeline` JSON instead of the Fabric UI

**Status:** Decided · **Date:** 2026-08-15

**Issue:** Phase 3.5's spec called for authoring `pl_grocery_medallion` by hand
in the Fabric UI, then syncing it down to Git.

**Options considered:**
1. Manual UI authoring, as specced.
2. Hand-author the git-format `DataPipeline` item directly — using the Phase 3
   `pl_dim_product.DataPipeline` as a template, resolving the real notebook
   GUIDs via the Fabric REST API — and publish it with `deploy.py`.

**Decision:** Option 2.

**Rationale:** Functionally identical result, without a manual click-through
step. The item originates in Git from the start, so there's no separate
"sync to Git" step needed afterward.

---

## DR-002 — Cross-workspace table references use ABFSS paths, not three-part names

**Status:** Decided · **Date:** 2026-08-15

**Issue:** `run_bronze` and `run_silver` failed with
`TABLE_OR_VIEW_NOT_FOUND` reading `lh_orchestration.config.table_metadata`.
Three-part table names (`lakehouse.schema.table`) only resolve within a
single Fabric workspace — confirmed against Microsoft's own docs and
community reports, not assumed.

**Options considered:**
1. Attach `lh_orchestration` as a "known lakehouse" in the caller notebook's
   metadata and keep the three-part reference.
2. Switch cross-workspace reads/writes to explicit ABFSS paths.

**Decision:** Option 2.

**Rationale:** Option 1 was tried first and does not actually resolve
cross-workspace attachment this way in practice. ABFSS paths are the
Microsoft-documented pattern for this exact case and don't depend on
notebook-metadata attachment succeeding.

---

## DR-003 — `run_gold`'s default lakehouse realigned to match its child notebook, not forced via `useRootDefaultLakehouse`

**Status:** Decided · **Date:** 2026-08-15

**Issue:** `mssparkutils.notebook.run()` refused to call `gold_dim_product`
because its default lakehouse (`lh_gold`) differed from the caller's
(`lh_orchestration`). Fabric's documented escape hatch is
`useRootDefaultLakehouse=True`.

**Options considered:**
1. Pass `useRootDefaultLakehouse=True` to force the child notebook to inherit
   the caller's default lakehouse.
2. Change `run_gold`'s own default lakehouse to `lh_gold`, matching the
   child.

**Decision:** Option 2.

**Rationale:** `gold_dim_product` writes to `conformed.dim_product` relying
on its own default lakehouse being `lh_gold`. Option 1 would have silently
redirected that write into `lh_orchestration` instead — a data-placement bug
with no obvious error at run time.

---

## DR-004 — Retire Phase 3 engineering-workspace artifacts only after verifying nothing depends on them

**Status:** Decided · **Date:** 2026-08-19

**Issue:** Phase 3.5 §3.3 called for deleting the old Phase 3 pipeline and
its 3 notebooks from `ws-grocery-engineering-dev`, now superseded by the
orchestration platform.

**Options considered:**
1. Delete immediately — the new pipeline was already verified working
   end-to-end.
2. First verify no other repo item or live Fabric schedule referenced them,
   then delete.

**Decision:** Option 2. (Raised as a direct question mid-session — "why are
we deleting, what's going to call this?" — before proceeding.)

**Rationale:** Deleting live workspace items is a real action against shared
cloud infrastructure, not a local file change. Worth a grep across the repo
and a schedule check before doing it, even though the outcome confirmed it
was safe both times.

---

## Backlog — considered, deliberately deferred

## DR-005 — Reshape Bronze/Silver/Gold so each layer actually means something

**Status:** Decided · **Date raised:** 2026-08-22 · **Implemented:** 2026-09-12

**Issue:** The generator emits `dim_product.parquet` already
dimension-shaped, and it lands in Bronze unchanged. Today, Bronze, Silver,
and Gold differ only by a few lineage columns and a handful of derived
columns — not by genuine raw → conformed → dimensional transformation.

**Options considered:**
1. Leave as-is — it works, and reshaping is real rework.
2. Generator emits source-shaped raw data into Bronze (source column names,
   a couple of realistic quality issues); Silver does real conformance plus
   an actual Great Expectations checkpoint; Gold does the real
   dimension-building (surrogate keys, derived business columns).

**Decision:** Option 2 — implemented.

**Rationale:** Genuine scope increase — needs generator changes and a real
GX suite, not a config tweak. Parked alongside DR-006 through DR-008 as the
Phase 4 body of work.

**Implementation note:** `grocery_gen.dimensions.products.to_raw_product_rows`
renames `ProductRow` to source-shaped columns (`sku_id`, `prod_desc`, ...)
and deterministically injects a null-key row and a duplicate row per
`messy_rate` (default 1%) — real, reproducible quality issues for Silver to
catch rather than a cosmetic rename. Silver's primary-key conformance
(not-null then uniqueness) now runs as an actual GX `ExpectationSuite`
checkpoint — `packages/grocery-gen/src/grocery_gen/quality/silver.py` — in
place of the hand-rolled PySpark asserts it replaces. `fabric/engineering/
util_dq.Notebook` mirrors the same two-expectation checkpoint for the Fabric
Silver notebook (Spark → pandas → GX → back to Spark, since the engineering
workspace has no environment to install this repo's wheel — DR-008 — and at
this project's row counts a driver-side collect is a reasonable trade-off
for a real checkpoint over hand-rolled asserts). Verified locally: 40
pytest tests pass, including `validate_primary_key` run directly against
`to_raw_product_rows`' deliberately-messy output. **Not yet verified via a
live Fabric pipeline run** — the notebook's GX/pandas path can only be
exercised inside an actual Fabric Spark session, unlike the DR-008 move,
which was confirmed end-to-end.

---

## DR-006 — Gold `dim_product` sourced from two tables (product + category), not one

**Status:** Decided · **Date raised:** 2026-08-22 · **Implemented:** 2026-09-12

**Issue:** Wanted a second source feeding Gold, to demonstrate multi-source
dimension building rather than a single straight-through table.

**Options considered:**
1. Product + category/department reference data, carrying a `gst_exempt`
   flag.
2. Product + image/URL data.

**Decision:** Option 1 — implemented.

**Rationale:** Category/department master data realistically comes from a
separate source system in retail, so it's a legitimate reason for two Bronze
sources rather than a contrived one. It also lets Gold implement the
GST-exemption logic the README already claims as a differentiator but never
actually built, and gives the join a real referential-integrity story.
Option 2 was rejected — no business logic, no DQ story, and images are
normally referenced by ID from blob storage rather than joined from a source
table in a real warehouse.

**Implementation note:** New `grocery_gen.dimensions.categories.generate_categories`
derives one row per `(department, category)` from the same `TAXONOMY` source
of truth the product generator already uses, carrying `gst_exempt`; exposed
via `grocery-gen categories` and landed as `category_master.parquet`.
`gold_dim_product.Notebook` joins `conformed.product` to `conformed.category`
on `(department, category)`, adds `product_sk`, and fails the run if any
product has no matching category (see DR-007 for why that check lives here
rather than in Silver). Verified locally via the generator's tests; not yet
verified via a live Fabric pipeline run (see DR-005's implementation note).

---

## DR-007 — Silver stays entity-complete; join, column selection, and referential-integrity checks all happen at the Gold join

**Status:** Decided · **Date raised:** 2026-08-22 · **Implemented:** 2026-09-12

**Issue:** With two Silver sources (`conformed.product`, `conformed.category`)
feeding one Gold table, where should columns be narrowed, the join happen,
and mismatches (e.g. a product's department code not found in category) be
caught?

**Options considered:**
1. Narrow columns and join at Silver, producing an already-merged,
   Gold-shaped table.
2. Keep Silver clean but entity-complete and independent per source; do the
   join, column projection, derived columns, and the referential-integrity
   check at Gold.

**Decision:** Option 2 — implemented.

**Rationale:** Keeps Silver reusable as a conformed source of truth for any
future consumer, rather than pre-shaped for this one Gold output. Gold is
the consumer-specific layer, so projection and business rules belong there.

**Implementation note:** `run_silver.Notebook` now applies each entity's own
`column_mapping` from `config.table_metadata` (raw → conformed names,
identity if absent) and runs the DR-005 GX primary-key checkpoint — nothing
entity-specific, no join. `gold_dim_product.Notebook` owns the
`product`+`category` join, column projection, and the referential-integrity
check (see DR-006). Verified locally; not yet verified via a live Fabric
pipeline run (see DR-005's implementation note).

---

## DR-008 — Move transform notebooks from `ws-grocery-orchestration-dev` to `ws-grocery-engineering-dev`

**Status:** Decided · **Date raised:** 2026-08-22 · **Implemented:** 2026-08-22

**Issue:** All 5 transform notebooks (`run_bronze`, `run_silver`, `run_gold`,
`gold_dim_product`, `util_logging`) live in the orchestration workspace
alongside the control-plane lakehouse (`config`/`runs`) and the pipeline
itself. `ws-grocery-engineering-dev` — named for exactly this purpose — has
sat empty since DR-004 retired the old Phase 3 items from it.

**Options considered:**
1. Leave as-is — it works, already verified end-to-end (`v0.3.5-orchestration-platform`).
2. Move the 5 transform notebooks to `engineering`, leaving only the
   pipeline and the control-plane lakehouse in `orchestration`.

**Decision:** Option 2 — implemented.

**Rationale:** "Orchestration" should mean coordination plus metadata;
"engineering" should hold the actual transform logic. The current layout
grew organically during Phase 3.5 rather than by deliberate design.

**Correction to the original wrinkle:** before implementing, checked whether
any of the 5 moving notebooks actually import `grocery_gen` (`env_grocery_orchestration`'s
only reason to exist beyond Spark compute sizing) — none do; only
`seed_metadata` does, and it stays in `orchestration`. So no environment
needed to be provisioned in `engineering` at all — the notebooks run on its
default runtime. The move ended up being: relocate the 5 notebook folders,
deploy to `engineering` (new item GUIDs), re-point the pipeline's
`BronzeDims`/`SilverDims`/`GoldDims` `TridentNotebook` activities to the new
notebook IDs with an explicit cross-workspace `workspaceId` (Fabric supports
this natively — no notebook code changes needed, since `%run` and
`mssparkutils.notebook.run()` still resolve by name within the caller's own
workspace, and all 5 moved together), then retire the orchestration copies
via `deploy.py --unpublish-orphans` after confirming no other repo item
referenced their old GUIDs. Verified end-to-end both before and after
retiring the old copies: pipeline green, 2000 rows at every layer.

**Sequencing (resolved):** did the workspace move first, deferring the
Bronze/Silver/Gold reshape (DR-005/006/007) to happen in the notebooks'
final home in `engineering`.
