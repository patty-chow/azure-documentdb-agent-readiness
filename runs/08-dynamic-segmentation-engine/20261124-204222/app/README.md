Dynamic segmentation engine sample for Azure DocumentDB (mongoClusters)

What this sample shows

- Connect to an Azure DocumentDB (MongoDB-compatible) cluster using pymongo and a singleton MongoClient.
- Seed a small customers + events dataset and create appropriate indexes (idempotent seed).
- An aggregation tool that computes per-customer behavioural metrics: recency (days since last event), frequency (events in a recent window), and category affinity (top categories and ratios).
- A LangChain-compatible agent wrapper that injects segmentation rules and assigns a segment label; if an OpenAI key is present the agent will use the LLM, otherwise a deterministic rule-based assigner is used.
- Write the assigned segment back to the customer's profile document in DocumentDB.
- A CLI demo and a small FastAPI endpoint (POST /segment) to trigger segmentation.

Prerequisites

- Python 3.13 on PATH (the environment used to build this sample).
- A reachable Azure DocumentDB cluster. Set the DOCUMENTDB_URI environment variable to the cluster connection string before running.
- (Optional) OPENAI_API_KEY if you want the LangChain agent to use OpenAI. If absent the sample uses a deterministic rules engine.

Quickstart

1. Copy environment template and set values:

   cp .env.example .env
   # edit .env and set DOCUMENTDB_URI (and OPENAI_API_KEY if available)

2. Install dependencies:

   pip install -r requirements.txt

3. Seed the sample data (idempotent):

   python scripts/seed.py

4. Run a one-shot segmentation for a demo customer (CLI):

   python -m src.cli --customer_id cust_1

   This will compute metrics, assign a segment label, write it back to the customers collection, and print the result.

5. (Optional) Start the HTTP demo server:

   uvicorn src.app:app --reload --port 8000

   POST to http://localhost:8000/segment with JSON {"customer_id":"cust_1"}

Cleaning up

- Remove the sample data by deleting the sample_customer_360_08 database from your cluster. This sample does not provide an automated teardown. Use your DocumentDB/Mongo tooling or the Azure portal.

Security note

- Never commit your DOCUMENTDB_URI or OPENAI_API_KEY to source control. This sample reads secrets from environment variables. See .env.example.

Files created

- src/ (application code)
- scripts/seed.py (idempotent seeding and index creation)
- requirements.txt
- .env.example
- README.md

See the built-in tests in tests/ for a basic aggregation check.
