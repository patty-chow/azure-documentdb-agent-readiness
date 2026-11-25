# 3. Build report: 06-order-history-timeline-agent

**Status: completed**

Created a small Python LangChain-compatible sample that demonstrates a conversational 'order history' agent backed by an Azure DocumentDB (MongoDB-compatible) cluster. The sample includes an idempotent seeder (seed.py) which creates indexes and inserts 300 synthetic orders into database sample_retail_06.orders, a lightweight agent/tool layer that exposes three tools (fetch order history, spend summary, order lookup), a deterministic demo run (works without an LLM key), and tests that run against the live cluster. I verified seeding, indexes, queries, an explain plan (index usage), and ran tests. The LangChain/LLM path is implemented but not executed because OPENAI_API_KEY was not present in this run (the agent builds LangChain objects lazily; set OPENAI_API_KEY to run the LLM-backed agent). Decision logs were recorded during the build for choices like language, LLM provider, and indexing approach.

## How to run

1) Create and activate a virtualenv (recommended):
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate

2) Install dependencies:
   pip install -r requirements.txt

3) Copy .env.example to .env and fill DOCUMENTDB_URI (and OPENAI_API_KEY if you want the LLM path):
   cp .env.example .env

4) Seed sample data (idempotent):
   python seed.py

5) Run the demonstration (deterministic, no LLM required):
   python run_agent.py
   - If you set OPENAI_API_KEY in the environment, run_agent.py will try to build a LangChain agent and use the LLM. The LLM path requires a working OpenAI API key and appropriate extras for langchain.

6) Run tests against the live cluster:
   pytest -q

Notes:
- DOCUMENTDB_URI must be set in your environment or .env. Do not commit secrets.
- The sample writes only to database 'sample_retail_06' collection 'orders'.

## Verified by running

- pip install -r requirements.txt: exit code 0 (dependencies installed or already present).
- python seed.py: ran successfully and inserted/upserted sample data (script printed 'Seeding ...' and 'Done').
- documentdb_count_documents(sample_retail_06.orders): returned count 300 via MCP documentdb_count_documents tool.
- documentdb_list_indexes(sample_retail_06.orders): returned 4 indexes (_id_, idx_order_id_unique, idx_customer_date, idx_order_date) via MCP documentdb_list_indexes.
- pytest tests/test_db.py: 1 passed (seed + queries verified against live cluster).
- python run_agent.py (deterministic demo): ran successfully (no OPENAI_API_KEY). It:
  - discovered a demo customer
  - fetched 5 most recent orders for that customer
  - executed a 'last_month' spend summary using the same in-memory conversational context and printed a JSON summary.
- documentdb_explain_operation (find with customer_id + sort): returned executionStats showing the 'idx_customer_date' index was used (winning plan contains IXSCAN on idx_customer_date) via MCP documentdb_explain_operation.

## Not verified

- LLM-backed LangChain agent end-to-end: I did not run the LLM-backed agent because OPENAI_API_KEY was not present (build_langchain_agent is implemented and will exercise langchain/OpenAI when the env var is set).
- LangChain 'chat' conversational behavior with a real LLM and follow-up resolution through tool-calls: not executed (requires OPENAI_API_KEY and possibly additional langchain community extras).
- Vector-search or full-text search features (createSearchIndexes / cosmosSearch vector indexes): not implemented or exercised in this sample because the sample focuses on order-history and aggregation examples; none of the DocumentDB vector or text-search features were created or verified.

## Open issues

- To run the LLM-backed agent, set OPENAI_API_KEY in the environment. Depending on the langchain installation, you may need to install additional 'langchain_community' extras (the sample imports langchain lazily; if a missing optional package error occurs when building the LLM agent, install the required extras).
- This sample uses the live DocumentDB cluster reachable from this environment. If you want to run in a CI environment without access to the cluster, add mocking or a local DocumentDB gateway container and adapt configuration (.env) accordingly.
- The agent's natural-language parsing in tools is minimal (key=value parsing and a 'last_month' token). The LLM + tool orchestration is a representative pattern; production usage should add better intent parsing, entity extraction, robust date parsing, validation and error handling.

## Files

- `README.md`
- `.env.example`
- `requirements.txt`
- `.gitignore`
- `seed.py`
- `run_agent.py`
- `src/__init__.py`
- `src/pkgagent/__init__.py`
- `src/pkgagent/db.py`
- `src/pkgagent/agent.py`
- `pkgagent/__init__.py`
- `tests/test_db.py`

