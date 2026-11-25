Customer 360 orchestration sample for Azure DocumentDB

What this sample shows
- A Python LangChain orchestration pipeline with three agents: ingest, dedup, and enrich.
- Uses an Azure DocumentDB (MongoDB wire protocol) cluster; connection read from DOCUMENTDB_URI.
- Stores customer profiles in database `sample_customer_360_18`, collection `customers`.
- Uses an LLM (OpenAI) for dedup matching and embeddings (text-embedding-3-small) for vector search.
- Logs each batch run to the `workflows` collection.

Prerequisites
- Python available (the environment's `python`/`pip` will be used).
- An Azure DocumentDB cluster reachable; set DOCUMENTDB_URI in your .env.
- OpenAI API key in OPENAI_API_KEY for the LLM and embeddings (or set to blank to use heuristics).

Setup
1. python -m venv .venv
2. source .venv/bin/activate  # or .venv\Scripts\activate on Windows
3. pip install -r requirements.txt
4. cp .env.example .env and fill DOCUMENTDB_URI and OPENAI_API_KEY

Run the sample
- Seed sample incoming records: python seed.py
- Run the pipeline once: python run_pipeline.py

Files
- seed.py: loads sample incoming records into `incoming` collection (idempotent upsert by email).
- run_pipeline.py: runs ingest -> dedup -> enrich and records a workflow document.
- src/db.py: Mongo client singleton.
- tests/: pytest-based unit tests (mocks DB and LLM).

Cleanup
- Remove sample documents by deleting the `customers`, `incoming`, and `workflows` collections from the `sample_customer_360_18` database.

Notes
- Do not commit secrets. Keep DOCUMENTDB_URI and OPENAI_API_KEY in your environment and never in source control.
- This sample is for demo purposes only; do not use in production without security reviews and proper IAM/networking.
