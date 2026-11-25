Azure DocumentDB — Care Coordination Multi-Agent Sample

This sample demonstrates a Python + LangChain multi-agent system that reads patient records from an Azure DocumentDB (MongoDB-compatible) cluster, retrieves referrals and medication lists, then synthesises a unified care plan and writes it back to the database.

What this sample shows
- A minimal multi-agent pattern: GP agent (primary care), Specialist agent (referrals), Pharmacy agent (meds).
- An orchestrator that calls each agent, synthesises a care plan with an LLM, and stores the result in the `care_plans` collection.
- A CLI and a minimal FastAPI endpoint for manual testing.
- Idempotent seed script to create sample data and single-field indexes on `patient_id`.

Important constraints
- Do NOT commit secrets. The app reads the DocumentDB connection string from DOCUMENTDB_URI at runtime.
- This sample does NOT provision Azure resources. Use the existing cluster pointed at by DOCUMENTDB_URI.
- Vector indexes are NOT created by default. If you希望 to enable vector retrieval, see the "Vector search and embeddings" section below.

Prerequisites
- Python 3.10+ (the run environment provides Python)
- A reachable Azure DocumentDB cluster. Put the connection string (mongodb+srv://... or non-SRV connection string) into DOCUMENTDB_URI.
- (Optional) OpenAI-compatible API key in OPENAI_API_KEY if you want real LLM/embedding calls.

Setup
1. Create and activate a virtualenv (the run environment already has one available):
   python -m venv .venv
   source .venv/bin/activate

2. Install dependencies:
   pip install -r requirements.txt

3. Copy the example env and edit:
   cp .env.example .env
   # Edit .env and set DOCUMENTDB_URI and (optionally) OPENAI_API_KEY

4. Seed sample data & indexes (idempotent):
   python seed_data.py

Run the orchestrator (CLI)
   python run_orchestrator.py --patient-id patient-001

Run the API (FastAPI) locally
   uvicorn app.api:app --reload
   # then POST http://127.0.0.1:8000/orchestrate with JSON {"patient_id": "patient-001"}

What the sample writes
- Database: sample_healthcare_19
- Collections created/used: patients, referrals, medications, care_plans
- Indexes: single-field index on patient_id for patients/referrals/medications
- The orchestrator inserts a document into care_plans with fields: patient_id, created_at, plan_text, sources

Vector search and embeddings
- This demo does not create vector indexes by default because embedding/LLM credentials may not be available. If you have OPENAI_API_KEY and want to enable vector retrieval:
  - Set EMBEDDING_MODEL (default text-embedding-3-small) and ensure you know the embedding dimension (1536 for text-embedding-3-small).
  - Follow the notes in app/db.py and the documentdb vector-search docs to create a vector index with the proper "dimensions".

Testing
- Unit tests are included under tests/ and mock the database + LLM, so they run without a live cluster or API keys:
   pytest -q

Cleanup
- The sample creates data in the database sample_healthcare_19. Remove it manually with your preferred MongoDB tooling if desired (do not commit credentials into code).

Files
- app/: application code
- seed_data.py: seed script to upsert sample data and ensure indexes
- run_orchestrator.py: CLI entrypoint
- .env.example: placeholder environment variables
- tests/: unit tests with mocks

License: MIT
