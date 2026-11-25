# Sanctions Screening Agent (Azure DocumentDB sample)

This sample demonstrates a Python LangChain-style sanctions-list screening agent that stores sanctions entries with embeddings in an Azure DocumentDB collection and performs combined vector + regex screening.

What it shows
- How to read DocumentDB connection string from DOCUMENTDB_URI
- How to seed a small synthetic sanctions dataset, compute embeddings (OpenAI), and store them in DocumentDB
- How to create a DocumentDB vector index (HNSW) for embeddings (assistant will create this during verification)
- A FastAPI `/screen` endpoint that runs a vector search via `$search` + `cosmosSearch` and a regex-based fuzzy search, consolidates results and produces a structured screening report

Prerequisites
- Python 3.11 (venv recommended)
- A reachable Azure DocumentDB cluster. Put the connection string into the environment variable `DOCUMENTDB_URI`.
- (Optional, for embeddings) An OpenAI API key in `OPENAI_API_KEY` if you want the seed script to compute embeddings.

Files
- `README.md` - this file
- `.env.example` - template for environment
- `requirements.txt` - pinned Python deps
- `src/` - application code (db client, seed script, FastAPI app)
- `tests/` - unit tests (mocked, run without live cluster)
- `infra/` - (optional) infra templates (not created by default)

Quickstart
1. Copy `.env.example` to `.env` and fill in `DOCUMENTDB_URI` and (optionally) `OPENAI_API_KEY`.
2. Create and activate a venv, then install dependencies:
   python -m venv .venv
   source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows
   pip install -r requirements.txt

3. Seed the database (this will compute embeddings if OPENAI_API_KEY is set):
   python -m src.seed

4. The assistant created a vector index during verification. To run the API locally:
   uvicorn src.app:app --reload --host 127.0.0.1 --port 8000

5. Example screening request (curl):
   curl -X POST http://127.0.0.1:8000/screen -H "Content-Type: application/json" -d '{"name": "Person 1"}'

Notes and security
- Never store secrets (connection strings, API keys) in repo files. Use environment variables.
- This sample is for learning only. Do not use it as-is in production without adding authentication, Entra ID, private endpoints, CMK, and auditing.

License: MIT
