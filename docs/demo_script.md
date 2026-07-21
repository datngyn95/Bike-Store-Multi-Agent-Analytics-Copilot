# Demo Script

## Setup

1. Start FastAPI from the project root:

   ```powershell
   python -m uvicorn api.app.main:app --host 127.0.0.1 --port 8000
   ```

2. Start the React/Next frontend:

   ```powershell
   cd frontend
   npm.cmd run dev
   ```

3. Open `http://127.0.0.1:3000` and log in with the demo credentials from `.env`.

## Walkthrough

1. Executive overview: show revenue `7,689,116.56`, `1,615` orders, late shipment rate and source pill `analytics.mart_executive_summary`.
2. Sales: filter year `2017`, show monthly trend, AOV and discount rate.
3. Products: highlight top product/category/brand and explain revenue after discount.
4. Inventory: filter `stockout_risk`, show product/store rows that need attention.
5. Customers: filter a state such as `NY`, explain segment distribution and customer revenue.
6. Copilot: ask `Cua hang nao co doanh thu cao nhat?`
7. Close by showing the copilot evidence block: routed agents, SQL, metrics, source tables and result rows.

## Backup Plan

If Supabase or the API is unavailable during a live demo, run the Sprint 9 E2E smoke test:

```powershell
cd frontend
npm.cmd run test:e2e
```

This builds the frontend, starts a mock FastAPI server and verifies the same auth, dashboard, sales filter and copilot evidence flow.
