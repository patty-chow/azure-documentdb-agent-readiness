Consent Preference Center sample

This sample demonstrates a small FastAPI service using Beanie (Motor) to store customer consent records in Azure DocumentDB (MongoDB-compatible). It shows how to:

- Record consent (append-only history) and withdraw consent
- Maintain an append-only history array for audit with consentVersion
- Enforce data retention using a TTL index on retention_expires_at

Prerequisites

- Python 3.11+ / 3.13 available
- A reachable Azure DocumentDB cluster; set DOCUMENTDB_URI in .env
- The database name used: sample_customer_360_11 (the app uses this DB)

Setup

1. pip install -r requirements.txt
2. cp .env.example .env and update DOCUMENTDB_URI
3. Run the seed script to create sample documents and indexes:
   python scripts/seed.py

Run

Start the app (development):

  uvicorn app.main:app --reload

API

- POST /consents/record
  body: { customerId: str, channels: { email: bool, sms: bool, ... }, actor?: str, reason?: str }
- POST /consents/withdraw
  body: { customerId: str, channels?: { email: bool, ... } (optional means withdraw all if omitted), actor?: str, reason?: str }
- GET /consents/{customerId}
  returns current preference state and latest consentVersion

Cleaning up

Delete the inserted documents from the database (use your preferred MongoDB client) or run a script to remove sample docs.

Notes

- The app reads DOCUMENTDB_URI from the environment; do not commit secrets.
- TTL retention period default is 365 days and configurable via CONSENT_RETENTION_DAYS env var.
