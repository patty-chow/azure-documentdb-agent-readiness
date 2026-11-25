# 3. Build report: 08-interest-rate-scenario-modeler

**Status: partial**

Sample app implemented: a Python LangChain-based interest-rate scenario modeler with a DocumentDB aggregation tool. Unit tests passed, the idempotent seed script inserted 60 sample positions into the reachable DocumentDB cluster, the aggregation pipeline ran and returned grouped exposures by maturity bucket and rate type, and a supporting index was created programmatically. The LLM end-to-end run was not executed because OPENAI_API_KEY was not set in the build environment. An attempt to use the documentdb_create_index MCP tool failed; programmatic index creation was used instead.

## How to run

1) Set environment variables:
   - DOCUMENTDB_URI (required) - connection string to the Azure DocumentDB/Mongo cluster
   - OPENAI_API_KEY (optional) - OpenAI API key to run the analyzer
   - DATABASE_NAME (optional; default sample_banking_08)

2) Create and activate a Python venv, then install deps:
   python -m venv .venv
   source .venv/bin/activate  # or the Windows equivalent
   pip install -r requirements.txt

3) Seed sample data (idempotent):
   python -m src.seed

4) Run aggregation (prints grouped exposures):
   python -c "from src.aggregation_tool import summarize_positions; import json; print(json.dumps(summarize_positions(), indent=2, default=str))"

5) Run the scenario analyzer (calls LLM if OPENAI_API_KEY is set):
   python -m src.agent

Notes: Do NOT commit secrets. See README.md for details.

## Verified by running

- pip install -r requirements.txt: succeeded
- pytest: 2 passed (unit tests check prompt formatters, no live DB/LLM required)
- python -m src.seed: seed completed (60 upserts) against database 'sample_banking_08'
- Aggregation: summarize_positions() executed against the live cluster and returned grouped results; index 'idx_maturity_rate_type' was created programmatically via pymongo.create_index

## Not verified

- documentdb_create_index MCP tool: attempted but failed with 'Error: Function failed.'; could not verify MCP-based index creation
- LLM full end-to-end: not executed because OPENAI_API_KEY was not set in the build environment
- Automated infrastructure provisioning (Bicep/Terraform): not attempted (sample uses a preprovisioned cluster)

## Open issues

- documentdb_create_index MCP tool failed in this environment; investigate MCP server connectivity/permissions if MCP-based index creation is required.
- LangChain/OpenAI model compatibility: consumers should set OPENAI_MODEL or pin exact langchain/openai versions for reproducible behavior.

## Files

- `README.md`
- `.env.example`
- `requirements.txt`
- `src/__init__.py`
- `src/db.py`
- `src/seed.py`
- `src/aggregation_tool.py`
- `src/agent.py`
- `tests/test_formatters.py`
- `tests/conftest.py`
- `BUILD_REPORT.json`

