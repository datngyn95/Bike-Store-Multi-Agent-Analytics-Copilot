# Portfolio Case Study

## Project Summary

Bike Store Multi-Agent Analytics Copilot is an end-to-end analytics project for retail bicycle sales. It demonstrates data engineering, cloud warehousing, API design, dashboard engineering and AI-assisted analytics in one coherent demo.

## Problem

Business users need fast answers about revenue, product performance, inventory risk, customers and store operations. Raw CSV files are not enough for reliable decision-making, and a generic chatbot is risky unless answers include governed SQL and metric evidence.

## Solution

The project turns headerless source CSVs into a Supabase PostgreSQL analytics warehouse, then exposes curated marts through FastAPI, Streamlit and React/Next. A Vietnamese orchestrator routes questions to domain agents and returns answers with SQL, metrics, tables, rows and warnings.

## Architecture

```text
CSV snapshot
  -> Supabase raw/staging
  -> analytics facts, dimensions and marts
  -> FastAPI metrics and copilot endpoints
  -> Streamlit dashboard + React/Next demo frontend
  -> multi-agent analytics copilot with SQL guardrails and RAG metadata
```

## Highlights

- Data quality checker logs `34/34` passing checks.
- Analytics marts reproduce the PRD revenue baseline `7,689,116.56`.
- FastAPI is separated from Streamlit runtime code.
- Copilot SQL is read-only and restricted to approved analytics/agent sources.
- React/Next frontend has demo auth and server-side API calls.
- Sprint 9 adds Playwright E2E checks with a mock API for repeatable demo validation.

## Demo Questions

- `Doanh thu theo thang nam 2017 nhu the nao?`
- `Cua hang nao co doanh thu cao nhat?`
- `San pham nao ban chay nhung ton kho thap?`
- `Khach hang o bang nao co revenue cao nhat?`
- `Co loi du lieu nao trong order_items khong?`

## Resume Bullets

- Built a cloud-first analytics warehouse on Supabase PostgreSQL from 9 headerless CSV files.
- Created staging, facts, dimensions, marts, data quality checks and metric catalog metadata.
- Implemented FastAPI metrics/copilot service with SQL guardrails and test coverage.
- Built a Vietnamese multi-agent analytics copilot with deterministic fallback behavior.
- Delivered Streamlit and React/Next dashboards with demo auth and Playwright E2E checks.
