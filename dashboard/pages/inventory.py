from __future__ import annotations

import streamlit as st

from components import charts, data, formatters as fmt, ui


RISK_STATUSES = ["stockout", "stockout_risk", "overstock_risk"]


def render() -> None:
    ui.page_title("Inventory", "Stock status, velocity, days of supply va inventory value.")

    inventory, error = data.inventory_risk()
    if not ui.require_data(inventory, error):
        return

    statuses = ["Tat ca", *sorted(inventory["inventory_status"].dropna().unique())]
    stores = ["Tat ca", *sorted(inventory["store_name"].dropna().unique())]
    with st.sidebar:
        st.markdown("#### Bo loc inventory")
        selected_status = st.selectbox("Status", statuses, key="inventory_status")
        selected_store = st.selectbox("Store", stores, key="inventory_store")

    filtered = inventory.copy()
    if selected_status != "Tat ca":
        filtered = filtered[filtered["inventory_status"] == selected_status]
    if selected_store != "Tat ca":
        filtered = filtered[filtered["store_name"] == selected_store]

    risk_count = filtered[filtered["inventory_status"].isin(RISK_STATUSES)]["product_id"].count()
    ui.metric_row(
        [
            ui.Metric("Store-product rows", fmt.number(len(filtered))),
            ui.Metric("Risk rows", fmt.number(risk_count)),
            ui.Metric("Stock quantity", fmt.number(filtered["stock_quantity"].sum())),
            ui.Metric("Inventory value", fmt.currency(filtered["inventory_value"].sum(), 0)),
        ]
    )

    status_df = (
        filtered.groupby("inventory_status", dropna=False)
        .agg(rows=("product_id", "count"), inventory_value=("inventory_value", "sum"), stock_quantity=("stock_quantity", "sum"))
        .reset_index()
    )
    store_df = (
        filtered.groupby("store_name", dropna=False)
        .agg(rows=("product_id", "count"), inventory_value=("inventory_value", "sum"), stock_quantity=("stock_quantity", "sum"))
        .sort_values("inventory_value", ascending=False)
        .reset_index()
    )

    col_left, col_right = st.columns(2)
    with col_left:
        st.plotly_chart(charts.bar(status_df, "inventory_status", "rows", title="Rows by inventory status"), width="stretch")
    with col_right:
        st.plotly_chart(charts.bar(store_df, "store_name", "inventory_value", title="Inventory value by store"), width="stretch")

    st.subheader("Inventory risk detail")
    ui.dataframe(
        filtered.head(100)[
            [
                "store_name",
                "product_name",
                "brand_name",
                "category_name",
                "stock_quantity",
                "units_sold_90d",
                "daily_sales_velocity",
                "days_of_supply",
                "inventory_value",
                "inventory_status",
            ]
        ],
        height=520,
    )
