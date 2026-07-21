# Bike Store Metrics Catalog

Sprint 7 moves metric definitions from a small compatibility view into seeded Supabase tables under the `agent` schema.

## Source Of Truth

Primary table:

```text
agent.metric_catalog
```

Compatibility view kept for the Streamlit dashboard:

```text
agent.metric_catalog_seed
```

Seed and DDL files:

```text
sql/agent/010_agent_metadata_tables.sql
sql/agent/020_seed_agent_metadata.sql
```

Run only the metadata seed:

```powershell
python scripts/seed_agent_metadata.py
```

Run with the normal SQL model flow:

```powershell
python scripts/run_sql_models.py
```

## Seeded Domains

The catalog covers:

- sales: revenue, gross_sales, discount_amount, orders, units_sold, AOV, discount_rate, sales_growth.
- customer: customer count, frequency, revenue per customer, state revenue, top customers.
- product: product/category/brand revenue, units sold, average selling price, product discount.
- inventory: stock quantity, inventory value, sales velocity, stockout and overstock risk.
- store: store revenue, orders, AOV, late shipment rate, inventory health.
- staff: orders, revenue, AOV and manager performance.
- data_quality: pass rate, failed checks, issue count and fact-level anomaly metrics.

Every metric row includes formula, grain, primary source, related tables, owner agent, display format and caveats when needed.

## Related Metadata

```text
agent.agent_registry
agent.sql_templates
agent.question_examples
agent.rag_embeddings
```

`agent.sql_templates` documents the deterministic readonly query templates used by the Python agents. `agent.question_examples` contains Vietnamese demo/evaluation questions with expected agents, templates, metrics and source tables.
