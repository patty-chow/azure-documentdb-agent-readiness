Loan Origination Orchestrator Sample

This sample demonstrates an orchestration pipeline that models each loan application as a state-machine document in Azure DocumentDB (MongoDB wire protocol) using Beanie. The orchestrator advances applications through states (submitted → underwriting → compliance → approved/rejected) by delegating to "specialist agents", updating the current_state atomically and recording a transition log.

Prerequisites
- Python (the environment has Python 3.13)
- A reachable Azure DocumentDB cluster; set DOCUMENTDB_URI in your environment or .env

Setup
1. python -m venv .venv && source .venv/bin/activate (or your platform equivalent)
2. pip install -r requirements.txt
3. Copy .env.example to .env and set DOCUMENTDB_URI

Run the sample
1. python scripts/seed.py  # creates a sample loan application (upsert)
2. python run_orchestrator.py  # runs the orchestrator once and logs transitions

What it shows
- Beanie modeling for loan applications
- Atomic state transitions using find_one_and_update (filter on expected current_state and $push transition)
- Transition logs with timestamps
- Optional LangChain LLM agents if OPENAI_API_KEY is set; otherwise deterministic stub agents are used.

Inspect the DB
- The sample uses database `sample_fintech_14` and collection `loan_applications`.
- Use the documentdb MCP server tools or your preferred mongosh client to inspect documents and indexes.

Cleanup
- Delete the sample document(s) from the collection, or drop the collection in your DB.

Notes
- Do not commit your DOCUMENTDB_URI or any secrets. Read them from environment variables at runtime.
