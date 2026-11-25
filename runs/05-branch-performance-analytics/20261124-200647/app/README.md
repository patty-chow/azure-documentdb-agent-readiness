Branch Performance Analytics Sample

What this sample shows

- A Python FastAPI service that computes per-branch performance summaries from a `transactions` collection using aggregation with $facet and caches results in a `branch_summaries` collection.
- A seed script that synthesizes sample transactions for ~10 branches.
- An endpoint to refresh cached summaries and an endpoint to ask natural-language questions about the cached summaries via a LangChain-style tool that uses OpenAI.

Prerequisites

- Python 3.11+ and pip
- An Azure DocumentDB (mongoClusters) cluster reachable from this machine. The connection string must be available in the environment variable DOCUMENTDB_URI.
- (Optional) An OpenAI API key in OPENAI_API_KEY to enable the /ask endpoint.

Quickstart

1. Install dependencies:

   python -m pip install -r requirements.txt

2. Create an .env file based on .env.example and set DOCUMENTDB_URI (and OPENAI_API_KEY if using /ask).

3. Seed sample data:

   python scripts/seed.py

4. Refresh summaries (compute and cache):

   python scripts/refresh_summaries.py

5. Run the FastAPI service:

   uvicorn app.main:app --reload

6. Endpoints

- GET /metrics/branches/{branch_id} — fetch cached summary for a branch
- POST /summaries/refresh — trigger recompute of all branch summaries (server-side aggregation)
- POST /ask — JSON body {"query":"..."}, returns an NL answer synthesized by the LLM and provenance (matched branches)

Security

- The app reads DOCUMENTDB_URI and OPENAI_API_KEY from environment variables. Never commit secrets to the repository.

Extending the sample

- The sample uses lexical retrieval over cached summaries. To add vector/hybrid search, pick an embedding model and create a DocumentDB vector index with matching dimensions (see the readiness report). The documentdb-vector-search skill has guidance for index kinds and tuning.

Files

- app/main.py — FastAPI app and endpoints
- app/db.py — Mongo client helper
- scripts/seed.py — creates sample transactions and indexes
- scripts/refresh_summaries.py — runs aggregation and upserts into branch_summaries
- .env.example — example environment variables

