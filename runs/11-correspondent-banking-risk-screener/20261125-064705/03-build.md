# 3. Build report: 11-correspondent-banking-risk-screener

**Status: completed**

Created a small Python LangChain-style sample that embeds correspondent profiles, seeds them into the provided DocumentDB (MongoDB-compatible) cluster, performs client-side vector similarity search against sanctions and adverse-media entries, and returns a risk score plus a plain-language narrative. The sample is runnable locally, uses environment variables for secrets, includes an idempotent seed script and unit tests, and was verified with dependency installation, unit tests, seeding (using deterministic synthetic embeddings when an OpenAI key was not present), and a demo review run.

## How to run

1) Create and activate a venv, then install dependencies:
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   pip install -r requirements.txt

2) Provide secrets via environment variables (do NOT commit real secrets). Copy .env.example to .env or set env vars:
   - DOCUMENTDB_URI (required)
   - OPENAI_API_KEY (optional; if absent the sample uses deterministic synthetic embeddings for demonstration)
   - OPENAI_API_BASE (optional, if using Azure OpenAI endpoints)

3) Seed the sample data (idempotent):
   python scripts/run_seed.py

4) Run an example review (calls the agent logic and prints JSON):
   python scripts/run_example.py

5) To run the HTTP API (optional):
   uvicorn src.main:app --reload
   POST /review with JSON {"correspondent_id":"c1"} or {"profile_text":"..."}

6) Run unit tests:
   pytest -q


## Verified by running

- pip install -r requirements.txt: exit code 0, dependencies installed
- pytest -q: 4 passed, 2 warnings
- python scripts/run_seed.py (via scripts/run_seed.py wrapper): seeded 2 correspondents, 2 sanctions, 2 adverse_media (used deterministic synthetic embeddings because OPENAI_API_KEY was not set)
- python scripts/run_example.py: executed review_correspondent(correspondent_id='c1') and returned risk_score, matches and risk_narrative; sample output printed successfully

## Not verified

- Server-side vector index creation (HNSW/IVF/DiskANN) on the managed DocumentDB cluster: exact createIndex parameters and server-side vector index creation were not attempted. Reason: the run environment didn't include the DocumentDB Agent Kit and exact createIndex parameter names for the managed cluster were ambiguous. The seed script creates safe basic indexes and stores embeddings; it falls back to client-side similarity to avoid relying on an undocumented createIndex call.
- Live OpenAI embeddings and LLM generation: embedding and narrative-generation calls using a real OPENAI_API_KEY were not executed in this run because OPENAI_API_KEY was not present. The code supports calling OpenAI (src/embeddings.py uses openai.Embeddings and src/agent.py will call a chat model when OPENAI_API_KEY is present), but in verification the sample used deterministic synthetic embeddings and the fallback narrative generator to keep the demo runnable without secrets.

## Open issues

- Server-side vector indexes: For production / performant large-scale search you should create a server-side vector index (HNSW, IVF or DiskANN) on the 'embedding' field. The sample intentionally uses client-side similarity for the demo; the repo README points this out and recommends creating proper vector indexes per provider docs.
- If you want the sample to compute real embeddings and LLM narratives during seeding and review, set OPENAI_API_KEY (and OPENAI_API_BASE if using Azure OpenAI) in the environment before running seed or the API. The code will then call the OpenAI API directly.
- This sample does not attempt to change Azure resource configuration (provisioning or server-side index changes) because Azure resource writes were disallowed by policy and because some createIndex parameters for the managed cluster were not authoritative in the provided materials. If you add the official DocumentDB Agent Kit or refer to the provider docs, you can add server-side createIndex logic.

## Files

- `requirements.txt`
- `.env.example`
- `README.md`
- `data/correspondents.json`
- `data/sanctions.json`
- `data/adverse_media.json`
- `src/__init__.py`
- `src/db.py`
- `src/embeddings.py`
- `src/agent.py`
- `src/main.py`
- `scripts/seed.py`
- `scripts/run_seed.py`
- `scripts/run_example.py`
- `tests/test_agent.py`
- `tests/conftest.py`

