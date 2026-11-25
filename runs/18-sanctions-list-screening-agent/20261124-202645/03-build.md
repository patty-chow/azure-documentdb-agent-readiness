# 3. Build report: 18-sanctions-list-screening-agent

**Status: completed**

Built a small Python sanctions-screening sample that seeds synthetic sanctions entries, stores embeddings, creates a DocumentDB vector index, and provides a FastAPI-based screening flow (plus CLI/demo scripts). Verified unit tests, data seeding, vector index creation (via PyMongo fallback), vector search, and a demo screening run. The DocumentDB MCP helper to create indexes failed; I used a PyMongo createIndexes command as a reliable fallback and documented that decision.

## How to run

1) Copy .env.example to .env and fill DOCUMENTDB_URI (and OPENAI_API_KEY if you want the seed script to compute real embeddings).
2) Create and activate a Python venv (Python 3.11), then install deps: pip install -r requirements.txt
3) Seed the database (idempotent): python -m src.seed
   - If OPENAI_API_KEY is set, the seed script will compute embeddings; otherwise it inserts documents with empty embeddings.
4) Create the vector index (if you don't want the assistant fallback): either run the helper script that was used in verification: python scripts/create_vector_index.py (this uses DOCUMENTDB_URI) -- or use the db command shown in README.
   Note: The assistant attempted to use the documentdb MCP helper but it failed; the repo includes scripts/create_vector_index.py which uses the Mongo createIndexes command and was used in verification.
5) (Optional) Update or seed embeddings for one or more documents: python scripts/update_embedding.py
6) Quick demo (local, no server): python scripts/demo_screen.py  (set DEMO_NAME env var to change query)  Example: DEMO_NAME="Person 1" python scripts/demo_screen.py
7) Run unit tests: pytest
8) To run the HTTP API: uvicorn src.app:app --reload --host 127.0.0.1 --port 8000
   POST to /screen with JSON {"name": "...", "country": "..."}. The app requires OPENAI_API_KEY to compute the query embedding at runtime.

Important secrets: Do not commit DOCUMENTDB_URI or OPENAI_API_KEY. Use environment variables as shown in .env.example.

## Verified by running

- pytest: 2 passed (tests/test_utils.py) — unit tests for scoring & cosine computations
- seed script: python -m src.seed executed — reported 'Seeded 200 documents into sample_banking_18.sanctions' (documents inserted with empty embeddings because OPENAI API key was not present during the run)
- Vector index creation via PyMongo: python scripts/create_vector_index.py executed — createIndexes returned ok and index appears in index list
- List indexes via documentdb_list_indexes: showed both _id_ and embedding_vector_idx with cosmosSearchOptions (kind=vector-hnsw, dimensions=1536, similarity=COS, m=16, efConstruction=64)
- Updated one document embedding: python scripts/update_embedding.py set a 1536-dim embedding for _id 'sanction_1' (matched=1 modified=1)
- Vector search against the collection: python scripts/run_vector_search.py executed and returned sanction_1 with searchScore 1.0 (aggregation using $search + cosmosSearch returned expected result)
- Demo screening CLI: python scripts/demo_screen.py executed and returned a consolidated screening report combining vector and regex signals (sanction_1 was high confidence match)

## Not verified

- Full runtime of the FastAPI /screen endpoint using real OpenAI embeddings (not executed): I did not start the uvicorn server and call /screen with OPENAI_API_KEY present. Reason: OPENAI_API_KEY was not set in the environment during verification, so the app would return 500 when trying to call the OpenAI Embeddings API. The sample app and demo script include fallback behavior and instructions to run with an API key.
- documentdb_create_index MCP helper tool: attempted twice and the MCP helper (documentdb_create_index) failed with 'Function failed.'; I did not re-try repeatedly. Instead, I used a PyMongo createIndexes fallback and verified index creation. The MCP helper failure is recorded in the audit trail.

## Open issues

- Tuning of scoring function and thresholds: I picked vector weight 0.7 / regex weight 0.3 and thresholds high>=0.8, medium>=0.5 as sample defaults. These are intentionally simple and must be tuned with labeled data for production.
- Embedding provider and dimensions: I chose OpenAI text-embedding-3-small (1536 dims) as a sample provider. If you use a different embedding model, update EMBEDDING_MODEL and EMBEDDING_DIM in .env.example and recreate the vector index with the matching 'dimensions' parameter.
- The documentdb_create_index MCP tool failed in this run; the repo includes scripts/create_vector_index.py as a robust PyMongo fallback. If you rely on MCP automation in your environment, re-run the MCP helper (documentdb_create_index) or investigate the failure.
- The sample uses a synthetic dataset inserted into sample_banking_18.sanctions. For a realistic demo or production use replace the seed data with licensed, curated sanctions lists and add appropriate privacy/compliance controls.

## Files

- `README.md`
- `.env.example`
- `requirements.txt`
- `src/__init__.py`
- `src/db.py`
- `src/seed.py`
- `src/utils.py`
- `src/app.py`
- `tests/test_utils.py`
- `tests/conftest.py`
- `scripts/create_vector_index.py`
- `scripts/update_embedding.py`
- `scripts/run_vector_search.py`
- `scripts/demo_screen.py`

