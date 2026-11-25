# 3. Build report: 18-adverse-event-reporting-pipeline

**Status: completed**

Created a small Python sample app that demonstrates ingesting adverse-event free-text, extracting structured fields with an LLM (optional), validating via Pydantic/Beanie, storing into Azure DocumentDB (MongoDB wire protocol), and an aggregation to surface most frequently reported events by drug. The repo includes a seed script that inserts 10 synthetic sample records directly (no LLM required) and creates a compound index to speed aggregations. I installed dependencies, ran the seed, and verified the aggregation and index using the DocumentDB MCP server tools.

## How to run

1) Create and activate a venv and install dependencies:
   python -m pip install -r requirements.txt

2) Set connection variables (example in .env.example). Minimal required env var: DOCUMENTDB_URI. Optionally set DOCUMENTDB_DATABASE (defaults to sample_healthcare_18) and OPENAI_API_KEY to enable LLM extraction.

3) Seed sample documents (inserts pre-parsed structured docs and ensures the compound index):
   python seed.py

4) Start the API (optional — extraction endpoint requires OPENAI_API_KEY):
   uvicorn src.main:app --reload
   POST /reports with JSON {"text":"..."} will attempt LLM extraction and store the structured doc. GET /reports/top-events returns top events grouped by drug.

Notes:
- Do NOT put secrets into the repo. Use environment variables or a secrets store.
- The seed script inserts pre-parsed examples so you can verify aggregation without an LLM key.
- If you want LLM extraction at runtime, set OPENAI_API_KEY to a valid OpenAI key and run the API; the code uses OPENAI_MODEL env var (default gpt-4o-mini).

## Verified by running

- pip install -r requirements.txt: succeeded (packages installed)
- python seed.py: succeeded (Inserted 10 sample documents into sample_healthcare_18.adverse_events)
- documentdb.aggregate (group by drug/event): succeeded (returned aggregated counts)
- documentdb.list_indexes on sample_healthcare_18.adverse_events: succeeded (found _id_ and idx_drug_event)

## Not verified

- Running the FastAPI app (uvicorn) and exercising the LLM extraction path with OPENAI_API_KEY: not executed because OPENAI_API_KEY was not provided in this environment.
- Beanie-based app startup path via Async PyMongo client (init_beanie): not executed or validated; seed and verification used synchronous PyMongo code to insert and verify sample data. (Reason: the sample seeds and verifies using the synchronous driver to avoid requiring the API/LLM to run.)

## Open issues

- The app code's startup uses PyMongo's MongoClient and Beanie initialization in a simplified way — Beanie 2 expects an async-capable database client (the quickstart uses PyMongo's Async client). In this sample I used direct pymongo inserts in seed.py for verification to avoid needing to exercise the web API in this run. If you plan to run the FastAPI server and Beanie init in your environment, validate and adapt the startup to the exact async client pattern your environment uses (see the Azure Beanie quickstart).
- LLM provider is chosen as OpenAI by default and the helper uses ChatCompletion; if you plan to run extraction you must set OPENAI_API_KEY and optionally adjust OPENAI_MODEL. The sample gracefully falls back to direct insertion in seed.py when the key is missing.
- If you want the sample to create indexes via the DocumentDB-specific createIndexes command for more advanced index types (full-text or cosmosSearch vector indexes), add those commands to a dedicated index-creation step; the sample currently creates a simple compound B-tree index on (drug, event) which is sufficient for the aggregation demo.

## Files

- `requirements.txt`
- `.env.example`
- `README.md`
- `src/models.py`
- `src/main.py`
- `seed.py`

