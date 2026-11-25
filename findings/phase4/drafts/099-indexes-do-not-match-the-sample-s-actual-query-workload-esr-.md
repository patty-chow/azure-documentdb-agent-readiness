---
title: "documentdb-indexing: add a query-to-index reconciliation step and an ensure_indexes lifecycle rule (29/100 samples shipped indexes that do not match their queries)"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 29
findings: 36
bucket: sample-violated-practice
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# documentdb-indexing: add a query-to-index reconciliation step and an ensure_indexes lifecycle rule

## What happens today

`skills/indexing/` explains index *shapes* thoroughly (`index-compound-esr.md`, `index-pattern-cookbook.md`, partial indexes in `index-single-field.md`, an "Always verify" footer in the cookbook, and `index-count-budget.md`'s "Never pre-create 'maybe useful' indexes"). It says nothing about **reconciling the indexes an agent declared with the queries it actually wrote**, and nothing about **where and when an application creates its indexes** (the only lifecycle rule, `index-lifecycle-drop-hide.md`, is about dropping). `local-deployment/local-prod-parity.md` mentions a `schema/01_indexes.js` but is not linked from the indexing skill and is not loaded when an agent is "designing indexes".

In a 100-sample experiment (gpt-5-mini, agent-kit skills + DocumentDB/Azure/Learn MCP servers) the agent loaded this skill, declared indexes up front from the cookbook, then wrote the queries and never went back. The audit stage found the two drifting apart in **29 of 100 samples (36 findings)**:

- **Index does not match the hot path.** Single-field indexes where the query filters two fields (`tickers`+`timestamp`, `vendorName`+`totalAmount`, `branchId`+`transactionDate`, `employee_id`+`timestamp`, `patientId`+`drugName`); a compound index `{customerId, updatedAt, processedAt}` whose equality prefix the abandonment query never supplies, so the sort on `updatedAt` cannot use it; `(product_id, sentiment_score)` indexed while the aggregation groups on `sentiment_label`; filter fields with no index at all (`procedureCode`, `sentiment.label`, `themes`, `pmid`, `year`, `source`/`start_time`, `applicant.ssn_last4`); a text index on `headline` that no endpoint uses; an unanchored regex over `name`/`alt_names` with only `_id_` and the vector index present; `$dateToString` grouping with no stored day key; a `$facet` pipeline that `explain` showed as COLLSCAN. No `partialFilterExpression` anywhere a status or optional-LLM-field filter called for one.
- **Creation is implicit, misplaced or missing.** Indexes created *after* bulk upserts; inside a query helper (`_ensure_index()` at query time); via `ensureIndexes()`/`syncIndexes()` at startup without `autoIndex:false`; via Mongoose schema `index: true` with `autoIndex:false` set in `db.js` and the field omitted from `create_indexes.js`, so the index never materialises; default names (`location_2dsphere`) and no manifest/migration script.
- **MCP failure with no fallback.** In two runs the builder called `documentdb_create_index`, got `Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true`, retried payloads, then logged a decision to "document the index for manual portal/CLI creation". A one-line driver `createIndexes` would have worked.
- HNSW vector indexes created with only `dimensions`/`similarity`, no `m`/`efConstruction` (vector-search has only `vector-create-diskann-index.md`).

## Why it matters

The skill's own ESR rule is being *cited* in these samples (audit `source: documentdb-indexing`) while the shipped code violates it, because the rule is applied once at design time and never checked against the final code. Samples are meant to be copied; a sample that ships `{status:1}` + `{createdAt:-1}` and a startup `syncIndexes()` teaches exactly the anti-pattern the skill warns about. A closing checklist is cheap for the model to follow and directly fixes the root cause (declare-first, never-reconcile).

## Proposed change (one PR)

### 1. New rule `skills/indexing/index-query-to-index-worksheet.md` — Priority CRITICAL

Run **after** application code is written, before declaring the sample done:

1. Grep the code for every `find(`, `findOne(`, `aggregate(`, `updateOne/updateMany(` filter, `countDocuments(`, and every `.sort(` / `$sort` / `$group._id`. Put each in a table: collection | predicate fields (eq / range / $in) | sort fields | group key.
2. For each row derive the ESR shape; one compound index per distinct prefix, drop single-field indexes that are a prefix of it.
3. If the predicate is a fixed value (`status: "abandoned"`, `llmTags.tier: {$exists:true}`) add `partialFilterExpression` and make sure the query repeats the predicate. Only filter forms that partial indexes accept may be used (equality, `$exists: true`, `$gt/$gte/$lt/$lte`, `$type`, `$and`/`$or`/`$in`); `$exists: false` and "field is missing" predicates are not accepted, so model those as an explicit boolean/status field instead (e.g. `categorized: false`).
4. If the query groups or filters on a derived value (`$dateToString`, lower-cased name) store the precomputed field (`day`, `normalized_name`) at write time and index that; never index-then-regex.
5. Delete every declared index that no row uses (text index with no `$search` endpoint, `(product_id, sentiment_score)` when the pipeline groups on `sentiment_label`).
6. Run `explain("executionStats")` for every row; require IXSCAN and no blocking SORT.

Worked example (the most common failure):

```javascript
// Declared up front:
db.carts.createIndex({ customerId: 1, updatedAt: 1, processedAt: 1 });
// Written later:
db.carts.find({ status: "open", updatedAt: { $lt: cutoff } }).sort({ updatedAt: 1 });
// explain: COLLSCAN + SORT — the query never supplies customerId, so the index prefix is broken.
// Fix: index the shape you wrote (equality first, then sort/range):
db.carts.createIndex({ status: 1, updatedAt: 1 }, { name: "idx_carts_status_updated" });
// Or, if only open carts are ever scanned, a smaller partial index the query must repeat:
db.carts.createIndex({ updatedAt: 1 },
  { name: "idx_open_carts_by_updated", partialFilterExpression: { status: "open" } });
// Then confirm: explain("executionStats") shows IXSCAN and no blocking SORT.
```

Output artefact: a `## Indexes` table in the README mapping each query to its named index. This is a reasonable acceptance criterion for sample prompts.

### 2. New rule `skills/indexing/index-ensure-script-lifecycle.md` — Priority HIGH

- Every app ships **one** idempotent, version-controlled `ensure_indexes` script (`scripts/ensure_indexes.{js,py}` or `schema/01_indexes.js`) that uses the driver `createIndexes` command with **explicit `name`s**, and is run as a deploy/migration step **before** seed/bulk load (`createIndex`/`createIndexes` is a no-op for an index whose key, name and options already match; changing options under the same name errors, so the script must drop/rename deliberately rather than silently redefine).
- Runtime code only **verifies** (`listIndexes`) and fails fast or warns; it never calls `createIndex` inside query helpers or workers.
- ODMs: `mongoose.connect(..., { autoIndex: false })`, Beanie: do not rely on `init_beanie` auto-creating indexes in production; the ensure script is the source of truth. Call out the trap seen in the run: `autoIndex:false` + schema `index: true` + field missing from the script = index never exists.
- **MCP fallback:** `documentdb_create_index` is a management tool and is off by default (`ENABLE_MANAGEMENT_TOOLS=true`, see `mcp-setup`). If it errors, do not retry payloads or defer to "manual portal creation" — write the index into the ensure script with the driver and run it. Include the 5-line pymongo and Node snippets.
- Verification step: `listIndexes` shows every expected name, then `explain("executionStats")` per worksheet row.

### 3. Wiring

- `skills/indexing/SKILL.md`: add both rules to the `## Rules` list (worksheet first) and one sentence after the index-engine note: "Index design is not finished until the worksheet has been run against the final code."
- `skills/query-optimization/query-explain-plan.md` and `skills/local-deployment/local-prod-parity.md`: link to the two new rules.
- Follow-up (separate PR to `vector-search/`): add `vector-create-hnsw-index.md` documenting `m` (default 16, range 2–100), `efConstruction` (default 64, range 4–1000, must be at least `2 * m`) and query-time `efSearch` (default 40), per https://learn.microsoft.com/en-us/azure/documentdb/vector-search; F1188 shows HNSW created with only `dimensions`/`similarity`. (Omitting them is valid — defaults apply — so frame this as "choose and record the values deliberately", not as an error.)

## Evidence (run folders in the experiment repo)

- `runs/12-abandoned-cart-recovery-orchestration/20261124-184507/05-audit.json` — compound index with unused `customerId` equality prefix; sort cannot use it; audit cites `documentdb-indexing` ESR rule as violated.
- `runs/17-ai-survey-response-analyzer/20261124-205518/events.jsonl` — three `documentdb_create_index` calls fail on the management-tools default; decision logged to leave index creation to the operator; no driver fallback.
- `runs/16-population-health-dashboard-backend/20261124-195348/events.jsonl` — `documentdb_explain_operation` on the `$facet` pipeline returns COLLSCAN; only single-field indexes shipped.
- `runs/16-subscription-billing-engine/20261124-192251/05-audit.json` — `autoIndex:false` in `db.js`, `subscriptionId: index:true` on the schema, omitted from `create_indexes.js`, so the index is never created.
- `runs/07-customer-review-sentiment-pipeline/20261125-054042/05-audit.json` — index on `(product_id, sentiment_score)`; aggregation groups on `sentiment_label`.

Other affected samples (29 distinct): 02-swift-message-parser-store, 02-transaction-categorization-agent, 03-portfolio-tracker-with-live-alerts, 04-earnings-call-rag-assistant, 05-branch-performance-analytics, 06-collateral-management-store, 06-omnichannel-interaction-history, 06-symptom-triage-chatbot-rag, 07-voice-of-customer-sentiment-hub, 08-insurance-pre-auth-multi-agent, 08-interest-rate-scenario-modeler, 08-personalized-email-campaign-builder, 11-market-news-sentiment-orchestration, 12-invoice-matching-reconciliation, 14-loan-origination-workflow-orchestration, 14-telehealth-session-summarizer, 15-prescription-refill-agent, 17-rare-disease-literature-search, 18-sanctions-list-screening-agent, 19-insider-threat-detection-pipeline, 19-proactive-outreach-orchestration, 20-interest-accrual-batch-processor, 20-open-banking-api-cache-layer, 20-store-locator-with-geospatial-search.

## Verification

### 1. Already covered? — partially_covered
The agent kit has the ingredients but not the reconciliation step or an application-side creation lifecycle:
- `skills/indexing/index-pattern-cookbook.md` ("## Always verify"): "Run `explain(\"executionStats\")` after creating the index" — verification exists, but only per index at creation time, not as a closing pass over the final code.
- `skills/indexing/index-count-budget.md`: "Never pre-create \"maybe useful\" indexes in production" — covers the principle behind deleting unused indexes, not a procedure.
- `skills/local-deployment/local-prod-parity.md`: "**Index definitions live in the repo**, not in a developer's mongosh history" with a `schema/01_indexes.js` example using named indexes — covers the ensure-script idea, but sits in local-deployment and is not linked from `skills/indexing/SKILL.md`.
- `skills/indexing/index-lifecycle-drop-hide.md` covers only drop/hide.
- No match anywhere in `skills/` or `knowledge-base/` for worksheet/reconcile, `autoIndex`, `syncIndexes`/`ensureIndexes`, or a fallback when the MCP `create_index` tool is disabled. `skills/mcp-setup/SKILL.md` lines 154–155 say how to enable `ENABLE_MANAGEMENT_TOOLS` but not what to do when it is off.
- `skills/vector-search/` has `vector-create-diskann-index.md` only; `m`/`efConstruction` do not appear anywhere in `skills/` (grep), and the SKILL.md description lists only `lBuild`/`lSearch`/`maxDegree`.

### 2. Is the premise true? — confirmed (minor corrections applied)
- Finding count and spread verified against `scratchpad/phase4/findings-default.json`: 36 findings across 29 distinct samples.
- MCP behaviour verified in microsoft/documentdb-mcp: `src/config.ts:213` `managementTools: parseBoolean(process.env.ENABLE_MANAGEMENT_TOOLS, false)`; `src/security/authorization.ts:50` throws "Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true to opt in."; `tool_list.md` lists `create_index` as a `management` tool.
- HNSW parameters verified on https://learn.microsoft.com/en-us/azure/documentdb/vector-search: `m` "16 by default, minimum value is 2, maximum value is 100"; `efConstruction` "64 by default ... `efConstruction` has to be at least `2 * m`"; `efSearch` 40 by default. Corrected the follow-up to state defaults and note that omitting them is valid.
- Correction: the draft listed `category: {$exists:false}` as a `partialFilterExpression` candidate. Partial index filters accept equality, `$exists: true`, comparison, `$type`, `$and`/`$or`/`$in` and geo operators only (https://www.mongodb.com/docs/manual/core/index-partial/); `$exists: false` is not accepted. Rewritten.
- Correction: the worked example used `partialFilterExpression: { processedAt: null }`, which is not a clearly supported partial filter; replaced with a `status: "open"` equality filter, and kept the core lesson (equality prefix never supplied, so COLLSCAN + SORT).
- Correction: "createIndex is idempotent for identical key+options" narrowed to identical key, name and options; a changed definition under the same name errors.
- Other claims check out against the kit clone: partial indexes in `index-single-field.md`, ESR in `index-compound-esr.md`, `schema/01_indexes.js` in `local-prod-parity.md`, `query-optimization/query-explain-plan.md` exists. Nothing in the draft contradicts the vCore facts (no RU, Atlas Search or databaseAccounts claims).

### 3. Maintainer skeptic — confirmed
Names exact files to add (`skills/indexing/index-query-to-index-worksheet.md`, `skills/indexing/index-ensure-script-lifecycle.md`), the SKILL.md rule list to edit and two cross-links, and has a concrete Azure DocumentDB angle: the DocumentDB MCP server's `create_index` is off by default and the kit gives no driver fallback, and the rule format matches existing kit rule files (priority, wrong/right example, verify). The HNSW item is correctly split into a separate follow-up. I would accept this as a PR with the edits above; the README query-to-index table is a suggestion for the sample prompts rather than kit content.

## Finding ids

- F0308
- F0341
- F0485
- F0584
- F0749
- F0754
- F0875
- F0876
- F0935
- F0995
- F1064
- F1188
- F1248
- F1293
- F1326
- F1853
- F1854
- F1942
- F1972
- F1973
- F2110
- F2450
- F2479
- F2613
- F2768
- F2799
- F2832
- F2833
- F2901
- F3139
- F3283
- F3351
- F3418
- F3453
- F3454
- F3525
