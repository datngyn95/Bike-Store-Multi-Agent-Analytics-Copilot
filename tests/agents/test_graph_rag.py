from agents.graph_rag import (
    GRAPH_RAG_SYSTEM_PROMPT,
    BikeStoreGraphRAG,
    ask_gemini_graph_rag,
    build_bike_store_graph,
)


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
        return "Trả lời bằng tiếng Việt dựa trên Graph RAG."


def test_graph_contains_required_domain_agents():
    graph, nodes = build_bike_store_graph()

    for agent_name in [
        "sales_agent",
        "customer_agent",
        "product_agent",
        "inventory_agent",
        "store_agent",
        "staff_agent",
        "data_quality_agent",
    ]:
        assert graph.has_node(f"agent:{agent_name}")

    assert graph.has_edge("agent:orchestrator_agent", "agent:sales_agent")
    assert graph.has_node("table:analytics.mart_sales_monthly")
    assert graph.has_node("metric:revenue")
    assert len(nodes) == graph.number_of_nodes()


def test_graph_rag_system_prompt_keeps_vietnamese_rule():
    assert "Luôn trả lời bằng tiếng Việt" in GRAPH_RAG_SYSTEM_PROMPT
    assert "Graph RAG" in GRAPH_RAG_SYSTEM_PROMPT
    assert "Bike Store" in GRAPH_RAG_SYSTEM_PROMPT


def test_ask_gemini_graph_rag_passes_system_prompt_to_llm():
    llm = FakeLLMClient()

    answer = ask_gemini_graph_rag(
        "Doanh thu theo tháng nằm ở mart nào?",
        "[VIEW] analytics.mart_sales_monthly",
        llm_client=llm,
    )

    assert answer == "Trả lời bằng tiếng Việt dựa trên Graph RAG."
    assert "Luôn trả lời bằng tiếng Việt" in llm.calls[0]["system_prompt"]
    assert "analytics.mart_sales_monthly" in llm.calls[0]["prompt"]


def test_graph_rag_retrieves_context_without_embeddings():
    rag = BikeStoreGraphRAG.from_project(build_embeddings=False, llm_client=FakeLLMClient())

    context, results, relevant_node_ids = rag.retrieve("doanh thu revenue sales", top_k=5)

    assert results
    assert relevant_node_ids
    assert "revenue" in context.lower() or "sales" in context.lower()
