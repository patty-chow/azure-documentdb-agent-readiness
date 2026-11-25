# 3. Build report: 07-voice-of-customer-sentiment-hub

**Status: completed**

I built a small Python sample that ingests customer feedback, analyzes sentiment/topics/quote with a prompt-style heuristic (with an LLM fallback path documented), stores enriched documents and deterministic embeddings in the provided Azure DocumentDB cluster, and runs aggregation pipelines to surface net sentiment by channel, topic and time. During the build I adapted to environment constraints (no Rust toolchain / pydantic-core wheels for this Python runtime) and used pymongo for a synchronous, minimal-dependency sample so the repository is verifiable in this environment. The sample attempts to create DocumentDB 'search' (vector/text) indexes with createSearchIndexes but the live cluster returned CommandNotSupported; the sample falls back to storing embeddings and still supports the aggregation demos.

## How to run

1) Create and activate a Python venv. 2) pip install -r requirements.txt. 3) Copy .env.example -> .env and set DOCUMENTDB_URI (and optionally OPENAI_API_KEY / EMBEDDING_MODEL / LLM_MODEL). 4) Seed sample data (this also attempts to create search indexes): python -m src.scripts.seed 5) Run aggregations / demo: python -m src.scripts.aggregations. The sample uses env vars (DOCUMENTDB_URI, DATABASE_NAME, EMBEDDING_DIM, OPENAI_API_KEY, etc.). See README.md for details.

## Verified by running

- pip install -r requirements.txt: succeeded (installed pymongo and small deps)
- python -m src.scripts.seed: succeeded — inserted 5 sample documents into database sample_customer_360_07.feedbacks; createSearchIndexes attempted and returned CommandNotSupported
- python -m src.scripts.aggregations: succeeded — printed sentiment-by-channel, sentiment-by-topic, and sentiment-by-day aggregation outputs

## Not verified

- Beanie + Motor ODM path: Not verified. I initially planned Beanie+Motor but pip build failed for pydantic-core under the available Python runtime (see 'guidance_for_builder' in readiness report). I switched to pymongo to allow verification in this environment. Evidence: pip error building pydantic-core (tool_result).
- LLM and cloud embeddings (OpenAI via LangChain): Not verified — the sample implements a deterministic heuristic fallback for analysis and embeddings so the repository is runnable without cloud keys. If you set OPENAI_API_KEY and dependencies for LangChain/OpenAI, the code can be extended to call a provider. The real LLM/embedding paths were not exercised in this run.
- Search index creation using createSearchIndexes: attempted but the cluster returned CommandNotSupported (errmsg: 'Search index creation is not supported yet'). The seed script handled this gracefully and continued; the sample documents and aggregation pipelines were still created and run.

## Open issues

- Environment Python version (3.13) prevented building pydantic-core wheels in this run, which forced switching away from Beanie/pydantic. If you want the original Beanie-based sample, re-run in a Python runtime with prebuilt pydantic-core wheels (e.g., CPython 3.11) or install Rust toolchain for wheel compilation.
- If you want vector/full-text search enabled, confirm that the target DocumentDB cluster supports createSearchIndexes (some clusters/tiers or control-plane settings may not allow it). When createSearchIndexes is supported, the sample's create_search_indexes function will create a vector-hnsw and text index; you may want to tune index type and parameters (vector-diskann vs vector-hnsw) for production scale.
- LLM/embedding integration (LangChain/OpenAI) was intentionally not installed to keep the sample lightweight and verifiable. If you supply OPENAI_API_KEY and add LangChain/OpenAI to requirements, adjust processor.py to call the real APIs (currently it uses a deterministic heuristic fallback) and ensure EMBEDDING_DIM matches the chosen model.

## Files

- `.env.example`
- `README.md`
- `requirements.txt`
- `pytest.ini`
- `src/app/db.py`
- `src/app/models.py`
- `src/app/processor.py`
- `src/scripts/seed.py`
- `src/scripts/aggregations.py`

