Next-Best-Action (NBA) multi-agent sample for Azure DocumentDB

This sample demonstrates a small Python LangChain-style multi-agent orchestrator that:
- Reads customer interaction history and preferences from an Azure DocumentDB (Mongo-compatible) cluster
- Runs three agents: propensity (likelihood to respond), channel selection (customer channel preferences), and timing (best send time)
- Combines results and writes an NBA recommendation document to sample_customer_360_03.nba_recommendations

What this sample shows
- How to connect to Azure DocumentDB using pymongo with a singleton MongoClient
- Idempotent seed script to create sample collections and indexes (non-vector)
- Optional OpenAI integration for embeddings/LLM if OPENAI_API_KEY is set; otherwise deterministic heuristics run
- How to run an orchestrator via CLI or a minimal FastAPI endpoint

Prerequisites
- Python (3.10+)
- A reachable Azure DocumentDB cluster and its connection string in env var DOCUMENTDB_URI
- (Optional) OpenAI API key in OPENAI_API_KEY to enable embedding/LLM features

Files
- src/: application code
- seed.py: idempotent seeding of sample data and non-vector indexes
- main.py: CLI demo and FastAPI app
- .env.example: example env variables
- requirements.txt: pinned dependencies
- tests/: basic unit test for orchestrator logic

Security
- Never store secrets in source. Set DOCUMENTDB_URI and OPENAI_API_KEY in your environment.

How to run
1. Create a virtualenv and install deps:
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2. Set environment variables (example .env):
   export DOCUMENTDB_URI="<your connection string>"
   export OPENAI_API_KEY="<optional>"

3. Seed the database with sample data:
   python seed.py

4. Run the demo CLI (creates and writes an NBA recommendation for a demo customer):
   python main.py --demo

5. Run the FastAPI app:
   uvicorn main:app --reload
   then POST or GET /nba?customer_id=<id>

Verification notes
- The repository includes scripts that run against a live cluster referenced by DOCUMENTDB_URI. The build report records which verification steps were executed.

License: MIT
