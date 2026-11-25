Azure DocumentDB Care Coordination Multi-Agent Sample

Overview

This sample demonstrates a small multi-agent care coordination system that reads data from an Azure DocumentDB (MongoDB-compatible) cluster and synthesizes a unified care plan document back into the database.

It is intentionally small and designed for learning. The orchestrator coordinates three worker agents:
- Primary Care Agent: reads the patient's primary care record from the patients collection
- Specialist Agent: retrieves referral notes from referrals collection
- Pharmacy Agent: checks current medications from medications collection

The orchestrator synthesises a unified care plan (using an LLM when configured) and writes it to the care_plans collection.

Important constraints
- This sample uses an existing live Azure DocumentDB cluster reachable from this machine. The connection string must be provided in the DOCUMENTDB_URI environment variable at runtime.
- The sample will NOT provision Azure resources.
- Do not commit secrets. Keep DOCUMENTDB_URI and any LLM keys out of source control.

What the sample shows
- How to connect to Azure DocumentDB using the official PyMongo driver with a singleton MongoClient
- A small, idempotent seed script to insert sample patients, referrals and medications
- A simple multi-agent orchestrator pattern (LangChain-compatible if you supply OPENAI_API_KEY and install the optional LangChain dependency)
- A CLI entrypoint and a minimal FastAPI endpoint for manual testing
- How to run unit tests that mock the DB and LLM clients

Prerequisites
- Python 3.10+ (this environment has Python 3.13 available)
- A reachable Azure DocumentDB connection string set in DOCUMENTDB_URI
- (Optional) An OpenAI-compatible API key set in OPENAI_API_KEY to enable real LLM synthesis

Files
- README.md (this file)
- .env.example — example env file with placeholders
- requirements.txt — Python dependencies
- seed_data.py — idempotent script to load sample data into sample_healthcare_19
- run_orchestrator.py — simple CLI to run the orchestrator for a patient
- app/ — application code (DB client, agents, orchestrator, FastAPI app)
- tests/ — unit tests that run without a live cluster by mocking dependencies

Quickstart

1. Create a virtual environment and activate it (optional but recommended)

   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .\.venv\Scripts\activate  # Windows PowerShell

2. Install dependencies

   pip install -r requirements.txt

3. Copy .env.example to .env and fill DOCUMENTDB_URI and optionally OPENAI_API_KEY

   cp .env.example .env
   # edit .env and set DOCUMENTDB_URI to the cluster connection string

4. Seed the sample data

   python seed_data.py

5. Run the orchestrator for a sample patient (CLI)

   python run_orchestrator.py --patient-id patient-1

   The script will call each agent, synthesise a care plan (mocked if OPENAI_API_KEY is missing), and insert the care plan into the care_plans collection.

6. Run the FastAPI server for HTTP testing

   uvicorn app.api:app --reload --port 8000

   POST http://localhost:8000/orchestrate with JSON body: {"patient_id": "patient-1"}

7. Run unit tests

   pytest -q

Notes & Next steps
- The sample includes single-field indexes on patient_id for quick lookups. For production or retrieval-heavy workloads, follow the documentdb-indexing and documentdb-vector-search guidance to add text / vector indexes. When adding vector indexes, set the dimensions to the embedding model output (the sample documents mention text-embedding-3-small with 1536 dims).
- The orchestrator uses a simple mocking fallback if OPENAI_API_KEY is not set; provide an API key to test the LLM-backed synthesis path. See .env.example for variable names.

Security
- Never commit your DOCUMENTDB_URI or OPENAI_API_KEY. Use environment variables or a secrets manager.

License

MIT
