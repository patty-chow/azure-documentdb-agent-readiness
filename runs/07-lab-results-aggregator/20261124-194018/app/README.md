Lab Results Aggregator (Azure DocumentDB + Beanie sample)

This sample demonstrates:
- Async Python service using FastAPI and Beanie (Motor) that stores time-series lab results in Azure DocumentDB.
- Aggregation pipelines using $setWindowFields to compute moving averages partitioned by patient and test code.
- A change-stream consumer that triggers real-time alerts for critical values.

Prerequisites
- Python 3.8+ (the run environment provides Python). Use a virtualenv.
- A reachable Azure DocumentDB cluster. Set DOCUMENTDB_URI in your environment or in a .env file (see .env.example).
- The sample uses the database: sample_healthcare_07

Quickstart
1. python -m venv .venv && source .venv/bin/activate
2. pip install -r requirements.txt
3. Copy .env.example to .env and set DOCUMENTDB_URI
4. Run the setup script to create indexes and seed demo data:
   python scripts/seed_data.py
5. Run the demo change-stream (it seeds a critical value and listens briefly for alerts):
   python scripts/demo_change_stream.py
6. Optionally run the API (not required for demo):
   uvicorn src.main:app --reload

Files
- src/: application code
- scripts/seed_data.py: seed demo data and creates index
- scripts/demo_change_stream.py: runs a short-lived change-stream demo that writes a critical value to trigger an alert
- .env.example: example env vars

Note
- Do NOT store secrets or connection strings in source control. The app reads DOCUMENTDB_URI at runtime.
