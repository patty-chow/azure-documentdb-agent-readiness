# 3. Build report: 14-telehealth-session-summarizer

**Status: completed**

A small Python sample app was created that accepts a telehealth transcript, generates a structured clinical summary (chief_complaint, assessment, plan, follow_up), and stores the result in an Azure DocumentDB (MongoDB-protocol) database named `sample_healthcare_14`. The code reads the cluster connection string from DOCUMENTDB_URI, uses a singleton PyMongo MongoClient, provides an idempotent seed script to insert a patient + transcripts, a CLI to call the summariser, and unit smoke test(s). OpenAI is supported for LLM summarisation (configurable via OPENAI_API_KEY), but the sample falls back to a small heuristic summariser when the key is absent so the sample can run in constrained environments. Index creation for patientId was created via the app (pymongo) during seeding and inspected using the documentdb MCP server tools.

## How to run

1) Create a virtualenv and activate it (Python 3.10+).
   python -m venv .venv
   source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows

2) Install dependencies
   pip install -r requirements.txt

3) Configure environment variables (copy .env.example to .env or set env vars):
   DOCUMENTDB_URI (required) — the Mongo-compatible connection string for the Azure DocumentDB cluster
   OPENAI_API_KEY (optional) — if present the sample will attempt a live OpenAI LLM call; otherwise it uses a small heuristic fallback
   Optional: LLM_MODEL, EMBEDDING_MODEL, DATABASE_NAME

4) Seed sample data (creates patient + transcripts and ensures indexes)
   python scripts/seed.py

5) Run the CLI demo
   python scripts/summarize_cli.py --patient-id patient_1 --transcript "Patient..."
   This prints the stored document and inserts it into the clinical_summaries collection.

6) Run smoke tests
   pytest -q

Notes:
- The app reads DOCUMENTDB_URI at runtime and never writes secrets to disk.
- The sample intentionally does not create a vector index by default; instructions to add embeddings/vector indexes are in README and code comments.

## Verified by running

- pip install -r requirements.txt: completed (packages installed)
- scripts/seed.py: completed (seed inserted patient and transcripts, create_indexes invoked)
- scripts/summarize_cli.py (fallback path): completed (inserted a clinical_summaries document using fallback summariser when OPENAI_API_KEY was not set)
- pytest: 1 passed (smoke test that inspected db connection and collections)
- documentdb_list_indexes (MCP): returned indexes including idx_patientId (verified)
- documentdb_find_documents (MCP): returned clinical_summaries documents (verified insertion)

## Not verified

- Live OpenAI LLM summarisation path: not executed because OPENAI_API_KEY was not present in the environment during verification (the code falls back to a simple heuristic summariser when the key is missing).
- Vector embeddings & cosmosSearch vector index creation: not created or tested. The sample includes guidance and a .env.example for embedding model choice (text-embedding-3-small, 1536 dims) but does not create a vector index by default to avoid making optional, non-essential cluster changes.
- Infrastructure provisioning (az / Bicep / Terraform): not executed. The run policy disallowed making Azure resource changes and the environment already provided a cluster per the prompt.

## Open issues

None.

## Files

- `requirements.txt`
- `.env.example`
- `README.md`
- `src/db.py`
- `src/summarizer.py`
- `scripts/seed.py`
- `scripts/summarize_cli.py`
- `tests/test_smoke.py`

