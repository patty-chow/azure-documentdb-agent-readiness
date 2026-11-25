# 3. Build report: 13-algorithmic-trade-journal

**Status: completed**

Built a small Python/FastAPI sample that records immutable trading events (signals, executions, outcomes) into an Azure DocumentDB (MongoDB-compatible) cluster and computes per-strategy statistics (win rate, avg P&L, total P&L, trade count). Because a canonical server-side max-drawdown aggregation example was not available in the readiness materials, max drawdown is computed deterministically client-side from a time-ordered cumulative P&L series. The repo includes a deterministic context-engineering formatter that converts aggregated stats to an LLM-ready textual summary. I logged design decisions (language, auth, indexes, driver pattern, drawdown computation) to the audit trail before acting. The app was seeded against the reachable cluster, indexes were created, and unit/integration tests passed.

## How to run

1) Copy .env.example to .env and set DOCUMENTDB_URI to your cluster connection string (do NOT commit secrets).
2) Install dependencies: pip install -r requirements.txt
3) Seed sample data (idempotent): python scripts/seed_data.py
4) Run tests (integration tests exercise the live cluster): pytest -q
5) Run the API server locally: uvicorn app.main:app --reload

Endpoints:
- POST /journal/signal (Signal JSON)
- POST /journal/execution (Execution JSON)
- POST /journal/outcome (Outcome JSON)
- GET /stats/{strategy_id}?start=&end= (returns structured stats and formatted summary)

Notes: The app reads the connection string at runtime from DOCUMENTDB_URI and uses database sample_fintech_13 and collection journal.

## Verified by running

- pip install -r requirements.txt: completed successfully
- Created package files and source files in repo: verified by file listing
- python scripts/seed_data.py: ran successfully; inserted sample documents into sample_fintech_13.journal (seed reported 'Seed complete')
- documentdb_list_databases db_name=sample_fintech_13: returned database and collection list (journal present, count=60)
- documentdb_list_indexes db_name=sample_fintech_13, collection_name=journal: returned indexes including idx_strategy_time (compound index on {strategy_id:1, timestamp:-1})
- documentdb_find_documents db_name=sample_fintech_13, collection_name=journal limit=5: returned sample documents showing signal/execution/outcome records
- pytest -q: 1 passed (tests/test_aggregations.py) — validated trade-count, total/avg P&L, win rate, cumulative series and client-side max drawdown calculation

## Not verified

- Did not run the FastAPI server (uvicorn) in this run because long-running servers are disallowed by the command-runner policy; the server code is included and can be started locally with uvicorn
- Did not attempt a server-side-only max-drawdown aggregation pipeline on the server (readiness report noted no canonical, fully-tested pattern was available); I computed drawdown client-side as a deterministic fallback
- No LLM provider or model was invoked — the context-engineering layer is a deterministic formatter only (the prompt did not request live model calls)

## Open issues

- Server-side max-drawdown: readiness report documented an information gap (no canonical server-side pipeline). If you require a purely server-side drawdown computation for very large series, provide a canonical pipeline or request an advanced pipeline design/review; current sample computes drawdown client-side after retrieving ordered outcomes.
- mongosh is not on PATH in the run environment (readiness report). Installing mongosh locally would make ad-hoc manual inspection easier; the sample used the documentdb MCP server for verification instead.

## Files

- `README.md`
- `.env.example`
- `requirements.txt`
- `.gitignore`
- `app/__init__.py`
- `app/db.py`
- `app/journal.py`
- `app/aggregations.py`
- `app/formatter.py`
- `app/main.py`
- `scripts/__init__.py`
- `scripts/seed_data.py`
- `tests/test_aggregations.py`

