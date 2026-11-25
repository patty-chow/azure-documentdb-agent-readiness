Cohort Analysis FastAPI sample for Azure DocumentDB (MongoDB-compatible)

What this sample shows
- How to connect to an Azure DocumentDB (MongoDB wire) cluster using PyMongo
- How to seed a small synthetic `customers` and `events` dataset
- An aggregation pipeline that groups customers by acquisition month (using $bucket), computes 30/60/90-day retention, and provides channel/product breakdowns using $facet
- Materialised cohort snapshot documents stored in `cohort_snapshots`, refreshed weekly via a background scheduler and on-demand via an admin endpoint

Prerequisites
- Python 3.11+ and pip
- A reachable Azure DocumentDB cluster connection string in environment variable DOCUMENTDB_URI
- The sample database name: sample_customer_360_15 (the app will create collections inside it)

Quick start
1. Copy .env.example -> .env and fill DOCUMENTDB_URI
2. Create a venv and install deps:
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
3. Seed sample data and create indexes:
   python scripts/seed.py
4. Generate a cohort snapshot once (or start the app which runs weekly jobs):
   python scripts/generate_snapshot.py
5. Run the API (dev):
   uvicorn app.main:app --reload --port 8000

API endpoints
- GET /cohorts -> list available snapshots
- GET /cohorts/{snapshot_month} -> snapshot details for month (YYYY-MM)
- POST /admin/refresh -> trigger on-demand snapshot refresh (protected only by network in this sample)

Files
- app/: FastAPI application, DB client and cohort pipeline
- scripts/seed.py: idempotent seeding (delete+insert) of sample data and index creation
- scripts/generate_snapshot.py: run the cohort aggregation and persist a snapshot

Notes and security
- Do NOT commit real secrets. Use .env and environment variables for DOCUMENTDB_URI.
- This sample uses a simple scheduler for weekly refresh. In production, use a separate job runner, RBAC, and secure endpoints.

Cleaning up
- To remove sample documents, drop the collections `customers`, `events`, `cohort_snapshots` from the sample_customer_360_15 database.
