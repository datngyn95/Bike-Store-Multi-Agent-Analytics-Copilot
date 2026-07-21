from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


AnswerBuilder = Callable[[list[dict[str, Any]]], str]
SQLBuilder = Callable[[str], str]


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.lower())
    without_marks = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return without_marks.replace("đ", "d")


@dataclass(frozen=True)
class SQLTemplate:
    name: str
    domain: str
    agents: tuple[str, ...]
    keywords: tuple[str, ...]
    metrics: tuple[str, ...]
    tables: tuple[str, ...]
    sql_builder: SQLBuilder
    answer_builder: AnswerBuilder
    description: str = ""

    def score(self, question: str) -> int:
        normalized_question = normalize_text(question)
        return sum(1 for keyword in self.keywords if normalize_text(keyword) in normalized_question)


def _year_from_question(question: str) -> int | None:
    match = re.search(r"\b(2016|2017|2018)\b", question)
    return int(match.group(1)) if match else None


def _number(value: Any) -> str:
    try:
        return f"{float(value):,.0f}"
    except (TypeError, ValueError):
        return str(value)


def _currency(value: Any) -> str:
    try:
        return f"${float(value):,.0f}"
    except (TypeError, ValueError):
        return str(value)


def _percent(value: Any) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return str(value)


def _sum(rows: list[dict[str, Any]], key: str) -> float:
    return sum(float(row.get(key) or 0) for row in rows)


def _sales_monthly_sql(question: str) -> str:
    year = _year_from_question(question)
    where_clause = f"where year = {year}" if year else ""
    return f"""
        select month, year, month_number, orders, units_sold, revenue, average_order_value, discount_rate
        from analytics.mart_sales_monthly
        {where_clause}
        order by month
        limit 100
    """


def _sales_summary_sql(_: str) -> str:
    return """
        select orders, order_items, customers_with_orders, products_sold, stores_with_orders,
               first_order_date, last_order_date, revenue, units_sold, average_order_value,
               discount_rate, avg_days_to_ship, late_shipment_rate
        from analytics.mart_executive_summary
        limit 1
    """


def _top_store_sql(_: str) -> str:
    return """
        select store_name, city, state, orders, customers, units_sold, revenue,
               average_order_value, late_shipment_rate
        from analytics.mart_sales_by_store
        order by revenue desc
        limit 10
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


def _product_performance_sql(question: str) -> str:
    normalized = normalize_text(question)
    if "category" in normalized or "nhom" in normalized or "danh muc" in normalized:
        return """
            select category_name, sum(revenue) as revenue, sum(units_sold) as units_sold,
                   count(*) as products, avg(discount_rate) as discount_rate
            from analytics.mart_product_performance
            group by category_name
            order by revenue desc
            limit 10
        """
    if "brand" in normalized or "thuong hieu" in normalized:
        return """
            select brand_name, sum(revenue) as revenue, sum(units_sold) as units_sold,
                   count(*) as products, avg(discount_rate) as discount_rate
            from analytics.mart_product_performance
            group by brand_name
            order by revenue desc
            limit 10
        """
    return """
        select product_name, brand_name, category_name, model_year, orders, units_sold,
               revenue, avg_selling_price, discount_rate
        from analytics.mart_product_performance
        order by revenue desc
        limit 20
    """


def _inventory_risk_sql(question: str) -> str:
    normalized = normalize_text(question)
    if "overstock" in normalized or "du hang" in normalized:
        where_clause = "where inventory_status = 'overstock_risk'"
    elif "stockout" in normalized or "het hang" in normalized or "sap het" in normalized:
        where_clause = "where inventory_status in ('stockout', 'stockout_risk')"
    else:
        where_clause = "where inventory_status in ('stockout', 'stockout_risk', 'overstock_risk')"
    return f"""
        select store_name, product_name, brand_name, category_name, stock_quantity,
               units_sold_90d, daily_sales_velocity, days_of_supply, inventory_value,
               inventory_status
        from analytics.mart_inventory_risk
        {where_clause}
        order by
            case inventory_status
                when 'stockout' then 1
                when 'stockout_risk' then 2
                when 'overstock_risk' then 3
                else 4
            end,
            case when days_of_supply is null then 1 else 0 end,
            days_of_supply asc,
            units_sold_90d desc
        limit 25
    """


def _customer_state_sql(question: str) -> str:
    normalized = normalize_text(question)
    if "top" in normalized or "vip" in normalized or "khach hang nao" in normalized:
        return """
            select customer_name, city, state, orders, units_sold, revenue,
                   first_order_date, last_order_date, customer_segment
            from analytics.mart_customer_segments
            order by revenue desc, orders desc
            limit 20
        """
    return """
        select state, count(*) as customers, sum(orders) as orders,
               sum(units_sold) as units_sold, sum(revenue) as revenue
        from analytics.mart_customer_segments
        group by state
        order by revenue desc
        limit 20
    """


def _staff_sql(_: str) -> str:
    return """
        select staff_name, store_name, manager_name, orders, customers, units_sold,
               revenue, average_order_value, late_shipment_rate
        from analytics.mart_staff_performance
        order by revenue desc
        limit 20
    """


def _data_quality_sql(_: str) -> str:
    return """
        select count(*) as rows_checked,
               count(*) filter (
                   where order_id is null
                      or item_id is null
                      or product_id is null
                      or quantity is null
                      or list_price is null
                      or discount is null
               ) as missing_required_fields,
               count(*) filter (
                   where quantity <= 0
                      or list_price <= 0
                      or discount < 0
                      or discount >= 1
               ) as invalid_numeric_rows,
               count(*) filter (where revenue < 0) as negative_revenue_rows
        from analytics.fact_sales
        limit 1
    """


def _metric_catalog_sql(_: str) -> str:
    return """
        select metric_name, description, formula, primary_source
        from agent.metric_catalog
        where is_active
        order by metric_name
        limit 50
    """


def _answer_sales_monthly(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "Không có dữ liệu doanh thu cho bộ lọc này."
    total_revenue = _sum(rows, "revenue")
    total_orders = _sum(rows, "orders")
    best = max(rows, key=lambda row: float(row.get("revenue") or 0))
    return (
        f"Tổng revenue là {_currency(total_revenue)} trên {_number(total_orders)} orders. "
        f"Tháng cao nhất là {best.get('month')} với {_currency(best.get('revenue'))}. "
        "Nguồn: analytics.mart_sales_monthly."
    )


def _answer_sales_summary(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "Không có dữ liệu executive summary."
    row = rows[0]
    return (
        f"Bike Store có {_number(row.get('orders'))} orders, "
        f"{_number(row.get('units_sold'))} units sold và revenue {_currency(row.get('revenue'))}. "
        f"AOV là {_currency(row.get('average_order_value'))}, late shipment rate {_percent(row.get('late_shipment_rate'))}. "
        "Nguồn: analytics.mart_executive_summary."
    )


def _answer_top_row(rows: list[dict[str, Any]], label_col: str, value_col: str, metric_name: str, source: str) -> str:
    if not rows:
        return "Không có kết quả phù hợp."
    top = rows[0]
    value = _currency(top.get(value_col)) if "rate" not in value_col else _percent(top.get(value_col))
    return f"{top.get(label_col)} đang dẫn đầu với {metric_name} {value}. Nguồn: {source}."


def _answer_product(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "Không có dữ liệu product performance."
    first = rows[0]
    label = first.get("product_name") or first.get("brand_name") or first.get("category_name")
    return (
        f"{label} đang dẫn đầu với revenue {_currency(first.get('revenue'))} "
        f"và {_number(first.get('units_sold'))} units sold. "
        "Nguồn: analytics.mart_product_performance."
    )


def _answer_inventory(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "Không có sản phẩm nào đang có rủi ro tồn kho theo template hiện tại."
    top = rows[0]
    return (
        f"Rủi ro nổi bật là {top.get('product_name')} tại {top.get('store_name')}: "
        f"stock {_number(top.get('stock_quantity'))}, bán 90 ngày {_number(top.get('units_sold_90d'))}, "
        f"trạng thái {top.get('inventory_status')}. Nguồn: analytics.mart_inventory_risk."
    )


def _answer_customer(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "Không có dữ liệu customer segment."
    top = rows[0]
    if "customer_name" in top:
        return (
            f"Khách hàng nổi bật là {top.get('customer_name')} tại {top.get('state')} "
            f"với revenue {_currency(top.get('revenue'))} và {_number(top.get('orders'))} orders. "
            "Nguồn: analytics.mart_customer_segments."
        )
    return (
        f"Bang/state dẫn đầu là {top.get('state')} với revenue {_currency(top.get('revenue'))} "
        f"trên {_number(top.get('customers'))} customers. Nguồn: analytics.mart_customer_segments."
    )


def _answer_staff(rows: list[dict[str, Any]]) -> str:
    return _answer_top_row(rows, "staff_name", "revenue", "revenue", "analytics.mart_staff_performance")


def _answer_delivery(rows: list[dict[str, Any]]) -> str:
    return _answer_top_row(
        rows,
        "store_name",
        "late_shipment_rate",
        "late shipment rate",
        "analytics.mart_delivery_performance",
    )


def _answer_data_quality(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "Không có dữ liệu để kiểm tra chất lượng dữ liệu."
    row = rows[0]
    issue_count = sum(
        int(row.get(key) or 0)
        for key in ("missing_required_fields", "invalid_numeric_rows", "negative_revenue_rows")
    )
    if issue_count == 0:
        return (
            f"Không thấy lỗi bắt buộc/numeric/revenue âm trong {_number(row.get('rows_checked'))} dòng fact_sales. "
            "Nguồn: analytics.fact_sales; báo cáo đầy đủ vẫn nằm ở reports/data_quality_report.md."
        )
    return (
        f"Phát hiện {_number(issue_count)} vấn đề dữ liệu trong analytics.fact_sales: "
        f"missing={_number(row.get('missing_required_fields'))}, "
        f"numeric={_number(row.get('invalid_numeric_rows'))}, "
        f"negative_revenue={_number(row.get('negative_revenue_rows'))}."
    )


def _answer_metric_catalog(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "Chưa đọc được metric catalog."
    metric_names = ", ".join(str(row.get("metric_name")) for row in rows[:8])
    return f"Metric catalog hiện có các metric chính: {metric_names}. Nguồn: agent.metric_catalog."


ALL_TEMPLATES: tuple[SQLTemplate, ...] = (
    SQLTemplate(
        name="sales_monthly",
        domain="sales",
        agents=("sales_agent",),
        keywords=("doanh thu", "revenue", "sales", "tháng", "theo tháng", "monthly", "2016", "2017", "2018"),
        metrics=("revenue", "orders", "units_sold", "average_order_value", "discount_rate"),
        tables=("analytics.mart_sales_monthly",),
        sql_builder=_sales_monthly_sql,
        answer_builder=_answer_sales_monthly,
        description="Doanh thu, order, AOV và discount theo tháng.",
    ),
    SQLTemplate(
        name="sales_summary",
        domain="sales",
        agents=("sales_agent",),
        keywords=("tổng quan", "overview", "kpi", "summary", "doanh số", "tổng doanh thu"),
        metrics=("revenue", "orders", "units_sold", "average_order_value", "late_shipment_rate"),
        tables=("analytics.mart_executive_summary",),
        sql_builder=_sales_summary_sql,
        answer_builder=_answer_sales_summary,
        description="KPI executive summary.",
    ),
    SQLTemplate(
        name="top_store",
        domain="store",
        agents=("store_agent", "sales_agent"),
        keywords=("cửa hàng", "cua hang", "store", "cao nhất", "top store", "doanh thu", "revenue"),
        metrics=("store_revenue", "orders", "average_order_value", "late_shipment_rate"),
        tables=("analytics.mart_sales_by_store",),
        sql_builder=_top_store_sql,
        answer_builder=lambda rows: _answer_top_row(rows, "store_name", "revenue", "revenue", "analytics.mart_sales_by_store"),
        description="Xếp hạng cửa hàng theo revenue.",
    ),
    SQLTemplate(
        name="delivery_late",
        domain="store",
        agents=("store_agent",),
        keywords=("giao trễ", "giao tre", "late", "delivery", "shipment", "ship", "chậm giao"),
        metrics=("late_shipment_rate", "avg_days_to_ship"),
        tables=("analytics.mart_delivery_performance",),
        sql_builder=_delivery_sql,
        answer_builder=_answer_delivery,
        description="Tỷ lệ giao trễ theo cửa hàng.",
    ),
    SQLTemplate(
        name="product_performance",
        domain="product",
        agents=("product_agent",),
        keywords=(
            "sản phẩm",
            "san pham",
            "product",
            "brand",
            "thương hiệu",
            "category",
            "danh mục",
            "model",
            "doanh thu",
            "revenue",
            "đóng góp",
            "dong gop",
        ),
        metrics=("product_revenue", "brand_revenue", "category_revenue", "units_sold", "avg_selling_price"),
        tables=("analytics.mart_product_performance",),
        sql_builder=_product_performance_sql,
        answer_builder=_answer_product,
        description="Hiệu quả sản phẩm, brand và category.",
    ),
    SQLTemplate(
        name="inventory_risk",
        domain="inventory",
        agents=("inventory_agent", "product_agent"),
        keywords=("tồn kho", "ton kho", "stock", "inventory", "stockout", "overstock", "bán chạy", "ban chay", "rủi ro", "rui ro"),
        metrics=("stock_quantity", "sales_velocity", "stockout_risk", "overstock_risk", "inventory_value"),
        tables=("analytics.mart_inventory_risk",),
        sql_builder=_inventory_risk_sql,
        answer_builder=_answer_inventory,
        description="Rủi ro stockout/overstock theo store và product.",
    ),
    SQLTemplate(
        name="customer_state",
        domain="customer",
        agents=("customer_agent",),
        keywords=("khách", "khach", "customer", "state", "bang", "bang nào", "city", "vip", "top khách"),
        metrics=("customer_count", "orders_per_customer", "revenue_per_customer", "state_revenue", "top_customers"),
        tables=("analytics.mart_customer_segments",),
        sql_builder=_customer_state_sql,
        answer_builder=_answer_customer,
        description="Phân tích khách hàng theo state hoặc top customer.",
    ),
    SQLTemplate(
        name="staff_revenue",
        domain="staff",
        agents=("staff_agent",),
        keywords=("nhân viên", "nhan vien", "staff", "manager", "xử lý", "xu ly", "salesperson"),
        metrics=("orders_by_staff", "revenue_by_staff", "avg_order_value_by_staff", "manager_performance"),
        tables=("analytics.mart_staff_performance",),
        sql_builder=_staff_sql,
        answer_builder=_answer_staff,
        description="Hiệu quả staff theo revenue/orders/AOV.",
    ),
    SQLTemplate(
        name="data_quality_fact_sales",
        domain="data_quality",
        agents=("data_quality_agent",),
        keywords=("lỗi dữ liệu", "loi du lieu", "data quality", "null", "duplicate", "foreign key", "order_items", "quality"),
        metrics=("missing_required_fields", "invalid_numeric_rows", "negative_revenue_rows"),
        tables=("analytics.fact_sales",),
        sql_builder=_data_quality_sql,
        answer_builder=_answer_data_quality,
        description="Kiểm tra chất lượng dữ liệu đọc-only trên analytics.fact_sales.",
    ),
    SQLTemplate(
        name="metric_catalog",
        domain="data_quality",
        agents=("data_quality_agent", "orchestrator_agent"),
        keywords=(
            "metric",
            "catalog",
            "định nghĩa",
            "dinh nghia",
            "formula",
            "kpi là gì",
            "kpi la gi",
            "revenue",
            "orders",
            "units_sold",
            "average_order_value",
        ),
        metrics=("metric_catalog",),
        tables=("agent.metric_catalog",),
        sql_builder=_metric_catalog_sql,
        answer_builder=_answer_metric_catalog,
        description="Tra cứu metric catalog read-only.",
    ),
)


def templates_for_domain(domain: str) -> tuple[SQLTemplate, ...]:
    return tuple(template for template in ALL_TEMPLATES if template.domain == domain)
