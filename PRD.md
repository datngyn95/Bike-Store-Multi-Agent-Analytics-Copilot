# PRD: Bike Store Multi-Agent Analytics Copilot

## 1. Tong Quan

Bike Store Multi-Agent Analytics Copilot la du an phan tich du lieu ban le xe dap dua tren bo du lieu `Bike_Store_DB`. Du an bien cac file CSV thanh mot cloud analytics warehouse tren Supabase PostgreSQL, sau do cung cap dashboard, API va copilot tieng Viet theo kien truc multi-agent.

Khac voi `FuzzyFactory_project` theo huong local-first DuckDB/Parquet, du an nay theo huong cloud-first:

```text
CSV raw files
    -> ETL/validation scripts
    -> Supabase PostgreSQL
    -> analytics schemas, views, marts
    -> Streamlit dashboard + FastAPI
    -> Multi-agent Vietnamese analytics copilot
```

Muc tieu la demo nang luc end-to-end:

- Data engineering voi CSV, schema mapping, ETL, data quality.
- Cloud database/warehouse voi Supabase PostgreSQL.
- SQL analytics, star schema va mart theo tung linh vuc.
- Streamlit dashboard cho business users.
- FastAPI phuc vu metric, chart data va copilot.
- Multi-agent analytics: moi agent phu trach mot domain rieng.
- GenAI/RAG tieng Viet de hoi dap, giai thich KPI va sinh SQL co guardrail.

## 2. Boi Canh Du Lieu

Nguon du lieu goc nam o:

```text
../Bike_Store_DB/
```

Khong sua truc tiep cac CSV goc. Du an se copy CSV vao `raw/` de co snapshot noi bo cho ETL, nhung `../Bike_Store_DB` van la source of record.

| File | Dong | Vai tro |
| --- | ---: | --- |
| `brands.csv` | 9 | Thuong hieu san pham |
| `categories.csv` | 7 | Nhom san pham |
| `customers.csv` | 1,445 | Khach hang |
| `orders.csv` | 1,615 | Don hang |
| `order_items.csv` | 4,722 | Dong san pham trong don |
| `products.csv` | 321 | Danh muc san pham |
| `staffs.csv` | 10 | Nhan vien ban hang |
| `stocks.csv` | 939 | Ton kho theo cua hang va san pham |
| `stores.csv` | 3 | Cua hang |

Luu y quan trong: CSV khong co header. ETL phai gan schema ro rang khi doc file.

### 2.1 Schema Nguon De Xuat

```text
brands:
brand_id, brand_name

categories:
category_id, category_name

customers:
customer_id, first_name, last_name, phone, email, street, city, state, zip_code

orders:
order_id, customer_id, order_status, order_date, required_date, shipped_date, store_id, staff_id

order_items:
order_id, item_id, product_id, quantity, list_price, discount

products:
product_id, product_name, brand_id, category_id, model_year, list_price

staffs:
staff_id, first_name, last_name, email, phone, active, store_id, manager_id

stocks:
store_id, product_id, quantity

stores:
store_id, store_name, phone, email, street, city, state, zip_code
```

### 2.2 KPI Nen Da Kiem Tra Nhanh

```text
Tong revenue sau discount: 7,689,116.56
Orders: 1,615
Order items: 4,722
Customers co don: 1,445
Khoang ngay order: 2016-01-01 -> 2018-12-28
Late shipment rate: khoang 31.7%
```

Doanh thu theo cua hang:

```text
Baldwin Bikes: 5,215,751.28
Santa Cruz Bikes: 1,605,823.04
Rowlett Bikes: 867,542.24
```

Top category theo revenue:

```text
Mountain Bikes
Road Bikes
Cruisers Bicycles
Electric Bikes
Cyclocross Bicycles
```

## 3. Nguoi Dung Muc Tieu

| Persona | Nhu cau |
| --- | --- |
| CEO/Founder | Xem doanh thu, tang truong, cua hang/san pham tot nhat |
| Sales Manager | Theo doi doanh so, don hang, nhan vien, discount |
| Inventory Manager | Tim san pham ban chay nhung ton kho thap, overstock, stockout risk |
| Product Manager | Hieu brand/category/product performance |
| Customer Analyst | Phan tich khach hang theo state, gia tri, tan suat mua |
| Data Analyst | Co SQL, mart, metric catalog, lineage, data quality |
| Recruiter/Mentor | Nhin thay nang luc full-stack data project va AI agent design |

## 4. Pham Vi San Pham

### 4.1 In Scope MVP

- Tao Supabase schemas: `raw`, `staging`, `analytics`, `agent`, `audit`.
- Load CSV khong header vao Supabase.
- Chuan hoa type, xu ly chuoi `NULL`, date, numeric, foreign keys.
- Tao star schema va mart analytics.
- Tao dashboard Streamlit theo domain.
- Tao FastAPI service cho metrics va copilot.
- Tao multi-agent analytics layer:
  - Sales Agent
  - Customer Agent
  - Product Agent
  - Inventory Agent
  - Store Agent
  - Staff Agent
  - Data Quality Agent
  - Orchestrator Agent
- Tao metric catalog, SQL template catalog va question examples.
- Guardrail SQL: chi `SELECT`, allowlist schema/view, row limit, timeout.
- Log cau hoi, agent duoc route, SQL, latency, ket qua tom tat.
- Hoi dap tieng Viet dua tren metadata, metric catalog, schema, SQL templates va ket qua truy van.

### 4.2 Out Of Scope MVP

- Real-time streaming.
- Auth phuc tap cho end users.
- Fine-tune LLM.
- Enterprise BI.
- Multi-tenant SaaS.
- Production-grade cost monitoring.
- Chinh sua du lieu transactional tu dashboard.

## 5. Stack De Xuat

Core:

```text
Python 3.11+
Supabase PostgreSQL
Postgres SQL / views / materialized views
pandas
SQLAlchemy hoac psycopg
Streamlit
FastAPI
Plotly
Pydantic
pytest
python-dotenv
```

AI/RAG:

```text
Google Gemini `gemini-2.5-flash` mac dinh
Gemini `gemini-3.5-flash` fallback cho quota/tam thoi
OpenAI API optional sau MVP
FastEmbed
pgvector tren Supabase
NetworkX cho Graph RAG metadata
```

MCP:

```text
Supabase MCP
Context7 MCP
Playwright MCP
Custom Bike Store MCP server
```

Optional later:

```text
React/Next frontend deploy Vercel
Vercel preview/production deployment
GitHub Actions cho CI
```

## 6. Kien Truc San Pham

```text
Bike_Store_DB/*.csv
        |
        v
scripts/load_csv_to_supabase.py
scripts/check_data_quality.py
        |
        v
Supabase PostgreSQL
  raw.*
  staging.*
  analytics.*
  agent.*
  audit.*
        |
        +--> SQL marts/views
        |      - mart_sales_monthly
        |      - mart_product_performance
        |      - mart_inventory_risk
        |      - mart_customer_segments
        |      - mart_staff_performance
        |
        +--> FastAPI
        |      - /health
        |      - /metrics/*
        |      - /copilot/ask
        |
        +--> Streamlit Dashboard
        |      - local analytics workspace
        |      - Executive
        |      - Sales
        |      - Customers
        |      - Products
        |      - Inventory
        |      - Stores
        |      - Staff
        |      - Copilot
        |
        +--> React/Next Frontend
        |      - deploy Vercel
        |      - demo auth
        |      - call FastAPI/Supabase-safe endpoints
        |
        v
Multi-Agent Analytics Copilot
  Orchestrator Agent
    -> Sales Agent
    -> Customer Agent
    -> Product Agent
    -> Inventory Agent
    -> Store Agent
    -> Staff Agent
    -> Data Quality Agent
```

## 7. Cau Truc Repo Nen Lam

```text
Bike_Store_Project/
  PRD.md
  AGENT.md
  MCP.md
  SKILL.md
  requirements.txt
  .env.example

  raw/
    brands.csv
    categories.csv
    customers.csv
    orders.csv
    order_items.csv
    products.csv
    staffs.csv
    stocks.csv
    stores.csv

  sql/
    ddl/
      001_create_schemas.sql
      002_raw_tables.sql
      003_staging_tables.sql
      004_analytics_tables.sql
      005_agent_tables.sql
    models/
      stg_brands.sql
      stg_categories.sql
      stg_customers.sql
      stg_orders.sql
      stg_order_items.sql
      stg_products.sql
      stg_staffs.sql
      stg_stocks.sql
      stg_stores.sql
    marts/
      dim_customer.sql
      dim_product.sql
      dim_store.sql
      dim_staff.sql
      fact_sales.sql
      fact_inventory.sql
      mart_sales_monthly.sql
      mart_product_performance.sql
      mart_inventory_risk.sql
      mart_customer_segments.sql
      mart_staff_performance.sql
    agent/
      agent_registry.sql
      metric_catalog.sql
      sql_templates.sql
      question_examples.sql

  scripts/
    load_csv_to_supabase.py
    run_sql_models.py
    seed_agent_metadata.py
    check_data_quality.py
    build_rag_index.py

  agents/
    base_agent.py
    orchestrator.py
    sales_agent.py
    customer_agent.py
    product_agent.py
    inventory_agent.py
    store_agent.py
    staff_agent.py
    data_quality_agent.py

  api/
    app/
      main.py
      db.py
      routes/
        health.py
        metrics.py
        copilot.py

  dashboard/
    streamlit_app.py
    pages/
      executive.py
      sales.py
      customers.py
      products.py
      inventory.py
      stores.py
      staff.py
      copilot.py
    components/
      charts.py
      filters.py
      metric_cards.py

  frontend/
    package.json
    next.config.js
    src/
      app/
      components/
      lib/
      styles/

  docs/
    data_dictionary.md
    architecture.md
    metrics_catalog.md
    supabase_setup.md
    demo_script.md

  tests/
    data_quality/
    api/
    agents/

  reports/
```

## 8. Supabase Data Design

### 8.1 Schemas

| Schema | Vai tro |
| --- | --- |
| `raw` | Du lieu gan nguyen ban tu CSV |
| `staging` | Clean type, standardize null/date/numeric |
| `analytics` | Star schema, facts, dims, marts |
| `agent` | Metadata cho multi-agent, metric catalog, SQL templates |
| `audit` | Log ETL, data quality, copilot query, API latency |

### 8.2 Star Schema

Facts:

```text
analytics.fact_sales
analytics.fact_inventory
```

Dimensions:

```text
analytics.dim_customer
analytics.dim_product
analytics.dim_brand
analytics.dim_category
analytics.dim_store
analytics.dim_staff
analytics.dim_date
```

Marts:

```text
analytics.mart_sales_monthly
analytics.mart_sales_by_store
analytics.mart_product_performance
analytics.mart_inventory_risk
analytics.mart_customer_segments
analytics.mart_staff_performance
analytics.mart_delivery_performance
```

## 9. Multi-Agent Scope

### 9.1 Orchestrator Agent

Trach nhiem:

- Phan loai intent cua cau hoi tieng Viet.
- Chon mot hoac nhieu domain agents.
- Truyen context: filters, time range, metric, entity.
- Hop nhat cau tra loi va insight.
- Yeu cau agent tra lai SQL, metric source, table source.
- Tu choi hoac hoi lai neu cau hoi yeu cau du lieu khong ton tai.

### 9.2 Sales Agent

Phu trach:

- Revenue, orders, units sold, AOV.
- Monthly/yearly sales trend.
- Store sales comparison.
- Discount impact.

Metrics:

```text
revenue = quantity * list_price * (1 - discount)
orders
units_sold
average_order_value
discount_rate
sales_growth
```

### 9.3 Customer Agent

Phu trach:

- Customer distribution by state/city.
- Customer lifetime revenue proxy.
- Top customers.
- Order frequency.

Metrics:

```text
customer_count
orders_per_customer
revenue_per_customer
state_revenue
top_customers
```

### 9.4 Product Agent

Phu trach:

- Product/category/brand performance.
- Model year performance.
- Price and discount analysis.

Metrics:

```text
product_revenue
units_sold
category_revenue
brand_revenue
avg_selling_price
discount_by_product
```

### 9.5 Inventory Agent

Phu trach:

- Stock by store/product.
- Stockout risk.
- Overstock risk.
- Inventory value proxy.

Metrics:

```text
stock_quantity
sales_velocity
stockout_risk
overstock_risk
inventory_value
```

### 9.6 Store Agent

Phu trach:

- Store revenue/orders/AOV.
- Delivery delay by store.
- Store inventory health.

Metrics:

```text
store_revenue
store_orders
store_aov
late_shipment_rate
store_inventory_health
```

### 9.7 Staff Agent

Phu trach:

- Staff order count.
- Staff revenue.
- Staff/store/manager performance.

Metrics:

```text
orders_by_staff
revenue_by_staff
avg_order_value_by_staff
manager_performance
```

### 9.8 Data Quality Agent

Phu trach:

- Null checks.
- Duplicate primary keys.
- Foreign key integrity.
- Invalid dates.
- Negative quantity/price.
- Orphan records.

## 10. Dashboard Requirements

Dashboard MVP dung Streamlit local. Du an cung co frontend React/Next de deploy demo len Vercel.

Streamlit local pages:

```text
Executive Overview
Sales Agent
Customer Agent
Product Agent
Inventory Agent
Store Agent
Staff Agent
Data Quality
AI Copilot
```

React/Next frontend pages:

```text
/
/sales
/products
/inventory
/customers
/copilot
/login
```

Dashboard demo phai co auth. MVP auth co the la simple password login cho Streamlit va React/Next demo, doc tu env:

```text
DASHBOARD_AUTH_ENABLED=true
DASHBOARD_DEMO_USER=
DASHBOARD_DEMO_PASSWORD=
```

Khong hard-code credentials vao code.

AI Copilot page phai hien:

- Cau tra loi tieng Viet.
- Agent duoc route.
- SQL da chay.
- Bang ket qua.
- Metric definitions.
- Related marts/tables.
- Chart neu phu hop.
- Warning neu cau hoi yeu cau metric khong co du lieu.

## 11. API Requirements

FastAPI endpoints:

```text
GET  /health
GET  /metrics/sales/summary
GET  /metrics/sales/monthly
GET  /metrics/products/performance
GET  /metrics/inventory/risk
GET  /metrics/customers/segments
GET  /metrics/staff/performance
POST /copilot/ask
```

`POST /copilot/ask` response:

```json
{
  "answer": "...",
  "agents": ["sales_agent"],
  "sql": "select ...",
  "rows": [],
  "metrics": [],
  "tables": [],
  "warnings": [],
  "latency_ms": 1234
}
```

### 11.1 Sprint 5 Implementation Boundary

Sprint 5 phai xay FastAPI thanh service layer rieng, khong import truc tiep code Streamlit dashboard.

Khong import `dashboard/components/data.py` vao FastAPI vi module nay phu thuoc `streamlit` cache/session/runtime va chi phu hop cho Sprint 4 local dashboard.

Kien truc de xuat cho Sprint 5:

```text
api/app/
  main.py
  db.py
  routes/
    health.py
    metrics.py
    copilot.py
  services/
    metrics_service.py
    copilot_service.py
  schemas/
    metrics.py
    copilot.py
```

Nguyen tac:

- `api/app/db.py`: tao SQLAlchemy engine thuan, khong import `streamlit`.
- `api/app/services/metrics_service.py`: chua query thuan cho sales, product, inventory, customer, staff.
- `api/app/routes/metrics.py`: chi map endpoint -> service -> response JSON.
- `api/app/services/copilot_service.py`: xu ly request `/copilot/ask`, SQL template/agent routing/guardrail o layer backend rieng.
- `dashboard/components/data.py`: giu cho Sprint 4, co the dung lam reference SQL nhung khong la dependency cua API.
- Sau Sprint 5, dashboard co the duoc refactor dan de goi FastAPI thay vi query DB truc tiep.

## 12. SQL And AI Guardrails

- Generated SQL chi duoc phep la `SELECT`.
- Cam `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `CREATE`, `GRANT`, `REVOKE`.
- Chi query allowlisted schemas/views:
  - `analytics.*`
  - mot so `agent.*` metadata read-only.
- Mac dinh limit 100 rows.
- Timeout query.
- Log moi query vao `audit.copilot_query_log`.
- Khong dua raw PII vao prompt LLM neu khong can.
- Khong gui toan bo raw data cho LLM; chi gui schema, metric catalog, retrieved context va result rows da gioi han.

## 13. Success Criteria

MVP thanh cong khi:

- Load duoc 9 CSV vao Supabase.
- Tao duoc staging, facts, dims va it nhat 5 marts.
- Dashboard hien thi KPI sales, product, customer, inventory.
- Copilot tra loi duoc it nhat 20 cau hoi mau bang tieng Viet.
- Moi cau tra loi copilot co agent, SQL, metric/table source.
- Data quality report chay duoc va co pass/fail ro rang.
- Project co README/demo script sau cac sprint tiep theo.
- CSV snapshot co mat trong `raw/`.
- Dashboard demo co auth.
- RAG dung `pgvector` tren Supabase.
- `gemini-2.5-flash` la LLM mac dinh, `gemini-3.5-flash` la fallback MVP.

## 14. Sprint Plan

Trang thai cap nhat: 2026-07-18

| Sprint | Trang thai | Cong viec |
| --- | --- | --- |
| Sprint 0 | Done | Documentation, repo skeleton, schema mapping cho 9 CSV khong header, raw CSV snapshot trong `raw/`, `.env.example` va cau truc thu muc du an. |
| Sprint 1 | Done | Supabase setup cho project `trftihwibpyaabpphdtw`, tao `raw` schema/tables, viet `scripts/load_csv_to_supabase.py`, load du 9 CSV vao Supabase va verify row counts. |
| Sprint 2 | Done | Tao staging views trong `sql/models/010_staging_views.sql`, clean type/date/numeric/null va status label, viet `scripts/check_data_quality.py`, log ket qua vao `audit.data_quality_check_results`, tao report `reports/data_quality_report.md`; data quality pass `34/34`. |
| Sprint 3 | Done | Tao analytics dims/facts/marts trong `sql/marts/`, viet `scripts/run_sql_models.py`, transform `staging -> analytics`, verify KPI: revenue `7,689,116.56`, orders `1,615`, order items `4,722`. |
| Sprint 4 | Done | Streamlit dashboard MVP doc tu `analytics.*`: Executive, Sales, Customers, Products, Inventory, Stores, Staff, Data Quality va Copilot shell voi SQL templates readonly. |
| Sprint 5 | Done | Da xay FastAPI service layer rieng trong `api/app`: `/health`, `/metrics/sales/summary`, `/metrics/sales/monthly`, product, inventory, customer, staff endpoints va `/copilot/ask` template backend co SQL guardrail. API khong import `dashboard/components/data.py`; da co tests `tests/api`. |
| Sprint 6 | Done | Da xay multi-agent analytics layer trong `agents/`: domain agents cho Sales, Customer, Product, Inventory, Store, Staff va Data Quality; SQL template selection, intent routing tieng Viet, runtime SQL guardrails va `/copilot/ask` da goi orchestrator thay vi template service rieng. Da co tests `tests/agents/test_domain_agents.py`. |
| Sprint 7 | Done | Da seed metadata tables trong `agent.*`: `agent_registry`, `metric_catalog`, `sql_templates`, `question_examples`; them `agent.rag_embeddings` voi pgvector/HNSW; mo rong Graph RAG voi metric/template/question nodes; `scripts/build_rag_index.py --sync-pgvector` co the upsert embeddings len Supabase. |
| Sprint 8 | Done | Da xay React/Next frontend trong `frontend/` voi demo auth signed HttpOnly cookie, route `/`, `/sales`, `/products`, `/inventory`, `/customers`, `/copilot`, `/login`; UI goi FastAPI endpoints server-side va co docs Vercel. |
| Sprint 9 | Done | Da them Playwright E2E smoke test cho auth/dashboard/sales/copilot voi mock FastAPI, README, demo script, portfolio case study va final test report. |

### Sprint Tiep Theo Se Thuc Thi

1. MVP da hoan tat Sprint 9: chay final verification, demo theo `docs/demo_script.md` va dung `docs/portfolio_case_study.md` cho portfolio.

## 15. Decisions

| Decision | Chot |
| --- | --- |
| LLM mac dinh | Dung `gemini-2.5-flash` cho copilot MVP |
| LLM fallback | Dung `gemini-3.5-flash` khi model chinh loi quota/tam thoi; neu van loi thi degraded mode dua tren SQL template/metric catalog |
| RAG/vector store | Dung `pgvector` tren Supabase |
| Dashboard/demo UI | Dung Streamlit local va them frontend React/Next deploy Vercel |
| Auth dashboard demo | Dung simple password gate doc tu env cho MVP; chua dung Supabase Auth/NextAuth |
| CSV source trong repo | Copy CSV vao `raw/` |
| FastAPI service layer | Sprint 5 tach `api/app/db.py`, `routes/`, `services/`, `schemas/`; khong import module Streamlit dashboard vao API. |
| FastAPI deploy | Deploy cung Vercel voi React/Next bang Python Runtime hoac Vercel Services; fallback sang Render/Railway/Fly neu can backend container dai han |

## 16. Closed MVP Decisions

### 16.1 Gemini Model Va Fallback

Chot cho MVP:

- Model mac dinh: `gemini-2.5-flash`.
- Model fallback: `gemini-3.5-flash`.
- Khong dung alias `gemini-flash-latest` trong MVP de tranh model bi doi ngam khi demo.
- Khi gap loi quota hoac loi tam thoi nhu `429 RESOURCE_EXHAUSTED`, `503 UNAVAILABLE`, backend retry bang exponential backoff + jitter truoc khi fallback.
- Neu model fallback van loi, copilot tra ve degraded response dua tren agent routing, SQL templates, metric catalog va query result co san; response phai co warning ro rang rang AI quota/service dang tam thoi khong kha dung.
- Khong fallback sang OpenAI trong MVP de giu stack gon va tranh phat sinh them secret/cost. OpenAI chi giu la optional upgrade sau MVP.

Env de xuat:

```text
AI_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash
GEMINI_FALLBACK_MODEL=gemini-3.5-flash
GEMINI_MAX_RETRIES=3
```

### 16.2 Auth Demo

Chot cho MVP:

- Dung simple password gate cho Streamlit va React/Next demo.
- Credentials doc tu env, khong hard-code vao code.
- Frontend Next dung login form, server-side check password, tao signed HttpOnly cookie/session cho cac route dashboard.
- FastAPI endpoint demo co the yeu cau shared demo token/header noi bo tu frontend server route neu can bao ve API co ban.
- Chua dung Supabase Auth vi MVP khong can user management, email flow, OAuth, RLS theo user hay multi-tenant.
- Chua dung NextAuth/Auth.js vi MVP khong can social login/OAuth providers.
- Sau MVP, nang cap len Supabase Auth neu can login that, audit theo user, RLS, hoac chia quyen theo role.

Env de xuat:

```text
DASHBOARD_AUTH_ENABLED=true
DASHBOARD_DEMO_USER=
DASHBOARD_DEMO_PASSWORD=
AUTH_COOKIE_SECRET=
API_DEMO_TOKEN=
```

### 16.3 FastAPI Deployment

Chot cho MVP:

- React/Next frontend deploy tren Vercel.
- FastAPI deploy cung Vercel voi Python Runtime hoac Vercel Services trong cung repo/deployment, route duoi `/api` hoac `/backend`.
- Frontend goi backend qua env `NEXT_PUBLIC_API_BASE_URL` hoac server-side `API_BASE_URL`.
- Supabase van la cloud database chinh; khong expose service role key ra browser.
- Neu copilot bi cold start, timeout, dependency size lon, can background worker, hoac can process chay dai hon gioi han serverless, chuyen FastAPI sang Render/Railway/Fly container va giu Next tren Vercel.

Env de xuat:

```text
API_BASE_URL=
NEXT_PUBLIC_API_BASE_URL=
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
```
