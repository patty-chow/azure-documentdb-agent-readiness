# Regulatory Compliance RAG Checker (Azure DocumentDB sample)

This sample demonstrates a small Retrieval-Augmented Generation (RAG) workflow using Azure DocumentDB (MongoDB-compatible) as the backing store for two collections: `regulations` and `policies`.

It includes:
- Seed script to insert a tiny synthetic dataset.
- Vector-index creation (DocumentDB vector index) via the DocumentDB MCP server.
- A simple CLI and a FastAPI POST /analyze endpoint that accepts a policy excerpt and returns a compliance-gap report.

Prerequisites
- Python 3.10+ (this environment uses Python 3.13).
- An existing Azure DocumentDB cluster reachable from this machine. Put its connection string in the environment variable `DOCUMENTDB_URI`.
- (Optional) OpenAI API key in `OPENAI_API_KEY` for embeddings and LLM summarization.

Files of interest
- src/db.py: MongoDB connection helper (singleton MongoClient).
- src/seed.py: Insert sample regulations and policies and compute embeddings (if OPENAI_API_KEY provided).
- src/analyze.py: CLI entry for analysis.
- src/app.py: FastAPI app exposing POST /analyze.
- scripts/create_indexes.py: Uses the DocumentDB MCP server to create the vector and textSearch indexes (no control-plane changes).
- .env.example: example env vars to set locally.

Quickstart

1. Create and activate a virtualenv, then install dependencies:

   python -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   .\.venv\Scripts\activate  # Windows
   pip install -r requirements.txt

2. Populate env vars (example):

   export DOCUMENTDB_URI="[USER]:[PASSWORD]@[CLUSTER_URI]"  # see .env.example
   export OPENAI_API_KEY="sk-..."  # optional

3. Seed sample data (inserts documents; embeddings computed if OPENAI_API_KEY present):

   python src/seed.py

4. Create DocumentDB indexes (uses the local documentdb MCP server `default` profile for data-plane operations):

   python scripts/create_indexes.py

5. Run the CLI to analyze an excerpt:

   python -m src.analyze "We require encryption of customer data at rest and in motion..."

6. Run the FastAPI app and POST /analyze:

   uvicorn src.app:app --reload --port 8000
   curl -X POST localhost:8000/analyze -H "Content-Type: application/json" -d '{"excerpt":"..."}'

Cleanup
- Delete the sample documents from the `sample_fintech_08` database using your preferred MongoDB admin tool, or drop the database.

Security notes
- Do not commit real secrets. This repo uses environment variables and provides `.env.example` for placeholders.
- This is a demo only. Do not assume production-grade authentication, private endpoints, CMK or RBAC configuration.

License: MIT
