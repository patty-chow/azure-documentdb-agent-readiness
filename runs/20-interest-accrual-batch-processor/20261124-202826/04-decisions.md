# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 3 |
| readiness_report | 2 |
| operator | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T10:57:39+00:00

## D002 (build): I chose Mongoose 7.x (ODM) for the sample, pinned with a caret range in package.json.

- **Instead of:** Mongoose 6.x with mongodb driver 4.x; Native mongodb driver 5.x without Mongoose; Mongoose 7.x (ODM)
- **Because:** Mongoose provides convenient schemas, validation, and an easy-to-understand model layer for a short sample; it aligns with the prompt review assumption and works well for cursor + bulkWrite patterns.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Use Mongoose 7.x (the current major compatible with Node 24) and the accompanying MongoDB driver 5.x; pin with caret ranges in package.json'
- **When:** 2026-11-25T10:58:05+00:00

## D003 (build): I chose to read the cluster connection string from process.env.DOCUMENTDB_URI at runtime.

- **Instead of:** Use Microsoft Entra/OIDC auth; Read SCRAM credentials from env; Read full connection string from process.env.DOCUMENTDB_URI
- **Because:** The run environment guarantees DOCUMENTDB_URI is provided; using it avoids hardcoding credentials or requiring additional auth setup in this sample.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report guidance: 'Read your connection string from process.env.DOCUMENTDB_URI at runtime and use the exact connection string the cluster provides (do not hardcode cosmos.mongo host suffix or port assumptions).'
- **When:** 2026-11-25T10:58:08+00:00

## D004 (build): I chose node-cron with default schedule '0 0 * * *' (midnight UTC) and provide a --once CLI flag for manual runs.

- **Instead of:** Use setInterval daily in local timezone; Use node-cron default local timezone; Use node-cron and default to midnight UTC '0 0 * * *' plus a --once flag
- **Because:** node-cron is lightweight and well-known; midnight UTC is an unambiguous default for a daily accrual job; --once supports manual verification runs.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Default cron schedule: "0 0 * * *" (midnight UTC) and provide a --once flag for manual runs.'
- **When:** 2026-11-25T10:58:12+00:00

## D005 (build): I chose a default batch size of 500 for cursor pagination and bulk writes.

- **Instead of:** Batch size 100; Batch size 500; Batch size 5000
- **Because:** 500 provides a balance between memory usage and throughput for a sample; it's adjustable via env var BATCH_SIZE for production tuning.
- **Reason came from:** `model_default`
- **Evidence:** Prompt asks for cursor-paginated batches; prompt review suggested batching but left size ambiguous.
- **When:** 2026-11-25T10:58:17+00:00

## D006 (build): I chose to create a partial compound index on accounts for {status:1, interestBearing:1} (partialFilterExpression to match active interest-bearing accounts) and an index on accrual_journal {accountId:1, runDate:1} with a unique constraint to help idempotency.

- **Instead of:** No special indexes; Create a compound partial index on {status, interestBearing} for account selection and index on journal.accountId+createdAt; Create a hashed shard key
- **Because:** A partial index speeds the account selection query and reduces write index budget; a unique compound index on accountId+runDate prevents duplicate journal entries for the same run (supports idempotency in the sample).
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report guidance: 'create supporting indexes (partial index on active/interestBearing and an index on accrual_journal.accountId, createdAt).'
Also documentdb-indexing skill recommended partial index for active/interest-bearing filters.
- **When:** 2026-11-25T10:58:21+00:00
