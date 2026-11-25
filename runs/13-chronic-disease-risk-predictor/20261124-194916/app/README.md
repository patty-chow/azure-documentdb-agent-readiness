Azure DocumentDB — Chronic Disease Risk Predictor Sample

This sample demonstrates using Azure DocumentDB vector search to store high-risk patient profile embeddings and a LlamaIndex/OpenAI-based agent to generate personalised risk narratives for new patients.

Overview
- Language: Python (uses system Python; sample tested with Python 3.13)
- Database: Azure DocumentDB (MongoDB-compatible). The connection string is read from DOCUMENTDB_URI environment variable.
- Database name: sample_healthcare_13
- Collection: high_risk_profiles
- Embeddings: OpenAI text-embedding-3-small (1536 dims) by default; randomized embeddings used when OPENAI_API_KEY is not present.
- LLM: OpenAI (used via LlamaIndex when OPENAI_API_KEY is present); otherwise a deterministic template is returned.

Files
- src/db.py              — MongoClient singleton and helpers
- src/embeddings.py      — embedding helpers (OpenAI or fallback)
- src/retriever.py       — DocumentDB $search-based retriever
- src/agent.py           — LlamaIndex / OpenAI agent wrapper (optional)
- src/app.py             — FastAPI app exposing /predict
- seed.py                — Idempotent seeding of synthetic high-risk profiles
- requirements.txt       — Python dependencies
- .env.example           — Example env file
- tests/                 — pytest tests using mongomock

Prerequisites
1. Copy .env.example to .env and fill DOCUMENTDB_URI and optionally OPENAI_API_KEY.
2. Python (3.10+). Create a virtualenv and activate it.
3. pip install -r requirements.txt

Quickstart (development)
1. pip install -r requirements.txt
2. cp .env.example .env and set DOCUMENTDB_URI (and OPENAI_API_KEY if you want real embeddings/LLM)
3. python seed.py  # seeds synthetic profiles (uses OPENAI if present, otherwise random embeddings)
4. uvicorn src.app:app --host 127.0.0.1 --port 8000
5. POST to http://127.0.0.1:8000/predict with JSON: {"features": {"age": 65, "bmi": 32, ...}}

Notes
- This sample is for demonstration only and not for clinical use. All data is synthetic.
- Secrets must be provided via environment variables; never commit real keys to the repo.

Cleanup
- To remove seeded documents, connect to the cluster and drop the collection `high_risk_profiles` in database `sample_healthcare_13`.

Assumptions and decisions are recorded in the project BUILD_REPORT.md and in the runtime logs when the app starts.
