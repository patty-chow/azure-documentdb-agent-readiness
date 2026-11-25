# 3. Build report: 19-care-coordination-multi-agent

**Status: partial**

Built a Python LangChain multi-agent sample that demonstrates reading patient records from an Azure DocumentDB cluster, retrieving referrals and medications via three simple agent classes, and an orchestrator that synthesises a care plan using an LLM. The repository includes an idempotent seed script that created collections and single-field indexes on the live cluster and unit tests that validate the orchestration flow (LLM calls are mocked). End-to-end synthesis against a live LLM/embeddings provider was not executed because the environment did not provide LLM/embedding credentials (OPENAI_API_KEY), so the final insertion of a real LLM-synthesised care plan was not verified live. See files_created for the app layout and the README for run instructions.

## How to run

1) Create and activate a virtualenv, install deps: pip install -r requirements.txt
2) Copy .env.example -> .env and set DOCUMENTDB_URI to your cluster connection string. Optionally set OPENAI_API_KEY, LLM_MODEL, EMBEDDING_MODEL if you want real LLM/embedding calls.
3) Seed the DB (idempotent): python seed_data.py
4) Run the CLI orchestrator (requires OPENAI_API_KEY to synthesise): python run_orchestrator.py --patient-id patient-001
5) Run the API: uvicorn app.api:app --reload and POST to /orchestrate with JSON {"patient_id": "patient-001"}
6) Run unit tests (they mock the LLM + DB for verification): pytest -q

## Verified by running

- pytest: 1 passed (tests/test_orchestrator.py)
- seed_data.py: ran successfully and reported 'Seed complete. Collections: patients, referrals, medications. DB: sample_healthcare_19'
- documentdb_list_databases (MCP): returned sample_healthcare_19 with collections patients (2), referrals (1), medications (2)
- documentdb_sample_documents (MCP): sampled documents from patients collection (2 documents returned)
- documentdb_list_indexes (MCP): patients collection indexes listed; idx_patient_id present

## Not verified

- End-to-end orchestrator run against a live LLM/embeddings provider: not executed because OPENAI_API_KEY / embedding credentials were not present in the environment.
- Vector index creation and vector-based retrieval: not created by default. The sample documents and seed script create only single-field patient_id indexes; vector index creation is documented in README and requires choosing embedding model/dimensions and credentials.
- Full hybrid search (BM25 + vector) and $search index examples: not exercised in this sample run.

## Open issues

- No OPENAI_API_KEY (or other LLM/embedding provider key) was available in the environment. Without credentials, the orchestrator cannot synthesise a real care plan via an LLM; tests mock LLM calls instead.
- Vector indexes were intentionally omitted by default because embedding model/dimension and credentials are environment-dependent. If you want vector search enabled, set OPENAI_API_KEY and EMBEDDING_MODEL and follow the README notes to create a vector index with the correct 'dimensions' parameter.
- LangChain warning: importing OpenAI from langchain root module is deprecated (warnings are printed). The sample uses langchain.OpenAI for simplicity as a common usage path; consider using the newer ChatOpenAI interface and updating LLM instantiation if desired.
- The sample uses pinned dependency versions chosen by the builder; users may wish to upgrade them to match their environment.

## Files

- `README.md`
- `requirements.txt`
- `.env.example`
- `app/__init__.py`
- `app/db.py`
- `app/agents.py`
- `app/orchestrator.py`
- `app/api.py`
- `seed_data.py`
- `run_orchestrator.py`
- `tests/test_orchestrator.py`
- `LICENSE`

