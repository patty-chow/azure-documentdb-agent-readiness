Seasonal Trend Spotter Agent (DocumentDB + Web Search)

What this sample shows

- A small Python "LangChain-style" agent that uses two tools:
  - a DocumentDB aggregation tool that computes sales velocity across seasons from a `sales` collection in database `sample_retail_17`.
  - a web-search tool that fetches trend signals for categories (pluggable provider: Bing if BING_API_KEY is provided, otherwise a mock fallback).
- How to seed synthetic sample data (idempotent), create an index to support the aggregation, run the agent locally, and clean up.

Prerequisites

- Python 3.10+ (3.11 recommended)
- A reachable Azure DocumentDB cluster with a MongoDB-compatible connection string in the environment variable DOCUMENTDB_URI. Do NOT store secrets in this repo.
- Optional: OPENAI_API_KEY for an LLM summarizer; BING_API_KEY for web search. If these are not present the sample falls back to local deterministic logic and mock web-search results so it can run for demos without keys.

Files

- requirements.txt — Python dependencies
- .env.example — example environment variables
- scripts/seed_data.py — idempotent seeding of synthetic sales data
- src/tools/documentdb_tool.py — DocumentDB aggregation tool
- src/tools/web_search_tool.py — Web search tool (pluggable provider)
- src/main.py — CLI entrypoint that runs the sample end-to-end

Quickstart

1. Create and activate a virtual environment:
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows

2. Install dependencies:
   pip install -r requirements.txt

3. Copy and edit environment file:
   cp .env.example .env
   # Set DOCUMENTDB_URI to your cluster connection string. Optionally set OPENAI_API_KEY and BING_API_KEY.

4. Seed the sample data (idempotent):
   python scripts/seed_data.py

5. Run the example agent:
   python src/main.py --run

Notes

- The sample uses a singleton MongoClient pattern and reads DOCUMENTDB_URI at runtime (per documentdb-driver guidance).
- No cloud resources are provisioned by this sample; it uses an existing cluster.

Cleanup

- To remove sample documents, connect to the cluster and drop the `sample_retail_17.sales` collection, or use the script to delete documents (not included to avoid accidental data loss).

Limitations

- The web-search provider in this sample is pluggable; if no API key is provided the tool returns mock signals. This keeps the example runnable in constrained environments.

