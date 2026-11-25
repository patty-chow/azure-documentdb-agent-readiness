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
open_questions: 3
---

# data-modeling skill: collection setup with $jsonSchema validators, Decimal128 money, BSON dates, and idempotent atomic writes

## What happens today

`skills/data-modeling/SKILL.md` has five rules: embed-vs-reference, 16 MB limit, denormalize reads, schema versioning, large-field split. Nothing in the skill tells an agent what to do when it **creates a collection** or **writes a business record**:

- No `$jsonSchema` validator guidance. Azure DocumentDB supports validators through `createCollection`/`collMod` (`validationLevel`, `validationAction`), with a subset of keywords. The kit has no mention of it.
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
- **Supported keywords:** `bsonType`, `required`, `properties`, `items`, `minItems`/`maxItems`, `minimum`/`maximum`, `minLength`/`maxLength`, `pattern`, and others. Link the Learn keyword table: https://learn.microsoft.com/en-us/documentdb/query/operators/evaluation-query/$jsonschema . Constrain string values with `pattern` (see Open questions on `enum`).
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

Store timestamps as BSON `Date` (UTC), never as strings or local time. TTL indexes only expire `Date` values. Query with `$gte`/`$lt` ranges. Bucket by local time with `$dateTrunc`/`$dateToParts` and a `timezone` argument. In compound indexes, put the date field after the equality fields (ESR order, see `indexing`).

### 5. New `data-modeling/model-immutable-audit-records.md` (MEDIUM)

Ledger and audit collections are append-only, with `createdAt`, `createdBy`, a source reference and `schemaVersion`. They never get a TTL index; expiring data goes in a separate collection. Corrections are compensating entries, not updates. For merges or LLM-assisted decisions, write a provenance document (`run_id`, inputs, scores, model and prompt version, `created_at`) to its own collection, and keep or soft-delete the originals.

### 6. New `data-modeling/model-agent-memory.md` (HIGH for agent/chatbot samples)

Use two collections. `raw_turns` holds one document per turn, with a validator, a TTL index on `createdAt` (for example 7 days) and an index on `{ sessionId: 1, createdAt: -1 }`. `long_term_summaries` holds compacted summaries with `embedding` (number[], never BSON binary), `embedding_model`, `embedding_dims`, `sourceTurnIds`, `createdAt` and `schemaVersion`, plus a `cosmosSearch` vector index. Recall is the last N turns plus the top-k vector hits. Compact into `long_term_summaries` when a session exceeds N turns or closes. If the memory holds regulated data (PHI, PII), store a canonical id instead of the raw text and say so in the README. Reference https://learn.microsoft.com/en-us/azure/cosmos-db/gen-ai/agentic-memories for the short-term/long-term pattern only, and state that its partition-key, container-TTL, VectorDistance and RU guidance is for Cosmos DB for NoSQL and does not apply here.

### 7. New `data-modeling/model-idempotent-atomic-writes.md` (HIGH)

Use draft 102's rule text as is, with one change: replace its first sentence ("Azure DocumentDB does not support retryable writes ...") with "The documented connection string sets `retrywrites=false`, so do not count on the driver to retry writes. Every retry your application issues must be safe to repeat." Do not state whether the service supports retryable writes (see Open questions). Sections:

- Unique index on the business key, partial when the key is optional, with a note to test partial unique indexes on your cluster.
- Upsert with `$setOnInsert` for create-once fields such as `createdAt`.
- One atomic `findOneAndUpdate` instead of find → mutate → `save()`: version in the filter, `$inc` the version, `$push` with `$slice`. Include a Beanie example covering `get_motor_collection()` in 1.x and `get_pymongo_collection()` in 2.x, and a Mongoose guarded decrement.
- A version-in-filter retry loop, with the statement that Azure DocumentDB has no `_etag`/`If-Match`.
- `withTransaction` only for multi-document changes, with external side effects kept outside the callback (it may run more than once).
- Side effects only after `upsertedCount === 1`.
- Inspect `bulkWrite` `writeErrors`, treating E11000 as "already applied".
- Validate LLM output (type, enum and range) before `$set`, and append it to a capped history array with the model id.

### 8. `data-modeling/model-16mb-limit.md`

Add "State machines and workflow history": cap every `$push` into `transitions`/`history`/`stateHistory` in the same update (`$each: [t], $slice: -100`), or write the full record to a side collection in the same session. Do not write "audit collection omitted for brevity".

### 9. `data-modeling/model-schema-versioning.md`

Add: "Write `schemaVersion` on every insert and seed document. For pipeline-produced fields, also `$set` `processing_status`, `last_updated`, `embedding_model` and `embedding_dims`, so a crashed run can resume." Cross-link `vector-search/vector-normalize-embeddings`.

### 10. `indexing/index-ttl-expiry.md`

Add one line: "TTL suits short-lived operational logs, not ledgers or compliance audit trails. See data-modeling/model-immutable-audit-records."

### 11. `driver/SKILL.md`

Add one Rules line pointing to `documentdb-data-modeling › model-idempotent-atomic-writes` for retry-safe and concurrent writes.

Not in this PR: the `retryWrites` values in `connection/SKILL.md`, `driver/driver-singleton-client.md` and `security/security-tls-required.md` are handled in a separate connection-string PR. A suggested `query-optimization` rule on `$setWindowFields` support is also left for a follow-up. The suggestion that finance sample prompts require Decimal128 belongs to the experiment harness (abinav2307/azure-documentdb-agent-readiness), which is a colleague's repository; coordinate that with them rather than filing it here. The same applies to fixing the generated 02-swift sample itself (adopt Decimal128, or add a README precision caveat); re-running it after this rule lands should produce that without a manual edit.

## Evidence

- `runs/03-core-banking-transaction-ledger/20261124-200452/05-audit.json`: `amount`/`balance` as `Number` with `$inc`. The data-modeling skill was loaded.
- `runs/02-swift-message-parser-store/20261124-200226/app/app/models.py`: `amount: Optional[float]`, summed with `$sum`.
- `runs/09-lead-scoring-agent/20261124-204408/05-audit.json`: no validator and no TTL on `engagement_signals`.
- `runs/15-digital-onboarding-orchestration/20261124-202211/05-audit.json`: unbounded `$push` history.
- `runs/11-preference-center-consent-store/20261124-204614/05-audit.json`: find-mutate-save. The audit attributes optimistic concurrency to this skill.
- `runs/08-dynamic-segmentation-engine/20261124-204222/05-audit.json`: `_etag`/`If-Match` recommended from the Cosmos DB NoSQL page.

## Open questions

1. [needs SME confirmation] The Learn `$jsonSchema` page lists `enum` (and `additionalProperties`, `allOf`/`anyOf`/`oneOf`/`not`, `patternProperties`, `min/maxProperties`, `dependencies`) as unsupported. Is that current? The rule uses `pattern`, which works either way. If `enum` is supported, the rule should say so.
2. [needs SME confirmation] Retryable writes. The documented connection string uses `retrywrites=false`. One source draft and part of the kit (`azure-deployment/SKILL.md`) say Azure DocumentDB does not support retryable writes. Other analysis from the same experiment notes that Learn does not clearly state this. What is the engineering answer, and why does the canonical string set `retrywrites=false`? This PR's wording deliberately avoids taking a position.
3. [needs SME confirmation] Learn says partial indexes do not support `UNIQUE` "unless the filter qualifies". Is `{ unique: true, partialFilterExpression: { key: { $exists: true } } }` accepted? If it is not, the rule should tell agents to make the key required instead.

## Source drafts

- 104-data-model-governance-missing-no-jsonschema-validators-or-sc.md
- 071-swift-message-sample-stores-monetary-amounts-as-float-withou.md
- 123-data-modeling-document-design-conventions-and-query-patterns.md
- 102-write-path-integrity-non-idempotent-and-non-atomic-writes-in.md
