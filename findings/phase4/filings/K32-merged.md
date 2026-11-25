---
id: K32
title: "query-optimization skill: 'before you ship a query' rules (projection, $match first, bounded results, allowDiskUse, anchored regex) and an explain('executionStats') verification template"
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
open_questions: 7
---

# query-optimization skill: "before you ship a query" rules and an explain('executionStats') verification template

This PR edits `skills/query-optimization/` (main change) and, because the verification template needs somewhere to report to, `skills/monitoring/` plus two housekeeping files.

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

## Why it matters

We had a coding agent (gpt-5-mini with this kit and the DocumentDB MCP server) build 100 Azure DocumentDB sample apps, then an auditor scored each app against documented practices. All counts below are from a single experiment run (latest run per sample) and are indicative only [needs SME confirmation: see Open question 7]. Together the two patterns affected about **45 distinct samples**; this union is an estimate, because the member drafts give only per-pattern totals and a topic match over the audit findings puts the overlap at roughly 12 samples.

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

Several audit findings described cost in request units (RU) or asked for RU/s or request-charge logging. That is Cosmos DB vocabulary; Azure DocumentDB capacity is vCore tiers. The new text describes cost as I/O, memory, network and latency, and says explicitly that there is no request-unit or request-charge model.

## Proposed change (file by file)

### `skills/query-optimization/SKILL.md`

1. Replace the frontmatter `description`:

```yaml
description: Query and aggregation-pipeline hygiene for Azure DocumentDB — projection by default, $match first, bounded results and pagination, allowDiskUse on heavy pipelines, index-friendly matching, and explain("executionStats") verification shipped with the app (templates/explain_queries.py|js). Use when WRITING any find/findOne/aggregate call, list endpoint, cursor loop or change-stream consumer, and when reviewing or diagnosing a slow query. For index-design workflow, see documentdb-query-optimizer.
```

2. Add after the title paragraph:

```markdown
## Before you ship a query (checklist)

1. **Project.** Every `find`/`findOne`/`$lookup` names the fields it needs (`projection: {...}`, Mongoose `.select('a b').lean()`). Never hand a whole document to an LLM prompt or an HTTP response.
2. **$match first.** Selective `$match` (and `$project`) before `$sort`, `$group`, `$lookup`, `$addFields`, `$bucket`, `$facet`.
3. **Group on the server.** No `find().sort().toArray()` followed by grouping, scoring or filtering in application code; write the pipeline.
4. **Bound the result.** `$limit`/`.limit()` or iterate the cursor with `batchSize`; never `toArray()` / `to_list()` / `list(cursor)` on an unbounded filter.
5. **Paginate every list endpoint** with `limit` + indexed `sort` + a range-anchored `next_token`; do not use `skip` for deep pages.
6. **`allowDiskUse: true`** on any pipeline with `$group`, `$sort` on an unindexed key, `$bucket` or `$facet` over more than a few thousand documents.
7. **Match on indexed shapes.** Anchored `^prefix` regex, a normalized field with equality, or a search index created with `createSearchIndexes` + `$search`; never unanchored case-insensitive `$regex`.
8. **Ship the plan check.** Copy `templates/explain_queries.py` (or `.js`) to `scripts/`, list the hot operations, and run it with `--strict` after seeding and after every index change.
```

3. Replace `## Rules` with:

```markdown
- [query-project-fields](query-project-fields.md) — Always project; Mongoose `.select().lean()`; exclude embeddings and sensitive fields from prompts and responses.
- [query-match-first](query-match-first.md) — `$match`/`$project` before `$sort`/`$group`/`$lookup`/`$addFields`; `$lookup` with a `pipeline` + `$project`; group on the server.
- [query-bounded-results](query-bounded-results.md) — `$limit`, cursor + `batchSize`, range-anchored `next_token`, no `skip` for deep pages, bounded change-stream consumers.
- [query-allow-disk-use](query-allow-disk-use.md) — `allowDiskUse: true` on heavy `$group`/`$sort`/`$facet` pipelines.
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
index name, and exits non-zero with `--strict` on COLLSCAN, an in-memory SORT,
or totalDocsExamined/nReturned > 10.
For aggregate pipelines the explain output carries a `stages` array; check the
first stage for COLLSCAN vs IXSCAN to confirm the leading $match uses an index.
Run it after seeding and after every index change; add a README step
"Verify indexes: `python scripts/explain_queries.py --strict`" and, where there
is CI, run it against the local DocumentDB container.
Optional: honour `DOCUMENTDB_EXPLAIN=1` in the app to log the plan of each hot
query once at startup (never log filter values that contain customer data).
```

Add the reference https://learn.microsoft.com/azure/documentdb/how-to-read-explain-output next to the MongoDB link.

### `skills/query-optimization/query-project-fields.md` (new; kit template Why it matters / Incorrect / Correct / References; Priority HIGH)

- Why: a projection-less `find` returns every field (embeddings of 1536+ floats, large text, audit arrays, PII); cost is paid on the server, the wire and driver deserialization, then the document lands in a prompt or response. [needs SME confirmation] On the PostgreSQL-based engine wide rows are detoasted on read and projection is applied after detoast (as `model-large-field-split.md` already states). Treat a projection-less `find` as a code-review finding.
- Incorrect: `segments.findOne({ segmentId })` then `JSON.stringify(seg)` into a prompt; `coll.find_one({"_id": id})`; `Account.find(filter).cursor()`.
- Correct: `findOne({ segmentId }, { projection: { _id: 0, name: 1, preferences: 1 } })`; `find_one({"_id": id}, projection={"current_state": 1})`; `Account.find(filter).select('balance interestRate').lean().batchSize(500).cursor()`; in pipelines, `$project` or `$unset: ["embedding"]` right after the first `$match`, and `$lookup` with `pipeline: [{ $match }, { $project }]`.
- References: https://learn.microsoft.com/en-us/documentdb/query/commands/query-and-write/find (section "Projections") and `documentdb-data-modeling` → `model-large-field-split.md`.

### `skills/query-optimization/query-match-first.md` (new)

- Incorrect: `find().sort().toArray()` + JS grouping (`04-customer-journey-mapper`); a `$sort → $group → $replaceRoot → $match` coverage pipeline (`06-collateral-management-store`).
- Correct: `aggregate([{ $match: { customerId } }, { $project: { timestamp: 1, channel: 1, eventType: 1 } }, { $sort: { timestamp: 1 } }, { $group: { _id: '$channel', events: { $push: '$$ROOT' } } }], { allowDiskUse: true })`; the eligibility `$match` moved before `$group`.
- Cross-link `model-denormalize-reads.md` for precomputing grouping keys (e.g. `maturity_bucket`) at write time instead of `$addFields` at query time.
- Close with "confirm with `explain('executionStats')` that the leading `$match` is an IXSCAN" and link `query-explain-plan.md`.

### `skills/query-optimization/query-bounded-results.md` (new)

- Incorrect: `find_all().to_list()` list endpoints, `list(coll.aggregate(p))`, `.skip(skip).limit(limit)`, a change-stream handler that awaits work per event with no concurrency bound.
- Correct: `find(filter, { projection }).sort({ strike: 1, _id: 1 }).limit(limit + 1)` returning `{ items, next_token }` and resuming with `{ $or: [{ strike: { $gt: s } }, { strike: s, _id: { $gt: id } }] }`; `for await (const doc of cursor.batchSize(500))` / `find(..., batch_size=500)`; `$limit` in every CLI/demo pipeline; a semaphore (e.g. `p-limit(8)`) around the change-stream handler, projecting the handler's own reads, with a note that `fullDocument: 'updateLookup'` multiplies the payload [needs SME confirmation: support and limits on Azure DocumentDB].

### `skills/query-optimization/query-allow-disk-use.md` (new)

- Incorrect: `aggregate(pipeline)` with `$group` over a whole collection.
- Correct: `aggregate(pipeline, { allowDiskUse: true })` / `aggregate(p, allowDiskUse=True)`.
- Rule: set it on any pipeline whose `$group`/`$sort`/`$facet` input is not bounded by an indexed `$match` + `$limit`; it does not make a bad pipeline fast [needs SME confirmation: whether it changes engine behavior, see Open question 2].
- Reference: https://learn.microsoft.com/en-us/documentdb/query/commands/aggregation/aggregate.

### `skills/query-optimization/query-anchored-regex.md` (new)

- Incorrect: `vendorName: { $regex: new RegExp(vendor, 'i') }` (unanchored, case-insensitive: full scan), in the same app as an anchored `^` regex elsewhere.
- Correct: store and index a normalized field (`vendorNormalized`, lower/trim) and match by equality; or an anchored `^` prefix on an indexed field; or a search index created with `createSearchIndexes` (not `createIndex` with a `"text"`/`"textSearch"` key; see `fts-create-search-index.md`) plus `$search` (link `fts-basic-search.md`).
- Verify with the explain template: the regex query must not report COLLSCAN.

### `skills/query-optimization/templates/explain_queries.py` (new)

A pymongo script that reads the URI from `DOCUMENTDB_URI` (never printed), runs `db.command({"explain": cmd, "verbosity": "executionStats"})` for each entry in an editable `OPERATIONS` list of find/sort and aggregate operations, recursively walks the output (aggregate explain nests plans under `stages`) collecting every `stage`, `indexName`, `nReturned`, `totalKeysExamined`, `totalDocsExamined` and `executionTimeMillis`, prints one line per operation, and exits 1 under `--strict` (ratio overridable with `--ratio`) on COLLSCAN, SORT or a docs/returned ratio above the threshold. The full script is in source draft 100 and is pasted into this PR unchanged. The default `OPERATIONS` examples should use projected, `$match`-first, `$limit`-bounded queries so the template also demonstrates the checklist.

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
- Capacity is the vCore tier, not request units; watch cluster metrics (CpuPercent, MemoryPercent, StoragePercent, IOPS, connections) in Azure Monitor instead of computing "RU consumption".
- App-side timings matter most on M30-and-lower and free tiers, where diagnostic logs are unavailable.
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

Replace `DocumentDBSlowQueries_CL` and its `DocsExamined` / `QueryShape` columns with `VCoreMongoRequests` (`DurationMs`, `OperationName`, `ErrorCode`); say there is no separate slow-query toggle (filter `vCoreMongoRequests` on duration, then confirm with explain); state the M30-and-lower / free-tier limit; link https://learn.microsoft.com/azure/documentdb/how-to-monitor-diagnostics-logs instead of the landing page.

### `docs/SKILLS.md`

Query-optimization row: "projection by default, `$match` first, bounded results / pagination, `allowDiskUse`, anchored regex, `explain("executionStats")` with a shippable `scripts/explain_queries` template". Monitoring row: add "app-side instrumentation and README observability checklist".

### `CHANGELOG.md`

One entry covering the five new query rules, the explain template, the two new monitoring rules and the two monitoring fixes.

### Across all new text

Write cost and benefit in I/O, memory, network and latency terms; do not use "RU". Do not claim anything about throttling errors 16500 / HTTP 429 (see Open question 6).

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

## Open questions

1. [needs SME confirmation] The `query-project-fields.md` rationale says wide rows are detoasted on read by the PostgreSQL-based engine and that projection is applied after detoast (as `model-large-field-split.md` already states). Is that accurate for current releases, and is it worth stating in a user-facing rule?
2. [needs SME confirmation] `allowDiskUse` is a documented `aggregate` option. Does it change behavior on Azure DocumentDB (spill to disk, memory limits per tier), or is it accepted but a no-op? The rule text should match what the engine does.
3. [needs SME confirmation] Is change-stream `fullDocument: 'updateLookup'` supported on all tiers, and does the bounded-consumer guidance need DocumentDB-specific change-stream limits?
4. [needs SME confirmation] Does the template's walker match real Azure DocumentDB explain output for find, aggregate (`stages` array) and a cosmosSearch vector pipeline, including the stage names it flags (COLLSCAN, SORT)?
5. [needs SME confirmation] Confirm the monitoring facts used: diagnostic logs unavailable on M30-and-lower and free tiers, the `vCoreMongoRequests` category / `VCoreMongoRequests` table and columns, and metric names `CpuPercent`, `MemoryPercent`, `StoragePercent`, `IOPS`. These were checked against Learn but should be confirmed before the rules ship.
6. [needs SME confirmation] Should the rules say anything about throttling errors? The review flagged the claim that error 16500 / HTTP 429 "is not returned" as unconfirmed, so this PR only states there is no request-unit or request-charge model and makes no claim about 429/16500. Engineering answer requested before adding either position.
7. [needs SME confirmation] All counts come from one run: 31 samples for query hygiene (54 under a looser match), 26 for missing verification/observability, and an estimated union of about 45. Which number, if any, should appear in public text?

Follow-up outside this repo (not part of this PR): the experiment harness should list `scripts/explain_queries.*` and the README checklist as required deliverables and stop asking for RU/request-charge logging. That repository belongs to a colleague; coordinate that filing with them.

## Source drafts

- 098-query-hygiene-missing-from-generated-code-no-projections-lat.md
- 100-samples-never-verify-plans-or-expose-operations-no-explain-e.md

## Merged from

- K32: query-optimization skill: add "before you ship a query" rules (projection, $match first, bounded results and pagination, allowDiskUse, anchored regex)
- K33: query-optimization: add an explain('executionStats') verification template and observability rules
