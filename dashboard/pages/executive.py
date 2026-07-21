from __future__ import annotations

import pandas as pd
import streamlit as st

from components import charts, data, formatters as fmt, ui


def render() -> None:
    ui.page_title("Executive", "Tong quan doanh thu, don hang, khach hang va suc khoe van hanh.")

    summary, error = data.executive_summary()
    if not ui.require_data(summary, error):
        return

    row = summary.iloc[0]
    ui.metric_row(
        [
            ui.Metric("Revenue", fmt.currency(row["revenue"], 0)),
            ui.Metric("Orders", fmt.number(row["orders"])),
            ui.Metric("Customers", fmt.number(row["customers_with_orders"])),
            ui.Metric("AOV", fmt.currency(row["average_order_value"], 0)),
            ui.Metric("Late shipment", fmt.percent(row["late_shipment_rate"])),
        ]
    )
    st.caption(
        f"Order range: {fmt.compact_date(row['first_order_date'])} -> {fmt.compact_date(row['last_order_date'])}"
    )

    monthly, monthly_error = data.sales_monthly()
    stores_df, stores_error = data.sales_by_store()
    products_df, products_error = data.product_performance()
    inventory_df, inventory_error = data.inventory_risk()
    ui.show_query_issue(monthly_error or stores_error or products_error or inventory_error)

    if not monthly.empty:
        monthly = monthly.copy()
        monthly["month"] = pd.to_datetime(monthly["month"])
        col_left, col_right = st.columns([2, 1])
        with col_left:
            st.plotly_chart(charts.line(monthly, "month", "revenue", "Monthly revenue"), width="stretch")
        with col_right:
            st.plotly_chart(charts.bar(monthly, "month", "orders", "Monthly orders"), width="stretch")

    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Store leaderboard")
        if not stores_df.empty:
            st.plotly_chart(
                charts.bar(stores_df, "store_name", "revenue", title="Revenue by store"),
                width="stretch",
            )
            ui.dataframe(
                stores_df[
                    ["store_name", "city", "state", "orders", "customers", "revenue", "late_shipment_rate"]
                ],
                height=260,
            )
    with col_right:
        st.subheader("Inventory risk mix")
        if not inventory_df.empty:
            status_df = (
                inventory_df.groupby("inventory_status", dropna=False)
                .agg(products=("product_id", "count"), inventory_value=("inventory_value", "sum"))
                .reset_index()
            )
            st.plotly_chart(charts.pie(status_df, "inventory_status", "products", "Inventory status"), width="stretch")
            ui.dataframe(status_df, height=260)

    st.subheader("Top products")
    if not products_df.empty:
        top_products = products_df.head(10)[
            ["product_name", "brand_name", "category_name", "orders", "units_sold", "revenue", "discount_rate"]
        ]
        ui.dataframe(top_products, height=320)
