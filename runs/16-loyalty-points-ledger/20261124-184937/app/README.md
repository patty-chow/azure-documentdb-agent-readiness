DocumentDB Loyalty Points Ledger Sample

This sample demonstrates a simple loyalty points ledger using Azure DocumentDB (vCore, MongoDB wire protocol) with Mongoose and Node.js.

What it demonstrates
- Immutable events collection: every earn/redeem is recorded as an event
- Running balances stored in a separate balances collection
- Multi-document transactions to atomically append an event and update the balance
- Two read endpoints: GET /balance?accountId=<id> and GET /history?accountId=<id>
- Idempotent seed script to create sample accounts and events and create required indexes

Prerequisites
- Node.js 24+ and npm
- A reachable Azure DocumentDB cluster (vCore). The connection string must be provided in the environment variable DOCUMENTDB_URI. Do not check this secret into source control.
- The sample uses the database named: sample_retail_16

Setup
1. Copy .env.example to .env and fill in DOCUMENTDB_URI (mongodb+srv://...)
2. npm install
3. npm run seed

Run (read-only sample server)
- npm start
- Example: curl "http://localhost:3000/balance?accountId=acct-1"
- Example: curl "http://localhost:3000/history?accountId=acct-1"

Scripts
- npm run seed  - idempotent seed that creates sample accounts/events using transactions
- npm run check - runs a quick local check (one-shot) that prints a balance and history for acct-1

Notes
- The sample reads DOCUMENTDB_URI from process.env at runtime. See .env.example
- This sample uses SCRAM credentials via the connection string. A production deployment should consider Microsoft Entra ID (OIDC) per Azure guidance; that is not demonstrated here.

Cleaning up
- Remove sample documents manually from the database (the sample does not create Azure resources). See mongosh/portal or use a small script to drop the collections.

License: MIT
