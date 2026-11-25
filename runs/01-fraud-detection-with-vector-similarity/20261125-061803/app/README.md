Fraud detection sample using Azure DocumentDB (MongoDB-compatible) with vector similarity

Overview

This sample demonstrates a simple Python LangChain-based agent that encodes transaction features as embeddings, stores fraud pattern vectors in a DocumentDB collection, and scores new transactions by searching for similar historical patterns.

It is intentionally small and safe: the DocumentDB connection string must be provided at runtime via the DOCUMENTDB_URI environment variable. Embeddings are produced via OpenAI through LangChain when OPENAI_API_KEY is set, otherwise a deterministic mock embedding is used so the sample still runs.

What this shows
- How to read DOCUMENTDB_URI and use the database `sample_fintech_01`.
- A seed script that creates a `fraud_patterns` collection and loads synthetic pattern documents.
- A FastAPI app with POST /score that returns a risk_score, textual explanation and matched patterns.
- A server-side index creation is attempted, but the sample falls back to client-side similarity if the cluster does not accept the vector index API.

Prerequisites
- Python 3.x and pip
- A reachable Azure DocumentDB cluster (MongoDB wire protocol) and its connection string set in DOCUMENTDB_URI
- (Optional) OPENAI_API_KEY in the environment to use real embeddings via LangChain/OpenAI

Quickstart
1. python -m pip install -r requirements.txt
2. Copy .env.example to .env and set DOCUMENTDB_URI and optionally OPENAI_API_KEY
3. python seed_data.py    # creates collection and loads sample patterns
4. uvicorn src.app:app --reload
5. POST a JSON transaction to http://localhost:8000/score

Files
- src/app.py - FastAPI app and endpoints
- src/agent.py - Agent code: embedding + search + scoring
- seed_data.py - Create collection/index and load synthetic data
- requirements.txt - Python dependencies
- .env.example - example environment variables

Security
Do not commit secrets. The sample reads DOCUMENTDB_URI and OPENAI_API_KEY from environment variables.

Notes on vector indexing
The exact server-side vector-index creation and search operators vary between DocumentDB/managed services. This sample attempts a plausible create_index vectorOptions call; if the cluster rejects it, the seed script continues and the app performs client-side similarity search so the demo still functions. See the seed script and README for more details.
