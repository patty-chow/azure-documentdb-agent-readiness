Sample: Customer review sentiment pipeline using Azure DocumentDB (MongoDB-compatible) and Beanie ODM

This sample shows an async Python pipeline that:
- Seeds a small set of synthetic product reviews into an Azure DocumentDB database (database: sample_retail_07, collection: reviews)
- Enriches each review with a sentiment score and tags by calling OpenAI (or using a local mock when OPENAI_API_KEY is not set)
- Upserts enriched documents back into DocumentDB using Beanie
- Runs a summary aggregation grouped by product and sentiment

Prerequisites
- Python 3.11+ on PATH (the run environment here has Python 3.13).
- A reachable Azure DocumentDB cluster; set DOCUMENTDB_URI in environment (see .env.example)
- (Optional) An OpenAI API key in OPENAI_API_KEY to enable real LLM enrichment. If not set, the pipeline runs in mock mode.

Setup
1. Create and activate a virtual environment (recommended):
   python -m venv .venv
   source .venv/bin/activate   # or .\.venv\Scripts\activate on Windows
2. Install dependencies:
   python -m pip install -r requirements.txt
3. Copy .env.example to .env and fill in DOCUMENTDB_URI and OPENAI_API_KEY (if you have one).

Seed data
- The seed script loads data/sample_reviews.json and upserts into sample_retail_07.reviews.

Run the pipeline (mock mode if OPENAI_API_KEY absent)
- Seed:
    python scripts/seed.py
- Run enrichment pipeline:
    python scripts/run_pipeline.py
- Run aggregation report:
    python scripts/aggregate.py

What this demonstrates
- Beanie async ODM usage with Azure DocumentDB (MongoDB wire protocol)
- Declaring indexes in the Beanie model
- A simple, bounded-concurrency LLM enrichment pattern with a mock fallback
- Aggregation pipelines for reporting

Cleaning up
- Delete the 'sample_retail_07' database or the 'reviews' collection via your preferred admin tool.

Notes
- Never commit secrets. Use .env (not checked in) to store DOCUMENTDB_URI and OPENAI_API_KEY.
- This sample intentionally keeps the dataset small to avoid costs.
