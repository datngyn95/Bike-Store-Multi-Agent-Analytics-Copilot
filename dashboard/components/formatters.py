from __future__ import annotations

import math
from typing import Any

import pandas as pd


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except TypeError:
        return False


def number(value: Any, digits: int = 0) -> str:
    if _is_missing(value):
        return "-"
    numeric = float(value)
    if math.isclose(numeric, round(numeric)):
        return f"{numeric:,.0f}"
    return f"{numeric:,.{digits}f}"


def currency(value: Any, digits: int = 0) -> str:
    if _is_missing(value):
        return "-"
    return f"${float(value):,.{digits}f}"


def percent(value: Any, digits: int = 1) -> str:
    if _is_missing(value):
        return "-"
    return f"{float(value) * 100:,.{digits}f}%"


def compact_date(value: Any) -> str:
    if _is_missing(value):
        return "-"
    return pd.to_datetime(value).strftime("%Y-%m-%d")
