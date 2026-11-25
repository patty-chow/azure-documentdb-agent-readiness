---
id: L08
title: "Small reference gaps on Azure DocumentDB Learn pages: transaction limits not linked from the transactions how-to, no TTL-index section, no $setWindowFields stage page"
repo: learn-docs
type: learn-feedback
status: needs_sme
priority: P2
sample_count: 9
member_drafts:
  - 048-misc-small-reference-gaps-on-learn-transaction-limits-table-.md
open_questions: 6
---

# Small reference gaps on Azure DocumentDB Learn pages: transaction limits not linked from the transactions how-to, no TTL-index section, no `$setWindowFields` stage page

This feedback comes from an experiment in which a coding agent built 100 small Azure DocumentDB sample apps using Microsoft Learn as its reference. Three independent gaps came up. In each case the fact exists or the feature works, but the agent could not find a page that says so. Each fix is a few paragraphs on an existing page or one new reference page. Pages were checked on 2026-11-25.

## What happens today

**A. Transaction limits.** `azure/documentdb/limitations.md` states "Maximum transaction lifetime: 30 seconds" under *MongoDB execution limitations*. The transactions how-to (`azure/documentdb/how-to-transactions.md`, ms.date 2023-08-28) does not mention this limit or link to the limitations page. On retries it says only that the `withTransaction()` callback "can run more than once". The Java and Python tabs use `startTransaction()`/`commitTransaction()` and show no retry handling.

**B. TTL indexes.** `azure/documentdb/indexing.md` covers single-field, compound, partial, text, wildcard and geospatial indexes, but not TTL. Neither page mentions `expireAfterSeconds`. A Learn search for "TTL expireAfterSeconds documentdb" returns the Azure Cosmos DB for MongoDB (RU) page `azure/cosmos-db/mongodb/time-to-live` as the first article result. That page teaches an index on the `_ts` system field and a per-document `ttl` property. Neither applies to Azure DocumentDB.

**C. `$setWindowFields`.** The DocumentDB MQL reference has 11 window-operator pages. The `$sum`, `$max` and other accumulator pages include "Using X in `$setWindowFields`" examples. However, `documentdb/query/operators/aggregation/$setwindowfields` returns 404. The `$sum` and `$max` examples use only whole-partition windows (`["unbounded","unbounded"]`). Cumulative windows appear only on `$stdDevPop`, `$covariancePop`, `$covarianceSamp` and `$integral`. No page shows a time-ordered running sum or running maximum, or two chained `$setWindowFields` stages.

## Why it matters

Nine of the 100 samples ran into these gaps:
- six raised a transaction-limits gap;
- one raised the TTL gap;
- two raised the window-function gap.

Counts are from one experiment run and from keyword searches over its outputs, so treat them as approximate.

The cost was the same each time:
- One ledger sample found no authoritative statement of transaction limits and shipped transactional writes with no timeout or retry handling.
- The TTL sample got the index right by following another source. It still recorded a doc gap about `_ts` and wrote an extra script only to prove that TTL fires on an ordinary Date field.
- Two analytics samples could not find `$setWindowFields` guidance. They computed running totals, drawdown and z-scores client-side, which does not scale.

## Proposed change

**A. `how-to-transactions.md`.** Add a "Limits and retry behavior" section after *Roll back a transaction*:
- "A transaction must complete within 30 seconds of starting, or the server aborts it. See [Service limits](limitations#mongodb-execution-limitations)." List any other transaction limits, such as operations or documents per transaction, cross-shard behaviour or size. If the only limits are the lifetime and the 16 MB document limit, say so.
- Explain the retry pattern the engine supports for transactions (see the open questions), and advise keeping transactions short: few documents, and no network calls inside the callback.
- State whether `withTransaction()` handles retries for the user. If it does, say that an explicit loop is only needed with `startTransaction()`/`commitTransaction()`.

**A. `limitations.md`.** Give transactions their own `### Transactions` heading so that search finds it, and link it back to the how-to.

**B. `indexing.md`.** Add a `## TTL indexes` section, with a TOC or in-page entry, containing the following:
- Azure DocumentDB supports standard MongoDB TTL indexes: a single-field index on a BSON Date field, plus `expireAfterSeconds`.
- Two examples: `db.sessions.createIndex({ createdAt: 1 }, { expireAfterSeconds: 3600 })`, and `db.beds.createIndex({ cleaningExpiresAt: 1 }, { expireAfterSeconds: 0 })` for expiry at a stored time.
- The rules: TTL indexes cannot be compound. Documents whose field is missing or not a Date never expire. Deletion runs in the background and can lag.
- A note: "Azure Cosmos DB for MongoDB (RU) implements TTL with the `_ts` field and a per-document `ttl` property. These don't apply to Azure DocumentDB."

**B. `azure/cosmos-db/mongodb/time-to-live.md`.** Add one sentence to the existing "Important" note: "Azure DocumentDB uses standard MongoDB TTL indexes on any Date field, not `_ts` or a per-document `ttl` property. See [TTL indexes](../../documentdb/indexing#ttl-indexes)."

**C. New page `documentdb/query/operators/aggregation/$setwindowfields.md`.** Link it from the window-operator index and the aggregation-stage index. It should cover:
- the syntax and the `partitionBy`, `sortBy`, `output` and `window` parameters (`documents` and `range` bounds);
- the operators supported in `output`;
- when `sortBy` is required;
- cost guidance for large partitions (`maxTimeMS`, and pre-aggregating with `$group` + `$dateTrunc`);
- one worked example. Suggested example (not yet validated on a cluster):

```javascript
db.trades.aggregate([
  { $match: { strategyId: "momentum-1" } },
  { $setWindowFields: { partitionBy: "$strategyId", sortBy: { closedAt: 1 },
      output: { cumulativePnl: { $sum: "$pnl", window: { documents: ["unbounded", "current"] } } } } },
  // separate stage: an output can't reference another output of the same stage
  { $setWindowFields: { partitionBy: "$strategyId", sortBy: { closedAt: 1 },
      output: { runningPeak: { $max: "$cumulativePnl", window: { documents: ["unbounded", "current"] } } } } },
  { $set: { drawdown: { $subtract: ["$runningPeak", "$cumulativePnl"] } } },
  { $sort: { closedAt: 1 } },
  { $group: { _id: "$strategyId", maxDrawdown: { $max: "$drawdown" }, finalPnl: { $last: "$cumulativePnl" } } }
])
```

Optionally, cross-link the existing cumulative examples on `$stdDevPop` and `$covariancePop`.

## Evidence

- `runs/07-multi-currency-ledger/20261124-190814/02-readiness.json` and `05-audit.json` (transaction lifetime and retry gap)
- `runs/05-shopping-cart-with-real-time-inventory/20261124-183232/events.jsonl` (transaction-limit searches)
- `runs/12-hospital-bed-occupancy-tracker/20261124-194835/events.jsonl` and `app/src/ttl_check.js` (TTL searches that returned the RU page)
- `runs/13-algorithmic-trade-journal/20261124-191835/05-audit.json` and `app/app/aggregations.py` (client-side drawdown)
- `runs/09-crypto-wallet-activity-analyzer/20261124-191004/doc-gaps.md` (server-side z-score gap)

## Open questions

1. [needs SME confirmation] Are there transaction limits beyond the 30-second lifetime, such as operations or documents per transaction, total size, or cross-shard transactions?
2. [needs SME confirmation] Which retry behaviour should the transactions page recommend? Two things need an engineering answer before either is documented:
   - whether the engine returns the `TransientTransactionError` and `UnknownTransactionCommitResult` error labels that drivers use to retry a transaction or its commit;
   - how that interacts with retryable writes.

   Other filings from this experiment disagree on retryable writes. One position is that the recommended `retrywrites=false` setting is required and that retryable writes cause errors. The other is that Learn does not state that retryable writes are unsupported.
3. [needs SME confirmation] TTL semantics on Azure DocumentDB: is it limited to single-field indexes, are non-Date values ignored, how is a missing field handled, and how long can background deletion lag?
4. [needs SME confirmation] Does the suggested `$setWindowFields` example run as written on Azure DocumentDB? In particular, are chained stages, `$last` in `$group` and the cumulative `documents` window on `$sum` and `$max` supported?
5. [needs SME confirmation] Is `sortBy` required for every window other than `documents: ["unbounded","unbounded"]`? Is 120 seconds the default query execution limit that cost guidance should cite?
6. [needs SME confirmation] The sample counts come from one run and keyword searches, and repeating the search gave slightly different sets. Recount before quoting the numbers externally.

## Source drafts

- 048-misc-small-reference-gaps-on-learn-transaction-limits-table-.md
