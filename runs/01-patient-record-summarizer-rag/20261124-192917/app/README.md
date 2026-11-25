Patient Record Summarizer (RAG) — Azure DocumentDB sample

This sample demonstrates storing chunked patient records in an Azure DocumentDB collection with vector embeddings and performing a retrieval-augmented clinical summary (RAG).

What this sample shows
- Ingest pseudonymized patient records as chunked documents with fields: patientId, sourceDocId, chunkId, text, embedding, schemaVersion.
- Create a cosmosSearch vector index (HNSW) on the embedding field with dimensions matching the embedding model.
- Query for relevant chunks with a vector KNN search pre-filtered by patientId and produce a grounded clinical summary.

Prerequisites
- Python 3.10+ (python on PATH)
- A reachable Azure DocumentDB cluster. Set DOCUMENTDB_URI in .env (copy .env.example -> .env).
- (Optional) OPENAI_API_KEY to generate real embeddings; otherwise the seed script generates deterministic synthetic embeddings.

Setup
1. python -m venv .venv
2. source .venv/bin/activate  # or .venv\Scripts\activate on Windows
3. pip install -r requirements.txt
4. cp .env.example .env and fill DOCUMENTDB_URI (and OPENAI_API_KEY if you want real embeddings)

Files
- scripts/seed.py — idempotent seeding of synthetic patient data (10 patients x ~5 chunks each). Generates embeddings via OpenAI if OPENAI_API_KEY present, else deterministic random vectors.
- scripts/query.py — example retrieval for a given patientId and question; prints top chunks with similarity scores and a simple OpenAI-based summary.
- src/db.py — MongoClient singleton helper.
- src/app.py — optional FastAPI app exposing POST /search (not started automatically by the tests).

Security
- Never commit your DOCUMENTDB_URI or API keys. Use environment variables as shown.

Notes and limitations
- This is a sample only. Do not use for PHI or production clinical workflows without proper compliance.
- The sample tries to create a vector index using the DocumentDB MCP tool; if that fails you can create the index manually via the Azure CLI or portal.

License: MIT
