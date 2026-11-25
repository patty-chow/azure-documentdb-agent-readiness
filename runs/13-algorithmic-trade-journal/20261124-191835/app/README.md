# Algorithmic Trading Journal (Azure DocumentDB sample)

This sample demonstrates storing immutable trading events (signals, executions, outcomes) in Azure DocumentDB (MongoDB-compatible) and computing per-strategy statistics (win rate, average P&L, total P&L, trade count, max drawdown).

What it includes:
- FastAPI service with endpoints to insert events and retrieve stats
- Aggregation pipelines for win rate / avg P&L / total P&L
- Client-side drawdown computation for correctness
- A deterministic context-engineering formatter that produces an LLM-ready summary
- Seed script to populate sample data for at least two strategies
- Tests that run aggregations against the live cluster

Prerequisites
- Python 3.10+ (the environment provides a suitable Python)
- A reachable Azure DocumentDB cluster with MongoDB wire protocol; set DOCUMENTDB_URI in your environment before running
- The sample uses database `sample_fintech_13` and collection `journal`

Quickstart
1. Copy `.env.example` to `.env` and set DOCUMENTDB_URI
2. Install dependencies: pip install -r requirements.txt
3. Seed sample data: python scripts/seed_data.py
4. Run tests: pytest -q
5. Run FastAPI locally: uvicorn app.main:app --reload

Security
- Do NOT store your connection string in the repo. Use the DOCUMENTDB_URI environment variable.

Files created by this sample
- app/ (FastAPI app and DB helpers)
- scripts/seed_data.py (idempotent sample data loader)
- tests/test_aggregations.py (Basic integration tests)

License: MIT
