Consent Preference Center - DocumentDB (Azure DocumentDB) sample

This sample implements a small FastAPI service using Beanie ODM to store customer consent records in an Azure DocumentDB (MongoDB-compatible) cluster.

What it shows
- Beanie Document model with append-only consent history
- TTL retention via a retention_date field and a TTL index (expireAfterSeconds=0)
- Endpoints to record consent, withdraw consent, and retrieve current preference state

Prerequisites
- Python 3.9+ (a venv is recommended)
- A reachable Azure DocumentDB connection string in the environment variable DOCUMENTDB_URI
- The target database name used by the sample: sample_customer_360_11

Important: Do NOT commit your connection string. Use .env (copy .env.example)

Setup
1. Copy .env.example to .env and fill DOCUMENTDB_URI with your connection string.
2. Install dependencies:
   pip install -r requirements.txt
3. Seed sample data (creates 3 example consent documents and creates the indexes):
   python scripts/seed.py
4. Run the FastAPI app (dev):
   uvicorn app.main:app --reload

API
- POST /consent
  Body: {"customer_id": "cust_1", "preferences": {"email": true}, "actor": "system"}
  Creates or updates the customer's consent, appends history, increments consentVersion

- POST /consent/withdraw
  Body: {"customer_id": "cust_1", "channels": ["email"], "actor": "user"}
  Marks channels as withdrawn (false) and appends history

- GET /consent/{customer_id}
  Returns current_preferences, consentVersion and history entries

Indexes and retention
- A TTL index is created on the retention_date field with expireAfterSeconds=0. The code sets retention_date to now + TTL_DAYS (default 365 days). Documents are removed by the server when retention_date is reached.

Notes and limitations
- The app reads DOCUMENTDB_URI from environment at runtime and does not log it.
- This sample purposely keeps the database name fixed to sample_customer_360_11 to avoid accidental writes to other databases.

Cleaning up
- Remove seeded documents manually or wait for TTL removal. To remove immediately, connect with a client and drop the 'consents' collection in sample_customer_360_11.
