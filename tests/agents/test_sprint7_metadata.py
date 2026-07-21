from __future__ import annotations

from pathlib import Path

from agents.graph_rag import QUESTION_EXAMPLES, build_bike_store_graph, node_text
from agents.sql_guardrails import validate_readonly_sql
from agents.sql_templates import ALL_TEMPLATES


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_agent_sql_artifacts_define_pgvector_metadata_tables():
    ddl = (PROJECT_ROOT / "sql" / "agent" / "010_agent_metadata_tables.sql").read_text(encoding="utf-8").lower()
    seed = (PROJECT_ROOT / "sql" / "agent" / "020_seed_agent_metadata.sql").read_text(encoding="utf-8").lower()

    assert "create extension if not exists vector" in ddl
    assert "create table if not exists agent.rag_embeddings" in ddl
    assert "embedding vector(384)" in ddl
    assert "using hnsw" in ddl

    assert "agent.metric_catalog" in seed
    assert "agent.sql_templates" in seed
    assert "agent.question_examples" in seed
    assert seed.count("'q_") >= 20


def test_graph_contains_sprint7_metadata_template_and_question_nodes():
    graph, nodes = build_bike_store_graph()

    for table_name in [
        "agent.agent_registry",
        "agent.metric_catalog",
        "agent.sql_templates",
        "agent.question_examples",
        "agent.rag_embeddings",
    ]:
        assert graph.has_node(f"table:{table_name}")

    assert graph.has_node("template:sales_monthly")
    assert graph.has_node("template:inventory_risk")
    assert graph.has_node("question:q_store_top_revenue")
    assert graph.has_edge("table:agent.sql_templates", "template:top_store")
    assert graph.has_edge("question:q_store_top_revenue", "template:top_store")
    assert len([node for node in nodes if node.get("type") == "question_example"]) >= 20


def test_runtime_sql_templates_remain_readonly_and_allowlisted():
    for template in ALL_TEMPLATES:
        sql = template.sql_builder("Doanh thu nam 2017")
        guarded_sql = validate_readonly_sql(sql, row_limit=50)

        assert guarded_sql.lower().lstrip().startswith(("select", "with"))
        assert "limit" in guarded_sql.lower()


def test_question_examples_reference_existing_templates_and_agents():
    template_names = {template.name for template in ALL_TEMPLATES}
    graph, _ = build_bike_store_graph()

    for example in QUESTION_EXAMPLES:
        assert example["template"] in template_names
        assert graph.has_node(f"template:{example['template']}")
        for agent_name in example["agents"]:
            assert graph.has_node(f"agent:{agent_name}")


def test_graph_node_text_includes_question_template_and_metric_signals():
    question_node = {
        "type": "question_example",
        "name": "q_metric_revenue",
        "question": "Metric revenue duoc dinh nghia nhu the nao?",
        "template": "metric_catalog",
        "metrics": ["revenue"],
        "tables": ["agent.metric_catalog"],
        "agents": ["data_quality_agent", "orchestrator_agent"],
    }

    text = node_text(question_node)

    assert "Metric revenue" in text
    assert "metric_catalog" in text
    assert "agent.metric_catalog" in text
