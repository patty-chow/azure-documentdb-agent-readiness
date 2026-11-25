# 3. Build report: 09-trade-settlement-tracker

**Status: partial**

I built a Node.js + Mongoose sample settlement-tracker app implemented as an Express service. The repository files (app code, model, seed script, change-stream watcher, README and .env.example) were created. I attempted to install dependencies and verify against the live DocumentDB cluster using the documentdb MCP server, but dependency installation failed (npm registry/version errors) and MCP insert calls failed; therefore I could not start the app or run the seed against the cluster from this environment. I did verify Node is available and I could query the cluster for databases (the target database existed but had no collections). The sample is ready for a developer to install dependencies locally (or in CI with network access), set DOCUMENTDB_URI, run the seed, and start the server to exercise transactions and the change-stream watcher.

## How to run

1) Copy .env.example to .env and set DOCUMENTDB_URI to your cluster connection string (mongodb+srv form) for the vCore DocumentDB cluster; do NOT commit secrets.
2) npm install
3) npm run seed  (or GET /seed if you prefer HTTP-based seed)
4) npm start  (starts the Express server on port 3000)

API endpoints (after starting server):
- POST /trades/:id/advance  payload: { "toState": "SETTLED", "by": "user", "note": "optional" }
- GET /settlement-rates  returns aggregation grouped by assetClass and counterparty
- GET /seed  invokes the seed script in-process (convenience for development)

Notes:
- The code reads DOCUMENTDB_URI from environment at runtime. See .env.example for placeholder.
- The app uses a singleton Mongoose connection and OLTP-style pool tuning (maxPoolSize=50, minPoolSize=10) as described in the sample comments.
- The change-stream watcher is started by the app; in this sample it logs detected FAILED settlements and runs a minimal exception workflow. For production add resume-token persistence and error backoff per the guidance.

## Verified by running

- node --version: v24.21.0 (verified by running `node --version`)
- documentdb_list_databases (MCP): returned database sample_banking_09 with no collections (verified via documentdb MCP server with connection_profile 'default')
- files created and written to workspace (package.json, README.md, .env.example, src/ and scripts/ files) - verified by write operations

## Not verified

- npm install and dependency resolution — attempt failed with 'No matching version found for mongoose@^7.14.0' and subsequent retries with other pinned 7.x versions failed. Reason: npm registry/version resolution errors in this environment (see npm stderr).
- Running the seed script (npm run seed or node scripts/seed.js) against the live cluster — could not run because dependencies were not installed locally.
- Starting the Express server (npm start) and exercising endpoints (/trades/:id/advance, /settlement-rates) — not run because dependencies could not be installed.
- Change stream end-to-end: detecting FAILED settlements from the live cluster — not verified (change-stream watcher included in code but not executed).
- Creating indexes and verifying index usage with explain() from the app — code calls createIndex(), but index creation and explain-based verification were not run in this environment.
- Inserting sample data via the documentdb MCP server — attempted but MCP insert call failed ('Function failed.'); exact error details were not returned by the MCP tool.

## Open issues

- Dependency installation failed in this environment: npm returned 'No matching version found for mongoose@^7.14.0' on first attempt and subsequent pinned 7.x versions also failed. This prevented runtime verification. Action: run `npm install` in an environment with normal npm registry access or adjust dependency pins to versions available in your registry.
- documentdb MCP server insert operations failed with 'Function failed.' when attempting to seed sample documents. The MCP server is available (list_databases worked), but insert failed — possible permission or transient error. Action: retry MCP insert or run the seed script from a developer machine with DOCUMENTDB_URI set.
- Change-stream resume token persistence is not implemented. For production or multi-shard clusters, implement resume-token persistence and robust backoff/error handling per guidance.
- Production security posture (private endpoints, Entra/RBAC, CMK for encryption) is not implemented here — sample reads connection string from environment and uses SCRAM-SHA-256 via cluster string; follow the documentdb-security skill guidance before using in production.

## Files

- `package.json`
- `README.md`
- `.env.example`
- `src/db.js`
- `src/models/trade.js`
- `src/index.js`
- `scripts/seed.js`
- `src/watcher/changeStream.js`

