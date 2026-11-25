# 3. Build report: 19-option-chain-data-store

**Status: completed**

Created a small Python/FastAPI sample that ingests options-chain snapshots into an Azure DocumentDB (MongoDB-compatible) cluster (database sample_fintech_19) using pymongo bulk_write with ordered=False and UpdateOne upserts. The sample ensures a compound ascending index on (underlying, expiry, strike). A seed script was provided and executed against the live cluster; the collection and index were verified via the documentdb MCP server tools. Unit tests could not be run in this environment due to a pydantic/FastAPI compatibility issue on Python 3.13 (see open_issues and not_verified).

## How to run

1) Create and activate a venv, then install deps:
   python -m venv .venv
   source .venv/bin/activate   # or .venv\Scripts\activate on Windows
   pip install -r requirements.txt

2) Configure connection: copy .env.example -> .env and set DOCUMENTDB_URI (do not commit secrets). The script and app also read DOCUMENTDB_URI from environment directly.

3) Seed sample data into database sample_fintech_19:
   python scripts/seed.py

4) Run the API for manual testing (dev):
   uvicorn app.main:app --reload
   - POST /ingest accepts JSON: {"underlying":"FOO","expiry":"2026-12-17","options":[{...}]}
   - GET /chains?underlying=FOO&expiry=2026-12-17 returns chain sorted by strike.

5) Clean up: remove the `options` collection using your cluster tools or the DocumentDB MCP server when finished.

## Verified by running

- pip install -r requirements.txt: completed (packages installed successfully)
- scripts/seed.py: executed successfully and wrote 3 upsert operations to sample_fintech_19.options
- documentdb_list_databases(db_name=sample_fintech_19): returned database with collection 'options' and count 3
- documentdb_list_indexes(db_name=sample_fintech_19, collection_name=options): compound index 'idx_underlying_expiry_strike' on {underlying:1, expiry:1, strike:1} present
- documentdb_find_documents(db_name=sample_fintech_19, collection_name=options, limit=10): returned the 3 seeded documents

## Not verified

- pytest: could not complete (internal import error). Pytest run raised a FastAPI/Pydantic import-time TypeError (ForwardRef._evaluate missing 'recursive_guard') under Python 3.13 in this environment; unit tests therefore were not run.
- uvicorn/HTTP endpoints: not run in this session (the seed, indexes and sample documents were verified via the MCP server; running the live HTTP server was not performed here).

## Open issues

- Unit tests (pytest) failed to import FastAPI / Pydantic models in this environment (Python 3.13) due to a pydantic forward-ref handling error. Workarounds: run the tests with Python 3.10/3.11 where FastAPI + pydantic v1 are fully supported, or install Rust toolchain and allow building pydantic-core/pydantic v2 (then upgrade FastAPI to a pydantic-v2-compatible release).
- The sample code pins pymongo==4.4.0; if your environment uses a different driver minor/patch, consider updating the pin in requirements.txt to match your constraints.

## Files

- `requirements.txt`
- `app/__init__.py`
- `app/db.py`
- `app/main.py`
- `scripts/seed.py`
- `seeds/sample_chain.json`
- `.env.example`
- `README.md`
- `tests/test_api.py`

