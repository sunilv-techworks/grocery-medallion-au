# Grocery Medallion AU

End-to-end data engineering portfolio project: synthetic Australian grocery data through a medallion architecture in Microsoft Fabric, with AI-powered demand forecasting and an MCP agent.

![Build](https://img.shields.io/github/actions/workflow/status/your-org/grocery-medallion-au/ci.yml?branch=main)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Overview

This project generates synthetic transactional data for a fictional Australian grocery retailer — covering fresh produce, bakery, dairy, and meat — and pipelines it through Bronze, Silver, and Gold layers in Microsoft Fabric. A semantic model built on the Gold layer powers Power BI reports and a conversational AI agent via an MCP server. Fresh-goods modelling (GST exemptions, seasonal wastage, supplier lead times) and a containerised demand forecasting model deployed via Azure AI Foundry are the primary technical differentiators.

## Architecture

- **Bronze layer:** Raw Parquet files landed from the synthetic generator, partitioned by date and domain.
- **Silver layer:** Cleaned, conformed, and enriched dimension and fact tables; deduplication and schema enforcement via Great Expectations.
- **Gold layer:** Star-schema semantic model optimised for Power BI; surrogate keys, slowly-changing dimensions, and pre-aggregated measures.
- **CI/CD:** GitHub Actions runs linting, type-checking, and tests on every push; Fabric artefacts are deployed via GitHub integration (Phase 7).
- **Data quality:** Great Expectations expectation suites are shared between the local generator pipeline and Fabric notebooks, ensuring consistent validation across environments.
- **Governance:** Microsoft Purview catalogue and lineage (Phase 6).
- **Forecasting:** Containerised demand forecasting model for fresh produce, trained and deployed via Azure AI Foundry (Phase 9).
- **Agent:** MCP server exposing the Gold semantic model to AI agents in Azure AI Foundry (Phase 10).

An architecture diagram lives at `docs/images/architecture.png` (placeholder — to be added in Phase 4).

## Repository layout

```
grocery-medallion-au/
├── .github/workflows/      CI/CD pipeline definitions
├── docs/                   Design documents and architecture diagrams
├── packages/
│   ├── grocery-gen/        Synthetic data generator CLI (Phase 1–3)
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
- [ ] Phase 2: Synthetic data generator (dimensions + facts)
- [ ] Phase 3: Containerise generator + GitHub Actions CI
- [ ] Phase 4: Fabric Bronze/Silver/Gold notebooks
- [ ] Phase 5: Semantic model + Power BI reports
- [ ] Phase 6: Purview catalogue + lineage
- [ ] Phase 7: CI/CD for Fabric artefacts via GitHub
- [ ] Phase 8: Daily incremental generator scheduled in Fabric
- [ ] Phase 9: Demand forecasting model (containerised, deployed via Foundry)
- [ ] Phase 10: MCP server + agent in Azure AI Foundry

## License

MIT — see [LICENSE](LICENSE).

## Author

Your Name — [your-email@example.com](mailto:your-email@example.com)
