Sample: DocumentDB + Beanie + LangChain orchestration

This sample demonstrates a small onboarding orchestrator implemented in Python using:
- Motor + Beanie for MongoDB/DocumentDB data access
- Atomic state transitions implemented with Motor sessions/transactions
- A minimal FastAPI surface and a CLI entrypoint

What it shows
- Modeling an onboarding application as a single document with embedded transition history
- Running three agents in sequence (ID verification, risk assessment, account opening)
- Persisting each state transition atomically and logging the transition

Prerequisites
- Python 3.11+ (this environment uses Python on PATH)
- An Azure DocumentDB cluster reachable; set DOCUMENTDB_URI in .env
- The sample uses database `sample_banking_15` by default

Quickstart
1. Copy .env.example to .env and set DOCUMENTDB_URI and other env vars.
2. Create and activate a virtualenv, then install dependencies:
   python -m pip install -r requirements.txt
3. Seed sample data:
   python scripts/seed.py
4. Run a single orchestrator run (CLI):
   python -m sample_orchestrator.run --app-id <applicant_id>
5. Run the FastAPI app:
   uvicorn sample_orchestrator.api:app --reload

Tests
- Unit tests use mocks and can be run without a live cluster:
  pytest

Security
- Do NOT commit real credentials. Read the cluster connection string from DOCUMENTDB_URI.

Cleanup
- The sample creates documents in the `sample_banking_15` database. Remove them manually or by script when finished.
