# 3. Build report: 10-wealth-management-rag-portal

**Status: completed**

Built a small Python sample that demonstrates a LlamaIndex-friendly RAG workflow backed by Azure DocumentDB vector search. The repo includes code to create collections/indexes, seed synthetic (or real if OPENAI_API_KEY is provided) embeddings into a research_documents collection, upsert portfolio documents, a simple RAG agent that combines portfolio context with retrieved research and calls an LLM (OpenAI by default), a FastAPI endpoint to query the agent, and unit tests. I verified dependency installation, unit tests, seeding the live cluster, vector index creation, and a demo query that returns retrieved docs and (simulated) answers.

## How to run

1) Create a Python virtualenv and install dependencies:
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2) Provide secrets via environment variables or .env file (see .env.example):
   - DOCUMENTDB_URI (required) — the Mongo connection string for the Azure DocumentDB cluster
   - OPENAI_API_KEY (optional) — to call OpenAI embeddings and chat for real embeddings/answers
   - (optional) OPENAI_EMBEDDING_MODEL, OPENAI_CHAT_MODEL

3) Seed the sample data (creates collections, vector index, and inserts documents):
   python scripts/seed.py

   - The seed script will use OPENAI_API_KEY to produce real embeddings if set; otherwise it generates synthetic normalized vectors and still creates the index and data.

4) Start the API server:
   uvicorn app:app --reload

5) Query the agent (example):
   curl -X POST "http://127.0.0.1:8000/query" -H "Content-Type: application/json" -d '{"client_id":"C123","question":"How is the client positioned for rising rates?"}'

6) Alternatively use the demo script to run a one-off query:
   python scripts/demo_query.py

7) Run tests:
   pytest -q

Cleanup: remove the database `sample_banking_10` from your cluster when done (use your preferred tooling or the documentdb MCP server).

## Verified by running

- pip install -r requirements.txt: exit code 0 (dependencies installed / already present in environment)
- pytest -q: 3 passed
- python scripts/seed.py: exit code 0 (created/ensured collections and inserted 30 research docs, upserted portfolios)
- documentdb_list_indexes (via MCP): research_documents indexes include 'research_embedding_hnsw' with cosmosSearchOptions kind=vector-hnsw, dimensions=1536, similarity=COS, maxDegree=32, lBuild=50
- python scripts/demo_query.py: exit code 0 — agent.answer_question executed, retrieved top-3 documents (scores returned), and simulated LLM answer returned; memory persisted to ./memory/<client_id>.txt

## Not verified

- End-to-end LLM responses using OpenAI (chat completions) were not validated in this run because OPENAI_API_KEY was not provided in the environment. The code path supports real OpenAI calls when OPENAI_API_KEY is set and will then generate real embeddings (seed) and real chat completions (agent).
- Full LlamaIndex-based Retriever integration: the sample is LlamaIndex-friendly and will attempt to import llama-index if present, but the sample's retrieval layer currently uses the DocumentDB vector search directly. I did not implement and verify a custom LlamaIndex Retriever class that calls DocumentDB; this is left as an exercise (the code comments indicate where to plug one).

## Open issues

- The sample uses a simulated LLM answer when OPENAI_API_KEY is not set. To exercise the real RAG path, set OPENAI_API_KEY in the environment and re-run scripts/seed.py (to compute real embeddings) and then query the API or run scripts/demo_query.py.
- A more complete LlamaIndex integration (implementing a custom Retriever that uses db.search_similar) would make the sample explicitly use LlamaIndex's query pipeline; I left a minimal fallback to keep the sample small and robust for environments without LLM keys.

## Files

- `requirements.txt`
- `README.md`
- `.env.example`
- `src/db.py`
- `src/agent.py`
- `app.py`
- `scripts/seed.py`
- `scripts/demo_query.py`
- `tests/test_db.py`
- `tests/test_seed.py`

