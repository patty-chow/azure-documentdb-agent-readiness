DocumentDB Billing Engine Sample

What this sample shows
- A minimal billing engine using Node.js + Mongoose against Azure DocumentDB
- Multi-document transactions: atomically recording a charge event and updating a subscription
- Idempotency via a unique index on idempotencyKey to prevent double-billing
- TTL index on entitlement.expiresAt to auto-expire trial entitlements

Prerequisites
- Node.js 24+ and npm
- An Azure DocumentDB cluster reachable from this machine. Set DOCUMENTDB_URI in your environment (see .env.example).
- The cluster must allow connections from this workstation.

Quickstart
1. npm install
2. Copy .env.example to .env and set DOCUMENTDB_URI
3. npm run create-indexes
4. npm run seed
5. npm run test-charge  # runs a one-shot charge to demonstrate transactional behavior
6. npm start           # starts HTTP API on port 3000 (endpoints: GET /plans, GET /customers, POST /charge)

API
- GET /plans
- GET /customers
- POST /charge { customerId, subscriptionId, amountCents, idempotencyKey }
  Returns existing charge when idempotencyKey already processed.

Cleanup
- Remove sample documents from the database `sample_fintech_16` using your preferred DB tooling.

Security
- The sample reads DOCUMENTDB_URI at runtime from environment variables. Do not check secrets into source control.

Notes
- This sample does not provision Azure resources. It expects an existing cluster as described above.
