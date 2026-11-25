# 3. Build report: 02-clinical-trial-matching-orchestration

**Status: completed**

A minimal Python LangChain orchestration sample was created that seeds a trials collection in the existing Azure DocumentDB cluster, provides a FastAPI endpoint and a demo to run a patient->match flow, applies a deterministic eligibility engine, and (when available) can call OpenAI for embeddings/LLM outputs. Unit tests run and passed. Seeding inserted 3 trial documents and created scalar indexes. An attempt to create a service-side vector index via the documentdb MCP helper failed; the sample falls back to client-side ranking using stored embeddings so the sample remains functional.

## How to run

1) Create and activate a Python virtualenv. 2) pip install -r requirements.txt. 3) Copy .env.example to .env and set DOCUMENTDB_URI (required). Optionally set OPENAI_API_KEY to enable real embeddings and LLM agents. 4) python seed.py (creates scalar indexes and inserts sample trials). 5) python demo.py to run a one-shot match demonstration. 6) Optionally run the FastAPI server: uvicorn app.main:app --reload --port 8000 and POST /match with a patient JSON payload. 7) Run tests with: python -m pytest -q.

## Verified by running

- pip install -r requirements.txt: succeeded (packages installed)
- pytest: 3 passed
- python seed.py: completed (Inserted/updated 3 trials; scalar indexes created)
- documentdb_sample_documents (via MCP server): returned sample documents (3 documents visible)
- documentdb_list_indexes (via MCP server): returned scalar indexes (criteria.conditions and criteria.min_age/max_age present)
- python demo.py: ran a sample match; returned ranked candidate(s) and stored match in 'matches' collection

## Not verified

- Creation of a service-side vector index using the documentdb MCP server: attempted but the create-index call failed with 'Error: Function failed.' The exact index creation syntax and success on this cluster was not verified programmatically (tool failure).
- LLM-based eligibility and consent agent outputs (OpenAI): not verified with real OpenAI API because OPENAI_API_KEY was not provided in this run (the sample falls back to deterministic rules and templated consent summaries when the key is missing).

## Open issues

- documentdb_create_index MCP helper call failed when attempting to create a cosmosSearch vector index of kind 'vector-hnsw' (dimensions=1536). This was recorded and the sample continues with client-side ranking. If you want service-side vector search, retry creating the index using the exact 'db.collection.createIndex' form shown in the vector-create-diskann guidance or consult cluster control-plane logs.
- If you want LLM-driven rationale and patient-facing consent summaries, set OPENAI_API_KEY in the environment and re-run demo/seed to exercise the LangChain/OpenAI paths.

## Files

- `README.md`
- `requirements.txt`
- `.env.example`
- `app/db.py`
- `app/main.py`
- `seed.py`
- `demo.py`
- `tests/test_eligibility.py`

