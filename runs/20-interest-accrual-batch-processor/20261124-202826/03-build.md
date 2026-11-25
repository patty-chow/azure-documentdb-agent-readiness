# 3. Build report: 20-interest-accrual-batch-processor

**Status: completed**

A small Node.js sample app was created that connects to an existing Azure DocumentDB cluster (read from process.env.DOCUMENTDB_URI), seeds sample accounts, and runs a daily accrual job that iterates active interest-bearing accounts using a cursor, computes daily interest, and writes immutable per-account journal documents using unordered bulkWrite calls. Indexes (partial index on accounts and unique compound index on accrual_journal) are created by the sample to support the query pattern and idempotency. I ran the seed and a one-time accrual run against the live cluster and verified indexes and inserted journal documents via the DocumentDB MCP tools.

## How to run

1. Copy .env.example -> .env and set DOCUMENTDB_URI to your cluster connection string (the sample expects the data-plane connection string provided in the run environment). Optionally set DB_NAME, BATCH_SIZE, and CRON_SCHEDULE. 2. npm install 3. npm run seed           # idempotent upsert of ~100 sample accounts 4. npm run start:once     # run the accrual job once for verification 5. To run scheduled daily, use npm start (node-cron schedule; default CRON_SCHEDULE='0 0 * * *' UTC).

## Verified by running

- npm install --no-audit --no-fund: exit code 0 (dependencies installed)
- npm run seed: exit code 0; seed summary reported nUpserted: 100 (100 accounts upserted)
- npm run start:once: exit code 0; sample run printed 'Run completed. Processed ~75 accruals (attempted inserts).' (75 accrual documents present after the run)
- documentdb_list_indexes (db sample_banking_20, collection accounts): returned indexes including 'idx_active_interestBearing' (partialFilterExpression: {status:'active', interestBearing:true}) and unique accountNumber index
- documentdb_list_indexes (db sample_banking_20, collection accrual_journal): returned indexes including 'uidx_account_runDate' unique compound index
- documentdb_find_documents (accrual_journal) returned sample documents and total_count: 75 (journal entries created by the run)
- npm test (jest): 1 test passed (accrual calculation unit test)

## Not verified

None.

## Open issues

None.

## Files

- `package.json`
- `.env.example`
- `README.md`
- `src/db.js`
- `src/models/account.js`
- `src/models/journal.js`
- `src/worker.js`
- `scripts/seed.js`
- `tests/worker.test.js`

