# 3. Build report: 07-customer-review-sentiment-pipeline

**Status: partial**

I began implementing the async Python Beanie pipeline but was only able to complete planning steps and load a couple of DocumentDB skills. I recorded two architecture decisions (async driver and OpenAI model) and loaded the documentdb-driver and documentdb-connection skills. I hit a tooling/parsing error while recording the index-choice decision and was subsequently prevented from creating files or running the pipeline in this turn. The repository files (package, scripts, README, .env.example, requirements) were planned but not written. Full code, index creation, seeding, and verification remain to be executed.

## How to run

Planned instructions (to be used once the files are created):

1) Create a Python 3.11 virtualenv and activate it (example):
   python -m venv .venv
   source .venv/bin/activate    # Linux/macOS
   .venv\Scripts\activate     # Windows

2) Install dependencies:
   pip install -r requirements.txt

3) Create a .env file from .env.example and set these environment variables:
   DOCUMENTDB_URI=<your DocumentDB MongoDB connection string>
   OPENAI_API_KEY=<your OpenAI API key>

4) Seed the sample data (idempotent):
   python scripts/seed_sample_data.py

5) Run the async pipeline to enrich raw reviews and upsert results:
   python -m sample_retail_07.run_pipeline

6) (Optional) Run the aggregation summary script to print counts and average sentiment per product and sentiment bucket:
   python -m sample_retail_07.summary

7) Cleanup: use the README guidance to drop created collections or delete the sample database if desired.

## Verified by running

- load_skill: documentdb-driver — succeeded
- load_skill: documentdb-connection — succeeded
- log_decision: Chose Beanie + Motor (AsyncIOMotorClient) as the async driver — recorded
- log_decision: Chose OpenAI model 'gpt-3.5-turbo' and env var OPENAI_API_KEY — recorded

## Not verified

- Writing project files (package, modules, scripts, README, .env.example, requirements.txt) — not done because file writes were not executed in this turn.
- pip install of requirements and runtime dependency verification — not run.
- Running seed script to load synthetic sample data into 'sample_retail_07.raw_reviews' — not run.
- Running the async pipeline to call OpenAI and upsert enriched documents into 'sample_retail_07.reviews' — not run.
- Creating indexes on the live cluster (product_id, tags multikey, sentiment_bucket) via the documentdb MCP server — not run.
- Executing aggregation summary on the live cluster and verifying results via documentdb MCP aggregate/explain — not run.

## Open issues

- I attempted to record the index-shape decision via the audit trail tool but the tool returned a parsing error; that prevented a clean recorded decision for the index plan. The intended index plan is: product_id (single-field), tags (multikey), sentiment_bucket (single-field).
- I did not create any files in the workspace this turn due to a tooling/flow restriction; the planned files and code still need to be written and tested.
- The Beanie vs PyMongo async-driver compatibility gap noted in the readiness report remains an open verification item. I selected Motor (AsyncIOMotorClient) for compatibility with Beanie, but the documentdb-connection skill recommends PyMongo AsyncMongoClient for new async code. This choice must be validated when installing dependencies and running the pipeline; if PyMongo AsyncMongoClient is preferred, the Beanie setup may need adjustment or a different Beanie release.
- Index vs vector decision: I chose NOT to include vector indexes (no embeddings) to keep the sample focused. If the user prefers embedding-based theme extraction and vector search, a vector index must be created with exact embedding dimensions (and the code updated to compute and store embeddings).

## Files

None.

