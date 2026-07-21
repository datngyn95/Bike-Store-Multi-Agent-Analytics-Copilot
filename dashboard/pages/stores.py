from __future__ import annotations

import pandas as pd
import streamlit as st

from components import charts, data, formatters as fmt, ui


def render() -> None:
    ui.page_title("Stores", "Revenue, delivery va inventory health theo cua hang.")

    stores_df, store_error = data.sales_by_store()
    delivery, delivery_error = data.delivery_performance()
    inventory, inventory_error = data.inventory_risk()
    if not ui.require_data(stores_df, store_error):
        return
    ui.show_query_issue(delivery_error or inventory_error)

    ui.metric_row(
        [
            ui.Metric("Stores", fmt.number(stores_df["store_id"].nunique())),
            ui.Metric("Revenue", fmt.currency(stores_df["revenue"].sum(), 0)),
            ui.Metric("Orders", fmt.number(stores_df["orders"].sum())),
            ui.Metric("Late shipment", fmt.percent(stores_df["late_shipment_rate"].mean())),
        ]
    )

    col_left, col_right = st.columns(2)
    with col_left:
        st.plotly_chart(charts.bar(stores_df, "store_name", "revenue", title="Store revenue"), width="stretch")
    with col_right:
        st.plotly_chart(charts.bar(stores_df, "store_name", "average_order_value", title="Store AOV"), width="stretch")

    if not delivery.empty:
        delivery = delivery.copy()
        delivery["month"] = pd.to_datetime(delivery["month"])
        delivery_monthly = (
            delivery.groupby("month", dropna=False)
            .agg(
                orders=("orders", "sum"),
                shipped_orders=("shipped_orders", "sum"),
                avg_days_to_ship=("avg_days_to_ship", "mean"),
                late_shipment_rate=("late_shipment_rate", "mean"),
            )
            .reset_index()
        )
        st.subheader("Delivery trend")
        st.plotly_chart(
            charts.line(delivery_monthly, "month", "late_shipment_rate", "Late shipment by month"),
            width="stretch",
        )

    if not inventory.empty:
        st.subheader("Inventory health by store")
        inventory_status = (
            inventory.groupby(["store_name", "inventory_status"], dropna=False)
            .agg(rows=("product_id", "count"))
            .reset_index()
        )
        st.plotly_chart(
            charts.bar(inventory_status, "store_name", "rows", color="inventory_status", title="Inventory status mix"),
            width="stretch",
        )

    st.subheader("Store detail")
    ui.dataframe(stores_df, height=320)
