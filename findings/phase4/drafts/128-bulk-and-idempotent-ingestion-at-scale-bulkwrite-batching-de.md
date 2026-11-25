---
title: "Add a \"Bulk and idempotent data ingestion\" how-to for Azure DocumentDB (bulkWrite batching, deterministic keys, retry/backoff)"
repo: learn-docs
type: learn-feedback
status: ready_with_edits
priority: P2
sample_count: 6
findings: 6
bucket: learn-practice_not_public
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Add a "Bulk and idempotent data ingestion" how-to for Azure DocumentDB

**Page area:** https://learn.microsoft.com/en-us/azure/documentdb/ (new how-to, for example `how-to-bulk-ingest-data`). Link it from the Python and Node.js quickstarts and from the "Batch limits" section of [Service limits and quotas](https://learn.microsoft.com/en-us/azure/documentdb/limitations).

## What happens today
We ran an experiment that had agents build 100 Azure DocumentDB sample apps. For ingestion, they could not find a DocumentDB Learn page on:
- batching `bulkWrite` / `bulk_write` (with `ordered: false`) and choosing a batch size
- handling `BulkWriteError` (writeErrors, duplicate key 11000 on retry) and checking `upsertedIds`
- idempotent upserts with a deterministic key, either a composed `_id` or a unique compound index such as `underlying+expiry+strike+optionType` plus `updateOne(..., upsert: true)`
- canonicalizing identifiers when data comes in (normalized email, digits-only phone, hashed id) so duplicate feeds don't create duplicate documents
- retry/backoff during large loads, including throttling and caching calls to an external embedding provider

The only related public facts today are scattered: the limits page states the per-request batch limit (25,000 writes per batch operation) and that unique index builds run in the foreground and block writes; the connection string uses `retrywrites=false`. Nothing ties these into an ingestion recipe. Agents marked these practices "prior knowledge only." For throttling, they cited Cosmos DB RU pages instead: `troubleshoot-request-rate-too-large`, "monitor RU consumption (429)" and `cosmos-db/mongodb/optimize-write-performance`. Those pages are about the request-unit (RU) based Azure Cosmos DB for MongoDB, not vCore-based Azure DocumentDB, which is sized by M-series compute tiers and has no request units.

## Why it matters
6 of the 100 samples hit this gap: ESG scoring, rare-disease literature search, seasonal trend spotter, drug formulary, options chain and the CDP platform. Results without a page to follow:
- One seed script ran `update_one` one document at a time in a loop instead of using `bulkWrite`.
- One pipeline called `bulk_write` with no `BulkWriteError` handling.
- Three audits marked retry/backoff as violated.
- Builders brought in RU and 429 ideas that don't apply to the service.

Because DocumentDB connection strings set `retrywrites=false` (retryable writes are not supported), the driver will not transparently retry a failed write. Application-level retries are therefore the norm, which makes idempotent write design essential rather than optional.

## Proposed content
1. **Batching:** `bulkWrite` / `insertMany` with `ordered: false`, a suggested starting batch of roughly 500 to 1,000 operations (tune against cluster tier and document size), and the hard limit of 25,000 writes per batch request (link to the "Batch limits" section of the limitations page; batches above it fail).
2. **Idempotency:** two patterns, with their tradeoffs.
   - (a) a deterministic composed `_id` (keep it under the 2 KB `_id` limit; hash long keys)
   - (b) a unique compound index plus `updateOne` with upsert on the same fields

   Create unique indexes before the bulk load (unique index builds run in the foreground and block writes on the collection). Show how to canonicalize key fields before writing.
3. **Errors:** inspect `BulkWriteError.details` / `writeErrors`, treat duplicate key 11000 on a retried insert as success for idempotent writes, retry only the failed operations, and use `upsertedIds` / matched and upserted counts to verify.
4. **Retry and capacity:** because `retrywrites=false`, implement application-level retry with exponential backoff and jitter for transient errors (network errors, failover). State that DocumentDB has no RU-based 429 throttling: during large loads, watch CPU, memory and IOPS for the M-tier and scale the tier (or use autoscale / higher-performance storage) if needed.
5. **Embeddings during ingest:** rate-limit and cache provider calls, and store vectors as `number[]` (not BSON binary) so cosmosSearch vector indexes pick them up.
6. PyMongo and Node.js snippets for steps 1 to 4.

Also ask the owners of the RU-based Cosmos DB for MongoDB throttling pages to add a note that they don't apply to Azure DocumentDB (vCore).

## Evidence (run folders)
- runs/19-option-chain-data-store/20261124-192712 (05-audit.json P12, doc-gaps.md "Idempotent upsert guidance")
- runs/17-esg-scoring-pipeline/20261124-192259 (05-audit.json "Bulk writes", doc-gaps.md)
- runs/17-seasonal-trend-spotter-agent/20261124-185115 (05-audit.json P32, doc-gaps.md "Seed/ingest batching guidance")
- runs/18-360-data-platform-cdp-orchestration/20261124-205822 (05-audit.json "Canonical identifiers at ingest")
- runs/10-drug-formulary-semantic-search/20261124-194440 (05-audit.json "Embedding provider rate-limits")
- runs/17-rare-disease-literature-search/20261124-195633

## Verification

### 1. Already covered? partially_covered
- https://learn.microsoft.com/en-us/azure/documentdb/limitations, "Batch limits": "Maximum writes per batch operation: **25,000 writes**" and "Batch operations exceeding 25,000 writes will **fail**." Same page: "Unique index builds are done in the foreground and block writes in the collection" and "Maximum size for `_id` field value: 2 KB." These are limits only, with no ingestion guidance.
- The DocumentDB TOC (https://learn.microsoft.com/en-us/azure/documentdb/toc.json) has no entry matching bulk, ingest, load, retry or throttle. The closest pages are the migration pages; https://learn.microsoft.com/en-us/azure/documentdb/how-to-migrate-native-tools covers mongoimport/mongorestore commands with no batching, ordered, idempotency or retry guidance. Command reference pages exist for `insert`/`update` and `$setOnInsert` but no recipe.
- Agent kit (not the target): skills/connection/SKILL.md "Retry Logic" has a generic withRetry backoff helper keyed on codes 16500/429 (RU-era codes); skills/local-deployment/local-sample-data-management.md says "Idempotent scripts only"; no bulkWrite/BulkWriteError/upsert guidance. documentdb-mcp has nothing relevant.
- Conclusion: the batch limit is public; the how-to the draft asks for is not.

### 2. Premise true? confirmed (with corrections applied)
- Corrected: the per-request write limit lives on the limitations page "Batch limits" section (25,000 writes), not on a max-document-size page. The draft now cites the exact number and page.
- Added: DocumentDB connection strings use `retrywrites=false` (retryable writes not supported; also stated in agent-kit skills/azure-deployment/SKILL.md), which strengthens the case for idempotent application-level retries.
- Added: unique index builds block writes, so create them before loading (limitations page).
- Verified: vCore DocumentDB uses M-series tiers, not RUs, so RU 429 pages do not apply; vectors must be `number[]` for cosmosSearch indexes. The 500 to 1,000 batch size is labeled a suggested starting point, not a documented limit.

### 3. Maintainer skeptic: confirmed
Names a concrete new page location, concrete sections with DocumentDB-specific content (25,000-write batch limit, retrywrites=false, foreground unique index builds, no RUs/M-tier monitoring, number[] vectors), linking points, and six evidence runs. This is not generic hygiene; the DocumentDB-specific angles (no retryable writes, no RU throttling) are exactly where agents went wrong. Acceptable as a Learn content request.

## Finding ids
- F2866
- F2903
- F2934
- F1618
- F3314
- F3006
