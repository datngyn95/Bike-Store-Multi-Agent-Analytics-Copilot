# React/Next Frontend Deployment

Sprint 8 adds a standalone Next app in `frontend/` for the Bike Store demo.

## Local Run

Start FastAPI from the project root:

```powershell
python -m uvicorn api.app.main:app --host 127.0.0.1 --port 8000
```

Start the frontend:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

The Next app loads `.env` from the project root for local development, so the existing `Bike_Store_Project/.env` can provide auth and API settings.

Open:

```text
http://127.0.0.1:3000
```

## E2E Smoke Test

Sprint 9 adds Playwright checks for the authenticated demo flow:

```powershell
cd frontend
npm.cmd run test:e2e
```

The test command builds the frontend, starts a mock FastAPI server and serves the Next app on test ports. Use it before a live demo to verify login, dashboard KPI rendering, sales filtering and copilot evidence display.

## Required Environment

Set these values for local demo and Vercel:

```env
DASHBOARD_AUTH_ENABLED=true
DASHBOARD_DEMO_USER=
DASHBOARD_DEMO_PASSWORD=
AUTH_COOKIE_SECRET=
AUTH_COOKIE_SECURE=
API_BASE_URL=
NEXT_PUBLIC_API_BASE_URL=
```

`API_BASE_URL` is used by server-rendered Next pages. `NEXT_PUBLIC_API_BASE_URL` is kept for future browser-side calls, but the Sprint 8 UI reads FastAPI from the server so Supabase service credentials never enter the browser bundle.

For local `next start` over plain HTTP, set `AUTH_COOKIE_SECURE=false`. For Vercel or any HTTPS production deployment, set it to `true` or leave it unset so production defaults to secure cookies.

## Vercel

Use `frontend` as the Vercel Root Directory.

Recommended settings:

```text
Framework Preset: Next.js
Install Command: npm install
Build Command: npm run build
Output Directory: .next
```

For production, set `API_BASE_URL` and `NEXT_PUBLIC_API_BASE_URL` to the deployed FastAPI URL. If FastAPI is deployed separately on Render/Railway/Fly, update FastAPI CORS env:

```env
CLIENT_ORIGIN=https://<vercel-app>.vercel.app
CLIENT_ORIGINS=https://<vercel-app>.vercel.app
```

Do not put `SUPABASE_SERVICE_ROLE_KEY` in any `NEXT_PUBLIC_*` variable.
