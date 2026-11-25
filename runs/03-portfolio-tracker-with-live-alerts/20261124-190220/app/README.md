# DocumentDB Portfolio Tracker (sample)

This sample demonstrates using Azure DocumentDB (MongoDB-compatible) with Node.js and Mongoose to:

- Store positions and alert rules
- Open a change stream on the positions collection and evaluate alert rules when prices update
- Fire a webhook (HTTP POST) when an alert threshold is breached
- Expose an aggregation endpoint that computes portfolio P&L and sector allocation

Prerequisites
- Node.js 24+ and npm
- A reachable Azure DocumentDB cluster. Set the connection string in the environment variable DOCUMENTDB_URI (do NOT store secrets in files).
- The sample uses the database name `sample_fintech_03`.

Quickstart
1. Install dependencies
   npm install

2. Seed example data
   npm run seed

3. Run the aggregation test (one-shot)
   npm run aggregate:test

4. Start the service (not required for tests)
   npm start

API
- GET /portfolio/:userId/summary
  Returns: { totalPnl, sectors: [{ sector, marketValue, percentage }] }

Design notes and choices
- Language & framework: Node.js + Express + Mongoose (Mongoose 7.x). Environment provides Node 24.
- Connection: Read DOCUMENTDB_URI from environment. TLS is required by DocumentDB.
- Indexes: defined on schemas: userId, symbol, compound {userId, symbol}, sector to support aggregation/filtering.
- Change stream: uses fullDocument: 'updateLookup' to evaluate rules on updates.
- Webhook delivery: the sample performs a single POST attempt and logs failures; production systems should implement durable retries or a queue.

Files of interest
- src/db.js — Mongoose connection (singleton)
- src/models/position.js — Position schema and indexes
- src/models/alertrule.js — AlertRule schema
- src/app.js — Express app and portfolio aggregation route
- src/alert_watcher.js — Change-stream listener (background)
- scripts/seed.js — Idempotent seed script
- scripts/aggregate_test.js — One-shot aggregation runner
- scripts/watch_test.js — Short-lived watcher runner for manual testing

Security & cleanup
- Do not commit DOCUMENTDB_URI into source control. Use environment variables or secret manager.
- To clean up sample data, connect to the cluster and drop the database `sample_fintech_03`.

Notes
- This sample avoids creating Azure resources; it uses an existing cluster referenced by DOCUMENTDB_URI.
- See README sections and inline comments for more production considerations (networking, private endpoints, CMK).
