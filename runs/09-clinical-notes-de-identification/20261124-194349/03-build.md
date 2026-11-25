# 3. Build report: 09-clinical-notes-de-identification

**Status: completed**

Created a small Python sample that demonstrates de-identifying clinical notes stored in an Azure DocumentDB (MongoDB API) cluster using Beanie ODM. The repo includes Beanie models (RawNote, DeidNote), an idempotent seed script (seed.py) with 5 synthetic clinical notes, a de-identification pipeline CLI (deid_pipeline.py) that supports a safe local dry-run (regex) and an OpenAI-backed run mode, helper DB initialization, tests, and instructions. I verified dependency installation, seeding, a dry-run de-identification which wrote DeidNote documents, index creation via a short Motor script, and unit tests. I attempted to use the documentdb MCP insertion and index APIs but fell back to the included code where the MCP tool failed during the run; those MCP failures are recorded below.

## How to run

1) Create & activate a Python venv (Python 3.13 used here).
2) pip install -r requirements.txt
3) Copy .env.example to .env and set DOCUMENTDB_URI (do NOT commit secrets). Optionally set OPENAI_API_KEY and OPENAI_MODEL for run mode.
4) Seed sample data: python seed.py
5) Dry-run de-id without calling OpenAI (safe): python deid_pipeline.py dry-run
6) To call OpenAI (will send notes to model): export OPENAI_API_KEY=sk-... && python deid_pipeline.py run
7) Create indexes (if you want to run from code): python create_indexes.py
8) Run unit tests: pytest
Notes: The sample uses the database sample_healthcare_09. The scripts read the DOCUMENTDB_URI from the environment. The dry-run mode uses a simple regex-based deid and is safe for CI; run mode uses OpenAI and requires OPENAI_API_KEY.

## Verified by running

- pip install -r requirements.txt: succeeded
- seed.py: ran and inserted 5 synthetic RawNote documents into sample_healthcare_09.raw_notes: 'Inserted 5 synthetic notes.'
- deid_pipeline.py dry-run: ran and created 5 DeidNote documents in sample_healthcare_09.deid_notes: 'Created 5 de-identified notes'
- documentdb MCP find: retrieved deid_notes and confirmed 5 de-identified documents (documentdb_find_documents returned total_count 5)
- create_indexes.py (Motor): ran and created indexes idx_sourceId and idx_created_at on deid_notes: 'Created indexes: idx_sourceId idx_created_at'
- documentdb MCP list_indexes: returned 3 indexes (including _id_, idx_sourceId, idx_created_at)
- pytest: 2 passed

## Not verified

- documentdb_insert_documents (MCP) for seeding: attempted twice and failed with 'Error: Function failed.' — I retried once then used the project seed script as a fallback.
- documentdb_create_index (MCP): attempted twice and failed with 'Error: Function failed.' — fallback was to create indexes with a local Motor script which succeeded.
- deid_pipeline.py run (OpenAI): NOT executed against OpenAI in verification because OPENAI_API_KEY was not provided in the environment during verification. The code path is present and will call OpenAI.ChatCompletion.create when an API key is supplied.
- Full end-to-end run using Beanie + OpenAI against the live cluster: not executed (see previous point).

## Open issues

- documentdb MCP insertion and index-creation tools returned errors during this run; I retried once for each operation and fell back to the sample scripts which performed the necessary DB inserts and index creation. If you prefer MCP-based verification, investigate MCP server availability or permissions in this environment.
- The sample's OpenAI run mode was not executed (no API key used during verification). Users who run the pipeline in 'run' mode must supply OPENAI_API_KEY and should review rate limits and model choice in README.
- Beanie / driver version choices were picked for stability in this environment (requirements.txt pinned). If your environment requires different versions, adjust requirements.txt accordingly.

## Files

- `requirements.txt`
- `src/models.py`
- `src/db.py`
- `src/__init__.py`
- `seed.py`
- `deid_pipeline.py`
- `.env.example`
- `README.md`
- `tests/test_models.py`
- `tests/conftest.py`
- `create_indexes.py`

