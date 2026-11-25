Customer 360 sample with Azure DocumentDB + LangChain

What this shows

- A small Python LangChain-based orchestration pipeline with three agents:
  - ingest agent: normalizes incoming customer records and upserts them into Azure DocumentDB
  - dedup agent: identifies & merges duplicate profiles (LLM-assisted with a deterministic fallback)
  - enrich agent: appends firmographic/demographic signals (synthetic in this sample)
- A workflow document is written per batch run (collection `workflows`).
- Demonstrates creating a native vector index for semantic matching (via the documentdb MCP tool) and a unique email index.

Prerequisites

- Python (the run environment already provides a virtualenv; `python`/`pip` resolve to it).
- An Azure DocumentDB cluster reachable from this machine. Set DOCUMENTDB_URI in your environment (or in a local `.env`) to the cluster connection string. Do not store secrets in the repo.
- (Optional) OpenAI API key in OPENAI_API_KEY to enable LLM-assisted dedupe and real embeddings. If not present, the sample falls back to deterministic behavior so it can still be run for verification.

Files of interest

- src/db.py - MongoDB client singleton and helpers
- src/pipeline.py - Ingest/Dedup/Enrich agents and orchestrator
- seed.py - Idempotent seeding/upsert of synthetic sample customer records
- run_pipeline.py - CLI entrypoint to run the pipeline
- .env.example - example environment variables

Quickstart

1. Copy .env.example to .env and fill DOCUMENTDB_URI and optionally OPENAI_API_KEY
   cp .env.example .env
   # edit .env

2. Install dependencies
   python -m pip install -r requirements.txt

3. Seed the sample data (idempotent upserts)
   python seed.py

4. Run the pipeline (ingest -> dedupe -> enrich)
   python run_pipeline.py --run

5. Inspect the `customers` and `workflows` collections in database `sample_customer_360_18`.

Cleanup

- Remove sample documents by dropping the `customers` and `workflows` collections, or remove the `sample_customer_360_18` database (do not run in production).

Security

- Never commit your DOCUMENTDB_URI or OPENAI_API_KEY. These are read from the environment or a local `.env` file loaded at runtime.

Notes

- The sample creates a native vector `cosmosSearch` index via the documentdb MCP server for accurate options — see the code and the build report for the exact index created.
- For real enrichment, replace the synthetic enrich logic with calls to your third-party signal provider.
