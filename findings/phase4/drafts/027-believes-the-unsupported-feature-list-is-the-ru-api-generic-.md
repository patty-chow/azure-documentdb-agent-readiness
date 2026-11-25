---
title: 'Add a "What differs from MongoDB" compatibility block to the connection skill (transactions, change streams, server-side JS, Atlas-only syntax) and drop the Cosmos DB vCore naming from data-modeling'
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 24
findings: 24
bucket: confusion-Q10
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Add a "What differs from MongoDB" block to the connection skill; drop Cosmos DB vCore naming from data-modeling

## What happens today

When an agent using this kit is asked which MongoDB features Azure DocumentDB does *not* support, it answers from its prior about **Azure Cosmos DB for MongoDB (RU)** and generic managed-MongoDB folklore. In a 100-sample experiment (gpt-5-mini, all 17 skills installed, DocumentDB + Azure + Learn MCP servers) the cold answer to that question was wrong or outdated in 24 samples, and the wrong parts were consistent:

| Claim in the cold answer | Samples (of 24) | Reality for Azure DocumentDB |
|---|---|---|
| Multi-document transactions "limited", "only within a partition/shard key", "cross-partition not supported" | 20 | Multi-document ACID transactions are supported (`startSession` / `withTransaction` / `commitTransaction` / `abortTransaction`; the session commands are supported on 5.0, 6.0, 7.0 and 8.0 per [compatibility-query-language](https://learn.microsoft.com/azure/documentdb/compatibility-query-language)); see [how-to-transactions](https://learn.microsoft.com/azure/documentdb/how-to-transactions). They are not partition-key scoped; this kit's own `skills/sharding/sharding-logical-vs-physical.md:45` already says cross-shard transactions are supported. Maximum transaction lifetime is 30 seconds ([limitations](https://learn.microsoft.com/azure/documentdb/limitations)). |
| Change streams "not supported", "behave differently", "support varies" | 8 | Supported ([change-streams](https://learn.microsoft.com/azure/documentdb/change-streams)): collection `watch()`, `resumeAfter` / `startAt` / `startAtOperationTime`, pre-images; `updateDescription` and multi-shard change streams are preview (multi-shard must be enabled under Features and can't be combined with the multishard rebalancer); `showExpandedEvents` and `$changeStreamSplitLargeEvent` are not supported |
| "Some aggregation stages may be missing" | 18 | 58/60 stages, 181/181 aggregation operators, 99.03% overall per [compatibility-query-language](https://learn.microsoft.com/azure/documentdb/compatibility-query-language); the missing stages are diagnostic ones (`$planCacheStats`, `$listSampledQueries`, `$listSearchIndexes`, `$shardedDataDistribution`, session listing stages) |
| No server-side JavaScript (`$where`, `$function`, `mapReduce`) | 22 | Correct, no fix needed |
| Host-level admin commands unavailable | 15 | Correct, no fix needed |

The kit does not correct the false beliefs where a build agent will see it:

- `skills/connection/SKILL.md` and `skills/driver/SKILL.md` (loaded in every build) have no supported-vs-unsupported summary at all.
- No file under `skills/` or `knowledge-base/` mentions change streams.
- Cross-shard transactions are stated only in `skills/sharding/sharding-logical-vs-physical.md:45,88-90`, which loads only for sharding tasks. The other transaction note is `skills/natural-language-querying/SKILL.md:258` ("Azure DocumentDB supports multi-document transactions"), which loads only for NL-query tasks, does not say *cross-shard*, and points readers (line 261) to `https://learn.microsoft.com/azure/documentdb/compatibility`, which returns **404** (same dead link in `compat/QUICKSTART.md:103`). The correct page is `compatibility-query-language`, which other kit files (e.g. `skills/indexing/index-single-field.md:89`) already link to.
- `skills/data-modeling/model-embed-vs-reference.md:7,49`, `model-16mb-limit.md:7,45` and `model-denormalize-reads.md:39` still call the product "Cosmos DB for MongoDB vCore" and link to `learn.microsoft.com/azure/cosmos-db/mongodb/vcore/...`, which reinforces exactly the Cosmos DB association behind the wrong answers.

## Why it matters

24 of 100 samples hit this. In these runs the readiness stage's Learn MCP search corrected the belief before code was written (e.g. `16-subscription-billing-engine` went on to build a transactional charge flow and `07-lab-results-aggregator` built a change-stream alert), so no sample shipped a workaround. But the correction came from Learn, not from the kit. A user who installs the kit without the Learn MCP, or an agent that does not search, keeps the RU-era model and will:

- co-locate documents by a shard key purely to stay "inside one partition" for a transaction (`16-subscription-billing-engine` build_risk: "over-constrain its schema");
- poll instead of using change streams, or write change-stream fallbacks (`07-lab-results-aggregator` build_risk: "implement unnecessary workarounds");
- avoid `$setWindowFields`, `$facet`, `$graphLookup` etc. that work fine.

Learn already states all of this; the gap is that the facts never reach the agent's context during a build. The sharding skill already says cross-shard transactions work, so this is also an internal consistency fix.

## Proposed change

### 1. `skills/connection/SKILL.md`, new subsection under "Azure DocumentDB Connection Specifics" (after "Authentication")

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

### 2. `skills/driver/SKILL.md`

The "Rules" section is a list of rule-file links, so add a short note under the intro paragraph instead: `Before avoiding a MongoDB feature, check "Compatibility at a glance" in the documentdb-connection skill; multi-document transactions and change streams are supported.`

### 3. Fix the dead compatibility link and the NLQ wording

- `skills/natural-language-querying/SKILL.md:261` and `compat/QUICKSTART.md:103`: `.../azure/documentdb/compatibility` → `.../azure/documentdb/compatibility-query-language`.
- `skills/natural-language-querying/SKILL.md:258`: "supports multi-document transactions" → "supports multi-document transactions across collections and shards (30-second maximum lifetime); change streams are also supported".

### 4. `skills/data-modeling/*`

- `model-embed-vs-reference.md:7` and `model-16mb-limit.md:7`: "Cosmos DB for MongoDB vCore" → "Azure DocumentDB".
- `model-embed-vs-reference.md:49`, `model-denormalize-reads.md:39`: link → `https://learn.microsoft.com/azure/documentdb/` (landing) or the specific DocumentDB page the maintainers prefer.
- `model-16mb-limit.md:45`: link → `https://learn.microsoft.com/azure/documentdb/limitations` (states the 16 MB BSON document limit).

## Evidence (run folders under `azure-documentdb-agent-readiness/runs/`)

- `16-subscription-billing-engine/20261124-192251/02-readiness.json`, confusions[Q10]: cold answer assumes cross-partition transactions unavailable; build_risk "over-constrain its schema"
- `07-lab-results-aggregator/20261124-194018/02-readiness.json`, confusions[Q10]: "no support for multi-shard distributed transactions and MongoDB change streams"; the build later used `coll.watch()` successfully (03-build.md)
- `20-interest-accrual-batch-processor/20261124-202826/02-readiness.json`, confusions[Q10]: "transactions that span partition keys may not be supported"
- `06-symptom-triage-chatbot-rag/20261124-193845/02-readiness.json`, confusions[Q10]: confused_with `azure_cosmos_db_for_mongodb_ru`
- `01-unified-customer-profile-store/20261124-203120/02-readiness.json`, confusions[Q10]: "some aggregation stages/transaction semantics may be restricted"

Kit state checked at commit `4f41c15` (2026-11-23).

## Verification

### 1. Already covered? partially_covered

- Agent kit (clone at `4f41c15`): `grep -rniE "change.?stream|\.watch\("` over `skills/` and `knowledge-base/` returns nothing. Transactions: `skills/sharding/sharding-logical-vs-physical.md:45` says "Cross-shard transactions (across both logical and physical shards) are supported" and `skills/natural-language-querying/SKILL.md:258` says "Azure DocumentDB supports multi-document transactions"; neither skill loads in a general build. `skills/connection/SKILL.md` (sections: Connection String Format, TLS Is Required, Authentication, ...) and `skills/driver/SKILL.md` have no compatibility summary. `skills/natural-language-querying/SKILL.md:261` and `compat/QUICKSTART.md:103` link to `learn.microsoft.com/azure/documentdb/compatibility`, which WebFetch confirms returns HTTP 404. The data-modeling lines quoted in the draft (`model-embed-vs-reference.md:7,49`, `model-16mb-limit.md:7,45`, `model-denormalize-reads.md:39`) still use "Cosmos DB for MongoDB vCore" and `/azure/cosmos-db/mongodb/vcore/` URLs.
- documentdb-mcp: no compatibility guidance (grep for change stream / transaction / unsupported hits only transport and update-operator parsing code), so it is not the right home.
- Learn fully documents the facts (compatibility-query-language, compatibility-features, change-streams, how-to-transactions, limitations, FAQ), so the gap is delivery into the kit, not missing docs. Verdict: partially covered (facts in the kit's sharding/NLQ skills and on Learn, but not where a build agent looks).

### 2. Premise true? confirmed (with corrections applied)

- 99.03%, 58/60 stages, 181/181 aggregation operators, wire versions 5.0–8.0: confirmed on https://learn.microsoft.com/en-us/azure/documentdb/compatibility-query-language and the FAQ ("supports MongoDB wire protocol versions 5.0, 6.0, 7.0, and 8.0").
- Transactions: `startSession`, `commitTransaction`, `abortTransaction` supported on v5.0–8.0 (compatibility-query-language, Session Commands); how-to-transactions documents ACID multi-operation transactions. Correction applied: Learn's how-to-transactions page does not itself say "across shards", so the cross-shard claim is now cited to the kit's own sharding skill, and the 30-second maximum transaction lifetime from https://learn.microsoft.com/en-us/azure/documentdb/limitations was added.
- Change streams: confirmed on https://learn.microsoft.com/en-us/azure/documentdb/change-streams (watch, resumeAfter, startAtOperationTime; "updateDescription ... (preview)"; "Multi-shard change streams (preview)"; showExpandedEvents unsupported). Added the per-cluster enablement and rebalancer conflict.
- Not available: `$where`, `$function`, `$accumulator` listed without support; `mapReduce` N/A; `serverStatus`, `top`, `connPoolStats`, `bulkWrite` command marked No; `fsync`, `setFeatureCompatibilityVersion` N/A (service-managed). Limitations page: batch write and bulk operations supported, max 25,000 writes per batch (added).
- Correction applied: the draft said "Atlas Search index definitions" are not available and to use "$search-style text indexes". Learn's limitations page documents preview full-text search indexes "that you create with `createSearchIndexes` and query with `$search`" with static `mappings.fields`, and the kit's own `skills/full-text-search/SKILL.md` uses that path. The block now says `$vectorSearch` is unavailable (use `cosmosSearch`) and full-text search uses `createSearchIndexes` + `$search` (preview, subset of mappings/operators) instead of calling search index definitions Atlas-only.
- Added time series / capped / clustered collections as unsupported per https://learn.microsoft.com/en-us/azure/documentdb/compatibility-features.
- Naming: FAQ says Azure DocumentDB "was previously named vCore-based Azure Cosmos DB for MongoDB" and is a separate service from Cosmos DB for MongoDB (RU); the rename in data-modeling is correct. 16 MB BSON limit confirmed on the limitations page.

### 3. Maintainer skeptic: confirmed

Names exact files and lines in Azure/documentdb-agent-kit, gives paste-ready text, fixes a verified 404 link, aligns naming with the product's current name, and makes the always-loaded connection skill consistent with the sharding skill. It is Azure DocumentDB specific and small. One small edit was made: the driver-skill pointer goes in the intro text, not the "Rules" list of rule-file links. Unrelated observation for the maintainers, kept out of this PR: the connection string template in `skills/connection/SKILL.md` sets retryWrites=true, while Learn's documented string uses retrywrites=false.

## Finding ids

F0044, F0075, F0152, F0183, F0425, F0561, F0632, F0768, F0892, F0921, F0973, F1078, F1106, F1202, F1302, F1374, F1438, F1526, F1628, F3363, F3396, F3429, F3462, F2782
