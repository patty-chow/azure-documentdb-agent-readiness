---
id: L09
title: "Add modeling and query pattern recipes for applications"
repo: learn-docs
type: learn-feedback
status: needs_sme
priority: P1
sample_count: 26
member_drafts:
  - 078-data-modeling-indexing-and-application-pattern-recipes-for-s.md
open_questions: 4
---

# Add modeling and query pattern recipes for applications

## What happens today

The Azure DocumentDB docs on Learn describe features and operators well, but no page tells an application developer how to model and index for a common app pattern, and the TOC has no data-modeling entry. The relevant guidance is scattered across operator, compatibility, indexing, change-stream and full-text-search pages, never phrased as "for a ledger / a status queue / a name-screening list, do this". Coding agents that search Learn land on an operator page, find no recipe, and fall back on generic MongoDB or Cosmos DB habits.

## Why it matters

In an experiment where an LLM coding agent (with the DocumentDB Agent Kit, the DocumentDB MCP server and the Learn MCP server) built 100 sample apps, 26 samples (48 findings) produced code that ran but broke a well-known DocumentDB practice. Counts are from one experiment run. The agent:

- stored money as JS `Number` or Python float (`parseFloat` on invoice totals) instead of Decimal128 or integer minor units;
- indexed only `{ lastUpdated: 1 }` for a `status + lastUpdated` query, with no compound or partial index and no `explain()`;
- ran unprefiltered, case-insensitive `$regex` over `name` and `alt_names` for fuzzy matching;
- grouped, bucketed and computed z-scores client-side instead of with `$group` / `$setWindowFields`;
- sent webhooks inline in change-stream handlers, with no delivery queue or dead-letter;
- added no collection validator despite strict Pydantic/Mongoose schemas, and was unsure `$bucket` and `$jsonSchema` were supported (the matrix says they are);
- improvised RAG patterns (client-side substring fallback, per-document vector upserts, no `/search` error contract) and lacked Mongoose/Beanie depth;
- asked for RU estimates, which do not exist on Azure DocumentDB (capacity is vCore tiers).

Samples are what customers copy first, so these become customer defaults.

## Proposed change

Add a TOC node **"Modeling and query patterns"** under `azure/documentdb`, next to Indexing, Change streams and Full-text search. Track it as one epic with one sub-issue per item; it is too large for a single PR. Each item is a short page or section; the page in brackets gets a "See also" link.

1. **Representing money** [`quickstart-nodejs-mongoose`, `quickstart-python-beanie`, `$toDecimal`]: store `Decimal128` or integer minor units plus currency, never double. Show Mongoose `Schema.Types.Decimal128`, pymongo `Decimal128("19.99")`, Beanie `Decimal`; in pipelines `{ $multiply: [ { $toDecimal: "$amount" }, { $toDecimal: "$rate" } ] }` and `$round` for presentation; one sentence on serializing Decimal128 to JSON in the API layer.
2. **Validate with `$jsonSchema`** [`compatibility-query-language`, `$jsonschema`, both ODM quickstarts]: `createCollection` with a `validator` and `validationLevel: "strict"`, an idempotent `collMod` upgrade path, and the matrix note on which operations are validated and that `bypassDocumentValidation` skips it.
3. **Indexing filtered time-window and lookup queries, verified with explain** [extend `how-to-create-indexes`; link from `how-to-read-explain-output`, `index-advisor`]: equality-sort-range compound `{ status: 1, lastUpdated: 1 }` and the partial alternative with `partialFilterExpression`; precomputed keys (`day`, buckets) with an idempotent backfill; latest-rate lookup `{ from: 1, to: 1, effectiveDate: -1 }` queried with `sort({ effectiveDate: -1 }).limit(1)`, plus the `$lookup` + `$first` variant; a persisted normalized key (set in a pre-save hook, indexed, queried by equality) instead of `$regex`; a short `verify-indexes` script printing `totalDocsExamined`, `totalKeysExamined`, `executionTimeMillis` and `$indexStats`, with the sentence "Azure DocumentDB does not report request units; use docs/keys examined and execution time"; a pointer to Index Advisor for workload-level suggestions; when to use `allowDiskUse: true`.
4. **Server-side aggregation** [`aggregate`, compatibility matrix]: timeline via indexed `$match` → `$sort` → `$group`, range pagination instead of `skip`; outliers via `$setWindowFields` with `$avg`/`$stdDevSamp` partitioned by day, plus the two-pass `$group` + `$lookup` variant; one line confirming `$bucket`, `$bucketAuto`, `$setWindowFields`, `$facet`, `$merge` support.
5. **Resilient change-stream consumer** [section on `change-streams`; link to its existing resume-token content rather than duplicate it]: the handler writes a `deliveries` record keyed by `change._id` and returns; a worker claims with `findOneAndUpdate`, retries with backoff and dead-letters after N attempts; incremental aggregates (update a per-cohort counter document from each event instead of recomputing nightly); restate the page's limitations (cursors reopened after failover, resumability lost on a single-shard to multi-shard transition) [needs SME confirmation] and a fallback to `startAtOperationTime` from the last processed event time; historical change streams with PITR reach back up to 35 days [needs SME confirmation].
6. **Ledger design**: append-only collection, immutable audit fields, unique `idempotencyKey` (`createdAt`, `createdBy`, `transactionRef`, `source`; Mongoose `immutable: true`); never a TTL index on a ledger; expire derived data in a separate collection.
7. **Fuzzy name matching without `$regex`** [`full-text-search-fuzzy`, `full-text-search-custom-analyzers`]: prerequisite that full-text search is in preview and must be enabled on the cluster [needs SME confirmation]; `createSearchIndexes` (`dynamic: false`) with `lowerCase` + `asciiFolding` + `edgeGram` on the index side and a `keyword` + `lowerCase` `searchAnalyzer`, queried with `$search` `text`; note that `autocomplete`, `regex` and `wildcard` operators inside `$search` are not supported, so use `edgeGram` for prefix matching; materialize `normalized_name` for exact hits; prefilter by country or shard key. Callout: "Do not run `{ $regex: ..., $options: 'i' }` over a whole collection in production. A case-insensitive, unanchored pattern cannot use an index selectively."
8. **ODM notes** [both ODM quickstarts]: Mongoose `strict: true` default and `strict: "throw"`, `immutable: true`, enum fields, a pre-save hook for normalized keys, `.lean()` + projection, a tenant-safety plugin that rejects `find`/`update`/`delete` without `tenantId`; Beanie `set()`/`update()` do not re-validate the full model, so validate a DTO first [needs SME confirmation], and aggregation should use the Beanie-initialized collection (`get_pymongo_collection()` in 2.x, `get_motor_collection()` in 1.x) [needs SME confirmation].
9. **RAG and agent patterns** [`vector-search`, `quickstart-python-vector-search`, `full-text-search-hybrid`]: vectors as `number[]` with `cosmosSearch` indexes (`vector-ivf`, `vector-hnsw`, `vector-diskann`), dimension limits 2,000 uncompressed, 4,000 with `compression: "half"` on HNSW or IVF, 16,000 with product quantization on DiskANN; state that BSON binary vectors (subtype 9) are stored and returned but not indexed, are silently absent from `cosmosSearch` results, and that a binary query vector is rejected ("expected an array type field"), so the page should name BSON binary explicitly rather than only "array of numbers"; batched `insert_many(..., ordered=False)` in batches of about 500–1000; detect index presence (`listIndexes` for the `cosmosSearch` index, `$listSearchIndexes` for text search indexes, see open question 1) and fall back to a server-side `$search` or hybrid query, not client-side substring scoring; `fetch_k` of 5–10× `k` for client-side rerank, otherwise the server `cosmosSearch` `k`; agent memory as `raw_turns` (TTL on `occurredAt`) plus `summaries` with `embedding: number[]` and `embedding_dim`; a minimal `/search` contract (400 on empty query, 502 on embedding failure, `similarity_score` in results); a short pymongo retry wrapper for transient errors; never pass connection strings or keys to the LLM, expose parameterized tools instead.
10. **Sharding in samples** [`partitioning`]: demos under about 100k documents stay single-shard; if a sample shards, show the shard key (`tenantId`, hashed `userId`) in code and in the `Microsoft.DocumentDB/mongoClusters` Bicep/ARM definition.

Do not write up as gaps: durable resume tokens (already on `change-streams`) and `$bucket` version checks (supported on 5.0–8.0).

Related kit follow-up (not part of this Learn item): Azure/documentdb-agent-kit has no rule for Decimal128, `$jsonSchema` or a delivery-queue consumer; it already has partial-index examples in `skills/indexing/index-pattern-cookbook.md`, and `skills/data-modeling/` covers embed-vs-reference, the 16 MB limit, denormalization, large-field split and schema versioning. Once these pages exist, the kit's `data-modeling` and `indexing` skills can link to them.

## Evidence

- `runs/07-multi-currency-ledger/20261124-190814/doc-gaps.md`
- `runs/12-abandoned-cart-recovery-orchestration/20261125-054042/05-audit.json`
- `runs/18-sanctions-list-screening-agent/20261124-202645/app/scripts/demo_screen.py`
- `runs/03-portfolio-tracker-with-live-alerts/20261124-190220/02-readiness.json`
- `runs/15-cohort-analysis-backend/20261124-205336/doc-gaps.md`
- `runs/12-invoice-matching-reconciliation/20261124-191603/app/src/agent.js`
- `runs/04-customer-journey-mapper/20261124-203553/doc-gaps.md`

## Resolved

- Vector-index facts: settled 2026-11-25 from the Learn vector-search, half-precision, product-quantization and limitations pages and engine issue documentdb/documentdb#109, see findings/phase4/DECISIONS.md.
  - Dimension limits quoted in item 9: 2,000 uncompressed; 4,000 with `compression: "half"` on HNSW or IVF; 16,000 with product quantization on DiskANN (vector-search "Features and limitations", half-precision, product-quantization and limitations pages). The select-algorithm quickstarts' HNSW 8,000 figure is a documentation inconsistency still open with engineering and is not quoted here.
  - BSON binary vectors are stored and returned intact but are not indexed by any `cosmosSearch` index kind, are silently absent from results, and a binary query vector is rejected; Learn requires an array of numbers (vector-search page, DiskANN field table and IVF Important box; engine issue documentdb/documentdb#109, closed completed 2026-04-28).
  - `listIndexes` reports vector-index options under `cosmosSearch`, so item 9's index-presence check is the documented shape (vector-search page, "Get vector index definitions").

## Open questions

1. [needs SME confirmation] `compatibility-query-language` marks `$listSearchIndexes` as unsupported, while the full-text-search pages use it to check index readiness. Which is correct? Item 9 depends on it.
2. [needs SME confirmation] Full-text search and multishard change streams are labeled preview on Learn. Are they still preview, and should items 5 and 7 keep the prerequisite wording?
3. [needs SME confirmation] Change-stream limits cited in item 5: the 35-day PITR historical-replay window, and the resumability behavior on single-shard to multi-shard transitions and after failover.
4. [needs SME confirmation] Beanie behavior in item 8: that `set()`/`update()` skip full-model validation, and the collection accessor name per Beanie version.

## Source drafts

- 078-data-modeling-indexing-and-application-pattern-recipes-for-s.md (its header said 28 samples; the samples it names recount to 26; 48 finding ids)
