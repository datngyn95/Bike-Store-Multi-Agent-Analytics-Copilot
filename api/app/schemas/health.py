from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    database_url_configured: bool
    database_connected: bool | None = None
    error: str | None = None
