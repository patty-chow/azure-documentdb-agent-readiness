# 3. Build report: 03-substitute-product-finder

**Status: partial**

Created FastAPI sample app files, ingestion and query scripts, README and assets. Attempted to install Python dependencies but pip install failed due to building pydantic-core on Python 3.13 (no prebuilt wheel). Because of that, I switched to using the DocumentDB MCP data-plane tools for verification. Attempts to call MCP create-index/insert APIs failed (function returned error). Verification via MCP could not be completed due to function errors. The repository is ready for a user to install dependencies locally (preferably on Python 3.11/3.12) and run the ingestion and app against a reachable DocumentDB cluster.

## How to run

1) Copy .env.example to .env and set DOCUMENTDB_URI and optionally OPENAI_API_KEY.
2) python -m pip install -r requirements.txt (recommended Python 3.11 or 3.12 to avoid pydantic-core build issues).
3) Ingest data: python scripts/ingest.py --count 10000 (use --count 100 for quick verification).
4) Run server: uvicorn app.main:app --reload
5) Open http://localhost:8000 and use the UI to run substitute lookups.

## Verified by running

- wrote project files: 11 created and saved

## Not verified

- pip install -r requirements.txt failed due to pydantic-core build errors on Python 3.13 (no prebuilt wheel)
- Could not run ingestion script locally because dependencies were not installed
- Could not create vector index using MCP documentdb_create_index (tool returned error)
- Could not insert sample documents via MCP tool (tool returned error)
- Could not run a server-side vector-search aggregation to validate /substitute behavior

## Open issues

- Dependency installation fails on the available Python runtime (3.13) because pydantic-core must be built from source; switch to Python 3.11/3.12 or install Rust toolchain and maturin to build wheels
- MCP documentdb_create_index and documentdb_insert_documents tool calls returned errors during automated verification; manual verification with the live cluster (using the .env and running scripts) should work in a developer environment.

## Files

- `requirements.txt`
- `.env.example`
- `README.md`
- `app/config.py`
- `app/models.py`
- `app/main.py`
- `app/routes.py`
- `scripts/ingest.py`
- `scripts/query_substitutes.py`
- `templates/index.html`
- `static/style.css`

