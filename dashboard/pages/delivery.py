from __future__ import annotations

import pandas as pd
import streamlit as st

from components import charts, data, formatters as fmt, ui


def render() -> None:
    ui.page_title("Delivery", "Shipping volume, average days to ship va late shipment rate.")

    delivery, error = data.delivery_performance()
    if not ui.require_data(delivery, error):
        return

    delivery = delivery.copy()
    delivery["month"] = pd.to_datetime(delivery["month"])
    stores = ["Tat ca", *sorted(delivery["store_name"].dropna().unique())]
    with st.sidebar:
        st.markdown("#### Bo loc delivery")
        selected_store = st.selectbox("Store", stores, key="delivery_store")

    filtered = delivery if selected_store == "Tat ca" else delivery[delivery["store_name"] == selected_store]
    shipped_orders = filtered["shipped_orders"].sum()
    weighted_days = (
        (filtered["avg_days_to_ship"].fillna(0) * filtered["shipped_orders"]).sum() / max(shipped_orders, 1)
    )
    weighted_late_rate = (
        (filtered["late_shipment_rate"].fillna(0) * filtered["shipped_orders"]).sum() / max(shipped_orders, 1)
    )

    ui.metric_row(
        [
            ui.Metric("Orders", fmt.number(filtered["orders"].sum())),
            ui.Metric("Shipped", fmt.number(shipped_orders)),
            ui.Metric("Avg days to ship", fmt.number(weighted_days, 2)),
            ui.Metric("Late shipment", fmt.percent(weighted_late_rate)),
        ]
    )

    monthly = (
        filtered.groupby("month", dropna=False)
        .agg(
            orders=("orders", "sum"),
            shipped_orders=("shipped_orders", "sum"),
            avg_days_to_ship=("avg_days_to_ship", "mean"),
            late_shipment_rate=("late_shipment_rate", "mean"),
        )
        .reset_index()
    )
    store_delivery = (
        filtered.groupby("store_name", dropna=False)
        .agg(
            orders=("orders", "sum"),
            shipped_orders=("shipped_orders", "sum"),
            avg_days_to_ship=("avg_days_to_ship", "mean"),
            late_shipment_rate=("late_shipment_rate", "mean"),
        )
        .sort_values("late_shipment_rate", ascending=False)
        .reset_index()
    )

    col_left, col_right = st.columns(2)
    with col_left:
        st.plotly_chart(charts.line(monthly, "month", "late_shipment_rate", "Late shipment trend"), width="stretch")
    with col_right:
        st.plotly_chart(charts.bar(store_delivery, "store_name", "late_shipment_rate", "Late shipment by store"), width="stretch")

    col_left, col_right = st.columns(2)
    with col_left:
        st.plotly_chart(charts.bar(store_delivery, "store_name", "shipped_orders", "Shipped orders by store"), width="stretch")
    with col_right:
        st.plotly_chart(charts.bar(store_delivery, "store_name", "avg_days_to_ship", "Average days to ship"), width="stretch")

    st.subheader("Delivery detail")
    ui.dataframe(
        filtered[
            [
                "month",
                "store_name",
                "orders",
                "shipped_orders",
                "avg_days_to_ship",
                "late_shipment_rate",
            ]
        ],
        height=480,
    )
