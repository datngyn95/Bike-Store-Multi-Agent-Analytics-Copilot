from __future__ import annotations

import pandas as pd
import plotly.express as px


COLOR_SEQUENCE = ["#0f8b8d", "#e36414", "#2f855a", "#6b7280", "#b7791f", "#805ad5"]


def line(df: pd.DataFrame, x: str, y: str, title: str | None = None):
    fig = px.line(df, x=x, y=y, markers=True, title=title, color_discrete_sequence=COLOR_SEQUENCE)
    fig.update_layout(margin=dict(l=8, r=8, t=42 if title else 10, b=8), hovermode="x unified")
    return fig


def bar(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str | None = None,
    color: str | None = None,
    orientation: str = "v",
):
    fig = px.bar(
        df,
        x=x,
        y=y,
        color=color,
        title=title,
        orientation=orientation,
        color_discrete_sequence=COLOR_SEQUENCE,
    )
    fig.update_layout(margin=dict(l=8, r=8, t=42 if title else 10, b=8), legend_title_text="")
    return fig


def pie(df: pd.DataFrame, names: str, values: str, title: str | None = None):
    fig = px.pie(df, names=names, values=values, title=title, color_discrete_sequence=COLOR_SEQUENCE)
    fig.update_layout(margin=dict(l=8, r=8, t=42 if title else 10, b=8), legend_title_text="")
    return fig
