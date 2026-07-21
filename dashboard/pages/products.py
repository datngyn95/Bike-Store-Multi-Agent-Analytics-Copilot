from __future__ import annotations

import streamlit as st

from components import charts, data, formatters as fmt, ui


def render() -> None:
    ui.page_title("Products", "Product, brand, category performance va discount.")

    products, error = data.product_performance()
    if not ui.require_data(products, error):
        return

    categories = ["Tat ca", *sorted(products["category_name"].dropna().unique())]
    brands = ["Tat ca", *sorted(products["brand_name"].dropna().unique())]
    with st.sidebar:
        st.markdown("#### Bo loc products")
        selected_category = st.selectbox("Category", categories, key="product_category")
        selected_brand = st.selectbox("Brand", brands, key="product_brand")

    filtered = products.copy()
    if selected_category != "Tat ca":
        filtered = filtered[filtered["category_name"] == selected_category]
    if selected_brand != "Tat ca":
        filtered = filtered[filtered["brand_name"] == selected_brand]

    ui.metric_row(
        [
            ui.Metric("Products", fmt.number(filtered["product_id"].nunique())),
            ui.Metric("Revenue", fmt.currency(filtered["revenue"].sum(), 0)),
            ui.Metric("Units sold", fmt.number(filtered["units_sold"].sum())),
            ui.Metric("Avg selling price", fmt.currency(filtered["revenue"].sum() / max(filtered["units_sold"].sum(), 1), 0)),
        ]
    )

    category_df = (
        filtered.groupby("category_name", dropna=False)
        .agg(revenue=("revenue", "sum"), units_sold=("units_sold", "sum"), products=("product_id", "count"))
        .sort_values("revenue", ascending=False)
        .reset_index()
    )
    brand_df = (
        filtered.groupby("brand_name", dropna=False)
        .agg(revenue=("revenue", "sum"), units_sold=("units_sold", "sum"), products=("product_id", "count"))
        .sort_values("revenue", ascending=False)
        .reset_index()
    )

    col_left, col_right = st.columns(2)
    with col_left:
        st.plotly_chart(charts.bar(category_df, "category_name", "revenue", title="Revenue by category"), width="stretch")
    with col_right:
        st.plotly_chart(charts.bar(brand_df.head(12), "brand_name", "revenue", title="Revenue by brand"), width="stretch")

    st.subheader("Product detail")
    ui.dataframe(
        filtered.head(50)[
            [
                "product_name",
                "brand_name",
                "category_name",
                "model_year",
                "orders",
                "units_sold",
                "revenue",
                "avg_selling_price",
                "discount_rate",
            ]
        ],
        height=500,
    )
