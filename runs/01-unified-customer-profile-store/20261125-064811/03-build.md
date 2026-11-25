# 3. Build report: 01-unified-customer-profile-store

**Status: completed**

Built a small Node.js (Express) + Mongoose sample that ingests customer events and upserts them into a canonical customer profile document in Azure DocumentDB (MongoDB-compatible). The sample reads the cluster connection string from DOCUMENTDB_URI, uses the database sample_customer_360_01, creates/ensures indexes idempotently (skips unsafe changes), seeds example events, and provides an HTTP POST /events endpoint to upsert events.

## How to run

1) Copy .env.example to .env and set DOCUMENTDB_URI to your Azure DocumentDB connection string (do NOT commit real credentials).
2) npm install
3) npm run seed   # reads sample-data/events.json and upserts to the database sample_customer_360_01 (creates indexes if safe)
4) npm run verify # prints the customer documents currently in the sample DB
5) npm start      # starts the HTTP API server on PORT (default 3000)
6) Example event POST: curl -X POST http://localhost:3000/events -H "Content-Type: application/json" -d '{"source":"crm","customerId":"cust-123","attributes":{"email":"x@example.com"}}'

Notes: The app reads the cluster URI from process.env.DOCUMENTDB_URI at runtime and uses the database sample_customer_360_01 (via mongoose.connection.useDb). Do not store secrets in the repo.

## Verified by running

- npm install: completed (exit code 0)
- npm run seed: completed (exit code 0). Seed script output: Upserting events from sample-data/events.json; handled an existing index conflict non-destructively when present.
- npm run verify: completed (exit code 0). Verification printed the inserted customer documents (sample output included two customers: cust-001 and cust-002).
- Started server locally (via npm start) was not long-running tested here, but the endpoint implementation exists and can be exercised with curl as described in README.

## Not verified

- Vector index creation (DiskANN/HNSW/IVF) — the sample did not create or test vector indexes. The readiness report requested an explicit tested example if vectors were to be mentioned; I did not add or test vector index creation against the cluster because the sample focuses on canonical profile upserts.
- Data-plane authentication variants (e.g., Microsoft Entra / AAD token auth) — the sample reads DOCUMENTDB_URI and uses it; I did not test alternative authentication modes because the authoritative support / usage was not available in the provided materials.
- Altering or dropping existing indexes on the live cluster — the seed script intentionally avoids destructive index changes. I did not drop or change any existing indexes on the cluster. The seed will skip creating a unique index if a conflicting index already exists (to avoid destructive changes).

## Open issues

None.

## Files

- `package.json`
- `.env.example`
- `README.md`
- `src/db.js`
- `src/index.js`
- `src/models/customer.js`
- `src/routes/events.js`
- `src/lib/upsert.js`
- `scripts/seed.js`
- `scripts/verify.js`
- `sample-data/events.json`

