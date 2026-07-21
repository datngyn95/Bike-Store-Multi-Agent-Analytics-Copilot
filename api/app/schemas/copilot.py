from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CopilotRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    limit: int | None = Field(default=None, ge=1, le=500)


class CopilotGraphNode(BaseModel):
    id: str
    label: str
    type: str = "unknown"
    source: str = ""
    description: str = ""
    score: float | None = None
    matched: bool = False


class CopilotGraphEdge(BaseModel):
    source: str
    target: str
    type: str = "related"


class CopilotGraphEvidence(BaseModel):
    nodes: list[CopilotGraphNode] = Field(default_factory=list)
    edges: list[CopilotGraphEdge] = Field(default_factory=list)


class CopilotResponse(BaseModel):
    answer: str
    agents: list[str] = Field(default_factory=list)
    sql: str = ""
    rows: list[dict[str, Any]] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    tables: list[str] = Field(default_factory=list)
    graph: CopilotGraphEvidence = Field(default_factory=CopilotGraphEvidence)
    warnings: list[str] = Field(default_factory=list)
    latency_ms: int
