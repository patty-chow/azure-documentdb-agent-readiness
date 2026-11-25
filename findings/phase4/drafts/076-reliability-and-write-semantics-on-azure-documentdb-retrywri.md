---
title: "Learn: add a \"Write semantics, transactions, and concurrency\" page for Azure DocumentDB (retrywrites=false rationale, write/read concern behavior, retry and atomic-update recipes)"
repo: learn-docs
type: learn-feedback
status: ready_with_edits
priority: P1
sample_count: 40
findings: 52
bucket: learn-doc_gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Add a "Write semantics, transactions, and concurrency" page for Azure DocumentDB

## What happens today

- Every quickstart (for example https://learn.microsoft.com/en-us/azure/documentdb/quickstart-nodejs) shows the canonical connection string with `retrywrites=false&maxIdleTimeMS=120000`, but no Azure DocumentDB page says why driver-managed retryable writes are turned off or what the application must do instead.
- Conceptual retry guidance does exist, but on a page outside the `/azure/documentdb/` tree that builders did not find: https://learn.microsoft.com/en-us/azure/reliability/reliability-documentdb ("Resilience to transient faults") tells readers to configure retries with exponential backoff, limit retry attempts, and make writes idempotent. It also says to "use MongoDB drivers that support automatic retry handling", which reads as contradicting `retrywrites=false` unless it is explained. It has no code.
- The replication model is documented: in-region HA replicates synchronously (writes are persisted on primary and standby before the response, per the reliability page and https://learn.microsoft.com/en-us/azure/documentdb/high-availability), and cross-region replicas are asynchronous. No page says how client `writeConcern` (`w`, `j`, `wtimeoutMS`), `readConcern` or `readPreference` values relate to that model, or whether they are honored, accepted and ignored, or rejected. The compatibility page (https://learn.microsoft.com/en-us/azure/documentdb/compatibility-query-language) only lists `getDefaultRWConcern` as supported and `setDefaultRWConcern` as not.
- Transactions appear only as supported `startSession`/`commitTransaction`/`abortTransaction` rows on the compatibility page and the bullet "Maximum transaction lifetime: 30 seconds" on https://learn.microsoft.com/en-us/azure/documentdb/limitations. There is no example and no guidance on when a single-document atomic update is the better choice.
- No page has a retry code sample, an optimistic-concurrency recipe, a claim-and-process (job-lease) pattern, or guidance on handling `bulkWrite` errors. The compatibility page marks the `bulkWrite` *command* as "No". Unless readers know that row means the MongoDB 8.0 server command, not the driver's `collection.bulkWrite()` helper, they read it as "bulk writes are unsupported". The limits page separately says write and bulk batch operations are supported up to 25,000 writes per batch.

## Why it matters

An experiment ran 100 Azure DocumentDB sample prompts (ledgers, inventory, multi-agent orchestration, RAG, batch processors) through gpt-5-mini with the DocumentDB Agent Kit and the DocumentDB, Azure and Learn MCP servers. 52 audit findings from 40 of the 100 samples share this root cause. With no vCore page to answer the question, the agent:

- **Set `retryWrites=true`, contradicting the documented connection string.** At least 19 generated apps do this (for example `runs/13-household-grouping-linkage/20261124-204947/app/src/db.js`, which sets `retryWrites: true, retryReads: true` in the Mongoose options), following general MongoDB advice. The audit flagged it but could not cite a Learn page that explains the consequence.
- **Shipped no application-level retry** in most samples. Only a handful of the generated apps contain any explicit backoff or tenacity code. Builders repeatedly wrote that retry guidance exists conceptually but there is no copy-paste helper for this service (03-core-banking-transaction-ledger, 04-earnings-call-rag-assistant, 09-crypto-wallet-activity-analyzer, 12-cross-border-payment-audit-trail, 13-algorithmic-trade-journal, 20-store-locator-with-geospatial-search).
- **Left `writeConcern`/`readConcern`/`readPreference` at driver defaults** in ledger and PHI samples (13-chronic-disease-risk-predictor, 16-loyalty-points-ledger, 19-option-chain-data-store, 16-atm-network-status-monitor), because a search for "Azure DocumentDB writeConcern" returned no authoritative mapping. Two runs (02-swift-message-parser-store and 19-proactive-outreach-orchestration) recorded "Azure DocumentDB ignores client-specified writeConcern" as a learned fact. The only Learn page behind that belief was a Cosmos DB for MongoDB (RU) feature page, and no vCore page confirms or corrects it.
- **Chose non-atomic versioning.** 16-multi-touch-attribution-model does `find().sort("version",-1).limit(1)` and then `insert_one(version+1)` (`app/src/attribution.py`) instead of an atomic counter. 06-collateral-management-store does the same. 10-expense-report-auto-categorizer reads and then saves with no atomic claim. 09-lead-scoring-agent, 08-insurance-pre-auth-multi-agent, 14-loan-origination-workflow-orchestration and 15-digital-onboarding-orchestration update orchestration state with no version or expected-state filter.
- **Pushed unbounded arrays.** 14-loan-origination-workflow-orchestration keeps an ever-growing `transitions` list, with no `$slice` or history-collection guidance to cite.
- **Computed drawdown client-side.** 13-algorithmic-trade-journal could not find whether `$setWindowFields` is available on its server version. The compatibility page lists it as supported on 5.0-8.0, but a "how do I" question does not surface that.
- **Did not persist change-stream resume tokens** (19-proactive-outreach-orchestration). 20-interest-accrual-batch-processor picked `BATCH_SIZE=500` and created indexes at worker startup from model priors, noting that the docs give no batch-size range or guidance on creating indexes at deployment time.

## Proposed change

Create one conceptual page, proposed URL `https://learn.microsoft.com/en-us/azure/documentdb/write-semantics-transactions-concurrency` (title: "Write semantics, transactions, and concurrency in Azure DocumentDB"). It should build on the existing "Resilience to transient faults" section of `azure/reliability/reliability-documentdb` and link to it rather than restate it. Add a one-line cross-link to the new page from `quickstart-nodejs`, `quickstart-python`, `quickstart-dotnet`, `how-to-connect-mongo-shell`, `compatibility-query-language` (next to the `bulkWrite` and `*RWConcern` rows), `limitations` (next to the 30-second transaction bullet), `high-availability`, and `reliability-documentdb`. Sections:

### 1. Why the connection string sets `retrywrites=false`
Add a prominent note directly under the connection string, mirrored in the quickstarts. It should state, as the product team confirms it:
- whether Azure DocumentDB supports driver retryable writes, and what happens if a client leaves them on (error, silent no-op, or other);
- what the driver does on a transient failure when they are off;
- the consequence: "your application owns write retries; make writes idempotent and wrap them in a bounded retry".

Reword the reliability page's "use MongoDB drivers that support automatic retry handling" line so it no longer appears to contradict `retrywrites=false`. For example, say that drivers may retry reads and server selection automatically, but write retries belong in application code.

### 2. Application-level retry recipes (copy-paste)
- PyMongo: a small decorator (for example tenacity) with an initial delay of 100-250 ms, factor 2, full jitter and at most 4-5 attempts, wrapping `insert_one`/`update_one`/`find_one_and_update`.
- Node.js driver (and Mongoose): an equivalent `withRetry()` helper used at the repository layer.
- A classification table built from the error codes and labels the service actually returns:
  - Retry: network and timeout errors, `TransientTransactionError` and `UnknownTransactionCommitResult` labels (retry the whole transaction or the commit), and write conflicts.
  - Never retry blindly: duplicate key `11000`, validation errors, or auth errors.
  - Throttling: the vCore service bills by tier, not by request units, so it does not throttle like the RU-based API (429 / 16500). Document what clients see when a cluster is saturated (for example timeouts or high latency). Note that `429` with `Retry-After` handling applies to the embedding and LLM endpoints that RAG samples call alongside the database, not to the cluster.
- How to combine retries with idempotency keys or unique indexes so that a retried insert is safe.
- Unordered `bulkWrite`: inspect `writeErrors`, drop `11000` entries, and retry only the remaining transient failures.

### 3. writeConcern, readConcern and readPreference on Azure DocumentDB
Publish an authoritative statement, verified against the engine, of which `w`/`j`/`wtimeoutMS` values and which `readConcern`/`readPreference` values are accepted, honored, accepted and ignored, or rejected. Tie the statement to the replication model that is already documented: synchronous primary-to-standby HA in-region, and asynchronous cross-region replicas served through a separate replica connection string. Include:
- a decision table with recommended defaults for ledger and financial writes versus analytics and dashboard reads;
- a `db.adminCommand({ getDefaultRWConcern: 1 })` one-liner so readers can see the cluster defaults.

The experiment's agents currently believe client writeConcern is ignored, a belief carried over from RU-era pages. Whether that is true or false, this section settles it on a vCore page.

### 4. Multi-document transactions
- State the scope of multi-document ACID transaction support, and whether it covers multiple shards. Restate the 30-second maximum lifetime from the limits page. State the cost on vCore: there is no request-unit charge, but long transactions hold locks and use the cluster's compute.
- Example: `const session = client.startSession(); try { await session.withTransaction(async () => { await accounts.updateOne(filter, update, { session }); await ledger.insertOne(entry, { session }); }); } finally { await session.endSession(); }`. Note that every operation inside the callback must receive `{ session }`. Show the Mongoose equivalent.
- When not to use a transaction: prefer a single-document atomic update (`findOneAndUpdate` with `$inc`/`$set`) or a single-document upsert, for example in read-heavy vector-ingest paths.

### 5. Optimistic concurrency and atomic update patterns
- Version field: `updateOne({ _id, version: n }, { $set: {...}, $inc: { version: 1 } })`. Treat `matchedCount === 0` as a conflict, then re-read and retry a bounded number of times.
- Expected-state claim for orchestrators: `findOneAndUpdate({ _id, status: 'submitted' }, { $set: { status: 'processing', locked_at: now, owner } }, { returnDocument: 'after' })` as the atomic claim-and-process (job-lease) recipe, plus how to handle expired leases.
- Say plainly that the MongoDB-compatible API has no `_etag`-like server mechanism, if that is the case. The experiment's agents searched for one and found only Cosmos DB (NoSQL/RU) pages.
- Allocate monotonic versions with a counter document: `findOneAndUpdate({ _id: key }, { $inc: { seq: 1 } }, { upsert: true, returnDocument: 'after' })`, instead of reading the current maximum and inserting max+1.
- Bounded history: `$push: { transitions: { $each: [t], $slice: -200 } }`, or a separate history collection keyed by parent id, citing the 16 MB document limit.
- Idempotent change-stream consumers: persist the resume token to a collection after each batch, resume with `resumeAfter`, and deduplicate by event id rather than applying a blind `$inc`. Link the change streams page for the options the service supports.

### 6. Write-path operational notes
- Unordered `bulkWrite`: give a starting batch range (for example a few hundred to about 1,000 operations per call on M30-class clusters), tuned down if timeouts or CPU pressure appear, and never above the 25,000-writes-per-batch limit. Clarify that the compatibility page's "bulkWrite: No" refers to the MongoDB 8.0 server command, and that the driver's `collection.bulkWrite()` works because it is sent as `insert`/`update`/`delete` commands.
- Create indexes, especially unique indexes, which the limits page says block writes on the collection while they build, in an idempotent deployment or migration script rather than at worker startup.
- Operator availability by server version: point to the compatibility table, give a detection one-liner (`db.version()` or `db.runCommand({ buildInfo: 1 })`), and show a worked server-side `$setWindowFields` running-max pipeline.

Related: the Agent Kit contradicts itself on the same point. `skills/connection/SKILL.md` shows `retryWrites=true`, and `skills/driver/driver-singleton-client.md` and `skills/security/security-tls-required.md` use `retryWrites: true`, while `skills/azure-deployment/SKILL.md` says `retrywrites=false` is required. Once this Learn page exists, the kit can link to it instead of restating the rule. That fix is tracked separately against Azure/documentdb-agent-kit.

## Evidence (run folders under azure-documentdb-agent-readiness/runs; no credentials)

- `runs/03-core-banking-transaction-ledger/20261124-200452/doc-gaps.md`: no transactions example and no retry-label snippet (F0365, F0370).
- `runs/13-household-grouping-linkage/20261124-204947/app/src/db.js` and `doc-gaps.md`: the generated app sets `retryWrites: true`, and the audit could cite no Learn explanation (F2230).
- `runs/02-swift-message-parser-store/20261124-200226/doc-gaps.md`: "client writeConcern ignored" recorded as fact from an RU-era page (F0297). The same happens in `runs/19-proactive-outreach-orchestration/20261124-205844/05-audit.json` (F3339).
- `runs/16-multi-touch-attribution-model/20261124-205342/app/src/attribution.py`: read-max-then-insert versioning (F2729, F2730, F2731).
- `runs/20-interest-accrual-batch-processor/20261124-202826/doc-gaps.md`: bulkWrite batch size, duplicate-key filtering, indexes created at startup (F3408, F3410, F3411).
- `runs/13-algorithmic-trade-journal/20261124-191835/doc-gaps.md`: `$setWindowFields` availability not discoverable, so drawdown was computed client-side (F2134, F2135, F2137).

## Verification

### 1. Already covered? partially_covered
Parts of the request exist, spread across pages outside the place builders looked, and none provide what samples needed: code, a writeConcern/readConcern statement, a rationale for `retrywrites=false`, or concurrency recipes.
- https://learn.microsoft.com/en-us/azure/reliability/reliability-documentdb ("Resilience to transient faults") already gives conceptual retry guidance: "Configure retries with exponential backoff, and limit the number of retry attempts." It also says to design writes to be idempotent. It has no code, never mentions `retrywrites=false`, and its line about using "MongoDB drivers that support automatic retry handling" is unexplained next to the connection string. The draft now builds on this page instead of claiming no retry guidance exists.
- The same page and https://learn.microsoft.com/en-us/azure/documentdb/high-availability document the replication model: "Writes are persisted on both primary and standby shards before the service returns a response". Cross-region replication is asynchronous. Neither page mentions writeConcern, readConcern or readPreference.
- https://learn.microsoft.com/en-us/azure/documentdb/limitations has "Maximum transaction lifetime: 30 seconds", "Maximum writes per batch operation: 25,000 writes", the 16 MB document limit, and the note that unique index builds block writes.
- https://learn.microsoft.com/en-us/azure/documentdb/compatibility-query-language lists `getDefaultRWConcern` as Yes, `setDefaultRWConcern` as No, the `bulkWrite` command as No, session and transaction commands as Yes, and `$setWindowFields` as Yes on 5.0-8.0.
- https://learn.microsoft.com/en-us/azure/documentdb/quickstart-nodejs shows the `retrywrites=false` string with no explanation.
- Learn search (https://learn.microsoft.com/api/search for "documentdb retryable writes" and "documentdb write concern transactions") returned no Azure DocumentDB page on retryable writes, write concern or optimistic concurrency. The only optimistic-concurrency hit was the Cosmos DB (NoSQL) page.
- Agent Kit: grepping `skills/` and `knowledge-base/` finds no writeConcern, readConcern, readPreference, withTransaction or optimistic-concurrency content. The retryWrites guidance contradicts itself (see Related).

### 2. Is the premise true? confirmed (with factual corrections applied)
The core premise holds: the Learn facts the draft cites all match the pages above. These claims were corrected in the body:
- "No page has retry guidance" became "conceptual retry guidance exists on the reliability page, with no code and no `retrywrites=false` rationale", and the reliability page was added to the cross-link list.
- "Map writeConcern to the replication model" now names the replication model already documented (synchronous HA in-region, asynchronous cross-region) instead of implying it is undocumented.
- The draft asked for handling of "429 / Retry-After from the service". Azure DocumentDB (vCore) bills by compute tier, not request units, and does not throttle with 429/16500 the way the RU-based API does. The body now limits 429/Retry-After to embedding and LLM providers and asks the service to document what saturation looks like. "Tune down on throttling" became "tune down on timeouts or CPU pressure".
- "34 of 100 apps set retryWrites=true" could not be reproduced. A case-insensitive grep of `runs/*/*/app` finds `retryWrites ... true` in 19 sample slugs, so the body now says "at least 19". "Only 24 apps contain backoff code" and "about 76 shipped with no retry wrapper" could not be reproduced either (an explicit tenacity/backoff grep finds 3 samples), so the body now says "most samples" and "only a handful".
- The Agent Kit claims that Azure DocumentDB "does not support retryable writes" and that leaving them on "will cause connection errors" (`skills/azure-deployment/SKILL.md`) are not stated on Learn. The body asks the product team to state the actual behavior rather than asserting it.
- The resource type, connection-string shape (`retrywrites=false&maxIdleTimeMS=120000`), the vCore and M-tier cost model, and the "formerly Azure Cosmos DB for MongoDB vCore" lineage are all consistent with the known facts.

### 3. Maintainer skeptic: confirmed
As a Learn maintainer, I would accept this with the edits applied. It names a concrete new page and slug, the specific pages to cross-link, and a concrete correction to an existing page (the reliability page's automatic-retry line). It also asks questions only this service can answer: why `retrywrites=false`, whether writeConcern and readConcern are honored, transaction scope, whether an `_etag` exists, and what the `bulkWrite: No` row means. Purely generic hygiene from the original draft (a SIGINT/SIGTERM `client.close()` snippet, and a detailed tour of Mongoose `__v`/`VersionError`) was removed or reduced to keep the page DocumentDB-specific. The page belongs in Learn (MicrosoftDocs/nosql-docs-pr, `azure/documentdb/`). The related kit inconsistency is tracked separately against Azure/documentdb-agent-kit.

## Finding ids

F0297, F0365, F0370, F0577, F0716, F0781, F0835, F0867, F1152, F1242, F1314, F1420, F1454, F1539, F1574, F1643, F1670, F1671, F1743, F1850, F1940, F2006, F2038, F2074, F2134, F2135, F2137, F2205, F2211, F2230, F2263, F2264, F2269, F2440, F2441, F2501, F2531, F2635, F2665, F2699, F2729, F2730, F2731, F3162, F3311, F3339, F3408, F3410, F3411, F3451, F3484, F3515
