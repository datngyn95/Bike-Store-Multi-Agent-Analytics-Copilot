# Sprint 7 RAG Metadata

Sprint 7 adds graph metadata and a Supabase pgvector store for the Vietnamese analytics copilot.

## Graph Nodes

`agents/graph_rag.py` builds a NetworkX graph from:

- project schemas: `raw`, `staging`, `analytics`, `agent`, `audit`
- SQL views in `sql/`
- domain agents and orchestrator agent
- metric catalog definitions
- SQL templates
- Vietnamese question examples
- data quality report source

Local graph artifacts are written to:

```text
graph_data/graph.json
graph_data/nodes.json
graph_data/index.faiss
```

## Supabase pgvector Store

DDL:

```text
sql/agent/010_agent_metadata_tables.sql
```

Vector table:

```text
agent.rag_embeddings
```

The table stores one embedding per graph node with:

- `node_id`
- `node_type`
- `node_name`
- `source`
- `content`
- `metadata`
- `embedding vector(384)`

It uses an HNSW cosine index for vector search.

## Commands

Seed metadata tables:

```powershell
python scripts/seed_agent_metadata.py
```

Build local graph and FAISS index:

```powershell
python scripts/build_rag_index.py
```

Build local graph and sync embeddings to Supabase:

```powershell
python scripts/build_rag_index.py --sync-pgvector
```

Retrieve context without embeddings:

```powershell
python scripts/build_rag_index.py --skip-embeddings --question "Metric revenue duoc dinh nghia nhu the nao?"
```

Ask Gemini with graph context:

```powershell
python scripts/build_rag_index.py --question "Cua hang nao co doanh thu cao nhat?" --ask-gemini
```

## Notes

`--sync-pgvector` requires:

- `DATABASE_URL` in `.env`
- `agent` metadata tables already seeded
- local FastEmbed model available or network access to download it

The default embedding model is `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, which produces 384-dimensional embeddings to match `agent.rag_embeddings.embedding`.
