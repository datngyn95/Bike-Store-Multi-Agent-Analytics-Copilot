from __future__ import annotations

import pandas as pd
import streamlit as st

from components import charts, data, formatters as fmt, ui


def render() -> None:
    ui.page_title("Data Quality", "Ket qua validation raw, staging va analytics.")

    results, source, error = data.data_quality_results()
    if error and source == "reports/data_quality_results.csv":
        st.warning("Audit query chua kha dung; dang doc report da sinh.")
    if not ui.require_data(results, None if not results.empty else error):
        return

    work = results.copy()
    work["checked_at"] = pd.to_datetime(work["checked_at"], errors="coerce")
    latest_run = work.sort_values("checked_at", ascending=False)["run_id"].iloc[0]
    latest = work[work["run_id"] == latest_run].copy()
    latest["status_norm"] = latest["status"].astype(str).str.lower()
    failed = latest[latest["status_norm"] != "pass"]
    pass_rate = (len(latest) - len(failed)) / max(len(latest), 1)

    ui.metric_row(
        [
            ui.Metric("Checks", fmt.number(len(latest))),
            ui.Metric("Failed", fmt.number(len(failed))),
            ui.Metric("Pass rate", fmt.percent(pass_rate)),
            ui.Metric("Source", source),
        ]
    )
    st.caption(f"Run ID: {latest_run}")

    category_df = (
        latest.groupby("category", dropna=False)
        .agg(checks=("check_name", "count"), failed=("status_norm", lambda values: (values != "pass").sum()))
        .reset_index()
    )
    status_df = latest.groupby("status_norm", dropna=False).agg(checks=("check_name", "count")).reset_index()

    col_left, col_right = st.columns(2)
    with col_left:
        st.plotly_chart(charts.bar(category_df, "category", "checks", title="Checks by category"), width="stretch")
    with col_right:
        st.plotly_chart(charts.pie(status_df, "status_norm", "checks", "Status mix"), width="stretch")

    st.subheader("Check results")
    ui.dataframe(
        latest[
            [
                "status",
                "check_name",
                "category",
                "severity",
                "issue_count",
                "max_allowed",
                "description",
            ]
        ],
        height=520,
    )
