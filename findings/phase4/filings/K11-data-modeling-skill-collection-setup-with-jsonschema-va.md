---
id: K11
title: "data-modeling skill: collection setup with $jsonSchema validators, Decimal128 money, BSON dates, and idempotent atomic writes"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P1
sample_count: 46
member_drafts:
  - 104-data-model-governance-missing-no-jsonschema-validators-or-sc.md
  - 071-swift-message-sample-stores-monetary-amounts-as-float-withou.md
  - 123-data-modeling-document-design-conventions-and-query-patterns.md
  - 102-write-path-integrity-non-idempotent-and-non-atomic-writes-in.md
open_questions: 1
---

# data-modeling skill: collection setup with $jsonSchema validators, Decimal128 money, BSON dates, and idempotent atomic writes

## What happens today

`skills/data-modeling/SKILL.md` has five rules: embed-vs-reference, 16 MB limit, denormalize reads, schema versioning, large-field split. Nothing in the skill tells an agent what to do when it **creates a collection** or **writes a business record**:

- No `$jsonSchema` validator guidance. Azure DocumentDB supports validators through `createCollection`/`collMod` (`validationLevel`, `validationAction`) with a subset of keywords, as a preview feature (Learn release notes, 2025-10-10). On a new cluster they work with no enablement step (managed test, 2026-11-25); a cluster where the feature is still gated answers `CommandNotSupported` "validator not supported yet" (reported on an older cluster in a May 2026 Q&A thread). The kit mentions neither the feature nor the error.
- No field-type guidance. Nothing says to store money as Decimal128 or integer minor units (`grep -ri decimal128 skills/` returns nothing) or to store timestamps as BSON `Date`.
- No lifetime decision per collection. TTL appears only as an index type in `skills/indexing/index-ttl-expiry.md`, and that file lists "short-lived audit logs" as a TTL use case with no warning against TTL on ledgers or compliance audit trails.
- `$push`/`$each`/`$slice` appears only once, as an optional snippet in `model-16mb-limit.md`. It is not applied to state-machine history. `schemaVersion` is presented as a migration aid, not something to write on every insert. Nothing covers persisting agent memory.
- Nothing covers retry-safe or concurrent writes. The only conditional update in the kit is the migration example in `model-schema-versioning.md`. Agents that look elsewhere end up on the Cosmos DB for NoSQL page and suggest `_etag`/`If-Match`, which Azure DocumentDB does not have.

## Why it matters

We ran 100 Azure DocumentDB sample prompts through a coding agent (gpt-5-mini) with this kit installed, then had a separate step audit each sample. **46 distinct samples (72 audit findings)** hit one of the gaps above. These counts come from one experiment run and may shift on a re-run. Patterns that came up repeatedly:

- **Money as doubles.** Every finance sample that was audited for monetary types (SWIFT parser, core-banking ledger, invoice reconciliation, Basel III) typed amounts as `float`/`Number` and ran `$inc`/`$sum` on them. No generated sample used Decimal128.
- **No validators.** Collections were created implicitly by `insertMany`. Mongoose subdocuments were left as `Mixed`. Nothing on the server enforced the embedding dimension.
- **No TTL, or TTL in the wrong place.** Collections the samples themselves described as ephemeral (run history, signal feeds, agent memory) never expired. The ledger sample needed a note that ledgers must not get TTL.
- **Unbounded history.** Every state transition was `$push`ed with no `$slice`. Conversation memory was kept in a process `Map`.
- **Unsafe writes.** Samples used `insertOne` with no unique business key, ran find → mutate → `save()` with no version check, rewrote `createdAt` under `$set` on upsert, did multi-document merges without a transaction, swallowed `bulkWrite` errors, and `$set` unvalidated LLM output as truth.
- The audit attributed "atomic updates" and "optimistic concurrency" to this skill and could not find them there. The core-banking run loaded the data-modeling skill twice and still skipped every one of these practices.

## Proposed change

All paths are under `skills/`. Each file is edited once.

### 1. `data-modeling/SKILL.md`

Insert after "Rules":

~~~markdown
## Collection setup checklist (do this for every new collection)

Collections created implicitly by the first insert get none of these guards. Create them explicitly (`createCollection`, or `collMod` if the collection exists) in the seed/setup script:

1. **Validator.** Add a `$jsonSchema` validator for required fields and types. See [model-schema-validation](model-schema-validation.md).
2. **Field types.** Money: Decimal128 or integer minor units. Time: BSON `Date` (UTC). See [model-monetary-values](model-monetary-values.md) and [model-dates-bson-utc](model-dates-bson-utc.md).
3. **`schemaVersion`.** Write it on every insert. See [model-schema-versioning](model-schema-versioning.md).
4. **Lifetime.** Logs, caches, run history, roll-ups, signal feeds and short-term memory get a TTL index plus a one-line retention note in the README. Ledgers and audit trails never get TTL. See [model-immutable-audit-records](model-immutable-audit-records.md) and `indexing/index-ttl-expiry`.
5. **Arrays.** Cap any array that grows per event with `$push`/`$each`/`$slice`, or move it to a side collection. See [model-16mb-limit](model-16mb-limit.md).
6. **Business key.** Add a unique index on the business key before loading data, and write with an upsert. See [model-idempotent-atomic-writes](model-idempotent-atomic-writes.md).
7. **Agent memory.** Use two collections, not an in-process map. See [model-agent-memory](model-agent-memory.md).
~~~

Add the six new files to the Rules list. Extend the `description` with: "…schema validation ($jsonSchema), field types for money (Decimal128) and time (BSON Date), TTL/retention vs immutable ledgers and audit trails, bounded history arrays, agent-memory persistence, idempotent and atomic writes (upsert on a business key, optimistic concurrency, transactions, bulkWrite errors, persisting LLM output). Use when writing a seed or setup script, handling amounts or balances, or storing logs, ledgers or agent memory."

### 2. New `data-modeling/model-schema-validation.md` (HIGH)

- **Why it matters:** Implicit collections accept any document shape. A validator rejects bad ids, timestamps, status values and wrong-length embedding arrays at the server. A vector whose length does not match the index `dimensions` silently produces wrong results (see `vector-search/vector-create-diskann-index`).
- **Preview status:** Collection validators are a preview feature (Learn release notes, 2025-10-10: "[Preview] Add schema validation support for $jsonSchema during rule creation or modification"). On a new cluster they work with no `previewFeatures` entry, feature registration or configuration step (managed test, 2026-11-25: M30, server version 8.0, engine 2.2-1/2.3.0). On a cluster where the feature is still gated (a Microsoft Q&A thread from May 2026 reported it on an older 8.0 M20 cluster), `createCollection`/`collMod` with `validator`, `validationLevel` or `validationAction` fails with `CommandNotSupported` "validator not supported yet" (engine `pg_documentdb/src/metadata/collection.c`, EnableSchemaValidation gate). The setup script must catch that error, log that validators are not enabled on the cluster, and continue; Learn documents no enablement path for such clusters. Validation applies to `insert`, `update`, `findAndModify` and the `$merge`/`$out` stages, and `bypassDocumentValidation` skips it (Learn compatibility page).
- **Supported keywords:** `bsonType`, `required`, `properties`, `items`, `minItems`/`maxItems`, `minimum`/`maximum`, `minLength`/`maxLength`, `pattern`, and others. Link the Learn keyword table: https://learn.microsoft.com/en-us/documentdb/query/operators/evaluation-query/$jsonschema . Not supported: `additionalProperties`, `allOf`/`anyOf`/`not`, `patternProperties`, `dependencies`, `minProperties`/`maxProperties`, `$ref`, `$schema`, `format`, `default`; `type: "integer"` and dot-notation property paths are rejected, so use `bsonType: "int"`/`"long"` and nested `properties`. On the managed service the rejected keywords fail with code 9 ("is not supported at this time", observed for `$schema`, `format` and `type: "integer"`), and `title` and `description` are accepted. Schemas generated from Pydantic or zod usually contain `anyOf` and `additionalProperties`, so translate them rather than passing them through. `enum` and `oneOf` are accepted and enforced on current clusters (a managed cluster created on 2026-11-25, and documentdb-local 0.117 and 1.2.0), although Learn's `$jsonSchema` page still lists them as unsupported, so `enum` is fine there. Clusters on older engine builds may reject them with code 9 ("Unknown $jsonSchema keyword"), so code that must run on any cluster can use `pattern` for strings (a keyword Learn lists as supported; the tests did not exercise it) or a query-operator validator with `$in`, and should handle code 9 at create time; the example below uses `pattern` for that reason.
- **Errors:** a violating insert or update returns write error 121 with no `codeName` or `errInfo`; a violating `findAndModify` fails with code 121 and codeName `DocumentFailedValidation` (MongoDB's name is `DocumentValidationFailure`), so match on the code, not the name. `validationAction: "warn"` accepts the violating write, and the open-source engine skips validation entirely in that mode, so it probably logs nothing: do not use it to audit (managed test, 2026-11-25).
- **Incorrect:** `await db.collection("leads").insertMany(docs)` with no validator.
- **Correct:**

```javascript
const validator = { $jsonSchema: { bsonType: "object",
  required: ["leadId", "createdAt", "schemaVersion", "embedding"],
  properties: {
    leadId: { bsonType: "string" }, createdAt: { bsonType: "date" },
    schemaVersion: { bsonType: "int" },
    status: { bsonType: "string", pattern: "^(new|qualified|lost)$" },
    embedding: { bsonType: "array", items: { bsonType: "double" }, minItems: 1536, maxItems: 1536 } } } };
const exists = await db.listCollections({ name: "leads" }).hasNext();
if (!exists) await db.createCollection("leads", { validator, validationLevel: "strict", validationAction: "error" });
else await db.command({ collMod: "leads", validator, validationLevel: "strict", validationAction: "error" });
```

Add the PyMongo equivalent (`create_collection(..., validator=...)`, `command("collMod", ...)`). For Mongoose, define real subdocument schemas instead of `Schema.Types.Mixed`, and add a note that Mongoose schemas do not replace the server-side validator, because Mongoose validation runs only for writes that go through Mongoose.

### 3. New `data-modeling/model-monetary-values.md` (HIGH; merges 071, 104, 123)

- **Why it matters:** `float`/`Number` are IEEE-754 doubles, so `$inc`/`$sum` accumulate rounding error. Azure DocumentDB stores BSON Decimal128 natively and supports `$toDecimal`/`$convert`.
- **Incorrect:** `amount: { type: Number }`, `amount: Optional[float]`, `$inc: { balance: -25.10 }`.
- **Correct:** mongosh `NumberDecimal("12.34")`. Mongoose `mongoose.Schema.Types.Decimal128` (add a getter that returns a string, with `toJSON: { getters: true }`). Node `Decimal128.fromString("-25.10")` as the `$inc` operand. PyMongo `Decimal128(Decimal("25.10"))`. Beanie `DecimalAnnotation`. Alternatively, store integer minor units (`amountMinor: 2510`, `bsonType: "long"`) with a `currency` field. Show the legacy-coercion pattern: `{ $sum: { $toDecimal: "$amount" } }`, and apply `$toDecimal` before `$multiply`/`$divide` in aggregations.
- **Rules:** Parse incoming amounts straight to Decimal, never through `float()`/`parseFloat()`. Use a Decimal128 operand for `$inc` on a Decimal128 field. Return amounts as strings or minor-unit integers. Use one representation per field. Decimal128 and integer fields index and sort like any scalar; equality queries on a Decimal128 field must also use Decimal128 values. If a sample keeps floats for brevity, say so in the README and the decision log, and name Decimal128 as the production choice.
- **References:** https://learn.microsoft.com/en-us/azure/documentdb/compatibility-query-language, https://learn.microsoft.com/en-us/documentdb/query/operators/aggregation/$todecimal and the BSON spec.

### 4. New `data-modeling/model-dates-bson-utc.md` (MEDIUM)

Store timestamps as BSON `Date` (UTC), never as strings or local time. TTL indexes are single-field and only expire BSON `Date` values: numbers, strings and missing fields are never deleted, and expiry lags by up to about a minute (engine `ttl_index.c` and `create_indexes.c`; Learn release notes 2025-10-10). The managed test of 2026-11-25 saw one purge a minute, at the top of the minute, so with no backlog a document goes 0 to about 60 seconds after it becomes eligible (large backlogs untested); it also saw a compound TTL index rejected (67) and, of the values tested, only BSON Dates, including an array holding a past Date, expire. Query with `$gte`/`$lt` ranges. Bucket by local time with `$dateTrunc`/`$dateToParts` and a `timezone` argument. In compound indexes, put the date field after the equality fields (ESR order, see `indexing`).

### 5. New `data-modeling/model-immutable-audit-records.md` (MEDIUM)

Ledger and audit collections are append-only, with `createdAt`, `createdBy`, a source reference and `schemaVersion`. They never get a TTL index; expiring data goes in a separate collection. Corrections are compensating entries, not updates. For merges or LLM-assisted decisions, write a provenance document (`run_id`, inputs, scores, model and prompt version, `created_at`) to its own collection, and keep or soft-delete the originals.

### 6. New `data-modeling/model-agent-memory.md` (HIGH for agent/chatbot samples)

Use two collections. `raw_turns` holds one document per turn, with a validator, a TTL index on `createdAt` (for example 7 days) and an index on `{ sessionId: 1, createdAt: -1 }`. `long_term_summaries` holds compacted summaries with `embedding` (number[], never BSON binary), `embedding_model`, `embedding_dims`, `sourceTurnIds`, `createdAt` and `schemaVersion`, plus a `cosmosSearch` vector index. Recall is the last N turns plus the top-k vector hits. Compact into `long_term_summaries` when a session exceeds N turns or closes. If the memory holds regulated data (PHI, PII), store a canonical id instead of the raw text and say so in the README. Reference https://learn.microsoft.com/en-us/azure/cosmos-db/gen-ai/agentic-memories for the short-term/long-term pattern only, and state that its partition-key, container-TTL, VectorDistance and RU guidance is for Cosmos DB for NoSQL and does not apply here.

### 7. New `data-modeling/model-idempotent-atomic-writes.md` (HIGH)

Use draft 102's rule text as is. Its first sentence ("Azure DocumentDB does not support retryable writes ...") is correct; replace it with the canonical one-liner from `findings/phase4/DECISIONS.md`: "Keep `retrywrites=false` in every Azure DocumentDB connection string. The service does not support retryable writes: the server does not de-duplicate a retried write, so a driver retry can apply a non-idempotent write twice. Handle transient write failures in application code with idempotent operations (upserts, deterministic keys)." Follow it with: "Every retry your application issues must be safe to repeat." Cite documentdb/documentdb#767 for the de-duplication gap. Do not claim that `retryWrites=true` causes connection errors; that is not established. Sections:

- Unique index on the business key, created before loading data (expect a unique index build to block writes). When the key is optional, use `{ unique: true, partialFilterExpression: { key: { $exists: true } } }`: the engine accepts unique partial indexes whose filter uses `$exists: true`, `$gt`-style comparisons, exact `$type`, top-level `$and`/`$or` or `$in` with scalars; it rejects `$exists: false` and mixing `partialFilterExpression` with `sparse` (engine `create_indexes.c` and regression tests; Learn's indexing page says only "unless the filter qualifies").
- Upsert with `$setOnInsert` for create-once fields such as `createdAt`.
- One atomic `findOneAndUpdate` instead of find → mutate → `save()`: version in the filter, `$inc` the version, `$push` with `$slice`. Include a Beanie example covering `get_motor_collection()` in 1.x and `get_pymongo_collection()` in 2.x, and a Mongoose guarded decrement.
- A version-in-filter retry loop, with the statement that `_etag`/`If-Match` belong to Cosmos DB for NoSQL: optimistic concurrency on Azure DocumentDB is an application pattern (own version field in the update filter), not a service feature.
- `withTransaction` only for multi-document changes, kept well inside the 30-second transaction lifetime (Learn limitations; on the service transactions ended 30 to 41 s after they started, busy or idle, and their writes were discarded), with no `createIndexes` or other DDL inside it (refused with code 263) and no explicit `readConcern`/`writeConcern` in the transaction options. The service returns `WriteConflict` (code 112) and `NoSuchTransaction` (251) without the `TransientTransactionError` label (documentdb/documentdb#339, #836), so `withTransaction` does not retry them: catch 112 and 251 (and code 1 `InternalError` from a statement after an idle gap, after which the commit returned 251) and re-run the whole transaction in application code with bounded attempts and backoff; a code 1 from the commit itself was never observed, so check with a read before re-running. With the default read concern a transaction's reads are not repeatable (a second read can see a concurrent commit), so a read-modify-write inside it can still lose a concurrent update: keep the version-in-filter guard on any write that depends on a read (managed test and documentdb-local). Keep external side effects outside the callback, because that re-run executes it again.
- Side effects only after `upsertedCount === 1`.
- Inspect `bulkWrite` `writeErrors`, treating E11000 as "already applied", and chunk `insertMany`/`bulkWrite` at or below 25,000 writes per request (Learn limitations: batches over 25,000 writes fail; `hello.maxWriteBatchSize` is 25,000 on the service, so drivers split larger `insert_many`/`bulkWrite` calls themselves, while a raw command over the cap fails with 16 `InvalidLength`). Collection-level `bulkWrite()` works; the compatibility page's `bulkWrite: No` row is the MongoDB 8.0 database-level command, which client-level bulk writes (`MongoClient.bulk_write`) send: on an 8.0 cluster PyMongo's fails at run time with code 2, so do not use them.
- Validate LLM output (type, enum and range) before `$set`, and append it to a capped history array with the model id.

### 8. `data-modeling/model-16mb-limit.md`

Add "State machines and workflow history": cap every `$push` into `transitions`/`history`/`stateHistory` in the same update (`$each: [t], $slice: -100`), or write the full record to a side collection in the same session. Do not write "audit collection omitted for brevity".

### 9. `data-modeling/model-schema-versioning.md`

Add: "Write `schemaVersion` on every insert and seed document. For pipeline-produced fields, also `$set` `processing_status`, `last_updated`, `embedding_model` and `embedding_dims`, so a crashed run can resume." Cross-link `vector-search/vector-normalize-embeddings`.

### 10. `indexing/index-ttl-expiry.md`

Add one line: "TTL suits short-lived operational logs, not ledgers or compliance audit trails. See data-modeling/model-immutable-audit-records." Also correct lines 12, 42 and 92 (and the matching `~60s` on `indexing/index-pattern-cookbook.md:238`): "a background thread deletes expired documents roughly every 60 seconds" matches the cadence the managed test of 2026-11-25 saw (one purge a minute, at the top of the minute; DECISIONS.md topic 10, item 5), though not the mechanism; write "expired documents are deleted once a minute, so with no backlog expiry lags by up to about a minute" and cite that observation (a backlog larger than one run deletes was not tested), the Learn release note of 2025-10-10 (TTL deletions run continuously for up to 60 seconds, preview) and the engine source for the single-field and Date-only rules, since Learn has no TTL page.

### 11. `driver/SKILL.md`

Add one Rules line pointing to `documentdb-data-modeling › model-idempotent-atomic-writes` for retry-safe and concurrent writes.

Not in this PR: the `retryWrites: true` values in `connection/SKILL.md`, `driver/driver-singleton-client.md` and `security/security-tls-required.md` must become `retrywrites=false` (retryable writes are not supported; see `findings/phase4/DECISIONS.md`) and are handled in a separate connection-string PR. A suggested `query-optimization` rule on `$setWindowFields` support is also left for a follow-up. The suggestion that finance sample prompts require Decimal128 belongs to the experiment harness (abinav2307/azure-documentdb-agent-readiness), which is a colleague's repository; coordinate that with them rather than filing it here. The same applies to fixing the generated 02-swift sample itself (adopt Decimal128, or add a README precision caveat); re-running it after this rule lands should produce that without a manual edit.

## Evidence

- `runs/03-core-banking-transaction-ledger/20261124-200452/05-audit.json`: `amount`/`balance` as `Number` with `$inc`. The data-modeling skill was loaded.
- `runs/02-swift-message-parser-store/20261124-200226/app/app/models.py`: `amount: Optional[float]`, summed with `$sum`.
- `runs/09-lead-scoring-agent/20261124-204408/05-audit.json`: no validator and no TTL on `engagement_signals`.
- `runs/15-digital-onboarding-orchestration/20261124-202211/05-audit.json`: unbounded `$push` history.
- `runs/11-preference-center-consent-store/20261124-204614/05-audit.json`: find-mutate-save. The audit attributes optimistic concurrency to this skill.
- `runs/08-dynamic-segmentation-engine/20261124-204222/05-audit.json`: `_etag`/`If-Match` recommended from the Cosmos DB NoSQL page.

## Resolved

retryWrites: answered 2026-11-25, see findings/phase4/DECISIONS.md. Retryable writes are not supported; retrywrites=false is required; the server does not de-duplicate retried writes (documentdb/documentdb#767).

`enum` and the other keywords Learn lists as unsupported: Learn's list is stale for `enum` and `oneOf`, which the open-source engine's main branch parses (`enum` merged 2026-07-23, `oneOf` merged 2026-07-16) and a managed cluster created on 2026-11-25 enforces (managed test; clusters on older engine builds may reject them with code 9 "Unknown $jsonSchema keyword"); `pattern` remains a valid constraint. `additionalProperties`, `allOf`, `anyOf`, `not`, `patternProperties`, `dependencies`, `minProperties` and `maxProperties` still fail ("Unknown $jsonSchema keyword" in the open-source engine; code 9 on the managed service for the keywords tested). Collection validators are a preview (release notes 2025-10-10) that worked on a new cluster with no enablement step; a cluster where the feature is still gated returns `CommandNotSupported` "validator not supported yet". Sources: ENGINE-TESTS.md, Managed service; https://learn.microsoft.com/en-us/documentdb/query/operators/evaluation-query/$jsonschema ; https://learn.microsoft.com/en-us/azure/documentdb/release-notes ; https://learn.microsoft.com/en-us/azure/documentdb/compatibility-query-language ; engine `pg_documentdb/src/jsonschema/bson_json_schema_tree.c` and `pg_documentdb/src/metadata/collection.c` (findings/phase4/DECISIONS.md, topic 10).

Partial unique index with `$exists: true`: accepted. The engine creates unique indexes with a `partialFilterExpression` and allows `$exists` in the filter when its value is true (also `$gt`-style comparisons, exact `$type`, top-level `$and`/`$or`, scalar `$in`), and rejects `$exists: false` and mixing `partialFilterExpression` with `sparse`; Learn's "unless the filter qualifies" is undefined and is a Learn fix, not a rule change. The managed test of 2026-11-25 saw the same behaviour on the service (`$exists: false` rejected with 67, `sparse` with a partial filter with 197). Sources: engine `pg_documentdb/src/commands/create_indexes.c` and regression tests `commands_create_indexes_background_unique_tests.out` and `bson_aggregation_stage_merge_tests.out`; https://learn.microsoft.com/en-us/azure/documentdb/indexing (findings/phase4/DECISIONS.md, topic 10).

Engine build and validator enablement (former open question 1): answered for a new cluster by the managed test of 2026-11-25. The cluster (M30, server version 8.0, created that day) reported engine `2.2-1`/`2.3.0`; validators worked with no `previewFeatures` entry, feature registration or configuration step; `enum` and `oneOf` were accepted and enforced; `title` and `description` were accepted; `$schema`, `format` and `type: "integer"` failed with code 9. Older clusters may still be gated (a Microsoft Q&A thread from May 2026 reported "validator not supported yet" on an 8.0 M20 cluster), so the setup script keeps its catch-and-continue branch. Sources: ENGINE-TESTS.md, Managed service; DECISIONS.md topic 10, item 1.

## Open questions

1. [needs SME confirmation] What remains of former open question 1: can existing clusters still be gated (the May 2026 Microsoft Q&A report of "validator not supported yet" on an 8.0 M20 cluster) or run an engine build that rejects `enum` and `oneOf` (code 9), and if so, what is the self-serve path to enable collection validators on them? DECISIONS.md topic 10 keeps this part open. Not blocking: the setup script catches the error, logs it and continues, and the rule handles code 9 at create time; only what the log message tells the user to do depends on the answer.

## Source drafts

- 104-data-model-governance-missing-no-jsonschema-validators-or-sc.md
- 071-swift-message-sample-stores-monetary-amounts-as-float-withou.md
- 123-data-modeling-document-design-conventions-and-query-patterns.md
- 102-write-path-integrity-non-idempotent-and-non-atomic-writes-in.md
