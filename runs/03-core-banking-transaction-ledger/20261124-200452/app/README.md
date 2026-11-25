# DocumentDB Core Banking Transaction Ledger (Sample)

This sample demonstrates using Azure DocumentDB (MongoDB-compatible) with Node.js and Mongoose to build a simple immutable transaction ledger. It shows how to:

- Record every debit/credit as an immutable Transaction document
- Use multi-document transactions (MongoDB sessions) to atomically append a transaction and update an Account balance snapshot
- Enforce idempotency with transactionRef and a unique index to prevent double-posting

Prerequisites
- Node.js 24+ (available in the run environment)
- A reachable Azure DocumentDB cluster connection string in the environment variable DOCUMENTDB_URI
  (Do NOT commit secrets; copy .env.example -> .env and set DOCUMENTDB_URI)

How to run
1. Install dependencies:
   npm install

2. Configure environment:
   cp .env.example .env
   # edit .env and set DOCUMENTDB_URI

3. Seed sample accounts (idempotent):
   npm run seed

4. Start the API server:
   npm start

API
- POST /transactions
  body: { accountId, amount, type: "debit"|"credit", transactionRef, metadata? }
  Behavior: atomically inserts the transaction and updates the account balance. Duplicate transactionRef are rejected and do not change balance.

- GET /accounts/:accountId
  Returns account snapshot and recent transactions.

Demo
Run `npm run demo` to exercise posting a transaction and attempting a duplicate post to show idempotency.

Verification
- The sample creates indexes on the transactions collection (unique transactionRef and compound {accountId, createdAt:-1}).
- Use the included `npm run check-indexes` script to print created indexes (requires DOCUMENTDB_URI and the documentdb MCP server for additional inspection).

Security
- This sample uses SCRAM credentials read from DOCUMENTDB_URI by default. For production, consider Microsoft Entra ID (RBAC) and private networking.

Cleanup
- The sample uses the database `sample_banking_03` by default. Drop the database or delete the collections manually if you created them against a shared cluster.

Notes
- Do NOT commit your connection string. Use environment variables.
