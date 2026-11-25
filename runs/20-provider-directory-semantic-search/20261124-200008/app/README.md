Provider Directory Semantic Search sample

This sample shows how to store provider profiles in Azure DocumentDB with embedded vectors and run semantic search via the cosmosSearch vector index. It implements a small FastAPI service with a /find-provider endpoint that accepts plain-language patient requests and returns ranked provider matches.

Prerequisites
- Python 3.10+ (python and pip point to a virtualenv)
- DOCUMENTDB_URI environment variable set to your cluster connection string
- (Optional) OPENAI_API_KEY for real embeddings; if omitted the sample uses a deterministic fallback embedding generator

Quickstart
1. pip install -r requirements.txt
2. cp .env.example .env and set DOCUMENTDB_URI (and OPENAI_API_KEY if available)
3. python seed.py    # creates collection, vector index, and loads sample data
4. python query_demo.py "Spanish-speaking cardiologist accepting Medicare" 5   # run a demo query
5. uvicorn app.main:app --reload   # start the API server

Files
- app/: FastAPI app and DB helper
- seed.py: create index and load sample documents
- data/providers.json: sample provider records
- query_demo.py: run a single-shot query against the DB

Notes
- The sample uses an HNSW vector index (vector-hnsw) with 1536-d vectors (text-embedding-3-small). The seed script will create the index via the createIndexes command.
- No Azure control-plane changes are made; the sample uses the existing cluster pointed at by DOCUMENTDB_URI.
