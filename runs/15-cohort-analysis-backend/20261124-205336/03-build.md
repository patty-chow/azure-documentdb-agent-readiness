# 3. Build report: 15-cohort-analysis-backend

**Status: completed**

Built a small Python FastAPI sample that performs cohort analysis against an existing Azure DocumentDB (MongoDB-compatible) cluster. The sample includes an idempotent seed script to create `customers` and `events`, an aggregation that groups customers by acquisition month using $bucket and computes 30/60/90-day retention with channel/product breakdowns, materialises snapshots in `cohort_snapshots`, and exposes simple HTTP endpoints plus a weekly scheduler. I verified dependency installation, seeding, snapshot generation, index creation, and unit tests. The app reads the cluster connection string from DOCUMENTDB_URI and uses a singleton MongoClient (driver best-practice).

## How to run

1) Copy .env.example -> .env and set DOCUMENTDB_URI to your cluster connection string (do NOT commit secrets). 2) Create and activate a venv, then install deps: python -m venv .venv; source .venv/bin/activate; pip install -r requirements.txt. 3) Seed data: python scripts/seed.py. 4) Generate a cohort snapshot once: python -c "import sys; sys.path.append('.') ; from app.db import get_db; from app.cohort import generate_cohort_snapshot; db=get_db(); print(generate_cohort_snapshot(db))" OR run the helper: python scripts/generate_snapshot.py (if you prefer, set PYTHONPATH='.' before running). 5) Run the API for manual inspection: uvicorn app.main:app --reload --port 8000 (the app schedules a weekly refresh using APScheduler and exposes endpoints GET /cohorts, GET /cohorts/{snapshot_month}, POST /admin/refresh).

## Verified by running

- pip install -r requirements.txt: exit code 0, dependencies installed (pymongo 4.5.0, fastapi 0.95.2, uvicorn 0.23.2, apscheduler 3.10.1, python-dotenv 1.0.0).
- scripts/seed.py: ran successfully; inserted customers=800, events=1177 into database sample_customer_360_15.
- Snapshot generation via generate_cohort_snapshot (python one-liner): exit code 0, inserted snapshot document (reported 'Generated snapshot: 2026-11-25 buckets: 13').
- documentdb_list_databases (MCP): confirmed collections in sample_customer_360_15: customers (800), events (1177), cohort_snapshots (1).
- documentdb_list_indexes (MCP): confirmed indexes created on customers and events (customer_id unique, acquired_at, channel, primary_product_id; events indexes on customer_id, event_date, product_id).
- Unit tests: ran pytest via a py -c wrapper that adds '.' to sys.path; 2 passed.

## Not verified

- Live weekly scheduler execution: the APScheduler job is scheduled inside app.main to run every 7 days, but I did not run a long-lived uvicorn server in this run to observe an actual weekly execution (the command runner does not allow long-running foreground processes).
- MONGODB-OIDC (Microsoft Entra/OIDC) authentication flow: I did not implement nor verify OIDC because the environment provides DOCUMENTDB_URI and SCRAM/SCRAM-SHA-256 is used; full OIDC flow would require extra configuration and interactive token flow which is out of scope for this sample run.
- Detailed aggregation explain() via the documentdb_explain_operation MCP tool: the main aggregation was executed and its result verified by snapshot insertion (via pymongo), but I did not separately call documentdb_explain_operation to collect executionStats for the pipeline. (The MCP server is available; this can be added to the sample verification if desired.)

## Open issues

- Module import during one-shot scripts: running scripts that import the local package required adding '.' to sys.path (I used a python -c wrapper to do this when needed). When running scripts directly (python scripts/generate_snapshot.py) some environments may need PYTHONPATH=. or running from the repository root. I documented this in README and used workarounds in verification.
- mongosh is not present on the run host (readiness_report noted mongosh missing). For interactive ad-hoc debugging developers may want to install mongosh or use the MCP documentdb tools (which I used for index listing).

## Files

- `requirements.txt`
- `.env.example`
- `README.md`
- `app/__init__.py`
- `app/db.py`
- `app/cohort.py`
- `app/main.py`
- `scripts/seed.py`
- `scripts/generate_snapshot.py`
- `tests/test_cohort.py`

