Azure DocumentDB — Correspondent Banking Risk Screener (sample)

This sample demonstrates:
- Using a Python LangChain-style agent to embed correspondent banking profiles
- Storing embeddings and documents in Azure DocumentDB (MongoDB-compatible)
- Creating a vector index (cosmosSearch) and running vector + text hybrid queries
- Returning a simple risk score, matched entries, and a plain-language narrative

Prerequisites
- Python (3.10+; environment has Python 3.13)
- An existing Azure DocumentDB cluster; connection string available in DOCUMENTDB_URI env var
- OpenAI API key available in OPENAI_API_KEY env var (for embeddings & narrative)

Files
- requirements.txt - Python dependencies
- .env.example - example environment variables
- src/ - application source
  - db.py - MongoDB client and index creation helpers
  - seed.py - seed sample data and create indexes
  - agent.py - embed, search and score logic
  - main.py - FastAPI app with POST /review
- seed/ - sample JSON seed data

Quickstart
1. Copy .env.example to .env and fill in DOCUMENTDB_URI and OPENAI_API_KEY
2. python -m venv .venv && source .venv/bin/activate
3. pip install -r requirements.txt
4. python -m src.seed  # loads seed data and creates collections & indexes
5. uvicorn src.main:app --reload
6. POST to http://127.0.0.1:8000/review with JSON {"correspondent_id": "corr_1"}

Notes & cleanup
- The sample writes to the database named `sample_banking_11`. To remove data, drop that database using mongosh or via an admin script.
- Do NOT commit secrets. The .env.example contains placeholders only.
