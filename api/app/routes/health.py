from __future__ import annotations

from fastapi import APIRouter, Query

from api.app.db import check_database_connection, has_configured_database_url
from api.app.schemas.health import HealthResponse


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(check_db: bool = Query(default=False)) -> HealthResponse:
    database_connected: bool | None = None
    error: str | None = None

    if check_db:
        database_connected, error = check_database_connection()

    return HealthResponse(
        status="ok" if error is None else "degraded",
        service="bike-store-api",
        database_url_configured=has_configured_database_url(),
        database_connected=database_connected,
        error=error,
    )
