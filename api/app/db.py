from __future__ import annotations

import os
from collections.abc import Generator
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


class ApiConfigError(RuntimeError):
    """Raised when API runtime configuration is missing or invalid."""


def database_url() -> str:
    return os.getenv("DATABASE_URL", "").strip()


def has_configured_database_url() -> bool:
    url = database_url()
    return bool(url) and "<" not in url


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    if not has_configured_database_url():
        raise ApiConfigError("DATABASE_URL chua duoc cau hinh cho FastAPI service.")
    return create_engine(database_url(), pool_pre_ping=True, pool_recycle=300)


@lru_cache(maxsize=1)
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(
        bind=get_engine(),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


def get_session() -> Generator[Session, None, None]:
    session = get_sessionmaker()()
    try:
        yield session
    finally:
        session.close()


def check_database_connection() -> tuple[bool, str | None]:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("select 1"))
    except Exception as exc:  # pragma: no cover - depends on local Supabase access.
        return False, str(exc)
    return True, None
