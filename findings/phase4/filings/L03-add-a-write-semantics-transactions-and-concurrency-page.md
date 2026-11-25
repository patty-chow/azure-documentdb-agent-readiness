---
id: L03
title: "Add a write semantics, transactions and concurrency page for Azure DocumentDB (retrywrites, write concern, idempotency)"
repo: learn-docs
type: learn-feedback
status: needs_sme
priority: P1
sample_count: 42
member_drafts:
  - 076-reliability-and-write-semantics-on-azure-documentdb-retrywri.md
  - 124-transactions-concurrency-control-write-durability-and-idempo.md
open_questions: 7
---

# Add a write semantics, transactions and concurrency page for Azure DocumentDB (retrywrites, write concern, idempotency)

## What happens today

Learn covers pieces of this on separate pages, which disagree on retryable writes:

- **Connection string.** Every quickstart (for example `quickstart-nodejs`) shows `retrywrites=false&maxIdleTimeMS=120000` with no explanation. `tutorial-nodejs-mongoose` has a "Why keep retryWrites=false?" section that calls it a sample choice, not a service requirement. `azure/reliability/reliability-documentdb` ("Resilience to transient faults") advises exponential backoff and idempotent writes, but also says to "use MongoDB drivers that support automatic retry handling". Readers cannot tell whether retryable writes are unsupported, discouraged or optional.
- **Transactions.** `how-to-transactions` shows the Node.js `withTransaction()` pattern; Python and Java get only manual start/commit. `limitations` states a 30-second lifetime. Nothing says when to avoid a transaction, what it costs across shards, or how the driver's `withTransaction()` retry loop (120-second default) interacts with the 30-second lifetime and `retrywrites=false`.
- **Write and read concern.** `high-availability` and the reliability page document synchronous in-region HA and asynchronous cross-region replicas. No page says which client `w`/`j`/`wtimeoutMS`, `readConcern` or `readPreference` values are honored, ignored or rejected. `compatibility-query-language` lists only `getDefaultRWConcern` (supported) and `setDefaultRWConcern` (not supported).
- **Concurrency and bulk writes.** No page has an application retry sample, an optimistic-concurrency or job-lease recipe, or change-stream deduplication guidance. The compatibility page marks the `bulkWrite` command "No" while `limitations` allows 25,000 writes per batch.

## Why it matters

We ran 100 Azure DocumentDB sample prompts through a coding agent (gpt-5-mini) with the DocumentDB Agent Kit and the DocumentDB, Azure and Learn MCP servers. 64 audit findings from 42 of the 100 samples trace to this gap. Counts are from one experiment run. With no page to cite, the agent:

- set `retryWrites=true` in at least 19 generated apps, unlike the documented connection string;
- shipped no application-level retry in most samples;
- left write and read concern at driver defaults in ledger samples, and twice recorded "client writeConcern is ignored" as fact from a Cosmos DB (RU) page;
- versioned records by reading the max and inserting max+1, and used unconditional `updateOne` calls, so concurrent writers overwrite each other;
- wrote `startSession()`/`withTransaction()` code from prior knowledge, because no page shows the session pattern together with error-label retry handling;
- computed aggregates such as drawdown client-side because it could not tell whether `$setWindowFields` is available on its server version;
- kept unbounded `$push` arrays, did not persist change-stream resume tokens, and guessed bulk batch sizes.

## Proposed change

Add a page, suggested slug `azure/documentdb/write-semantics-transactions-concurrency`, that builds on the "Resilience to transient faults" section of `reliability-documentdb` and links to it rather than restating it. Link the new page from the quickstarts (`quickstart-nodejs`, `quickstart-python`, `quickstart-dotnet`), `how-to-connect-mongo-shell`, `tutorial-nodejs-mongoose`, `change-streams`, `how-to-transactions`, `compatibility-query-language`, `limitations`, `high-availability` and `reliability-documentdb`. Sections:

1. **Retryable writes.** One engineering-confirmed statement of whether the service supports driver retryable writes, what happens if a client enables them, and why the connection string sets `retrywrites=false`; say what the driver does on a transient failure when they are off, and state the consequence (the application owns write retries, so make writes idempotent and wrap them in a bounded retry). Put the note directly under the connection string and mirror it in the quickstarts and the Mongoose tutorial. Reword the reliability page's "use MongoDB drivers that support automatic retry handling" line so it no longer appears to contradict `retrywrites=false` (for example: drivers may retry reads and server selection, but write retries belong in application code).
2. **Application retry recipes.** PyMongo (for example a tenacity decorator) and Node.js/Mongoose `withRetry()` helpers used at the repository layer: initial delay 100-250 ms, factor 2, full jitter, at most 4-5 attempts. What to retry (network/timeout errors, `TransientTransactionError`, `UnknownTransactionCommitResult`, write conflicts) and what never to retry blindly (duplicate key `11000`, validation, auth). Describe what clients see on a saturated cluster, and note that `429`/`Retry-After` handling belongs to the embedding and LLM endpoints that RAG samples call, not to the cluster, if engineering confirms the cluster does not return it. Pair retries with idempotency keys or unique indexes; for unordered `bulkWrite`, retry only the transient `writeErrors`.
3. **Write concern, read concern, read preference.** Default values, which values are honored, and the durability each gives with and without in-region HA and with cross-region replicas. Tie it to the documented replication model (synchronous in-region HA; asynchronous cross-region replicas reached through a separate replica connection string). Add a decision table with recommended defaults for ledger writes versus analytics reads, a `db.adminCommand({ getDefaultRWConcern: 1 })` one-liner to show the cluster defaults, and a note that `setDefaultRWConcern` is not supported.
4. **Transactions.** Scope (including cross-shard), cost and limits beyond the 30-second lifetime, how `withTransaction()` retries relate to that lifetime and to `retrywrites=false`, and when to prefer a single-document atomic update (`findOneAndUpdate` with `$inc`/`$set`, or an upsert), for example on high-throughput ingestion or read-heavy vector-search paths. Show the Node.js `withTransaction()` example with a note that every operation in the callback must receive `{ session }`, plus the Mongoose equivalent. Add Python `with_transaction()` and Java `withTransaction()` snippets to `how-to-transactions`.
5. **Optimistic concurrency and atomic patterns.** Version field: `updateOne({ _id, version: n }, { $set: {...}, $inc: { version: 1 } })`, treating `matchedCount === 0` (or a null `findOneAndUpdate` result) as a conflict, then re-reading and retrying a bounded number of times. Job lease: `findOneAndUpdate({ _id, status: 'submitted' }, { $set: { status: 'processing', owner, locked_at } })`, plus how to reclaim expired leases. Counter document with `$inc` and `upsert`. Bounded history with `$push` and `$slice`, citing the 16 MB limit. State whether any `_etag`-like mechanism exists.
6. **Change-stream consumers and bulk loads.** Make consumers idempotent: persist the resume token to a checkpoint collection after each batch and resume with `resumeAfter`, deduplicate by event id (a unique index on an idempotency key with an upsert-based handler) instead of applying a blind `$inc`; link `change-streams`. Clarify the `bulkWrite: No` row, give a batch-size range per tier, and never exceed the documented 25,000 writes per batch, and advise building unique indexes in an idempotent deployment or migration script rather than at worker startup, since the build blocks writes.
7. **Operator availability by server version.** Point to the compatibility table, give a detection one-liner (`db.version()` or `db.runCommand({ buildInfo: 1 })`), and show a worked server-side `$setWindowFields` running-max pipeline.

Related: the Agent Kit contradicts itself on `retryWrites` (its deployment skill says `retrywrites=false` is required, while other skills use `retryWrites: true`). That fix is tracked separately against Azure/documentdb-agent-kit; once this page exists the kit can link to it.

## Evidence

Run folders in the experiment repository:

- `runs/03-core-banking-transaction-ledger/20261124-200452` (transactions written from prior knowledge)
- `runs/13-household-grouping-linkage/20261124-204947` (`app/src/db.js` sets `retryWrites: true`)
- `runs/02-swift-message-parser-store/20261124-200226` ("writeConcern ignored" taken from an RU-era page)
- `runs/16-multi-touch-attribution-model/20261124-205342` (`app/src/attribution.py` read-max-then-insert versioning)
- `runs/09-lead-scoring-agent/20261124-204408` (unconditional `updateOne` in `app/src/scoreLead.js`)
- `runs/20-interest-accrual-batch-processor/20261124-202826` (guessed bulk batch size, indexes built at startup)
- `runs/13-algorithmic-trade-journal/20261124-191835` (`$setWindowFields` availability not discoverable; drawdown computed client-side)
- `runs/19-proactive-outreach-orchestration/20261124-205844` ("writeConcern ignored" recorded as fact; resume tokens not persisted)

## Open questions

1. [needs SME confirmation] Retryable writes. Two positions circulate: that the service does not support retryable writes and leaving them on causes errors (the Agent Kit's deployment skill), and that `retrywrites=false` is a sample choice the service does not require (the Mongoose tutorial). What is the engineering answer, and what happens if a client sets `retryWrites=true`?
2. [needs SME confirmation] Which `w`/`j`/`wtimeoutMS`, `readConcern` and `readPreference` values are honored, and what are the defaults?
3. [needs SME confirmation] Does the service ever return 429 or error 16500 under load, or only timeouts and latency?
4. [needs SME confirmation] Are multi-document transactions supported across shards, at what cost, and with what size limits?
5. [needs SME confirmation] Does the compatibility page's `bulkWrite: No` row refer only to the MongoDB 8.0 server command, with the driver's `collection.bulkWrite()` working?
6. [needs SME confirmation] Is there any server-side `_etag` or equivalent concurrency token?
7. [needs SME confirmation] What batch-size range fits each tier, and can change-stream events replay after a resume (including multishard streams, and are they GA)?

## Source drafts

- 076-reliability-and-write-semantics-on-azure-documentdb-retrywri.md
- 124-transactions-concurrency-control-write-durability-and-idempo.md
