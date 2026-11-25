---
title: "Add a \"Bulk writes and idempotent seeding\" developer-guide page to Azure DocumentDB docs"
repo: learn-docs
type: learn-feedback
status: ready_with_edits
priority: P1
sample_count: 15
findings: 20
bucket: learn-doc_gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Docs request: "Bulk writes and idempotent seeding" page for Azure DocumentDB

**Proposed location:** Azure DocumentDB developer guide, next to [Indexing best practices](https://learn.microsoft.com/en-us/azure/documentdb/how-to-create-indexes) (suggested slug `how-to-bulk-write-idempotent-seed`). Link it from the "Insert documents" sections of `quickstart-python` and `quickstart-nodejs`, and from the indexing pages.

## What happens today

Each piece of the pattern is documented somewhere on its own, but nothing connects them into a recipe for a seed or ingest script that is safe to run twice:

- The [`$setOnInsert` reference](https://learn.microsoft.com/en-us/documentdb/query/operators/field-update/$setoninsert) shows `updateOne(..., {upsert: true})` for one document.
- The [MQL compatibility page](https://learn.microsoft.com/en-us/azure/documentdb/compatibility-query-language) lists TTL and unique index properties as supported. It also lists the **server `bulkWrite` command as not supported** in v5.0 to v8.0, and says client wrappers that call supported commands (`insert`, `update`, `delete`) work. Nothing turns this into plain driver guidance, so agents cannot tell whether `bulk_write` / `bulkWrite` is safe to use.
- [Indexing best practices](https://learn.microsoft.com/en-us/azure/documentdb/how-to-create-indexes) says to build indexes after the data load for large migrations, and to use `blocking: true` when building on an empty collection. It does not cover unique indexes used as idempotency guards.
- The quickstarts show a single `insert_many` / `insertMany`.

The Azure DocumentDB Agent Kit does document TTL (`skills/indexing/index-ttl-expiry.md`). It does not cover upserts, bulk writes or idempotent keys. Its only seed guidance, in `skills/local-deployment/local-sample-data-management.md`, says "Idempotent scripts only", but the example below that line is a plain `insertMany` that fails or duplicates data when run again.

In a 100-sample agent-readiness run (gpt-5-mini + Agent Kit + DocumentDB/Azure/Learn MCP servers), every sample prompt asked for "a seed script that loads sample data, creates the index, and can be run twice without duplicating data". Twenty audit `doc_gaps` records from 15 samples point at this missing page. Because the agent had nothing to cite, it produced these failures:

- `insert_many` behind a unique index, so a rerun raises `DuplicateKeyError`, which is caught and printed instead of being upserted (`04-earnings-call-rag-assistant`).
- The README claims the seed is idempotent, but `Heartbeat.create` in a loop inserts duplicates on every run (`16-atm-network-status-monitor`, `18-adverse-event-reporting-pipeline`, `04-medical-imaging-metadata-store`).
- The upsert uses `$set` for every field, so `createdAt` is overwritten on each refresh (`16-population-health-dashboard-backend`).
- A loop of single-document upserts instead of a batched collection bulk write, with no batch size or backoff (`17-seasonal-trend-spotter-agent`, `17-rare-disease-literature-search`).
- `bulk_write` written from prior knowledge, marked `prior_knowledge_only`, with no `BulkWriteError` handling (`17-esg-scoring-pipeline`).
- Sessions stored with no TTL index (`02-ai-powered-product-recommendations`).
- Index creation left implicit in `init_beanie` / `syncIndexes()`, with no guidance on whether it belongs at startup or in a migration (`15-supplier-po-management`, `01-unified-customer-profile-store`).
- The seed never checks which database it is connected to and has no confirm flag (`18-returns-refund-workflow-orchestration`). There is no clean-up section for the collection or the vector index (`17-esg-scoring-pipeline`).
- Canonical keys invented ad hoc: SHA-256 of (name, params), `<minId>_<maxId>` pair keys, `underlying+expiry+strike+type` composite filters (`16-population-health-dashboard-backend`, `19-cross-sell-recommendation-beanie`, `19-option-chain-data-store`).

## Why it matters

Seed scripts are the first code a developer runs against a new cluster, and the most-copied code in any sample. There are two Azure DocumentDB details that generic MongoDB knowledge gets wrong:

1. The server `bulkWrite` command is not supported. The newer client-level APIs (PyMongo `MongoClient.bulk_write`, Node driver `MongoClient.bulkWrite`) send that command. Collection-level `bulk_write` / `bulkWrite` does not.
2. The connection string uses `retrywrites=false`, so the driver does not retry writes automatically. A retry in application code is only safe when every write is idempotent.

Without a page that states this, humans and agents ship seeds that corrupt counts on the second run, or call an API the service rejects.

## Proposed page outline (one page, about two screens)

1. **Which bulk APIs work.** Collection-level `Collection.bulk_write` (PyMongo), `collection.bulkWrite` (Node driver) and Mongoose `Model.bulkWrite` are supported, because they send `insert` / `update` / `delete` commands. Client-level `MongoClient.bulk_write` / `client.bulkWrite` send the server `bulkWrite` command, which is listed as not supported. Link the compatibility table. Recommend `ordered=False` for seeds.
2. **Pick an idempotency key.** Choose between a deterministic `_id` and a natural key backed by `createIndex({tenantId:1, orderNumber:1}, {unique:true})`. Give three worked key shapes:
   - a composite business key (`tenantId+orderNumber`)
   - a sorted unordered pair (`'<minId>_<maxId>'`)
   - a hash of canonicalized parameters for derived or materialized documents (sort keys before hashing)

   Trade-offs: a deterministic `_id` uses the built-in `_id` index and gives the simplest upsert filter. A filter-based upsert keeps ObjectId, but needs an explicit unique compound index, or concurrent upserts can insert duplicates.
3. **Upsert correctly.** Use `update_one(filter, {'$set': {...}, '$setOnInsert': {'createdAt': now}}, upsert=True)` and link the `$setOnInsert` reference. Use `$inc` for counters (for example co-purchase counts) and `ReplaceOne(..., upsert=True)` to refresh a whole document. Show the aggregation-then-upsert pattern for derived collections (`$merge` is supported).
4. **Batch it.** PyMongo:
   ```python
   from pymongo import UpdateOne
   from pymongo.errors import BulkWriteError
   ops = [UpdateOne({'_id': d['_id']}, {'$set': d, '$setOnInsert': {'createdAt': now}}, upsert=True) for d in docs]
   for i in range(0, len(ops), BATCH):
       try:
           r = coll.bulk_write(ops[i:i+BATCH], ordered=False)   # collection-level, not MongoClient.bulk_write
           print(r.upserted_count, r.modified_count, len(r.upserted_ids))
       except BulkWriteError as e:
           # 11000 = duplicate key (a concurrent upsert won the race); anything else is a real error
           fatal = [w for w in e.details['writeErrors'] if w['code'] != 11000]
           if fatal: raise
   ```
   Show the Node equivalent with `collection.bulkWrite(ops, {ordered:false})` and `MongoBulkWriteError`. State the service's recommended batch sizes per vCore (M-series) tier. The docs team should supply these numbers, because none are published today. Explain that, because connection strings use `retrywrites=false`, transient and network errors need retries in application code (exponential backoff with jitter), which are safe only because the writes above are idempotent upserts.
5. **TTL for ephemeral data.** Show `createIndex({createdAt:1}, {expireAfterSeconds: 3600})`. The field must be a BSON Date, and the index must be single-field. Link the compatibility table entry.
6. **Create indexes explicitly, in the right order.** `syncIndexes()` / `init_beanie` is fine for samples. In production, build indexes in a separate migration step. Explain how this fits with the existing guidance to build indexes after a large load: build the **unique** index that enforces idempotency first, on the empty collection with `blocking: true`. A unique index build fails if duplicates already exist, and it takes an exclusive lock on the collection while it builds. Non-unique secondary indexes and vector indexes can be built after a large initial load.
7. **Seed-and-index script template** (Python and Node). Steps:
   - read the connection string from an environment variable, never hard-coded
   - check that `db.name` matches the expected sample database name
   - require `--confirm` / `--force`
   - create indexes, bulk upsert, and print counts

   End with a **Clean up** section: `drop_collection`, drop the cosmosSearch vector index by name, and a reminder to run `az documentdb mongocluster delete`.

## Evidence (run folders from the experiment)

- `runs/04-earnings-call-rag-assistant/20261124-190247/05-audit.json`: run-twice requirement `partly_met`. Unique index plus `insert_many`; `DuplicateKeyError` is caught and printed.
- `runs/16-atm-network-status-monitor/20261124-202405/05-audit.json`: the seed inserts duplicate heartbeats despite the README's idempotency claim.
- `runs/17-esg-scoring-pipeline/20261124-192259/doc-gaps.md`: `bulk_write` marked prior-knowledge-only; no `BulkWriteError` handling; no clean-up section.
- `runs/16-population-health-dashboard-backend/20261124-195348/doc-gaps.md`: `$setOnInsert` missing, so `createdAt` is overwritten; a deterministic cache `_id` had to be invented.
- `runs/18-returns-refund-workflow-orchestration/20261124-185415/doc-gaps.md`: the seed has no database-name check and no confirm flag.
- `runs/19-cross-sell-recommendation-beanie/20261124-185532/doc-gaps.md`: the canonical pair key and aggregation-to-upsert with `$inc` had to be invented.

## Follow-up (separate PR, Azure/documentdb-agent-kit)

Once the page exists, link it from `skills/data-modeling/SKILL.md`. In `skills/local-deployment/local-sample-data-management.md`, replace the non-idempotent `insertMany` example with an upsert-based collection-level `bulkWrite`.

## Verification

### 1. Already covered? partially_covered
- Learn [`$setOnInsert` reference](https://learn.microsoft.com/en-us/documentdb/query/operators/field-update/$setoninsert) covers a single-document upsert: "The `$setOnInsert` operator only takes effect during upsert operations". It has no batch or bulk example and no idempotency-key guidance.
- Learn [compatibility-query-language](https://learn.microsoft.com/en-us/azure/documentdb/compatibility-query-language) lists TTL and Unique as supported index properties and `$setOnInsert`, `$inc` and `$merge` as supported. It lists `bulkWrite` as "❌ No" and says "Any function that relies on supported server commands is compatible". It does not explain what this means for driver bulk APIs.
- Learn [how-to-create-indexes](https://learn.microsoft.com/en-us/azure/documentdb/how-to-create-indexes) covers index timing for large loads and the `blocking: true` option. It does not cover unique-index idempotency.
- Agent Kit `skills/indexing/index-ttl-expiry.md` covers TTL, including the date-field requirement. The kit has no upsert, bulk-write or idempotent-key guidance. `skills/local-deployment/local-sample-data-management.md:72` says "Idempotent scripts only", but its example is a plain `insertMany`.
- A Learn search for bulk write, upsert, TTL and unique index on Azure DocumentDB returned no dedicated page. The probed URLs `/azure/documentdb/ttl` and `/how-to-bulk-write` return 404.
- Conclusion: the pieces exist but are scattered, and there is no seeding or bulk-write recipe. The draft now links the existing pages and points the TTL section at existing coverage.

### 2. Premise true? confirmed (corrections applied)
- Corrected: the original draft said to confirm that `bulk_write` / `bulkWrite` is supported. The compatibility page lists the server `bulkWrite` command as unsupported in v5.0 to v8.0. Collection-level driver bulk APIs work because they issue the supported `insert`, `update` and `delete` commands. The client-level `MongoClient.bulk_write` / `client.bulkWrite` APIs (added in recent drivers for MongoDB 8.0) send the unsupported command. Section 1 of the outline now makes this distinction.
- Corrected: the original draft gave unsourced batch sizes of "100–500 / 500–2000". No source publishes these, so the outline now asks the docs team to supply recommendations per tier.
- Added: the connection string uses `retrywrites=false`, so the driver does not retry writes automatically. Retries in application code are required and safe only with idempotent writes.
- Reconciled: "create the unique index before inserting" is consistent with the `blocking: true` guidance for empty collections. The compatibility page warns that a unique index build takes an exclusive lock on the collection. Secondary indexes can still be deferred for large loads, as how-to-create-indexes recommends.
- `$setOnInsert`, `$inc`, `$merge`, TTL (BSON Date, single-field) and unique compound indexes are all confirmed by the Learn pages above and by the Agent Kit TTL skill.

### 3. Maintainer skeptic: confirmed
The draft names a concrete new page, its location and the pages to link from, and gives an outline with code. It is specific to Azure DocumentDB: the unsupported server `bulkWrite` command, `retrywrites=false`, the exclusive lock during a unique index build, M-series tiers, the cosmosSearch vector index and `az documentdb mongocluster` clean-up. It belongs on Learn docs, and the Agent Kit change is split off as a follow-up. A docs maintainer would accept it with these edits.

## Finding ids
F0166, F0197, F0199, F0575, F0617, F2636, F2667, F2762, F2765, F2796, F2856, F2860, F2862, F2894, F2924, F3029, F3090, F3193, F3195, F3309
