Sample: Credit Risk Multi-Agent Scorer (sample_fintech_06)

This sample shows a small multi-agent pipeline that reads applicant data from an Azure DocumentDB (MongoDB-compatible) cluster, scores the applicant using simple rules and an optional LLM (LangChain/OpenAI), and writes the score and explanation back to the applicant document.

Prerequisites
- Python 3.10+ (system python available)
- A reachable Azure DocumentDB cluster and its MongoDB connection string in env var DOCUMENTDB_URI
- (Optional) OPENAI_API_KEY if you want the LLM agents to call OpenAI. If not set, run with --mock.

Quickstart
1. Create a virtualenv and install:
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2. Copy .env.example to .env and set DOCUMENTDB_URI (and optionally OPENAI_API_KEY).

3. Seed sample data (idempotent):
   python -m sample_fintech_06.seed

4. Run the pipeline end-to-end against an applicant (mock LLM mode):
   python -m sample_fintech_06.run --applicant-id applicant-1 --mock

5. To run tests (they use mock mode and the live cluster):
   pytest -q

Files
- sample_fintech_06/: package with db client, agents, seed and runner
- tests/: pytest verifying the pipeline with mock LLM

Security
- Do not commit your real DOCUMENTDB_URI or OPENAI_API_KEY. Use .env to provide secrets at runtime.
