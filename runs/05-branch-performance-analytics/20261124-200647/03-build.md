# 3. Build report: 05-branch-performance-analytics

**Status: completed**

Built a compact Python FastAPI sample that computes branch-level performance summaries from a transactions collection, caches them in branch_summaries, exposes endpoints to read and refresh them, and provides a LangChain-style NL tool that synthesizes answers from the cached summaries via OpenAI. The repo includes seed and refresh scripts. I verified dependency installation, seeded synthetic data (~5k transactions), refreshed summaries (10 branches), inspected documents and indexes via the DocumentDB MCP tools, and exercised the FastAPI handlers via a smoke script (including the /ask fallback when OPENAI_API_KEY is not set). I avoided heavy native build failures by not installing full LangChain (see not_verified).

## How to run

1) Install dependencies: python -m pip install -r requirements.txt
2) Copy .env.example -> .env and set DOCUMENTDB_URI (and OPENAI_API_KEY if you want real LLM answers).
3) Seed sample data: python scripts/seed.py
4) Compute and cache summaries: python scripts/refresh_summaries.py
5) (Optional) Run the FastAPI server: uvicorn app.main:app --reload
6) Example endpoints:
   - GET /metrics/branches/{branch_id} (branch_id example: BR-001)
   - POST /summaries/refresh (triggers recompute)
   - POST /ask with JSON {"query":"..."} (requires OPENAI_API_KEY for real LLM answers; otherwise returns a message and matched branches)
7) A quick smoke-run that executes handlers directly (no running server): python scripts/run_smoke.py

## Verified by running

- pip install -r requirements.txt: succeeded (langchain was intentionally not installed to avoid pydantic-core native build issues)
- scripts/seed.py: executed and inserted ~5000 transactions for 10 branches (Inserted ~5000 transactions for 10 branches)
- scripts/refresh_summaries.py: executed and refreshed 10 branch summaries (Refreshed 10 branch summaries)
- documentdb.find documents (via documentdb MCP server) branch_summaries: returned 10 branch summary documents (sampled first 10)
- documentdb.list_indexes (via documentdb MCP server) transactions: returned indexes (_id, branchId, transactionDate, products.productId)
- scripts/run_smoke.py: invoked FastAPI handler functions directly; get_branch_metrics returned summary keys; refresh_summaries returned refreshed_branches:10; ask returned fallback message because OPENAI_API_KEY was not set

## Not verified

- Running the FastAPI app via uvicorn and exercising endpoints over HTTP (I exercised handler functions directly with a smoke script instead to avoid starting a long-running process in this environment).
- End-to-end LLM answers using OpenAI: not executed because OPENAI_API_KEY was not present in the environment during verification; the /ask endpoint returns a helpful message when the key is missing.
- Vector/hybrid search and DocumentDB vector index creation: not implemented or verified. The readiness report warned that embedding model + vector-dimension must be chosen before creating vector indexes; I deferred adding vector indexes to keep the sample runnable and documented how to extend the sample with vector/hybrid search.
- PyTest test run: pytest was not installed on PATH in this environment, so I executed the seed and refresh scripts directly instead of running tests under pytest.

## Open issues

- LangChain package: I intentionally did not install langchain to avoid a pydantic-core native build failure in this environment (Rust/cargo build error during pip install). The sample implements a small LangChain-style tool inside app/main.py that composes summaries and calls OpenAI; repo consumers may replace it with LangChain-based retrievers/agents if desired. (See D008 decision logged.)
- Vector search: the sample uses simple lexical retrieval over summaryText for the /ask tool. If you want vector/hybrid search, pick an embedding model and exact dimensions, create a DocumentDB vector index with matching dimensions using createSearchIndexes, and update the retriever to use cosine/ANN queries. Guidance and skill references are in the readiness report and the documentdb-vector-search skill.
- Production hardening and auth: sample reads DOCUMENTDB_URI from env. For production, use secure secret storage, Private Endpoint/Firewall, and optionally Microsoft Entra ID auth (the readiness report explains allowedModes).
- Tests: I added a tiny pytest file but did not run pytest (absent from PATH). If you want CI-friendly tests, add pytest to dev dependencies and run pytest in your CI pipeline.

## Files

- `requirements.txt`
- `README.md`
- `.env.example`
- `app/db.py`
- `app/main.py`
- `scripts/seed.py`
- `scripts/refresh_summaries.py`
- `scripts/run_smoke.py`
- `tests/test_seed_and_refresh.py`

