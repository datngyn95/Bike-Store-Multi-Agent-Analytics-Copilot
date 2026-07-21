from agents.base_agent import BIKE_STORE_SYSTEM_PROMPT, BaseAgent
from agents.orchestrator import ORCHESTRATOR_SYSTEM_PROMPT, OrchestratorAgent


class FakeLLMClient:
    def __init__(self) -> None:
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
        return "Đây là câu trả lời tiếng Việt."


def test_base_agent_enforces_vietnamese_system_prompt():
    llm = FakeLLMClient()
    agent = BaseAgent(
        name="sales_agent",
        domain="sales",
        description="Theo dõi doanh thu Bike Store.",
        llm_client=llm,
        default_tables=["analytics.mart_sales_monthly"],
        default_metrics=["revenue"],
    )

    result = agent.answer("Revenue by month?")

    assert result["answer"] == "Đây là câu trả lời tiếng Việt."
    assert "Luôn trả lời bằng tiếng Việt" in llm.calls[0]["system_prompt"]
    assert "Giải thích KPI ngắn gọn" in llm.calls[0]["system_prompt"]
    assert "Bike Store" in llm.calls[0]["system_prompt"]


def test_orchestrator_inherits_bike_store_language_rule():
    llm = FakeLLMClient()
    orchestrator = OrchestratorAgent(llm_client=llm)

    result = orchestrator.answer("Cửa hàng nào có doanh thu cao nhất?")

    assert result["agents"] == ["orchestrator_agent"]
    assert "Luôn trả lời bằng tiếng Việt" in llm.calls[0]["system_prompt"]
    assert "Xác định lĩnh vực phù hợp" in llm.calls[0]["system_prompt"]
    assert ORCHESTRATOR_SYSTEM_PROMPT.startswith(BIKE_STORE_SYSTEM_PROMPT)
