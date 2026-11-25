---
title: "data-modeling: add \"idempotent and atomic writes\" rule (upsert on business key, $setOnInsert, version-in-filter, withTransaction, bulkWrite 11000, LLM output as untrusted input)"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 18
findings: 23
bucket: sample-violated-practice
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# data-modeling: add "idempotent and atomic writes" rule

## What happens today

`skills/data-modeling/SKILL.md` lists five rules: embed-vs-reference, 16 MB limit, denormalize-reads, schema-versioning, large-field-split. None of them says how to *write* a business record so that a retried request, a change-stream replay, a re-run seed, or a second concurrent worker does not duplicate or clobber it. The only conditional update in the whole kit is the `updateOne({ _id, schemaVersion: 1 }, ...)` inside `model-schema-versioning.md`, and it is there for migration, not for concurrency.

Azure DocumentDB does not support retryable writes; the service connection string sets `retrywrites=false`, and the kit already says so in `skills/azure-deployment/SKILL.md` (lines 288-291: "Azure DocumentDB does not support retryable writes"). Every retry is therefore an application-level retry, so business-key idempotency is the only thing standing between a transient error and a duplicate claim, return, outreach send or ledger event.

Note that the kit is inconsistent here: `skills/connection/SKILL.md` line 60 shows `retryWrites=true` in its canonical connection string, and `skills/driver/driver-singleton-client.md` line 26 and `skills/security/security-tls-required.md` line 26 pass `retryWrites: true`. This PR changes those three to `retrywrites=false` / `retryWrites: false` so the new rule and the connection guidance agree.

## Why it matters

In a 100-sample run (gpt-5-mini, kit skills + DocumentDB/Azure/Learn MCP), **18 samples** produced 23 audit findings on this theme. The agent wrote exactly the code the kit does not warn against:

- `insertOne` / `Model.create` with no unique index or upsert on the business key (`claimId`, `returnId`, `eventId`, `transactionRef`, merge-id): 18-chargeback-dispute-multi-agent, 18-returns-refund-workflow-orchestration, 16-loyalty-points-ledger, 20-identity-resolution-multi-agent.
- External side effect (outreach send) with no prior existence check and no unique index on `eventId`: 19-proactive-outreach-orchestration.
- ODM find → mutate → `save()` in two steps for consent history + version bump (Beanie) and refill save + separate `refillCount` decrement (Mongoose), no version in the filter: 11-preference-center-consent-store, 15-prescription-refill-agent.
- `createdAt` under `$set` on an upsert, so it is rewritten on every refresh: 16-population-health-dashboard-backend.
- Version assigned by `find().sort().limit(1)` then `insert_one`: 16-multi-touch-attribution-model.
- Summary recomputed by `aggregate` and overwritten with `$set` on every heartbeat instead of `$inc` deltas: 16-atm-network-status-monitor.
- Multi-document CDP merge (update + delete) with no `withTransaction`: 18-360-data-platform-cdp-orchestration.
- `bulkWrite` exception caught wholesale, `writeErrors` never inspected, E11000 not recognised as the expected idempotency signal: 20-interest-accrual-batch-processor.
- LLM-produced `clv_score` / `clv_tier` cast and `$set` as top-level truth with no enum/range check and no history: 12-clv-prediction-pipeline.
- Unique index on an optional field without `partialFilterExpression`: 03-core-banking-transaction-ledger.

Two second-order effects show the gap is in the kit, not just the model:

1. The auditor **attributed** "atomic single-document updates" and "optimistic concurrency with a version in the filter" to `skills/data-modeling/SKILL.md` (run 11, discovery_id P09/P10), i.e. it expected the practice to live there and could not find it.
2. Where it kept searching it landed on the **Cosmos DB NoSQL** page and recommended `_etag` + `If-Match` (run 08, P13, source `learn.microsoft.com/azure/cosmos-db/database-transactions-optimistic-concurrency`). Six of 106 audits mention ETag/If-Match. DocumentDB has no `_etag`; the equivalent is a version field in a conditional update. The kit should say so in one line so the model stops importing the NoSQL-API concept.

Run 11's `doc_gaps` asked for exactly this: "atomic findOneAndUpdate operations using Beanie ... optimistic concurrency patterns that show how to use a consentVersion field in the update filter".

## Proposed change

### 1. New rule file `skills/data-modeling/model-idempotent-atomic-writes.md`

```markdown
# model-idempotent-atomic-writes

**Category:** Data Modeling · **Priority:** HIGH

## Why it matters

Azure DocumentDB does not support retryable writes (the connection string sets
`retrywrites=false`), so every retry is one your application issues. A retried POST, a replayed change-stream event,
a re-run seed or a second worker will insert a duplicate, or overwrite a newer state,
unless the write itself is idempotent and atomic. DocumentDB has no `_etag` /
`If-Match` (that is the Cosmos DB NoSQL API); optimistic concurrency here is a
version field in the update filter.

## Incorrect

```javascript
// 1. Duplicate on retry: nothing stops a second decision for the same claim
await decisions.insertOne({ claimId, outcome, createdAt: new Date() });

// 2. Read-modify-write: two requests both read version 3, both save version 4
const c = await Consent.findOne({ customerId });
c.history.push(entry); c.consentVersion += 1; await c.save();

// 3. createdAt rewritten on every refresh
await summaries.updateOne({ _id: key }, { $set: { ...doc, createdAt: now } }, { upsert: true });

// 4. Side effect before the record exists
await sendEmail(customer); await outreachLogs.insertOne({ eventId, ... });

// 5. bulkWrite failure swallowed; duplicate-key and network error treated alike
try { await coll.bulkWrite(ops) } catch (e) { console.error(e) }

// 6. LLM output written as truth
await customers.updateOne({ _id }, { $set: { clv_tier: llm.tier, clv_score: Number(llm.score) } });
```

## Correct

**Unique index on the business key, created in the seed/index script before data is
loaded.** Partial when the key is optional (a plain unique index treats every missing field
as the same `null`). Learn notes that partial indexes support `UNIQUE` only when the filter
qualifies, so test the partial unique index on your cluster; if it is rejected, make the key
required instead.

```javascript
await decisions.createIndex({ claimId: 1 }, { unique: true });
await txns.createIndex({ transactionRef: 1 },
  { unique: true, partialFilterExpression: { transactionRef: { $exists: true } } });
```

**Upsert on the business key; `$setOnInsert` for create-once fields.**

```javascript
// Node driver
const r = await decisions.updateOne(
  { claimId },
  { $set: { outcome, decidedAt: new Date() },
    $setOnInsert: { createdAt: new Date(), schemaVersion: 1 } },
  { upsert: true });
```
```python
# pymongo
res = coll.update_one(
    {"_id": key},
    {"$set": {"summary": summary, "expiresAt": expires_at},
     "$setOnInsert": {"createdAt": now, "params": params}},
    upsert=True)
```

**One atomic update instead of find → mutate → save.** `$inc` the version, `$push` with
`$each` + `$slice` to cap history (see model-16mb-limit).

```python
# Beanie: bypass the document save() path for the hot write
# (Beanie 1.x: get_motor_collection(); Beanie 2.x: get_pymongo_collection())
doc = await Consent.get_motor_collection().find_one_and_update(
    {"customerId": cid, "consentVersion": expected_version},   # version in filter
    {"$set": {"channels": channels},
     "$inc": {"consentVersion": 1},
     "$push": {"history": {"$each": [entry], "$slice": -200}}},
    return_document=ReturnDocument.AFTER)
if doc is None:
    raise Conflict("consent changed concurrently; re-read and retry")
```
```javascript
// Mongoose: guarded decrement, no refill when none left
const p = await Prescription.findOneAndUpdate(
  { _id: prescriptionId, refillCount: { $gt: 0 } },
  { $inc: { refillCount: -1 } }, { new: true });
if (!p) throw new Error("no refills remaining");
```

**Version-in-filter retry loop (optimistic concurrency on DocumentDB).**

```javascript
for (let attempt = 0; attempt < 3; attempt++) {
  const cur = await profiles.findOne({ customerId });
  const next = computeSegment(cur);
  const r = await profiles.updateOne(
    { customerId, version: cur.version },
    { $set: { segment: next }, $inc: { version: 1 } });
  if (r.matchedCount === 1) return;
}
throw new Error("lost update race after 3 attempts");
```

**Two documents that must change together: `withTransaction`.** Keep it short; most
cases above are single-document and need no transaction. The driver can run the callback
more than once, so keep external side effects (emails, payments, API calls) outside it.

```javascript
await client.withSession(s => s.withTransaction(async () => {
  await refills.insertOne({ refillId, prescriptionId }, { session: s });
  await prescriptions.updateOne({ _id: prescriptionId, refillCount: { $gt: 0 } },
                                { $inc: { refillCount: -1 } }, { session: s });
}));
```

**Side effects only after the insert succeeded.**

```javascript
const r = await outreachLogs.updateOne({ eventId },
  { $setOnInsert: { eventId, customerId, status: "pending", createdAt: new Date() } },
  { upsert: true });
if (r.upsertedCount === 1) await sendEmail(customer);   // replay: upsertedCount 0, no send
```

**Inspect `BulkWriteResult`; E11000 is the idempotency signal, not a failure.**

```javascript
try {
  await ledger.bulkWrite(ops, { ordered: false });
} catch (e) {
  if (e.code !== 11000 && !e.writeErrors) throw e;          // transient: let the caller retry
  const real = (e.writeErrors ?? []).filter(w => w.code !== 11000);
  if (real.length) throw new AggregateError(real, "non-duplicate write errors");
  // all remaining errors were duplicates: already applied, nothing to do
}
```

**LLM outputs are untrusted input.** Validate type, enum and range; truncate free text;
append to a history array with the model id; derive the "latest" fields from it.

```python
TIERS = {"low", "medium", "high", "vip"}
tier = str(out.get("tier", "")).lower()
score = float(out.get("score"))
if tier not in TIERS or not (0 <= score <= 1000):
    raise ValueError("LLM output out of contract")
customers.update_one({"_id": cid}, {
    "$push": {"clv_history": {"$each": [{"at": now, "score": score, "tier": tier,
              "rationale": str(out.get("rationale", ""))[:500], "model": MODEL_ID}],
              "$slice": -50}},
    "$set": {"clv_score": score, "clv_tier": tier}})
```

## References

- Group multiple operations in transactions in Azure DocumentDB:
  https://learn.microsoft.com/azure/documentdb/how-to-transactions
- Indexes on Azure DocumentDB (partial indexes and their `UNIQUE` limitation):
  https://learn.microsoft.com/azure/documentdb/indexing
  and this kit's `indexing/index-single-field.md`, `indexing/index-pattern-cookbook.md`
- Companion rules: `model-schema-versioning.md` (conditional update for migration),
  `model-16mb-limit.md` (`$slice` to cap arrays)
```

### 2. Register it in `skills/data-modeling/SKILL.md`

Add to **Rules**:

```markdown
- [model-idempotent-atomic-writes](model-idempotent-atomic-writes.md) — Upsert on a unique business key, `$setOnInsert` / `$inc` / `$push`+`$slice` in one atomic update, version-in-filter instead of `_etag`, `withTransaction` only for multi-document changes, E11000 as the idempotency signal, LLM output validated before `$set`.
```

Extend the frontmatter `description` so the skill triggers on write-path questions, e.g. append: `..., making writes idempotent and atomic (retry-safe inserts, upsert on a business key, concurrent writers, optimistic concurrency, transactions, bulkWrite error handling, persisting LLM output).`

### 3. Fix the `retryWrites` inconsistency

Change `retryWrites=true` to `retrywrites=false` in `skills/connection/SKILL.md` line 60, and `retryWrites: true` to `retryWrites: false` in `skills/driver/driver-singleton-client.md` line 26 and `skills/security/security-tls-required.md` line 26, matching `skills/azure-deployment/SKILL.md` line 288.

### 4. One-line pointer in `skills/driver/SKILL.md`

Under Rules: `- For retry-safe and concurrent writes (upsert on a business key, version-in-filter, withTransaction, bulkWrite 11000) see documentdb-data-modeling › model-idempotent-atomic-writes.`

## Evidence (run folders, 100-sample experiment, 2026-11-24)

- `runs/11-preference-center-consent-store/20261124-204614/05-audit.json` — checks P09/P10 cite data-modeling/SKILL.md as the source for atomic updates + optimistic concurrency; `doc_gaps` asks for Beanie `find_one_and_update` + consentVersion-in-filter example.
- `runs/08-dynamic-segmentation-engine/20261124-204222/05-audit.json` — check P13 recommends `_etag` / `If-Match` from the Cosmos DB NoSQL page.
- `runs/18-chargeback-dispute-multi-agent/20261124-192501/05-audit.json` — P21: `insertOne` decision with no upsert on `claimId`.
- `runs/19-proactive-outreach-orchestration/20261124-205844/05-audit.json` — outreach send with no existence check or unique `eventId`.
- `runs/20-interest-accrual-batch-processor/20261124-202826/05-audit.json` — bulkWrite exception swallowed, 11000 not handled.
- `runs/12-clv-prediction-pipeline/20261124-204841/05-audit.json` — LLM `clv_tier`/`clv_score` `$set` unvalidated, no history.
- `runs/16-population-health-dashboard-backend/20261124-195348/05-audit.json` — `createdAt` under `$set` on upsert.

## Verification

### 1. Already covered? confirmed (not there)

- `skills/data-modeling/SKILL.md` lists exactly five rules (embed-vs-reference, 16 MB, denormalize-reads, schema-versioning, large-field-split); none covers idempotent or atomic writes. A grep of `skills/` and `knowledge-base/` for idempotent, `$setOnInsert`, upsert, `withTransaction`, optimistic, 11000/E11000, `_etag` and untrusted finds no write-safety guidance. The hits are unrelated: `storage/storage-disk-hydration-sequencing.md:96` ("Idempotent retry with exponential backoff") is about disk hydration, `local-deployment/local-sample-data-management.md:72` says only "Idempotent scripts only", and `natural-language-querying/SKILL.md:19` treats tool output as untrusted, which is not LLM output written to the database.
- The only conditional update is `model-schema-versioning.md:31` (`updateOne({ _id: doc._id, schemaVersion: 1 }, ...)`), which is there for migration, as the draft says. `partialFilterExpression` appears in `indexing/index-single-field.md` and `index-pattern-cookbook.md`, but never alongside `unique` on a business key.
- microsoft/documentdb-mcp: the only hit is `$setOnInsert` in the operator allow-list in `src/tools/utils/paramParser.ts:186`. It has no guidance, and that repo is not the right place for it.
- Learn: https://learn.microsoft.com/en-us/azure/documentdb/how-to-transactions documents `withTransaction` but not business-key idempotency or optimistic concurrency.

### 2. Premise true? confirmed (one detail corrected)

- One claim was wrong and has been corrected in the body. The draft said `skills/connection/SKILL.md` line 60 sets `retrywrites=false`. In fact it shows `retryWrites=true`, as do `driver/driver-singleton-client.md:26` and `security/security-tls-required.md:26`. Only `azure-deployment/SKILL.md:288-291` uses `retrywrites=false` and says "Azure DocumentDB does not support retryable writes". The core argument still holds, because retries are app-level on this service. The body now cites the correct file and adds a step that fixes the inconsistency.
- Transactions: Learn how-to-transactions confirms multi-document ACID transactions with `startSession()`/`withTransaction()`, and warns that the callback "can run more than once if the driver retries the transaction. Avoid non-idempotent external side effects in the callback." This guidance is now in the rule.
- Partial indexes: https://learn.microsoft.com/en-us/azure/documentdb/indexing supports `partialFilterExpression`, with the limitation that partial indexes "don't support ORDER BY or UNIQUE unless the filter qualifies". The rule now says to test partial unique indexes. The draft's original reference, how-to-index, does not cover unique or partial indexes, so the reference was replaced.
- DocumentDB (vCore) has no `_etag`/If-Match; that comes from the Cosmos DB NoSQL API. A version field in the update filter is the correct pattern. Six of 106 audits mention ETag/If-Match (verified by grep). In run 08 the audit says "include _etag/If-Match semantics". In run 11 the audit attributes these practices to data-modeling/SKILL.md (verified).
- The Beanie snippet now notes that Beanie 2.x renamed `get_motor_collection()` to `get_pymongo_collection()`.
- `$push` with `$each`/`$slice`, `$setOnInsert`, `$inc`, `findOneAndUpdate`, unordered `bulkWrite` and E11000 duplicate-key errors are standard MongoDB wire-protocol behavior that DocumentDB supports. No contradiction found.

### 3. Maintainer skeptic: confirmed

The PR names exact files (a new `skills/data-modeling/model-idempotent-atomic-writes.md`, plus `data-modeling/SKILL.md`, `driver/SKILL.md` and the three `retryWrites` lines) and follows the kit's rule format (why it matters, incorrect, correct, references). It has a clear DocumentDB angle: no retryable writes, no `_etag`, the partial-unique limitation, and `withTransaction` callback re-runs. It is backed by 18 samples. One possible concern is scope: the LLM-output-validation section is closer to generic hygiene. It is acceptable because it is short and tied to `$set` on DocumentDB, but a maintainer may ask to trim it. The PR belongs in Azure/documentdb-agent-kit.

## Finding ids

- F0342
- F0376
- F1190
- F1191
- F1218
- F1882
- F1883
- F1884
- F2040
- F2011
- F2012
- F2612
- F2673
- F2676
- F2704
- F2738
- F2771
- F3001
- F3065
- F3097
- F3352
- F3387
- F3420
