DocumentDB Options Chain Ingest Sample

This sample shows how to ingest option-chain snapshots into an Azure DocumentDB (MongoDB-compatible) cluster using pymongo bulk_write(ordered=False), create a compound index, and expose a simple HTTP API to retrieve full chains by underlying and expiry.

Prerequisites
- Python 3.10+
- An Azure DocumentDB cluster reachable from this machine. Set DOCUMENTDB_URI in your environment or in a local .env file (see .env.example). The sample uses database `sample_fintech_19` by default.

Setup
1. Create a virtualenv and install dependencies:

   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2. Configure the connection string:
   - Copy .env.example -> .env and set DOCUMENTDB_URI to your cluster connection string.

3. Seed sample data:
   python scripts/seed.py

Run the API (development):
   uvicorn app.main:app --reload

Endpoints
- POST /ingest
  Body: {"underlying":"FOO","expiry":"2026-12-17","options":[{...}]}
  Writes documents via bulk_write(ordered=False) with UpdateOne upserts.

- GET /chains?underlying=FOO&expiry=2026-12-17
  Returns the list of option documents sorted by strike ascending.

Notes
- The connection string must be provided at runtime via DOCUMENTDB_URI. Do not commit secrets to the repo.
- The app ensures a compound index on {underlying:1, expiry:1, strike:1} at startup and in the seed script.

Cleaning up
- This sample only writes data to the sample_fintech_19 database. Use your cluster tools or the DocumentDB MCP server to remove the `options` collection when done.
