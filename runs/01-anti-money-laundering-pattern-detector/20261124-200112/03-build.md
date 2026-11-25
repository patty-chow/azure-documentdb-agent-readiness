# 3. Build report: 01-anti-money-laundering-pattern-detector

**Status: completed**

Built a small Python AML Pattern Detector sample that connects to an existing Azure DocumentDB cluster (reads DOCUMENTDB_URI from env), seeds sample accounts and transactions, creates indexes (via PyMongo in the seed script), exposes a CLI and a small FastAPI endpoint to run analysis, and provides tests. The sample implements three heuristic detection routines (structuring, rapid pass-through, circular transfers) that use MongoDB aggregations and $graphLookup; it produces structured narratives and optionally uses an LLM/embeddings when OPENAI_API_KEY is provided (otherwise a deterministic stub is used). I verified seeding, index creation (via PyMongo), core analysis, tests, and inspected indexes and an explain plan via the documentdb MCP server tools where available. One MCP index-creation call failed and was worked around by creating indexes in seed.py via PyMongo.

## How to run

1) Create and activate a virtual environment (optional but recommended): python -m venv .venv && source .venv/bin/activate
2) Install deps: pip install -r requirements.txt
3) Copy .env.example to .env and set DOCUMENTDB_URI to your cluster SRV connection string; optionally set OPENAI_API_KEY and OPENAI_* model vars.
4) Seed sample data and create indexes: python seed.py
5a) Run CLI analysis: python run.py analyze [--use-llm]
5b) Run HTTP API: uvicorn app.main:app --reload  (POST /analyze with JSON {"use_llm": false} )
6) Run tests: pytest

Notes:
- Do NOT put real secrets into source control. Use .env locally and keep secrets out of files.
- The sample writes only to the database named `sample_banking_01`; remove that DB in your cluster to clean up.

## Verified by running

- pip install -r requirements.txt: completed successfully (packages installed)
- seed.py: executed successfully, inserted/updated sample accounts and transactions into sample_banking_01
- pytest: 2 passed (tests/test_seed_and_analysis.py) - verified collections exist and analysis runs
- documentdb_list_indexes (MCP): returned index list for sample_banking_01.transactions (includes from_account, to_account, from_account+timestamp)
- documentdb_aggregate (MCP): aggregation grouping amount<1000 returned expected structuring result for account A2 (5 txs, total 4500)
- documentdb_explain_operation (MCP): explain on find {from_account: 'A6'} returned an explain (planner output, executionStats) showing execution and indexes considered

## Not verified

- LLM/embedding end-to-end generation against a real OpenAI API: not executed because OPENAI_API_KEY was not set in the environment. The sample supports an OpenAI-based narrative generator (langchain wrapper) but tests used a deterministic stub.
- Programmatic index creation via the documentdb MCP tool (documentdb_create_index) failed in this environment (the tool returned an error). I used PyMongo create_index in seed.py as an idempotent fallback. The MCP index-creation API call error needs investigation if maintainers want MCP-based index management.
- Vector index creation and vector-search integration (cosmosSearch, DiskANN/HNSW/IVF) were not implemented or verified. The readiness report flagged an embedding-dim alignment decision; I chose to make embeddings optional (OpenAI text-embedding-3-small, 1536 dims) but did not create vector indexes or run vector queries in this sample.

## Open issues

- documentdb_create_index MCP call failed here; fallback to PyMongo worked. If you want to manage indexes via MCP server in CI or automation, investigate the MCP server connectivity/profile or credentials.
- LLM usage requires an API key (OPENAI_API_KEY). With no key the sample uses a deterministic stub; maintainers should run with a proper key to exercise narrative generation and embedding-based enhancements.
- No vector indexes or vector-search integration implemented. If you want a hybrid lexical+semantic detection or use LangChain vector stores, add createIndexes with cosmosSearchOptions and embed documents (and ensure index dimensions match embedding model).

## Files

- `requirements.txt`
- `.env.example`
- `README.md`
- `seed.py`
- `run.py`
- `aml_agent/__init__.py`
- `aml_agent/db.py`
- `aml_agent/analysis.py`
- `aml_agent/llm.py`
- `app/main.py`
- `tests/test_seed_and_analysis.py`

