---
title: "local-deployment skill: add idempotent seed-script template (Node + Python), tiny licensed fixture, and demo-size guidance; fix non-idempotent insertMany example"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 11
findings: 11
bucket: learn-information_gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# local-deployment: add an idempotent seed-script template, a tiny licensed fixture, and demo-size guidance (and fix the non-idempotent example)

## What happens today

`skills/local-deployment/local-sample-data-management.md` ends with the guideline **"Idempotent scripts only — they may re-run if the container volume is recreated."** But the page's own *Correct* example is:

```javascript
db.getSiblingDB('app').users.insertMany([
  { _id: 1, email: 'ada@example.com', name: 'Ada' },
  { _id: 2, email: 'linus@example.com', name: 'Linus' }
]);
```

Run it a second time against a database that already holds the data (a manual `mongosh` re-run, CI, or the same logic reused in an app-level seed) and it fails with `E11000 duplicate key error` on `_id`. (Strictly, the image runs `INIT_DATA_PATH` scripts only when it initialises a fresh data volume, so the "volume recreated" case starts from an empty database; the problem is that the example teaches a pattern that is not re-runnable anywhere else.) The rule and its own example disagree.

Beyond that, nothing an agent loads from this skill gives it:

- a reusable **idempotent seeding pattern** (deterministic key + `bulkWrite` upsert, optional drop-and-reload flag, verification count, dedupe for chunked RAG ingestion);
- an **example dataset with a licence statement** it can copy into a sample repo;
- a **rule of thumb for demo dataset size**.

The kit does ship seeders under `scenarios/`, and one of them is close to the right pattern: `scenarios/contoso/contoso-seed.js` is resumable ("does not drop"; inserts only the missing `_id`s so repeated runs converge), uses a seeded PRNG (`CONTOSO_SEED`, default 42) and has an opt-in `CONTOSO_FRESH=1` drop. `scenarios/ecommerce/seed.sh`, by contrast, drops collections unconditionally and uses unseeded `Math.random()`. Both are bash/mongosh scripts run against a local container to build large datasets for the diagnostics skills, and neither is referenced from the local-deployment skill, so an agent writing an app-level `seed.js` / `seed.py` against an Azure DocumentDB cluster never finds them. The new rule can point to `contoso-seed.js` as a larger worked example of the same contract.

## Why it matters

In a 100-sample experiment (gpt-5-mini building Azure DocumentDB sample apps with this kit installed), the samples carried the requirement *"a seed script loads sample data and creates the index, and can be run twice without duplicating data"*:

- In **90 of 120** readiness runs the information gaps mentioned the seed (size, idempotency or dataset content), several explicitly noting "documentdb-local-deployment shows how to seed data but does not supply a canonical example dataset or license" or "mentions sample-data scripts but not a recommended dataset size".
- In **48 of 117** audits the re-runnable-seed requirement was recorded as not fully met. Typical failure: the ATM monitor sample upserted status docs but `Heartbeat.create()` inside the loop duplicated heartbeats on every run while the README claimed idempotency; the Beanie cross-sell sample planned an idempotent seed and never wrote one; the earnings-call RAG sample had to invent its own `chunk_id` scheme and dedupe logic.
- Each builder designed its own idempotency contract and invented its own dataset size (5 stores, 20 ATMs, 500-2,000 events, ...), so the 100 samples are inconsistent with each other for no reason.

The 11 findings synthesised here are the ones that named this skill directly as where they looked.

## Proposed change (small PR, 3 files)

### 1. `skills/local-deployment/local-sample-data-management.md` — fix the example

Replace the `seed/10_data.js` `insertMany` block with:

```javascript
// seed/10_data.js — safe to re-run: upsert on the natural key
const users = db.getSiblingDB('app').users;
users.bulkWrite([
  { replaceOne: { filter: { email: 'ada@example.com' },   replacement: { email: 'ada@example.com',   name: 'Ada' },   upsert: true } },
  { replaceOne: { filter: { email: 'linus@example.com' }, replacement: { email: 'linus@example.com', name: 'Linus' }, upsert: true } }
], { ordered: false });
print('users: ' + users.countDocuments());   // expect 2 on every run
```

and add one sentence under *Incorrect*: `insertMany` with fixed `_id`s (or without a unique key) is **not** idempotent — the second run fails with a duplicate-key error or silently doubles the data.

### 2. New rule file `skills/local-deployment/local-idempotent-seed-scripts.md`

Suggested content (trimmed; happy to adjust tone to match the other rule files):

```markdown
# local-idempotent-seed-scripts

**Category:** Local Deployment · **Priority:** MEDIUM

## Why it matters
Sample apps get seeded many times: first run, after a container reset, in CI, and
by every reader who clones the repo. A seed that duplicates data on re-run breaks
tests, inflates dashboards and makes "verify against the cluster" meaningless.

## Contract — seed scripts must be safe to re-run
1. Every seeded document has a **deterministic key**: a stable `_id` (string) or a
   natural key with a unique index. Write with `bulkWrite` + `replaceOne(upsert)`.
2. Create indexes in the same script with explicit names; `createIndex` is
   idempotent when the definition matches.
3. Offer an opt-in `--reset` / `SEED_RESET=true` flag that drops the collection
   first. Never drop by default.
4. Finish with a count and exit non-zero if it differs from the fixture size.
5. For chunked ingestion (RAG): `chunk_id = sha1(source_id + ':' + chunk_index)`
   and upsert on it, so re-ingesting a document never duplicates chunks.

## Sizing your demo dataset
- CRUD / REST / change-stream demos: **20-100 documents** (one screen of output).
- Aggregation, reporting, dashboard demos: **1,000-10,000 documents**, generated
  deterministically from a seeded PRNG (no `Math.random()` without a seed).
- Vector-search demos: **200-500 vectors** — enough for a meaningful top-k,
  cheap to embed; vectors must be `number[]`, not BSON binary.
- Geospatial demos: 10-50 points within one city so `$geoNear` radii make sense.
Start from the fixture below and scale with a generator function, never by
hand-editing JSON.

## Fixture (synthetic, MIT — same licence as this repo; no real people or places)
12 documents in `seed/fixture.json`: each has `sku` (natural key), `name`,
`description` (text suitable for embedding), `category`, `price`, `stock`,
`updatedAt`, and `location` as a GeoJSON Point near Seattle. Example:

{ "sku": "SKU-0001", "name": "Trail Thermos 500ml",
  "description": "Double-walled steel bottle that keeps drinks hot for 12 hours.",
  "category": "outdoor", "price": 24.5, "stock": 40,
  "updatedAt": "2026-01-15T00:00:00Z",
  "location": { "type": "Point", "coordinates": [-122.3321, 47.6062] } }

## Correct — Node (mongodb driver)
Note: `fixture.json` stores `updatedAt` as an ISO string; convert to `Date` before writing if the app queries by date.
// seed/seed.js  — node seed/seed.js [--reset]
import { MongoClient } from 'mongodb';
import fixture from './fixture.json' with { type: 'json' };   // Node 22+ (or use fs.readFileSync + JSON.parse)
const uri = process.env.DOCUMENTDB_URI;            // never hard-code
if (!uri) throw new Error('DOCUMENTDB_URI is required');
const client = new MongoClient(uri);
const col = client.db(process.env.DATABASE_NAME ?? 'sample').collection('products');
if (process.argv.includes('--reset')) await col.drop().catch(() => {});
await col.bulkWrite(fixture.map(d => ({
  replaceOne: { filter: { sku: d.sku }, replacement: d, upsert: true } })), { ordered: false });
await col.createIndex({ sku: 1 }, { unique: true, name: 'sku_unique' });
await col.createIndex({ location: '2dsphere' }, { name: 'location_2dsphere' });
const n = await col.countDocuments();
console.log(`seeded ${n} products`);
if (n !== fixture.length) process.exit(1);
await client.close();

## Correct — Python (pymongo)
# seed/seed.py — python seed/seed.py [--reset]
import json, os, sys
from pymongo import MongoClient, ReplaceOne
uri = os.environ["DOCUMENTDB_URI"]                 # never hard-code
col = MongoClient(uri)[os.getenv("DATABASE_NAME", "sample")]["products"]
fixture = json.load(open("seed/fixture.json"))
if "--reset" in sys.argv: col.drop()
col.bulk_write([ReplaceOne({"sku": d["sku"]}, d, upsert=True) for d in fixture], ordered=False)
col.create_index("sku", unique=True, name="sku_unique")
col.create_index([("location", "2dsphere")], name="location_2dsphere")
n = col.count_documents({})
print(f"seeded {n} products")
sys.exit(0 if n == len(fixture) else 1)

Both scripts run unchanged against the local Gateway and an Azure DocumentDB
cluster; only `DOCUMENTDB_URI` changes (see local-env-driven-config; the local URI carries the TLS relaxation for the self-signed cert, the Azure URI uses `mongocluster.cosmos.azure.com` with `tls=true` and SCRAM-SHA-256 or Entra ID).
For a larger resumable, deterministic example see `scenarios/contoso/contoso-seed.js`.

## Incorrect
- `insertMany(fixture)` with no key: doubles the data on every run.
- `insertMany` with fixed `_id`: E11000 on the second run.
- `drop()` unconditionally at the top: destroys data a reader added while testing.
- `Math.random()` IDs or coordinates: tests cannot assert on results.
```

(The actual PR would include the full 12-document `fixture.json` next to the rule, or inline, whichever matches how the kit prefers to ship assets.)

### 3. `skills/local-deployment/SKILL.md`

- Add to the Rules list: `- [local-idempotent-seed-scripts](local-idempotent-seed-scripts.md) — Seed scripts must be safe to re-run: deterministic key + bulkWrite upsert, opt-in reset, count check; includes a Node/Python template, a 12-doc MIT fixture and demo-size guidance.`
- Append to the front-matter `description`: `..., idempotent seed-script template and demo dataset sizing. Use when ... writing the seed script for a sample app.` so the skill triggers when an agent is writing `seed.js` / `seed.py`.

Optional follow-up (not in this PR): link the same pattern from the Learn quickstart "load sample data" sections.

## Evidence (run folders from the experiment; no connection strings)

- `runs/16-atm-network-status-monitor/20261124-202405/doc-gaps.md` — [high] "Seed script idempotency for heartbeats": looked in seed.js and the documentdb-local-deployment skill, "no dedicated seed-idempotency template was present"; `05-audit.json` requirement `partly_met`.
- `runs/04-earnings-call-rag-assistant/20261124-190247/doc-gaps.md` — [high] "Idempotent seed-ingest pattern": "no small canonical example for idempotent chunked ingestion was found" in quickstarts or agent-kit skills.
- `runs/20-store-locator-with-geospatial-search/20261124-185729/02-readiness.json` — information_gaps "Seed dataset content and licensing": skill "does not supply a canonical example dataset or license"; builder invented 5 GeoJSON stores.
- `runs/19-cross-sell-recommendation-beanie/20261124-185532/05-audit.json` — seed requirement `not_met`: idempotent seed planned, never written.
- `runs/04-customer-journey-mapper/20261124-203553/02-readiness.json` and `runs/16-atm-network-status-monitor/20261124-202405/02-readiness.json` — "no skill or doc specified the recommended sample dataset size" (500-2,000 events? 20 or 100 ATMs?).

## Verification

### 1. Already covered? partially_covered
- `skills/local-deployment/local-sample-data-management.md` already states the rule ("Idempotent scripts only — they may re-run if the container volume is recreated.") but gives no template, and its only data example is `insertMany` with fixed `_id: 1`, `_id: 2`, which is not re-runnable.
- `skills/local-deployment/SKILL.md` lists seven rules; none covers seed idempotency, fixtures or dataset sizing. `local-prod-parity.md` only says "`seed/` data is local-only, `schema/` ... runs in every environment".
- grep for `idempot|bulkWrite|upsert` across `skills/` and `knowledge-base/` finds only that one guideline line (plus an unrelated retry note in `skills/storage/storage-disk-hydration-sequencing.md`).
- `scenarios/contoso/contoso-seed.js` already implements a resumable, seeded-PRNG, opt-in-drop seeder ("RESUMABLE: does not drop ... Set CONTOSO_FRESH=1 to drop first"), but it is a large diagnostics dataset and is not referenced from any skill. The draft now points to it rather than calling it drop-and-reload.
- No fixture with a licence statement and no demo-size guidance exists anywhere in the kit. Learn was not the target of this PR; the Learn link is left as an optional follow-up.

### 2. Premise true? confirmed (after corrections)
- `insertMany` with duplicate `_id` raises E11000 / BulkWriteError: standard MongoDB wire-protocol behaviour, which Azure DocumentDB follows. `bulkWrite` with `replaceOne` + `upsert`, `createIndex` with unique and `2dsphere`, and `$geoNear` are supported by Azure DocumentDB (Learn: MongoDB compatibility / geospatial pages under https://learn.microsoft.com/en-us/azure/documentdb/).
- Vector guidance ("vectors must be `number[]`, not BSON binary") matches the known cosmosSearch behaviour.
- Corrected: the draft called both scenario seeders "drop-and-reload ... use Math.random()". That holds only for `scenarios/ecommerce/seed.sh`; `scenarios/contoso/contoso-seed.js` is resumable and deterministic (CONTOSO_SEED default 42).
- Corrected: `INIT_DATA_PATH` scripts run when the image initialises a fresh volume, so the E11000 failure happens on a manual or app-level re-run, not literally on volume recreation. Reworded.
- Corrected: the experiment-wide counts ("81 of 100", "39 of 100") could not be reproduced. They were replaced with counts recomputed from the run folders: 90 of 120 `02-readiness.json` files mention the seed in information_gaps, and 48 of 117 `05-audit.json` files record the seed/re-run requirement as not fully met.
- Added: JSON import attributes need Node 22+, and the ISO-string `updatedAt` note.

### 3. Maintainer skeptic: confirmed
The draft names exact files (`local-sample-data-management.md`, a new `local-idempotent-seed-scripts.md`, `SKILL.md`) and concrete changes. It fixes a real inconsistency between the skill's rule and its example. The topic is a DocumentDB local-to-Azure workflow that already fits this skill's stated scope ("writing sample apps ... versioned seed and schema scripts"). The demo-size numbers are opinionated, but they are clearly labelled as rules of thumb, so a maintainer can edit them in review. Accept with small edits.

## Finding ids
- F0469
- F0537
- F0569
- F0738
- F0775
- F0831
- F2661
- F2723
- F2919
- F3471
- F3508
