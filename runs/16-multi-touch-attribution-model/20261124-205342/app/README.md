Multi-Touch Attribution Sample for Azure DocumentDB

Overview

This sample demonstrates how to read customer journey event documents from an Azure DocumentDB (MongoDB-compatible) cluster, compute simple attribution models (first-touch, last-touch, linear), and store versioned attribution results per customer. It also exposes a small LangChain-based tool that lets marketers ask natural-language questions about attribution results.

Prerequisites

- Python 3.10+ (the environment here provides `python`)
- An Azure DocumentDB cluster reachable with a connection string in the environment variable DOCUMENTDB_URI
- An OpenAI API key in OPENAI_API_KEY (used by the LangChain tool)

Important: Do NOT commit your DOCUMENTDB_URI or OPENAI_API_KEY to source control. Use .env and .env.example.

What this sample shows

- How to connect to Azure DocumentDB using pymongo (singleton MongoClient pattern)
- How to seed a small synthetic events dataset
- How to run attribution aggregations (first-touch, last-touch, linear)
- How to store versioned attribution results per customer
- A simple LangChain/OpenAI tool to ask natural-language questions about attribution results

Repository structure

- src/: application code (db, attribution logic, LangChain glue, FastAPI app)
- scripts/seed.py: idempotent seed script to load sample events into the live cluster
- scripts/run_attribution.py: runs attribution pipelines and stores results
- tests/: unit tests for attribution logic (uses mongomock)
- .env.example: placeholder for environment variables
- requirements.txt: pinned Python dependencies

Setup

1. Create and activate a virtual environment

   python -m venv .venv
   source .venv/bin/activate   # or .\.venv\Scripts\activate on Windows

2. Install dependencies

   pip install -r requirements.txt

3. Create a .env file from .env.example and fill values (do not commit)

   cp .env.example .env
   # edit .env and set DOCUMENTDB_URI and OPENAI_API_KEY

4. Seed the database (writes to the live cluster pointed to by DOCUMENTDB_URI)

   python scripts/seed.py

5. Run the attribution pipelines (stores versioned results in attribution_results)

   python scripts/run_attribution.py

6. (Optional) Start the HTTP API

   uvicorn src.app:app --reload

   POST /run-attribution  -> triggers pipelines
   POST /query           -> accepts {"customer_id": "<id>", "question": "..."}

7. Run unit tests

   pytest -q

Cleaning up

- Remove the sample data by deleting the collections created (events, attribution_results) using your preferred MongoDB tool. Do not run any destructive azure control-plane commands from this sample.

Notes & limitations

- This sample connects to the live cluster provided via DOCUMENTDB_URI. The run environment disallows provisioning new Azure resources.
- The LangChain tool uses OpenAI via environment variable OPENAI_API_KEY. If you prefer Azure OpenAI, adapt the LangChain config accordingly.

License

MIT
