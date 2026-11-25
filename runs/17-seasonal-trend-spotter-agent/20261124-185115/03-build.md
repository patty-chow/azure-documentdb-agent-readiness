# 3. Build report: 17-seasonal-trend-spotter-agent

**Status: completed**

Built a small Python LangChain-style agent sample that (1) seeds an idempotent synthetic `sales` dataset into the existing DocumentDB cluster, (2) defines a DocumentDB aggregation tool that computes seasonal sales velocity, (3) defines a pluggable web-search tool (Bing when BING_API_KEY present, mock fallback otherwise), and (4) combines both signals into a ranked list printed to stdout. I verified dependency install, seeding, index presence, an aggregation run via the documentdb MCP server, and the end-to-end example run producing a JSON ranked list.

## How to run

1) Create & activate a virtualenv (Python 3.10+). 2) pip install -r requirements.txt. 3) cp .env.example .env and set DOCUMENTDB_URI to your cluster connection string. Optionally set BING_API_KEY and/or OPENAI_API_KEY. 4) Seed data (idempotent): python scripts/seed_data.py. 5) Run the example agent flow: python src/main.py --run. The script prints the combined ranking JSON to stdout.

## Verified by running

- pip install -r requirements.txt: succeeded (packages installed/available)
- scripts/seed_data.py: ran and inserted documents into sample_retail_17.sales (seed completed, inserted ~1494 new documents during this run).
- documentdb_list_databases (MCP): returned database sample_retail_17 with collection 'sales' and counts (sales count: 1798).
- documentdb_list_indexes (MCP): showed indexes including category_1_sale_date_1 (index exists).
- documentdb_aggregate (MCP): ran aggregation pipeline that computed seasonal totals and returned results (20 rows returned in the test pipeline).
- python src/main.py --run: ran end-to-end flow using the DocumentDB aggregation tool and web-search tool (mock fallback) and printed a combined ranking JSON.

## Not verified

- Calling real Bing Web Search API: not executed because BING_API_KEY was not provided in the environment (the web-search tool used a deterministic mock fallback).
- Using an external LLM (OpenAI) for summarization: not executed because OPENAI_API_KEY was not provided; the sample supports it but falls back to deterministic logic in absence of a key.
- Vector index creation / vector-search features: not used or created in this sample (the sample focuses on aggregation + web search signals).
- Provisioning a DocumentDB cluster: intentionally not performed (run policy forbids Azure writes). The sample uses an existing cluster per the run environment.

## Open issues

- The seed script attempted to create a unique index on tx_id; duplicates already existed in the collection and the script reports a warning and proceeds. If the user expects a clean unique index, duplicate tx_id values must be resolved manually before creating the unique index.
- If you want live web-search signals or LLM summarization, set BING_API_KEY/BING_ENDPOINT and/or OPENAI_API_KEY in .env and re-run; the sample will then use the live services but may incur API costs.
- For production or larger-scale demos, consider adding tighter dependency pinning and tests that exercise both the live-key path and the mock path.

## Files

- `requirements.txt`
- `README.md`
- `.env.example`
- `scripts/seed_data.py`
- `src/tools/documentdb_tool.py`
- `src/tools/web_search_tool.py`
- `src/main.py`

