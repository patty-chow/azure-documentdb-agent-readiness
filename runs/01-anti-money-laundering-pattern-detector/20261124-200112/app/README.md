AML Pattern Detector sample

What this shows
- A minimal Python LangChain-style agent that analyzes transaction documents in an Azure DocumentDB (MongoDB-compatible) cluster and flags suspicious counterparty chains using aggregation pipelines (graph lookup, cycle detection, structuring, rapid pass-through).
- A small FastAPI HTTP endpoint and a CLI entrypoint to run the analysis.

Prerequisites
- Python 3.10+ (a Python 3.13 runtime is available in the build environment).
- A reachable Azure DocumentDB cluster; set DOCUMENTDB_URI in your .env to the SRV connection string.
- (Optional) OpenAI API key in OPENAI_API_KEY to enable LLM-based narrative generation. If missing, the sample uses a deterministic stub summarizer.

Setup
1. python -m venv .venv
2. source .venv/bin/activate
3. pip install -r requirements.txt
4. cp .env.example .env and edit to add DOCUMENTDB_URI (and optional OpenAI keys)
5. python seed.py  # idempotent - creates sample data and indexes

Run
- CLI: python run.py analyze
- HTTP: uvicorn app.main:app --reload
  POST /analyze  with JSON body {"min_amount":1000} to run analysis. Returns JSON narratives for flagged chains.

Tests
- pytest

Cleanup
- The sample writes only to the database named `sample_banking_01`. To remove the sample data, drop that database from your cluster (e.g., via the portal or a mongo client).

Security notes
- Do not commit real secrets. Use .env for local development.
- This sample is for learning and demonstration; it is not production hardened.
