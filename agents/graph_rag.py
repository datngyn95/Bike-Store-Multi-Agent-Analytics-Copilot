from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import faiss
import networkx as nx
import numpy as np
from fastembed import TextEmbedding
from networkx.readwrite import json_graph

from .base_agent import BIKE_STORE_SYSTEM_PROMPT, GeminiClient, LLMClient
from .sql_templates import ALL_TEMPLATES


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAPH_DATA_DIR = PROJECT_ROOT / "graph_data"
DEFAULT_EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)
DEFAULT_EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))
DEFAULT_TOP_K = 8


GRAPH_RAG_SYSTEM_PROMPT = f"""
{BIKE_STORE_SYSTEM_PROMPT}

Quy tắc Graph RAG bổ sung:
- Sử dụng graph context làm nguồn tri thức chính về schema, metric, mart và domain agent.
- Khi trả lời, nêu rõ node/source liên quan như agent, metric, bảng hoặc mart nếu có.
- Nếu graph context không chứa thông tin cần thiết, nói rõ là chưa đủ thông tin trong graph.
- Không bịa metric, quan hệ bảng hoặc agent chưa tồn tại trong graph.
- Ưu tiên câu trả lời ngắn, có cấu trúc, phù hợp người dùng phân tích dữ liệu Bike Store.
""".strip()


DOMAIN_AGENTS: dict[str, dict[str, Any]] = {
    "sales_agent": {
        "domain": "sales",
        "description": "Phân tích doanh thu, đơn hàng, số lượng bán, AOV, discount và xu hướng bán hàng.",
        "metrics": ["revenue", "orders", "units_sold", "average_order_value", "discount_rate", "sales_growth"],
        "tables": ["analytics.fact_sales", "analytics.mart_sales_monthly", "analytics.mart_sales_by_store"],
    },
    "customer_agent": {
        "domain": "customer",
        "description": "Phân tích khách hàng theo state/city, top customers, doanh thu và tần suất mua.",
        "metrics": ["customer_count", "orders_per_customer", "revenue_per_customer", "state_revenue", "top_customers"],
        "tables": ["analytics.dim_customer", "analytics.mart_customer_segments", "analytics.fact_sales"],
    },
    "product_agent": {
        "domain": "product",
        "description": "Phân tích hiệu suất sản phẩm, brand, category, model year, giá bán và discount.",
        "metrics": ["product_revenue", "units_sold", "category_revenue", "brand_revenue", "avg_selling_price"],
        "tables": ["analytics.dim_product", "analytics.mart_product_performance", "analytics.fact_sales"],
    },
    "inventory_agent": {
        "domain": "inventory",
        "description": "Phân tích tồn kho, sales velocity, stockout risk, overstock risk và inventory value.",
        "metrics": ["stock_quantity", "sales_velocity", "stockout_risk", "overstock_risk", "inventory_value"],
        "tables": ["analytics.fact_inventory", "analytics.mart_inventory_risk"],
    },
    "store_agent": {
        "domain": "store",
        "description": "Phân tích doanh thu cửa hàng, đơn hàng, AOV, giao trễ và sức khỏe tồn kho.",
        "metrics": ["store_revenue", "store_orders", "store_aov", "late_shipment_rate", "store_inventory_health"],
        "tables": ["analytics.dim_store", "analytics.mart_sales_by_store", "analytics.mart_delivery_performance"],
    },
    "staff_agent": {
        "domain": "staff",
        "description": "Phân tích hiệu suất nhân viên, số đơn, doanh thu, AOV và manager/store performance.",
        "metrics": ["orders_by_staff", "revenue_by_staff", "avg_order_value_by_staff", "manager_performance"],
        "tables": ["analytics.dim_staff", "analytics.mart_staff_performance", "analytics.fact_sales"],
    },
    "data_quality_agent": {
        "domain": "data_quality",
        "description": "Giải thích data quality checks, null, duplicate key, FK integrity, invalid dates và orphan records.",
        "metrics": ["dq_pass_rate", "failed_checks", "issue_count"],
        "tables": ["audit.data_quality_check_results", "reports.data_quality_report", "staging.*", "analytics.*"],
    },
}


METRICS: dict[str, dict[str, str]] = {
    "revenue": {
        "description": "Doanh thu sau discount.",
        "formula": "quantity * list_price * (1 - discount)",
        "source": "analytics.fact_sales",
    },
    "orders": {
        "description": "Số đơn hàng distinct.",
        "formula": "count(distinct order_id)",
        "source": "analytics.fact_sales",
    },
    "units_sold": {
        "description": "Tổng số lượng sản phẩm bán ra.",
        "formula": "sum(quantity)",
        "source": "analytics.fact_sales",
    },
    "average_order_value": {
        "description": "Giá trị đơn hàng trung bình.",
        "formula": "sum(revenue) / count(distinct order_id)",
        "source": "analytics.fact_sales",
    },
    "discount_rate": {
        "description": "Tỷ lệ discount theo gross sales.",
        "formula": "sum(discount_amount) / sum(gross_sales)",
        "source": "analytics.fact_sales",
    },
    "late_shipment_rate": {
        "description": "Tỷ lệ giao trễ trên đơn đã ship.",
        "formula": "avg(is_late_shipment)",
        "source": "analytics.fact_sales",
    },
    "stock_quantity": {
        "description": "Số lượng tồn kho theo store/product.",
        "formula": "sum(stock_quantity)",
        "source": "analytics.fact_inventory",
    },
    "inventory_value": {
        "description": "Giá trị tồn kho proxy.",
        "formula": "stock_quantity * list_price",
        "source": "analytics.fact_inventory",
    },
    "sales_velocity": {
        "description": "Tốc độ bán gần đây dùng cho inventory risk.",
        "formula": "units_sold_90d / 90",
        "source": "analytics.mart_inventory_risk",
    },
    "stockout_risk": {
        "description": "Rủi ro hết hàng khi stock thấp so với sales velocity.",
        "formula": "inventory_status in ('stockout', 'stockout_risk')",
        "source": "analytics.mart_inventory_risk",
    },
}


VIEW_DESCRIPTIONS: dict[str, str] = {
    "analytics.fact_sales": "Fact bán hàng ở cấp order item, chứa revenue, discount, shipment flags và keys tới customer/store/staff/product.",
    "analytics.fact_inventory": "Fact tồn kho theo store và product, có stock_quantity và inventory_value.",
    "analytics.mart_sales_monthly": "Mart xu hướng doanh thu theo tháng cho dashboard Sales/Executive.",
    "analytics.mart_sales_by_store": "Mart so sánh doanh thu, orders, AOV và late shipment theo cửa hàng.",
    "analytics.mart_product_performance": "Mart hiệu suất sản phẩm, brand, category, units sold, revenue và discount.",
    "analytics.mart_inventory_risk": "Mart rủi ro tồn kho với sales velocity, days of supply và inventory_status.",
    "analytics.mart_customer_segments": "Mart phân khúc khách hàng theo revenue, orders và hành vi mua.",
    "analytics.mart_staff_performance": "Mart hiệu suất nhân viên theo orders, revenue, AOV và manager/store.",
    "analytics.mart_delivery_performance": "Mart hiệu suất giao hàng theo tháng và cửa hàng.",
    "analytics.mart_executive_summary": "Một dòng KPI tổng quan cho Executive dashboard.",
}


METRICS.update(
    {
        "gross_sales": {
            "description": "Revenue before discount.",
            "formula": "quantity * list_price",
            "source": "analytics.fact_sales",
        },
        "discount_amount": {
            "description": "Absolute discount amount.",
            "formula": "quantity * list_price * discount",
            "source": "analytics.fact_sales",
        },
        "order_items": {
            "description": "Line item count.",
            "formula": "count(*)",
            "source": "analytics.fact_sales",
        },
        "sales_growth": {
            "description": "Period-over-period revenue growth.",
            "formula": "(current_period_revenue - prior_period_revenue) / prior_period_revenue",
            "source": "analytics.mart_sales_monthly",
        },
        "customer_count": {
            "description": "Customer count in a segment or geography.",
            "formula": "count(distinct customer_id)",
            "source": "analytics.mart_customer_segments",
        },
        "orders_per_customer": {
            "description": "Average order frequency per customer.",
            "formula": "sum(orders) / count(distinct customer_id)",
            "source": "analytics.mart_customer_segments",
        },
        "revenue_per_customer": {
            "description": "Average revenue per customer.",
            "formula": "sum(revenue) / count(distinct customer_id)",
            "source": "analytics.mart_customer_segments",
        },
        "state_revenue": {
            "description": "Revenue grouped by customer state.",
            "formula": "sum(revenue) grouped by state",
            "source": "analytics.mart_customer_segments",
        },
        "top_customers": {
            "description": "Highest value customers by revenue and orders.",
            "formula": "order customers by revenue desc, orders desc",
            "source": "analytics.mart_customer_segments",
        },
        "product_revenue": {
            "description": "Revenue by product.",
            "formula": "sum(revenue) grouped by product_id",
            "source": "analytics.mart_product_performance",
        },
        "category_revenue": {
            "description": "Revenue by product category.",
            "formula": "sum(revenue) grouped by category_name",
            "source": "analytics.mart_product_performance",
        },
        "brand_revenue": {
            "description": "Revenue by brand.",
            "formula": "sum(revenue) grouped by brand_name",
            "source": "analytics.mart_product_performance",
        },
        "avg_selling_price": {
            "description": "Average selling price after discount.",
            "formula": "sum(revenue) / sum(quantity)",
            "source": "analytics.mart_product_performance",
        },
        "discount_by_product": {
            "description": "Discount rate by product, brand or category.",
            "formula": "sum(discount_amount) / sum(gross_sales)",
            "source": "analytics.mart_product_performance",
        },
        "overstock_risk": {
            "description": "Excess inventory or inventory with no recent sales.",
            "formula": "inventory_status = 'overstock_risk'",
            "source": "analytics.mart_inventory_risk",
        },
        "store_revenue": {
            "description": "Revenue grouped by store.",
            "formula": "sum(revenue) grouped by store_id",
            "source": "analytics.mart_sales_by_store",
        },
        "store_orders": {
            "description": "Distinct orders grouped by store.",
            "formula": "count(distinct order_id) grouped by store_id",
            "source": "analytics.mart_sales_by_store",
        },
        "store_aov": {
            "description": "Average order value by store.",
            "formula": "sum(revenue) / count(distinct order_id)",
            "source": "analytics.mart_sales_by_store",
        },
        "store_inventory_health": {
            "description": "Inventory health summary by store.",
            "formula": "count products by inventory_status grouped by store",
            "source": "analytics.mart_inventory_risk",
        },
        "orders_by_staff": {
            "description": "Distinct orders handled by staff.",
            "formula": "count(distinct order_id) grouped by staff_id",
            "source": "analytics.mart_staff_performance",
        },
        "revenue_by_staff": {
            "description": "Revenue handled by staff.",
            "formula": "sum(revenue) grouped by staff_id",
            "source": "analytics.mart_staff_performance",
        },
        "avg_order_value_by_staff": {
            "description": "Average order value by staff.",
            "formula": "sum(revenue) / count(distinct order_id)",
            "source": "analytics.mart_staff_performance",
        },
        "manager_performance": {
            "description": "Staff performance grouped by manager.",
            "formula": "aggregate staff orders and revenue by manager_id",
            "source": "analytics.mart_staff_performance",
        },
        "dq_pass_rate": {
            "description": "Share of data quality checks passing.",
            "formula": "passed_checks / total_checks",
            "source": "audit.data_quality_check_results",
        },
        "failed_checks": {
            "description": "Count of failed data quality checks.",
            "formula": "count(*) where status = 'fail'",
            "source": "audit.data_quality_check_results",
        },
        "issue_count": {
            "description": "Total issue count from data quality checks.",
            "formula": "sum(issue_count)",
            "source": "audit.data_quality_check_results",
        },
        "missing_required_fields": {
            "description": "Rows with required fact_sales fields missing.",
            "formula": "count rows where required fields are null",
            "source": "analytics.fact_sales",
        },
        "invalid_numeric_rows": {
            "description": "Rows with invalid quantity, price or discount values.",
            "formula": "count rows where numeric rules fail",
            "source": "analytics.fact_sales",
        },
        "negative_revenue_rows": {
            "description": "Rows with negative revenue.",
            "formula": "count rows where revenue < 0",
            "source": "analytics.fact_sales",
        },
    }
)

VIEW_DESCRIPTIONS.update(
    {
        "analytics.fact_sales": "Order-item sales fact with revenue, discount, shipment flags and customer/store/staff/product keys.",
        "analytics.fact_inventory": "Store-product inventory fact with stock quantity and inventory value proxy.",
        "analytics.mart_sales_monthly": "Monthly revenue trend mart for Sales and Executive dashboards.",
        "analytics.mart_sales_by_store": "Store comparison mart with revenue, orders, AOV and late shipment rate.",
        "analytics.mart_product_performance": "Product performance mart by product, brand and category.",
        "analytics.mart_inventory_risk": "Inventory risk mart with sales velocity, days of supply and inventory status.",
        "analytics.mart_customer_segments": "Customer segmentation mart by revenue, orders and buying behavior.",
        "analytics.mart_staff_performance": "Staff performance mart by orders, revenue, AOV and manager/store.",
        "analytics.mart_delivery_performance": "Delivery performance mart by month and store.",
        "analytics.mart_executive_summary": "Single-row KPI overview for the Executive dashboard.",
    }
)

AGENT_METADATA_TABLES: tuple[dict[str, Any], ...] = (
    {
        "name": "agent.agent_registry",
        "description": "Registry of orchestrator and domain agents, their domains, default metrics and table scope.",
        "source": "sql/agent/010_agent_metadata_tables.sql",
    },
    {
        "name": "agent.metric_catalog",
        "description": "Seeded metric definitions, formulas, grain, source tables, caveats and owner agents.",
        "source": "sql/agent/020_seed_agent_metadata.sql",
    },
    {
        "name": "agent.sql_templates",
        "description": "Read-only SQL template catalog for deterministic copilot answers and guardrail-friendly query generation.",
        "source": "sql/agent/020_seed_agent_metadata.sql",
    },
    {
        "name": "agent.question_examples",
        "description": "Vietnamese evaluation and demo questions with expected agents, templates, metrics and source tables.",
        "source": "sql/agent/020_seed_agent_metadata.sql",
    },
    {
        "name": "agent.rag_embeddings",
        "description": "pgvector-backed embedding store for graph nodes used by the Bike Store RAG layer.",
        "source": "sql/agent/010_agent_metadata_tables.sql",
    },
)

QUESTION_EXAMPLES: tuple[dict[str, Any], ...] = (
    {
        "id": "q_sales_monthly_2017",
        "domain": "sales",
        "question": "Doanh thu theo thang nam 2017 nhu the nao?",
        "agents": ["sales_agent"],
        "template": "sales_monthly",
        "metrics": ["revenue", "orders"],
        "tables": ["analytics.mart_sales_monthly"],
    },
    {
        "id": "q_sales_summary",
        "domain": "sales",
        "question": "Tong revenue, orders va AOV cua Bike Store la bao nhieu?",
        "agents": ["sales_agent"],
        "template": "sales_summary",
        "metrics": ["revenue", "orders", "average_order_value"],
        "tables": ["analytics.mart_executive_summary"],
    },
    {
        "id": "q_store_top_revenue",
        "domain": "store",
        "question": "Cua hang nao co doanh thu cao nhat?",
        "agents": ["store_agent", "sales_agent"],
        "template": "top_store",
        "metrics": ["store_revenue"],
        "tables": ["analytics.mart_sales_by_store"],
    },
    {
        "id": "q_delivery_late_store",
        "domain": "store",
        "question": "Cua hang nao co ty le giao tre cao nhat?",
        "agents": ["store_agent"],
        "template": "delivery_late",
        "metrics": ["late_shipment_rate"],
        "tables": ["analytics.mart_delivery_performance"],
    },
    {
        "id": "q_product_top_revenue",
        "domain": "product",
        "question": "San pham nao co revenue cao nhat?",
        "agents": ["product_agent"],
        "template": "product_performance",
        "metrics": ["product_revenue"],
        "tables": ["analytics.mart_product_performance"],
    },
    {
        "id": "q_brand_revenue",
        "domain": "product",
        "question": "Brand nao dong gop doanh thu lon nhat?",
        "agents": ["product_agent"],
        "template": "product_performance",
        "metrics": ["brand_revenue"],
        "tables": ["analytics.mart_product_performance"],
    },
    {
        "id": "q_inventory_stockout",
        "domain": "inventory",
        "question": "San pham nao ban chay nhung ton kho thap?",
        "agents": ["inventory_agent", "product_agent"],
        "template": "inventory_risk",
        "metrics": ["stockout_risk", "sales_velocity"],
        "tables": ["analytics.mart_inventory_risk"],
    },
    {
        "id": "q_inventory_overstock",
        "domain": "inventory",
        "question": "Mat hang nao co rui ro overstock?",
        "agents": ["inventory_agent", "product_agent"],
        "template": "inventory_risk",
        "metrics": ["overstock_risk"],
        "tables": ["analytics.mart_inventory_risk"],
    },
    {
        "id": "q_customer_state_revenue",
        "domain": "customer",
        "question": "Bang nao co revenue khach hang cao nhat?",
        "agents": ["customer_agent"],
        "template": "customer_state",
        "metrics": ["state_revenue"],
        "tables": ["analytics.mart_customer_segments"],
    },
    {
        "id": "q_customer_top",
        "domain": "customer",
        "question": "Khach hang VIP hoac top customers la ai?",
        "agents": ["customer_agent"],
        "template": "customer_state",
        "metrics": ["top_customers"],
        "tables": ["analytics.mart_customer_segments"],
    },
    {
        "id": "q_staff_revenue",
        "domain": "staff",
        "question": "Nhan vien nao tao revenue cao nhat?",
        "agents": ["staff_agent"],
        "template": "staff_revenue",
        "metrics": ["revenue_by_staff"],
        "tables": ["analytics.mart_staff_performance"],
    },
    {
        "id": "q_staff_orders",
        "domain": "staff",
        "question": "Nhan vien nao xu ly nhieu don nhat?",
        "agents": ["staff_agent"],
        "template": "staff_revenue",
        "metrics": ["orders_by_staff"],
        "tables": ["analytics.mart_staff_performance"],
    },
    {
        "id": "q_dq_order_items",
        "domain": "data_quality",
        "question": "Co loi du lieu nao trong order_items khong?",
        "agents": ["data_quality_agent"],
        "template": "data_quality_fact_sales",
        "metrics": ["missing_required_fields", "invalid_numeric_rows"],
        "tables": ["analytics.fact_sales"],
    },
    {
        "id": "q_metric_revenue",
        "domain": "data_quality",
        "question": "Metric revenue duoc dinh nghia nhu the nao?",
        "agents": ["data_quality_agent", "orchestrator_agent"],
        "template": "metric_catalog",
        "metrics": ["revenue"],
        "tables": ["agent.metric_catalog"],
    },
    {
        "id": "q_sales_discount",
        "domain": "sales",
        "question": "Ty le discount toan bo dataset la bao nhieu?",
        "agents": ["sales_agent"],
        "template": "sales_summary",
        "metrics": ["discount_rate"],
        "tables": ["analytics.mart_executive_summary"],
    },
    {
        "id": "q_store_aov",
        "domain": "store",
        "question": "Cua hang nao co AOV cao nhat?",
        "agents": ["store_agent", "sales_agent"],
        "template": "top_store",
        "metrics": ["store_aov"],
        "tables": ["analytics.mart_sales_by_store"],
    },
    {
        "id": "q_category_units",
        "domain": "product",
        "question": "Category nao ban chay nhat theo units sold?",
        "agents": ["product_agent"],
        "template": "product_performance",
        "metrics": ["category_revenue", "units_sold"],
        "tables": ["analytics.mart_product_performance"],
    },
    {
        "id": "q_product_discount",
        "domain": "product",
        "question": "San pham nao co discount rate cao nhat?",
        "agents": ["product_agent"],
        "template": "product_performance",
        "metrics": ["discount_by_product"],
        "tables": ["analytics.mart_product_performance"],
    },
    {
        "id": "q_inventory_value",
        "domain": "inventory",
        "question": "Gia tri ton kho proxy duoc tinh tu bang nao?",
        "agents": ["inventory_agent"],
        "template": "metric_catalog",
        "metrics": ["inventory_value"],
        "tables": ["agent.metric_catalog"],
    },
    {
        "id": "q_customer_frequency",
        "domain": "customer",
        "question": "Tan suat mua trung binh cua khach hang duoc tinh nhu the nao?",
        "agents": ["customer_agent"],
        "template": "metric_catalog",
        "metrics": ["orders_per_customer"],
        "tables": ["agent.metric_catalog"],
    },
    {
        "id": "q_staff_manager",
        "domain": "staff",
        "question": "Manager nao co team performance tot nhat?",
        "agents": ["staff_agent"],
        "template": "staff_revenue",
        "metrics": ["manager_performance"],
        "tables": ["analytics.mart_staff_performance"],
    },
    {
        "id": "q_metric_late_shipment",
        "domain": "data_quality",
        "question": "Metric late_shipment_rate lay tu bang nao?",
        "agents": ["data_quality_agent", "orchestrator_agent"],
        "template": "metric_catalog",
        "metrics": ["late_shipment_rate"],
        "tables": ["agent.metric_catalog"],
    },
    {
        "id": "q_schema_monthly_sales",
        "domain": "data_quality",
        "question": "Bang nao phu hop de ve monthly sales trend?",
        "agents": ["data_quality_agent", "orchestrator_agent"],
        "template": "metric_catalog",
        "metrics": ["revenue", "orders"],
        "tables": ["agent.metric_catalog", "analytics.mart_sales_monthly"],
    },
    {
        "id": "q_agent_scope",
        "domain": "data_quality",
        "question": "Copilot ho tro nhung domain agent nao?",
        "agents": ["data_quality_agent", "orchestrator_agent"],
        "template": "metric_catalog",
        "metrics": ["metric_catalog"],
        "tables": ["agent.agent_registry"],
    },
)


@dataclass(frozen=True)
class GraphRAGResult:
    answer: str
    graph_context: str
    node_ids: list[str]
    sources: list[dict[str, Any]]


def node_text(node: dict[str, Any]) -> str:
    parts = [
        str(node.get("type", "")),
        str(node.get("name", "")),
        str(node.get("description", "")),
        str(node.get("source", "")),
        str(node.get("domain", "")),
        str(node.get("formula", "")),
        str(node.get("question", "")),
        str(node.get("template", "")),
        str(node.get("sql_template", "")),
        " ".join(node.get("metrics", []) or []),
        " ".join(node.get("tables", []) or []),
        " ".join(node.get("agents", []) or []),
    ]
    return " - ".join(part for part in parts if part)


def add_node(graph: nx.DiGraph, nodes: list[dict[str, Any]], node_id: str, **attrs: Any) -> None:
    data = {"id": node_id, **attrs}
    if not graph.has_node(node_id):
        graph.add_node(node_id, **data)
        nodes.append(data)
    else:
        graph.nodes[node_id].update(data)
        for index, node in enumerate(nodes):
            if node["id"] == node_id:
                nodes[index] = {**node, **data}
                break


def add_edge(graph: nx.DiGraph, source: str, target: str, edge_type: str) -> None:
    if graph.has_node(source) and graph.has_node(target):
        graph.add_edge(source, target, type=edge_type)


def ensure_table_node(
    graph: nx.DiGraph,
    nodes: list[dict[str, Any]],
    table_name: str,
    *,
    description: str | None = None,
    source: str = "agent metadata",
    node_type: str = "table",
) -> str:
    table_id = f"table:{table_name}"
    if not graph.has_node(table_id):
        add_node(
            graph,
            nodes,
            table_id,
            type=node_type,
            name=table_name,
            description=description or f"Table or view {table_name}.",
            source=source,
        )
        schema_name = table_name.split(".", 1)[0]
        add_edge(graph, f"schema:{schema_name}", table_id, "contains")
    return table_id


def parse_sql_views(sql_dir: Path) -> list[dict[str, Any]]:
    sql_views: list[dict[str, Any]] = []
    view_pattern = re.compile(
        r"create\s+or\s+replace\s+view\s+((?:raw|staging|analytics|agent|audit)\.[a-zA-Z_][a-zA-Z0-9_]*)\s+as",
        re.IGNORECASE,
    )
    relation_pattern = re.compile(r"\b(raw|staging|analytics|agent|audit)\.([a-zA-Z_][a-zA-Z0-9_]*)\b")

    for sql_file in sorted(sql_dir.rglob("*.sql")):
        sql = sql_file.read_text(encoding="utf-8")
        matches = list(view_pattern.finditer(sql))
        for index, match in enumerate(matches):
            view_name = match.group(1).lower()
            start = match.start()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(sql)
            statement = sql[start:end]
            dependencies = sorted(
                {
                    f"{schema.lower()}.{table.lower()}"
                    for schema, table in relation_pattern.findall(statement)
                    if f"{schema.lower()}.{table.lower()}" != view_name
                }
            )
            sql_views.append(
                {
                    "view_name": view_name,
                    "schema": view_name.split(".", 1)[0],
                    "file": str(sql_file.relative_to(PROJECT_ROOT)),
                    "description": VIEW_DESCRIPTIONS.get(view_name, f"SQL view {view_name}"),
                    "dependencies": dependencies,
                    "code_snippet": statement.strip()[:1200],
                }
            )

    return sql_views


def build_bike_store_graph(project_root: Path = PROJECT_ROOT) -> tuple[nx.DiGraph, list[dict[str, Any]]]:
    graph = nx.DiGraph()
    nodes: list[dict[str, Any]] = []

    add_node(
        graph,
        nodes,
        "project:bike_store",
        type="project",
        name="Bike Store Multi-Agent Analytics Copilot",
        description="Cloud-first analytics project: CSV -> Supabase -> analytics marts -> dashboard/API -> multi-agent Vietnamese copilot.",
        source="PRD.md",
    )

    for schema in ["raw", "staging", "analytics", "agent", "audit"]:
        schema_id = f"schema:{schema}"
        add_node(
            graph,
            nodes,
            schema_id,
            type="schema",
            name=schema,
            description=f"Supabase PostgreSQL schema `{schema}` trong kiến trúc Bike Store.",
            source="PRD.md",
        )
        add_edge(graph, "project:bike_store", schema_id, "has_schema")

    for metadata_table in AGENT_METADATA_TABLES:
        table_id = ensure_table_node(
            graph,
            nodes,
            metadata_table["name"],
            description=metadata_table["description"],
            source=metadata_table["source"],
            node_type="metadata_table",
        )
        add_edge(graph, "project:bike_store", table_id, "has_metadata_table")

    for sql_view in parse_sql_views(project_root / "sql"):
        view_name = sql_view["view_name"]
        view_id = f"table:{view_name}"
        add_node(
            graph,
            nodes,
            view_id,
            type="view",
            name=view_name,
            description=sql_view["description"],
            source=sql_view["file"],
            code_snippet=sql_view["code_snippet"],
        )
        add_edge(graph, f"schema:{sql_view['schema']}", view_id, "contains")

        for dependency in sql_view["dependencies"]:
            dependency_id = f"table:{dependency}"
            if not graph.has_node(dependency_id):
                add_node(
                    graph,
                    nodes,
                    dependency_id,
                    type="table",
                    name=dependency,
                    description=f"Referenced relation {dependency}.",
                    source="sql dependency",
                )
                add_edge(graph, f"schema:{dependency.split('.', 1)[0]}", dependency_id, "contains")
            add_edge(graph, view_id, dependency_id, "depends_on")

    add_node(
        graph,
        nodes,
        "agent:orchestrator_agent",
        type="agent",
        name="orchestrator_agent",
        description="Điều phối câu hỏi tiếng Việt tới đúng domain agent và tổng hợp câu trả lời.",
        source="agents/orchestrator.py",
        tables=["analytics.*", "agent.*"],
        metrics=list(METRICS.keys()),
    )
    add_edge(graph, "project:bike_store", "agent:orchestrator_agent", "has_agent")

    for agent_name, agent_data in DOMAIN_AGENTS.items():
        agent_id = f"agent:{agent_name}"
        add_node(
            graph,
            nodes,
            agent_id,
            type="agent",
            name=agent_name,
            description=agent_data["description"],
            source="PRD.md section 9",
            domain=agent_data["domain"],
            metrics=agent_data["metrics"],
            tables=agent_data["tables"],
        )
        add_edge(graph, "agent:orchestrator_agent", agent_id, "routes_to")

        for table_name in agent_data["tables"]:
            table_id = f"table:{table_name}"
            if not graph.has_node(table_id):
                add_node(
                    graph,
                    nodes,
                    table_id,
                    type="table",
                    name=table_name,
                    description=f"Table or view used by {agent_name}.",
                    source="agent contract",
                )
            add_edge(graph, agent_id, table_id, "uses_table")

        for metric_name in agent_data["metrics"]:
            metric_id = f"metric:{metric_name}"
            metric_data = METRICS.get(
                metric_name,
                {
                    "description": f"Metric {metric_name} thuộc domain {agent_data['domain']}.",
                    "formula": "Chưa seed công thức chi tiết.",
                    "source": agent_data["tables"][0],
                },
            )
            add_node(
                graph,
                nodes,
                metric_id,
                type="metric",
                name=metric_name,
                description=metric_data["description"],
                formula=metric_data["formula"],
                source=metric_data["source"],
            )
            add_edge(graph, agent_id, metric_id, "owns_metric")
            source_table_id = f"table:{metric_data['source']}"
            if graph.has_node(source_table_id):
                add_edge(graph, metric_id, source_table_id, "computed_from")

    metric_catalog_table_id = ensure_table_node(
        graph,
        nodes,
        "agent.metric_catalog",
        description="Seeded metric definitions and source lineage for the copilot.",
        source="sql/agent/020_seed_agent_metadata.sql",
        node_type="metadata_table",
    )
    for metric_name, metric_data in METRICS.items():
        metric_id = f"metric:{metric_name}"
        if not graph.has_node(metric_id):
            add_node(
                graph,
                nodes,
                metric_id,
                type="metric",
                name=metric_name,
                description=metric_data["description"],
                formula=metric_data["formula"],
                source=metric_data["source"],
            )
        add_edge(graph, metric_catalog_table_id, metric_id, "defines_metric")
        source_table_id = ensure_table_node(
            graph,
            nodes,
            metric_data["source"],
            source="metric source",
        )
        add_edge(graph, metric_id, source_table_id, "computed_from")

    template_catalog_table_id = ensure_table_node(
        graph,
        nodes,
        "agent.sql_templates",
        description="Read-only SQL template catalog for deterministic copilot answers.",
        source="sql/agent/020_seed_agent_metadata.sql",
        node_type="metadata_table",
    )
    for template in ALL_TEMPLATES:
        template_id = f"template:{template.name}"
        try:
            sql_template = template.sql_builder("").strip()
        except Exception:
            sql_template = ""

        add_node(
            graph,
            nodes,
            template_id,
            type="sql_template",
            name=template.name,
            domain=template.domain,
            description=template.description,
            source="agents/sql_templates.py",
            agents=list(template.agents),
            metrics=list(template.metrics),
            tables=list(template.tables),
            keywords=list(template.keywords),
            sql_template=sql_template[:1200],
        )
        add_edge(graph, template_catalog_table_id, template_id, "catalogs_template")

        for agent_name in template.agents:
            add_edge(graph, f"agent:{agent_name}", template_id, "can_answer")
        for metric_name in template.metrics:
            metric_id = f"metric:{metric_name}"
            if not graph.has_node(metric_id):
                add_node(
                    graph,
                    nodes,
                    metric_id,
                    type="metric",
                    name=metric_name,
                    description=f"Metric used by SQL template {template.name}.",
                    formula="See SQL template and metric catalog.",
                    source="agent.sql_templates",
                )
                add_edge(graph, metric_catalog_table_id, metric_id, "defines_metric")
            add_edge(graph, template_id, metric_id, "returns_metric")
        for table_name in template.tables:
            table_id = ensure_table_node(
                graph,
                nodes,
                table_name,
                source="sql template",
            )
            add_edge(graph, template_id, table_id, "queries_table")

    question_catalog_table_id = ensure_table_node(
        graph,
        nodes,
        "agent.question_examples",
        description="Vietnamese evaluation and demo questions for copilot routing.",
        source="sql/agent/020_seed_agent_metadata.sql",
        node_type="metadata_table",
    )
    for example in QUESTION_EXAMPLES:
        question_id = f"question:{example['id']}"
        add_node(
            graph,
            nodes,
            question_id,
            type="question_example",
            name=example["id"],
            description=example["question"],
            source="sql/agent/020_seed_agent_metadata.sql",
            question=example["question"],
            domain=example["domain"],
            agents=example["agents"],
            metrics=example["metrics"],
            tables=example["tables"],
            template=example["template"],
        )
        add_edge(graph, question_catalog_table_id, question_id, "catalogs_question")
        add_edge(graph, question_id, f"template:{example['template']}", "expects_template")
        for agent_name in example["agents"]:
            add_edge(graph, question_id, f"agent:{agent_name}", "expects_agent")
        for metric_name in example["metrics"]:
            add_edge(graph, question_id, f"metric:{metric_name}", "asks_metric")
        for table_name in example["tables"]:
            table_id = ensure_table_node(graph, nodes, table_name, source="question source")
            add_edge(graph, question_id, table_id, "expects_table")

    report_id = "report:data_quality_report"
    add_node(
        graph,
        nodes,
        report_id,
        type="report",
        name="data_quality_report.md",
        description="Report pass/fail data quality checks: row counts, null, duplicate keys, FK integrity, dates, numeric rules và KPI regression.",
        source="reports/data_quality_report.md",
    )
    add_edge(graph, "agent:data_quality_agent", report_id, "uses_report")

    return graph, nodes


def load_embedding_model(model_name: str = DEFAULT_EMBEDDING_MODEL) -> TextEmbedding:
    return TextEmbedding(model_name=model_name)


def embed_nodes(nodes: list[dict[str, Any]], embed_model: TextEmbedding) -> np.ndarray:
    texts = [node_text(node) for node in nodes]
    embeddings = list(embed_model.embed(texts))
    embeddings_np = np.array(embeddings).astype("float32")
    faiss.normalize_L2(embeddings_np)
    return embeddings_np


def build_embedding_index_from_embeddings(embeddings_np: np.ndarray) -> faiss.Index:
    index = faiss.IndexFlatIP(embeddings_np.shape[1])
    index.add(embeddings_np)
    return index


def build_embedding_index(nodes: list[dict[str, Any]], embed_model: TextEmbedding) -> faiss.Index:
    return build_embedding_index_from_embeddings(embed_nodes(nodes, embed_model))


def search_nodes(
    query: str,
    index: faiss.Index,
    nodes: list[dict[str, Any]],
    embed_model: TextEmbedding,
    top_k: int = DEFAULT_TOP_K,
) -> list[dict[str, Any]]:
    query_emb = np.array(list(embed_model.embed([query]))).astype("float32")
    faiss.normalize_L2(query_emb)
    distances, indices = index.search(query_emb, min(top_k, len(nodes)))

    results: list[dict[str, Any]] = []
    for distance, index_position in zip(distances[0], indices[0]):
        if 0 <= index_position < len(nodes):
            results.append({**nodes[index_position], "score": float(distance)})
    return results


def lexical_search_nodes(query: str, nodes: list[dict[str, Any]], top_k: int = DEFAULT_TOP_K) -> list[dict[str, Any]]:
    tokens = {token for token in re.split(r"\W+", query.lower()) if token}
    scored: list[tuple[int, dict[str, Any]]] = []
    for node in nodes:
        text = node_text(node).lower()
        score = sum(1 for token in tokens if token in text)
        if score:
            scored.append((score, node))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [{**node, "score": float(score)} for score, node in scored[:top_k]]


def hybrid_search_nodes(
    query: str,
    index: faiss.Index,
    nodes: list[dict[str, Any]],
    embed_model: TextEmbedding,
    top_k: int = DEFAULT_TOP_K,
) -> list[dict[str, Any]]:
    semantic_results = search_nodes(query, index, nodes, embed_model, top_k=top_k)
    lexical_results = lexical_search_nodes(query, nodes, top_k=top_k)

    merged: dict[str, dict[str, Any]] = {}
    for rank, result in enumerate(semantic_results):
        score = float(result.get("score", 0.0)) + ((top_k - rank) / top_k)
        merged[result["id"]] = {**result, "score": score, "retrieval": "semantic"}

    for rank, result in enumerate(lexical_results):
        boost = 1.5 + ((top_k - rank) / top_k)
        existing = merged.get(result["id"])
        if existing:
            existing["score"] = float(existing.get("score", 0.0)) + boost
            existing["retrieval"] = "hybrid"
        else:
            merged[result["id"]] = {**result, "score": boost, "retrieval": "lexical"}

    return sorted(merged.values(), key=lambda item: float(item.get("score", 0.0)), reverse=True)[:top_k]


def get_subgraph_context(graph: nx.DiGraph, node_ids: list[str], depth: int = 1) -> tuple[str, set[str]]:
    relevant_nodes: set[str] = set()
    for node_id in node_ids:
        if graph.has_node(node_id):
            relevant_nodes.update(nx.ego_graph(graph, node_id, radius=depth, undirected=True).nodes())

    context_parts: list[str] = []
    for node_id in sorted(relevant_nodes):
        data = graph.nodes[node_id]
        part = f"[{data.get('type', 'unknown').upper()}] {data.get('name', node_id)}"
        if data.get("description"):
            part += f"\n  Description: {data['description']}"
        if data.get("formula"):
            part += f"\n  Formula: {data['formula']}"
        if data.get("source"):
            part += f"\n  Source: {data['source']}"
        if data.get("metrics"):
            part += f"\n  Metrics: {', '.join(data['metrics'])}"
        if data.get("tables"):
            part += f"\n  Tables: {', '.join(data['tables'])}"

        incoming = [
            f"{source} --[{graph.edges[source, node_id].get('type', 'related')}]-->"
            for source in graph.predecessors(node_id)
        ]
        outgoing = [
            f"--[{graph.edges[node_id, target].get('type', 'related')}]--> {target}"
            for target in graph.successors(node_id)
        ]
        if incoming:
            part += f"\n  Incoming: {', '.join(incoming[:8])}"
        if outgoing:
            part += f"\n  Outgoing: {', '.join(outgoing[:8])}"

        context_parts.append(part)

    return "\n\n".join(context_parts), relevant_nodes


def save_graph_data(
    graph: nx.DiGraph,
    nodes: list[dict[str, Any]],
    index: faiss.Index | None = None,
    data_dir: Path = DEFAULT_GRAPH_DATA_DIR,
) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "graph.json").write_text(
        json.dumps(json_graph.node_link_data(graph), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (data_dir / "nodes.json").write_text(
        json.dumps(nodes, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if index is not None:
        faiss.write_index(index, str(data_dir / "index.faiss"))


def load_graph_data(data_dir: Path = DEFAULT_GRAPH_DATA_DIR) -> tuple[nx.DiGraph | None, list[dict[str, Any]] | None, faiss.Index | None]:
    graph_path = data_dir / "graph.json"
    nodes_path = data_dir / "nodes.json"
    index_path = data_dir / "index.faiss"
    if not graph_path.exists() or not nodes_path.exists():
        return None, None, None

    graph = json_graph.node_link_graph(json.loads(graph_path.read_text(encoding="utf-8")), directed=True)
    nodes = json.loads(nodes_path.read_text(encoding="utf-8"))
    index = faiss.read_index(str(index_path)) if index_path.exists() else None
    if index is not None and index.ntotal != len(nodes):
        index = None
    return graph, nodes, index


def ask_gemini_graph_rag(
    question: str,
    graph_context: str,
    chat_history: list[dict[str, str]] | None = None,
    llm_client: LLMClient | None = None,
) -> str:
    history = chat_history or []
    history_text = "\n".join(f"{item.get('role', 'user')}: {item.get('text', '')}" for item in history[-6:])
    prompt = f"""
Graph context:
---
{graph_context}
---

Chat history:
{history_text}

Câu hỏi người dùng:
{question}
""".strip()

    client = llm_client or GeminiClient()
    return client.generate(prompt, system_prompt=GRAPH_RAG_SYSTEM_PROMPT, temperature=0.1, max_output_tokens=1200)


@dataclass
class BikeStoreGraphRAG:
    graph: nx.DiGraph
    nodes: list[dict[str, Any]]
    index: faiss.Index | None = None
    embed_model: TextEmbedding | None = None
    llm_client: LLMClient | None = None

    @classmethod
    def from_project(
        cls,
        project_root: Path = PROJECT_ROOT,
        *,
        build_embeddings: bool = True,
        embedding_model_name: str = DEFAULT_EMBEDDING_MODEL,
        llm_client: LLMClient | None = None,
    ) -> "BikeStoreGraphRAG":
        graph, nodes = build_bike_store_graph(project_root)
        embed_model = load_embedding_model(embedding_model_name) if build_embeddings else None
        index = build_embedding_index(nodes, embed_model) if embed_model is not None else None
        return cls(graph=graph, nodes=nodes, index=index, embed_model=embed_model, llm_client=llm_client)

    def retrieve(self, question: str, top_k: int = DEFAULT_TOP_K, depth: int = 1) -> tuple[str, list[dict[str, Any]], set[str]]:
        if self.index is not None and self.embed_model is not None:
            results = hybrid_search_nodes(question, self.index, self.nodes, self.embed_model, top_k=top_k)
        else:
            results = lexical_search_nodes(question, self.nodes, top_k=top_k)
        node_ids = [result["id"] for result in results]
        context, relevant_node_ids = get_subgraph_context(self.graph, node_ids, depth=depth)
        return context, results, relevant_node_ids

    def answer(self, question: str, chat_history: list[dict[str, str]] | None = None, top_k: int = DEFAULT_TOP_K) -> GraphRAGResult:
        context, results, relevant_node_ids = self.retrieve(question, top_k=top_k)
        answer = ask_gemini_graph_rag(question, context, chat_history=chat_history, llm_client=self.llm_client)
        return GraphRAGResult(
            answer=answer,
            graph_context=context,
            node_ids=sorted(relevant_node_ids),
            sources=results,
        )
