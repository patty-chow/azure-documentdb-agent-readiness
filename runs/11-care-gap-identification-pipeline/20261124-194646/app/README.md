Azure DocumentDB Sample: Care Gap Identification Pipeline

This sample shows a Python LangChain agent that uses Azure DocumentDB (MongoDB-wire) aggregations to identify patients missing recommended screenings and generates prioritized outreach talking points.

What it demonstrates
- Connect to an Azure DocumentDB cluster using DOCUMENTDB_URI (SCRAM credentials) from the environment
- Seed a small synthetic healthcare dataset (patients + visits) into database `sample_healthcare_11`
- Run an aggregation to compute last-visit and identify care gaps based on simple guideline rules (age, diagnosis, last visit)
- A LangChain agent wrapper (optional) that will prioritize patients and produce outreach talking points using an LLM. The agent is skipped if no OPENAI_API_KEY is present.

Files
- src/db.py - Mongo client and DB helpers
- src/seed.py - Seed script to create collections, indexes and load synthetic data
- src/agent.py - LangChain agent wrapper and LLM integration (skipped if no key)
- src/main.py - CLI entrypoint: run aggregation and optionally the agent
- .env.example - example environment variables

Prerequisites
- Python 3.10+ and pip
- An Azure DocumentDB connection string in the environment variable DOCUMENTDB_URI
- (Optional) OPENAI_API_KEY for the LLM features

Quickstart
1. python -m venv .venv && source .venv/bin/activate
2. pip install -r requirements.txt
3. cp .env.example .env and fill DOCUMENTDB_URI (and OPENAI_API_KEY if you want LLM outputs)
4. python src/seed.py   # creates collections, indexes, and inserts sample data
5. python src/main.py   # runs the aggregation and prints flagged patients; tries the LLM if key is present

Security
- Do not commit secrets. The seed uses synthetic data only.

Notes
- This sample deliberately avoids vector search to keep the example focused on aggregation and prompt/context engineering. See README for pointers if you want to extend using vector indexes.
