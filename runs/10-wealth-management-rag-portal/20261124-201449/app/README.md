Wealth Management RAG Portal (DocumentDB + LlamaIndex sample)

This sample demonstrates:
- Indexing wealth-management research documents into an Azure DocumentDB (Mongo-compatible) collection with vector embeddings.
- Creating a native vector index (cosmosSearch / vector-hnsw) on the collection.
- A simple RAG agent that fetches a client's portfolio, retrieves relevant research via vector search, and answers Relationship Manager questions using an LLM. The agent supports lightweight memory per client (conversation history file).

Prerequisites
- A reachable Azure DocumentDB cluster (Mongo wire protocol) and its connection string available in DOCUMENTDB_URI environment variable.
- (Optional for real embeddings/LLM) OPENAI_API_KEY set to call OpenAI embeddings and chat models. If not provided, the seed script will generate synthetic random embeddings so the sample remains runnable.

Important: Do NOT commit secrets. Use .env or environment variables.

Files
- src/db.py - Database helpers: connect, create index, seed helpers, search.
- scripts/seed.py - Seed research documents and portfolio samples (idempotent upserts). Uses OPENAI_API_KEY if present, otherwise creates synthetic embeddings.
- src/agent.py - A small RAG agent that combines portfolio context with retrieved docs and calls an LLM (OpenAI by default). It attempts to use LlamaIndex if installed but falls back to a direct prompt-based RAG flow.
- app.py - FastAPI app exposing /query endpoint to ask questions.
- .env.example - Example environment variables to set.
- requirements.txt - Python dependencies.

How to run (local developer machine)
1) Create a virtualenv and install dependencies
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2) Populate env vars (create .env from .env.example) and set DOCUMENTDB_URI. Optionally set OPENAI_API_KEY.

3) Seed the sample data (creates collections, index, and inserts documents)
   python scripts/seed.py

4) Start the API
   uvicorn app:app --reload

5) Query the agent (example)
   curl -X POST "http://127.0.0.1:8000/query" -H "Content-Type: application/json" -d '{"client_id":"C123","question":"How is the client positioned for rising rates?"}'

Cleanup
- Delete the `sample_banking_10` database from your cluster (use mongosh or the MCP server tools) when done.

Security & Production Notes
- This sample uses secrets from environment variables. For production, prefer managed identity / Entra ID and private endpoints.
- Vector index parameters are tuned for a small sample; production should follow guidance in the documentdb-vector-search skill.

References
- documentdb-vector-search (skill)
- documentdb-indexing (skill)
