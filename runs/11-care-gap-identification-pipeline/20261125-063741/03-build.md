# 3. Build report: 11-care-gap-identification-pipeline

**Status: completed**

Implemented a small Python sample that demonstrates a LangChain-style agent workflow against an Azure DocumentDB (MongoDB-compatible) cluster. The sample connects using DOCUMENTDB_URI, creates conventional indexes, seeds synthetic patient and visit data, runs a care-gap detection pipeline (aggregation + in-Python logic), and produces a prioritized outreach list with talking points. The LLM path uses OpenAI (if OPENAI_API_KEY is set), otherwise falls back to deterministic templates. Unit tests for the gap-detection logic were added and passed. All work was done without provisioning Azure resources.

## How to run

1) Create and activate a virtualenv (recommended):
   python -m venv .venv
   source .venv/bin/activate   # mac/linux
   .\.venv\Scripts\activate  # windows
2) Install dependencies:
   pip install -r requirements.txt
3) Provide DOCUMENTDB_URI in your environment (and optionally OPENAI_API_KEY and OPENAI_MODEL). See .env.example for placeholders.
4) Seed sample data (idempotent):
   python -c "import sys; sys.path.insert(0, '.'); from src.db import load_sample_data; load_sample_data()"
5) Run the pipeline end-to-end (prints JSON):
   python -c "import sys, json; sys.path.insert(0, '.'); from src.pipeline import run_end_to_end; print(json.dumps(run_end_to_end(), default=str, indent=2))"
6) Run unit tests (no live DB required):
   python -c "import sys; sys.path.insert(0, '.'); import pytest; raise SystemExit(pytest.main(['-q']))"

Notes:
- Do not commit real credentials; read DOCUMENTDB_URI from env. See .env.example.
- The sample intentionally creates conventional (B-tree) indexes only. Vector-index creation is provider-specific and was not attempted in code.

## Verified by running

- pip install -r requirements.txt: succeeded (installed pymongo, langchain, openai, python-dotenv, pytest, ...).
- pytest: 2 passed (tests/test_pipeline.py) - verified detect_gaps behavior with in-memory fixtures.
- Seed data script executed against live cluster: created/ensured indexes and inserted sample patients and visits (script run via: python -c "import sys; sys.path.insert(0, '.'); from src.db import load_sample_data; load_sample_data()" ). Output: Ensured indexes: patients->idx_patients_diagnoses, visits->idx_visits_patient_visitdate; Inserted sample patients and visits.
- End-to-end pipeline executed against live cluster (python -c "... from src.pipeline import run_end_to_end ..."): produced a prioritized list with talking points. Because OPENAI_API_KEY was not set in the environment, the sample used the fallback templated messages (heuristic path). Example output (abbreviated): list of patients p2, p4, p1 with priority scores and templated talking_points.

## Not verified

- Creation of provider-specific vector indexes (DiskANN/HNSW/IVF) was not attempted because the exact createIndex syntax/options are provider-specific and not present in local documentation; readiness guidance recommended not to create these automatically.
- LLM-based prioritisation and JSON-structured reply via the OpenAI client: not executed in verification because OPENAI_API_KEY was not present; the code path is present and will call OpenAI when the env var is provided.
- Authentication modes other than credentials embedded in DOCUMENTDB_URI (e.g., AAD token auth) were not implemented or tested; the code reads DOCUMENTDB_URI and uses it as-is. The cluster's auth surface (AAD vs SCRAM) was not programmatically detected or altered.

## Open issues

- Vector-index creation remains unimplemented due to missing authoritative provider index syntax. If you need vector search examples on this specific cluster, provide provider docs or an accelerator and I'll add an idempotent vector-index creation step.
- If you prefer the sample to actually call an LLM during verification, set OPENAI_API_KEY and optionally OPENAI_MODEL in the environment and re-run the pipeline to verify the LLM path.
- A small warning from pymongo was emitted indicating the endpoint appears to be CosmosDB-compatible; the sample uses standard pymongo and runs fine, but consider reviewing provider-specific compatibility notes if you hit feature incompatibilities.

## Files

- `requirements.txt`
- `README.md`
- `.env.example`
- `src/__init__.py`
- `src/db.py`
- `src/pipeline.py`
- `scripts/seed_data.py`
- `run_pipeline.py`
- `tests/test_pipeline.py`

