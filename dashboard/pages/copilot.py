from __future__ import annotations

import re
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components import data, formatters as fmt, ui


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@dataclass(frozen=True)
class CopilotTemplate:
    name: str
    agents: list[str]
    keywords: list[str]
    metrics: list[str]
    tables: list[str]
    sql_builder: Callable[[str], str]
    answer_builder: Callable[[pd.DataFrame], str]


def _year_from_question(question: str) -> int | None:
    match = re.search(r"\b(2016|2017|2018)\b", question)
    return int(match.group(1)) if match else None


def _sales_monthly_sql(question: str) -> str:
    year = _year_from_question(question)
    where_clause = f"where year = {year}" if year else ""
    return f"""
        select month, year, orders, units_sold, revenue, average_order_value, discount_rate
        from analytics.mart_sales_monthly
        {where_clause}
        order by month
        limit 100
    """


def _top_store_sql(_: str) -> str:
    return """
        select store_name, city, state, orders, customers, revenue, average_order_value, late_shipment_rate
        from analytics.mart_sales_by_store
        order by revenue desc
        limit 10
    """


def _inventory_risk_sql(_: str) -> str:
    return """
        select store_name, product_name, brand_name, category_name, stock_quantity, units_sold_90d,
               daily_sales_velocity, days_of_supply, inventory_value, inventory_status
        from analytics.mart_inventory_risk
        where units_sold_90d > 0
        order by
            case when days_of_supply is null then 1 else 0 end,
            days_of_supply asc,
            units_sold_90d desc
        limit 25
    """


def _brand_sql(_: str) -> str:
    return """
        select brand_name, sum(revenue) as revenue, sum(units_sold) as units_sold, count(*) as products
        from analytics.mart_product_performance
        group by brand_name
        order by revenue desc
        limit 10
    """


def _customer_state_sql(_: str) -> str:
    return """
        select state, count(*) as customers, sum(orders) as orders, sum(revenue) as revenue
        from analytics.mart_customer_segments
        group by state
        order by revenue desc
        limit 20
    """


def _staff_sql(_: str) -> str:
    return """
        select staff_name, store_name, manager_name, orders, customers, units_sold, revenue, average_order_value
        from analytics.mart_staff_performance
        order by revenue desc
        limit 20
    """


def _delivery_sql(_: str) -> str:
    return """
        select store_name, sum(orders) as orders, sum(shipped_orders) as shipped_orders,
               avg(avg_days_to_ship) as avg_days_to_ship,
               avg(late_shipment_rate) as late_shipment_rate
        from analytics.mart_delivery_performance
        group by store_name
        order by late_shipment_rate desc
        limit 10
    """


def _answer_sales_monthly(df: pd.DataFrame) -> str:
    if df.empty:
        return "Khong co du lieu doanh thu cho bo loc nay."
    total_revenue = df["revenue"].sum()
    total_orders = df["orders"].sum()
    best = df.sort_values("revenue", ascending=False).iloc[0]
    return (
        f"Tong revenue la {fmt.currency(total_revenue, 0)} tren {fmt.number(total_orders)} orders. "
        f"Thang cao nhat la {fmt.compact_date(best['month'])} voi {fmt.currency(best['revenue'], 0)}."
    )


def _answer_top_row(df: pd.DataFrame, label_col: str, value_col: str, metric_name: str) -> str:
    if df.empty:
        return "Khong co ket qua phu hop."
    top = df.iloc[0]
    return f"{top[label_col]} dang dan dau voi {metric_name} {fmt.currency(top[value_col], 0)}."


def _answer_inventory(df: pd.DataFrame) -> str:
    if df.empty:
        return "Khong co san pham co sales velocity trong cua so 90 ngay gan nhat."
    top = df.iloc[0]
    return (
        f"Rui ro noi bat la {top['product_name']} tai {top['store_name']}: "
        f"stock {fmt.number(top['stock_quantity'])}, ban 90 ngay {fmt.number(top['units_sold_90d'])}."
    )


def _answer_delivery(df: pd.DataFrame) -> str:
    if df.empty:
        return "Khong co du lieu delivery."
    top = df.iloc[0]
    return f"{top['store_name']} co late shipment rate cao nhat: {fmt.percent(top['late_shipment_rate'])}."


TEMPLATES = [
    CopilotTemplate(
        "sales_monthly",
        ["sales_agent"],
        ["doanh thu", "revenue", "sales", "thang"],
        ["revenue", "orders", "average_order_value"],
        ["analytics.mart_sales_monthly"],
        _sales_monthly_sql,
        _answer_sales_monthly,
    ),
    CopilotTemplate(
        "top_store",
        ["store_agent", "sales_agent"],
        ["cua hang", "store", "cao nhat"],
        ["store_revenue", "orders", "average_order_value"],
        ["analytics.mart_sales_by_store"],
        _top_store_sql,
        lambda df: _answer_top_row(df, "store_name", "revenue", "revenue"),
    ),
    CopilotTemplate(
        "inventory_risk",
        ["inventory_agent", "product_agent"],
        ["ton kho", "stock", "stockout", "rui ro", "ban chay"],
        ["stock_quantity", "sales_velocity", "stockout_risk"],
        ["analytics.mart_inventory_risk"],
        _inventory_risk_sql,
        _answer_inventory,
    ),
    CopilotTemplate(
        "brand_revenue",
        ["product_agent"],
        ["brand", "thuong hieu", "dong gop"],
        ["brand_revenue", "units_sold"],
        ["analytics.mart_product_performance"],
        _brand_sql,
        lambda df: _answer_top_row(df, "brand_name", "revenue", "revenue"),
    ),
    CopilotTemplate(
        "customer_state",
        ["customer_agent"],
        ["khach hang", "state", "bang", "customer"],
        ["state_revenue", "customer_count"],
        ["analytics.mart_customer_segments"],
        _customer_state_sql,
        lambda df: _answer_top_row(df, "state", "revenue", "revenue"),
    ),
    CopilotTemplate(
        "staff_revenue",
        ["staff_agent"],
        ["nhan vien", "staff", "xu ly"],
        ["revenue_by_staff", "orders_by_staff"],
        ["analytics.mart_staff_performance"],
        _staff_sql,
        lambda df: _answer_top_row(df, "staff_name", "revenue", "revenue"),
    ),
    CopilotTemplate(
        "delivery_late",
        ["store_agent"],
        ["giao tre", "ty le giao", "late", "delivery", "ship", "cua hang", "cao nhat"],
        ["late_shipment_rate"],
        ["analytics.mart_delivery_performance"],
        _delivery_sql,
        _answer_delivery,
    ),
]


EXAMPLES = [
    "Doanh thu theo thang nam 2017 nhu the nao?",
    "Cua hang nao co doanh thu cao nhat?",
    "San pham nao ban chay nhung ton kho thap?",
    "Brand nao dong gop doanh thu lon nhat?",
    "Khach hang o bang nao co revenue cao nhat?",
    "Nhan vien nao xu ly revenue cao nhat?",
    "Cua hang nao co ty le giao tre cao nhat?",
]


def _route(question: str) -> CopilotTemplate | None:
    normalized = question.lower()
    scored = []
    for template in TEMPLATES:
        score = sum(1 for keyword in template.keywords if keyword in normalized)
        if score:
            scored.append((score, template))
    if not scored:
        return None
    return sorted(scored, key=lambda item: item[0], reverse=True)[0][1]


@st.cache_resource(show_spinner=False)
def _runtime_graph_rag():
    try:
        from agents.graph_rag import BikeStoreGraphRAG, load_graph_data

        graph, nodes, _index = load_graph_data()
        if graph is not None and nodes is not None:
            return BikeStoreGraphRAG(graph=graph, nodes=nodes)
        return BikeStoreGraphRAG.from_project(build_embeddings=False)
    except Exception:
        return None


def _graph_evidence(question: str, template: CopilotTemplate, max_nodes: int = 36, max_edges: int = 80) -> dict[str, Any]:
    rag = _runtime_graph_rag()
    if rag is None:
        return {"nodes": [], "edges": []}

    retrieval_query = " ".join([question, *template.agents, *template.metrics, *template.tables])
    try:
        _context, matches, relevant_node_ids = rag.retrieve(retrieval_query, top_k=8, depth=1)
    except Exception:
        return {"nodes": [], "edges": []}

    matched_ids = [str(match["id"]) for match in matches if match.get("id")]
    matched_set = set(matched_ids)
    score_by_id = {str(match["id"]): float(match.get("score", 0.0)) for match in matches if match.get("id")}
    supporting_ids = sorted(str(node_id) for node_id in relevant_node_ids if str(node_id) not in matched_set)
    selected_ids = [node_id for node_id in matched_ids if node_id in relevant_node_ids]
    selected_ids.extend(supporting_ids)
    selected_ids = selected_ids[:max_nodes]
    selected_set = set(selected_ids)

    nodes = []
    for node_id in selected_ids:
        if not rag.graph.has_node(node_id):
            continue
        node = rag.graph.nodes[node_id]
        nodes.append(
            {
                "id": node_id,
                "label": str(node.get("name") or node_id),
                "type": str(node.get("type") or "unknown"),
                "source": str(node.get("source") or ""),
                "description": str(node.get("description") or ""),
                "score": score_by_id.get(node_id),
                "matched": node_id in matched_set,
            }
        )

    edges = []
    for source, target, edge in rag.graph.edges(data=True):
        if source in selected_set and target in selected_set:
            edges.append({"source": str(source), "target": str(target), "type": str(edge.get("type") or "related")})
        if len(edges) >= max_edges:
            break

    return {"nodes": nodes, "edges": edges}


def _graph_evidence_figure(evidence: dict[str, Any]) -> go.Figure:
    graph = nx.DiGraph()
    for node in evidence["nodes"]:
        graph.add_node(node["id"], **node)
    for edge in evidence["edges"]:
        if graph.has_node(edge["source"]) and graph.has_node(edge["target"]):
            graph.add_edge(edge["source"], edge["target"], type=edge["type"])

    if graph.number_of_edges() > 0:
        positions = nx.spring_layout(graph, seed=7, k=0.72, iterations=80)
    else:
        positions = nx.circular_layout(graph)

    edge_x: list[float | None] = []
    edge_y: list[float | None] = []
    for source, target in graph.edges():
        x0, y0 = positions[source]
        x1, y1 = positions[target]
        edge_x.extend([float(x0), float(x1), None])
        edge_y.extend([float(y0), float(y1), None])

    type_colors = {
        "agent": "#0f8b8d",
        "metric": "#2f855a",
        "sql_template": "#805ad5",
        "question_example": "#b7791f",
        "table": "#6b7280",
        "view": "#6b7280",
        "metadata_table": "#6b7280",
        "schema": "#e36414",
        "project": "#e36414",
        "report": "#c53030",
    }

    node_x = []
    node_y = []
    node_text = []
    node_hover = []
    node_color = []
    node_size = []
    for node_id, node in graph.nodes(data=True):
        x, y = positions[node_id]
        node_x.append(float(x))
        node_y.append(float(y))
        node_text.append(str(node["label"])[:28])
        node_hover.append(
            "<br>".join(
                [
                    f"<b>{node['label']}</b>",
                    f"type: {node['type']}",
                    f"source: {node['source']}",
                    str(node["description"])[:220],
                ]
            )
        )
        node_color.append("#27f1e6" if node.get("matched") else type_colors.get(str(node["type"]), "#6b7280"))
        node_size.append(22 if node.get("matched") else 15)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line=dict(width=1.25, color="rgba(15, 139, 141, 0.42)"),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            marker=dict(size=node_size, color=node_color, line=dict(width=1, color="#ffffff")),
            text=node_text,
            textposition="top center",
            hovertext=node_hover,
            hoverinfo="text",
            showlegend=False,
        )
    )
    fig.update_layout(
        height=460,
        margin=dict(l=8, r=8, t=12, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig


def render() -> None:
    ui.page_title("Copilot", "Shell tieng Viet voi SQL template readonly cho Sprint 4.")

    if "copilot_question" not in st.session_state:
        st.session_state.copilot_question = EXAMPLES[0]

    selected_example = st.selectbox("Cau hoi mau", EXAMPLES)
    if st.button("Nap cau hoi", width="content"):
        st.session_state.copilot_question = selected_example

    question = st.text_area("Cau hoi", key="copilot_question", height=90)
    submitted = st.button("Chay copilot shell", type="primary")

    metric_catalog, catalog_error = data.metric_catalog()
    if catalog_error is None and not metric_catalog.empty:
        with st.expander("Metric definitions", expanded=False):
            ui.dataframe(metric_catalog, height=240)

    if not submitted:
        return

    template = _route(question)
    if template is None:
        st.warning("Copilot shell chua co SQL template cho cau hoi nay.")
        st.json({"agents": [], "warnings": ["unsupported_template"]})
        return

    sql = template.sql_builder(question)
    rows, error = data.run_copilot_template(sql)
    if error:
        st.error(error)
        return

    st.subheader("Answer")
    st.write(template.answer_builder(rows))

    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Agents")
        st.json(template.agents)
    with col_right:
        st.subheader("Sources")
        st.json({"metrics": template.metrics, "tables": template.tables})

    st.subheader("SQL")
    st.code(sql.strip(), language="sql")

    st.subheader("Rows")
    ui.dataframe(rows, height=420)

    evidence = _graph_evidence(question, template)
    st.subheader("Graph RAG evidence")
    if evidence["nodes"]:
        st.caption(f"{len(evidence['nodes'])} nodes, {len(evidence['edges'])} edges")
        st.plotly_chart(_graph_evidence_figure(evidence), width="stretch")
    else:
        st.caption("Khong co graph evidence cho cau hoi nay.")
