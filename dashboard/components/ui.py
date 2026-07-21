from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import pandas as pd
import streamlit as st


@dataclass(frozen=True)
class Metric:
    label: str
    value: str
    delta: str | None = None


def configure_page() -> None:
    st.set_page_config(
        page_title="Bike Store Analytics",
        page_icon=":bar_chart:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        :root {
            --bike-accent: #0f8b8d;
            --bike-accent-2: #e36414;
            --bike-success: #2f855a;
            --bike-warning: #b7791f;
            --bike-danger: #c53030;
            --bike-ink: #202124;
            --bike-muted: #667085;
            --bike-line: #e5e7eb;
        }
        .block-container {
            padding-top: 1.25rem;
            padding-bottom: 2.5rem;
        }
        [data-testid="stSidebar"] {
            border-right: 1px solid var(--bike-line);
        }
        [data-testid="stMetric"] {
            border: 1px solid var(--bike-line);
            border-radius: 8px;
            padding: 0.85rem 0.95rem;
            background: #ffffff;
        }
        [data-testid="stMetricLabel"] p {
            color: var(--bike-muted);
            font-size: 0.82rem;
        }
        h1, h2, h3 {
            letter-spacing: 0;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--bike-line);
            border-radius: 8px;
            overflow: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_title(title: str, subtitle: str | None = None) -> None:
    st.title(title)
    if subtitle:
        st.caption(subtitle)


def metric_row(metrics: Iterable[Metric]) -> None:
    metric_list = list(metrics)
    if not metric_list:
        return
    columns = st.columns(len(metric_list))
    for column, metric in zip(columns, metric_list, strict=True):
        column.metric(metric.label, metric.value, metric.delta)


def show_query_issue(error: str | None) -> None:
    if error:
        st.warning(error)


def require_data(df: pd.DataFrame, error: str | None = None) -> bool:
    if error:
        st.error(error)
        return False
    if df.empty:
        st.info("Chua co du lieu cho man hinh nay.")
        return False
    return True


def dataframe(df: pd.DataFrame, height: int = 420) -> None:
    st.dataframe(df, width="stretch", hide_index=True, height=height)
