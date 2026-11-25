---
title: "Three small reference gaps on Azure DocumentDB Learn pages: transaction limits not linked from the transactions how-to, no TTL-index section (search lands on the RU `_ts` page), no `$setWindowFields` stage page or running-total example"
repo: learn-docs
type: learn-feedback
status: ready_with_edits
priority: P2
sample_count: 3
findings: 3
bucket: learn-information_gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Three small reference gaps on Azure DocumentDB Learn pages (transaction limits, TTL indexes, `$setWindowFields`)

Source: an automated "agent readiness" experiment that had gpt-5-mini build 100 Azure DocumentDB sample apps using the DocumentDB Agent Kit skills plus the Learn, Azure and DocumentDB MCP servers. Each item below was raised by one sample's cold-quiz/readiness stage and then checked against the live Learn pages on 2026-11-25. The three items are independent. Each is a small PR to `MicrosoftDocs/nosql-docs-pr`.

---

## A. Transaction limits are documented, but not where anyone looks for them

**Today.** `azure/documentdb/limitations.md` has one line about transactions, under *Query and execution limitations > MongoDB execution limitations*: "Maximum transaction lifetime: 30 seconds." The transactions how-to, `azure/documentdb/how-to-transactions.md` (ms.date 2023-08-28), does not mention the limit and does not link to the limits page. On retry or abort behaviour it only says that the `withTransaction()` callback "can run more than once if the driver retries the transaction". The Java and Python tabs use `startTransaction()`/`commitTransaction()` and show no retry handling at all.

**What the agents did.** Sample `07-multi-currency-ledger` wrote in its readiness report that it found no authoritative statement of transaction limits and retry behaviour. It tried `load_skill("documentdb-transactions")` (no such skill exists) and shipped transactional posting with no timeout or retry handling. The audit stage flagged "Transaction lifetime and retry limits guidance" as a high-priority doc gap. Other samples (for example `05-shopping-cart-with-real-time-inventory`, `16-atm-network-status-monitor` and `19-proactive-outreach-orchestration`) ran Learn searches for the 30-second transaction lifetime. In all, six of the 100 samples raised a transaction-limits finding in their readiness, audit or doc-gap output.

**Proposed change.**
1. `how-to-transactions.md`: add a **"Limits and retry behavior"** section after *Roll back a transaction*:
   - "A transaction must complete within **30 seconds** of starting, or the server aborts it. See [Service limits](limitations#mongodb-execution-limitations)." List any other transaction constraints that apply (operations or documents per transaction, cross-shard transactions, size). If there are none beyond the lifetime and the 16 MB document limit, say so explicitly.
   - Show the driver-neutral retry pattern: retry the whole transaction on `TransientTransactionError`, retry only the commit on `UnknownTransactionCommitResult`, and keep transactions short (few documents, no network calls inside the callback).
   - Note that `withTransaction()` already implements this retry loop. The explicit loop is needed only with `startTransaction()`/`commitTransaction()`, which the Java and Python tabs use today.
2. `limitations.md`: give transactions their own `### Transactions` sub-heading, so Learn search ranks it for "transaction lifetime", and link back to `how-to-transactions`.

---

## B. No TTL-index content for Azure DocumentDB, and search lands on the RU `_ts` page

**Today.** `azure/documentdb/indexing.md` covers single-field, compound, partial, text, wildcard and geospatial indexes, but not TTL. Neither it nor `limitations.md` mentions `expireAfterSeconds`. A Learn search for "TTL expireAfterSeconds documentdb" returns `azure/cosmos-db/mongodb/time-to-live` ("Per-Document TTL feature - Azure Cosmos DB for MongoDB") as the first article result. That page teaches `createIndex({"_ts":1}, {expireAfterSeconds: 10})` and a root-level per-document `ttl` property. Both are behaviours of the RU-based Azure Cosmos DB for MongoDB and do not apply to Azure DocumentDB.

**What the agent did.** Sample `12-hospital-bed-occupancy-tracker` ran three TTL searches, and the RU page came back first. It built the index correctly anyway (`createIndex({ cleaningExpiresAt: 1 }, { expireAfterSeconds: 0 })`, following the Agent Kit's `skills/indexing/index-ttl-expiry.md`). It still recorded an information gap about `_ts`-based TTL and wrote an extra `app/src/ttl_check.js` script whose only job was to prove that TTL fires on an arbitrary Date field. The outcome was correct, but the work was wasted and the model came away thinking `_ts` might matter.

**Proposed change.**
1. `azure/documentdb/indexing.md`: add a **"## TTL indexes"** section, plus a TOC or in-page entry, containing:
   - "Azure DocumentDB supports standard MongoDB TTL indexes. A TTL index is a single-field index on any field whose value is a BSON Date. A background process deletes a document once `fieldValue + expireAfterSeconds` has passed."
   - The two canonical forms: `db.sessions.createIndex({ createdAt: 1 }, { expireAfterSeconds: 3600 })`, and `db.beds.createIndex({ cleaningExpiresAt: 1 }, { expireAfterSeconds: 0 })` for "delete at exactly this time".
   - The rules:
     - TTL works only on single-field indexes, not compound ones.
     - The field must hold a Date. Numbers and strings are never expired, and neither are documents that lack the field.
     - Deletion is best-effort background work and may lag behind the expiry time.
   - A note: "Azure Cosmos DB for MongoDB (RU) implements TTL differently, with an index on the system `_ts` field and an optional per-document `ttl` property. Those concepts don't apply to Azure DocumentDB."
2. `azure/cosmos-db/mongodb/time-to-live.md`: the page already opens with an "Important" note that points MQL users to Azure DocumentDB. Extend it with one sentence: "Azure DocumentDB uses standard MongoDB TTL indexes on any Date field. It doesn't use `_ts` or a per-document `ttl` property. See [TTL indexes in Azure DocumentDB](../../documentdb/indexing#ttl-indexes)."

---

## C. `$setWindowFields` has no stage page and no running-total or running-max example

**Today.** The MQL reference at learn.microsoft.com/documentdb has a *Window Operators* section with 11 pages (`$covariancePop` through `$shift`, including `$expMovingAvg`, `$integral`, `$rank` and `$locf`). The accumulator pages (`$sum`, `$max`, `$min`, `$avg`, `$count`, `$stdDevPop`) also include "Using X in `$setWindowFields`" examples. However:
- No `$setWindowFields` stage page exists. `documentdb/query/operators/aggregation/$setwindowfields` returns 404, so nothing documents the `partitionBy`, `sortBy`, `output` and `window` parameters in one place.
- The `$sum` and `$max` window examples use only `documents: ["unbounded", "unbounded"]` (a whole-partition total) and no `sortBy`.
- Cumulative windows do appear, but only for statistical operators: `documents: ["unbounded", "current"]` on `$covariancePop`, `$covarianceSamp` and `$stdDevPop`, and `range: ["unbounded", "current"]` on `$integral`.
- No page shows a time-ordered running sum or running maximum. No page shows how to chain two `$setWindowFields` stages, which is needed when one output depends on another, as in drawdown.

**What the agent did.** Sample `13-algorithmic-trade-journal` needed the maximum drawdown over an ordered P&L series. Its Learn searches for "$setWindowFields Azure DocumentDB" returned only the migration guides and release notes, not the operator reference. It computed cumulative P&L and drawdown client-side, with a Python loop over the full result set (`app/app/aggregations.py`). The audit logged two high-priority gaps: no server-side drawdown example, and no actionable `$setWindowFields` guidance. Sample `09-crypto-wallet-activity-analyzer` hit the same wall for a server-side z-score and also fell back to client-side computation.

**Proposed change.** Add `documentdb/query/operators/aggregation/$setwindowfields.md`, linked from the window-operators index and the aggregation-stage index. It should give the syntax, describe the `partitionBy`/`sortBy`/`output`/`window` parameters (`documents` and `range` bounds), list the operators that can be used in `output`, and include one worked example that computes a running sum, a running maximum and a drawdown. Suggested example below. It uses only operators that the compatibility table lists as supported. Please validate it on a cluster before publishing, because the experiment did not run it.

```javascript
// Collection: trades { strategyId, closedAt: Date, pnl: Number }
db.trades.aggregate([
  { $match: { strategyId: "momentum-1" } },
  // 1. cumulative P&L in time order
  { $setWindowFields: {
      partitionBy: "$strategyId",
      sortBy: { closedAt: 1 },
      output: {
        cumulativePnl: { $sum: "$pnl", window: { documents: ["unbounded", "current"] } }
      }
  } },
  // 2. running peak of the cumulative series (a separate stage, because an output
  //    can't reference another output of the same $setWindowFields)
  { $setWindowFields: {
      partitionBy: "$strategyId",
      sortBy: { closedAt: 1 },
      output: {
        runningPeak: { $max: "$cumulativePnl", window: { documents: ["unbounded", "current"] } }
      }
  } },
  // 3. drawdown at each point, then the maximum
  { $set: { drawdown: { $subtract: ["$runningPeak", "$cumulativePnl"] } } },
  { $sort: { closedAt: 1 } },
  { $group: {
      _id: "$strategyId",
      maxDrawdown: { $max: "$drawdown" },
      finalPnl: { $last: "$cumulativePnl" }
  } }
])
```

Add two points the agents were missing:
- `sortBy` is required for any window other than `documents: ["unbounded", "unbounded"]`, which is why the existing `$sum` and `$max` examples can omit it.
- Large partitions are expensive. Set `maxTimeMS` (the default query execution limit is 120 seconds) and consider first pre-aggregating to one document per day with `$group` + `$dateTrunc`.

Optionally, cross-link the existing cumulative-window examples on `$stdDevPop` and `$covariancePop` from the new page.

---

## Why it matters

Only 3 of the 100 samples raised these exact findings (one each), but the cost was the same in all three. The fact exists or the feature works, yet the agent cannot find the page that says so. As a result it does one of three things:
- verifies at runtime with extra scripts (sample 12);
- falls back to client-side computation that doesn't scale (samples 13 and 09);
- ships without the safeguard the docs should have taught (sample 07, which has no transaction timeout or retry handling).

None of the three fixes needs new engine behaviour. Each is a few paragraphs on an existing page or one new reference page.

## Evidence (run folders in the experiment repo)

- `runs/07-multi-currency-ledger/20261124-190814/02-readiness.json` (information_gaps) and `05-audit.json` (doc_gaps "Transaction lifetime and retry limits guidance")
- `runs/05-shopping-cart-with-real-time-inventory/20261124-183232/events.jsonl` (transaction-related Learn searches)
- `runs/12-hospital-bed-occupancy-tracker/20261124-194835/events.jsonl` (TTL searches that returned the RU per-document TTL page) and `app/src/ttl_check.js`
- `runs/13-algorithmic-trade-journal/20261124-191835/05-audit.json` (doc_gaps) and `app/app/aggregations.py`
- `runs/09-crypto-wallet-activity-analyzer/20261124-191004/doc-gaps.md` ("Server-side z-score example")

## Verification

### 1. Already covered? partially_covered
- **A:** the fact is covered, but not where the agent looked. https://learn.microsoft.com/en-us/azure/documentdb/limitations (ms.date 2026-11-04) says, under "MongoDB execution limitations": "Maximum transaction lifetime: 30 seconds." https://learn.microsoft.com/en-us/azure/documentdb/how-to-transactions (ms.date 2023-08-28) has no limits section and no link to that page. Its only retry text is about the `withTransaction()` callback running more than once.
- **B:** not covered. https://learn.microsoft.com/en-us/azure/documentdb/indexing (ms.date 2024-09-23) has no TTL section and no `expireAfterSeconds`. The Learn search API for "TTL expireAfterSeconds documentdb" ranks https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/time-to-live second, after the product landing page. That page teaches `db.coll.createIndex({"_ts":1}, {expireAfterSeconds: 10})` and a per-document `ttl` property. The Agent Kit already covers TTL correctly in `skills/indexing/index-ttl-expiry.md` (single-field, non-compound, `expireAfterSeconds: 0` for an explicit expiry date). That is why the sample got it right; Learn is still missing the content.
- **C:** partially covered. Accumulator and window-operator pages do contain `$setWindowFields` examples:
  - https://learn.microsoft.com/en-us/documentdb/query/operators/accumulators/$sum has "Example 3: Using `$sum` in `$setWindowFields`" with `documents: ["unbounded", "unbounded"]`, and `$max` has the same pattern.
  - `$stdDevPop`, `$covariancePop` and `$covarianceSamp` use `documents: ["unbounded", "current"]`, and `$integral` uses `range: ["unbounded", "current"]`.
  - https://learn.microsoft.com/en-us/documentdb/query/operators/aggregation/$setwindowfields returns 404, and no page shows a running sum or running max over a sorted series.
  - The draft has been corrected to reflect this.

### 2. Is the premise true? confirmed (sub-claims corrected)
- Confirmed:
  - The 30-second lifetime is on /limitations, and the how-to has no limits section or link.
  - The DocumentDB indexing page has no TTL content.
  - The RU TTL page uses `_ts` and a per-document `ttl` property, and its own note says `_ts` is "an Azure Cosmos DB-specific field".
  - Standard MongoDB TTL semantics (a single-field index on a Date field) are what the Agent Kit documents for DocumentDB.
  - The `$setWindowFields` stage page is missing.
- Corrected in the body:
  - (a) The original draft said "`$sum`/`$max`/`$min`/`$avg` as window operators have no page". This is wrong: those accumulator pages include `$setWindowFields` examples.
  - (b) The original draft said no page shows `documents: ["unbounded","current"]`. This is wrong: `$stdDevPop`, `$covariancePop` and `$covarianceSamp` do. What is missing is a running sum or max, and chained stages.
  - (c) The original draft said "`sortBy` is required for any documents/range window". This is inaccurate, because the existing `$sum` example uses a `documents` window without `sortBy`. It now reads "required for any window other than `documents: ["unbounded","unbounded"]`".
  - (d) The unverified claim that "`$setWindowFields` holds a partition in memory" was softened to a cost note that cites the documented 120-second default execution limit.
  - (e) An explicit `$sort` was added before the `$group`/`$last` in the example.
  - (f) The claim that the RU page is the "top result" now says "first article result", since the landing page ranks first.
  - (g) An unverified sample reference (`07-lab-results-aggregator`) and an exact line range were removed.
- The "six of 100 samples" count for transaction-limits findings was re-checked by a grep across `02-readiness.json`, `05-audit.json` and `doc-gaps.md`. It matches: 05-shopping-cart, 06-collateral-management-store, 07-multi-currency-ledger, 09-trade-settlement-tracker, 16-loyalty-points-ledger and 16-subscription-billing-engine.

### 3. Maintainer skeptic: confirmed
Each item names exact source files in `MicrosoftDocs/nosql-docs-pr` (`azure/documentdb/how-to-transactions.md`, `azure/documentdb/limitations.md`, `azure/documentdb/indexing.md`, `azure/cosmos-db/mongodb/time-to-live.md`, and a new `documentdb/query/operators/aggregation/$setwindowfields.md`), with concrete text to add. All three are specific to Azure DocumentDB. B fixes an RU/vCore confusion that is a real correctness hazard. As a docs maintainer I would accept them as three small PRs. The only caveat is that the C example must be run on a cluster before it is merged.

## Finding ids
- F1143
- F2062
- F2131
