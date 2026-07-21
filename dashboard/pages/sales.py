from __future__ import annotations

import pandas as pd
import streamlit as st

from components import charts, data, formatters as fmt, ui


def render() -> None:
    ui.page_title("Sales", "Revenue, order volume, AOV, discount va delivery trend.")

    monthly, monthly_error = data.sales_monthly()
    stores_df, stores_error = data.sales_by_store()
    delivery, delivery_error = data.delivery_performance()
    if not ui.require_data(monthly, monthly_error):
        return
    ui.show_query_issue(stores_error or delivery_error)

    monthly = monthly.copy()
    monthly["month"] = pd.to_datetime(monthly["month"])
    years = ["Tat ca", *[str(year) for year in sorted(monthly["year"].dropna().unique())]]
    with st.sidebar:
        st.markdown("#### Bo loc sales")
        selected_year = st.selectbox("Nam", years, key="sales_year")

    filtered = monthly if selected_year == "Tat ca" else monthly[monthly["year"].astype(str) == selected_year]
    ui.metric_row(
        [
            ui.Metric("Revenue", fmt.currency(filtered["revenue"].sum(), 0)),
            ui.Metric("Orders", fmt.number(filtered["orders"].sum())),
            ui.Metric("Units sold", fmt.number(filtered["units_sold"].sum())),
            ui.Metric("AOV", fmt.currency(filtered["revenue"].sum() / max(filtered["orders"].sum(), 1), 0)),
            ui.Metric("Discount", fmt.percent(filtered["discount_amount"].sum() / max(filtered["gross_sales"].sum(), 1))),
        ]
    )

    col_left, col_right = st.columns(2)
    with col_left:
        st.plotly_chart(charts.line(filtered, "month", "revenue", "Revenue trend"), width="stretch")
    with col_right:
        st.plotly_chart(charts.line(filtered, "month", "average_order_value", "AOV trend"), width="stretch")

    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Store sales")
        if not stores_df.empty:
            st.plotly_chart(charts.bar(stores_df, "store_name", "revenue", title="Revenue by store"), width="stretch")
            ui.dataframe(stores_df, height=300)
    with col_right:
        st.subheader("Delivery")
        if not delivery.empty:
            delivery = delivery.copy()
            delivery["month"] = pd.to_datetime(delivery["month"])
            if selected_year != "Tat ca":
                delivery = delivery[delivery["month"].dt.year.astype(str) == selected_year]
            store_delivery = (
                delivery.groupby("store_name", dropna=False)
                .agg(orders=("orders", "sum"), avg_days_to_ship=("avg_days_to_ship", "mean"), late_shipment_rate=("late_shipment_rate", "mean"))
                .reset_index()
            )
            st.plotly_chart(
                charts.bar(store_delivery, "store_name", "late_shipment_rate", title="Late shipment rate"),
                width="stretch",
            )
            ui.dataframe(store_delivery, height=300)

    st.subheader("Monthly detail")
    ui.dataframe(filtered, height=360)
