Correspondent Banking Risk Screener (DocumentDB + LangChain sample)

Overview

This sample demonstrates:
- Embedding correspondent bank profiles and sanctions/adverse-media snippets with OpenAI embeddings
- Storing documents and embeddings in an Azure DocumentDB (MongoDB-compatible) cluster
- Performing similarity search locally (client-side) and returning matched entries
- Generating a plain-language risk narrative using a chat model (OpenAI)

Important constraints
- The sample uses the database name `sample_banking_11`. It must not touch other databases.
- The DocumentDB connection string must be provided via the DOCUMENTDB_URI environment variable.
- Do NOT commit real secrets. Use .env (see .env.example).

Quickstart

1. Create a virtual environment and install dependencies:
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   pip install -r requirements.txt

2. Set environment variables (see .env.example). The DocumentDB cluster must be reachable and the account must allow data-plane writes.

3. Seed the sample data (this will create collections and insert sample documents):
   python scripts/seed.py

4. Run the API:
   uvicorn src.main:app --reload

5. Call the review endpoint (example):
   POST /review with JSON {"correspondent_id": "c1"} or {"profile_text": "..."}

Notes and troubleshooting
- The sample computes vector similarity on the client using numpy to avoid depending on cluster-specific createIndex parameters. For production use, create a proper vector index on the server (HNSW/IVF/DiskANN) per the provider's docs.
- If seed.py fails to create a vector index on the server, the script still uploads documents and embeddings; see its output for warnings.

Files
- src/: application code
- scripts/seed.py: idempotent data loader
- data/: sample JSON documents
- tests/: unit tests (use pytest)

License: MIT
