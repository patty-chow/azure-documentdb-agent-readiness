Drug Formulary Semantic Search (DocumentDB + LlamaIndex)

What this sample shows
- A small FastAPI service that stores drug formulary entries in an Azure DocumentDB (MongoDB-compatible) collection with embedded vectors.
- A /formulary-search endpoint that accepts a clinical intent string, embeds it, and returns the top-10 formulary matches ranked by vector similarity.

Prerequisites
- Python 3.11+ and pip
- An Azure DocumentDB cluster reachable from this machine. Set DOCUMENTDB_URI in your environment with the MongoDB connection string (do not put secrets into files).
- An OpenAI API key for embeddings (set OPENAI_API_KEY) or another embedding provider compatible with the code.

Quickstart
1. Create and activate a virtualenv, then install:
   pip install -r requirements.txt

2. Set environment variables (example):
   export DOCUMENTDB_URI="<your connection string>"
   export OPENAI_API_KEY="<your openai key>"

3. Seed sample data (idempotent upsert):
   python scripts/seed_data.py

4. Run a quick query demo (one-shot):
   python scripts/query_demo.py --query "patient with hypertension needing ACE inhibitor guidance"

5. Run the web service locally (development):
   uvicorn main:app --reload
   Then POST to http://127.0.0.1:8000/formulary-search with JSON {"query": "..."}

Notes and security
- The sample reads secrets from environment variables; never commit real keys.
- This sample is for demonstration and development only. Production considerations (private endpoints, RBAC, CMK, scaling, secure secret management) are out of scope.

Files created
- main.py: FastAPI app
- db.py: Mongo client singleton helper
- scripts/seed_data.py: Seed and upsert sample formulary entries with embeddings
- scripts/query_demo.py: One-shot query runner for verification
- requirements.txt
- .env.example

License: MIT (sample synthetic data)
