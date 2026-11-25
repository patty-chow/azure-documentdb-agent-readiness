---
title: "Add a `driver-bulk-load-idempotent-seed` rule to the documentdb-driver skill (reference seed.js / seed.py skeleton)"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 11
findings: 14
bucket: sample-violated-practice
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Add `driver-bulk-load-idempotent-seed`: a reference seed / bulk-load pattern for Azure DocumentDB

## What happens today

The kit has 17 skills and none of them says how to bulk-load data. Grepping `skills/` and `knowledge-base/` for `bulkWrite`, `bulk_write`, `insertMany`, `insert_many`, `writeErrors` or `allowDiskUse` finds only the small `insertMany` example in `skills/local-deployment/local-sample-data-management.md`, which says "Idempotent scripts only" but does not show how. `skills/driver/SKILL.md` has one rule (`driver-singleton-client`), and its description does not mention seeding or bulk loading, so an agent writing `seed.py` has no reason to open it.

We ran gpt-5-mini with this kit (plus the DocumentDB, Azure and Learn MCP servers) over 100 sample-app prompts. Each prompt required that a seed script load sample data, create the index, and be safe to run twice without duplicating data. The model knew the seed had to be idempotent and reached for `upsert: true`. With no pattern to follow, it made the same mistakes across at least 11 samples:

| Mistake | Example (run folder under `runs/`) |
|---|---|
| A loop of single `update_one` / `replace_one` / `save()` / `findOneAndUpdate` calls instead of chunked `bulkWrite` | `16-population-health-dashboard-backend/20261124-195348` (`app/seed.py`: 5,000 single `update_one(upsert=True)` calls); `10-support-ticket-rag-assistant/20261124-204529` (`app/seed.py:69-74`); `18-360-data-platform-cdp-orchestration/20261124-205822` (`pipeline.py:24-42`) |
| Upserts mixed with a plain insert or a random id, so every rerun duplicates rows | `10-multi-tenant-storefront-saas/20261124-184121` (`app/src/seed.js:25-31`: `Order.create(...)` next to upserts); `19-cross-sell-recommendation-beanie/20261125-055705` (`seed.py`: `save()` per document, ids from `random.randint`) |
| All secondary indexes created before the load, or no unique index on the business key | `01-anti-money-laundering-pattern-detector/20261124-200112` (`seed.py:18-23`); `02-ai-powered-product-recommendations/20261124-181835` (`insertMany`, no unique index on `productId`) |
| `MongoBulkWriteError` caught, logged and dropped; `writeErrors` never read, so 11000 is not told apart from transient errors | `02-real-time-event-stream-ingestion/20261124-203233` (`app/src/ingest.js:40-42`, flagged `[high]` in that run's `doc-gaps.md`) |
| A nightly job iterates `find({})` with no `batch_size`, resume marker or concurrency limit | `19-insider-threat-detection-pipeline/20261124-202818` (`run_nightly.py:18-22`); `16-multi-touch-attribution-model/20261124-205342` |
| A destructive seed with no check of the target database name and no opt-in flag | `18-returns-refund-workflow-orchestration/20261124-185415` (`app/scripts/seed.js:5-6`) |
| `aggregate(pipeline, allowDiskUse=False)` on a faceted pipeline | `16-population-health-dashboard-backend/20261124-195348` (`app/aggregations.py`) |

When the model looked for bulk-load guidance it found the Cosmos DB **RU-based** page (`learn.microsoft.com/azure/cosmos-db/mongodb/optimize-write-performance`) and copied its wording. The `16-population-health` audit justifies batching as reducing "RU charge", but Azure DocumentDB capacity is vCore tiers (M-series), not request units. No Azure DocumentDB page exists to point at: `learn.microsoft.com/en-us/azure/documentdb/best-practices` and `.../how-to-optimize-write-performance` both return 404. The kit is the right place for this guidance.

## Why it matters

- 14 audit findings across at least 11 of the 100 samples come down to this one missing pattern.
- A seed is usually the first thing a developer runs against a new cluster. Five thousand single upserts over TLS to `*.mongocluster.cosmos.azure.com` are slow enough that people decide the service is slow. A seed that duplicates rows on its second run makes the sample look broken.
- Ingest and nightly jobs reach production in the same shape. Dropping `writeErrors` means writes are lost silently on transient errors. Azure DocumentDB connection strings set `retrywrites=false`, so the driver does not retry those writes, and the application has to.

## Proposed change

### 1. New rule file: `skills/driver/driver-bulk-load-idempotent-seed.md`

Use the same layout as `driver-singleton-client.md` (Why it matters / Incorrect / Correct / References). Priority HIGH. Core text:

> **Why it matters.** Seeds, imports and nightly jobs are the largest writes most apps ever do. A single upsert per document costs one round trip each. A seed that is not keyed on a natural key duplicates data when it runs again. A bulk error that is logged and dropped hides lost writes. Make every write an upsert filtered on a deterministic natural key. Create a unique index on that key **before** the load: it keeps the upsert filter fast and turns any accidental plain insert or concurrent rerun into a duplicate-key error (11000) instead of a duplicate row. Create the other indexes (secondary, text and `cosmosSearch` vector) **after** the load, so the engine builds each one once instead of updating it on every write. Do this especially for `vector-ivf`, which needs data in the collection to build useful lists. Azure DocumentDB connection strings use `retrywrites=false`, so the script has to retry failed operations itself.

**Incorrect** (what the model generated; `16-population-health` seed.py, condensed):

```python
patients.create_index([("patient_id", 1)], unique=True)
patients.create_index([("diagnoses", 1)])     # 4 more secondary indexes before the load
for i in range(1, 5001):
    patients.update_one({"patient_id": f"P{i}"}, {"$set": gen_patient(i)}, upsert=True)  # 5000 round trips
```

**Correct: `seed.js` skeleton**

```javascript
import { MongoClient, MongoBulkWriteError } from "mongodb";

const DB_NAME = process.env.DATABASE_NAME;
const CHUNK = Number(process.env.SEED_CHUNK_SIZE ?? 1000);

// 1. Refuse to run against anything that does not look like the sample DB unless opted in.
if (!/^sample_/.test(DB_NAME) && !process.argv.includes("--confirm")) {
  throw new Error(`Refusing to seed "${DB_NAME}": pass --confirm to write to a non-sample database`);
}

const client = new MongoClient(process.env.DOCUMENTDB_URI); // connection string from env, never hard-coded
const db = client.db(DB_NAME);
const products = db.collection("products");
let duplicates = 0;

// 5. Read writeErrors: 11000 means "already there" for a seed; retry only the rest, with backoff
//    (the connection string sets retrywrites=false, so the driver will not retry writes for you).
async function runBulk(coll, ops, attempt = 0) {
  try {
    return await coll.bulkWrite(ops, { ordered: false });
  } catch (err) {
    if (!(err instanceof MongoBulkWriteError)) throw err;
    const writeErrors = [].concat(err.writeErrors ?? []);   // may be a single WriteError or an array
    const failed = writeErrors.filter(e => e.code !== 11000);
    duplicates += writeErrors.length - failed.length;
    if (failed.length === 0) return err.result;
    if (attempt >= 2) throw err;
    await new Promise(r => setTimeout(r, 500 * 2 ** attempt));
    return runBulk(coll, failed.map(e => ops[e.index]), attempt + 1);
  }
}

try {
  // 2. Unique index on the natural key FIRST.
  await products.createIndex({ productId: 1 }, { unique: true, name: "products_productId_unique" });

  // 3. Deterministic ids, chunked unordered upserts.
  const docs = generateProducts(); // productId derived from the data, never Math.random()
  let upserted = 0, matched = 0;
  for (let i = 0; i < docs.length; i += CHUNK) {
    const ops = docs.slice(i, i + CHUNK).map(d => ({
      updateOne: { filter: { productId: d.productId }, update: { $set: d }, upsert: true }
    }));
    const res = await runBulk(products, ops);
    upserted += res.upsertedCount ?? 0; matched += res.matchedCount ?? 0;
  }

  // 4. Secondary / text / vector indexes AFTER the load. Embeddings must be stored as number[]
  //    (BSON binary vectors are not indexed by cosmosSearch).
  await products.createIndex({ category: 1, price: -1 }, { name: "products_category_price" });
  await db.command({ createIndexes: "products", indexes: [{ name: "products_vec", key: { embedding: "cosmosSearch" },
    cosmosSearchOptions: { kind: "vector-hnsw", m: 16, efConstruction: 64, similarity: "COS", dimensions: 1536 } }] });

  console.log(`seed ok: ${upserted} inserted, ${matched} already present, ${duplicates} duplicate-key ignored`);
} finally {
  await client.close();
}
```

**Correct: `seed.py` skeleton** (same steps, PyMongo)

```python
import os, sys, time
from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError

DB_NAME = os.environ["DATABASE_NAME"]
CHUNK = int(os.environ.get("SEED_CHUNK_SIZE", "1000"))
if not DB_NAME.startswith("sample_") and "--confirm" not in sys.argv:
    sys.exit(f'Refusing to seed "{DB_NAME}": pass --confirm to write to a non-sample database')

client = MongoClient(os.environ["DOCUMENTDB_URI"])               # connection string from env
coll = client[DB_NAME]["patients"]
coll.create_index([("patient_id", 1)], unique=True, name="patients_patient_id_unique")  # before the load

def run_bulk(ops, attempt=0):
    try:
        return coll.bulk_write(ops, ordered=False)
    except BulkWriteError as e:
        errs = e.details.get("writeErrors", [])
        failed = [w for w in errs if w["code"] != 11000]           # 11000 = already present, fine for a seed
        if not failed:
            return e.details
        if attempt >= 2:
            raise
        time.sleep(0.5 * 2 ** attempt)                             # retrywrites=false: retry here, not in the driver
        return run_bulk([ops[w["index"]] for w in failed], attempt + 1)

docs = list(generate_patients())                                  # patient_id derived from data, not uuid4()
for i in range(0, len(docs), CHUNK):
    run_bulk([UpdateOne({"patient_id": d["patient_id"]}, {"$set": d}, upsert=True) for d in docs[i:i + CHUNK]])

coll.create_index([("region", 1), ("age", 1)], name="patients_region_age")             # after the load
```

**Batch / nightly jobs** (a short section in the same rule): iterate with `find(filter).sort("_id", 1).batch_size(500)`. Save the last processed `_id` as a high-water mark, so that a restart resumes with `{"_id": {"$gt": marker}}`. Cap concurrency (`asyncio.Semaphore(8)` or `p-limit`) so a job cannot drain the connection pool. Pass `allowDiskUse=True` on aggregations whose `$group`, `$facet` or `$sort` stage runs over unbounded input. Do not reuse the `16500` / `429` "rate limited" codes from RU-based Cosmos DB guidance. Azure DocumentDB has no request-unit throttling, so retry on transient network, failover and timeout errors instead.

**References**: the MongoDB Node.js driver `Collection.bulkWrite` and `MongoBulkWriteError`; PyMongo `bulk_write` and `BulkWriteError.details`; the kit's own `index-single-field` (natural key with `unique`) and `vector-search/vector-choose-index-type.md` (which index kinds can be built on an empty collection). The rule must state the number[] requirement and the create-after-load ordering itself, because the vector-search skill does not spell them out today.

### 2. Register it

In `skills/driver/SKILL.md`:

```markdown
- [driver-bulk-load-idempotent-seed](driver-bulk-load-idempotent-seed.md) — Seed / import / nightly-job pattern: unique index on the natural key first, deterministic ids, chunked unordered `bulkWrite` upserts, other indexes after the load, `writeErrors` inspection (tolerate 11000, retry the rest because `retrywrites=false`), resumable `batch_size` cursor loops, DB-name guard + `--confirm`, `allowDiskUse` for heavy aggregations.
```

Widen the front matter `description` so the rule actually triggers by appending *"…bulk loading, seed scripts, imports and batch jobs (chunked `bulkWrite`, idempotent upserts, partial-failure handling)."* Also add a one-line pointer from `skills/local-deployment/local-sample-data-management.md`, at the "Idempotent scripts only" bullet, to the new rule.

### 3. CHANGELOG

Add one entry under a new dated heading: "Add `driver-bulk-load-idempotent-seed` rule with reference seed.js / seed.py."

Related, separate follow-ups: `skills/connection/SKILL.md` shows `retryWrites=true` in its connection-string example (line 60), and its `withRetry` helper keys on `16500` / `429` RU throttling codes. Both contradict Azure DocumentDB behaviour (`retrywrites=false`, no RUs) and are worth fixing in their own PR. `CONTRIBUTING.md` also still points at `skills/documentdb-best-practices/rules/` and a `metadata.json` that no longer exist.

## Evidence (run folders)

- `runs/16-population-health-dashboard-backend/20261124-195348/05-audit.json`: 5 indexes before 5,000 single upserts; `allowDiskUse=False`; "RU charge" wording
- `runs/10-support-ticket-rag-assistant/20261124-204529/05-audit.json`: per-document upsert loop at `app/seed.py:69-74`
- `runs/10-multi-tenant-storefront-saas/20261124-184121/05-audit.json`: `Order.create()` beside upserts, duplicates on rerun
- `runs/02-real-time-event-stream-ingestion/20261124-203233/doc-gaps.md`: `[high]` bulk-write partial-failure handling; `writeErrors` dropped
- `runs/19-insider-threat-detection-pipeline/20261124-202818/05-audit.json`: `replace_one` per document; nightly loop over `find({})` with no `batch_size` or resume marker
- `runs/19-cross-sell-recommendation-beanie/20261125-055705/05-audit.json`: `save()` per document

🤖 Generated with [Claude Code](https://claude.com/claude-code)

## Verification

### 1. Already covered? partially_covered
- `skills/driver/SKILL.md` lists only `driver-singleton-client`, and its description covers client and pool use, not loading data.
- `skills/local-deployment/local-sample-data-management.md:63` has a small `insertMany`, and line 72 says "Idempotent scripts only". The goal is stated but no pattern is given: no chunking, upserts on a natural key, `writeErrors` handling or index ordering. It also sits in the local-deployment skill, where an agent writing a seed for an Azure cluster does not look.
- A grep of `skills/` and `knowledge-base/` for `bulkWrite|bulk_write|insert_many|writeErrors|allowDiskUse` finds no other hits (`fts-create-search-index.md` matches "bulk" only in passing).
- `skills/connection/SKILL.md:209-237` has a generic `withRetry` helper, but it is not about bulk writes and keys on RU codes.
- Microsoft Learn: `https://learn.microsoft.com/en-us/azure/documentdb/how-to-optimize-write-performance`, `.../best-practices` and `.../optimize-write-performance` return HTTP 404. A Learn search API query for "documentdb bulk write performance" returns no Azure DocumentDB page. The RU-based page `https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/optimize-write-performance` returns 200, which is consistent with the agent landing there.

### 2. Is the premise true? confirmed, with corrections applied
- The evidence checks out against the run files. `16-population-health` audit text includes "reduce overhead and RU charge compared to many single inserts" and the `allowDiskUse` topic. `10-support-ticket` says "seed.py upserts documents one-by-one in a loop (app/seed.py lines 69-74)". `10-multi-tenant` cites `Order.create` at `seed.js` lines 25-31. `19-insider-threat` cites `replace_one(..., upsert=True)` and a fix to use `.batch_size()` with a last_processed marker. `19-cross-sell` cites `await pp.save()`. The `02-real-time` doc-gaps entry is `[high] Bulk-write partial-failure handling`. The idempotent-seed requirement appears in all 100 audits.
- Corrections applied to the body:
  - **Sample count.** The draft said 12 samples. Only 11 distinct samples are verifiable from the cited run folders, so the body now says "at least 11".
  - **Node.js `writeErrors`.** `MongoBulkWriteError.writeErrors` can be a single `WriteError` rather than an array (`OneOrMore<WriteError>` typing). The skeleton now normalises it with `[].concat(...)`.
  - **JS skeleton.** It used an undefined `client` and an undeclared `duplicates`. Both are now declared, and the client is closed in `finally`.
  - **Unique-index rationale.** The draft said the unique index "is what makes the upsert idempotent". An upsert filtered on a deterministic key is already idempotent when runs happen one after another. The index keeps the filter fast and turns a plain insert or a concurrent rerun into an 11000 error instead of a duplicate row. The text is corrected.
  - **Kit references.** The draft said the kit's vector-search skill documents "number[] requirement, create vector index after load". It does not: `vector-choose-index-type.md` only notes HNSW "can be built on empty collections". The rule now states both points itself.
  - **Retry angle added.** Azure DocumentDB connection strings use `retrywrites=false`, so application-level retry of failed bulk operations is needed. The body also warns against the `16500` / `429` RU codes found in `skills/connection/SKILL.md`.
- The `cosmosSearch` createIndexes syntax (`kind: "vector-hnsw"`, `m`, `efConstruction`, `similarity: "COS"`, `dimensions`) matches the documented Azure DocumentDB vector index options. Capacity is vCore M-tiers, not RUs.

### 3. Maintainer skeptic: confirmed
The PR names exact files: a new `skills/driver/driver-bulk-load-idempotent-seed.md`, plus edits to `skills/driver/SKILL.md`, `local-sample-data-management.md` and `CHANGELOG.md`. It follows the existing rule layout and has concrete code. The Azure DocumentDB-specific content goes beyond generic hygiene: `retrywrites=false` requires retry in the application, the vector index is created after the load and must be stored as number[], the agent drifted to RU-based guidance, and no Learn page covers this. It belongs in Azure/documentdb-agent-kit, not documentdb-mcp or Learn, since Learn has no page for it and the agent read the kit. Accepted with the small edits above. The batch-job section could be split into a follow-up if the maintainer wants a smaller PR.

## Finding ids
F0031, F0204, F0281, F1616, F1708, F1676, F2737, F2770, F2772, F3007, F3249, F3286, F3288, F3101
