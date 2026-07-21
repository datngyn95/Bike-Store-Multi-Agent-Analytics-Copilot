# AGENT.md: Implementation Guide

## 1. Mission

Build `Bike_Store_Project` as a cloud-first analytics project using Supabase PostgreSQL and a Vietnamese multi-agent analytics copilot.

The project must demonstrate:

- CSV ingestion from the Bike Store dataset.
- Supabase cloud database as the primary analytical store.
- SQL staging, warehouse facts/dims, marts and metric catalog.
- Streamlit dashboard as the main demo UI.
- React/Next frontend for Vercel demo.
- FastAPI service for metrics and copilot.
- Multi-agent analytics architecture.
- Gemini-first RAG/LLM layer with pgvector and strict SQL guardrails.

Use `PRD.md` as the product source of truth.

## 2. Non-Negotiable Rules

- Do not modify files in `../Bike_Store_DB`.
- Copy CSV snapshots into `raw/` and load ETL from project-local `raw/`.
- Treat Supabase PostgreSQL as the source of truth after ETL.
- Do not make DuckDB/Parquet the main warehouse for this project.
- Keep scripts reproducible; avoid manual-only notebook workflows.
- Store credentials only in `.env`; never commit secrets.
- Use service-role credentials only in backend scripts, never in frontend/browser code.
- Every generated SQL query from the copilot must be read-only `SELECT`.
- Only allow copilot SQL against approved `analytics.*` views/marts and safe `agent.*` metadata tables.
- Every agent response should include evidence: SQL, metric name, table/mart source, filters and warnings.
- If a KPI cannot be computed from available data, say it is unavailable instead of inventing it.

## 3. Updated Stack

Core runtime:

```text
Python 3.11+
Supabase PostgreSQL
SQLAlchemy or psycopg
pandas
python-dotenv
pydantic
```

Analytics:

```text
Postgres SQL
views/materialized views
SQL marts
metric catalog tables
data quality SQL tests
```

App:

```text
Streamlit
FastAPI
Plotly
pytest
```

AI:

```text
Google Gemini as default LLM
OpenAI as optional fallback only
FastEmbed
pgvector on Supabase
NetworkX for Graph RAG metadata when useful
```

Frontend:

```text
Streamlit local analytics dashboard
React/Next frontend for Vercel deployment
Demo auth enabled
```

MCP:

```text
Supabase MCP
Context7 MCP
Playwright MCP
Custom Bike Store MCP server
```

## 4. Expected Repository Shape

```text
Bike_Store_Project/
  PRD.md
  AGENT.md
  MCP.md
  SKILL.md
  requirements.txt
  .env.example

  raw/
  sql/
    ddl/
    models/
    marts/
    agent/
  scripts/
  agents/
  api/
    app/
      routes/
  dashboard/
    pages/
    components/
  frontend/
    src/
  docs/
  tests/
    data_quality/
    api/
    agents/
  reports/
```

## 5. Environment Contract

Recommended `.env.example` later:

```env
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
DATABASE_URL=postgresql://postgres.<PROJECT_REF>:<PASSWORD>@<REGION>.pooler.supabase.com:5432/postgres?sslmode=require
DIRECT_URL=postgresql://postgres:<PASSWORD>@db.<PROJECT_REF>.supabase.co:5432/postgres?sslmode=require

LLM_PROVIDER=gemini
GEMINI_API_KEY=
OPENAI_API_KEY=

VECTOR_STORE=pgvector
PGVECTOR_SCHEMA=agent

DASHBOARD_AUTH_ENABLED=true
DASHBOARD_DEMO_USER=
DASHBOARD_DEMO_PASSWORD=

COPILOT_SQL_ROW_LIMIT=100
COPILOT_SQL_TIMEOUT_SECONDS=15
```

Use `DATABASE_URL` for app/runtime connection. Use `DIRECT_URL` for migrations only when required. Do not put demo auth credentials or service-role keys in frontend code.

## 6. Source Data Contract

CSV files have no header. Always pass explicit column names. ETL should load from project-local `raw/`, which is copied from `../Bike_Store_DB`.

```text
brands.csv:
brand_id, brand_name

categories.csv:
category_id, category_name

customers.csv:
customer_id, first_name, last_name, phone, email, street, city, state, zip_code

orders.csv:
order_id, customer_id, order_status, order_date, required_date, shipped_date, store_id, staff_id

order_items.csv:
order_id, item_id, product_id, quantity, list_price, discount

products.csv:
product_id, product_name, brand_id, category_id, model_year, list_price

staffs.csv:
staff_id, first_name, last_name, email, phone, active, store_id, manager_id

stocks.csv:
store_id, product_id, quantity

stores.csv:
store_id, store_name, phone, email, street, city, state, zip_code
```

Convert string `NULL` to database null.

## 7. Database Design

Create schemas:

```sql
create schema if not exists raw;
create schema if not exists staging;
create schema if not exists analytics;
create schema if not exists agent;
create schema if not exists audit;
```

Layering:

```text
raw.*       = loaded CSV rows
staging.*   = typed and cleaned views/tables
analytics.* = facts, dims, marts
agent.*     = metric catalog, SQL templates, agent metadata
audit.*     = ETL logs, data quality logs, copilot query logs
```

## 8. Implementation Workflow

For each sprint:

1. Read `PRD.md`, this file and relevant SQL/docs.
2. Use Context7 before relying on current library/API behavior.
3. Implement the smallest runnable slice.
4. Add or update tests/report scripts.
5. Run verification commands.
6. Update docs when behavior changes.

## 9. Sprint Execution Guide

### Sprint 0: Docs and Skeleton

Deliver:

- `PRD.md`
- `AGENT.md`
- `MCP.md`
- `SKILL.md`
- Folder skeleton
- Initial data dictionary notes

### Sprint 1: Supabase Raw Layer

Deliver:

- `sql/ddl/001_create_schemas.sql`
- `sql/ddl/002_raw_tables.sql`
- `scripts/load_csv_to_supabase.py`
- Row-count validation report.
- Copy 9 CSV files into `raw/`.

Acceptance:

- All 9 CSV files load into `raw.*`.
- Row counts match expected profile.
- Loader is idempotent or has explicit truncate/reload mode.

### Sprint 2: Staging and Data Quality

Deliver:

- `sql/models/stg_*.sql`
- `scripts/check_data_quality.py`
- `reports/data_quality_summary.json`

Checks:

- Primary key uniqueness.
- Foreign key integrity.
- Required columns not null.
- Valid date order: `order_date <= required_date`; shipped date can be null.
- Non-negative quantity/price/discount.

### Sprint 3: Analytics Warehouse

Deliver:

- Dimensions.
- `fact_sales`.
- `fact_inventory`.
- Core marts.
- Metric catalog seed.

Required marts:

```text
analytics.mart_sales_monthly
analytics.mart_sales_by_store
analytics.mart_product_performance
analytics.mart_inventory_risk
analytics.mart_customer_segments
analytics.mart_staff_performance
```

### Sprint 4: Streamlit Dashboard

Deliver pages:

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

Dashboard must query Supabase, not local CSV.

Dashboard must support simple demo auth when `DASHBOARD_AUTH_ENABLED=true`.

### Sprint 5: FastAPI Service

Deliver:

- `/health`
- `/metrics/*`
- `/copilot/ask`
- API tests.

### Sprint 6: Multi-Agent Layer

Deliver:

- `agents/base_agent.py`
- `agents/orchestrator.py`
- Domain agents.
- Intent classifier.
- SQL template selection.
- Agent response contract.

### Sprint 7: RAG and SQL Guardrails

Deliver:

- Metric/schema/document graph.
- Vector index with `pgvector` on Supabase.
- SQL validator.
- Evaluation questions.

Commands:

```powershell
python scripts/seed_agent_metadata.py
python scripts/build_rag_index.py --sync-pgvector
```

### Sprint 8: React/Next Frontend and Vercel

Deliver:

- `frontend/` app.
- Authenticated demo screens.
- API integration through safe FastAPI endpoints.
- Vercel deployment notes.

### Sprint 9: Polish and Demo

Deliver:

- Demo script.
- Portfolio case study.
- Playwright E2E checks.
- Final test report.

## 10. Agent Contracts

All agents should return:

```python
{
    "agent": "sales_agent",
    "answer": "...",
    "sql": "select ...",
    "rows": [],
    "metrics": [],
    "tables": [],
    "filters": {},
    "warnings": [],
}
```

### Orchestrator Agent

Responsibilities:

- Classify Vietnamese question intent.
- Choose one or more domain agents.
- Merge answers.
- Prevent unsupported metric claims.
- Log route and latency.

### Sales Agent

Query revenue, orders, units sold, AOV, discount and sales trend.

### Customer Agent

Query state/city distribution, top customers, revenue per customer and order frequency.

### Product Agent

Query product, category, brand, model year and discount performance.

### Inventory Agent

Query stock quantity, sales velocity, stockout risk and overstock risk.

### Store Agent

Query store revenue, orders, AOV, late shipment rate and inventory health.

### Staff Agent

Query staff revenue, order count, AOV and manager/store performance.

### Data Quality Agent

Query validation reports and explain data issues.

## 11. SQL Guardrail Rules

Before executing any generated SQL:

- Strip comments.
- Reject multiple statements.
- Parse or regex-check first keyword is `select` or `with`.
- Reject destructive keywords.
- Require allowlisted schema/table names.
- Add `limit` if missing.
- Execute with timeout.
- Log query to `audit.copilot_query_log`.

Reject keywords:

```text
insert update delete drop alter truncate create grant revoke copy execute call
```

Allowlist:

```text
analytics.*
agent.metric_catalog
agent.sql_templates
agent.agent_registry
agent.question_examples
```

## 12. MCP Usage

- Use Supabase MCP for database/schema/migration inspection when available.
- Use Context7 MCP before coding with Supabase, Streamlit, FastAPI, Gemini, OpenAI fallback, SQLAlchemy, psycopg, pgvector, React, Next or Vercel.
- Use Playwright MCP for dashboard/copilot E2E tests.
- Use the custom MCP pattern from `../GenAPI/day3/mcp` if building a Bike Store MCP server.
- Treat Duckle MCP from `../FuzzyFactory_project` as a pattern reference only, not core architecture.

## 13. Verification

Minimum checks per sprint:

```powershell
python scripts/check_data_quality.py
python scripts/run_sql_models.py
pytest
```

For dashboard:

```powershell
python -m streamlit run dashboard/streamlit_app.py --server.port 8501 --server.address localhost
```

For API:

```powershell
python -m uvicorn api.app.main:app --host 127.0.0.1 --port 8000
```

## 14. Example Business Questions

```text
Doanh thu theo thang nam 2017 nhu the nao?
Cua hang nao co doanh thu cao nhat?
San pham nao ban chay nhung ton kho thap?
Brand nao dong gop doanh thu lon nhat?
Khach hang o bang nao co revenue cao nhat?
Nhan vien nao xu ly nhieu don nhat?
Cua hang nao co ty le giao tre cao nhat?
Co loi du lieu nao trong order_items khong?
```
