Care Gap Identification Pipeline

This sample demonstrates a Python LangChain-style agent that uses a DocumentDB (MongoDB-compatible) aggregation tool to identify patients missing recommended screenings, prioritise them, and generate outreach talking points.

What it shows
- Connecting to an Azure DocumentDB MongoDB-compatible cluster via pymongo (DOCUMENTDB_URI env var)
- Idempotent seed script that creates collections and indexes and inserts sample patient and visit documents
- A small agent pipeline that runs server-side aggregations to compute last visit dates and identifies care gaps using guideline context injected into prompts
- Prioritisation and generation of outreach talking points via an LLM (OpenAI-compatible). Falls back to templated messages if OPENAI_API_KEY is not set.

Prerequisites
- Python 3.10+
- DOCUMENTDB_URI environment variable pointing to the MongoDB connection string for the sample_healthcare_11 database. Do NOT store secrets in the repo.
- (Optional) OPENAI_API_KEY for LLM-powered prioritisation and messages. If not present the sample will generate simple templated talking points.

Files of interest
- src/db.py: Database helpers (connect, seed, indexes)
- src/pipeline.py: Care gap detection, LangChain-like agent wrapper and orchestration
- scripts/seed_data.py: Idempotent seeding script
- run_pipeline.py: Demo CLI that runs the end-to-end sample and prints results
- .env.example: Example environment variables

Quickstart
1) Create and activate a virtualenv (recommended)
   python -m venv .venv
   source .venv/bin/activate   # mac/linux
   .\.venv\Scripts\activate  # windows
2) Install dependencies
   pip install -r requirements.txt
3) Populate sample data (reads DOCUMENTDB_URI from environment)
   python scripts/seed_data.py
4) Run the pipeline
   python run_pipeline.py

Cleanup
- The sample is non-destructive. To remove seeded data, connect with a Mongo client and drop the 'patients' and 'visits' collections from the 'sample_healthcare_11' database.

Security
- Do not commit real PHI. This sample uses synthetic data.
- DOCUMENTDB_URI must be provided via environment; see .env.example

Limitations
- Vector indexes are not created; the seed script creates conventional indexes only (provider-specific vector index creation was intentionally avoided). See readiness report for details.
