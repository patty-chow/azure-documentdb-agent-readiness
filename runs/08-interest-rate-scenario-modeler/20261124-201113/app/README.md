Interest Rate Scenario Modeler (Azure DocumentDB + LangChain)

What this sample shows

- How to seed a positions collection in an Azure DocumentDB (MongoDB-compatible) cluster and create a simple index.
- A Python "aggregation tool" that groups fixed and floating rate positions into maturity buckets and summarizes exposures.
- A minimal LangChain-based scenario analyzer that prompts an LLM (OpenAI) to reason about Net Interest Income (NII) impact under parallel shift, steepening, and inversion scenarios and returns a structured JSON report.

Prerequisites

- Python 3.10+ and pip
- An Azure DocumentDB cluster reachable from this machine. Set the connection string in the environment variable DOCUMENTDB_URI (do NOT store secrets in repo).
- (For LLM) An OpenAI API key in OPENAI_API_KEY if you want to run the agent.

Files

- src/db.py: MongoDB client singleton and helper to get the positions collection.
- src/seed.py: Idempotent seed script to insert sample positions (upserts by position_id).
- src/aggregation_tool.py: Aggregation pipeline that buckets maturities and groups by rate_type.
- src/agent.py: LangChain-based scenario analyzer that uses the aggregation tool and asks an LLM to reason about scenarios.
- .env.example: example env variables (placeholders)
- requirements.txt: Python dependencies
- tests/: unit tests that run without a live cluster or LLM.

Quick start

1. Create and activate a Python virtualenv, then install deps:

    python -m venv .venv
    source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows
    pip install -r requirements.txt

2. Set environment variables (example):

    export DOCUMENTDB_URI="mongodb://<username>:<password>@host:10255/?ssl=true&replicaSet=globaldb"
    export OPENAI_API_KEY="sk-..."

   Or use a .env and your shell's preferred method.

3. Seed sample data (idempotent):

    python -m src.seed

4. Run the aggregation tool from the CLI to print grouped exposures:

    python -c "from src.aggregation_tool import summarize_positions; print(summarize_positions())"

5. Run the scenario analyzer (this will call OpenAI if OPENAI_API_KEY is set):

    python -m src.agent

Cleanup

- The seed script upserts by position_id. To remove sample data manually, drop the collection using your preferred MongoDB tooling.

Notes and decisions

- Language/runtime: Python 3.x (see README) — decision logged in the build report.
- LLM provider: OpenAI, model: gpt-4 — configured via OPENAI_API_KEY (not committed).
- No embeddings/vector search used to keep the sample focused.
- Maturity buckets: 0-1y, 1-3y, 3-5y, 5-10y, >10y.
- Index: created on {maturity_date: 1, rate_type: 1} to support aggregation.

See BUILD_REPORT.json for details of what was executed during the automated build and verification.
