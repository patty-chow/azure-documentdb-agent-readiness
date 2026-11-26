---
id: K32
title: "query-optimization skill: 'before you ship a query' rules (projection, $match first, bounded results, per-tier memory bounds instead of allowDiskUse, anchored regex) and an explain('executionStats') verification template"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P1
sample_count: 45
member_drafts:
  - 098-query-hygiene-missing-from-generated-code-no-projections-lat.md
  - 100-samples-never-verify-plans-or-expose-operations-no-explain-e.md
merged_from:
  - K32
  - K33
open_questions: 2
---

# query-optimization skill: "before you ship a query" rules and an explain('executionStats') verification template

This PR edits `skills/query-optimization/` (main change) and, because the verification template needs somewhere to report to, `skills/monitoring/` plus two housekeeping files. It also corrects two kit files that deny the existence of a COLLSCAN stage (`scripts/perf-advisor.sh`, `testing/scenarios/ecommerce-missing-index/SCENARIO.md`).

## What happens today

The kit gives a code-generating agent index-design and `explain()` advice, but nothing about how much data a query returns and nothing the agent can copy into an app to prove a query uses its index.

**Query hygiene is not where code-writing agents look (from K32):**
- `skills/query-optimization/SKILL.md` has one rule, `query-explain-plan.md`. Its description limits it to reviewing a query, diagnosing a slow one, or checking index use.
- `skills/query-optimizer/SKILL.md` (line 8) says not to invoke it for "general query writing".
- The only general statements ("project only needed fields", "`$match` as early as possible", "`$limit` after `$sort`", "prefer left-anchored `/^prefix/`") are in `skills/natural-language-querying/SKILL.md` lines 276-295. That skill is for ad-hoc MCP querying and loaded in 12 of 221 build runs. The skills agents did load while writing app code (`driver` 108 runs, `indexing` 99, `data-modeling` 91) say nothing on projection or result size.
- Nothing in `skills/` or `knowledge-base/` covers `allowDiskUse`, `batchSize`, range-based pagination versus `skip`, or bounded change-stream consumers. `docs/SKILLS.md` line 22 describes query-optimization as `explain("executionStats")` and avoiding `COLLSCAN` only.

Typical generated code:

```js
const timeline = await coll.find({ customerId }).sort({ timestamp: 1 }).toArray(); // no projection, no limit, grouped in JS
PurchaseOrder.find({ vendorName: { $regex: new RegExp(vendor, 'i') }, ... })      // unanchored, case-insensitive
const cursor = Account.find(filter).cursor();                                      // no .select(), .lean(), .batchSize()
```
```py
docs = await Supplier.find_all().to_list(); return [d.dict() for d in docs]        # unbounded list endpoint
```

**Plan verification and observability are never shipped (from K33):**
- `skills/query-optimization/query-explain-plan.md` ends with "Automate in CI with a small harness that asserts `totalDocsExamined / nReturned < threshold` for critical queries", but the kit ships no such harness and no `templates/` folder.
- `skills/monitoring/` covers only cluster-side setup (diagnostic settings, a Kusto query, a Bicep alert sketch). It says nothing about what the application should emit and gives agents no README text to drop into a sample.
- Two existing monitoring details are wrong: the Bicep sketch uses `cpu_percent` instead of `CpuPercent`, and the slow-query rule uses a placeholder `DocumentDBSlowQueries_CL` table instead of `VCoreMongoRequests`.
- The kit links the MongoDB explain page but not the Azure DocumentDB pages on explain output and diagnostic logs.
- Three kit statements about explain output are wrong: `scripts/perf-advisor.sh` (lines 406-407) and `testing/scenarios/ecommerce-missing-index/SCENARIO.md` (line 21) say DocumentDB "never emits a literal COLLSCAN stage" and falls back to an `_id_` IXSCAN, and `query-explain-plan.md` (lines 23, 28) tells readers to detect scatter-gather from a `shards[]` array. Learn (`how-to-read-explain-output`, `how-to-index`) documents a COLLSCAN stage, this experiment observed `winningPlan.stage: 'COLLSCAN'` for both find and aggregate explains on the managed service (the managed test of 2026-11-25 showed that both forms occur: COLLSCAN once autovacuum has run, `FETCH` over a bitmap `IXSCAN` on `_id_` before it, so "never" is wrong but the `_id_` form is real), and no Learn page documents a `shards[]` field (the documented cross-shard view is the `allShardsQueryPlan` / `allShardsExecution` explain modes).

## Why it matters

We had a coding agent (gpt-5-mini with this kit and the DocumentDB MCP server) build 100 Azure DocumentDB sample apps, then an auditor scored each app against documented practices. All counts below are from a single experiment run (latest run per sample) and are indicative only [needs SME confirmation: see Open question 2]. Together the two patterns affected about **45 distinct samples**; this union is an estimate, because the member drafts give only per-pattern totals and a topic match over the audit findings puts the overlap at roughly 12 samples.

- **Query hygiene: 31 samples** (46 audit findings, each rated "violated"; a looser search across all audits finds at least one related violation in 54 samples). The agent put whole documents, including embeddings and PII fields, into LLM prompts (`08-personalized-email-campaign-builder`, `14-loan-origination-workflow-orchestration`, `19-proactive-outreach-orchestration`); returned unbounded collections from public list endpoints (`15-supplier-po-management`, `19-option-chain-data-store`, `20-store-locator-with-geospatial-search`); grouped and scored in application code instead of in a pipeline; and used unanchored case-insensitive regex. In one sample the agent searched for pagination guidance, found nothing it could cite, and shipped an unbounded endpoint.
- **No plan verification or observability: 26 samples** (35 violated checks), all sourced to `documentdb-monitoring`, `documentdb-query-optimization` or `documentdb-query-optimizer`. Across all 100:

  | Signal | Samples |
  |---|---|
  | Code contains an `explain(...)` call | 2 |
  | Emits OpenTelemetry / Prometheus / App Insights metrics | 0 |
  | README mentions diagnostic settings, Log Analytics or slow-operation analysis | 1 |
  | Agent called `documentdb_explain_operation` via MCP during the build | 11 |

  The agent does check plans interactively, then ships nothing: in one run it called `documentdb_explain_operation` four times on the main aggregation and delivered an app with no explain step, metrics or monitoring notes.

The two gaps compound. A sample that fetches whole documents with no limit also never shows a plan, so developers who clone it learn "create an index and hope it is used"; an ESR compound or cosmosSearch vector index the planner skips stays invisible until production. Agents copy template files and checklists far more reliably than they build a harness from a one-line hint.

Several audit findings described cost in request units (RU) or asked for RU/s or request-charge logging. That is Cosmos DB vocabulary; Azure DocumentDB capacity is vCore tiers. The new text describes cost as I/O, memory, network and latency, and says explicitly that there is no request-unit or request-charge model and no throttling error code: Azure DocumentDB never returns 16500 / HTTP 429 (RU-based Cosmos DB for MongoDB codes; the open-source engine has no such code in any error-mapping file and no rate-limiting path in the gateway, the Learn troubleshooting table lists no throttling code, and no agent received one across the runs). Resource pressure shows up as latency and timeouts instead: the default query execution limit is 120 seconds, overridable per query with `maxTimeMS`, and a cancelled query surfaces as code 50 ExceededTimeLimit (confirmed on the managed service; `maxTimeMS` limits only the command that carries it, so a `getMore` is not limited unless it carries its own).

## Proposed change (file by file)

### `skills/query-optimization/SKILL.md`

1. Replace the frontmatter `description`:

```yaml
description: Query and aggregation-pipeline hygiene for Azure DocumentDB — projection by default, $match first, bounded results and pagination, per-tier memory bounds (allowDiskUse is accepted and ignored), index-friendly matching, and explain("executionStats") verification shipped with the app (templates/explain_queries.py|js). Use when WRITING any find/findOne/aggregate call, list endpoint, cursor loop or change-stream consumer, and when reviewing or diagnosing a slow query. For index-design workflow, see documentdb-query-optimizer.
```

2. Add after the title paragraph:

```markdown
## Before you ship a query (checklist)

1. **Project.** Every `find`/`findOne`/`$lookup` names the fields it needs (`projection: {...}`, Mongoose `.select('a b').lean()`). Never hand a whole document to an LLM prompt or an HTTP response.
2. **$match first.** Selective `$match` (and `$project`) before `$sort`, `$group`, `$lookup`, `$addFields`, `$bucket`, `$facet`.
3. **Group on the server.** No `find().sort().toArray()` followed by grouping, scoring or filtering in application code; write the pipeline.
4. **Bound the result.** `$limit`/`.limit()` or iterate the cursor with `batchSize`; never `toArray()` / `to_list()` / `list(cursor)` on an unbounded filter.
5. **Paginate every list endpoint** with `limit` + indexed `sort` + a range-anchored `next_token`; do not use `skip` for deep pages.
6. **Bound pipeline memory, not `allowDiskUse`.** Azure DocumentDB accepts and ignores `allowDiskUse`; query memory is capped per tier (about 150 MiB on M80) and sorting is done in memory, so put an indexed `$match` (and a `$limit` where possible) in front of every `$group`, `$sort` on an unindexed key, `$bucket` or `$facet`.
7. **Match on indexed shapes.** Anchored `^prefix` regex, a normalized field with equality, or a search index created with `createSearchIndexes` + `$search`; never unanchored case-insensitive `$regex`.
8. **Ship the plan check.** Copy `templates/explain_queries.py` (or `.js`) to `scripts/`, list the hot operations, and run it with `--strict` after seeding and after every index change.
```

3. Replace `## Rules` with:

```markdown
- [query-project-fields](query-project-fields.md) — Always project; Mongoose `.select().lean()`; exclude embeddings and sensitive fields from prompts and responses.
- [query-match-first](query-match-first.md) — `$match`/`$project` before `$sort`/`$group`/`$lookup`/`$addFields`; `$lookup` with a `pipeline` + `$project`; group on the server.
- [query-bounded-results](query-bounded-results.md) — `$limit`, cursor + `batchSize`, range-anchored `next_token`, no `skip` for deep pages, bounded change-stream consumers.
- [query-allow-disk-use](query-allow-disk-use.md) — `allowDiskUse` is accepted and ignored on Azure DocumentDB; query memory is bounded per tier and sorts run in memory, so bound the input of heavy `$group`/`$sort`/`$facet` pipelines with an indexed `$match` + `$limit`.
- [query-anchored-regex](query-anchored-regex.md) — Unanchored `/x/i` forces a `COLLSCAN`; use `^prefix`, a normalized indexed field, or `$search`.
- [query-explain-plan](query-explain-plan.md) — Verify with `explain("executionStats")` and ship `scripts/explain_queries.*` with the app (template in `templates/`).
```

### `skills/query-optimization/query-explain-plan.md`

Replace the closing "Automate in CI..." sentence with:

```markdown
## Ship the check with the app

Do not leave explain() in your MCP session. Every sample or service must include
`scripts/explain_queries.{py,js}` (copy from `templates/`), listing its hot
find/aggregate operations. The script prints, per operation: the plan stages,
totalKeysExamined, totalDocsExamined, nReturned, executionTimeMillis and the
index name, and exits non-zero with `--strict` on a full scan: a COLLSCAN, an
IXSCAN on `_id_` for a filter that is not on `_id`, or a stage that examined more
than 10 documents per document it returned. Compare `totalDocsExamined` with
`nReturned` on the FETCH or COLLSCAN stage that reports both, not on the top-level
totals (a `LIMIT` root can report 1 document examined over a scan that examined
12,346) or on a bitmap IXSCAN leaf, which reports keys only. A SORT stage is
reported as a warning (on this
service sorting is done in memory and does not push down to the index, so bound the
sorted input with an indexed $match + $limit rather than expecting the stage to vanish).
For aggregate pipelines the explain output carries a `stages` array and the plan sits
at `stages[0].$cursor.queryPlanner.winningPlan`; check that first stage's leaf scan
(an IXSCAN on the intended index, not a COLLSCAN or an IXSCAN on `_id_`) to confirm
the leading $match uses an index. Find explains use the
DocumentDB-specific layout (explainVersion 2, `winningPlan.stage`, `indexName`,
`runtimeFilterSet`, `indexFilterSet`, `isBitmap`, `estimatedTotalKeysExamined`).
Send the `explain` command with `verbosity: "executionStats"`: PyMongo's
`Cursor.explain()` sends no verbosity, and the service then answers at
`queryPlanner` level with no executionStats. No plan check right after a bulk load
is reliable: until autovacuum has run (the delay after a load varied in testing
and was not controlled), an unindexed find can explain as FETCH over a bitmap
IXSCAN on `_id_`, an indexed `find_one` as `LIMIT` over a COLLSCAN, and an indexed
query as an IXSCAN with 1 document examined while its `allPlansExecution` explain
shows a full scan, so do not time queries right after a load.
Run it after seeding (after a bulk load, trust the result only once
`collectionPlannerStatistics.allVisibleFraction` in a `queryPlanner` explain reads
1.0; it reads 0.0 until autovacuum has run) and after
every index change; add a README step
"Verify indexes: `python scripts/explain_queries.py --strict`" and, where there
is CI, run it against the local DocumentDB container.
Optional: honour `DOCUMENTDB_EXPLAIN=1` in the app to log the plan of each hot
query once at startup (never log filter values that contain customer data).
```

Add the references https://learn.microsoft.com/azure/documentdb/how-to-read-explain-output and https://learn.microsoft.com/azure/documentdb/how-to-index (the page that shows the explainVersion 2 find layout) next to the MongoDB link.

Also fix lines 23 and 28: remove the advice to read a `shards[]` array to detect scatter-gather. No Learn page documents such a field for Azure DocumentDB; the documented cross-shard view is the `allShardsQueryPlan` / `allShardsExecution` explain modes (release notes 2024-03-03), so point readers there instead.

### `skills/query-optimization/query-project-fields.md` (new; kit template Why it matters / Incorrect / Correct / References; Priority HIGH)

- Why: a projection-less `find` returns every field (embeddings of 1536+ floats, large text, audit arrays, PII); cost is paid on the wire and in driver deserialization, then the document lands in a prompt or response. Say plainly that a projection reduces what is sent over the wire and deserialized, not what the server reads from storage: the engine stores each document as one `bson` column and detoasts the whole document before any filter or projection function sees it (`DatumGetPgBson` in `pg_documentdb_core/include/io/pgbson.h`; engine issue #695 traces `$ne` cost on large rows to UNTOAST), which is what `model-large-field-split.md` already describes. Whether to name the PostgreSQL detail in a user-facing rule is a maintainer choice; the rule itself uses the wire-versus-storage phrasing and cites the two engine sources. Treat a projection-less `find` as a code-review finding.
- Incorrect: `segments.findOne({ segmentId })` then `JSON.stringify(seg)` into a prompt; `coll.find_one({"_id": id})`; `Account.find(filter).cursor()`.
- Correct: `findOne({ segmentId }, { projection: { _id: 0, name: 1, preferences: 1 } })`; `find_one({"_id": id}, projection={"current_state": 1})`; `Account.find(filter).select('balance interestRate').lean().batchSize(500).cursor()`; in pipelines, `$project` or `$unset: ["embedding"]` right after the first `$match`, and `$lookup` with `pipeline: [{ $match }, { $project }]`.
- References: https://learn.microsoft.com/en-us/documentdb/query/commands/query-and-write/find (section "Projections") and `documentdb-data-modeling` → `model-large-field-split.md`.

### `skills/query-optimization/query-match-first.md` (new)

- Incorrect: `find().sort().toArray()` + JS grouping (`04-customer-journey-mapper`); a `$sort → $group → $replaceRoot → $match` coverage pipeline (`06-collateral-management-store`).
- Correct: `aggregate([{ $match: { customerId } }, { $project: { timestamp: 1, channel: 1, eventType: 1 } }, { $sort: { timestamp: 1 } }, { $group: { _id: '$channel', events: { $push: '$$ROOT' } } }])`; the eligibility `$match` moved before `$group`. (No `allowDiskUse`: the service ignores it; see `query-allow-disk-use.md`.)
- Cross-link `model-denormalize-reads.md` for precomputing grouping keys (e.g. `maturity_bucket`) at write time instead of `$addFields` at query time.
- Close with "confirm with `explain('executionStats')` that the leading `$match` is an IXSCAN on the intended index" and link `query-explain-plan.md`.

### `skills/query-optimization/query-bounded-results.md` (new)

- Incorrect: `find_all().to_list()` list endpoints, `list(coll.aggregate(p))`, `.skip(skip).limit(limit)`, a change-stream handler that awaits work per event with no concurrency bound.
- Correct: `find(filter, { projection }).sort({ strike: 1, _id: 1 }).limit(limit + 1)` returning `{ items, next_token }` and resuming with `{ $or: [{ strike: { $gt: s } }, { strike: s, _id: { $gt: id } }] }`; `for await (const doc of cursor.batchSize(500))` / `find(..., batch_size=500)`; `$limit` in every CLI/demo pipeline; a semaphore (e.g. `p-limit(8)`) around the change-stream handler, projecting the handler's own reads, with a note that change events carry whole documents: on the service every insert and update event carries `fullDocument`, with or without `updateLookup` (managed test, 2026-11-25), so drop fields the handler does not need with a `$project` stage in the watch pipeline. `updateLookup` is listed as a supported `fullDocument` option on the `$changeStream` operator page and no tier restriction is documented (the limitations and free-tier pages have no change-stream entry); run `07-lab-results-aggregator/20261124-194018` opened `watch(full_document='updateLookup')` on an M30 cluster and received an insert event, and the managed test (M30) saw `updateLookup` accepted, with events identical to those without it. DocumentDB-specific change-stream facts (400 MB active change log, historical replay up to 35 days via PITR, multishard change streams and `updateDescription` in preview with their enablement steps) belong to the change-streams skill proposed in K04; this rule cross-links it rather than restating them.

### `skills/query-optimization/query-allow-disk-use.md` (new)

- Why: Azure DocumentDB accepts `allowDiskUse` and ignores it. The engine lists the option in `IgnoredCommonSpecFields` ("command options that are not currently supported. At runtime, we ignore these optional fields", `pg_documentdb/src/commands/commands_common.c` lines 51-62), and run `02-ai-powered-product-recommendations/20261124-181835` ran `aggregate(pipeline, { allowDiskUse: true })` without error. Memory is governed by the tier instead: the limitations page says the query memory limit depends on the tier (about 150 MiB on M80) and that sorting is done in memory and does not push down to the index.
- Incorrect: `aggregate(pipeline, { allowDiskUse: true })` with `$group` or `$sort` over a whole collection, expecting the option to spill to disk.
- Correct: `aggregate([{ $match: <indexed filter> }, { $project: {...} }, { $limit: n }, { $group: ... }])` — bound the input with an indexed `$match` (and `$limit` where the result allows) so the pipeline stays within the tier's memory; the option may stay in code copied from MongoDB but must not be relied on.
- References: https://learn.microsoft.com/en-us/azure/documentdb/limitations (Maximum MongoDB query size; General indexing limitations); https://github.com/documentdb/documentdb/blob/main/pg_documentdb/src/commands/commands_common.c (lines 51-70); https://learn.microsoft.com/en-us/documentdb/query/commands/aggregation/aggregate (lists the option without saying it is ignored).

### `skills/query-optimization/query-anchored-regex.md` (new)

- Incorrect: `vendorName: { $regex: new RegExp(vendor, 'i') }` (unanchored, case-insensitive: full scan), in the same app as an anchored `^` regex elsewhere.
- Correct: store and index a normalized field (`vendorNormalized`, lower/trim) and match by equality; or an anchored `^` prefix on an indexed field; or a search index created with `createSearchIndexes` (not `createIndex` with a `"text"`/`"textSearch"` key; see `fts-create-search-index.md`) plus `$search` (link `fts-basic-search.md`).
- Verify with the explain template: the regex query must not report a full scan (see `query-explain-plan.md`).

### `skills/query-optimization/templates/explain_queries.py` (new)

A pymongo script that reads the URI from `DOCUMENTDB_URI` (never printed), runs `db.command({"explain": cmd, "verbosity": "executionStats"})` for each entry in an editable `OPERATIONS` list of find/sort and aggregate operations, recursively walks the output (aggregate explain nests the plan under `stages[].$cursor.queryPlanner.winningPlan`; find explain uses `queryPlanner.winningPlan` with explainVersion 2) collecting every `stage`, `indexName`, `nReturned`, `totalKeysExamined`, `totalDocsExamined` and `executionTimeMillis`, prints one line per operation, warns on a SORT stage, and exits 1 under `--strict` (ratio overridable with `--ratio`) on a full scan: a COLLSCAN, an IXSCAN on `_id_` for a filter that is not on `_id`, or a docs/returned ratio above the threshold on a `FETCH` or `COLLSCAN` stage that reports both counts. This walk matches the real layout for find and aggregate explains on the managed service (Learn `how-to-read-explain-output` lists the stage names COLLSCAN, IXSCAN, FETCH, SORT, COUNT_SCAN, COUNT, GROUP, LIMIT, DISTINCT_SCAN, DISTINCT_UNWIND, UNIQUE, PARALLEL_MERGE; runs `01-anti-money-laundering-pattern-detector/20261124-200112` and `12-cross-border-payment-audit-trail/20261124-201744` returned `winningPlan.stage: 'COLLSCAN'` for a find and an aggregate respectively). A full scan reported without a COLLSCAN stage, as `FETCH` over a bitmap `IXSCAN` on `_id_`, is caught by the `_id_` check and by the ratio read at that `FETCH`, not at the leaf (the bitmap `IXSCAN` reports keys only, with `nReturned` equal to the collection size): the engine tests in `findings/phase4/ENGINE-TESTS.md` saw that plan on the local container and, before autovacuum had run, on the managed service (2026-11-25). They also saw a `LIMIT` root report 1 document examined over a scan of 12,346, which is why the ratio is read on the `FETCH` or `COLLSCAN` stage that reports both, not from the top-level totals. On the managed service a `$search` cosmosSearch pipeline on IVF explains as `FETCH` (with `cosmosSearchCustomParams`) over `IXSCAN` on the vector index, then `LIMIT` and `PROJECT`, with no SORT or COLLSCAN (see Resolved), so the walker recognises it; it should still report an operation that yields no recognised stage name as "no plan stage recognised" rather than fail. The full script is in source draft 100, but it needs changes before it is pasted into this PR, because as drafted it does not do what this paragraph says: its walker keeps the first `nReturned` and `totalDocsExamined` it meets (the top-level totals), collects `indexName` from `queryPlanner.indexCosts` as well as from the plan (on the service `indexCosts` listed `_id_` even for queries that used `i_1`), and fails `--strict` on any SORT. Compare the counts on the `FETCH` or `COLLSCAN` stage that reports both, take the `_id_` check from the winning plan's IXSCAN only, and keep SORT a warning. The default `OPERATIONS` examples should use projected, `$match`-first, `$limit`-bounded queries so the template also demonstrates the checklist.

### `skills/query-optimization/templates/explain_queries.js` (new)

Same shape as the Python script, using the Node driver. Both templates are tested in `testing/` against the local container the kit already uses.

### `skills/monitoring/SKILL.md`

Add two rules:

```markdown
- [monitoring-app-instrumentation](monitoring-app-instrumentation.md) — Emit app-side counters/latency (OpenTelemetry) for writes, retries, duplicate keys, embedding failures and slow operations; Azure DocumentDB has no request-unit or request-charge model.
- [monitoring-readme-checklist](monitoring-readme-checklist.md) — Every sample README carries an "Observability / Production checklist" section (metrics to watch, diagnostic settings to Log Analytics, slow-operation query, one alert).
```

### `skills/monitoring/monitoring-app-instrumentation.md` (new; Why / Incorrect / Correct / References)

- OpenTelemetry (to Azure Monitor via `azure-monitor-opentelemetry` / `@azure/monitor-opentelemetry`, or Prometheus): `db_write_total{op,outcome}`, `db_write_retries_total`, `db_duplicate_key_total`, a `db_op_duration_ms` histogram per hot operation, `embedding_failures_total`, `slow_op_total` (e.g. 500 ms) with a correlation id.
- Incorrect: `print("done")` progress output and reading a `requestCharge` field. Correct: a short Python snippet with these counters around `insert_many` and the main aggregation.
- Capacity is the vCore tier, not request units; watch cluster metrics (CpuPercent, MemoryPercent, StoragePercent, IOPS, connections) in Azure Monitor instead of computing "RU consumption". There is no throttling error to count: Azure DocumentDB never returns 16500 / 429 (RU-based Cosmos DB for MongoDB codes absent from the engine's error mappings and from the Learn troubleshooting table), so do not instrument a "throttled" counter; count timeouts (code 50 ExceededTimeLimit, default query limit 120 s, per-query `maxTimeMS`) and latency instead.
- App-side timings matter most on M30-and-lower and free tiers, where diagnostic logs are unavailable (how-to-monitor-diagnostics-logs: "not available with compute tier M30 or lower tiers, or free-tier SKUs") and the platform `MongoRequestDurationMs` metric ("Mongo request duration") needs M40 or higher (monitor-metrics).
- Never log connection strings, credentials or raw customer filter values.

### `skills/monitoring/monitoring-readme-checklist.md` (new)

The section agents paste into READMEs:

```markdown
## Observability / Production checklist

- **Metrics**: platform metrics are collected automatically. In Azure Monitor for the
  `Microsoft.DocumentDB/mongoClusters` resource watch CpuPercent, MemoryPercent,
  StoragePercent and IOPS per node, plus connection counts (thresholds in
  `documentdb-monitoring`). There is no request-unit / request-charge metric on this service.
- **Diagnostic logs** (M40 and above; not available on M30 or lower or free tier): create a
  diagnostic setting that routes the `vCoreMongoRequests` category to Log Analytics —
  `az monitor diagnostic-settings create --name ddb-diag --resource <cluster-resource-id>
  --workspace <log-analytics-id> --logs '[{"category":"vCoreMongoRequests","enabled":true}]'`.
  Find slow operations by querying the `VCoreMongoRequests` table on `DurationMs`
  (for example P99 by `OperationName`). The table holds full command text, so restrict workspace access.
- **Verify plans**: `python scripts/explain_queries.py --strict` after seeding and after any index change.
- **Alert**: at least one metric alert (CpuPercent > 75 for 10 min) routed to your on-call channel; see
  `monitoring-metrics-alerts` for a Bicep sketch.
```

### `skills/monitoring/monitoring-metrics-alerts.md` (fix)

`metricName: 'cpu_percent'` → `'CpuPercent'`, and use `MemoryPercent`, `StoragePercent` and `IOPS` for any further alerts. Add the M30-and-lower caveat only where it applies (diagnostic logs, not platform metrics).

### `skills/monitoring/monitoring-slow-query-log.md` (fix)

Replace `DocumentDBSlowQueries_CL` and its `DocsExamined` / `Namespace` / `QueryShape` columns with the resource-specific `VCoreMongoRequests` table (`DurationMs`, `OperationName`, `DatabaseName`, `CollectionName`, `ErrorCode`, `PiiCommandText`, `ClientIp`, `UserAgent`, `TimeGenerated`; Azure Monitor tables reference, ms.date 2026-07-27); remove step 2's "Enable slow-query / operation logs" toggle, which does not exist (the only diagnostic category is `vCoreMongoRequests`; filter on `DurationMs`, then confirm with explain); state that diagnostic logs are not available on M30 or lower or free tiers (how-to-monitor-diagnostics-logs Important box; note that the limitations page's free-tier bullet says only "available only in paid tiers", an inconsistency recorded in Open question 1, and use the stricter M40-and-above wording); note that the KQL assumes a Log Analytics workspace with resource-specific logs (the supported-logs reference lists only `AzureDiagnostics`); link https://learn.microsoft.com/azure/documentdb/how-to-monitor-diagnostics-logs instead of the landing page.

### `scripts/perf-advisor.sh` (fix, lines 406-407) and `testing/scenarios/ecommerce-missing-index/SCENARIO.md` (fix, line 21)

Both state that "DocumentDB (Postgres-backed) never emits a literal COLLSCAN stage" and falls back to a full IXSCAN over `_id_`. Learn `how-to-index` and `how-to-read-explain-output` document a COLLSCAN stage, and this experiment observed `winningPlan.stage: 'COLLSCAN'` for a find explain (`01-anti-money-laundering-pattern-detector/20261124-200112`) and an aggregate explain (`12-cross-border-payment-audit-trail/20261124-201744`, at `stages[0].$cursor.queryPlanner.winningPlan`) on the managed service. Rewrite both to treat COLLSCAN and an `_id_` IXSCAN on a non-`_id` filter as the same full-scan signal, on the managed service as on the local container, because whether `COLLSCAN` shows depends on the collection's vacuum state and the explain verbosity. On documentdb-local 0.117 an unindexed predicate over 200,000 documents produced no COLLSCAN but `FETCH` with a runtime filter over a bitmap `IXSCAN` on `_id_` with all 200,000 documents examined, and the managed test of 2026-11-25 saw the same `_id_` form on the service just after a 50,000-document load (at the default, `queryPlanner` and `executionStats` verbosities) and a root `COLLSCAN` once autovacuum had run (`findings/phase4/ENGINE-TESTS.md`). Documents examined versus `nReturned`, read on the `FETCH` or `COLLSCAN` stage that reports both, is a better signal than top-level `totalDocsExamined`, which a `LIMIT` root understates; but no plan check is reliable right after a bulk load, when an indexed find's `executionStats` explain showed IXSCAN with 1 document examined while its `allPlansExecution` explain and latency indicated a full scan.

### `docs/SKILLS.md`

Query-optimization row: "projection by default, `$match` first, bounded results / pagination, per-tier memory bounds (`allowDiskUse` is ignored), anchored regex, `explain("executionStats")` with a shippable `scripts/explain_queries` template". Monitoring row: add "app-side instrumentation and README observability checklist".

### `CHANGELOG.md`

One entry covering the five new query rules, the explain template, the two new monitoring rules, the two monitoring fixes and the COLLSCAN / `shards[]` corrections.

### Across all new text

Write cost and benefit in I/O, memory, network and latency terms; do not use "RU". Where retry or error handling comes up, say that Azure DocumentDB returns no throttling code (16500 / HTTP 429 are RU-based Cosmos DB for MongoDB codes the engine does not have) and that the signals to watch are latency and code 50 ExceededTimeLimit timeouts; do not quote 16500 / 429 as something to retry on. Do not state that `allowDiskUse` changes engine behaviour.

Out of scope: bulk-write findings (per-document inserts/updates in loops) belong to a separate write-path change.

## Evidence

Run folders from the experiment (each has `05-audit.json` and the generated `app/`):

- `runs/04-customer-journey-mapper/20261124-203553/` (`app/src/aggregationTool.js`: find + sort + toArray, grouped in JS)
- `runs/12-invoice-matching-reconciliation/20261124-191603/` (`app/src/reconciler.js`)
- `runs/19-option-chain-data-store/20261124-192712/` (`doc-gaps.md` records pagination as prior knowledge only; `app/app/main.py`)
- `runs/15-supplier-po-management/20261124-184929/` (`app/app/main.py`: unbounded list endpoint)
- `runs/19-proactive-outreach-orchestration/20261124-205844/` (`app/src/listener.js`: unbounded change-stream consumer)
- `runs/20-interest-accrual-batch-processor/20261124-202826/` (both patterns: `app/src/worker.js` cursor without projection; audit asks for a `--profile` explain flag)
- `runs/09-crypto-wallet-activity-analyzer/20261124-191004/events.jsonl` (four interactive explain calls, nothing shipped)
- `runs/12-abandoned-cart-recovery-orchestration/20261124-184507/05-audit.json` (two violated explain/slow-query checks; `events.jsonl` shows list-indexes, no explain)
- `runs/08-regulatory-compliance-rag-checker/20261124-190949/05-audit.json` (auditor proposes `scripts/explain_queries.py`)
- `runs/03-core-banking-transaction-ledger/20261124-200452/05-audit.json` (asks for commit/failure, duplicate-key and retry counters)
- `runs/01-anti-money-laundering-pattern-detector/20261125-064030/app/src/db.py` and `runs/retail-semantic-search/20261122-152144/app/scripts/verify-live.js` (the two samples that shipped plan verification)

## Resolved

- Detoast rationale in `query-project-fields.md` (former Q1): accurate as an engine description, so the rule says a projection reduces what is sent over the wire and deserialized, not what the server reads from storage, and whether to name the PostgreSQL detail is a maintainer choice. Sources: DECISIONS.md topic 10 (engine_source); `pg_documentdb_core/include/io/pgbson.h` (`DatumGetPgBson` -> `PG_DETOAST_DATUM`); engine issue documentdb/documentdb#695.
- `allowDiskUse` on Azure DocumentDB (former Q2): a no-op, accepted and ignored (`IgnoredCommonSpecFields` in `pg_documentdb/src/commands/commands_common.c` lines 51-62; observed accepted in run `02-ai-powered-product-recommendations/20261124-181835`), with query memory capped per tier (about 150 MiB on M80) and sorting done in memory, so the rule now says bound the input instead of setting the option. Sources: DECISIONS.md topic 10 (engine_source); https://learn.microsoft.com/en-us/azure/documentdb/limitations; https://learn.microsoft.com/en-us/documentdb/query/commands/aggregation/aggregate.
- `fullDocument: 'updateLookup'` tier support (former Q3): no tier restriction is documented anywhere and the option is listed as supported (`$changeStream` operator page Parameters table and Example 1; limitations and free-tier pages have no change-stream entry); observed working on an M30 cluster in run `07-lab-results-aggregator/20261124-194018`, and the managed test of 2026-11-25 (M30) saw it accepted, with update events carrying `fullDocument` as of the update with or without it (ENGINE-TESTS.md, Managed service); DocumentDB-specific change-stream limits exist (400 MB active log, 35-day historical replay, multishard and `updateDescription` in preview) and belong to the K04 change-streams skill, which this rule cross-links. Sources: DECISIONS.md topic 8 (documented); https://learn.microsoft.com/en-us/documentdb/query/operators/aggregation/$changestream; https://learn.microsoft.com/en-us/azure/documentdb/change-streams.
- Template walker versus real explain output for find and aggregate (former Q4, first part): matches, provided the walker descends into `stages[].$cursor` for aggregate explains; Learn lists COLLSCAN, IXSCAN, FETCH, SORT and the other stage names, and the managed service returned `winningPlan.stage: 'COLLSCAN'` for a find (`01-anti-money-laundering-pattern-detector/20261124-200112`) and an aggregate (`12-cross-border-payment-audit-trail/20261124-201744`). Qualified by the managed test of 2026-11-25: whether COLLSCAN appears depends on the collection's vacuum state and the explain verbosity, and neither it nor top-level `totalDocsExamined` is a reliable full-scan check, so the template compares documents examined with `nReturned` on the `FETCH` or `COLLSCAN` stage that reports both and takes the index name from the winning plan; PyMongo's `Cursor.explain()` returns no executionStats on the service, which is why the template sends the explain command. The vector-pipeline part is answered below. Sources: DECISIONS.md topic 10 (documented and managed test); https://learn.microsoft.com/en-us/azure/documentdb/how-to-read-explain-output; https://learn.microsoft.com/en-us/azure/documentdb/how-to-index.
- Monitoring facts (former Q5): confirmed; diagnostic category `vCoreMongoRequests`, resource-specific table `VCoreMongoRequests` (columns include `DurationMs`, `OperationName`, `DatabaseName`, `CollectionName`, `ErrorCode`, `PiiCommandText`), no separate slow-query toggle, and REST metric names `CpuPercent`, `MemoryPercent`, `StoragePercent`, `IOPS` (plus `MongoRequestDurationMs`, M40 or higher); diagnostic logs unavailable on M30 or lower and free tiers per the how-to, with the limitations page's looser wording left as Open question 1. Sources: DECISIONS.md topic 10 (documented); https://learn.microsoft.com/en-us/azure/documentdb/how-to-monitor-diagnostics-logs; https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/vcoremongorequests; https://learn.microsoft.com/en-us/azure/azure-monitor/reference/supported-logs/microsoft-documentdb-mongoclusters-logs; https://learn.microsoft.com/en-us/azure/azure-monitor/reference/supported-metrics/microsoft-documentdb-mongoclusters-metrics; https://learn.microsoft.com/en-us/azure/documentdb/monitor-metrics.
- Throttling errors 16500 / HTTP 429 (former Q6): Azure DocumentDB does not return them; they are request-unit errors of the RU-based Cosmos DB for MongoDB, absent from every engine error-mapping file and from the Learn troubleshooting table, with no rate-limiting path in the gateway and none observed across the runs, so the rules state this and point to latency and code 50 ExceededTimeLimit (120 s default, `maxTimeMS`) as the resource-pressure signals. Sources: DECISIONS.md topic 2 (engine_source); https://learn.microsoft.com/en-us/azure/documentdb/troubleshoot-common-issues; https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/error-codes-solutions; https://learn.microsoft.com/en-us/azure/documentdb/limitations; github.com/documentdb/documentdb @ a5f1636 (`error_mappings.csv`, `documentdb_errors.csv`, `pg_documentdb_gw/include/all_error_mappings_oss_generated.csv`).
- Explain layout of a cosmosSearch pipeline (former Open question 1): answered by the managed test of 2026-11-25. `stages[0].$cursor.queryPlanner.winningPlan` is `FETCH` with `cosmosSearchCustomParams` (`{nProbes: 2}` on IVF) over `IXSCAN` on the vector index, then `LIMIT` and `PROJECT`, with no `SORT` or `COLLSCAN`, the same layout documentdb-local 0.117 showed, so the template's walk finds an IXSCAN and flags nothing. Sources: ENGINE-TESTS.md, Managed service; DECISIONS.md topic 10, item 3.

## Open questions

1. [needs SME confirmation] Is the diagnostic-log gate "M30 and lower lack it" (how-to-monitor-diagnostics-logs Important box) or "free tier only lacks it" (limitations page free-tier bullet, "available only in paid tiers", updated 2026-11-17)? The two current Learn pages disagree; this PR uses the how-to's stricter M40-and-above wording and flags the limitations-page sentence.
2. [needs SME confirmation] All counts come from one run: 31 samples for query hygiene (54 under a looser match), 26 for missing verification/observability, and an estimated union of about 45. Which number, if any, should appear in public text?

Follow-up outside this repo (not part of this PR): the experiment harness should list `scripts/explain_queries.*` and the README checklist as required deliverables and stop asking for RU/request-charge logging or for 429 / RequestRateTooLarge handling (audit rubric H07 propagates that RU-era advice; 63-64 of the audits list it). That repository belongs to a colleague; coordinate that filing with them.

## Source drafts

- 098-query-hygiene-missing-from-generated-code-no-projections-lat.md
- 100-samples-never-verify-plans-or-expose-operations-no-explain-e.md

## Merged from

- K32: query-optimization skill: add "before you ship a query" rules (projection, $match first, bounded results and pagination, allowDiskUse, anchored regex)
- K33: query-optimization: add an explain('executionStats') verification template and observability rules
