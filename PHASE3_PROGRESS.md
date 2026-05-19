# Phase 3 Progress Tracker

Last updated: 2026-04-27

## Status: PAUSED — resuming Step 11 (semantic model)

---

## Completed

- [x] PR #2 merged — `fabric/` subfolders scaffolded on `main`
- [x] PR #4 merged — ruff fixes (SIM108 + format) on `main`
- [x] `main` is clean, CI green
- [x] **Step 1:** `fabric/storage`, `fabric/engineering`, `fabric/semantic`, `fabric/bi`, `fabric/ai` folders exist on `main`
- [x] **Step 2:** All 5 dev workspaces created in Fabric portal (Trial capacity)
  - `ws-grocery-storage-dev`
  - `ws-grocery-engineering-dev`
  - `ws-grocery-semantic-dev`
  - `ws-grocery-bi-dev`
  - `ws-grocery-ai-dev`

---

## In Progress

- [ ] **Step 3:** Connect each workspace to GitHub (`main` branch, per-workspace subfolder)
  - **Note:** Use PAT (not OAuth). GitHub → Settings → Developer settings → Tokens (classic) → scope: `repo`

  | Workspace | Git folder | Connected? |
  |---|---|---|
  | `ws-grocery-storage-dev` | `fabric/storage` | ✅ |
  | `ws-grocery-engineering-dev` | `fabric/engineering` | ✅ |
  | `ws-grocery-semantic-dev` | `fabric/semantic` | ✅ |
  | `ws-grocery-bi-dev` | `fabric/bi` | ✅ |
  | `ws-grocery-ai-dev` | `fabric/ai` | ✅ |

  After each: expect "0 items to sync" both directions.

---

## Not Started

- [x] **Step 4:** Create 3 lakehouses in `ws-grocery-storage-dev`
  - `lh_bronze` — schemas enabled, `CREATE SCHEMA conformed;`, `Files/landing/` folder created
  - `lh_silver` — schemas enabled, `CREATE SCHEMA conformed;`
  - `lh_gold`  — schemas enabled, `CREATE SCHEMA conformed;`
  - All 3 synced to Git (committed directly to `main` from workspace)
  - Note: fine-grained PAT needed with Contents=Read/Write + Metadata=Read-only

- [ ] **Step 5:** Note down ABFS paths for all 3 lakehouses (don't commit GUIDs)

- [x] **Step 6:** `dim_product.parquet` uploaded to `lh_bronze/Files/landing/`

- [x] **Step 7:** `bronze__01_ingest_dim_product` — runs successfully, 2000 rows in `lh_bronze.conformed.dim_product` ✅ Synced to Git
  - Fix: add `spark.sql("CREATE SCHEMA IF NOT EXISTS conformed")` before saveAsTable

- [x] **Step 8:** `silver__02_clean_dim_product` — 2000 rows in `lh_silver.conformed.dim_product` ✅ Synced to Git

- [x] **Step 9:** `gold__03_derive_dim_product` — 2000 rows in `lh_gold.conformed.dim_product` ✅ Synced to Git

- [x] **Step 10:** `pl_dim_product` pipeline — Bronze → Silver → Gold, ran green ✅ Synced to Git

- [x] **Step 11:** `sm_grocery_core` semantic model — Direct Lake on `lh_gold.conformed.dim_product` ✅ Synced to Git

- [x] **Step 12:** `rpt_dim_product_overview` report — treemap + bar chart ✅ Synced to Git

- [x] **Step 13:** End-to-end test — pipeline ran green, semantic model refreshed, `rpt_dim_product_overview` renders correctly (treemap: 10 departments, bar chart: Alcohol top ~$40, Fresh Produce bottom ~$5) ✅

- [ ] **Step 14:** Round-trip Git verification — edit a notebook from VS Code, PR to main, confirm workspace picks it up

- [ ] **Step 15:** Tag `v0.3.0-phase3-spike`, update README Architecture section

---

## Active branch
`feature/phase-3-fabric-spike-2` (already merged — all remaining Fabric artefacts
will be committed to a new branch when round-trip Git sync is verified in Step 14)

## Notes
- Fabric notebook code is in the spec (PHASE_3_SPEC_FINAL_V3.md). Ask Claude to
  paste each cell when you reach Steps 7, 8, 9.
- Don't commit lakehouse GUIDs/ABFS paths to the repo.
- Trial capacity 60-day clock is running — set a calendar reminder for day 50.
