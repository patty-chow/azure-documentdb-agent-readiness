# Azure DocumentDB Regulatory Compliance RAG Checker

This sample demonstrates a small RAG (retrieval-augmented generation) workflow that:
- Stores regulatory clauses and internal policy documents as separate collections in an Azure DocumentDB (MongoDB-compatible) cluster
- Computes OpenAI embeddings for documents and stores them with each document
- Performs simple nearest-neighbour retrieval (brute-force cosine similarity) to find relevant regulatory clauses for a policy excerpt
- Produces a compliance gap report using the retrieved context and an LLM (OpenAI ChatCompletion)

The repository also includes an adapter showing how to wire LlamaIndex; the runtime demo uses direct OpenAI API calls so it can be run in this environment without requiring LlamaIndex API changes.

Prerequisites
- Python 3.10+ (the run environment provides Python 3.13)
- An Azure DocumentDB cluster reachable from this machine. Set its connection string in the environment variable DOCUMENTDB_URI
- An OpenAI API key in OPENAI_API_KEY (used for embeddings and chat completions)

Files
- src/db.py - MongoDB client and helpers
- src/seed.py - Seeds small synthetic regulatory and policy documents and computes embeddings
- src/app.py - CLI and small FastAPI analyze endpoint (a one-shot CLI run is used in verification)
- src/llama_index_adapter.py - Example adapter showing how you could wire LlamaIndex (optional)
- requirements.txt - pinned Python dependencies
- .env.example - example environment variable names

Security
- Never put real secrets into repository files. DOCUMENTDB_URI and OPENAI_API_KEY must come from environment variables.

Quickstart (local)
1. Install deps: python -m pip install -r requirements.txt
2. Export env vars:
   - export DOCUMENTDB_URI="<your connection string>"
   - export OPENAI_API_KEY="<your openai key>"
3. Seed sample data: python src/seed.py
4. Run the one-shot analyzer (CLI example):
   python src/app.py --analyze "Our policy requires multifactor authentication for all admin logins."

Notes and non-goals
- This is a developer sample designed for small datasets and experimentation. For production at scale, create a proper DocumentDB vector index (HNSW / DiskANN) using the documented createIndexes/runCommand pattern and perform server-side $search queries.
- The seed script uses a small synthetic dataset for demo purposes.

License: MIT
