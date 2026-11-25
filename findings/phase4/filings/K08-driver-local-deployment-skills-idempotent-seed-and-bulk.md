---
id: K08
title: "driver/local-deployment skills: idempotent seed and bulk-load rule with reference seed scripts"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P1
sample_count: 15
member_drafts:
  - 103-seed-and-batch-load-scripts-are-per-document-loops-not-idemp.md
  - 053-documentdb-local-deployment-skill-lacks-an-idempotent-seed-s.md
open_questions: 6
---

# driver/local-deployment skills: idempotent seed and bulk-load rule with reference seed scripts

## What happens today

Nothing in the kit shows an agent how to write a seed script, an import or a batch job for Azure DocumentDB.

- `skills/local-deployment/local-sample-data-management.md` says "Idempotent scripts only", but its own *Correct* example is an `insertMany` with fixed `_id: 1` / `_id: 2`. Run it a second time against a populated database (a manual `mongosh` run, CI, or the same code reused in an app seed) and it fails with E11000. The image runs `INIT_DATA_PATH` scripts only on a fresh volume, so the problem is the pattern the example teaches, not the container.
- `skills/driver/SKILL.md` has one rule (`driver-singleton-client`), and its description does not mention seeding or bulk loading. An agent writing `seed.py` has no reason to open it.
- A grep of `skills/` and `knowledge-base/` for `bulkWrite`, `bulk_write`, `insert_many`, `writeErrors` or `allowDiskUse` returns no hits, and `insertMany` appears only in that one example. Nothing covers chunking, natural-key upserts, partial-failure handling, index ordering, a sample fixture with a licence, or demo dataset size.
- `scenarios/contoso/contoso-seed.js` already follows the right contract: it is resumable, uses a seeded PRNG and needs an opt-in drop. No skill links to it. `scenarios/ecommerce/seed.sh` drops collections every time it runs and uses unseeded `Math.random()`.
- Microsoft Learn has no Azure DocumentDB bulk-write page (`.../azure/documentdb/how-to-optimize-write-performance` and `.../best-practices` return 404). Agents end up on the request-unit-based Cosmos DB page and copy its "RU charge" wording. Azure DocumentDB capacity is sized by vCore tier, not request units.

## Why it matters

We ran one experiment: gpt-5-mini, with this kit and the DocumentDB, Azure and Learn MCP servers, built 100 sample apps. Every prompt asked for a seed script that loads data, creates the index and can run twice without duplicating data. The counts below come from that single run and may change on a re-run.

- **15 distinct samples** are cited in the member drafts' evidence: 12 show a concrete seeding or bulk-load defect in their run folders, and 3 more (an earnings-call RAG assistant, a store locator and a customer-journey mapper) report that no skill gave them a seed dataset, a licence, a dataset size or a chunk-id scheme. The model knew the seed had to be idempotent and reached for `upsert: true`, but without a pattern to follow it:
  - wrote loops of single `update_one` / `replace_one` / `save()` calls (one sample made 5,000 single upserts);
  - mixed upserts with plain inserts or random ids, so every rerun added duplicate rows (an ATM monitor upserted status documents but created a new heartbeat on every run);
  - created every secondary index before the load;
  - caught `MongoBulkWriteError` and dropped `writeErrors`;
  - iterated nightly jobs over `find({})` with no batch size or resume marker;
  - seeded destructively with no check on the database name;
  - set `allowDiskUse=False` on a faceted aggregation.
- Every builder invented its own idempotency contract and dataset size (5 stores, 20 ATMs, 500 to 2,000 events), so the samples are inconsistent with each other.
- A seed is usually the first thing a developer runs against a new cluster. If it is slow or doubles its data, the service looks broken.

## Proposed change

### 1. New file `skills/driver/driver-bulk-load-idempotent-seed.md` (priority HIGH, same layout as `driver-singleton-client.md`)

> **Why it matters.** Seeds, imports and nightly jobs are the largest writes most apps make. One upsert per document costs one round trip each. A seed that is not keyed on a natural key duplicates data when rerun. A bulk error that is logged and dropped hides lost writes.
>
> **Contract.**
> 1. Give every document a deterministic natural key (or a stable string `_id`), never `Math.random()` or `uuid4()`.
> 2. Create a unique index on that key **before** the load. It keeps the upsert filter fast and turns a stray plain insert or a concurrent rerun into E11000 instead of a duplicate row.
> 3. Write in chunks (about 1,000) with unordered `bulkWrite` upserts.
> 4. Read `writeErrors`. Treat 11000 as "already present" and retry the other errors with backoff. The Azure DocumentDB connection string sets `retrywrites=false`, so the driver does not retry writes and the script must retry for itself. [needs SME confirmation: the reason for `retrywrites=false`, see Open question 1]
> 5. Create secondary, text and `cosmosSearch` vector indexes **after** the load [needs SME confirmation for each vector kind, see Open question 3]. Give every index an explicit name; `createIndex` is a no-op when the same definition already exists, so the script stays re-runnable. Store embeddings as `number[]`.
> 6. Never drop by default. Use an opt-in `--reset` flag (or `SEED_RESET=true`), and refuse non-`sample_` databases unless `--confirm` is passed.
> 7. Finish with a count check and exit non-zero on a mismatch.
> 8. For chunked RAG ingestion, upsert on `chunk_id = sha1(source_id + ":" + chunk_index)`.

**Incorrect** (generated):

```python
patients.create_index([("diagnoses", 1)])          # secondary indexes before the load
for i in range(1, 5001):
    patients.update_one({"patient_id": f"P{i}"}, {"$set": gen_patient(i)}, upsert=True)  # 5,000 round trips
```

**Correct: `seed.js`**

```javascript
import { MongoClient, MongoBulkWriteError } from "mongodb";
const DB_NAME = process.env.DATABASE_NAME;
const CHUNK = Number(process.env.SEED_CHUNK_SIZE ?? 1000);
if (!/^sample_/.test(DB_NAME) && !process.argv.includes("--confirm"))
  throw new Error(`Refusing to seed "${DB_NAME}": pass --confirm for a non-sample database`);
const client = new MongoClient(process.env.DOCUMENTDB_URI);   // from env, never hard-coded
const db = client.db(DB_NAME), products = db.collection("products");
let duplicates = 0;

async function runBulk(coll, ops, attempt = 0) {
  try { return await coll.bulkWrite(ops, { ordered: false }); }
  catch (err) {
    if (!(err instanceof MongoBulkWriteError)) throw err;
    const writeErrors = [].concat(err.writeErrors ?? []);      // may be one WriteError or an array
    const failed = writeErrors.filter(e => e.code !== 11000);
    duplicates += writeErrors.length - failed.length;
    if (failed.length === 0) return err.result;
    if (attempt >= 2) throw err;
    await new Promise(r => setTimeout(r, 500 * 2 ** attempt));
    return runBulk(coll, failed.map(e => ops[e.index]), attempt + 1);
  }
}

try {
  if (process.argv.includes("--reset")) await products.drop().catch(() => {});
  await products.createIndex({ productId: 1 }, { unique: true, name: "products_productId_unique" });
  const docs = generateProducts();                             // productId derived from data
  for (let i = 0; i < docs.length; i += CHUNK)
    await runBulk(products, docs.slice(i, i + CHUNK).map(d => ({
      updateOne: { filter: { productId: d.productId }, update: { $set: d }, upsert: true } })));
  await products.createIndex({ category: 1, price: -1 }, { name: "products_category_price" });
  await db.command({ createIndexes: "products", indexes: [{ name: "products_vec", key: { embedding: "cosmosSearch" },
    cosmosSearchOptions: { kind: "vector-hnsw", m: 16, efConstruction: 64, similarity: "COS", dimensions: 1536 } }] });
  const n = await products.countDocuments();
  console.log(`seeded ${n} products (${duplicates} duplicate-key ignored)`);
  if (n !== docs.length) process.exitCode = 1;
} finally { await client.close(); }
```

The HNSW values above (`m: 16`, `efConstruction: 64`) are placeholders. [needs SME confirmation: supported HNSW and IVF limits, see Open question 4]

**Correct: `seed.py`**

```python
import os, sys, time
from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError

DB_NAME = os.environ["DATABASE_NAME"]
CHUNK = int(os.environ.get("SEED_CHUNK_SIZE", "1000"))
if not DB_NAME.startswith("sample_") and "--confirm" not in sys.argv:
    sys.exit(f'Refusing to seed "{DB_NAME}": pass --confirm for a non-sample database')

def run_bulk(coll, ops, attempt=0):
    try:
        return coll.bulk_write(ops, ordered=False)
    except BulkWriteError as e:
        failed = [w for w in e.details.get("writeErrors", []) if w["code"] != 11000]
        if not failed:
            return e.details
        if attempt >= 2:
            raise
        time.sleep(0.5 * 2 ** attempt)        # retrywrites=false: retry here
        return run_bulk(coll, [ops[w["index"]] for w in failed], attempt + 1)

with MongoClient(os.environ["DOCUMENTDB_URI"]) as client:
    coll = client[DB_NAME]["patients"]
    if "--reset" in sys.argv:
        coll.drop()
    coll.create_index([("patient_id", 1)], unique=True, name="patients_patient_id_unique")
    docs = list(generate_patients())          # patient_id derived from data
    for i in range(0, len(docs), CHUNK):
        run_bulk(coll, [UpdateOne({"patient_id": d["patient_id"]}, {"$set": d}, upsert=True)
                        for d in docs[i:i + CHUNK]])
    coll.create_index([("region", 1), ("age", 1)], name="patients_region_age")
    n = coll.count_documents({})
    print(f"seeded {n} patients")
    sys.exit(0 if n == len(docs) else 1)
```

> **Batch and nightly jobs.** Iterate with `find(filter).sort("_id", 1).batch_size(500)`. Save the last `_id` so that a restart resumes from `{"_id": {"$gt": marker}}`. Cap concurrency (`asyncio.Semaphore(8)` or `p-limit`). Pass `allowDiskUse=True` to `$group`, `$facet` or `$sort` over unbounded input. Retry on transient network, failover and timeout errors. Do not copy the request-unit throttling logic (16500 / 429) from Cosmos DB RU guidance. [needs SME confirmation: whether vCore can return 16500 or 429, see Open question 2]
>
> **Local and Azure.** The same script runs against the local Gateway container and an Azure DocumentDB cluster; only `DOCUMENTDB_URI` changes (see `local-env-driven-config`). The local URI carries the TLS relaxation for the self-signed certificate; the Azure URI uses `tls=true` with SCRAM-SHA-256 or Entra ID.
>
> **References.** Node.js `Collection.bulkWrite` / `MongoBulkWriteError`; PyMongo `bulk_write` / `BulkWriteError.details`; `index-single-field`; `vector-search/vector-choose-index-type.md`; `scenarios/contoso/contoso-seed.js` for a larger resumable example.

### 2. `skills/driver/SKILL.md`

Add to Rules: `- [driver-bulk-load-idempotent-seed](driver-bulk-load-idempotent-seed.md) — Seed, import and batch-job pattern: unique natural-key index first, chunked unordered bulkWrite upserts, writeErrors handling, indexes after load, opt-in reset, count check.` Append to the front-matter `description`: "…bulk loading, seed scripts, imports and batch jobs."

### 3. `skills/local-deployment/local-sample-data-management.md`

Replace the `insertMany` example with:

```javascript
// seed/10_data.js: safe to re-run, upserts on the natural key
const users = db.getSiblingDB('app').users;
users.createIndex({ userId: 1 }, { unique: true, name: 'users_userId_unique' });
users.bulkWrite([
  { replaceOne: { filter: { userId: 'u-ada' },   replacement: { userId: 'u-ada',   name: 'Ada' },   upsert: true } },
  { replaceOne: { filter: { userId: 'u-linus' }, replacement: { userId: 'u-linus', name: 'Linus' }, upsert: true } }
], { ordered: false });
print('users: ' + users.countDocuments());   // 2 on every run
```

Under *Incorrect*, add: "`insertMany` with fixed `_id`s fails with E11000 on the second run. Without a unique key it silently doubles the data." At the "Idempotent scripts only" bullet, add: "See `driver/driver-bulk-load-idempotent-seed` for the full pattern." Then add this section:

> **Sizing a demo dataset** (rules of thumb): CRUD, REST and change-stream demos use 20 to 100 documents. Aggregation and dashboard demos use 1,000 to 10,000, generated from a seeded PRNG. Vector demos use 200 to 500 `number[]` vectors. Geospatial demos use 10 to 50 points in one city. Start from `seed/fixture.json`, which holds 12 synthetic products under the repository's licence. Each product has `sku`, `name`, `description`, `category`, `price`, `stock`, `updatedAt` and a GeoJSON `location`. Scale the fixture up with a generator function, not by hand-editing. `updatedAt` is stored as an ISO string in the fixture; convert it to a `Date` before writing if the app queries by date.

Add `skills/local-deployment/seed/fixture.json` (12 synthetic documents, no real people or places) in this PR.

### 4. `skills/local-deployment/SKILL.md` and `CHANGELOG.md`

Append to the `description`: "…idempotent seed scripts and demo dataset sizing." Add a CHANGELOG entry: "Add `driver-bulk-load-idempotent-seed` rule, fix non-idempotent seed example, add demo fixture."

Out of scope: the `retryWrites=true` example (`skills/connection/SKILL.md:60`) and the RU-code `withRetry` helper (`skills/connection/SKILL.md:224-230`) belong to the separate connection-string PR. `CONTRIBUTING.md` still points at `skills/documentdb-best-practices/rules/` and a `metadata.json` that no longer exist; that is a separate small fix. Optional follow-up: link the same seed pattern from the Learn quickstart "load sample data" sections (doc feedback, not this PR).

## Evidence

- `runs/16-population-health-dashboard-backend/20261124-195348/05-audit.json`
- `runs/10-multi-tenant-storefront-saas/20261124-184121/05-audit.json`
- `runs/02-real-time-event-stream-ingestion/20261124-203233/doc-gaps.md`
- `runs/16-atm-network-status-monitor/20261124-202405/doc-gaps.md`
- `runs/04-earnings-call-rag-assistant/20261124-190247/doc-gaps.md`
- `runs/20-store-locator-with-geospatial-search/20261124-185729/02-readiness.json`

## Open questions

1. [needs SME confirmation] **Retries.** The connection string sets `retrywrites=false`. The drafts disagree on why. One reading is that retryable writes are not supported by the service. The other is that they are only switched off in the documented string. Which is it, and should the rule tell scripts to retry in application code in either case?
2. [needs SME confirmation] Can vCore return 16500 or 429? The rule tells readers not to copy RU throttling logic.
3. [needs SME confirmation] Does creating `cosmosSearch` indexes after the load matter for each kind? In particular, does `vector-ivf` need data before it builds, and can HNSW be built on an empty collection?
4. [needs SME confirmation] Are the HNSW options in the skeleton (`m: 16`, `efConstruction: 64`) within the supported limits? Are binary (non-`number[]`) vectors ignored by `cosmosSearch`?
5. Should the rule live in `driver`, as proposed, or in `local-deployment`? Do the demo-size numbers suit the maintainers?
6. The sample count (15 = 11 from draft 103 plus 4 more from draft 053; the cross-sell sample appears in both) comes from the member drafts' evidence paths, not from their finding-id lists, which also include findings on unrelated topics (cold-quiz naming). The counts come from one run and may change after the harness fixes; re-check before quoting them publicly.

## Source drafts

- 103-seed-and-batch-load-scripts-are-per-document-loops-not-idemp.md
- 053-documentdb-local-deployment-skill-lacks-an-idempotent-seed-s.md
