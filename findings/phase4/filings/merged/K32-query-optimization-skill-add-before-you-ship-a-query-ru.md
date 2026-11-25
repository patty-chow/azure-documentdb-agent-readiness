---
id: K32
title: "query-optimization skill: add 'before you ship a query' rules (projection, $match first, bounded results and pagination, allowDiskUse, anchored regex)"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P1
sample_count: 31
member_drafts:
  - 098-query-hygiene-missing-from-generated-code-no-projections-lat.md
open_questions: 4
---

# query-optimization skill: add "before you ship a query" rules

## What happens today

The kit gives a code-generating agent index design and `explain()` advice, but no rule about how much data a query returns.

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

## Why it matters

We ran an experiment in which an AI agent built 100 sample apps on Azure DocumentDB with this kit installed, and an auditor scored each app against documented practices. 46 audit findings across **31 of the 100 samples** were this pattern, each rated "violated" (a looser search across all audits finds at least one related violation in 54 samples). Counts come from a single experiment run and should be treated as indicative [needs SME confirmation: see Open question 4].

What the agent did wrong: put whole documents, including embeddings and PII fields, into LLM prompts (`08-personalized-email-campaign-builder`, `14-loan-origination-workflow-orchestration`, `19-proactive-outreach-orchestration`); returned unbounded collections from public list endpoints (`15-supplier-po-management`, `19-option-chain-data-store`, `20-store-locator-with-geospatial-search`); grouped and scored in application code instead of in a pipeline; used unanchored case-insensitive regex. In one sample the agent searched for pagination guidance, found nothing it could cite, and shipped an unbounded endpoint.

Some audit findings described the cost in request units (RU). Azure DocumentDB capacity is vCore tiers, not RUs, so the new text describes cost as I/O, memory, network and latency.

## Proposed change (all under `skills/query-optimization/` unless noted)

### 1. `SKILL.md`

Replace the frontmatter `description`:

```yaml
description: Query and aggregation-pipeline hygiene for Azure DocumentDB — projection by default, $match first, bounded results and pagination, allowDiskUse on heavy pipelines, index-friendly matching, and explain("executionStats") verification. Use when WRITING any find/findOne/aggregate call, list endpoint, cursor loop or change-stream consumer, and when reviewing or diagnosing a slow query. For index-design workflow, see documentdb-query-optimizer.
```

Add after the title paragraph:

```markdown
## Before you ship a query (checklist)

1. **Project.** Every `find`/`findOne`/`$lookup` names the fields it needs (`projection: {...}`, Mongoose `.select('a b').lean()`). Never hand a whole document to an LLM prompt or an HTTP response.
2. **$match first.** Selective `$match` (and `$project`) before `$sort`, `$group`, `$lookup`, `$addFields`, `$bucket`, `$facet`.
3. **Group on the server.** No `find().sort().toArray()` followed by grouping, scoring or filtering in application code; write the pipeline.
4. **Bound the result.** `$limit`/`.limit()` or iterate the cursor with `batchSize`; never `toArray()` / `to_list()` / `list(cursor)` on an unbounded filter.
5. **Paginate every list endpoint** with `limit` + indexed `sort` + a range-anchored `next_token`; do not use `skip` for deep pages.
6. **`allowDiskUse: true`** on any pipeline with `$group`, `$sort` on an unindexed key, `$bucket` or `$facet` over more than a few thousand documents.
7. **Match on indexed shapes.** Anchored `^prefix` regex, a normalized field with equality, or a search index created with `createSearchIndexes` + `$search`; never unanchored case-insensitive `$regex`.
```

Replace `## Rules` with:

```markdown
- [query-project-fields](query-project-fields.md) — Always project; Mongoose `.select().lean()`; exclude embeddings and sensitive fields from prompts and responses.
- [query-match-first](query-match-first.md) — `$match`/`$project` before `$sort`/`$group`/`$lookup`/`$addFields`; `$lookup` with a `pipeline` + `$project`; group on the server.
- [query-bounded-results](query-bounded-results.md) — `$limit`, cursor + `batchSize`, range-anchored `next_token`, no `skip` for deep pages, bounded change-stream consumers.
- [query-allow-disk-use](query-allow-disk-use.md) — `allowDiskUse: true` on heavy `$group`/`$sort`/`$facet` pipelines.
- [query-anchored-regex](query-anchored-regex.md) — Unanchored `/x/i` forces a `COLLSCAN`; use `^prefix`, a normalized indexed field, or `$search`.
- [query-explain-plan](query-explain-plan.md) — (unchanged)
```

### 2. Five new rule files (kit template: Why it matters / Incorrect / Correct / References)

- **`query-project-fields.md`** (Priority HIGH). Why: a projection-less `find` returns every field (embeddings of 1536+ floats, large text, audit arrays, PII); cost is paid on the server, the wire and driver deserialization, then the document lands in a prompt or response. [needs SME confirmation] On the PostgreSQL-based engine wide rows are detoasted on read and projection is applied after detoast (as `model-large-field-split.md` already states). Treat a projection-less `find` as a code-review finding. Incorrect: `segments.findOne({ segmentId })` then `JSON.stringify(seg)` into a prompt; `coll.find_one({"_id": id})`; `Account.find(filter).cursor()`. Correct: `findOne({ segmentId }, { projection: { _id: 0, name: 1, preferences: 1 } })`; `find_one({"_id": id}, projection={"current_state": 1})`; `Account.find(filter).select('balance interestRate').lean().batchSize(500).cursor()`; in pipelines, `$project` or `$unset: ["embedding"]` right after the first `$match`, and `$lookup` with `pipeline: [{ $match }, { $project }]`. References: https://learn.microsoft.com/en-us/documentdb/query/commands/query-and-write/find (section "Projections") and `documentdb-data-modeling` → `model-large-field-split.md`.
- **`query-match-first.md`**. Incorrect: `find().sort().toArray()` + JS grouping (`04-customer-journey-mapper`); a `$sort → $group → $replaceRoot → $match` coverage pipeline (`06-collateral-management-store`). Correct: `aggregate([{ $match: { customerId } }, { $project: { timestamp: 1, channel: 1, eventType: 1 } }, { $sort: { timestamp: 1 } }, { $group: { _id: '$channel', events: { $push: '$$ROOT' } } }], { allowDiskUse: true })`, eligibility `$match` moved before `$group`. Cross-link `model-denormalize-reads.md` for precomputing grouping keys (e.g. `maturity_bucket`) at write time instead of `$addFields` at query time.
- **`query-bounded-results.md`**. Incorrect: `find_all().to_list()` list endpoints, `list(coll.aggregate(p))`, `.skip(skip).limit(limit)`, a change-stream handler that awaits work per event with no concurrency bound. Correct: `find(filter, { projection }).sort({ strike: 1, _id: 1 }).limit(limit + 1)` returning `{ items, next_token }` and resuming with `{ $or: [{ strike: { $gt: s } }, { strike: s, _id: { $gt: id } }] }`; `for await (const doc of cursor.batchSize(500))` / `find(..., batch_size=500)`; `$limit` in every CLI/demo pipeline; a semaphore (e.g. `p-limit(8)`) around the change-stream handler, projecting the handler's own reads, with a note that `fullDocument: 'updateLookup'` multiplies the payload [needs SME confirmation: support and limits on Azure DocumentDB].
- **`query-allow-disk-use.md`**. Incorrect: `aggregate(pipeline)` with `$group` over a whole collection. Correct: `aggregate(pipeline, { allowDiskUse: true })` / `aggregate(p, allowDiskUse=True)`. Rule: set it on any pipeline whose `$group`/`$sort`/`$facet` input is not bounded by an indexed `$match` + `$limit`; it does not make a bad pipeline fast [needs SME confirmation: whether it changes engine behavior, see Open question 2]. Reference: https://learn.microsoft.com/en-us/documentdb/query/commands/aggregation/aggregate.
- **`query-anchored-regex.md`**. Incorrect: `vendorName: { $regex: new RegExp(vendor, 'i') }` (unanchored, case-insensitive: full scan), in the same app as an anchored `^` regex elsewhere. Correct: store and index a normalized field (`vendorNormalized`, lower/trim) and match by equality; or an anchored `^` prefix on an indexed field; or a search index created with `createSearchIndexes` (not `createIndex` with a `"text"`/`"textSearch"` key; see `fts-create-search-index.md`) plus `$search` (link `fts-basic-search.md`).

### 3. Housekeeping

- `docs/SKILLS.md`, query-optimization row: "projection by default, `$match` first, bounded results / pagination, `allowDiskUse`, anchored regex, `explain("executionStats")`".
- `CHANGELOG.md` entry.
- Write cost/benefit in I/O, memory, network and latency terms; do not use "RU".

Out of scope: bulk-write findings (per-document inserts/updates in loops) and missing-`explain()` findings belong to separate write-path and explain-plan changes.

## Evidence

Run folders from the experiment (each has `05-audit.json` and the generated `app/`):

- `runs/04-customer-journey-mapper/20261124-203553/` (`app/src/aggregationTool.js`)
- `runs/12-invoice-matching-reconciliation/20261124-191603/` (`app/src/reconciler.js`)
- `runs/19-option-chain-data-store/20261124-192712/` (`doc-gaps.md`, `app/app/main.py`)
- `runs/20-interest-accrual-batch-processor/20261124-202826/` (`app/src/worker.js`)
- `runs/15-supplier-po-management/20261124-184929/` (`app/app/main.py`)
- `runs/19-proactive-outreach-orchestration/20261124-205844/` (`app/src/listener.js`)

## Open questions

1. [needs SME confirmation] The `query-project-fields.md` rationale says wide rows are detoasted on read by the PostgreSQL-based engine and that projection is applied after detoast (as `model-large-field-split.md` already states). Is that accurate for current releases, and is it worth stating in a user-facing rule?
2. [needs SME confirmation] `allowDiskUse` is a documented `aggregate` option. Does it change behavior on Azure DocumentDB (spill to disk, memory limits per tier), or is it accepted but a no-op? The rule text should match what the engine does.
3. [needs SME confirmation] Is change-stream `fullDocument: 'updateLookup'` supported on all tiers, and does the bounded-consumer guidance need DocumentDB-specific change-stream limits?
4. [needs SME confirmation] The 31-sample count comes from one run; a looser match gives 54. Which number, if any, should appear in public text?

## Source drafts

- 098-query-hygiene-missing-from-generated-code-no-projections-lat.md
