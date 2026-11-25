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
open_questions: 4
---

# Small reference gaps on Azure DocumentDB Learn pages: transaction limits not linked from the transactions how-to, no TTL-index section, no `$setWindowFields` stage page

This feedback comes from an experiment in which a coding agent built 100 small Azure DocumentDB sample apps using Microsoft Learn as its reference. Three independent gaps came up. In each case the fact exists or the feature works, but the agent could not find a page that says so. Each fix is a few paragraphs on an existing page or one new reference page. Pages were checked on 2026-11-25.

## What happens today

**A. Transaction limits.** `azure/documentdb/limitations.md` states "Maximum transaction lifetime: 30 seconds" under *MongoDB execution limitations*. The transactions how-to (`azure/documentdb/how-to-transactions.md`, ms.date 2023-08-28, updated 2026-11-18) does not mention this limit or link to the limitations page. On retries it says only that the `withTransaction()` callback "can run more than once if the driver retries the transaction". That sentence presumes the `TransientTransactionError` label, which the service does not send: a write conflict comes back as code 112 `WriteConflict` with an empty label list (engine issue documentdb/documentdb#339, reproduced against the managed service), so `withTransaction()` surfaces the error instead of retrying. The Java and Python tabs use `startTransaction()`/`commitTransaction()` and show no retry handling. No Learn page lists which commands are refused inside a transaction (code 263 `OperationNotSupportedInTransaction` appears in the troubleshooting table without a command list).

**B. TTL indexes.** `azure/documentdb/indexing.md` covers single-field, compound, partial, text, wildcard and geospatial indexes, but not TTL. Neither page mentions `expireAfterSeconds`; the compatibility page only lists the TTL index property as supported, and the only Learn statement about TTL behaviour is a release-note line (2025-10-10). A Learn search for "TTL expireAfterSeconds documentdb" returns the Azure Cosmos DB for MongoDB (RU) page `azure/cosmos-db/mongodb/time-to-live` as the first article result. That page teaches an index on the `_ts` system field and a per-document `ttl` property. Neither applies to Azure DocumentDB.

**C. `$setWindowFields`.** The DocumentDB MQL reference has 11 window-operator pages. The `$sum`, `$max` and other accumulator pages include "Using X in `$setWindowFields`" examples. However, `documentdb/query/operators/aggregation/$setwindowfields` returns 404. The `$sum` and `$max` examples use only whole-partition windows (`["unbounded","unbounded"]`). Cumulative windows appear only on `$stdDevPop`, `$covariancePop`, `$covarianceSamp`, `$integral` and `$push`. No page shows a time-ordered running sum or running maximum, or two chained `$setWindowFields` stages.

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
- "A transaction must complete within 30 seconds of starting; after that the server aborts it and later statements in it fail. See [Service limits](limitations#mongodb-execution-limitations)." The 30-second limit applies to single-shard and sharded clusters alike. State that transactions span logical and physical shards (as the partitioning page already says). State that no count or size cap per transaction is documented beyond the 30-second lifetime, the 16 MB document limit and the 25,000-writes-per-request batch cap, or document the cap if one exists (see open questions). Do not name the error code a client gets at expiry until it is confirmed (see open questions).
- State which commands are refused inside a transaction with code 263 `OperationNotSupportedInTransaction`: DDL and admin commands such as `createIndexes`, `createSearchIndexes`, `dropIndexes`, `reIndex`, `drop`, `renameCollection`, `listCollections`, `currentOp` and `killOp`, plus data operations on the `admin`, `config` and `local` databases and on `system.*` collections. Describe the categories rather than an exact list, because the gateway build Azure runs is not published. Also state that `readConcern` cannot be set after the transaction has started (`InvalidOptions`).
- Replace the sentence "The callback can run more than once if the driver retries the transaction". Azure DocumentDB returns `WriteConflict` (112, "Could not acquire lock within transaction") and `NoSuchTransaction` (251) without the `TransientTransactionError` or `UnknownTransactionCommitResult` error labels (engine issue documentdb/documentdb#339; the gateway's error reply carries only `ok`, `code`, `codeName` and `errmsg`), so `withTransaction()` does not retry them. Show an application-level loop that re-runs the whole transaction on code 112 or 251 with bounded attempts and backoff, and advise keeping transactions short: few documents, and no network calls inside the callback. Note that drivers attach `UnknownTransactionCommitResult` themselves for network errors during `commitTransaction`, so a dropped connection at commit may still be retried by the driver; that behaviour was not verified against the service.
- Explain why `retrywrites=false` is required, with the de-duplication reason, so readers do not expect driver-level retries to cover transactional or single-document writes. Suggested text: "Keep `retrywrites=false` in every Azure DocumentDB connection string. The service does not support retryable writes: the server does not de-duplicate a retried write, so a driver retry can apply a non-idempotent write twice. Handle transient write failures in application code with idempotent operations (upserts, deterministic keys)." Link this from the limitations page as well.
- Say plainly that `withTransaction()` does not retry Azure DocumentDB server errors, so the explicit retry loop is needed with `withTransaction()` as well as with `startTransaction()`/`commitTransaction()`.

**A. `limitations.md`.** Give transactions their own `### Transactions` heading so that search finds it, and link it back to the how-to.

**A. `troubleshoot-common-issues.md`.** Add rows for 112 `WriteConflict` and 251 `NoSuchTransaction` to the error-code table, say which command categories trigger 263, and state that none of these errors carries MongoDB's transient-error labels.

**B. `indexing.md`.** Add a `## TTL indexes` section, with a TOC or in-page entry, containing the following:
- Azure DocumentDB supports standard MongoDB TTL indexes: a single-field index on a BSON Date field, plus a numeric `expireAfterSeconds`.
- Two examples: `db.sessions.createIndex({ createdAt: 1 }, { expireAfterSeconds: 3600 })`, and `db.beds.createIndex({ cleaningExpiresAt: 1 }, { expireAfterSeconds: 0 })` for expiry at a stored time.
- The rules: TTL indexes cannot be compound (the engine rejects them with "TTL indexes work only on single fields, and compound indexes are incompatible with TTL functionality"). Documents whose field is missing or not a Date never expire, because the purge is a `$lt` comparison against a Date value. A `partialFilterExpression` on the index also restricts which documents the purge deletes. Deletion runs in the background: the TTL task runs every minute and performs batch deletions continuously for up to 60 seconds (release note 2025-10-10, marked preview), so expiry lags by up to about a minute and is not exact. Link the release note from this section, since today it is the only Learn statement of TTL behaviour.
- A note: "Azure Cosmos DB for MongoDB (RU) implements TTL with the `_ts` field and a per-document `ttl` property. These don't apply to Azure DocumentDB."

**B. `azure/cosmos-db/mongodb/time-to-live.md`.** Add one sentence to the existing "Important" note: "Azure DocumentDB uses standard MongoDB TTL indexes on any Date field, not `_ts` or a per-document `ttl` property. See [TTL indexes](../../documentdb/indexing#ttl-indexes)."

**C. New page `documentdb/query/operators/aggregation/$setwindowfields.md`.** Link it from the window-operator index and the aggregation-stage index. It should cover:
- the syntax and the `partitionBy`, `sortBy`, `output` and `window` parameters (`documents` and `range` bounds);
- the operators supported in `output`;
- when `sortBy` is required: for every `documents` window except `["unbounded","unbounded"]` (error "Missing sortBy field for document-based window"), for every `range` window, which needs exactly one ascending `sortBy` field (errors "Expected a single sort by field for range-based window", "Expected ascending sortBy field definition"), and for `$derivative`, `$integral`, `$shift`, `$expMovingAvg`, `$linearFill`, `$locf`, `$rank`, `$denseRank` and `$documentNumber`; an output with no window and no `sortBy` is allowed;
- cost guidance for large partitions: the default query execution limit is 120 seconds, overridable per query with `maxTimeMS` (limitations page), and pre-aggregating with `$group` + `$dateTrunc` reduces partition size;
- one worked example. Suggested example (each component is documented or was observed working individually; the combined pipeline has not been run on a cluster, see open questions):

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

Optionally, cross-link the existing cumulative examples on `$stdDevPop`, `$covariancePop` and `$push`.

## Evidence

- `runs/07-multi-currency-ledger/20261124-190814/02-readiness.json` and `05-audit.json` (transaction lifetime and retry gap)
- `runs/05-shopping-cart-with-real-time-inventory/20261124-183232/events.jsonl` (transaction-limit searches)
- `runs/12-hospital-bed-occupancy-tracker/20261124-194835/events.jsonl` and `app/src/ttl_check.js` (TTL searches that returned the RU page; a document with a Date 5 s in the future was still present after 30 s of polling, consistent with a purge lag of up to about a minute)
- `runs/13-algorithmic-trade-journal/20261124-191835/05-audit.json` and `app/app/aggregations.py` (client-side drawdown)
- `runs/09-crypto-wallet-activity-analyzer/20261124-191004/doc-gaps.md` (server-side z-score gap)
- `runs/07-lab-results-aggregator/20261124-194018/events.jsonl` (`$setWindowFields` with `partitionBy`, `sortBy` and a bounded `documents` window on `$avg` returned 9 rows against the cluster)

## Resolved

- retryWrites: answered 2026-11-25, see findings/phase4/DECISIONS.md. Retryable writes are not supported; retrywrites=false is required; the server does not de-duplicate retried writes (documentdb/documentdb#767).
- Transaction error labels and retry pattern: the gateway never emits `TransientTransactionError` or `UnknownTransactionCommitResult`; `WriteConflict` (112) and `NoSuchTransaction` (251) arrive unlabelled, so `withTransaction()` does not retry them and the application must re-run the whole transaction with bounded attempts and backoff. Sources: https://github.com/documentdb/documentdb/issues/339 (reproduced on the managed service), #428, #698 and #836; gateway `responses/error.rs:64-71` at commit a5f1636; MongoDB convenient-transactions spec (findings/phase4/DECISIONS.md, topics 2 and 9).
- Transaction scope and refused commands: transactions span logical and physical shards (https://learn.microsoft.com/en-us/azure/documentdb/partitioning, updated 2026-08-25); the 30-second lifetime applies without a shard qualifier (https://learn.microsoft.com/en-us/azure/documentdb/limitations, updated 2026-11-17; gateway `dynamic.rs:26`); DDL and admin commands and data operations on admin/config/local and system.* are refused with code 263 (gateway `request_type.rs:470-484`, `validation.rs:41-92`, main branch; the exact list differs between main and release/1.0-RC2, so filings describe categories). Source: findings/phase4/DECISIONS.md, topic 9.
- TTL semantics: single-field only ("TTL indexes work only on single fields...", `create_indexes.c:2793`); `expireAfterSeconds` must be numeric (`:2297`); the purge is a `$lt` against a Date value, so non-Date and missing fields are not deleted (inference from `ttl_index.c:640-756`); `partialFilterExpression` is applied to the purge; the task runs every minute (pg_cron `* * * * *`) with batch deletion continuously for up to 60 seconds (https://learn.microsoft.com/en-us/azure/documentdb/release-notes, 2025-10-10), so "about 60 seconds, not exact" is the right wording. Source: findings/phase4/DECISIONS.md, topic 10.
- `$setWindowFields` component support: the stage, the `$sum`/`$max`/`$last` window operators, `$last` in `$group` and bounded `documents` windows are each documented or observed working (https://learn.microsoft.com/en-us/azure/documentdb/compatibility-query-language, updated 2026-06-13; release notes 2024-08-05, 2024-09-16, 2024-10-14; engine regression tests `bson_aggregation_pipeline_tests_sumavg_group.out`; run `07-lab-results-aggregator/20261124-194018`). Source: findings/phase4/DECISIONS.md, topic 10.
- `sortBy` requirement: required for every `documents` window except both-unbounded and for every `range` window (exactly one ascending field), plus operator-specific rules; an output with no window and no `sortBy` is allowed. Source: `bson_aggregation_window_operators.c:508-548` and related lines; https://learn.microsoft.com/en-us/azure/documentdb/operators/window-operators/$rank (findings/phase4/DECISIONS.md, topic 10).
- Default query execution limit: 120 seconds, overridable per query with `maxTimeMS`. Source: https://learn.microsoft.com/en-us/azure/documentdb/limitations (ms.date 2026-11-04, updated 2026-11-17) (findings/phase4/DECISIONS.md, topic 10).

## Open questions

1. [needs SME confirmation] Are there numeric limits on operations, documents or bytes per transaction beyond the 30-second lifetime, and what error (code 251 `NoSuchTransaction` or something else) does a client receive when a transaction exceeds 30 seconds on Azure? The limitations page lists only the lifetime, the how-to lists no limits, and the engine exposes no per-transaction count or size setting; no run hit the timeout.
2. [needs SME confirmation] Does the exact example above (two chained `$setWindowFields` stages with a cumulative `documents: ["unbounded","current"]` window on `$sum` and `$max`, followed by `$group` with `$last`) run as written on the managed service? Each component is documented or observed, but no run executed the combined pipeline and no cited regression test covers a cumulative `$max`.
3. [needs SME confirmation] Actual TTL purge cadence on managed clusters: the every-minute schedule with up-to-60-second continuous batches is the open-source default and the release note marks the continuous behaviour as preview; service-side settings are not published, and the one observation (no delete within 30 s of a 5 s expiry) does not bound the lag.
4. The sample counts come from one run and keyword searches, and repeating the search gave slightly different sets. Recount before quoting the numbers externally.

## Source drafts

- 048-misc-small-reference-gaps-on-learn-transaction-limits-table-.md
