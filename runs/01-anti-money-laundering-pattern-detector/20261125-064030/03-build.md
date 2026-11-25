# 3. Build report: 01-anti-money-laundering-pattern-detector

**Status: completed**

Built a small Python sample that demonstrates DocumentDB (MongoDB-compatible) aggregation-based AML detection. The sample uses PyMongo to connect to the cluster via DOCUMENTDB_URI, seeds an idempotent synthetic dataset in database `sample_banking_01`, creates recommended indexes, follows transaction chains (attempting $graphLookup and falling back to client-side traversal), applies simple AML rules (structuring, rapid pass-through, circular transfers), and produces structured suspicious-chain narratives. Optional OpenAI summarization is supported when OPENAI_API_KEY is provided. I verified dependency installation, data seeding and the detector run against the live cluster in this environment.

## How to run

1) Create and activate a venv (recommended):
   python -m venv .venv
   source .venv/bin/activate  # macOS / Linux
   .\.venv\Scripts\activate  # Windows (PowerShell)

2) Install dependencies:
   pip install -r requirements.txt

3) Copy .env.example to .env and set values (DOCUMENTDB_URI is required; OPENAI_API_KEY optional):
   cp .env.example .env
   # fill DOCUMENTDB_URI and optionally OPENAI_API_KEY

4) Seed sample data (idempotent):
   python -m src.seed_data

5) Run the detector and print JSON narratives:
   python -m src.run_detector --limit 10

Notes:
- The sample reads DOCUMENTDB_URI and OPENAI_API_KEY from the environment (.env supported via python-dotenv).
- The detector will try to use server-side $graphLookup. If the server rejects it, the code falls back to a client-side traversal implementation.

## Verified by running

- pip install -r requirements.txt: succeeded (dependencies installed into the active Python environment).
- python -m src.seed_data: succeeded (seeded sample data into sample_banking_01 database).
- python -m src.run_detector --limit 10: succeeded (detector ran and printed 3 flagged chains; sample output verified).

## Not verified

- Full $graphLookup behavior matrix across DocumentDB vector index configs — the code performs a runtime check (supports_graph_lookup) and falls back if unsupported, but detailed cluster-specific vector index createIndex parameter names were not programmatically validated because cluster management operations are disallowed by policy.
- LangChain 'agent' orchestration beyond optional integration: the code is LangChain-friendly (langchain is a dependency) but the sample implements the aggregation tool and optional OpenAI summarization; complex LangChain agent flows (tool-using AgentExecutor with RL or long-term memory) were intentionally omitted to keep the sample compact and self-contained.
- OpenAI summarization was not exercised in this run because OPENAI_API_KEY may not have been set in the environment (the code will use OpenAI when the key is present).

## Open issues

None.

## Files

- `README.md`
- `requirements.txt`
- `.env.example`
- `src/__init__.py`
- `src/db.py`
- `src/seed_data.py`
- `src/detector.py`
- `src/run_detector.py`
- `tests/test_seed_and_detect.py`

