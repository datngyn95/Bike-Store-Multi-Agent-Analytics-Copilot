# Bike Store Multi-Agent Analytics Copilot

Cloud-first analytics demo for the Bike Store dataset. The project loads CSV snapshots into Supabase PostgreSQL, builds staging/analytics marts, exposes metrics through FastAPI, and serves both a Streamlit dashboard and a React/Next demo frontend with a Vietnamese multi-agent copilot.

## What Is Included

- Supabase schemas: `raw`, `staging`, `analytics`, `agent`, `audit`.
- Reproducible CSV loader, SQL model runner, data quality checker and RAG index builder.
- Analytics marts for sales, products, inventory, customers, stores, staff and executive summary.
- FastAPI endpoints for dashboard metrics and `/copilot/ask`.
- Multi-agent routing for Sales, Customer, Product, Inventory, Store, Staff and Data Quality questions.
- Streamlit local dashboard plus authenticated React/Next frontend.
- Sprint 9 E2E demo checks with Playwright and a mock FastAPI server.

## Quick Start

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Fill `.env` with Supabase and demo auth values. Do not put service-role credentials in frontend `NEXT_PUBLIC_*` variables.
For local `next start` over HTTP, keep `AUTH_COOKIE_SECURE=false`; use `true` or leave production defaults for HTTPS deployments.

Run the API:

```powershell
python -m uvicorn api.app.main:app --host 127.0.0.1 --port 8000
```

Run the React/Next frontend:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Open `http://127.0.0.1:3000`.

## Verification

```powershell
pytest
cd frontend
npm.cmd run typecheck
npm.cmd run build
npm.cmd run test:e2e
```

The Playwright suite builds the frontend, starts a mock FastAPI server and serves the Next app on test ports, so it can validate the demo flow without requiring live Supabase access.

## Demo Flow

Use [docs/demo_script.md](docs/demo_script.md) for the final walkthrough and [docs/portfolio_case_study.md](docs/portfolio_case_study.md) for portfolio framing.

Current MVP baseline:

- Revenue after discount: `7,689,116.56`
- Orders: `1,615`
- Order items: `4,722`
- Data quality: `34/34` checks passing
- Top store: `Baldwin Bikes`
