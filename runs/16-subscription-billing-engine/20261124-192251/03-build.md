# 3. Build report: 16-subscription-billing-engine

**Status: completed**

Created a small Node.js (Express) + Mongoose sample billing engine that demonstrates multi-document transactions for charging, idempotency via a unique index, and TTL-based entitlements. The sample connects to an existing Azure DocumentDB cluster via the DOCUMENTDB_URI environment variable, creates indexes, seeds sample data, and includes a one-shot test script that performed a charge and showed idempotency behaviour. Indexes (unique idempotency key, TTL index) were created and verified via the documentdb MCP server.

## How to run

1) Install deps: npm install
2) Copy .env.example -> .env and set DOCUMENTDB_URI to your cluster connection string (do NOT commit secrets).
3) Create indexes: npm run create-indexes
4) Seed sample data: npm run seed
5) Run the one-shot test that demonstrates a transactional charge and idempotency: npm run test-charge
6) (Optional) Start the HTTP API server: npm start  # exposes GET /plans, GET /customers, POST /charge

Notes: the sample uses database sample_fintech_16 by default (set DATABASE_NAME env var to change).

## Verified by running

- npm install: 0 exit code, dependencies installed
- node scripts/create_indexes.js: 0 exit code — created unique index on ChargeEvent.idempotencyKey, index on ChargeEvent.customerId, TTL index on Entitlement.expiresAt
- node scripts/seed.js: 0 exit code — upserted 3 plans, 3 customers, created a subscription and entitlement (logged customer and subscription ids)
- node scripts/test_charge.js: 0 exit code — executed a charge via the sample logic: first attempt returned status 'charged' and created a ChargeEvent; second attempt with same idempotencyKey returned 'already_processed' and returned the existing event
- documentdb_list_indexes (via documentdb MCP server) for collection 'chargeevents' in database 'sample_fintech_16': shows indexes _id_, uniq_idempotencyKey (unique: true), idx_charge_customerId
- documentdb_list_indexes (via documentdb MCP server) for collection 'entitlements' in database 'sample_fintech_16': shows _id_ and ttl_entitlement_expiresAt with expireAfterSeconds: 0

## Not verified

- TTL expiry semantics observed in practice: index was created, but automatic deletion of expired entitlement documents was not observed (requires waiting for the background TTL thread and passage of time). This is not verified because TTL removal is time-based and was not accelerated for the test run.
- HTTP API endpoints (GET /plans, GET /customers, POST /charge) were not tested through HTTP requests; the transactional charge logic was exercised via the scripts/test_charge.js one-shot script that uses the same Mongoose models and logic.

## Open issues

None.

## Files

- `package.json`
- `.env.example`
- `README.md`
- `src/db.js`
- `src/index.js`
- `src/models/plan.js`
- `src/models/customer.js`
- `src/models/subscription.js`
- `src/models/chargeEvent.js`
- `src/models/entitlement.js`
- `scripts/create_indexes.js`
- `scripts/seed.js`
- `scripts/test_charge.js`
- `.gitignore`

