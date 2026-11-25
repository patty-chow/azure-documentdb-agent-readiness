Azure DocumentDB — Settlement Tracker sample

This sample demonstrates:
- Modeling trades as state-machine documents in Azure DocumentDB (MongoDB wire protocol)
- Advancing trade state atomically using MongoDB transactions
- Logging each state transition in the same transaction
- Using a change stream to detect FAILED settlements and trigger an exception handler
- Exposing an aggregation endpoint to report settlement rates by asset class and counterparty

Prerequisites
- Node.js 24+ and npm
- Access to a vCore Azure DocumentDB cluster (MongoDB wire protocol) with connection string in DOCUMENTDB_URI
- The sample uses database: sample_banking_09

Quickstart
1. Copy .env.example to .env and set DOCUMENTDB_URI
2. npm install
3. npm run seed
4. npm start

API
- POST /trades/:id/advance  { toState, by, note }  — advance a trade's state in a transaction
- GET /settlement-rates  — aggregation grouped by assetClass and counterparty
- GET /seed  — optional: run seeding via HTTP

Security & secrets
- Do NOT commit real credentials. Read connection string from DOCUMENTDB_URI at runtime.

Cleanup
- Remove sample data from the 'sample_banking_09' database via your preferred tools.

Notes
- This sample is for learning and development. For production follow the documentdb-security guidance (private endpoints, Entra auth, CMK).
