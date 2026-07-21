from __future__ import annotations

import os
from functools import lru_cache
from time import perf_counter
from typing import Any

from sqlalchemy.orm import Session

from agents.base_agent import GeminiClient, LLMClient
from agents.orchestrator import OrchestratorAgent
from api.app.schemas.copilot import CopilotGraphEvidence, CopilotResponse
from api.app.services.query_utils import execute_rows


def _configured_row_limit() -> int:
    raw_limit = os.getenv("COPILOT_SQL_ROW_LIMIT", "100").strip()
    try:
        return max(1, min(int(raw_limit), 500))
    except ValueError:
        return 100


def _configured_llm_provider() -> str:
    provider = (os.getenv("LLM_PROVIDER") or os.getenv("AI_PROVIDER") or "").strip().lower()
    if provider:
        return provider
    return "gemini" if os.getenv("GEMINI_API_KEY", "").strip() else ""


def _has_configured_gemini_key() -> bool:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    return bool(api_key) and "<" not in api_key


def _graph_evidence_enabled() -> bool:
    return os.getenv("COPILOT_GRAPH_EVIDENCE", "true").strip().lower() not in {"0", "false", "no", "off"}


@lru_cache(maxsize=1)
def _build_runtime_llm_client() -> LLMClient | None:
    if _configured_llm_provider() != "gemini" or not _has_configured_gemini_key():
        return None

    try:
        return GeminiClient()
    except RuntimeError:
        return None


@lru_cache(maxsize=1)
def _build_runtime_graph_rag() -> Any | None:
    if not _graph_evidence_enabled():
        return None

    try:
        from agents.graph_rag import BikeStoreGraphRAG, load_graph_data

        graph, nodes, _index = load_graph_data()
        if graph is not None and nodes is not None:
            return BikeStoreGraphRAG(graph=graph, nodes=nodes)
        return BikeStoreGraphRAG.from_project(build_embeddings=False)
    except Exception:
        return None


def _empty_graph_evidence() -> CopilotGraphEvidence:
    return CopilotGraphEvidence(nodes=[], edges=[])


def _graph_evidence_for_question(
    question: str,
    result: dict[str, Any],
    *,
    top_k: int = 8,
    max_nodes: int = 36,
    max_edges: int = 80,
) -> CopilotGraphEvidence:
    rag = _build_runtime_graph_rag()
    if rag is None:
        return _empty_graph_evidence()

    retrieval_query = " ".join(
        [
            question,
            " ".join(str(item) for item in result.get("agents", [])),
            " ".join(str(item) for item in result.get("metrics", [])),
            " ".join(str(item) for item in result.get("tables", [])),
        ]
    ).strip()

    try:
        _context, matches, relevant_node_ids = rag.retrieve(retrieval_query, top_k=top_k, depth=1)
    except Exception:
        return _empty_graph_evidence()

    matched_ids = [str(match["id"]) for match in matches if match.get("id")]
    matched_set = set(matched_ids)
    score_by_id = {str(match["id"]): float(match.get("score", 0.0)) for match in matches if match.get("id")}

    supporting_ids = sorted(str(node_id) for node_id in relevant_node_ids if str(node_id) not in matched_set)
    selected_ids = [node_id for node_id in matched_ids if node_id in relevant_node_ids]
    selected_ids.extend(supporting_ids)
    selected_ids = selected_ids[:max_nodes]
    selected_set = set(selected_ids)

    nodes = []
    for node_id in selected_ids:
        if not rag.graph.has_node(node_id):
            continue
        data = rag.graph.nodes[node_id]
        nodes.append(
            {
                "id": node_id,
                "label": str(data.get("name") or node_id),
                "type": str(data.get("type") or "unknown"),
                "source": str(data.get("source") or ""),
                "description": str(data.get("description") or ""),
                "score": score_by_id.get(node_id),
                "matched": node_id in matched_set,
            }
        )

    edges = []
    for source, target, data in rag.graph.edges(data=True):
        if source in selected_set and target in selected_set:
            edges.append(
                {
                    "source": str(source),
                    "target": str(target),
                    "type": str(data.get("type") or "related"),
                }
            )
        if len(edges) >= max_edges:
            break

    return CopilotGraphEvidence(nodes=nodes, edges=edges)


class CopilotService:
    def __init__(self, session: Session, orchestrator: OrchestratorAgent | None = None) -> None:
        self.session = session
        self.orchestrator = orchestrator or OrchestratorAgent.with_default_agents(
            llm_client=_build_runtime_llm_client()
        )

    def ask(self, question: str, *, limit: int | None = None) -> CopilotResponse:
        started_at = perf_counter()
        row_limit = limit or _configured_row_limit()
        result = self.orchestrator.ask(
            question,
            query_executor=self._execute_sql,
            row_limit=row_limit,
        )
        return CopilotResponse(
            answer=str(result.get("answer", "")),
            agents=list(result.get("agents", [])),
            sql=str(result.get("sql", "")),
            rows=list(result.get("rows", [])),
            metrics=list(result.get("metrics", [])),
            tables=list(result.get("tables", [])),
            graph=_graph_evidence_for_question(question, result),
            warnings=list(result.get("warnings", [])),
            latency_ms=self._latency_ms(started_at),
        )

    def _execute_sql(self, sql: str) -> list[dict[str, Any]]:
        return execute_rows(self.session, sql)

    @staticmethod
    def _latency_ms(started_at: float) -> int:
        return int((perf_counter() - started_at) * 1000)
