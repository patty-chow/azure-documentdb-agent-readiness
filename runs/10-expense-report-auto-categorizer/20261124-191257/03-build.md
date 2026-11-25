# 3. Build report: 10-expense-report-auto-categorizer

**Status: completed**

Built a small Python sample app that uses Beanie ODM against an Azure DocumentDB cluster to seed expense reports, process submitted reports with a LangChain-capable classifier (with a deterministic fallback for demo runs), persist enriched documents back to the database, and create useful indexes. The sample is runnable without an LLM API key (deterministic fallback) so it can be verified in this environment. Key design choices and trade-offs were logged to the audit trail before acting.

## How to run

1) Create and activate a virtualenv (Python 3.10+ recommended):
   python -m venv .venv
   source .venv/bin/activate   # or .\.venv\Scripts\activate on Windows

2) Install dependencies:
   pip install -r requirements.txt

3) Copy .env.example to .env and set DOCUMENTDB_URI to your cluster (SRV form recommended). Optionally set OPENAI_API_KEY to enable the AI pathway.

4) Seed sample data (idempotent):
   python -m src.seed

5) (Optional) Create indexes used by the sample:
   python -m src.indexes

6) Run the processor in deterministic demo mode (does not require an AI key):
   python main.py --no-ai

7) To run with LangChain/OpenAI (real AI): ensure OPENAI_API_KEY is set and run
   python main.py

Notes: No Azure resources were provisioned by this sample. The app reads DOCUMENTDB_URI from the environment and writes no secrets to files.

## Verified by running

- pip install -r requirements.txt: succeeded (packages installed or already present in venv).
- python -m src.seed: succeeded — seeded 3 sample reports (idempotent upsert).
- python -m src.indexes: succeeded — created indexes idx_status and idx_submitter_date on collection 'expense_reports'.
- documentdb_list_indexes (MCP server): listed 3 indexes (_id_, idx_status, idx_submitter_date) for sample_fintech_10.expense_reports.
- python main.py --no-ai: succeeded — processed submitted reports and updated 3 reports; printed per-item classification and final counts.

## Not verified

- AI-driven LangChain path with a real OpenAI API key (OPENAI_API_KEY) was not executed in this run because no API key was provided in the environment; the code path exists and will be used when OPENAI_API_KEY is set.
- Vector indexes or embedding-based features: intentionally not created because the embedding model and output dimension were unspecified in the prompt and readiness report flagged this as a gap; creating vector indexes requires choosing an embedding model/dimension first.
- Complete cross-version compatibility matrix for Beanie + Motor + PyMongo against Azure DocumentDB (MongoDB 7.0 wire) was not exhaustively tested. The readiness report noted this gap; the sample uses Motor because it integrates with Beanie, and the decision was logged as model_default.

## Open issues

None.

## Files

- `requirements.txt`
- `.env.example`
- `README.md`
- `src/models.py`
- `src/db.py`
- `src/seed.py`
- `src/processor.py`
- `src/indexes.py`
- `main.py`

