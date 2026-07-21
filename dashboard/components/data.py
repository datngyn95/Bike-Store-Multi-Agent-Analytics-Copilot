from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from components.db import PROJECT_ROOT, query_df, try_query_df


def executive_summary() -> tuple[pd.DataFrame, str | None]:
    return try_query_df("select * from analytics.mart_executive_summary")


def sales_monthly() -> tuple[pd.DataFrame, str | None]:
    return try_query_df(
        """
        select month, year, month_number, orders, order_items, customers, units_sold,
               gross_sales, discount_amount, revenue, average_order_value, discount_rate
        from analytics.mart_sales_monthly
        order by month
        """
    )


def sales_by_store() -> tuple[pd.DataFrame, str | None]:
    return try_query_df(
        """
        select store_id, store_name, city, state, orders, customers, units_sold,
               revenue, average_order_value, late_shipment_rate
        from analytics.mart_sales_by_store
        order by revenue desc
        """
    )


def product_performance() -> tuple[pd.DataFrame, str | None]:
    return try_query_df(
        """
        select product_id, product_name, brand_id, brand_name, category_id, category_name,
               model_year, orders, units_sold, gross_sales, discount_amount, revenue,
               avg_selling_price, discount_rate
        from analytics.mart_product_performance
        order by revenue desc
        """
    )


def inventory_risk() -> tuple[pd.DataFrame, str | None]:
    return try_query_df(
        """
        select store_id, store_name, product_id, product_name, brand_name, category_name,
               stock_quantity, units_sold_90d, daily_sales_velocity, days_of_supply,
               inventory_value, inventory_status
        from analytics.mart_inventory_risk
        order by
            case inventory_status
                when 'stockout' then 1
                when 'stockout_risk' then 2
                when 'overstock_risk' then 3
                else 4
            end,
            units_sold_90d desc,
            inventory_value desc
        """
    )


def customer_segments() -> tuple[pd.DataFrame, str | None]:
    return try_query_df(
        """
        select customer_id, customer_name, city, state, orders, units_sold, revenue,
               first_order_date, last_order_date, customer_segment
        from analytics.mart_customer_segments
        order by revenue desc, orders desc
        """
    )


def staff_performance() -> tuple[pd.DataFrame, str | None]:
    return try_query_df(
        """
        select staff_id, staff_name, store_id, store_name, manager_id, manager_name,
               orders, customers, units_sold, revenue, average_order_value, late_shipment_rate
        from analytics.mart_staff_performance
        order by revenue desc
        """
    )


def delivery_performance() -> tuple[pd.DataFrame, str | None]:
    return try_query_df(
        """
        select month, store_id, store_name, orders, shipped_orders,
               avg_days_to_ship, late_shipment_rate
        from analytics.mart_delivery_performance
        order by month, store_name
        """
    )


def metric_catalog() -> tuple[pd.DataFrame, str | None]:
    return try_query_df(
        """
        select metric_name, description, formula, primary_source
        from agent.metric_catalog_seed
        order by metric_name
        """
    )


def data_quality_results() -> tuple[pd.DataFrame, str, str | None]:
    audit_sql = """
        select run_id, checked_at, check_name, category, severity, status,
               issue_count, max_allowed, description
        from audit.data_quality_check_results
        order by checked_at desc, check_name
    """
    df, error = try_query_df(audit_sql)
    if error is None and not df.empty:
        return df, "audit.data_quality_check_results", None

    fallback_df, fallback_error = _local_data_quality_results()
    if fallback_error:
        return pd.DataFrame(), "reports/data_quality_results.csv", error or fallback_error
    return fallback_df, "reports/data_quality_results.csv", error


@st.cache_data(ttl=300, show_spinner=False)
def _local_data_quality_results() -> tuple[pd.DataFrame, str | None]:
    report_path = PROJECT_ROOT / "reports" / "data_quality_results.csv"
    if not report_path.exists():
        return pd.DataFrame(), f"Khong tim thay {report_path}"
    return pd.read_csv(report_path), None


def run_copilot_template(sql: str) -> tuple[pd.DataFrame, str | None]:
    return try_query_df(sql)
