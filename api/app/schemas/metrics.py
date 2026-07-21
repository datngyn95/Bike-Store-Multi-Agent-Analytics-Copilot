from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SalesSummaryResponse(BaseModel):
    source: str
    metrics: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class MetricsResponse(BaseModel):
    source: str
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int
    warnings: list[str] = Field(default_factory=list)
