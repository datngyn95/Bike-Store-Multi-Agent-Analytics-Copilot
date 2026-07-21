from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def to_jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime, time)):
        return value.isoformat()
    return value


def normalize_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {key: to_jsonable(value) for key, value in row.items()}


def execute_rows(
    session: Session,
    sql: str,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    result = session.execute(text(sql), params or {})
    return [normalize_row(row) for row in result.mappings().all()]
