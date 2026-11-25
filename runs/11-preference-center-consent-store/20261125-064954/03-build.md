# 3. Build report: 11-preference-center-consent-store

**Status: completed**

Built a small FastAPI service (app/main.py) that models customer consent with append-only history and TTL retention. The repo includes a seed script that inserted sample documents into the live Azure DocumentDB cluster (database sample_customer_360_11) and created the TTL and customer_id indexes. Dependencies were installed, the seed and index-inspection scripts were executed against the cluster, and a placeholder test was run.

## How to run

1) Copy .env.example to .env and fill in DOCUMENTDB_URI with your cluster connection string (do NOT check it into source control).
2) Install dependencies:
   pip install -r requirements.txt
3) Seed example data and create indexes:
   python scripts/seed.py
   (This will insert 3 sample consent documents into the database sample_customer_360_11 and create the TTL and customer_id indexes.)
4) Inspect indexes (optional):
   python scripts/inspect_indexes.py
5) Start the app (dev):
   uvicorn app.main:app --reload
   (The app reads DOCUMENTDB_URI from the environment at runtime. Endpoints: POST /consent, POST /consent/withdraw, GET /consent/{customer_id}.)

## Verified by running

- pip install -r requirements.txt: succeeded
- python scripts/seed.py: succeeded (Inserted cust_001, cust_002, cust_003 and created indexes)
- python scripts/inspect_indexes.py: succeeded (listed indexes: _id_, ttl_retention_date, ix_customer_id_unique)
- pytest: 1 passed (placeholder test)

## Not verified

- Starting the app with uvicorn and exercising endpoints against the running server was not executed (I did not start a long-running process in the run environment).
- End-to-end Beanie initialization in the FastAPI startup in this execution context was not exercised by an integration test; the seed/inspect scripts used motor directly to avoid beanie init compatibility differences encountered while running in this environment.

## Open issues

- Beanie initialization in the FastAPI startup can be sensitive to Beanie/Motor versions and startup ordering in some environments. During development I observed an init-time incompatibility when attempting to call beanie.init_beanie from a script context; to make seeding robust the seed/inspect scripts use motor directly. The app main still calls init_beanie on startup; when you run with uvicorn in your environment, the startup will initialize Beanie (reads DOCUMENTDB_URI).
- This sample intentionally reads DOCUMENTDB_URI from the environment and does not log it. Ensure DOCUMENTDB_URI is set before running the app or scripts.
- The sample does not provision cloud resources; it targets the pre-provisioned cluster described in the run environment and uses database sample_customer_360_11 as required.

## Files

- `requirements.txt`
- `.env.example`
- `README.md`
- `app/__init__.py`
- `app/main.py`
- `scripts/seed.py`
- `scripts/inspect_indexes.py`
- `tests/test_basic.py`

