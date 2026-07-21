# MCP.md: MCP Plan For Bike Store Project

## 1. Purpose

This project should use MCP servers to reduce manual work around cloud database operations, documentation lookup, browser testing and optional custom analytics tools.

Priority order:

```text
1. Supabase MCP
2. Context7 MCP
3. Playwright MCP
4. Custom Bike Store MCP server
5. Duckle MCP pattern reference
```

## 2. Supabase MCP

Source found in previous workspace:

- `../MCP.txt`
- `../GenAPI/day3/mcp/.mcp.json`
- `../try-on-codex-sprint2/.mcp.json`

Known setup:

```powershell
codex mcp add supabase --url "https://mcp.supabase.com/mcp"
codex mcp login supabase
codex mcp list
```

Example `.mcp.json`:

```json
{
  "mcpServers": {
    "supabase": {
      "type": "http",
      "url": "https://mcp.supabase.com/mcp"
    }
  }
}
```

Use Supabase MCP for:

- Inspecting projects and database schemas.
- Creating or reviewing migrations.
- Checking table/view definitions.
- Running safe SQL during development.
- Verifying row counts and data quality outputs.
- Managing Supabase project metadata where supported.

Do not expose service role keys in prompts, CLI arguments or frontend code.

## 3. Context7 MCP

Source found in previous workspace:

- `../try-on-codex-sprint2/.claude/settings.local.json`
- `../GenAPI/GenAPI.txt`
- `../FUTURE-BOXES-V1/.claude/agents/agent-react.md`
- `../FUTURE-BOXES-V1/.claude/agents/agent-uiux.md`

Use Context7 before coding with:

```text
Supabase Python client
Postgres / pgvector
SQLAlchemy
psycopg
Streamlit
FastAPI
Pydantic
Gemini / Google GenAI SDK
OpenAI SDK if fallback is implemented
React
Next.js
Vercel
Plotly
Playwright
```

Expected workflow:

```text
1. Resolve library ID.
2. Query current docs.
3. Implement based on current API.
4. Record assumptions in docs or comments if behavior is version-sensitive.
```

## 4. Playwright MCP

Source found in previous workspace:

- `../1806.txt`
- `../reading-diary-starter/CLAUDE.md`

Use Playwright MCP for E2E testing:

- Streamlit page loads.
- Dashboard filters update charts.
- Copilot question submits successfully.
- Copilot displays answer, SQL, selected agent and table rows.
- Data Quality page shows pass/fail state.

Example E2E flows:

```text
Open Executive page -> verify KPI cards render
Open Sales page -> select year 2017 -> verify monthly chart changes
Open Inventory page -> filter high stockout risk -> verify table rows
Open Copilot page -> ask "Cua hang nao doanh thu cao nhat?" -> verify Sales Agent and SQL are shown
```

## 5. Custom Bike Store MCP Server

Reference pattern:

- `../GenAPI/day3/mcp/README.md`

That project used:

```text
User <-> Streamlit MCP Client + Gemini <-> MCP Server <-> Supabase REST API
```

For Bike Store, create a custom MCP server only after core Supabase tables and marts exist.

Recommended tools:

| Tool | Purpose |
| --- | --- |
| `get_schema_info` | Return safe schema/table/column metadata |
| `get_metric_catalog` | Return metric definitions |
| `query_sales` | Query sales marts with filters |
| `query_customers` | Query customer marts with filters |
| `query_products` | Query product/category/brand marts |
| `query_inventory` | Query inventory risk mart |
| `query_stores` | Query store performance mart |
| `query_staff` | Query staff performance mart |
| `run_data_quality_check` | Return data quality summary |
| `aggregate_metric` | Safe group-by aggregation for charts |

Tool contract:

```json
{
  "filters": {
    "start_date": "2017-01-01",
    "end_date": "2017-12-31",
    "store_id": 1
  },
  "limit": 100
}
```

Return:

```json
{
  "rows": [],
  "sql": "select ...",
  "metrics": [],
  "tables": [],
  "warnings": []
}
```

Security rules:

- Tools should execute predefined SQL templates or validated query builders.
- Do not accept arbitrary SQL from clients.
- Apply row limit and timeout.
- Use service role only server-side.

## 6. Duckle MCP Pattern Reference

Reference:

- `../FuzzyFactory_project/dashboard/services/duckle_mcp.py`
- `../FuzzyFactory_project/README.md`

Use as a pattern for:

- MCP status page.
- Tool list/auth check.
- Pipeline status contract.
- Warehouse status contract.
- Metric catalog contract.

Do not make Duckle MCP required for this project because Bike Store is Supabase cloud-first.

## 7. Recommended MCP-Backed Workflow

Sprint 1:

```text
Use Supabase MCP to verify schemas/tables.
Use Context7 for Supabase/Postgres connection docs.
```

Sprint 2:

```text
Use Supabase MCP for data quality SQL checks.
Use Context7 for SQLAlchemy/psycopg patterns.
```

Sprint 4:

```text
Use Context7 for Streamlit and Plotly.
Use Playwright MCP for UI smoke tests.
```

Sprint 6:

```text
Use Context7 for LLM SDK.
Optionally build custom Bike Store MCP tools.
```

Sprint 8:

```text
Use Context7 for React/Next/Vercel docs.
Use Playwright MCP for authenticated frontend smoke tests.
```

Sprint 9:

```text
Use Playwright MCP for demo E2E.
Use Supabase MCP for final database verification.
```

## 8. Files To Add Later

```text
.mcp.json
scripts/mcp_server.py
scripts/mcp_client_smoke_test.py
docs/mcp_tool_contracts.md
```

Initial `.mcp.json`:

```json
{
  "mcpServers": {
    "supabase": {
      "type": "http",
      "url": "https://mcp.supabase.com/mcp"
    }
  }
}
```
