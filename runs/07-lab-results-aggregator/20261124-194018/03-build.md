# 3. Build report: 07-lab-results-aggregator

**Status: completed**

Built an async Python sample (FastAPI + Beanie + Motor) that stores time-series lab results in an Azure DocumentDB cluster (database: sample_healthcare_07). The sample includes: a Beanie Document model, a compound index {patientId:1, testCode:1, timestamp:1}, aggregation pipeline using $setWindowFields to compute moving averages, an endpoint to flag out-of-range/critical values, a seed script that inserts demo data, and a short-lived change-stream demo script that inserts a critical value and confirms the cluster emits the change. I verified dependency installation, created/indexed the collection, seeded data (200 docs), ran the moving-average aggregation, ran a change-stream demo that observed the inserted critical document, and used the DocumentDB MCP tools to confirm index creation and explain the aggregation plan (index used).

## How to run

1) Create and activate a virtual environment (recommended). 2) Copy .env.example to .env and set DOCUMENTDB_URI to your cluster connection string (mongodb+srv ...). 3) pip install -r requirements.txt. 4) Seed demo data and create the index: python scripts/seed_data.py (the script uses the DOCUMENTDB_URI and the database sample_healthcare_07). 5) Run the short-lived change-stream demo that inserts a critical value and listens briefly for the change: python scripts/demo_change_stream.py. 6) Run the aggregation demo locally: python scripts/run_agg.py. 7) Optionally run the FastAPI service: uvicorn src.main:app --reload (the sample's /results endpoint accepts inserts; the background change-stream monitor is started on app startup).

## Verified by running

- pip install -r requirements.txt: succeeded (dependencies installed).
- python scripts/seed_data.py (via wrapper): succeeded — inserted 200 demo documents into sample_healthcare_07.lab_results.
- documentdb_list_databases (MCP): returned database sample_healthcare_07 with collection lab_results count=200.
- src.db.create_compound_index executed during startup/seed: created compound index {patientId:1, testCode:1, timestamp:1}.
- documentdb_list_indexes (MCP): listed indexes and confirmed 'patientId_1_testCode_1_timestamp_1' exists alongside default _id index.
- scripts/demo_change_stream.py: started a watcher and inserted a critical GLU value; change stream observed the inserted document (printed doc).
- scripts/run_agg.py: ran the $setWindowFields aggregation for patient_001/GLU and printed results (count and sample rows).
- documentdb_explain_operation (MCP) for the aggregation: returned an explain plan showing an IXSCAN using the compound index (patientId_1_testCode_1_timestamp_1) — index was used for the query and pipeline stages executed.

## Not verified

- Running the full FastAPI server (uvicorn src.main:app) with the background change-stream monitor and verifying the monitor emits alerts in that process — I validated change-stream behavior using the short-lived demo watcher but did not launch the full server process to observe the monitor's prints.
- Beanie/Motor/pymongo exact compatibility matrix against Azure DocumentDB wire protocol versions — readiness_report flagged this as an information gap. I pinned workable package versions, but exact compatibility with all supported cluster wire-protocol versions was not programmatically verified.
- Behavior with different DOCUMENTDB_URI variants (already containing tls/authMechanism/retryWrites parameters) — the sample app appends parameters when missing; duplicate-parameter warning can appear (observed warning about duplicate 'retryWrites'). I did not exhaustively test all URI permutations or alternate auth methods (Entra/RBAC) in this sample run.

## Open issues

- Beanie/Motor compatibility: the readiness_report listed a missing compatibility matrix. I pinned Beanie==1.22.6 and Motor==3.2.0; these worked in the run but contributors should validate the pinned versions against their target cluster wire-protocol versions if they run different DocumentDB server versions.
- Normalized URI helper appends tls/authMechanism/retryWrites if missing; if the provided URI already includes these options a 'Duplicate URI option' warning can appear (observed at runtime). Consider a more robust URI parser/merge to avoid duplicates.
- Reference ranges are hard-coded in the sample (REFERENCE_RANGES dict). For production or extended demos, move ranges to a separate collection or external service. README documents how to swap to DB-based ranges.
- The sample's background change-stream monitor is a simple console-based alert emitter for demonstration. For production-ready alerting, add durable retry/resume behavior, persistent alert sinks (webhook, message bus, or notifications), and resume-token persistence for reliable restart.

## Files

- `requirements.txt`
- `.env.example`
- `README.md`
- `src/models.py`
- `src/db.py`
- `src/main.py`
- `scripts/seed_data.py`
- `scripts/demo_change_stream.py`
- `scripts/run_agg.py`

