# Grocery Medallion AU

End-to-end data engineering portfolio project: synthetic Australian grocery data through a medallion architecture in Microsoft Fabric, with AI-powered demand forecasting and an MCP agent.

![Build](https://img.shields.io/github/actions/workflow/status/your-org/grocery-medallion-au/ci.yml?branch=main)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Overview

This project generates synthetic transactional data for a fictional Australian grocery retailer — covering fresh produce, bakery, dairy, and meat — and pipelines it through Bronze, Silver, and Gold layers in Microsoft Fabric. A semantic model built on the Gold layer powers Power BI reports and a conversational AI agent via an MCP server. Fresh-goods modelling (GST exemptions, seasonal wastage, supplier lead times) and a containerised demand forecasting model deployed via Azure AI Foundry are the primary technical differentiators.

## Architecture

### Fabric workspace topology

Five function-split Fabric workspaces, each connected to this repo via Git integration (PAT, per-workspace subfolder):

| Workspace | Git folder | Purpose |
|---|---|---|
| `ws-grocery-storage-dev` | `fabric/storage` | Three schema-enabled lakehouses: `lh_bronze`, `lh_silver`, `lh_gold` |
| `ws-grocery-engineering-dev` | `fabric/engineering` | PySpark notebooks + Fabric pipeline |
| `ws-grocery-semantic-dev` | `fabric/semantic` | Direct Lake semantic model |
| `ws-grocery-bi-dev` | `fabric/bi` | Power BI reports |
| `ws-grocery-ai-dev` | `fabric/ai` | MCP server + Foundry agent (Phase 10) |

### Medallion layers

- **Bronze (`lh_bronze.conformed.dim_product`):** Raw Parquet landed from the synthetic generator, ingested with an audit batch-ID column.
- **Silver (`lh_silver.conformed.dim_product`):** DQ-validated — null checks, duplicate checks, price-above-cost assertion.
- **Gold (`lh_gold.conformed.dim_product`):** Derived columns — `is_perishable`, `is_seasonal`, `price_tier`, `margin_pct` — optimised for the semantic model.
- **Semantic model (`sm_grocery_core`):** Direct Lake on Gold; powers `rpt_dim_product_overview` (treemap by department/category, avg retail price by department).

### Remaining phases

- **CI/CD:** GitHub Actions runs linting, type-checking, and tests on every push.
- **Governance:** Microsoft Purview catalogue and lineage (Phase 6).
- **Forecasting:** Containerised demand forecasting model for fresh produce, deployed via Azure AI Foundry (Phase 9).
- **Agent:** MCP server exposing the Gold semantic model to AI agents in Azure AI Foundry (Phase 10).

## Repository layout

```
grocery-medallion-au/
├── .github/workflows/      CI/CD pipeline definitions
├── docs/                   Design documents and architecture diagrams
├── fabric/
│   ├── storage/            Lakehouse definitions (lh_bronze, lh_silver, lh_gold)
│   ├── engineering/        PySpark notebooks + Fabric pipeline
│   ├── semantic/           Direct Lake semantic model
│   ├── bi/                 Power BI reports
│   └── ai/                 MCP server + Foundry agent (Phase 10)
├── packages/
│   ├── grocery-gen/        Synthetic data generator CLI
│   ├── grocery-forecast/   Demand forecasting model (Phase 9)
│   └── grocery-mcp/        MCP server for AI agent (Phase 10)
├── .pre-commit-config.yaml Pre-commit hooks (ruff, mypy, etc.)
├── pyproject.toml          Workspace root — shared tooling config
└── README.md               This file
```

## Quick start

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install all workspace packages
uv sync

# Run the data generator CLI
uv run grocery-gen --help
```

## Roadmap

- [x] Phase 1: Project skeleton + CLI scaffolding
- [x] Phase 2: `dim_product` synthetic generator — 2 000 SKUs, AU GST rules, seasonal fresh goods, charm pricing
- [x] Phase 3: Fabric spike — 5-workspace topology, medallion lakehouses, PySpark notebooks, pipeline, Direct Lake semantic model, Power BI report, Git round-trip verified (`v0.3.0-phase3-spike`)
- [ ] Phase 4: Full dimension suite (stores, customers, dates, promotions)
- [ ] Phase 5: Fact tables + incremental load
- [ ] Phase 6: Purview catalogue + lineage
- [ ] Phase 7: CI/CD for Fabric artefacts via GitHub
- [ ] Phase 8: Daily incremental generator scheduled in Fabric
- [ ] Phase 9: Demand forecasting model (containerised, deployed via Foundry)
- [ ] Phase 10: MCP server + agent in Azure AI Foundry

## License

MIT — see [LICENSE](LICENSE).

## Author

Sunil Venkatesh — [sunilv@techworksconsulting.com.au](mailto:sunilv@techworksconsulting.com.au)
