# 3. Build report: 03-portfolio-tracker-with-live-alerts

**Status: completed**

Built a small Node.js + Mongoose sample app that demonstrates storing positions and alert rules in Azure DocumentDB, running a change-stream watcher to evaluate alert rules and send webhooks, and exposing an aggregation endpoint that computes portfolio P&L and sector allocation. The sample includes an idempotent seed script, index creation, a one-shot aggregation test, a short-lived change-stream watcher test, and unit tests for the aggregation helper. All runnable operations in this environment were executed and verified against the live cluster referenced by DOCUMENTDB_URI.

## How to run

1) Install dependencies: npm install
2) Configure env: copy .env.example to .env and set DOCUMENTDB_URI to your cluster connection string (SRV style). Do NOT commit secrets.
3) Seed sample data (idempotent): npm run seed
4) Ensure indexes (script provided): node scripts/create_indexes.js
5) Run one-shot aggregation to verify results: npm run aggregate:test  (or: node scripts/aggregate_test.js <userId>)
6) Run short-lived change-stream watcher test (runs 10s): npm run watch:test  (or: node scripts/watch_test.js)
7) Start the full service (long-running): npm start — the server hosts GET /portfolio/:userId/summary and starts the alert watcher (not required for tests).
8) Run unit tests: npm test

Notes:
- The app reads the cluster connection string from process.env.DOCUMENTDB_URI. The sample forces use of the database sample_fintech_03.
- Webhook URLs in seed data are placeholders; for real testing replace them with a reachable endpoint.

## Verified by running

- npm install: completed (dependencies installed)
- jest unit tests: 1 passed (tests/aggregation.test.js)
- seed script: node scripts/seed.js — completed (inserted/upserted sample positions and alert rules)
- database inspection (documentdb_list_databases via MCP): sample_fintech_03 exists and contained collections positions (count:4) and alertrules (count:2)
- sample documents fetched (documentdb_find_documents on positions): returned 4 documents (sample data present)
- explicit index creation script: node scripts/create_indexes.js — completed (created intended indexes)
- index verification (documentdb_list_indexes via MCP): positions and alertrules indexes present (userId, symbol, sector, compound userId+symbol, userId+active, etc.)
- one-shot aggregation: node scripts/aggregate_test.js — returned portfolio summary JSON for user1 (totalPnl and sector allocations)
- short-lived change-stream watch test: node scripts/watch_test.js — change stream opened, watcher ran for 10s and stopped without runtime errors

## Not verified

- Webhook delivery end-to-end verification: The sample sends a single POST attempt to the webhook URL when an alert triggers. Delivery to external webhook endpoints was not validated (no local webhook receiver was configured and sample seed uses placeholder webhook.site URLs).
- Production sharding/resharding behavior and multi-shard change-stream behavior: Not exercised in this sample environment. The code opens change streams with fullDocument: 'updateLookup' as documented; for production multi-shard clusters verify cluster settings and compatibility before relying on global change streams.
- Large-scale performance and connection-pool tuning under load: The sample uses conservative pool settings informed by the documentdb-connection skill, but no load testing was performed in this run.
- Provisioning of Azure DocumentDB resources (Bicep/Terraform/az): Not attempted because the run policy disallows creating Azure resources. IaC was not added to the repo (by design) — sample uses an existing cluster provided via DOCUMENTDB_URI.

## Open issues

None.

## Files

- `package.json`
- `README.md`
- `.env.example`
- `src/db.js`
- `src/models/position.js`
- `src/models/alertrule.js`
- `src/aggregation.js`
- `src/app.js`
- `src/server.js`
- `src/alert_watcher.js`
- `scripts/seed.js`
- `scripts/aggregate_test.js`
- `scripts/watch_test.js`
- `scripts/create_indexes.js`
- `tests/aggregation.test.js`

