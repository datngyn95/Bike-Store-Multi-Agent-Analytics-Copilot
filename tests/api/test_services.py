from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from api.app.services.copilot_service import CopilotService
from api.app.services.metrics_service import MetricsService
from api.app.services.sql_guardrails import SQLGuardrailError, validate_readonly_sql


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return self

    def all(self):
        return self._rows


class FakeSession:
    def __init__(self, rows):
        self.rows = rows
        self.sql = ""
        self.params = None

    def execute(self, statement, params=None):
        self.sql = str(statement)
        self.params = params or {}
        return FakeResult(self.rows)


def test_metrics_service_sales_summary_normalizes_values():
    session = FakeSession(
        [
            {
                "orders": 1615,
                "revenue": Decimal("7689116.56"),
                "first_order_date": date(2016, 1, 1),
            }
        ]
    )

    response = MetricsService(session).sales_summary()

    assert response.source == "analytics.mart_executive_summary"
    assert response.metrics["revenue"] == 7689116.56
    assert response.metrics["first_order_date"] == "2016-01-01"


def test_metrics_service_monthly_uses_year_filter_and_limit():
    session = FakeSession([{"year": 2017, "orders": 10, "revenue": Decimal("1000.00")}])

    response = MetricsService(session).sales_monthly(year=2017, limit=10)

    assert response.row_count == 1
    assert "analytics.mart_sales_monthly" in session.sql
    assert "where year = :year" in session.sql
    assert session.params == {"limit": 10, "year": 2017}


def test_copilot_service_routes_top_store_question_with_guarded_sql(monkeypatch):
    from api.app.services import copilot_service

    copilot_service._build_runtime_llm_client.cache_clear()
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("AI_PROVIDER", raising=False)

    session = FakeSession(
        [
            {
                "store_name": "Baldwin Bikes",
                "city": "Baldwin",
                "state": "NY",
                "orders": 100,
                "customers": 90,
                "revenue": Decimal("5215751.28"),
            }
        ]
    )

    response = CopilotService(session).ask("Cua hang nao co doanh thu cao nhat?")

    assert response.agents == ["store_agent", "sales_agent"]
    assert response.tables == ["analytics.mart_sales_by_store"]
    assert "analytics.mart_sales_by_store" in response.sql
    assert response.rows[0]["revenue"] == 5215751.28
    assert "Baldwin Bikes" in response.answer
    assert response.graph.nodes
    assert response.graph.edges
    assert any(node.id == "table:analytics.mart_sales_by_store" for node in response.graph.nodes)
    copilot_service._build_runtime_llm_client.cache_clear()


def test_copilot_service_wires_gemini_client_when_env_is_configured(monkeypatch):
    from api.app.services import copilot_service

    class FakeGeminiClient:
        pass

    copilot_service._build_runtime_llm_client.cache_clear()
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(copilot_service, "GeminiClient", FakeGeminiClient)

    service = copilot_service.CopilotService(FakeSession([]))

    assert isinstance(service.orchestrator.llm_client, FakeGeminiClient)
    copilot_service._build_runtime_llm_client.cache_clear()


def test_sql_guardrail_rejects_write_queries():
    with pytest.raises(SQLGuardrailError):
        validate_readonly_sql("drop table analytics.fact_sales", row_limit=100)


def test_sql_guardrail_rejects_non_allowlisted_tables():
    with pytest.raises(SQLGuardrailError):
        validate_readonly_sql("select * from raw.orders", row_limit=100)


def test_sql_guardrail_adds_default_limit_when_missing():
    sql = validate_readonly_sql("select * from analytics.mart_sales_monthly", row_limit=25)

    assert sql.endswith("limit 25")


def test_fastapi_layer_does_not_import_streamlit_dashboard_code():
    api_root = Path(__file__).resolve().parents[2] / "api" / "app"

    for path in api_root.rglob("*.py"):
        source = path.read_text(encoding="utf-8").lower()
        assert "streamlit" not in source
        assert "dashboard" not in source
