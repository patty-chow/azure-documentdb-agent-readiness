# 3. Build report: 12-clv-prediction-pipeline

**Status: completed**

Implemented a Python sample that demonstrates computing customer metrics (purchase frequency, average order value, tenure) against an Azure DocumentDB cluster, seeding sample data, creating a multikey index, and a LangChain-based agent that calls an LLM to assign a CLV score/tier and persist it back to the customer document. Code, tests, and scripts were added and unit/integration checks were executed against the live cluster where possible. The LLM classification step is implemented but could not be executed in this run because OPENAI_API_KEY was not set in the environment.

## How to run

1) Create and activate a virtualenv and install deps:
   python -m venv .venv
   source .venv/bin/activate   # or .venv\Scripts\activate on Windows
   pip install -r requirements.txt

2) Set required environment variables (or create a .env file):
   export DOCUMENTDB_URI="<your-documentdb-uri>"
   export OPENAI_API_KEY="<your-openai-key>"   # required only for the LLM step

3) Seed sample data (idempotent):
   python -c "import sys; sys.path.append('src'); from seed import seed; seed()"

4) Create sample index (if not already created by the script):
   python -c "import sys; sys.path.append('src'); from db import get_customers_collection; coll=get_customers_collection(); print(coll.create_index([('purchases.date',1)], name='purchases_date_idx'))"

5) Run the CLV agent for a customer (this will call the LLM if OPENAI_API_KEY is set):
   # seed and then run
   python run_clv.py --seed --customer-id sample_cust_1

6) Run the tests (they exercise aggregation and DB update logic but do not require OPENAI_API_KEY):
   pytest -q

Notes:
- The app reads DOCUMENTDB_URI and OPENAI_API_KEY only from environment variables. Do not check secrets into source control. Use .env.example as a template.
- The LangChain agent uses OpenAI gpt-3.5-turbo by default; set OPENAI_API_KEY to enable the LLM classification step.

## Verified by running

- pip install -r requirements.txt: succeeded
- Index creation: created multikey index on purchases.date via local pymongo script (src/create_indexes.py / inline python command): succeeded
- Seed sample data: seeded sample customers into database 'sample_customer_360_12' collection 'customers' via src/seed.py: succeeded
- pytest: 1 passed (tests/test_clv.py verifies compute_customer_metrics and update_customer_clv and DB writes): succeeded
- documentdb_list_indexes (MCP): returned 2 indexes (_id_ and purchases_date_idx): succeeded
- documentdb_sample_documents (MCP): returned sample documents including seeded customers (one document shows clv fields after test update): succeeded

## Not verified

- End-to-end LangChain agent call to external LLM (OpenAI): not executed because OPENAI_API_KEY was not present in the environment; the code path is implemented (src/agent.py) and will run when the OPENAI_API_KEY env var is set.
- documentdb_create_index MCP tool: attempted but the MCP call failed with 'Error: Function failed.'; index creation was performed via pymongo as a workaround.

## Open issues

- If you want the agent to run against an LLM during CI or automated verification, set OPENAI_API_KEY in the environment and re-run run_clv.py (or run compute_and_classify for a customer).
- documentdb_create_index MCP tool failure — investigate MCP server availability if you expect to prefer MCP-based index management instead of client-side index creation.

## Files

- `requirements.txt`
- `README.md`
- `.env.example`
- `src/__init__.py`
- `src/db.py`
- `src/seed.py`
- `src/create_indexes.py`
- `src/clv_tool.py`
- `src/agent.py`
- `run_clv.py`
- `tests/test_clv.py`

