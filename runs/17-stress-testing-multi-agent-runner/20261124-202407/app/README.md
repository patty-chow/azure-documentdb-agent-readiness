Azure DocumentDB Sample: LangChain Multi-Agent Stress Test

What this sample shows
- A small Python-based multi-agent stress-testing orchestrator.
- ScenarioAgent: generates macroeconomic shock parameters.
- ImpactAgent: runs aggregation pipelines against an Azure DocumentDB (Mongo-compatible) cluster to compute P&L impacts.
- ReportingAgent: synthesises a structured report and stores the run as a DocumentDB document for audit.

Prerequisites
- Python 3.10+ (3.11 recommended).
- A reachable Azure DocumentDB cluster. Set DOCUMENTDB_URI in a .env file or environment.
- (Optional) OPENAI_API_KEY if you want LLM-generated textual summaries.

Quickstart
1. Create virtualenv and install dependencies
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2. Copy .env.example to .env and set DOCUMENTDB_URI and optional OPENAI_API_KEY.

3. Seed sample data (idempotent):
   python -m src.seed

4. Run a stress test (CLI):
   python -m src.run_stress_test --sample_size 100

Files created in your sample database (DB_NAME from .env or env):
- positions collection: sample positions inserted/updated by the seed script.
- stress_runs collection: each run is persisted with scenario parameters and impact summary.

Cleaning up
- Delete the two collections from your cluster or drop the sample database.

Security
- Never commit secrets. Use environment variables; see .env.example.

Notes
- This sample uses synchronous PyMongo MongoClient and a singleton client per process (documentdb-driver guidance).
- The LLM step is optional; reporting will fall back to a deterministic summary if OPENAI_API_KEY is not provided.
