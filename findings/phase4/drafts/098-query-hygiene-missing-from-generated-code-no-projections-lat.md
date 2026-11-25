---
title: "query-optimization skill: add \"before you ship a query\" rules (projection, $match-first, bounded results/pagination, allowDiskUse, anchored regex) so generated read paths stop fetching whole collections"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 31
findings: 46
bucket: sample-violated-practice
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# query-optimization: add "before you ship a query" rules so generated read paths stop fetching whole collections

## What happens today

`skills/query-optimization/SKILL.md` has one rule, `query-explain-plan.md`, and its description is scoped to *reviewing* or *diagnosing* a query. `skills/query-optimizer/SKILL.md` says "Do not invoke for general query writing". The only place the kit says "project only needed fields", "$match early", "$limit after $sort" is `natural-language-querying/SKILL.md` lines 276-295, which is an MCP ad-hoc-query skill and was loaded in 12 of 221 build runs. The skills a code-generating agent does load (`driver` 108 runs, `indexing` 99, `data-modeling` 91) say nothing about what a query returns or how much of it.

So an agent building an app with the kit gets index design and `explain()` advice but no rule about payload discipline, and emits code like this (real output from the runs):

```js
// 04-customer-journey-mapper/app/src/aggregationTool.js
const timeline = await coll.find({ customerId }).sort({ timestamp: 1 }).toArray();
const byChannel = {};                       // grouping done in JS, no projection, no limit
for (const ev of timeline) { ... }
```

```js
// 12-invoice-matching-reconciliation/app/src/reconciler.js
PurchaseOrder.find({ vendorName: { $regex: new RegExp(vendor, 'i') },   // unanchored, defeats the index
                     totalAmount: { $gte: minAmount, $lte: maxAmount } }).limit(10)   // full docs incl. lineItems, scored in JS
```

```py
# 19-option-chain-data-store/app/app/main.py  and  15-supplier-po-management/app/app/main.py
cursor = coll.find({...}).sort("strike", 1); results = [d for d in cursor]; return results   # no projection, no limit, no next_token
docs = await Supplier.find_all().to_list(); return [d.dict() for d in docs]
```

```js
// 20-interest-accrual-batch-processor/app/src/worker.js
const cursor = Account.find(filter).cursor();   // no .select(), no .lean(), no .batchSize()
```

## Why it matters

- 46 audit findings across **31 of the 100 samples** are exactly this pattern (a looser regex over all `05-audit.json` files puts at least one such violated check in 54 samples). Every one was rated "violated" against a practice the auditor attributed to this kit, i.e. the kit states the principle somewhere but the builder never saw a concrete "do this instead".
- The failure is not cosmetic: full documents (embeddings, `applicant.ssn_last4`, outreach logs) were stuffed into LLM prompts (`08-personalized-email-campaign-builder`, `14-loan-origination-workflow-orchestration`, `19-proactive-outreach-orchestration`) and returned from public list endpoints with no limit (`15-supplier-po-management`, `19-option-chain-data-store`, `20-store-locator-with-geospatial-search`).
- In `19-option-chain-data-store/doc-gaps.md` the agent recorded pagination guidance as `prior_knowledge_only` after searching and finding nothing it could cite; it shipped an unbounded endpoint.
- Several findings phrase the cost in "RU" terms. That is Cosmos DB RU-API vocabulary and does not apply to vCore clusters; the recommendation (project and paginate) stands. The new rule text should say "I/O, memory and network", not RU.

## Proposed change (all under `skills/query-optimization/`)

### 1. `SKILL.md`: widen the trigger and add a checklist

Replace the frontmatter `description` with:

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

Extend `## Rules` to:

```markdown
- [query-project-fields](query-project-fields.md) — Always project; Mongoose `.select().lean()`; exclude embeddings and sensitive fields from prompts and responses.
- [query-match-first](query-match-first.md) — `$match`/`$project` before `$sort`/`$group`/`$lookup`/`$addFields`; `$lookup` with a `pipeline` + `$project`; group on the server, not in app code.
- [query-bounded-results](query-bounded-results.md) — `$limit`, cursor + `batchSize`, range-anchored `next_token`, no `skip` for deep pages, bounded worker queue on change-stream consumers.
- [query-allow-disk-use](query-allow-disk-use.md) — `allowDiskUse: true` on heavy `$group`/`$sort`/`$facet` pipelines.
- [query-anchored-regex](query-anchored-regex.md) — Unanchored `/x/i` forces a `COLLSCAN`; use `^prefix`, a normalized indexed field, or `$search`.
- [query-explain-plan](query-explain-plan.md) — (unchanged)
```

### 2. New rule files (kit template: Why it matters / Incorrect / Correct / References)

`query-project-fields.md`, full text:

```markdown
# query-project-fields

**Category:** Query & Aggregation Optimization · **Priority:** HIGH

## Why it matters

A `find` without a projection returns every field of every matching document — embeddings (1536+ floats each), large text blobs, audit arrays, PII. On Azure DocumentDB (PostgreSQL engine) wide rows are detoasted on read, so the cost is paid on the server, on the wire and again in driver deserialization. In agent code the whole document then lands in an LLM prompt or an HTTP response. Project by default; treat a projection-less `find` as a code-review finding.

## Incorrect

```javascript
const seg = await segments.findOne({ segmentId });          // whole doc, incl. embedding + PII
const prompt = `Write an email for: ${JSON.stringify(seg)}`;
```
```python
doc = coll.find_one({"_id": id})                              # orchestrator re-reads the full application
```
```javascript
const cursor = Account.find(filter).cursor();                 // Mongoose: hydrated full documents
```

## Correct

```javascript
const seg = await segments.findOne(
  { segmentId },
  { projection: { _id: 0, name: 1, preferences: 1, purchase_history: 1 } }   // never `embedding`, never PII you do not use
);
```
```python
doc = coll.find_one({"_id": id}, projection={"current_state": 1, "applicant.name": 1})
```
```javascript
const cursor = Account.find(filter).select('balance interestRate').lean().batchSize(500).cursor();
```

In aggregation, `$project` (or `$unset: ["embedding"]`) right after the first `$match`, and inside `$lookup` use `pipeline: [{ $match: ... }, { $project: { event_date: 1, channel: 1 } }]` instead of pulling the whole foreign array.

## References

- https://learn.microsoft.com/en-us/documentdb/query/commands/query-and-write/find (section "Projections")
- `documentdb-data-modeling` → `model-large-field-split.md` (projection is applied after detoast; split very large fields)
```

`query-match-first.md`: Incorrect = the `coll.find({customerId}).sort({timestamp:1}).toArray()` + JS grouping from `04-customer-journey-mapper`, and the `$sort → $group → $replaceRoot → $match` coverage pipeline from `06-collateral-management-store`. Correct = `coll.aggregate([{ $match: { customerId } }, { $project: { timestamp:1, channel:1, eventType:1 } }, { $sort: { timestamp: 1 } }, { $group: { _id: '$channel', events: { $push: '$$ROOT' } } }], { allowDiskUse: true })` and the eligibility `$match` moved before `$group`. One sentence pointing to `model-denormalize-reads.md` for "precompute the grouping key (e.g. `maturity_bucket`) at write time instead of `$addFields` at query time".

`query-bounded-results.md`: Incorrect = `GET /chains` and `find_all().to_list()` list endpoints, `list(coll.aggregate(pipeline))`, `.skip(skip).limit(limit)`, and a change-stream `on('change', async ...)` that awaits an orchestrator per event with no concurrency bound. Correct = (a) `find(filter, { projection }).sort({ strike: 1, _id: 1 }).limit(limit + 1)` returning `{ items, next_token: encode(last.strike, last._id) }` and resuming with `{ $or: [{ strike: { $gt: s } }, { strike: s, _id: { $gt: id } }] }`; (b) `for await (const doc of cursor.batchSize(500))` in Node, `for doc in coll.find(..., batch_size=500)` in PyMongo; (c) a `$limit` stage in every CLI/demo aggregation; (d) a semaphore / `p-limit(8)` around the change-stream handler, with the note that `fullDocument: 'updateLookup'` multiplies the payload so project the handler's reads too.

`query-allow-disk-use.md` (reference: `allowDiskUse` is a documented `aggregate` option, https://learn.microsoft.com/en-us/documentdb/query/commands/aggregation/aggregate): Incorrect = `Position.aggregate(pipeline)` / `db.transactions.aggregate(p)` with `$group` over a whole collection. Correct = `aggregate(pipeline, { allowDiskUse: true })` (Node), `aggregate(p, allowDiskUse=True)` (PyMongo), with the rule "set it on any pipeline whose `$group`/`$sort`/`$facet` input is not already bounded by an indexed `$match` + `$limit`; it does not make a bad pipeline fast, it stops it from failing".

`query-anchored-regex.md`: Incorrect = `vendorName: { $regex: new RegExp(vendor, 'i') }` (unanchored, case-insensitive: full scan) sitting in the same app as an anchored `^` regex two files away. Correct = store `vendorNormalized` (lower/trim) at write time, index it, match with equality; or `^` anchored prefix on an indexed field; or a search index created with `createSearchIndexes` (not `createIndex` with a `"text"`/`"textSearch"` key; see `fts-create-search-index.md`) + `$search` for real keyword matching (link `fts-basic-search.md`).

### 3. Housekeeping

- `docs/SKILLS.md` row for `query-optimization/`: "projection by default, `$match` first, bounded results / pagination, `allowDiskUse`, anchored regex, `explain("executionStats")`".
- CHANGELOG entry.
- Write cost/benefit in I/O, memory, network and latency terms; do not use "RU".

## Out of scope for this PR

Bulk-write findings (`insertOne` in a loop, `update_one` per customer) and "no `explain()` instrumentation" findings were grouped with this theme in the experiment but belong to the write-path theme and to the existing `query-explain-plan.md` respectively.

## Evidence (run folders under `runs/`)

- `runs/04-customer-journey-mapper/20261124-203553/05-audit.json` (checks P08, P09, P16) and `app/src/aggregationTool.js`
- `runs/12-invoice-matching-reconciliation/20261124-191603/05-audit.json` (P10, P11, P18) and `app/src/reconciler.js`
- `runs/19-option-chain-data-store/20261124-192712/05-audit.json` (P14, P21), `doc-gaps.md` (pagination recorded as prior_knowledge_only) and `app/app/main.py`
- `runs/20-interest-accrual-batch-processor/20261124-202826/05-audit.json` and `app/src/worker.js`
- `runs/15-supplier-po-management/20261124-184929/05-audit.json` and `app/app/main.py`
- `runs/19-proactive-outreach-orchestration/20261124-205844/05-audit.json` and `app/src/listener.js`

## Verification

### 1. Already covered? partially_covered

The principles exist in the kit but not in a skill that fires during code generation, and there are no concrete rewrite rules.

- `skills/query-optimization/SKILL.md` has one rule (`query-explain-plan.md`). Its description reads "Use when reviewing a specific query, diagnosing a slow query, or validating that an index is actually being used."
- `skills/query-optimizer/SKILL.md` line 8 says not to invoke it for "general query writing unless user asks for performance or index help".
- `skills/natural-language-querying/SKILL.md` lines 276-295 hold the only general statements: "Project only needed fields", "Filter early — Use `$match` as early as possible", "Add `$limit` after `$sort` when appropriate", and "prefer left-anchored patterns like `/^prefix/`". This skill is for MCP ad-hoc querying, not app code.
- No rule anywhere in `skills/` or `knowledge-base/` covers `allowDiskUse`, `batchSize`, skip-vs-range pagination or bounded change-stream consumers (grep for allowDiskUse, batchSize, skip(, pagination found nothing relevant). `skills/driver/` has nothing on projection.
- Partial overlap that the PR should cross-link: `skills/data-modeling/model-denormalize-reads.md` (it uses a projection example), `skills/data-modeling/model-large-field-split.md` ("projection is applied *after* the server detoasts the row") and `skills/full-text-search/fts-basic-search.md` (use `$search` instead of `$regex`).
- `docs/SKILLS.md` line 22 lists query-optimization as "`explain(\"executionStats\")`, avoiding `COLLSCAN`" only. `CHANGELOG.md` exists.
- On Learn, https://learn.microsoft.com/en-us/documentdb/query/commands/query-and-write/find documents the projection syntax and https://learn.microsoft.com/en-us/documentdb/query/commands/aggregation/aggregate lists `allowDiskUse` as an option. Neither page gives best-practice guidance on projecting, paginating or ordering stages.

### 2. Premise true? confirmed (with corrections applied)

- Every kit file and line the draft quotes was checked against the clone and is accurate.
- Count: the 46 findings cover 31 distinct samples (checked against `phase4/findings-default.json`).
- The draft's statement that "RU" does not apply to vCore is correct: capacity is M-series vCore tiers.
- `allowDiskUse` is a supported `aggregate` option (Learn aggregate page). Projection syntax matches the Learn find page.
- Correction 1: the draft's reference URL `learn.microsoft.com/azure/documentdb/query/commands/query-and-write/find#projections` returns 404. It now points to the live page, https://learn.microsoft.com/en-us/documentdb/query/commands/query-and-write/find.
- Correction 2: the draft recommended a "text index" or "`textSearch` index" with `$search`. `skills/full-text-search/fts-create-search-index.md` says full-text search uses a search index created with `createSearchIndexes`, "**not** `createIndexes` with a `\"text\"` or `\"textSearch\"` key type". Checklist item 7 and the `query-anchored-regex.md` outline now say this.
- Addition: a Learn reference for `allowDiskUse` was added to the `query-allow-disk-use.md` outline.

### 3. Maintainer skeptic: confirmed

The PR names exact files: the `skills/query-optimization/SKILL.md` description and checklist, five new rule files in the kit's existing Why it matters / Incorrect / Correct / References template, a `docs/SKILLS.md` row and a CHANGELOG line. It has a clear DocumentDB angle: detoast cost on the PostgreSQL engine, `createSearchIndexes` + `$search` instead of regex, and no RU vocabulary. It cross-links existing rules instead of duplicating them and sets aside out-of-scope findings. The trigger-scope evidence (the skill is not selected while writing code) is the strongest reason to accept it. Small edits only.

## Finding ids

- F0414
- F0449
- F0486
- F0547
- F0548
- F0550
- F0786
- F0842
- F0750
- F0877
- F0751
- F0840
- F0881
- F0936
- F0963
- F0994
- F1250
- F1331
- F1287
- F1288
- F1291
- F1943
- F1974
- F1977
- F2111
- F1855
- F1915
- F2010
- F2112
- F2113
- F2175
- F2176
- F2237
- F2379
- F2453
- F2509
- F2610
- F2642
- F3096
- F3318
- F3350
- F3315
- F3354
- F3416
- F3417
- F3521
