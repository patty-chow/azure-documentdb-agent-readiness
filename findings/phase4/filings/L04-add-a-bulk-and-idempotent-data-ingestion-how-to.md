---
id: L04
title: "Add a bulk and idempotent data ingestion how-to for Azure DocumentDB"
repo: learn-docs
type: learn-feedback
status: needs_sme
priority: P1
sample_count: 17
member_drafts:
  - 077-idempotent-seeding-bulk-writes-and-index-migration-cookbook-.md
  - 128-bulk-and-idempotent-ingestion-at-scale-bulkwrite-batching-de.md
open_questions: 5
---

# Add a bulk and idempotent data ingestion how-to for Azure DocumentDB

**Proposed location:** a new how-to in the Azure DocumentDB developer guide (for example `how-to-bulk-ingest-data`), next to [Indexing best practices](https://learn.microsoft.com/en-us/azure/documentdb/how-to-create-indexes). Link it from the "Insert documents" steps of the Python and Node.js quickstarts, from the indexing pages, and from "Batch limits" on [Service limits](https://learn.microsoft.com/en-us/azure/documentdb/limitations).

## What happens today

Each piece of a safe ingestion pattern is documented on its own page. No page connects them into a recipe for a seed or load script that can run twice:

- The [`$setOnInsert` reference](https://learn.microsoft.com/en-us/documentdb/query/operators/field-update/$setoninsert) shows a single-document upsert. It has no batch example and no guidance on idempotency keys.
- The [MQL compatibility page](https://learn.microsoft.com/en-us/azure/documentdb/compatibility-query-language) lists the server `bulkWrite` command as not supported, and says functions built on supported commands (`insert`, `update`, `delete`) work. It does not explain what this means for driver bulk APIs.
- [Service limits](https://learn.microsoft.com/en-us/azure/documentdb/limitations) gives the 25,000-writes-per-batch limit, the 2 KB `_id` limit, and says unique index builds run in the foreground and block writes. These are listed as limits, with no ingestion guidance.
- [Indexing best practices](https://learn.microsoft.com/en-us/azure/documentdb/how-to-create-indexes) says to build indexes after a large load, and to use `blocking: true` on an empty collection. It does not cover unique indexes used as idempotency guards.
- The quickstarts show a single `insert_many` / `insertMany`. The [Agent Kit](https://github.com/Azure/documentdb-agent-kit) covers TTL (`skills/indexing/index-ttl-expiry.md`) but has no upsert, bulk-write or idempotency-key guidance; `skills/local-deployment/local-sample-data-management.md:72` says "Idempotent scripts only", yet the example in that section (line 63) is a plain `insertMany`. The DocumentDB table of contents has no entry for bulk, ingest, retry or throttling. Probed URLs such as `/azure/documentdb/how-to-bulk-write` return 404.

Agents without a page to follow fell back to prior knowledge or to RU-based Azure Cosmos DB for MongoDB pages (`troubleshoot-request-rate-too-large`, `optimize-write-performance`). Those pages don't apply to Azure DocumentDB, which is sized by vCore (M-series) tiers and has no request units.

## Why it matters

We had an AI agent (gpt-5-mini, with the Azure DocumentDB Agent Kit and the DocumentDB, Azure and Learn MCP servers) build 100 sample apps. Every prompt asked for a seed script that loads data, creates the index, and can run twice without duplicating data. **17 of the 100 samples** hit this gap (26 findings). The counts come from one experiment run and may shift on a re-run. What the agent did wrong:

- Called `insert_many` behind a unique index, so a second run raised `DuplicateKeyError`, which was caught and printed instead of upserted.
- Claimed in the README that the seed was idempotent while inserting duplicates in a loop on every run.
- Upserted with `$set` on every field, so `createdAt` was overwritten on each refresh.
- Looped single-document upserts with no batching or backoff; called `bulk_write` from prior knowledge with no `BulkWriteError` handling.
- Invented ad hoc canonical keys (parameter hashes, sorted pair keys, composite option-chain keys) and did not canonicalize identifiers at ingest.
- Left index creation implicit in ODM startup; stored sessions without a TTL index; skipped a target-database check and a clean-up section.
- Imported RU-based throttling ideas (request units, 429 handling) from Azure Cosmos DB for MongoDB pages. Azure DocumentDB has no request units; whether it ever returns 429/16500 is open question 2. [needs SME confirmation]

Seed scripts are the first code a developer runs against a new cluster and the most-copied code in any sample, so this gap spreads.

## Proposed change

One page, about two screens, with PyMongo and Node.js snippets:

1. **Which bulk APIs work.** Collection-level `Collection.bulk_write` (PyMongo), `collection.bulkWrite` (Node) and Mongoose `Model.bulkWrite` send `insert`/`update`/`delete` and are supported. Client-level `MongoClient.bulk_write` / `client.bulkWrite` send the server `bulkWrite` command, which is listed as not supported. Use `ordered=False` for loads.
2. **Batch size and limits.** State the 25,000-writes-per-batch hard limit and link "Batch limits". Give recommended starting batch sizes per M-series tier; the docs team should supply these, since none are published today.
3. **Pick an idempotency key.** Compare a deterministic `_id` (simplest filter, uses the built-in index; keep it under 2 KB, hash long keys) with a natural key backed by a unique compound index such as `createIndex({tenantId:1, orderNumber:1}, {unique:true})`. Without that unique index, concurrent filter-based upserts can insert duplicates. Show three key shapes: a composite business key, a sorted pair key (`<minId>_<maxId>`), and a hash of canonicalized parameters (keys sorted before hashing). Show canonicalizing identifiers before writing (normalized email, digits-only phone).
4. **Upsert correctly.** `update_one(filter, {'$set': {...}, '$setOnInsert': {'createdAt': now}}, upsert=True)`; `$inc` for counters; `ReplaceOne(..., upsert=True)` to refresh whole documents; aggregation-then-upsert (or `$merge`) for derived collections.
5. **Handle errors.** Inspect `BulkWriteError.details['writeErrors']`; treat duplicate key 11000 as success for idempotent writes; retry only failed operations; verify with upserted and matched counts. Show the Node equivalent with `collection.bulkWrite(ops, {ordered: false})` and `MongoBulkWriteError`. Example:
   ```python
   ops = [UpdateOne({'_id': d['_id']}, {'$set': d, '$setOnInsert': {'createdAt': now}}, upsert=True) for d in docs]
   for i in range(0, len(ops), BATCH):
       try:
           coll.bulk_write(ops[i:i+BATCH], ordered=False)  # collection-level
       except BulkWriteError as e:
           if [w for w in e.details['writeErrors'] if w['code'] != 11000]: raise
   ```
6. **Retries and capacity.** The documented connection string sets `retrywrites=false`, so the driver does not retry writes for you. Show application-level retry with exponential backoff and jitter for transient errors (network errors, failover), safe only because the writes are idempotent. For large loads, watch CPU, memory and IOPS for the tier and scale the tier or storage if needed, rather than looking for request-unit throttling.
7. **Index order.** Build the unique index that enforces idempotency first, on the empty collection with `blocking: true`; it fails if duplicates exist and blocks writes while it builds. Build other secondary and cosmosSearch vector indexes after a large initial load. In production, create indexes in a migration step, not implicitly at app startup.
8. **TTL for ephemeral data.** `createIndex({createdAt:1}, {expireAfterSeconds: 3600})`; the index must be single-field and the field a BSON Date. Link the TTL entry in the compatibility table.
9. **Embeddings during ingest.** Rate-limit and cache embedding-provider calls; store vectors as `number[]`, not BSON binary, so cosmosSearch indexes pick them up.
10. **Script template and clean-up.** Read the connection string from an environment variable, never hard-coded; check that the database name matches the expected sample database; require `--confirm` / `--force`; create indexes, bulk upsert, print counts. End with a Clean up section: drop the collection, drop the cosmosSearch vector index by name, and a reminder to run `az documentdb mongocluster delete`.

Also ask the owners of the RU-based Cosmos DB for MongoDB throttling pages to add a note that they don't apply to Azure DocumentDB.

**Follow-up (separate PR, Azure/documentdb-agent-kit, after the page exists):** link the page from `skills/data-modeling/SKILL.md`, and in `skills/local-deployment/local-sample-data-management.md` replace the non-idempotent `insertMany` example with an upsert-based collection-level `bulkWrite`. Coordinate with the kit seeding/bulk-load PR (drafts 053, 086, 103) so the two don't overlap.

## Evidence

- `runs/04-earnings-call-rag-assistant/20261124-190247/05-audit.json` (unique index plus `insert_many`; rerun error swallowed)
- `runs/16-atm-network-status-monitor/20261124-202405/05-audit.json` (duplicates despite idempotency claim)
- `runs/17-esg-scoring-pipeline/20261124-192259/doc-gaps.md` (`bulk_write` from prior knowledge, no error handling)
- `runs/16-population-health-dashboard-backend/20261124-195348/doc-gaps.md` (`createdAt` overwritten)
- `runs/19-option-chain-data-store/20261124-192712/doc-gaps.md` (idempotent upsert guidance missing)
- `runs/18-360-data-platform-cdp-orchestration/20261124-205822/05-audit.json` (canonical identifiers at ingest)
- `runs/19-cross-sell-recommendation-beanie/20261124-185532/doc-gaps.md` (pair key and aggregation-to-upsert with `$inc` invented)
- `runs/18-returns-refund-workflow-orchestration/20261124-185415/doc-gaps.md` (no database-name check or confirm flag)
- `runs/10-drug-formulary-semantic-search/20261124-194440/05-audit.json` (embedding provider rate limits)

## Open questions

1. [needs SME confirmation] Why `retrywrites=false`. One position, held by source draft 128 and by several kit drafts, is that retryable writes are not supported and enabling them causes write errors (draft 077 states only that the string sets `retrywrites=false`). Another draft in this set says Learn does not claim they are unsupported. Which is correct, so the page can state the reason?
2. [needs SME confirmation] Whether Azure DocumentDB ever returns error 16500 or HTTP 429 under load, so the page can say what transient errors to retry on.
3. [needs SME confirmation] Recommended starting batch sizes per M-series tier. One draft suggested 500 to 1,000 operations; no published source supports a number.
4. [needs SME confirmation] That client-level `MongoClient.bulk_write` / `client.bulkWrite` fail against the service while collection-level bulk APIs succeed, for the driver versions the quickstarts use.
5. [needs SME confirmation] Whether the unique-index guidance (foreground build, blocks writes) and the `blocking: true` option are current for all supported server versions.

## Source drafts

- 077-idempotent-seeding-bulk-writes-and-index-migration-cookbook-.md
- 128-bulk-and-idempotent-ingestion-at-scale-bulkwrite-batching-de.md
