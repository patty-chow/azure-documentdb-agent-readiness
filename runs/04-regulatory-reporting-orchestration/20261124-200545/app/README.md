Azure DocumentDB Sample: Regulatory Reporting Orchestration (Python)

This sample demonstrates a small LangChain-style orchestration pipeline that
queries an Azure DocumentDB (MongoDB-compatible) cluster for reporting-period
data, runs simple validation, and formats a regulatory-style filing. The
orchestrator logs each step as a workflow_runs document in the DocumentDB
cluster.

Prerequisites
- Python 3.10+ (the run environment has Python 3.13)
- A reachable Azure DocumentDB cluster connection string in DOCUMENTDB_URI
- (Optional) OpenAI API key in OPENAI_API_KEY to enable LLM-driven validation/formatting

Setup
1. Create and activate a virtualenv:
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
2. Install dependencies:
   pip install -r requirements.txt
3. Copy .env.example to .env and fill in DOCUMENTDB_URI (and OPENAI_API_KEY if desired).
4. Seed the sample data (idempotent):
   python scripts/seed.py --count 100
5. Run the orchestration for a reporting period (e.g., 2023-Q4):
   python scripts/run_report.py --period 2023-Q4

What this sample shows
- How to connect to Azure DocumentDB using PyMongo and a singleton client
- A simple three-agent orchestration: DataExtractionAgent, ValidationAgent, FilingAgent
- Workflow logging into a workflow_runs collection
- Idempotent seed script to populate accounts, transactions, and positions

Files of interest
- src/db.py: MongoClient singleton and helpers
- src/orchestrator.py: Orchestration pipeline and agents
- scripts/seed.py: Seed data into sample_banking_04 (safe to run twice)
- scripts/run_report.py: CLI that runs the pipeline and writes the filing to examples/

Security note
Do not store DOCUMENTDB_URI or any credentials in the repository. Use environment
variables or secure secret stores. This sample reads the connection string from
DOCUMENTDB_URI at runtime.
