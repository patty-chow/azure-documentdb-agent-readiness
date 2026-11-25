# 3. Build report: 11-care-gap-identification-pipeline

**Status: completed**

Built a Python sample that seeds a synthetic patients+visits dataset into an existing Azure DocumentDB cluster (database sample_healthcare_11), creates recommended indexes, runs an aggregation to identify care gaps (colon cancer screening, mammogram, diabetes HbA1c), and provides a LangChain agent wrapper that prioritizes patients and generates outreach talking points (LLM call is optional and runs only if OPENAI_API_KEY is provided). Verified seeding, aggregation and local prioritization logic against the live cluster and inspected collections/indexes via the DocumentDB MCP server.

## How to run

1. Create and activate a Python venv (Python 3.10+). Example: python -m venv .venv && source .venv/bin/activate
2. pip install -r requirements.txt
3. Copy .env.example to .env and set DOCUMENTDB_URI to your connection string. Optionally set OPENAI_API_KEY and OPENAI_MODEL for LLM features.
4. python src/seed.py   # creates collections, indexes and loads synthetic sample data into sample_healthcare_11
5. python src/main.py   # runs the aggregation to find care gaps, prints a summary, and runs the (optional) prioritization/talking-points step

Notes:
- The LangChain/LLM step is skipped/heuristic if OPENAI_API_KEY is not set. The code is safe to run without an LLM key.

## Verified by running

- pip install -r requirements.txt: completed (packages installed)
- python src/seed.py: completed (120 patients and 224 visits inserted)
- python src/main.py: completed (aggregation run; 38 patients with care gaps found; heuristic prioritization and talking points generated)
- documentdb_list_databases: returned sample_healthcare_11 with patients (120) and visits (224)
- documentdb_list_indexes for patients: returned index list (including patient_id, diagnosis_codes, dob)
- documentdb_list_indexes for visits: returned compound index on (patient_id, visit_date -1)

## Not verified

- Live LLM-driven LangChain agent output parsing and JSON extraction: not executed with an API key in this run (the code falls back to a local heuristic when OPENAI_API_KEY is absent). Reason: no trusted LLM credentials present in the runtime environment; the app is written to skip live LLM calls unless the developer supplies OPENAI_API_KEY (documented in README).
- Microsoft Entra ID (OIDC) authentication flow was not exercised: sample uses DOCUMENTDB_URI (SCRAM) per environment; Entra/OIDC example is documented in README as optional. Reason: run_policy and sample scope prefixed to use DOCUMENTDB_URI and not modify cluster settings.

## Open issues

- No OpenAI API key present during verification so LLM-driven prioritization/talking points were not validated end-to-end; the code will run the LLM step if OPENAI_API_KEY is set and network access to the provider is available.
- Vector search / embeddings not implemented here (intentionally). The sample focuses on aggregation + LLM prompt engineering; vector-based hybrid search could be added as an extension.

## Files

- `requirements.txt`
- `.env.example`
- `README.md`
- `src/db.py`
- `src/seed.py`
- `src/main.py`
- `src/agent.py`

