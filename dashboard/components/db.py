from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import Engine
except ModuleNotFoundError as exc:  # pragma: no cover - environment guidance for Streamlit.
    create_engine = None
    text = None
    Engine = object
    SQLALCHEMY_IMPORT_ERROR = exc
else:
    SQLALCHEMY_IMPORT_ERROR = None


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "y", "on"}


def database_url() -> str:
    return os.getenv("DATABASE_URL", "").strip()


def has_configured_database_url() -> bool:
    url = database_url()
    return bool(url) and "<" not in url


@st.cache_resource(show_spinner=False)
def get_engine() -> Engine:
    if SQLALCHEMY_IMPORT_ERROR is not None:
        raise RuntimeError(
            "Thieu package SQLAlchemy trong Python environment dang chay Streamlit. "
            "Chay: python -m pip install -r requirements.txt, sau do start lai bang "
            "python -m streamlit run dashboard/streamlit_app.py --server.port 8501."
        ) from SQLALCHEMY_IMPORT_ERROR
    url = database_url()
    if not has_configured_database_url():
        raise RuntimeError(
            "DATABASE_URL chua duoc cau hinh. Hay dien chuoi ket noi Supabase Postgres trong .env."
        )
    return create_engine(url, pool_pre_ping=True, pool_recycle=300)


@st.cache_data(ttl=300, show_spinner=False)
def query_df(sql: str, params: dict[str, object] | None = None) -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as connection:
        return pd.read_sql_query(text(sql), connection, params=params or {})


def try_query_df(sql: str, params: dict[str, object] | None = None) -> tuple[pd.DataFrame, str | None]:
    try:
        return query_df(sql, params), None
    except Exception as exc:  # pragma: no cover - UI reports the database error.
        return pd.DataFrame(), str(exc)


def clear_query_cache() -> None:
    query_df.clear()
