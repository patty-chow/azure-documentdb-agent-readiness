---
title: "Extend \"Group multiple operations in transactions\" with write concern, retry, concurrency-control and idempotent-consumer guidance for Azure DocumentDB"
repo: learn-docs
type: learn-feedback
status: ready_with_edits
priority: P1
sample_count: 11
findings: 12
bucket: learn-practice_not_public
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Extend "Group multiple operations in transactions" (how-to-transactions) with write-safety guidance for Azure DocumentDB

## What happens today
Learn already covers the basics of transactions on Azure DocumentDB, but the guidance is spread over several pages, and the parts agents needed most are missing:

- **Covered:** [how-to-transactions](https://learn.microsoft.com/en-us/azure/documentdb/how-to-transactions) shows the Node.js pattern: `startSession()`, `withTransaction()`, `{ session }` passed to every operation, and `endSession()` in `finally`. It notes that the callback can run more than once when the driver retries. It also has Java and Python start/commit and abort snippets.
- **Covered:** [limitations](https://learn.microsoft.com/en-us/azure/documentdb/limitations) states a 30-second maximum transaction lifetime.
- **Covered:** [compatibility-query-language](https://learn.microsoft.com/en-us/azure/documentdb/compatibility-query-language) lists `startSession`, `commitTransaction`, `abortTransaction` and `getDefaultRWConcern` as supported, and `setDefaultRWConcern` as not supported.
- **Covered:** [tutorial-nodejs-mongoose](https://learn.microsoft.com/en-us/azure/documentdb/tutorial-nodejs-mongoose) explains why its sample sets `retryWrites=false`, shows a single-document conditional `findOneAndUpdate` with `$inc`, warns that blind application retries can apply a write twice, and links to how-to-transactions.
- **Covered:** [change-streams](https://learn.microsoft.com/en-us/azure/documentdb/change-streams) shows how to persist and resume from resume tokens.

**Not covered on any of these pages:**
- **Write concern:** what the service's default `w`/`j` are (the value `getDefaultRWConcern` returns), which client-supplied `w`/`j` values are honored, and what durability each gives on a cluster with or without in-region HA.
- **When not to use transactions:** cost and limits beyond the 30-second lifetime (size, cross-shard cost), and when a single-document atomic update is preferable, for example on high-throughput ingestion or read-heavy vector-search paths.
- **Retry behavior:** how `withTransaction()` retry (on the `TransientTransactionError` and `UnknownTransactionCommitResult` labels, with the driver's default 120-second overall timeout) interacts with the service's 30-second transaction lifetime and with `retryWrites=false` in the documented connection string. With `retryWrites=false`, the driver does not retry `commitTransaction` on its own.
- **Optimistic concurrency for competing writers:** a version field in the `findOneAndUpdate` filter, `$inc` on that field in the update, and a retry when nothing matches.
- **Idempotent change-stream consumers:** events can be replayed after a resume, so the consumer needs a unique idempotency key or a processed-event checkpoint collection.
- **Python and Java `withTransaction` equivalents:** today the page shows only manual start/commit for these languages, without `with_transaction()` or `withTransaction()`.

## Why it matters
We ran an agent-readiness experiment over 100 Azure DocumentDB sample prompts (gpt-5-mini, with the DocumentDB Agent Kit and the Learn MCP server). 11 samples needed at least one of these patterns, and the audit marked 12 of those practices "prior_knowledge_only": the agent could not find a Learn page to cite for them. What that led to:
- **09-lead-scoring:** writes scores with an unconditional `updateOne` and no version check (app/src/scoreLead.js), so concurrent scorers can overwrite each other's updates.
- **19-option-chain:** leaves `writeConcern` at driver defaults because it could not confirm how the service maps write concern.
- **20-provider-directory:** could not confirm whether the usual "avoid multi-document transactions on hot paths" advice applies to this engine.
- **12-hospital-bed-occupancy:** found nothing on Learn about deduplicating change-stream events after a resume.
- **03-core-banking:** implemented `startSession()`/`withTransaction()` with `{ session }` correctly, but from prior knowledge. It reported that Learn has no one place that shows the session pattern together with error-label retry handling.
- **Other samples (loan origination, digital onboarding, insurance pre-auth):** fell back on generic MongoDB advice for competing writers.

## Proposed change
Extend https://learn.microsoft.com/en-us/azure/documentdb/how-to-transactions, or add a companion how-to linked from it and from tutorial-nodejs-mongoose. Add these sections:
1. **Limits and when not to use transactions:** link the 30-second lifetime and add any size or cross-shard cost guidance. The DocumentDB Agent Kit already says cross-shard transactions are supported but cost more. Say when to prefer single-document atomic updates.
2. **Retries:** how `withTransaction()` retries, what happens when its default 120-second timeout is longer than the 30-second service lifetime, and how `retryWrites=false` affects commit retries. Add Python `with_transaction()` and Java `withTransaction()` snippets next to the existing Node.js one.
3. **Write concern:** the service default (as returned by `getDefaultRWConcern`), which `w`/`j` values are honored, and what each guarantees with and without in-region HA. Note that `setDefaultRWConcern` isn't supported.
4. **Optimistic concurrency:** `findOneAndUpdate({ _id, version }, { $set: {...}, $inc: { version: 1 } })`, then a bounded retry loop when it returns null.
5. **Idempotent consumers:** a unique index on an idempotency key, an upsert-based handler, and a processed-event or resume-token checkpoint collection. Link to change-streams.

## Evidence (run folders)
- runs/03-core-banking-transaction-ledger/20261124-200452 (05-audit.json practice "Session + withTransaction pattern", prior_knowledge_only, followed; doc gap "Public pattern for Mongoose transactions + session usage")
- runs/09-lead-scoring-agent/20261124-204408 (05-audit.json practice "Optimistic concurrency"; doc gap "Optimistic concurrency for scoring writes")
- runs/19-option-chain-data-store/20261124-192712 (05-audit.json practice "Write concern and durability"; doc gap "Write concern mapping docs")
- runs/12-hospital-bed-occupancy-tracker/20261124-194835 (05-audit.json practice "Change-stream idempotency")
- runs/20-provider-directory-semantic-search/20261124-200008 (05-audit.json practice "Transactions guidance"; doc gap "Public guidance on multi-document transactions")
- Also: runs/02-real-time-event-stream-ingestion/20261124-203233, runs/04-regulatory-reporting-orchestration/20261124-200545, runs/07-multi-currency-ledger/20261124-190814, runs/08-insurance-pre-auth-multi-agent/20261124-194215, runs/14-loan-origination-workflow-orchestration/20261124-191837, runs/15-digital-onboarding-orchestration/20261124-202211

## Verification

### 1. Already covered? partially_covered
The original draft said no page covers transactions. That is wrong: several Learn pages cover the basics.
- https://learn.microsoft.com/en-us/azure/documentdb/how-to-transactions ("Group multiple operations in transactions", updated 2026-11-18). It shows `startSession()` and `withTransaction()`, with the instruction "Pass the session in the options for every operation that belongs to the transaction", and notes that "The callback can run more than once if the driver retries the transaction."
- https://learn.microsoft.com/en-us/azure/documentdb/limitations: "Maximum transaction lifetime: 30 seconds."
- https://learn.microsoft.com/en-us/azure/documentdb/compatibility-query-language: session commands are supported, `getDefaultRWConcern` is supported, `setDefaultRWConcern` is not.
- https://learn.microsoft.com/en-us/azure/documentdb/tutorial-nodejs-mongoose: has a "Why keep retryWrites=false?" section, a Sessions and transactions row linking how-to-transactions, and a conditional `findOneAndUpdate` reservation.
- https://learn.microsoft.com/en-us/azure/documentdb/change-streams: shows resume tokens with `resumeAfter`.

None of these pages covers write-concern semantics, when to avoid transactions, how retries interact with `retryWrites=false` and the 30-second lifetime, version-based optimistic concurrency, or change-stream consumer deduplication.
- **Agent Kit:** skills/sharding/sharding-logical-vs-physical.md says cross-shard transactions "are supported but cost more", and skills/natural-language-querying/SKILL.md line 258 says transactions are supported. Neither says anything about write concern, optimistic concurrency or idempotency.
- **documentdb-mcp:** no transaction or write-concern guidance found.

The draft was rewritten to extend the existing page rather than ask for a new one.

### 2. Is the premise true? confirmed (with corrections applied)
The service facts in the draft are consistent with the sources above. Three claims were corrected:
- **"No page covers transactions":** replaced with the covered/not-covered split above.
- **"03-core-banking used withTransaction with no retry on transient transaction errors":** wrong. `withTransaction()` already retries on the `TransientTransactionError` and `UnknownTransactionCommitResult` labels, and how-to-transactions says so. The 05-audit.json in that run marks the pattern "followed". The run's real gap was that it had to rely on prior knowledge.
- **"retrywrites=false affects transaction retries":** made precise. The `withTransaction()` callback and commit loops run regardless of `retryWrites`. `retryWrites=false` only stops the driver's single automatic retry of the commit and of other eligible writes. tutorial-nodejs-mongoose says the setting is a sample choice, "not a statement that Azure DocumentDB requires retryable writes to be disabled".

The 09-lead-scoring claim is confirmed by its 05-audit.json evidence: an unconditional `updateOne` in app/src/scoreLead.js line 65.

### 3. Maintainer skeptic: confirmed
I would accept this as feedback on the how-to-transactions page. It names a specific page and specific sections, and most of the asks are specific to this service:
- the default write concern and which values are honored
- the 30-second lifetime against the driver's 120-second `withTransaction` timeout
- `retryWrites=false` in the documented connection strings
- cross-shard transaction cost

The optimistic-concurrency and idempotent-consumer sections are closer to general MongoDB practice. They are kept as short sections because they are the alternative the page should point to when it tells readers not to use transactions. Evidence covers 11 samples.

## Finding ids
- F0278
- F0377
- F0690
- F1155
- F1254
- F1545
- F1550
- F2448
- F2540
- F2078
- F3317
- F3490
