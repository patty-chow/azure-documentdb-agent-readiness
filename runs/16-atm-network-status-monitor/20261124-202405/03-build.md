# 3. Build report: 16-atm-network-status-monitor

**Status: partial**

I built a Node.js + Mongoose sample ATM network status monitor app (source files, models, logic, seed script, tests, README) that reads the Azure DocumentDB connection from DOCUMENTDB_URI. I loaded DocumentDB guidance skills and created all app files. I attempted to install Node dependencies twice but npm install failed (registry/version resolution error), so I could not run the seed, start the app, or execute tests against the live cluster. I did verify that the documentdb MCP server is available and listed existing databases (the target sample database sample_banking_16 was not present). The repository is ready to run once dependencies can be installed and the environment has a reachable DOCUMENTDB_URI.

## How to run

1) Copy .env.example -> .env and set DOCUMENTDB_URI to your cluster's connection string. Optionally set DATABASE_NAME and AVAILABILITY_THRESHOLD (default 0.95).
2) npm install
3) npm run seed   # inserts idempotent sample ATMs and initial heartbeats; updates per-ATM status and writes the network summary
4) npm start      # starts the Express API (POST /heartbeat, GET /summary) and a change-stream listener (long-running)
5) npm test       # runs unit tests (uses mongodb-memory-server for in-memory DB)

Notes:
- The app reads DOCUMENTDB_URI at runtime and never writes secrets to the repo.
- The DB used is the DATABASE_NAME env var, default 'sample_banking_16'.
- If you cannot run a local DocumentDB gateway, point DOCUMENTDB_URI to the provided live cluster.

## Verified by running

- Loaded skills: documentdb-driver, documentdb-connection, documentdb-local-deployment (loaded via load_skill).
- Wrote app source files and tests (listed in files_created).
- Attempted npm install twice; both attempts failed with npm ETARGET errors (no matching package version for supertest).
- Queried the documentdb MCP server for databases (documentdb_list_databases) and received: sample_banking_15, sample_banking_13 (no sample_banking_16 present).

## Not verified

- npm install (failed due to npm ETARGET errors) — could not install dependencies, so cannot run seed, start, or tests.
- npm run seed — seed script not executed because dependencies missing; no sample data was loaded into the live cluster.
- Starting the long-running Express server (npm start) and change-stream behavior — not executed (long-running processes are not started in this run and dependencies were not installed).
- Automated verification of created collections/indexes in the target database 'sample_banking_16' — not performed because seed did not run.
- Integration tests and endpoint verification (POST /heartbeat, GET /summary) — not run due to missing dependencies.

## Open issues

- npm install failed twice with errors: 'No matching version found for supertest@^6.4.4' (and on retry for 6.4.3). This prevented dependency installation and running seed/start/tests. Possible causes: network/registry access, or selected dev dependency versions unavailable in this environment. Action: retry npm install in an environment with network access or adjust dev dependency versions to available ones.
- The sample_banking_16 database was not present on the cluster when I listed databases; because seed was not run I did not create it. After installing dependencies, run `npm run seed` to populate sample_banking_16 and verify behavior.
- I did not run mongosh; the readiness report recommended installing mongosh for manual verification. If you prefer interactive verification, install mongosh or use the documentdb MCP server tools.

## Files

- `package.json`
- `.env.example`
- `.gitignore`
- `README.md`
- `db.js`
- `models/heartbeat.js`
- `models/atmStatus.js`
- `models/summary.js`
- `models/alert.js`
- `logic/summaryUpdater.js`
- `seed.js`
- `index.js`
- `test/heartbeat.test.js`

