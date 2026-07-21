from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from agents.graph_rag import (
    DEFAULT_EMBEDDING_DIMENSION,
    DEFAULT_GRAPH_DATA_DIR,
    ask_gemini_graph_rag,
    build_bike_store_graph,
    build_embedding_index_from_embeddings,
    embed_nodes,
    get_subgraph_context,
    hybrid_search_nodes,
    lexical_search_nodes,
    load_embedding_model,
    node_text,
    save_graph_data,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and query the Bike Store Graph RAG index.")
    parser.add_argument("--env-file", default=str(PROJECT_ROOT / ".env"), help="Path to .env file.")
    parser.add_argument("--data-dir", default=str(DEFAULT_GRAPH_DATA_DIR), help="Directory for graph.json, nodes.json and index.faiss.")
    parser.add_argument("--skip-embeddings", action="store_true", help="Build only graph.json/nodes.json, without FAISS index.")
    parser.add_argument("--question", default=None, help="Optional Vietnamese question to retrieve context for.")
    parser.add_argument("--ask-gemini", action="store_true", help="Ask Gemini using Graph RAG context. Requires valid GEMINI_API_KEY.")
    parser.add_argument("--top-k", type=int, default=8, help="Number of graph nodes to retrieve.")
    parser.add_argument(
        "--sync-pgvector",
        action="store_true",
        help="Upsert graph node embeddings into agent.rag_embeddings. Requires DATABASE_URL and seeded agent tables.",
    )
    return parser.parse_args()


def create_engine_from_env() -> Engine:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is missing. Add it to Bike_Store_Project/.env.")
    return create_engine(database_url, pool_pre_ping=True, future=True)


def _pgvector_literal(values) -> str:
    return "[" + ",".join(f"{float(value):.8f}" for value in values) + "]"


def _node_metadata(node: dict) -> str:
    metadata = {
        key: value
        for key, value in node.items()
        if key not in {"id", "type", "name", "description"}
    }
    return json.dumps(metadata, ensure_ascii=False)


def sync_pgvector_embeddings(engine: Engine, nodes: list[dict], embeddings) -> int:
    if len(nodes) != len(embeddings):
        raise RuntimeError("Node count and embedding count do not match.")

    if embeddings.shape[1] != DEFAULT_EMBEDDING_DIMENSION:
        raise RuntimeError(
            f"Embedding dimension {embeddings.shape[1]} does not match agent.rag_embeddings vector({DEFAULT_EMBEDDING_DIMENSION})."
        )

    upsert_sql = text(
        """
        insert into agent.rag_embeddings (
            node_id,
            node_type,
            node_name,
            source,
            content,
            metadata,
            embedding,
            updated_at
        )
        values (
            :node_id,
            :node_type,
            :node_name,
            :source,
            :content,
            cast(:metadata as jsonb),
            cast(:embedding as vector),
            now()
        )
        on conflict (node_id) do update set
            node_type = excluded.node_type,
            node_name = excluded.node_name,
            source = excluded.source,
            content = excluded.content,
            metadata = excluded.metadata,
            embedding = excluded.embedding,
            updated_at = now()
        """
    )

    with engine.begin() as conn:
        conn.exec_driver_sql("set local search_path = public, extensions, agent, analytics, staging, raw, audit")
        for node, embedding in zip(nodes, embeddings, strict=True):
            conn.execute(
                upsert_sql,
                {
                    "node_id": node["id"],
                    "node_type": node.get("type", "unknown"),
                    "node_name": node.get("name", node["id"]),
                    "source": node.get("source", "graph"),
                    "content": node_text(node),
                    "metadata": _node_metadata(node),
                    "embedding": _pgvector_literal(embedding),
                },
            )
    return len(nodes)


def main() -> None:
    args = parse_args()
    load_dotenv(args.env_file)

    graph, nodes = build_bike_store_graph(PROJECT_ROOT)
    index = None
    embed_model = None
    embeddings = None

    if not args.skip_embeddings:
        embed_model = load_embedding_model()
        embeddings = embed_nodes(nodes, embed_model)
        index = build_embedding_index_from_embeddings(embeddings)

    data_dir = Path(args.data_dir)
    if not data_dir.is_absolute():
        data_dir = (PROJECT_ROOT / data_dir).resolve()
    save_graph_data(graph, nodes, index=index, data_dir=data_dir)

    print(f"Graph nodes: {graph.number_of_nodes()}")
    print(f"Graph edges: {graph.number_of_edges()}")
    print(f"Graph data directory: {data_dir}")
    print(f"FAISS index: {'created' if index is not None else 'skipped'}")

    if args.sync_pgvector:
        if embeddings is None:
            raise RuntimeError("--sync-pgvector requires embeddings. Remove --skip-embeddings.")
        synced = sync_pgvector_embeddings(create_engine_from_env(), nodes, embeddings)
        print(f"pgvector rows upserted: {synced}")

    if args.question:
        if index is not None and embed_model is not None:
            results = hybrid_search_nodes(args.question, index, nodes, embed_model, top_k=args.top_k)
        else:
            results = lexical_search_nodes(args.question, nodes, top_k=args.top_k)

        context, relevant_node_ids = get_subgraph_context(graph, [result["id"] for result in results], depth=1)
        print(f"Retrieved nodes: {len(results)}")
        print(f"Relevant subgraph nodes: {len(relevant_node_ids)}")
        for result in results:
            print(f"- {result['id']} score={result.get('score')}")

        if args.ask_gemini:
            answer = ask_gemini_graph_rag(args.question, context)
            print("\nGemini answer:")
            print(answer)


if __name__ == "__main__":
    main()
