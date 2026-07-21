from __future__ import annotations

import streamlit as st

from components import charts, data, formatters as fmt, ui


def render() -> None:
    ui.page_title("Customers", "Customer segments, geo revenue va top customers.")

    customers, error = data.customer_segments()
    if not ui.require_data(customers, error):
        return

    segments = ["Tat ca", *sorted(customers["customer_segment"].dropna().unique())]
    with st.sidebar:
        st.markdown("#### Bo loc customers")
        selected_segment = st.selectbox("Segment", segments, key="customer_segment")

    filtered = customers if selected_segment == "Tat ca" else customers[customers["customer_segment"] == selected_segment]
    ui.metric_row(
        [
            ui.Metric("Customers", fmt.number(filtered["customer_id"].nunique())),
            ui.Metric("Revenue", fmt.currency(filtered["revenue"].sum(), 0)),
            ui.Metric("Orders", fmt.number(filtered["orders"].sum())),
            ui.Metric("Repeat customers", fmt.number((filtered["orders"] >= 2).sum())),
        ]
    )

    segment_df = (
        customers.groupby("customer_segment", dropna=False)
        .agg(customers=("customer_id", "count"), revenue=("revenue", "sum"), orders=("orders", "sum"))
        .reset_index()
    )
    state_df = (
        filtered.groupby("state", dropna=False)
        .agg(customers=("customer_id", "count"), revenue=("revenue", "sum"), orders=("orders", "sum"))
        .sort_values("revenue", ascending=False)
        .reset_index()
    )

    col_left, col_right = st.columns(2)
    with col_left:
        st.plotly_chart(charts.bar(segment_df, "customer_segment", "customers", title="Customer segments"), width="stretch")
    with col_right:
        st.plotly_chart(charts.bar(state_df.head(12), "state", "revenue", title="Revenue by state"), width="stretch")

    st.subheader("Top customers")
    ui.dataframe(
        filtered.head(25)[
            ["customer_name", "city", "state", "customer_segment", "orders", "units_sold", "revenue", "last_order_date"]
        ],
        height=460,
    )
