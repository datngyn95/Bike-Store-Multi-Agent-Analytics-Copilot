from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.app.main import app
from api.app.routes.copilot import get_copilot_service
from api.app.routes.metrics import get_metrics_service


@pytest.fixture()
def client():
    app.dependency_overrides.clear()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class FakeMetricsService:
    def sales_summary(self):
        return {
            "source": "analytics.mart_executive_summary",
            "metrics": {"orders": 1615, "revenue": 7689116.56},
            "warnings": [],
        }

    def sales_monthly(self, *, year=None, limit=100):
        return {
            "source": "analytics.mart_sales_monthly",
            "rows": [{"year": year or 2017, "orders": 10, "revenue": 1000.0}],
            "row_count": 1,
            "warnings": [],
        }

    def product_performance(self, *, limit=100):
        return {"source": "analytics.mart_product_performance", "rows": [], "row_count": 0, "warnings": []}

    def inventory_risk(self, *, status=None, limit=100):
        return {"source": "analytics.mart_inventory_risk", "rows": [], "row_count": 0, "warnings": []}

    def customer_segments(self, *, segment=None, state=None, limit=100):
        return {"source": "analytics.mart_customer_segments", "rows": [], "row_count": 0, "warnings": []}

    def staff_performance(self, *, limit=100):
        return {"source": "analytics.mart_staff_performance", "rows": [], "row_count": 0, "warnings": []}


class FakeCopilotService:
    def ask(self, question, *, limit=None):
        return {
            "answer": "Baldwin Bikes dang dan dau.",
            "agents": ["store_agent", "sales_agent"],
            "sql": "select * from analytics.mart_sales_by_store limit 10",
            "rows": [{"store_name": "Baldwin Bikes", "revenue": 5215751.28}],
            "metrics": ["store_revenue"],
            "tables": ["analytics.mart_sales_by_store"],
            "warnings": [],
            "latency_ms": 1,
        }


def test_health_endpoint_does_not_require_database(client):
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "bike-store-api"
    assert "database_url_configured" in payload


def test_sales_summary_endpoint_uses_service_dependency(client):
    app.dependency_overrides[get_metrics_service] = lambda: FakeMetricsService()

    response = client.get("/metrics/sales/summary")

    assert response.status_code == 200
    assert response.json()["metrics"]["orders"] == 1615


def test_sales_monthly_endpoint_accepts_year_filter(client):
    app.dependency_overrides[get_metrics_service] = lambda: FakeMetricsService()

    response = client.get("/metrics/sales/monthly?year=2017&limit=10")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "analytics.mart_sales_monthly"
    assert payload["rows"][0]["year"] == 2017


def test_copilot_endpoint_returns_prd_contract(client):
    app.dependency_overrides[get_copilot_service] = lambda: FakeCopilotService()

    response = client.post("/copilot/ask", json={"question": "Cua hang nao co doanh thu cao nhat?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["agents"] == ["store_agent", "sales_agent"]
    assert payload["tables"] == ["analytics.mart_sales_by_store"]
    assert payload["graph"] == {"nodes": [], "edges": []}
    assert payload["latency_ms"] >= 0
