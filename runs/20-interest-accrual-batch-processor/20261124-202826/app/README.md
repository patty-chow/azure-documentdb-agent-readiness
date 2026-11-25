# DocumentDB Interest Accrual Batch Processor (sample)

This sample demonstrates a daily batch processor that:
- Iterates all active, interest-bearing accounts from Azure DocumentDB (Mongo-compatible)
- Computes a daily accrued interest amount using a simple formula
- Writes an immutable journal document per account using unordered bulk writes for throughput

Prerequisites
- Node.js 24+, npm
- A reachable Azure DocumentDB cluster. Set the connection string in DOCUMENTDB_URI (see .env.example). The sample uses the database `sample_banking_20`.

Quickstart
1. Copy .env.example -> .env and set DOCUMENTDB_URI
2. npm install
3. npm run seed       # creates ~100 sample accounts (idempotent upsert)
4. npm run start:once # run the accrual job once for testing

What the sample shows
- Use of a singleton Mongoose connection (src/db.js)
- Cursor-based pagination (Mongoose cursor) and batching
- Unordered bulk writes (Journal.collection.bulkWrite(..., {ordered:false}))
- Partial index on accounts for fast selection of active interest-bearing accounts
- Unique compound index on journal (accountId + runDate) to avoid duplicate accruals for the same day

Configuration
- DOCUMENTDB_URI: connection string (required)
- DB_NAME: optional, default sample_banking_20
- BATCH_SIZE: optional, default 500
- CRON_SCHEDULE: optional, default "0 0 * * *" (midnight UTC)

Notes and limitations
- This sample uses a simple daily accrual formula: amount = balance * (APR/100) / 365. It is for demonstration only and not financial advice.
- The journal insert is attempted via unordered bulk writes; partial failures may still leave some inserts (intended for throughput).
- No cloud infrastructure provisioning is performed by this repo. The sample connects to the cluster referenced by DOCUMENTDB_URI.

Cleaning up
- To remove sample documents, connect to the database and drop the `accounts` and `accrual_journal` collections.

License: MIT
