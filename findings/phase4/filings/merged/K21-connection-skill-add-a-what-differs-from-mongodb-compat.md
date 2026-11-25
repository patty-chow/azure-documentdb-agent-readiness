---
id: K21
title: "connection skill: add a 'What differs from MongoDB' compatibility block"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P1
sample_count: 24
member_drafts:
  - 027-believes-the-unsupported-feature-list-is-the-ru-api-generic-.md
open_questions: 4
---

# connection skill: add a "What differs from MongoDB" compatibility block

## What happens today

When an agent using this kit is asked which MongoDB features Azure DocumentDB does not support, it answers from its prior about Azure Cosmos DB for MongoDB (RU) and generic managed-MongoDB folklore. In an agent-readiness experiment (100 sample apps, gpt-5-mini, all kit skills installed, DocumentDB + Azure + Learn MCP servers), that answer was wrong or outdated in 24 samples, and the errors were consistent:

| Claim in the agent's answer | Samples (of 24) | Azure DocumentDB |
|---|---|---|
| Multi-document transactions "limited" or "only within a partition/shard key" | 20 | Supported (`startSession` / `withTransaction` / `commitTransaction` / `abortTransaction`, wire versions 5.0 to 8.0); 30-second maximum lifetime ([limitations](https://learn.microsoft.com/azure/documentdb/limitations)) |
| Change streams "not supported" or "support varies" | 8 | Supported: `watch()`, `resumeAfter` / `startAtOperationTime`, pre-images; `updateDescription` and multi-shard change streams documented as preview [needs SME confirmation] ([change-streams](https://learn.microsoft.com/azure/documentdb/change-streams)) |
| "Some aggregation stages may be missing" | 18 | 58/60 stages, 181/181 aggregation operators, 99.03% overall; the missing stages are diagnostic ([compatibility-query-language](https://learn.microsoft.com/azure/documentdb/compatibility-query-language)) |
| No server-side JavaScript; no host-level admin commands | 22 / 15 | Correct |

The kit does not correct this where a build agent looks:

- `skills/connection/SKILL.md` and `skills/driver/SKILL.md`, loaded in every build, have no supported-versus-unsupported summary.
- No file under `skills/` or `knowledge-base/` mentions change streams.
- Cross-shard transactions are stated only in `skills/sharding/sharding-logical-vs-physical.md:45`, which loads only for sharding tasks. `skills/natural-language-querying/SKILL.md:258` says transactions are supported but not across shards, and line 261 (and `compat/QUICKSTART.md:103`) links to `learn.microsoft.com/azure/documentdb/compatibility`, which returns 404.
- `skills/data-modeling/model-embed-vs-reference.md:7,49`, `model-16mb-limit.md:7,45` and `model-denormalize-reads.md:39` still say "Cosmos DB for MongoDB vCore" and link to `/azure/cosmos-db/mongodb/vcore/` pages, reinforcing the Cosmos DB association behind the wrong answers.

## Why it matters

24 of the 100 samples hit this (counts are from one experiment run). In these runs a Learn MCP search corrected the belief before code was written, so no sample shipped a workaround, but the correction came from Learn, not the kit. Without the Learn MCP, the agent keeps the RU-era model and will co-locate documents by shard key just to keep a transaction "inside one partition", poll instead of using change streams or write change-stream fallbacks, and avoid stages such as `$setWindowFields`, `$facet` and `$graphLookup` that work. The sharding skill already says cross-shard transactions work, so this is also an internal-consistency fix.

## Proposed change

### 1. `skills/connection/SKILL.md`: new subsection under "Azure DocumentDB Connection Specifics", after "Authentication"

```markdown
### Compatibility at a glance: what differs from MongoDB

Azure DocumentDB speaks MongoDB wire protocol **5.0, 6.0, 7.0 or 8.0** (the
cluster's `serverVersion`) and supports 99.03% of MongoDB operators. Do **not**
apply Azure Cosmos DB for MongoDB (RU) or Amazon DocumentDB limitations here;
they are different services.

**Supported (use them):**
- Multi-document ACID transactions across collections and shards
  (`startSession` → `withTransaction` or `commitTransaction`/`abortTransaction`).
  They are not partition-key scoped. Keep each transaction under the
  30-second maximum lifetime.
- Change streams: `collection.watch()`, `resumeAfter`, `startAtOperationTime`,
  pre-images. `updateDescription` and multi-shard change streams are preview
  (multi-shard is enabled per cluster under Features); check Learn.
- All common aggregation stages (`$lookup`, `$facet`, `$graphLookup`,
  `$setWindowFields`, `$merge`, `$out`, `$unionWith`, ...).
- Vector search via `cosmosSearch` (`vector-ivf`, `vector-hnsw`, `vector-diskann`);
  vectors must be `number[]`.
- Full-text search via `createSearchIndexes` + `$search` (see the
  documentdb-full-text-search skill; preview, supports a subset of mappings
  and operators).

**Not available (do not generate):**
- Server-side JavaScript: `$where`, `$function`, `$accumulator`, `mapReduce`.
- Host-level admin/diagnostic commands: `serverStatus`, `top`, `connPoolStats`,
  `fsync`, `setFeatureCompatibilityVersion`, replication and shard-balancer
  commands (the service manages these).
- The `bulkWrite` *server command*; the driver's `bulkWrite()` / `insertMany()`
  helpers are fine (max 25,000 writes per batch).
- Atlas-only `$vectorSearch` (use `cosmosSearch`).
- Time series, capped and clustered collections.

Authoritative lists:
https://learn.microsoft.com/azure/documentdb/compatibility-query-language ·
https://learn.microsoft.com/azure/documentdb/compatibility-features ·
https://learn.microsoft.com/azure/documentdb/how-to-transactions ·
https://learn.microsoft.com/azure/documentdb/change-streams ·
https://learn.microsoft.com/azure/documentdb/limitations
```

Before merging, settle three claims in this block (see Open questions 1-3): transactions spanning shards, the multi-shard change-stream enablement and limits, and the "preview" labels on full-text search, multi-shard change streams and `updateDescription` [needs SME confirmation].

### 2. `skills/driver/SKILL.md`: one line under the intro paragraph (not in the "Rules" list of rule-file links)

```markdown
Before avoiding a MongoDB feature, check "Compatibility at a glance" in the documentdb-connection skill; multi-document transactions and change streams are supported.
```

### 3. `skills/natural-language-querying/SKILL.md`

- Line 258: "supports multi-document transactions" → "supports multi-document transactions across collections and shards (30-second maximum lifetime); change streams are also supported".
- Line 261: `.../azure/documentdb/compatibility` → `.../azure/documentdb/compatibility-query-language`.

### 4. `compat/QUICKSTART.md`

- Line 103: same link fix as above.

### 5. `skills/data-modeling/`

- `model-embed-vs-reference.md:7`: "Cosmos DB for MongoDB vCore" → "Azure DocumentDB"; line 49: link → `https://learn.microsoft.com/azure/documentdb/` (or the specific page maintainers prefer).
- `model-16mb-limit.md:7`: same rename; line 45: link → `https://learn.microsoft.com/azure/documentdb/limitations` (states the 16 MB BSON limit).
- `model-denormalize-reads.md:39`: link → `https://learn.microsoft.com/azure/documentdb/`.

Line numbers are against kit commit `4f41c15` (2026-11-23).

## Evidence

Run folders in the experiment harness (`runs/`):

- `16-subscription-billing-engine/20261124-192251/02-readiness.json` (confusion Q10: assumes cross-partition transactions unavailable; build risk "over-constrain its schema")
- `07-lab-results-aggregator/20261124-194018/02-readiness.json` (confusion Q10: "no support for multi-shard distributed transactions and MongoDB change streams"; the build later used `coll.watch()` successfully)
- `20-interest-accrual-batch-processor/20261124-202826/02-readiness.json` (confusion Q10: transactions spanning partition keys "may not be supported")
- `06-symptom-triage-chatbot-rag/20261124-193845/02-readiness.json` (confusion Q10: confused with Cosmos DB for MongoDB RU)
- `01-unified-customer-profile-store/20261124-203120/02-readiness.json` (confusion Q10: aggregation stages and transaction semantics "may be restricted")

## Open questions

1. [needs SME confirmation] Cross-shard transactions: Learn's how-to-transactions page documents multi-document ACID transactions but does not itself say "across shards"; the block relies on the kit's sharding skill for that. Please confirm transactions span shards on sharded clusters.
2. [needs SME confirmation] Multi-shard change streams: confirm they are enabled per cluster under Features, cannot be combined with the multishard rebalancer, and what other change-stream limits (log retention, PITR window) an agent should know.
3. [needs SME confirmation] Preview status: confirm whether full-text search (`createSearchIndexes` + `$search`), multi-shard change streams and `updateDescription` are still preview or now GA, so the block's labels are current.
4. [needs SME confirmation] Out of scope for this PR but adjacent: the connection string template in `skills/connection/SKILL.md` sets `retryWrites=true`, while Learn's documented connection string uses `retrywrites=false`. Contributors disagree on whether retryable writes are unsupported or merely not the documented default; please give the engineering answer (handled in a separate retryWrites PR).

## Source drafts

- 027-believes-the-unsupported-feature-list-is-the-ru-api-generic-.md
