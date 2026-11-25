Clinical Notes De-identification Sample (Azure DocumentDB + Beanie)

Overview
- This sample shows a simple Python pipeline that reads raw clinical notes from an Azure DocumentDB cluster (MongoDB API), sends each note to a de-identification routine (either a safe local dry-run or OpenAI), and writes a de-identified document referencing the original via `sourceId`.

What it demonstrates
- Beanie ODM models for RawNote and DeidNote
- Singleton async DB initialization using Motor and Beanie
- Seed script to insert synthetic clinical notes (idempotent)
- A `deid_pipeline.py` CLI with `dry-run` (local regex) and `run` (OpenAI) modes

Prerequisites
- Python 3.13
- An Azure DocumentDB cluster reachable from this machine. Set DOCUMENTDB_URI in environment (see .env.example). The sample uses database `sample_healthcare_09`.
- For full OpenAI de-identification, set OPENAI_API_KEY. Use dry-run for offline testing.

Quickstart
1. Create and activate a venv
   python -m venv .venv
   source .venv/bin/activate   (Linux/macOS)
   .\.venv\\Scripts\\activate  (Windows)
2. Install dependencies
   pip install -r requirements.txt
3. Copy .env.example to .env and set DOCUMENTDB_URI (DO NOT commit secrets)
4. Seed sample data
   python seed.py
5. Run dry-run (safe, does not call OpenAI)
   python deid_pipeline.py dry-run
6. To run against OpenAI (will call the API):
   export OPENAI_API_KEY=sk-...
   python deid_pipeline.py run

Security
- All provided notes are synthetic. Never commit real PHI to version control. The sample avoids printing note contents. Connection strings and API keys must be provided via environment variables.

Cleaning up
- Delete the `raw_notes` and `deid_notes` collections from the `sample_healthcare_09` database when finished using your preferred tool (mongosh, Azure portal, or the documentdb MCP server).

Files
- src/models.py - Beanie Document models
- src/db.py - DB initialization helper
- seed.py - idempotent seeding of synthetic notes
- deid_pipeline.py - CLI pipeline (dry-run and OpenAI run modes)
- .env.example - example environment file
- requirements.txt - pinned dependencies

License: MIT
