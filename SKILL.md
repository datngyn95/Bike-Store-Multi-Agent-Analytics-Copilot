---
name: bike-store-multi-agent-analytics
description: Use when building, modifying, reviewing, or extending the Bike Store Multi-Agent Analytics Copilot project. Applies to Supabase cloud database setup, CSV ETL, SQL marts, Streamlit dashboards, FastAPI services, multi-agent analytics, Vietnamese copilot behavior, MCP usage, and project documentation.
---

# Bike Store Multi-Agent Analytics Skill

## Core Instruction

When working in this project, read these files first:

```text
PRD.md
AGENT.md
MCP.md
```

Treat `PRD.md` as the product source of truth, `AGENT.md` as the implementation guide, and `MCP.md` as the tool integration plan.

## Project Doctrine

Build cloud-first, not local-first.

```text
CSV snapshot in raw/ -> Supabase PostgreSQL -> analytics marts -> dashboard/API -> multi-agent copilot
```

Do not use DuckDB/Parquet as the primary warehouse. Use Supabase PostgreSQL as the durable analytical source of truth.

Do not modify source CSVs in `../Bike_Store_DB`. Copy them into `raw/` and load ETL from the project-local snapshot.

Use Gemini as the default LLM and `pgvector` on Supabase as the RAG/vector store.

## Default Workflow

1. Identify the sprint or domain being changed.
2. Read the relevant project docs and existing code.
3. Use Context7 for current library/API documentation when coding with frameworks or SDKs.
4. Use Supabase MCP when database inspection or migration verification is available.
5. Implement a small reproducible slice.
6. Add focused verification.
7. Update docs if behavior, schema, metrics, MCP tools, or agent contracts change.

## Domain Agent Map

Route business questions by domain:

| Domain | Agent |
| --- | --- |
| revenue, orders, AOV, discount, trend | Sales Agent |
| customers, states, top buyers, frequency | Customer Agent |
| products, categories, brands, model year | Product Agent |
| stock, stockout, overstock, inventory value | Inventory Agent |
| stores, store revenue, delivery delay | Store Agent |
| staff, manager, staff revenue/orders | Staff Agent |
| nulls, duplicates, FK, invalid dates | Data Quality Agent |
| mixed or ambiguous intent | Orchestrator Agent |

## SQL Rules

Generated copilot SQL must be safe:

- Allow only `SELECT` or `WITH ... SELECT`.
- Reject destructive keywords.
- Query only approved `analytics.*` marts/views and safe `agent.*` metadata.
- Add row limit when missing.
- Log executed queries.
- Explain unavailable metrics instead of inventing values.

## Supabase Rules

Use schemas consistently:

```text
raw       = loaded CSV rows
staging   = typed and cleaned data
analytics = facts, dimensions, marts
agent     = metric catalog and agent metadata
audit     = logs and checks
```

Use service role only in backend scripts. Do not expose it to Streamlit browser output, client code, logs, or screenshots.

## Dashboard Rules

Streamlit is the MVP local UI. Add a React/Next frontend for Vercel demo. Both should query Supabase through safe backend/service paths, not local CSVs.

Dashboard demo must support auth through environment variables, not hard-coded credentials.

Expected pages:

```text
Executive
Sales
Customers
Products
Inventory
Stores
Staff
Data Quality
Copilot
```

The Copilot page should show:

```text
answer
selected agent(s)
SQL
result rows
metric definitions
source marts/tables
warnings
```

## Documentation Rules

Keep docs practical and implementation-ready.

Update:

- `PRD.md` when product scope changes.
- `AGENT.md` when implementation workflow, architecture, or rules change.
- `MCP.md` when MCP setup/tool contracts change.
- `docs/metrics_catalog.md` when metrics change.
- `docs/data_dictionary.md` when schema interpretation changes.

## Verification

Prefer these checks as the project grows:

```powershell
python scripts/check_data_quality.py
python scripts/run_sql_models.py
pytest
python -m streamlit run dashboard/streamlit_app.py --server.port 8501 --server.address localhost
python -m uvicorn api.app.main:app --host 127.0.0.1 --port 8000
```

Use Playwright MCP for final dashboard and copilot E2E flows.
