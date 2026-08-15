# Phase 3.5 Progress Tracker

Last updated: 2026-08-15

## Status: IN PROGRESS — Step 3.2 (run pl_grocery_medallion end-to-end)

Spec: `PHASE_3_5_SPEC_V2.md`
Branch: `feature/phase-3.5-platform`

---

## Prerequisites

- [x] Phase 3 complete and tagged `v0.3.0-phase3-spike`
- [x] Feature branch `feature/phase-3.5-platform` created
- [x] `.env` confirmed gitignored (was already excluded from Phase 1)
- [ ] Trial capacity expiry checked (60-day clock from Phase 3 start)

---

## Section 1 — Foundations

- [x] **1.1** Entra app registration — `grocery-medallion-au-deployer-dev` created, tenant ID + client ID + secret captured ✅
- [x] **1.2** Fabric tenant setting — both SPN settings enabled for entire organisation ✅
- [x] **1.3** SPN added as Admin to all 5 existing workspaces (storage, engineering, semantic, bi, ai) ✅
- [x] **1.4** `tools/verify-spn.py` created, `.env` loaded, SPN verified — 5 workspaces visible ✅
  - storage:     `5b41ba82-6075-49aa-90d8-94835e822115`
  - engineering: `6d4ec153-ea4d-4bd1-92ff-13f6c6ea83d7`
  - semantic:    `a8ad9315-1e3f-4cda-b0dc-2c684e837141`
  - bi:          `7c8e3700-1735-49fa-aed6-b73126456b92`
  - ai:          `b982af59-a2bf-48d1-af27-cf53da699b64`
  - orchestration: `832c353e-3226-4e92-9ea7-66ffa2f4660e`
- [x] **1.5** `grocery_gen` wheel built — `dist/grocery_gen-0.1.0-py3-none-any.whl` (repo root dist/, not package subfolder) ✅
- [x] **1.6** `ws-grocery-orchestration-dev` created (GUID: `832c353e-3226-4e92-9ea7-66ffa2f4660e`), SPN added as Admin, Git-connected to `fabric/orchestration`; `lh_orchestration` created with schemas `config` and `runs` ✅
- [x] **1.7** `env_grocery_orchestration` Fabric Environment created, wheel uploaded, Published; set as default Spark env; synced to Git ✅
- [x] **1.8** `deploy.py`, `parameter.yml`, `config/fabric-ids.example.yaml` committed; `config/fabric-ids.yaml` (real GUIDs) created locally and gitignored; `fabric-cicd==0.1.30` added as dev dep ✅
- [x] **1.9** `deploy.py` verified — environment published and deployed successfully ✅ (parameter.yml warning is harmless — fix deferred to Phase 7 when find_replace entries are needed)

---

## Section 2 — Platform notebooks

- [x] **2.1** `init_runs_log.Notebook` authored in VS Code ✅
- [x] **2.2** `util_logging.Notebook` authored — `RUNS_LOG_TABLE` uses three-part name ✅
- [x] **2.3** `seed_metadata.Notebook` authored — includes `grocery_gen` wheel smoke test ✅
- [x] **2.4** `run_bronze.Notebook` authored — default lakehouse `lh_bronze` ✅
- [x] **2.5** `run_silver.Notebook` authored — default lakehouse `lh_silver` ✅
- [x] **2.6** `run_gold.Notebook` (dispatcher) + `gold_dim_product.Notebook` authored ✅
- [x] **2.7** Cross-lakehouse model verified against spec table ✅
- [x] **2.8** All 7 notebooks deployed via `deploy.py` — Published in `ws-grocery-orchestration-dev` ✅
- [x] **2.9** `init_runs_log` run once (creates table); `seed_metadata` run once (1 row in `config.table_metadata`) ✅ — lakehouse GUIDs written back by Fabric and committed to main
- [x] **2.10** `pl_grocery_medallion` pipeline created — 4 activities (SeedMetadata → BronzeDims → SilverDims → GoldDims) ✅ — authored directly as git-format `DataPipeline` item (using `pl_dim_product.DataPipeline` from Phase 3 as a template, notebook GUIDs pulled from the workspace via Fabric REST API) and published via `deploy.py`, skipping manual UI authoring; item id `f4785488-3a93-4718-bc14-c6e6c827101a` in `ws-grocery-orchestration-dev`

---

## Section 3 — Retrofit Phase 3

- [x] **3.1** `lh_bronze/Files/landing/dim_product.parquet` confirmed present (or re-uploaded) ✅ — verified via OneLake DFS API, 95,285 bytes, last modified 2026-05-12 (carried over from Phase 3), no re-upload needed
- [ ] **3.2** `pl_grocery_medallion` run end-to-end — 2000 rows in `lh_gold.conformed.dim_product`, 3 success rows in `lh_orchestration.runs.pipeline_runs`
- [ ] **3.3** Phase 3 artifacts removed from `fabric/engineering/` (4 items), `deploy.py --unpublish-orphans` run against engineering workspace, items gone from `ws-grocery-engineering-dev`

---

## Section 4 — Verify, tag, document

- [ ] **4.1** End-to-end verification after cleanup — pipeline green, Gold output matches Phase 3 numbers
- [ ] **4.2** Round-trip Git sync verified — comment added to `util_logging` locally, deployed, visible in Fabric
- [ ] **4.3** README Architecture section updated with deployment platform + orchestration platform descriptions
- [ ] **4.4** Tagged `v0.3.5-orchestration-platform`

---

## Notes

- SPN secret expires 6 months from creation — set a calendar reminder for month 5 to rotate.
- `config/fabric-ids.yaml` is gitignored; `config/fabric-ids.example.yaml` is the committed template.
- Do not commit `.env` or `config/fabric-ids.yaml`.
- `[tool.uv.dev-dependencies]` deprecation warning — deferred to Phase 7.
- Phase 3 lakehouses already have the `conformed` schema — `run_bronze`/`run_silver`/`run_gold` do not need `CREATE SCHEMA`.
- Fabric Environment publish takes 5–15 min on first publish. Don't deploy notebooks until status is "Published".
- `%run util_logging` cells: no `#` prefix. `# %run` is a Python comment and silently does nothing.
