Clinical Trial Matching — DocumentDB + LangChain sample

What this sample shows

- A small Python LangChain orchestration that:
  - Accepts a patient profile JSON
  - Uses embedding-based similarity to rank clinical trials stored in Azure DocumentDB
  - Applies an eligibility agent to evaluate inclusion/exclusion rules
  - Uses a consent agent (LLM) to produce a plain-language trial summary for the patient
  - Stores match results back into DocumentDB

Key decisions made

- Language/runtime: Python (3.13 available on the build machine).
- Embeddings: OpenAI text-embedding-3-small (1536 dims) when OPENAI_API_KEY is provided; otherwise the seed uses random vectors for local testing.
- LLM for agents: OpenAI gpt-3.5-turbo via OPENAI_API_KEY (sample will fall back to deterministic text if key missing).
- DB connection: DOCUMENTDB_URI environment variable (do not check secrets into repo).
- Indexes: scalar indexes (criteria.conditions, criteria.min_age/max_age) created by the seed; attempt to create a vector index via the documentdb MCP server is made during verification but the sample works without it by doing client-side ranking.

Prerequisites

- Python 3.11+ (the build machine has Python 3.13)
- A reachable Azure DocumentDB cluster; set DOCUMENTDB_URI in your environment. Do NOT put connection strings in files.
- (Optional) OpenAI API key in OPENAI_API_KEY to generate real embeddings and run the LLM agents.

Quickstart

1. Create a virtualenv and install dependencies

   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   pip install -r requirements.txt

2. Copy the example env and fill values

   cp .env.example .env
   # Edit .env and provide DOCUMENTDB_URI and OPENAI_API_KEY (optional)

3. Seed sample data (creates collection, scalar indexes, and inserts documents)

   python seed.py

4. Run a one-shot match demo

   python demo.py

5. (Optional) Run the FastAPI app

   uvicorn app.main:app --reload --port 8000
   POST http://localhost:8000/match with a JSON body of a patient profile

Cleaning up

- The sample does not provision Azure resources. To remove the seeded documents, connect to your cluster and drop the 'sample_healthcare_02' database or the 'trials' collection created by the seed script.

Security and privacy

- This sample uses synthetic data only. Do NOT use real patient data when experimenting unless you have appropriate approvals and safeguards.

Files of interest

- app/main.py — FastAPI app and match orchestration
- app/db.py — MongoClient singleton and helper functions
- seed.py — Seed script to create sample trials and indexes
- demo.py — Runs a sample match end-to-end (calls the same code as FastAPI do)
- .env.example — Environment variable placeholders

Limitations

- The sample uses client-side ranking for vector similarity if the environment or MCP call to create a service-side vector index is not available.
- LLM calls are optional (require OPENAI_API_KEY). When absent, the eligibility agent uses deterministic rule checks and the consent agent produces a simple templated summary.

