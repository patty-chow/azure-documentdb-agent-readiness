# Azure DocumentDB Swift Message Ingest (sample 02)

This sample shows an async Python service using Beanie ODM and Motor to ingest SWIFT MT103 and MT202 messages into an Azure DocumentDB (MongoDB-compatible) cluster, validate required fields, bulk-insert batches for throughput, and expose an aggregation endpoint that summarizes daily message volume and total value by message type.

IMPORTANT: The cluster connection string must be provided at runtime through the environment variable `DOCUMENTDB_URI`. Do NOT store secrets in repository files.

Prerequisites
- Python 3.11+ (this environment has Python 3.13)
- An Azure DocumentDB cluster reachable from this machine. The connection string must be set in env var `DOCUMENTDB_URI` (mongodb+srv://... or mongodb://... with TLS).

How the sample is laid out
- src/
  - app.py: FastAPI app with /ingest and /aggregations/daily-summary
  - models.py: Beanie Document model and Pydantic parsing helpers
  - db.py: connection (Motor) and Beanie initialization
- seed.py: idempotent script to load sample MT messages and parsed documents
- create_indexes.py: idempotent index creation script
- requirements.txt: project dependencies (loose pinned ranges)
- .env.example: example environment file

Quickstart
1. Create a virtualenv and install deps:
   python -m venv .venv
   source .venv/bin/activate  # or .\venv\Scripts\activate on Windows
   pip install -r requirements.txt

2. Provide the connection string:
   cp .env.example .env
   # edit .env and set DOCUMENTDB_URI to your cluster's connection string

3. Seed sample data and create indexes:
   python create_indexes.py
   python seed.py

4. Run the FastAPI app:
   uvicorn src.app:app --reload

5. Example ingest (POST /ingest):
   curl -X POST localhost:8000/ingest -H 'Content-Type: application/json' -d '["MT103|:20:ABC123|:32A:240101USD1234.56|:50K:/12345\nJOHN DOE","MT202|:20:DEF456|:32A:240101USD2000.00|:50K:/67890\nACME CORP"]'

6. Aggregation:
   curl localhost:8000/aggregations/daily-summary

Notes and assumptions
- The SWIFT parser here is intentionally small and demonstrates tag extraction for a handful of common tags (:20:, :32A:, :50K:, :59:). This is NOT a full SWIFT MT parser.
- The sample uses a single collection `swift_messages` in the database `sample_banking_02`.
- Connection string is read from DOCUMENTDB_URI. The sample will not provision or change cloud resources.

Cleanup
- The sample does not create any Azure resources. To remove the sample data, you can drop the collection from your cluster (using your preferred MongoDB tool) or use the DocumentDB MCP server tools.

License: MIT
