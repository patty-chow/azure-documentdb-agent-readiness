# 3. Build report: 01-patient-record-summarizer-rag

**Status: completed**

A small Python sample repo implementing a Patient Record Summarizer (RAG) that stores chunked patient records and embeddings in an Azure DocumentDB-compatible (MongoDB-wire) cluster. The sample provides a FastAPI /search endpoint that re-ranks stored embeddings in-application (cosine similarity), constructs a clinical summarization prompt, and returns a grounded answer with document references. Unit tests mock DB and OpenAI calls and passed locally.

## How to run

1) Create and activate a virtualenv, then install dependencies:
   python -m pip install -r requirements.txt

2) Configure environment variables (example):
   export DOCUMENTDB_URI="mongodb://username:password@your-documentdb:10255/?ssl=true&replicaSet=globaldb"
   export OPENAI_API_KEY="sk-..."  # optional for seed; required for real embeddings/chats

3) Seed the demo data (writes to database sample_healthcare_01, collection patient_chunks):
   python seed.py
   Note: seed.py is idempotent and will insert deterministic synthetic chunks; if OPENAI_API_KEY is absent the seed generates deterministic pseudo-random embeddings.

4) Run the API locally:
   uvicorn app.main:app --reload

5) Example request (POST http://127.0.0.1:8000/search):
   {"patientId": "patient_1", "question": "Summarize recent cardiology history and meds.", "top_k": 5}

6) Run tests (unit tests mock DB/OpenAI):
   pytest -q


## Verified by running

- pip install -r requirements.txt: succeeded (dependencies installed locally)
- pytest -q: 3 passed, 1 skipped

## Not verified

- Seeded data written into a live DocumentDB cluster (seed.py was not executed against a live cluster in this run because DOCUMENTDB_URI was not validated here). Reason: integration with the live cluster was not performed during automated test run; run 'python seed.py' locally with DOCUMENTDB_URI set to verify.
- Creation of provider-native vector index (e.g., DiskANN/HNSW/IVF or provider-specific knnVector createIndex) was not executed or validated. Reason: environment lacks authoritative agent-kit/docs and run policy forbids Azure control-plane changes; sample uses application-side re-rank as a robust fallback. The README documents how to replace the fallback with a native index when validated.
- End-to-end OpenAI embedding and chat calls against real OpenAI API were not exercised in automated tests. Tests mock OpenAI. To verify live OpenAI calls, set OPENAI_API_KEY and run seed.py and an actual /search query.
- Authentication variants (Azure AD for MongoDB wire protocol, or other managed auth flows) were not validated. The sample reads DOCUMENTDB_URI from env; if your cluster uses AAD or a different auth mechanism consult the provider docs and update the connection approach.

## Open issues

None.

## Files

- `requirements.txt`
- `README.md`
- `.env.example`
- `LICENSE`
- `app/__init__.py`
- `app/db.py`
- `app/store.py`
- `app/embeddings.py`
- `app/summarizer.py`
- `app/main.py`
- `seed.py`
- `tests/test_app.py`
- `tests/test_seed.py`

