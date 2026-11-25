---
title: "Learn: add a \"Modeling and query patterns for applications\" recipe section (money, validators, compound/partial indexes with explain, server-side aggregation, change-stream consumers, fuzzy name matching, ODM and RAG patterns)"
repo: learn-docs
type: learn-feedback
status: ready_with_edits
priority: P1
sample_count: 28
findings: 48
bucket: learn-doc_gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Add a "Modeling and query patterns for applications" recipe section to Azure DocumentDB on Learn

## What happens today

The Azure DocumentDB docs (https://learn.microsoft.com/en-us/azure/documentdb/) cover features and operators well. No page tells an application developer how to model and index for a common app pattern, and the TOC has no data-modeling entry. The guidance that does exist is spread across operator reference pages (`$toDecimal`, `$jsonSchema`, `$setWindowFields`), the compatibility matrix, `how-to-create-indexes`, `how-to-read-explain-output`, `change-streams` and the full-text-search pages. None of it is written as "for a ledger / a status queue / a name-screening list, do this".

We ran a readiness pipeline over 100 sample prompts with gpt-5-mini, the DocumentDB Agent Kit, the DocumentDB MCP server and the Learn MCP server. **In 28 of the 100 samples (48 findings)** the generated design ran but broke a well-known DocumentDB best practice. Each time, the audit found that the agent had looked on Learn and in the kit and found only prior knowledge or an operator page, with no DocumentDB recipe. Concretely:

| What the agent did | Samples | Confirmed in code |
|---|---|---|
| Stored money as JS `Number` / Python float, not Decimal128 or integer minor units | 07-multi-currency-ledger, 12-invoice-matching-reconciliation, 13-basel-iii-capital-ratio-calculator, 16-loyalty-points-ledger | `parseFloat(amountMatch[1])` for `totalAmount` in `app/src/agent.js` and `app/src/llm.js` (12-invoice-matching) |
| Created a single-field `{lastUpdated:1}` index for a `status + lastUpdated` query, with no compound or partial index and no `explain()` | 12-abandoned-cart-recovery-orchestration, 14-telehealth-session-summarizer, 09-lead-scoring-agent | `createIndex({ lastUpdated: 1 })` only in `app/src/run.js`; audit checks P07, P08, P11 "violated" |
| Ran an unprefiltered `$regex` with `$options:'i'` over `name` and `alt_names` for fuzzy matching | 18-sanctions-list-screening-agent, 12-invoice-matching-reconciliation | `coll.find({"$or":[{"name":{"$regex":...}},{"alt_names":{"$elemMatch":{"$regex":...}}}]})` in `app/scripts/demo_screen.py` |
| Computed grouping, bucketing or z-scores client-side instead of with `$group` / `$setWindowFields` | 04-customer-journey-mapper, 09-crypto-wallet-activity-analyzer, 08-interest-rate-scenario-modeler, 02-swift-message-parser-store | audit: "implemented grouping client-side which is unsafe for large timelines" |
| Sent webhook HTTP calls inline in the change-stream handler, with no deliveries queue and no dead-letter, and recomputed everything instead of updating incrementally | 03-portfolio-tracker-with-live-alerts, 15-cohort-analysis-backend | readiness `information_gaps`: "Webhook delivery/retry policy ... no installed skill prescribes a sample policy" |
| Added no collection validator even though the app has a strict Pydantic/Mongoose schema | 13-algorithmic-trade-journal, 13-household-grouping-linkage, 15-cohort-analysis-backend, 12-cross-border-payment-audit-trail | audit: "uses Pydantic validation ... lacks a DB-level validator" |
| Did not find feature support: builders were unsure whether `$bucket`/`$bucketAuto` and `$jsonSchema` validators are supported | 15-cohort-analysis-backend | `compatibility-query-language` lists both as supported on v5.0–v8.0; the agent never reached that row |
| Lacked ODM depth (Mongoose strict/immutable, `.lean()`+projection, tenant plugin; Beanie `update()` validation, aggregation via the Beanie collection) | 10-multi-tenant-storefront-saas, 15-supplier-po-management, 17-ai-survey-response-analyzer, 16-loyalty-points-ledger, 12-cross-border-payment-audit-trail | audit: pattern present only as `prior_knowledge_only` |
| Improvised RAG/agent patterns (client-side substring fallback when no vector index, per-document upserts for vector seeding, no `/search` error contract, agent memory held in process) | 13-product-q-a-chatbot-rag, 14-hyper-personalized-content-engine, 10-expense-report-auto-categorizer, 14-telehealth-session-summarizer, 08-regulatory-compliance-rag-checker, 14-dynamic-pricing-engine, 09-lead-scoring-agent, 20-provider-directory-semantic-search | audit `doc_gaps` in each run |

## Why it matters

Customers copy these patterns out of samples first. A sample gallery that stores money as floats, scans whole collections with `$regex` and skips `explain()` teaches the wrong defaults. Without a DocumentDB-branded recipe, an LLM agent falls back on its generic MongoDB/Cosmos DB knowledge every time. Several findings still asked for "RU estimates", which do not exist on Azure DocumentDB (vCore tiers, not request units). The fix is cheap. Each recipe is one or two screens, and most of the content already exists on operator and feature pages. It only needs to be assembled and linked from the pages agents actually land on.

## Proposed change

Add a TOC node **"Modeling and query patterns"** under `azure/documentdb`, as a sibling of Indexing, Change streams and Full-text search. Track it as one epic with one sub-issue per bullet. Each bullet becomes one short page or section, and the existing page named in brackets gets a "See also" link to it. The bullets are ordered by how many samples hit the problem.

1. **Representing money** [link from `quickstart-nodejs-mongoose`, `quickstart-python-beanie`, `/documentdb/query/operators/aggregation/$todecimal`]
   - Store amounts as `Decimal128`, or as integer minor units plus a currency code. Never use double.
   - Mongoose: `amount: { type: mongoose.Schema.Types.Decimal128, required: true }`. pymongo: `bson.decimal128.Decimal128("19.99")`. Beanie: a `Decimal` field, which the Beanie/pydantic BSON encoder stores as Decimal128.
   - In pipelines, use `{ $multiply: [ { $toDecimal: "$amount" }, { $toDecimal: "$rate" } ] }` so arithmetic stays decimal, and `$round` for presentation.
   - Add one sentence on serializing Decimal128 to JSON in the API layer.

2. **Validate documents with `$jsonSchema`** [link from `compatibility-query-language` (`$jsonSchema*` row), `/documentdb/query/operators/evaluation-query/$jsonschema` and both ODM quickstarts]
   - `db.createCollection("trades", { validator: { $jsonSchema: { bsonType: "object", required: ["strategy_id","type","timestamp","pnl"], properties: { pnl: { bsonType: "decimal" } } } }, validationLevel: "strict" })`.
   - Idempotent apply/upgrade script: when the collection already exists, run `collMod` with the same validator.
   - State in the recipe itself what the matrix note already says: "Schema validation supports: `insert`, `update`, `findAndModify`, and the `$merge` / `$out` stages", and `bypassDocumentValidation` skips it.

3. **Indexing for filtered time-window and lookup queries, verified with explain** [extend `how-to-create-indexes`, which today has one two-field compound example and no ordering or verification guidance; link from `how-to-read-explain-output` and `index-advisor`]
   - Compound example in equality-sort-range order: `db.carts.createIndex({ status: 1, lastUpdated: 1 })`. Partial alternative: `db.carts.createIndex({ lastUpdated: 1 }, { partialFilterExpression: { status: "abandoned" } })` (partial indexes are listed as supported under "Index properties" in the compatibility page).
   - Precomputed keys: write `day: "2026-11-24"` (or `$dateTrunc` at ingest) and `maturity_bucket` at insert time, then index `{ message_type: 1, day: 1 }`. Show the backfill `updateMany` as an idempotent migration step.
   - Latest-rate lookup: index `{ from: 1, to: 1, effectiveDate: -1 }` and query with `find().sort({effectiveDate:-1}).limit(1)`, plus the `$lookup` + `$first` variant.
   - Persisted normalized key: set `vendor_normalized` in a pre-save hook, index it, and query it with equality instead of `$regex`.
   - A 20-line `verify-indexes.js` / `verify_indexes.py` that runs `explain("executionStats")` for the app's main queries and prints `totalDocsExamined`, `totalKeysExamined` and `executionTimeMillis`, plus `$indexStats` to find unused indexes. Say explicitly: *Azure DocumentDB does not report request units; use docs/keys examined and execution time.* Point to Index Advisor for workload-level suggestions.
   - Explain when to set `allowDiskUse: true` on `aggregate()`.

4. **Server-side aggregation patterns** [link from `/documentdb/query/commands/aggregation/aggregate`, `compatibility-query-language`]
   - Timeline: an indexed `$match`, then `$sort`, then `$group` by `{customerId, channel}`. Paginate by range (`_id` or timestamp) instead of `skip`.
   - Outliers: `$setWindowFields` with `$avg`/`$stdDevSamp` partitioned by day, then `$set: { z: {$divide:[{$subtract:["$v","$mean"]},"$sd"]} }`. Also show the two-pass `$group` + `$lookup` variant.
   - Add one line each confirming that `$bucket`, `$bucketAuto`, `$setWindowFields`, `$facet` and `$merge` are supported on 5.0–8.0. The matrix already says so, but agents never found it.

5. **Resilient change-stream consumer** [section on `change-streams`, which already shows `resumeAfter` with a durably saved token in six languages. Link to it rather than duplicate it]
   - The handler writes a delivery record `{ _id: change._id (idempotency key), ruleId, userId, payload, status: "pending", attempts: 0, nextAttemptAt }` to a `deliveries` collection and returns. A separate worker claims pending rows (`findOneAndUpdate` setting `status: "sending"`), POSTs, retries with backoff, and dead-letters after N attempts.
   - Incremental aggregates: update a per-cohort counter document from each event instead of recomputing nightly.
   - Restate the page's own limitations: going from single-shard to multi-shard breaks resumability, and cursors must be reopened after failover. The consumer must tolerate a failed `resumeAfter` and fall back to `startAtOperationTime` from the last processed event time. Historical change streams with PITR integration can reach back up to 35 days.

6. **Ledger design** (section in the same node)
   - Use an append-only collection with immutable audit fields `createdAt`, `createdBy`, `transactionRef`, `source` and `idempotencyKey` (unique index), and Mongoose `immutable: true`. **Never put a TTL index on a ledger.** Expire derived data in a separate collection.

7. **Fuzzy name matching without `$regex`** [link from `full-text-search-fuzzy`, `full-text-search-custom-analyzers`]
   - Start with a prerequisite line: full-text search is in preview and must be enabled on the cluster first (`full-text-search-overview#enable-full-text-search`).
   - Use a `createSearchIndexes` definition with `dynamic: false` and a custom analyzer: `lowerCase` + `asciiFolding` token filters plus an `edgeGram` token filter on the index side, and a `keyword`-tokenizer + `lowerCase` `searchAnalyzer` on the query side. Query it with the `$search` `text` operator. The custom-analyzers page already demonstrates this asymmetric index/search analyzer pattern for part numbers; this recipe applies it to person and entity names. Note that the `autocomplete`, `regex` and `wildcard` operators inside `$search` are not supported. Use `edgeGram`, not `autocomplete`, for prefix matching.
   - Materialize `normalized_name` for exact/equality hits. Prefilter by `country` (or the shard key) using a structured filter alongside the text query.
   - Callout: "Do not run `{ $regex: ..., $options: 'i' }` over a whole collection in production. A case-insensitive, unanchored pattern cannot use an index selectively: at best it scans the whole index, and with no index it scans the whole collection."

8. **ODM notes** [sections appended to `quickstart-nodejs-mongoose` and `quickstart-python-beanie`]
   - Mongoose: the `strict: true` default and `strict: "throw"`, `immutable: true` for `createdAt`, and enum fields. A pre-save hook for normalized keys. `.lean()` + projection for read-heavy endpoints. A 15-line tenant-safety plugin that rejects `find`/`update`/`delete` without `tenantId`.
   - Beanie: `Document.set()` / `update()` send update operators to the server without re-validating the full model, so validate a DTO first and then apply it. Run pipelines through the Beanie-initialized collection (`Model.get_pymongo_collection()` in Beanie 2.x, `get_motor_collection()` in 1.x) so Beanie and raw aggregation share one client.

9. **RAG and agent application patterns** [section on `vector-search`, link from `quickstart-python-vector-search` and `full-text-search-hybrid`]
   - Vectors are `number[]` (BSON binary vectors are not indexed). Seed with `insert_many(..., ordered=False)` in batches of about 500–1000.
   - Detect index presence before querying: `listIndexes` shows the `cosmosSearch` vector index, and `$listSearchIndexes` (as used on the full-text-search pages) shows text search indexes. If one is missing, fall back to a server-side `$search` text index or a hybrid query, not to client-side substring scoring.
   - `fetch_k` guidance for client-side rerank: fetch 5–10× `k` and cap it by the latency target. Use the server `cosmosSearch` `k` directly when there is no rerank.
   - Agent memory shape: `raw_turns` with a TTL index on `occurredAt`, and `summaries` with `embedding: number[]` and `embedding_dim`.
   - Minimal `/search` contract: 400 on an empty query, 502 on embedding failure, and results that carry `similarity_score`.
   - A 10-line pymongo retry wrapper for transient errors, and a security callout: **never pass connection strings or keys to the LLM; expose parameterized tools that call the database.**

10. **Sharding guidance for samples** [callout on `partitioning`]: a demo under about 100k documents stays single-shard. If the sample shards, show the shard key (`tenantId`, hashed `userId`) both in code and in the Bicep/ARM definition of the `Microsoft.DocumentDB/mongoClusters` deployment.

## Evidence (run folders from the experiment; no connection strings)

- `runs/07-multi-currency-ledger/20261124-190814/doc-gaps.md`: "Decimal128 / currency arithmetic guidance" and "Exchange-rate document indexing pattern"
- `runs/12-abandoned-cart-recovery-orchestration/20261125-054042/05-audit.json`: checks P07/P08/P11 violated; `app/src/run.js` creates only `{ lastUpdated: 1 }`
- `runs/18-sanctions-list-screening-agent/20261124-202645/app/scripts/demo_screen.py`: unprefiltered `$regex` over `name` / `alt_names`; `doc-gaps.md` "Regex vs full-text recommendations"
- `runs/03-portfolio-tracker-with-live-alerts/20261124-190220/02-readiness.json`: `information_gaps` on webhook delivery policy and delivery-record storage
- `runs/15-cohort-analysis-backend/20261124-205336/doc-gaps.md`: `$bucket` support, validators, explain diagnostics, incremental snapshots
- `runs/12-invoice-matching-reconciliation/20261124-191603/app/src/agent.js`: `parseFloat` for `totalAmount`
- `runs/04-customer-journey-mapper/20261124-203553/doc-gaps.md`: client-side grouping instead of a server-side timeline pipeline

## Notes for the writer

- Two of the raw findings were wrong and should **not** be written up as stated. Durable resume tokens are already on `change-streams`; keep that content and link to it. `$bucket`/`$bucketAuto` need no version check on 5.0–8.0.
- The compatibility page lists `$listSearchIndexes` as "No" on every version, but the full-text-search pages use `$listSearchIndexes` to check index readiness. Reconcile the two before recipe 9 relies on it.
- Keep every example in Azure DocumentDB terms: resource `Microsoft.DocumentDB/mongoClusters`, `az documentdb mongocluster`, vCore (M-series) tiers with no RUs, `cosmosSearch` vector indexes with `number[]` vectors, `$search` text indexes created with `createSearchIndexes` (not Atlas Search), and the PostgreSQL-based DocumentDB engine.
- The companion Agent Kit (Azure/documentdb-agent-kit) has no rule for Decimal128, `$jsonSchema` or a delivery-queue consumer. It already has partial-index examples in `skills/indexing/index-pattern-cookbook.md`. Once these pages exist, the kit's `data-modeling` and `indexing` skills can link to them instead of restating them.

## Verification

### 1. Already covered? partially_covered

- The Learn TOC (https://learn.microsoft.com/en-us/azure/documentdb/toc.json) has no entry titled data modeling, validation or Decimal128. The closest are the `$jsonSchema` and `$toDecimal` operator reference pages. That confirms the central gap: there is no application-pattern or modeling node.
- Pieces exist but are scattered, and none is phrased as a recipe:
  - `change-streams` (https://learn.microsoft.com/en-us/azure/documentdb/change-streams) already covers durable resume tokens. Under "Resume a change stream": "The `_id` field of each change event serves as the resume token. Store it durably". It also covers `startAtOperationTime` historical replay and the failover and shard-transition limitations. It has no delivery-queue, retry or dead-letter consumer pattern.
  - `compatibility-query-language` lists `$jsonSchema*`, `$bucket`, `$bucketAuto`, `$setWindowFields`, `$toDecimal` and `$search` as supported on v5.0–v8.0, and partial indexes as supported. Its note reads: "Schema validation supports: `insert`, `update`, `findAndModify`, and the `$merge` / `$out` stages". It gives no usage recipe.
  - `full-text-search-custom-analyzers` documents `createSearchIndexes`, `lowerCase`, `asciiFolding`, the `edgeGram` tokenizer and filter, `$search` `text`, and an asymmetric `analyzer`/`searchAnalyzer` prefix example on part numbers. It does not address name screening or prefiltering, and does not warn against `$regex`.
  - `how-to-create-indexes` (Indexing best practices) has a single compound-index example (`{"lastName":1,"timeInOrgInYears":1}`). It does not cover ESR ordering, partial indexes, explain verification or `$indexStats`.
- Agent Kit: `grep -i decimal128|jsonschema|dead.?letter` over `skills/` and `knowledge-base/` returns nothing. `skills/indexing/index-pattern-cookbook.md` has `partialFilterExpression` examples. `skills/data-modeling/` has embed-vs-reference, 16 MB limit, denormalization, large-field split and schema versioning, but nothing on money, validators or ledgers.
- The verdict is partially covered: change-stream resume, operator support and analyzer mechanics exist, while the recipes the draft asks for do not. The draft body already treats resume tokens and `$bucket` support as existing content to link rather than write. This verification added the existing-coverage pointers to recipes 3, 5 and 7.

### 2. Is the premise true? confirmed (with precision edits)

- Every feature the recipes rely on is supported according to `compatibility-query-language`: `$jsonSchema`, `$toDecimal`, `$bucket`/`$bucketAuto`, `$setWindowFields`, `$facet`, `$merge`, `$lookup`, `$indexStats`, `$search`, `collMod`, `explain`, and partial and TTL index properties. The change-stream limitations quoted in recipe 5 match the "Limitations" section of `change-streams`. Analyzer and tokenizer names in recipe 7 match the tables on `full-text-search-custom-analyzers`. No RU metric exists on vCore, consistent with the M-series tier model.
- Edits applied for precision:
  - Added that full-text search is in preview and must be enabled on the cluster ("Full-text search is in preview. Before using these examples, enable full-text search").
  - Added that the `autocomplete`, `regex` and `wildcard` operators inside `$search` are unsupported, per "Current limitations" on the custom-analyzers page.
  - Replaced "cannot use a B-tree index" with the more accurate "cannot use an index selectively (at best a full index scan)".
  - Split index-presence detection into `listIndexes` for `cosmosSearch` and `$listSearchIndexes` for search indexes, and flagged that the compatibility matrix marks `$listSearchIndexes` "No" while the FTS pages use it.
  - Named the Beanie collection accessor by version.
  - Added the PITR 35-day historical-replay note from `change-streams`.
- No claim contradicts the fixed facts (mongoClusters, `az documentdb mongocluster`, `cosmosSearch` with `number[]`, `$search` text indexes, vCore tiers, PostgreSQL-based engine).

### 3. Maintainer skeptic: confirmed

- As a Learn maintainer for azure/documentdb, I would accept this as an epic. It names the exact pages to extend or link from (`how-to-create-indexes`, `change-streams`, `full-text-search-custom-analyzers`, `full-text-search-fuzzy`, `compatibility-query-language`, `quickstart-nodejs-mongoose`, `quickstart-python-beanie`, `vector-search`, `partitioning`, `index-advisor`) and gives a concrete snippet-level outline for each recipe.
- Every item has a DocumentDB angle: no RUs, `createSearchIndexes`/`$search` analyzers instead of Atlas Search, `cosmosSearch` `number[]` vectors, vCore change-stream limitations, and the compatibility matrix rows. That makes it more than generic hygiene.
- The small edit needed is to file it as one tracking issue with ten sub-issues, because it is too large for a single PR. Learn docs is the right repository. The kit follow-up is noted separately.

## Finding ids

F0300, F0366, F0367, F0404, F0474, F0475, F0476, F0477, F0481, F0543, F1148, F1149, F1151, F1281, F1356, F1419, F1540, F1543, F1642, F1644, F1669, F1966, F1970, F2033, F2103, F2104, F2140, F2172, F2232, F2307, F2308, F2311, F2374, F2377, F2411, F2412, F2475, F2478, F2502, F2503, F2504, F2505, F2633, F2700, F2827, F3131, F3136, F3476
