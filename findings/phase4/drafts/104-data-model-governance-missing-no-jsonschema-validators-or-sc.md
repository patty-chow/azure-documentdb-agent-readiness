---
title: "data-modeling skill: add \"collection setup\" step with $jsonSchema validators, Decimal128 money rule, TTL-for-ephemeral rule, bounded-history shape and agent-memory template"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 22
findings: 27
bucket: sample-violated-practice
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# data-modeling: add a "collection setup" step — $jsonSchema validators, Decimal128 for money, TTL for ephemeral collections, bounded history, agent-memory template

## What happens today

`skills/data-modeling/SKILL.md` lists five rules (embed-vs-reference, 16 MB limit, denormalize reads, schema versioning, large-field split). It never mentions:

- server-side **`$jsonSchema` validators** (Azure DocumentDB supports them via `createCollection`/`collMod` with `validationLevel`/`validationAction`, but only a subset of keywords: `enum`, `additionalProperties`, `allOf`/`anyOf`/`oneOf`/`not`, `patternProperties`, `min/maxProperties` and `dependencies` are not supported),
- **Decimal128** or integer minor units for money (`grep -ri decimal128 skills/` returns nothing),
- **when a collection needs a TTL index** (TTL lives only in the indexing skill, framed as an index type, not as a data-modeling decision),
- how to persist **agent memory**.

`$push`/`$each`/`$slice` appears once, in an optional rolling-summary snippet in `model-16mb-limit.md` (not applied to state-machine history), `schemaVersion` is described as a migration aid rather than something to write on every insert, and "store model + dimensions alongside vectors" lives only in `vector-search/vector-normalize-embeddings.md`.

Because the skill has no "when you create a collection, do these things" step, agents that loaded it (the core-banking run loaded `documentdb-data-modeling` twice) still created every collection implicitly and skipped all of the above.

## Why it matters

In a 100-sample run of gpt-5-mini building Azure DocumentDB apps with the kit installed, **22 distinct samples (27 audit findings)** violated one of these practices:

| Gap | Samples | What the agent did |
|---|---|---|
| No `$jsonSchema` validator | 7 (patient-record RAG, unified-customer-profile, clinical-trial matching, inventory multi-agent, lead-scoring, survey analyzer, chargeback multi-agent) | `seed.py`/`seed.js` only `insertMany`/upsert; Mongoose subdocs left as `Schema.Types.Mixed`; embedding arrays normalized in app code with nothing enforcing dimension server-side |
| Money as binary float | 4 — **all four finance samples** (SWIFT parser store, core-banking ledger, invoice reconciliation, Basel III) | `amount: Optional[float]`, `amount: { type: Number }`, `balance: { type: Number }` then `$inc` and `$sum` on them; no Decimal128, `$toDecimal` or cents anywhere |
| No TTL on self-described ephemeral collections | 5 (regulatory-reporting `workflow_runs`, branch-analytics `branch_summaries`, lead-scoring `engagement_signals`, prescription-refill `AgentMemory`, CDP `workflows`) | index-creation helpers exist but never add `expireAfterSeconds`; no retention note |
| Unbounded embedded history / memory | 5 (trade-settlement `stateHistory`, loan-origination `transitions`, digital-onboarding `history`, financial-advisor in-process `Map`, personalization engine with no memory store at all) | `$push` every transition with no `$slice`; audit collection "omitted for brevity"; conversation memory in an uncapped process `Map`; memory store the prompt asked for never built |
| `schemaVersion`/processing metadata missing on insert | 2 (AML detector, ESG pipeline) | seed docs have no `schemaVersion`; pipeline writes embedding with no `embedding_model`/`embedding_dims`/`processing_status`, so it cannot resume |

Note for reviewers: one audit phrased the TTL rationale as "control storage and RU costs". RU is Cosmos DB vocabulary; on vCore the argument is document size, storage and working-set growth. The new text below uses vCore terms only.

## Proposed change

All paths under `skills/data-modeling/`.

### 1. `SKILL.md` — new section after "Rules", before "Companion tool"

```markdown
## Collection setup checklist (do this for every new collection)

Collections created implicitly by the first insert get none of the guards below. Create them explicitly (`createCollection` or `collMod`) and answer each question in the seed/setup script:

1. **Validator** — add a `$jsonSchema` validator for required fields and types. See [model-schema-validation](model-schema-validation.md).
2. **`schemaVersion`** — write it on every insert, not only during migrations. See [model-schema-versioning](model-schema-versioning.md).
3. **Lifetime** — is this a log, cache, run history, roll-up, signal feed or short-term memory? Then it needs a TTL index and a one-line retention note in the README. Ledgers and audit trails never get TTL. See `documentdb-indexing/index-ttl-expiry`.
4. **Arrays** — any array that grows per event (history, transitions, turns, events) must be capped with `$push`/`$each`/`$slice` or moved to a side collection. See [model-16mb-limit](model-16mb-limit.md).
5. **Money** — amounts, balances, prices, exposures: Decimal128 or integer minor units, never double. See [model-decimal128-money](model-decimal128-money.md).
6. **Agent memory** — two collections, not an in-process map. See [model-agent-memory](model-agent-memory.md).
```

Add the three new rules to the Rules list and extend the frontmatter `description` with: "…schema validation ($jsonSchema), Decimal128 for monetary values, TTL/retention for ephemeral collections, bounded history arrays, agent-memory persistence. Use when … handling money/amounts/balances, storing logs/caches/run history/agent memory, or writing a seed or setup script that creates collections."

### 2. New `model-schema-validation.md`

```markdown
# model-schema-validation

**Category:** Data Modeling · **Priority:** HIGH

## Why it matters
Implicitly created collections accept any shape. A `$jsonSchema` validator rejects malformed inserts and updates at the server, which matters most for fields the app cannot recover from later: ids, timestamps, status values, and embedding arrays of the wrong length (a vector whose length does not match the index `dimensions` produces wrong results silently; see `documentdb-vector-search/vector-create-diskann-index`).

Azure DocumentDB supports `$jsonSchema` with a **subset of keywords**. Supported: `bsonType`, `type`, `required`, `properties`, `items`, `additionalItems`, `minItems`/`maxItems`, `uniqueItems`, `minimum`/`maximum`, `exclusiveMinimum`/`exclusiveMaximum`, `multipleOf`, `minLength`/`maxLength`, `pattern`. **Not supported:** `enum` (use `pattern` on strings instead), `additionalProperties`, `allOf`/`anyOf`/`oneOf`/`not`, `patternProperties`, `minProperties`/`maxProperties`, `dependencies`. Check the table before adding a keyword:
https://learn.microsoft.com/en-us/documentdb/query/operators/evaluation-query/$jsonschema#supported-keywords

## Incorrect
```javascript
await db.collection("leads").insertMany(docs); // collection created implicitly, no validator
```

## Correct
```javascript
// Node driver — create with validator; use collMod if the collection already exists
const validator = {
  $jsonSchema: {
    bsonType: "object",
    required: ["leadId", "companyId", "createdAt", "schemaVersion", "embedding"],
    properties: {
      leadId:        { bsonType: "string" },
      companyId:     { bsonType: "string" },
      createdAt:     { bsonType: "date" },
      schemaVersion: { bsonType: "int" },
      status:        { bsonType: "string", pattern: "^(new|qualified|lost)$" }, // enum is NOT supported on Azure DocumentDB
      embedding:     { bsonType: "array", items: { bsonType: "double" }, minItems: 1536, maxItems: 1536 }
    }
  }
};
const exists = await db.listCollections({ name: "leads" }).hasNext();
if (!exists) await db.createCollection("leads", { validator, validationLevel: "strict", validationAction: "error" });
else        await db.command({ collMod: "leads", validator, validationLevel: "strict", validationAction: "error" });
```
```python
# PyMongo
db.create_collection("leads", validator=validator)           # first time
db.command("collMod", "leads", validator=validator)          # existing collection
```
Mongoose: define real subdocument schemas instead of `Schema.Types.Mixed`, **and** still apply the server-side validator above — Mongoose validation only runs for writes that go through Mongoose.

## References
- https://learn.microsoft.com/en-us/documentdb/query/operators/evaluation-query/$jsonschema
```

### 3. New `model-decimal128-money.md`

```markdown
# model-decimal128-money

**Category:** Data Modeling · **Priority:** CRITICAL (any sample that stores an amount, balance, price, fee or exposure)

## Why it matters
JS `Number` and Python `float` are IEEE-754 doubles: `0.1 + 0.2 !== 0.3`, and `$inc`/`$sum` over thousands of rows accumulate the error. Azure DocumentDB stores BSON **Decimal128** natively and offers `$toDecimal`/`$convert` in aggregation. Use Decimal128 (or integer minor units such as cents) for every monetary field.

## Incorrect
```javascript
amount:  { type: Number },                       // Mongoose → double
await accounts.updateOne({ _id }, { $inc: { balance: -25.10 } });
```
```python
class Transfer(BaseModel):
    amount: Optional[float]                     # pydantic → double
```

## Correct
```javascript
// Mongoose
amount:  { type: mongoose.Schema.Types.Decimal128, required: true },
balance: { type: mongoose.Schema.Types.Decimal128, required: true, default: () => mongoose.Types.Decimal128.fromString("0.00") },
// read back: doc.balance.toString()  (add a getter if you want strings in toJSON)

// Node driver
const { Decimal128 } = require("mongodb");
await accounts.updateOne({ _id }, { $inc: { balance: Decimal128.fromString("-25.10") } });
```
```python
# PyMongo
from decimal import Decimal
from bson.decimal128 import Decimal128
coll.insert_one({"amount": Decimal128(Decimal("25.10"))})
doc["amount"].to_decimal()                                       # back to decimal.Decimal
coll.update_one({"_id": _id}, {"$inc": {"balance": Decimal128("-25.10")}})
```
```javascript
// Aggregation: coerce legacy doubles instead of summing them raw
{ $group: { _id: "$accountId", total: { $sum: { $toDecimal: "$amount" } } } }
```

Rules:
- `$inc` keeps Decimal128 precision only when the operand is itself Decimal128. Passing a JS `Number`/Python `float` to `$inc` on a Decimal128 field reintroduces binary rounding before the add.
- Decimal128 fields index and sort normally; equality queries must also use Decimal128 values.
- Alternative: store integer minor units (`amountCents: 2510`, `bsonType: "long"`) and format at the edge. Pick one convention per sample and say which in the README.

## References
- https://learn.microsoft.com/en-us/documentdb/query/operators/aggregation/$todecimal
- BSON Decimal128 spec
```

### 4. New `model-agent-memory.md`

```markdown
# model-agent-memory

**Category:** Data Modeling · **Priority:** HIGH (any sample described as an agent, chatbot or copilot)

## Why it matters
An in-process `Map`/`dict` of messages is not a memory store: it is lost on restart, unbounded, and invisible to other replicas. Store short-term raw turns with a TTL and long-term summaries with an embedding so recall is bounded and searchable.

## Incorrect
```javascript
const memory = new Map(); // sessionId -> [ ...every message ever ]
memory.get(sessionId).push(msg);
```

## Correct — two collections
```javascript
// raw_turns: one document per turn, expires automatically
await db.createCollection("raw_turns", { validator: { $jsonSchema: { bsonType: "object",
  required: ["sessionId", "role", "content", "createdAt", "schemaVersion"] } } });
await db.collection("raw_turns").createIndex({ createdAt: 1 }, { expireAfterSeconds: 60 * 60 * 24 * 7, name: "raw_turns_ttl_7d" });
await db.collection("raw_turns").createIndex({ sessionId: 1, createdAt: -1 });

// long_term_summaries: periodic compaction of raw_turns, with embedding + metadata
await db.collection("long_term_summaries").insertOne({
  userId, summary, embedding,                 // number[] — never BSON binary
  embedding_model: process.env.OPENAI_EMBEDDING_MODEL, embedding_dims: embedding.length,
  sourceTurnIds, createdAt: new Date(), schemaVersion: 1
});
// vector index on long_term_summaries.embedding via cosmosSearch (see documentdb-vector-search)
```
Recall = last N `raw_turns` for the session + top-k vector hits from `long_term_summaries`. Compact when a session exceeds N turns or closes. If the memory holds regulated data (PHI, PII), store a canonical id instead of the raw text and say so in the README.

## References
- https://learn.microsoft.com/en-us/azure/cosmos-db/gen-ai/agentic-memories (written for Azure Cosmos DB for NoSQL: its partition-key, container-TTL, VectorDistance and RU guidance does not apply; reuse only the short-term vs long-term memory and one-document-per-turn pattern, implemented here with a TTL index and a cosmosSearch vector index)
```

### 5. `model-16mb-limit.md` — add after "Correct"

```markdown
### State machines and workflow history
Every `$push` into `transitions`/`history`/`stateHistory` must be capped **in the same update**, or go to a side collection written in the same transaction. Do not write "audit collection omitted for brevity" — ship the side collection.

```python
# keep the last 100 transitions on the document…
coll.update_one({"_id": wf_id, "state": from_state},
    {"$set": {"state": to_state}, "$push": {"transitions": {"$each": [t], "$slice": -100}}}, session=s)
# …and the full record in a side collection, same session
db.workflow_transitions.insert_one({**t, "workflowId": wf_id}, session=s)
```
```

### 6. `model-schema-versioning.md` — add one paragraph to "Correct"

```markdown
Write `schemaVersion` on **every insert and seed document**, not only when migrating. For pipeline-produced fields (embeddings, scores, summaries) also persist `processing_status`, `last_updated`, `embedding_model` and `embedding_dims` in the same `$set`, so a crashed run can resume and a model change can be detected per document. (Cross-link `documentdb-vector-search/vector-normalize-embeddings`, which already says to store model + dimensions alongside vectors.)
```

## Out of scope for this repo (noted for the sample-prompt owners)

Fintech-category sample prompts should state "monetary fields use Decimal128" as an explicit requirement; all four finance samples in the run defaulted to doubles even where the audit later found the `$toDecimal` Learn page.

## Evidence (run folders from the readiness experiment)

- `runs/03-core-banking-transaction-ledger/20261124-200452/05-audit.json` — `amount`/`balance: Number`, `$inc` on doubles; data-modeling skill was loaded in `events.jsonl`
- `runs/02-swift-message-parser-store/20261124-200226/05-audit.json` — `amount: Optional[float]`, float `$sum`
- `runs/15-digital-onboarding-orchestration/20261124-202211/05-audit.json` — `$push` history with no `$slice`, cited the data-modeling SKILL.md as the source practice
- `runs/09-lead-scoring-agent/20261124-204408/05-audit.json` — no `$jsonSchema` validator, no TTL on `engagement_signals`
- `runs/14-hyper-personalized-content-engine/20261124-205043/05-audit.json` and `doc-gaps.md` — agent memory requested in the prompt, never implemented; doc gap "Agent-memory persistence guidance for samples"

🤖 Generated with [Claude Code](https://claude.com/claude-code)

## Verification

### 1. Already covered? partially_covered
Grepped `skills/` and `knowledge-base/` in the Azure/documentdb-agent-kit clone for `Decimal128`, `jsonSchema`, `validator`, `$slice`, `expireAfterSeconds`, `schemaVersion` and agent memory.
- **Not present:** no `Decimal128`, `$jsonSchema`/validator or agent-memory guidance anywhere in the kit (the only "validator" hit is "Use a JSON validator" in `skills/mcp-setup/SKILL.md`, which is about MCP config files).
- **Partly present:** `skills/data-modeling/model-16mb-limit.md` has one optional rolling-summary snippet: `$push: { recentEvents: { $each: [newEvent], $slice: -50 } }`. State-machine history is not covered. TTL is covered as an index type in `skills/indexing/index-ttl-expiry.md` (plus `index-pattern-cookbook.md` and `query-optimizer/references/core-indexing-principles.md`), but nothing tells the agent which collections need one. `skills/data-modeling/model-schema-versioning.md` shows `schemaVersion: 2` and lazy migration, but does not say to write it on every insert. `skills/vector-search/SKILL.md` already says "store model + dimensions alongside vectors" (vector-normalize-embeddings).
- `skills/data-modeling/SKILL.md` frontmatter does not trigger on money, validation, retention or memory.
So the pieces that exist are scattered across other skills and the data-modeling skill has no step that applies them when a collection is created. The new rule files and the checklist are not covered. The draft now cross-links the existing indexing and vector-search rules instead of duplicating them.

### 2. Is the premise true? confirmed (one snippet corrected)
- `$jsonSchema` validators work on Azure DocumentDB through `createCollection` with `validator`, `validationLevel` ("strict"/"moderate") and `validationAction` ("error"/"warn"). `bsonType`, `required`, `properties`, `items`, `minItems`/`maxItems` and `pattern` are listed as supported. Source: https://learn.microsoft.com/en-us/documentdb/query/operators/evaluation-query/$jsonschema
- **Correction applied:** the same page lists `enum` under "Unsupported Keywords", with the workaround "Use `$in` operator instead". The original draft's validator example used `status: { enum: [...] }`, which would have taught agents something the service does not support. It now uses `bsonType: "string"` plus `pattern`, and the full unsupported list (`enum`, `additionalProperties`, `allOf`/`anyOf`/`oneOf`/`not`, `patternProperties`, `min/maxProperties`, `dependencies`) is spelled out in the rule and in "What happens today".
- **Correction applied:** the draft said a wrong-length vector is "silently excluded from the vector index". I found no source for that. The kit's own `skills/vector-search/vector-create-diskann-index.md` says dimensions must match and that mismatches "produce wrong results silently". The text now says that instead. Vectors remain number[] (BSON binary is not indexed), and the vector index is cosmosSearch.
- `$toDecimal` is supported and returns Decimal128. Source: https://learn.microsoft.com/en-us/documentdb/query/operators/aggregation/$todecimal ("converts an input expression into a Decimal value"). Learn URLs were changed to the canonical `en-us/documentdb/query/operators/...` form.
- The agent-memory reference https://learn.microsoft.com/en-us/azure/cosmos-db/gen-ai/agentic-memories exists, but it is written for Azure Cosmos DB for NoSQL (partition keys, container TTL, VectorDistance, RU charges). The reference note now says to reuse only the short-term vs long-term pattern, implemented with a TTL index and a cosmosSearch index on vCore.
- The draft's vCore restatement of the audit's "RU" wording (document size, storage and working-set growth) is correct: capacity is M-series vCore tiers, not RUs.
- Double vs Decimal128 precision, `$inc` with a Decimal128 operand, `$push`/`$each`/`$slice`, TTL via `expireAfterSeconds` on a single-field date index, and multi-document transactions are standard MongoDB-wire behavior that Azure DocumentDB supports. The TTL constraints match the kit's `index-ttl-expiry.md`.
- Sample count checked against `findings-default.json`: the 27 finding ids span 22 distinct samples, which matches the draft.

### 3. Maintainer skeptic: confirmed
As a documentdb-agent-kit maintainer I would accept this PR. It names exact files (`skills/data-modeling/SKILL.md`, three new rule files, `model-16mb-limit.md`, `model-schema-versioning.md`) and gives paste-ready text in the repo's existing rule format (why it matters, incorrect, correct, references). It has a real Azure DocumentDB angle: the supported-keyword subset for `$jsonSchema` (now corrected), number[] vectors and cosmosSearch in the memory template, vCore rather than RU framing, and `$toDecimal` support. The evidence is 22 of 100 samples, with the skill loaded in the failing runs. Small edit for review: the maintainer may ask to split it into two PRs (validation plus Decimal128, then TTL, history and memory). The fintech prompt note is correctly marked as out of scope for this repo. It belongs to the sample-prompt owners (the pipeline repo), not the kit.

## Finding ids

- F0101
- F0174
- F0246
- F0034
- F0307
- F0378
- F0380
- F0687
- F0748
- F1516
- F1547
- F1551
- F1580
- F2114
- F2177
- F2449
- F2541
- F2544
- F2418
- F2579
- F2611
- F2834
- F2864
- F2865
- F2868
- F3062
- F3000
