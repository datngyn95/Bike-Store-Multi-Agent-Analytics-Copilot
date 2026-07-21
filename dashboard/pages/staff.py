from __future__ import annotations

import streamlit as st

from components import charts, data, formatters as fmt, ui


def render() -> None:
    ui.page_title("Staff", "Staff revenue, orders, AOV va manager performance.")

    staff_df, error = data.staff_performance()
    if not ui.require_data(staff_df, error):
        return

    stores = ["Tat ca", *sorted(staff_df["store_name"].dropna().unique())]
    with st.sidebar:
        st.markdown("#### Bo loc staff")
        selected_store = st.selectbox("Store", stores, key="staff_store")

    filtered = staff_df if selected_store == "Tat ca" else staff_df[staff_df["store_name"] == selected_store]
    ui.metric_row(
        [
            ui.Metric("Staff", fmt.number(filtered["staff_id"].nunique())),
            ui.Metric("Revenue", fmt.currency(filtered["revenue"].sum(), 0)),
            ui.Metric("Orders", fmt.number(filtered["orders"].sum())),
            ui.Metric("AOV", fmt.currency(filtered["revenue"].sum() / max(filtered["orders"].sum(), 1), 0)),
        ]
    )

    manager_df = (
        filtered.groupby("manager_name", dropna=False)
        .agg(staff=("staff_id", "count"), revenue=("revenue", "sum"), orders=("orders", "sum"))
        .sort_values("revenue", ascending=False)
        .reset_index()
    )

    col_left, col_right = st.columns(2)
    with col_left:
        st.plotly_chart(charts.bar(filtered, "staff_name", "revenue", title="Revenue by staff"), width="stretch")
    with col_right:
        st.plotly_chart(charts.bar(manager_df, "manager_name", "revenue", title="Revenue by manager"), width="stretch")

    st.subheader("Staff detail")
    ui.dataframe(
        filtered[
            [
                "staff_name",
                "store_name",
                "manager_name",
                "orders",
                "customers",
                "units_sold",
                "revenue",
                "average_order_value",
                "late_shipment_rate",
            ]
        ],
        height=420,
    )
