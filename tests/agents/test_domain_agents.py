from __future__ import annotations

from agents.domain_agents import build_default_domain_agents
from agents.orchestrator import OrchestratorAgent


class FakeLLM:
    def __init__(self, answer: str = "Xin chao, minh co the ho tro phan tich Bike Store.") -> None:
        self.answer = answer
        self.calls = []

    def generate(self, prompt, *, system_prompt, temperature=0.2, max_output_tokens=1024):
        self.calls.append(
            {
                "prompt": prompt,
                "system_prompt": system_prompt,
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
            }
        )
        return self.answer


def test_default_domain_agents_cover_sprint6_scope():
    agents = build_default_domain_agents()

    assert set(agents) == {
        "sales",
        "customer",
        "product",
        "inventory",
        "store",
        "staff",
        "data_quality",
    }
    assert agents["sales"].name == "sales_agent"
    assert agents["inventory"].templates
    assert agents["data_quality"].templates


def test_orchestrator_plans_accented_store_question():
    orchestrator = OrchestratorAgent.with_default_agents()

    plan = orchestrator.plan("Cửa hàng nào có doanh thu cao nhất?")

    assert plan["template"] == "top_store"
    assert plan["agents"] == ["store_agent", "sales_agent"]
    assert plan["tables"] == ["analytics.mart_sales_by_store"]


def test_orchestrator_plans_product_brand_question():
    orchestrator = OrchestratorAgent.with_default_agents()

    plan = orchestrator.plan("Brand nào đóng góp doanh thu lớn nhất?")

    assert plan["template"] == "product_performance"
    assert plan["agents"] == ["product_agent"]
    assert plan["tables"] == ["analytics.mart_product_performance"]


def test_orchestrator_plans_metric_catalog_question():
    orchestrator = OrchestratorAgent.with_default_agents()

    plan = orchestrator.plan("Metric revenue được định nghĩa như thế nào?")

    assert plan["template"] == "metric_catalog"
    assert plan["agents"] == ["data_quality_agent", "orchestrator_agent"]
    assert plan["tables"] == ["agent.metric_catalog"]


def test_orchestrator_uses_llm_for_non_template_question_without_sql():
    llm = FakeLLM()
    orchestrator = OrchestratorAgent.with_default_agents(llm_client=llm)

    def execute(sql):
        raise AssertionError(f"Unexpected SQL execution: {sql}")

    result = orchestrator.ask("chao", query_executor=execute, row_limit=10)

    assert result["agents"] == ["orchestrator_agent"]
    assert result["answer"] == llm.answer
    assert result["sql"] == ""
    assert result["warnings"] == []
    assert llm.calls
    assert llm.calls[0]["max_output_tokens"] == 512


def test_orchestrator_uses_llm_to_explain_sql_template_result():
    llm = FakeLLM("Baldwin Bikes dang dan dau doanh thu, voi nguon tu mart cua hang.")
    orchestrator = OrchestratorAgent.with_default_agents(llm_client=llm)
    captured = {}

    def execute(sql):
        captured["sql"] = sql
        return [
            {
                "store_name": "Baldwin Bikes",
                "revenue": 5215751.28,
                "orders": 100,
            }
        ]

    result = orchestrator.ask(
        "Cua hang nao co doanh thu cao nhat?",
        query_executor=execute,
        row_limit=10,
    )

    assert result["agents"] == ["store_agent", "sales_agent"]
    assert result["answer"] == llm.answer
    assert "analytics.mart_sales_by_store" in captured["sql"]
    assert "Template: top_store" in llm.calls[0]["prompt"]
    assert "Baldwin Bikes" in llm.calls[0]["prompt"]
    assert "analytics.mart_sales_by_store" in llm.calls[0]["prompt"]
    assert llm.calls[0]["max_output_tokens"] == 768
    assert result["warnings"] == []


def test_orchestrator_runs_store_template_with_guarded_sql():
    orchestrator = OrchestratorAgent.with_default_agents()
    captured = {}

    def execute(sql):
        captured["sql"] = sql
        return [
            {
                "store_name": "Baldwin Bikes",
                "revenue": 5215751.28,
                "orders": 100,
            }
        ]

    result = orchestrator.ask(
        "Cua hang nao co doanh thu cao nhat?",
        query_executor=execute,
        row_limit=10,
    )

    assert result["agents"] == ["store_agent", "sales_agent"]
    assert "analytics.mart_sales_by_store" in captured["sql"]
    assert "Baldwin Bikes" in result["answer"]
    assert result["warnings"] == []


def test_data_quality_agent_uses_readonly_analytics_source():
    orchestrator = OrchestratorAgent.with_default_agents()

    result = orchestrator.ask(
        "Có lỗi dữ liệu nào trong order_items không?",
        query_executor=lambda sql: [
            {
                "rows_checked": 4722,
                "missing_required_fields": 0,
                "invalid_numeric_rows": 0,
                "negative_revenue_rows": 0,
            }
        ],
        row_limit=10,
    )

    assert result["agents"] == ["data_quality_agent"]
    assert result["tables"] == ["analytics.fact_sales"]
    assert "audit." not in result["sql"].lower()
    assert "Không thấy lỗi" in result["answer"]
