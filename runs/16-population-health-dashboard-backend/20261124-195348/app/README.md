Population Health Dashboard Backend (Azure DocumentDB sample)

This sample implements a Python FastAPI service that computes faceted aggregations over a synthetic `patients` collection and stores materialized summaries in an `aggregations_cache` collection in an Azure DocumentDB (MongoDB-compatible) cluster.

What it shows
- Building aggregation pipelines with $facet to produce diagnosis, age-band, gender and region breakdowns.
- Materializing expensive aggregations into a cache collection with TTL and refreshing them on a schedule (in-process scheduler).
- Best-practice MongoDB client usage: singleton MongoClient reading DOCUMENTDB_URI from the environment.

Prerequisites
- Python 3.11 (or compatible 3.x)
- A reachable Azure DocumentDB cluster and a SRV-style connection string in DOCUMENTDB_URI environment variable

Setup
1. Create a virtual environment and install dependencies:
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2. Copy .env.example to .env and set DOCUMENTDB_URI:
   cp .env.example .env
   # edit .env and set DOCUMENTDB_URI to your cluster's connection string

3. Seed sample data into sample_healthcare_16.patients:
   python seed.py --count 5000

4. Run the FastAPI app:
   uvicorn main:app --reload

API endpoints
- GET /facets?use_cache=true — compute (or return cached) facets for provided filters
- GET /summaries/{name} — fetch a cached summary document
- POST /summaries/refresh — trigger a manual refresh of the default summary

Testing
- Unit tests that don't require a live cluster:
  pytest -q

Cleaning up
- Remove seed data and summaries from the sample database if desired (use your mongoclient or the documentdb MCP server tools). This sample does not include a destructive cleanup script.

Notes
- Do not check real secrets into source control; DOCUMENTDB_URI is read from the environment. See .env.example for the placeholder.
