---
id: K17
title: "full-text-search skill: Azure AI Search is not required, document preview enablement with CommandNotSupported fail-fast, and add the server-side $unionWith RRF hybrid pipeline"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P1
sample_count: 73
member_drafts:
  - 022-believes-full-text-hybrid-search-requires-an-external-azure-.md
  - 024-believes-hybrid-fusion-must-be-a-two-step-client-side-re-ran.md
  - 025-skill-gap-full-text-search-is-a-preview-feature-that-must-be.md
merged_from:
  - K17
  - K18
  - K19
open_questions: 6
---

# full-text-search skill: Azure AI Search is not required, document preview enablement with `CommandNotSupported` fail-fast, and add the server-side `$unionWith` RRF hybrid pipeline

All counts come from one experiment run: gpt-5-mini built 100 Azure DocumentDB sample apps with this kit plus the DocumentDB, Azure and Learn MCP servers installed. Some runs were repeated. Treat the counts as indicative.

**Sample count (73, estimated).** The members report 67 (K17), 14 (K18) and 5 (K19; 2 backed by finding ids, 3 more found in run artifacts) samples, 86 if none overlapped. Re-checking the run's findings set: 9 of the 14 K18 samples also gave an external-search cold answer for the same quiz question and are counted as already inside K17's 67; 4 of the 5 K19 samples (12, 15, 11, 07) also gave an external-search cold answer, and 12 and 15 are stated in their source draft to hold that belief, so all 4 are counted as overlap. That leaves 67 + 5 (K18 samples whose cold answer was about client-side fusion only) + 1 (K19 sample 04, a template with no enablement step) = 73. K17's exact 67-sample list was not available in the findings set, so the true union lies between 73 and 86.

## What happens today

`skills/full-text-search/` teaches the right API (`createSearchIndexes`, `$search`, `searchScore`, `cosmosSearch` vector indexes, RRF fusion), but it has three gaps that leave agents with wrong defaults.

1. **It never says Azure AI Search is not needed** (from K17). The skill never names the architecture agents bring over from Azure Cosmos DB for NoSQL and Cosmos DB for MongoDB (RU): sync documents into Azure AI Search (formerly Azure Cognitive Search) through a change feed, indexer or custom ETL, and run BM25 and hybrid ranking there. `grep -rniE 'ai search|cognitive|cosmos db for nosql|external search' skills/` returns no hits. The single-store fact is only implicit: `SKILL.md` says "Combine BM25 and vector search (RRF) on the same collection", and `fts-hybrid-search.md` says both index types work on the same collection. `fts-hybrid-search.md` References links only `vector-search` and `overview`, and `skills/indexing/index-text-prefer-textsearch.md` links the bare `https://learn.microsoft.com/azure/documentdb/` root. Learn already states the point: `full-text-search-overview` says the engine works without a separate search cluster, and `full-text-search-hybrid` ("Architecture: two indexes, one collection") says there is no replication or synchronization layer and both index types are included at no extra cost.

2. **It never says full-text search must be enabled first** (from K19). Nothing in `SKILL.md` or `fts-create-search-index.md` says that full-text search is a **preview** feature, **off by default**, that must be enabled per cluster before `createSearchIndexes` or `$search` works [needs SME confirmation: current preview/GA status]; that Learn says to wait **about 10 minutes** after enabling; or that on a cluster without the feature `createSearchIndexes` returns `{ ok: 0, code: 115, codeName: "CommandNotSupported", errmsg: "Search index creation is not supported yet" }` (seen in run logs; Learn does not document this string) [needs SME confirmation]. A grep for `preview`, `enable`, `FullTextSearch`, `CommandNotSupported` or `prerequisite` over `skills/full-text-search/` and `knowledge-base/` finds only an unrelated `dynamic: true` guideline. Learn documents the steps ([Enable full-text search](https://learn.microsoft.com/azure/documentdb/full-text-search-overview#enable-full-text-search): portal Settings > Features > Full-text search > Enable; an `az rest` PATCH adding `FullTextSearch` to `properties.previewFeatures` on `Microsoft.DocumentDB/mongoClusters`, api-version `2024-07-01`; AzAPI and Bicep variants).

3. **It teaches only client-side hybrid fusion** (from K18). `fts-hybrid-search.md` runs the keyword `$search` arm, runs the `cosmosSearch` vector arm, then fuses the arrays with a JavaScript `rrf()` helper. Its intro says you can "execute both queries in one round trip and combine them in the application", but the example makes two aggregation calls, so it is not one round trip. Nothing in the kit mentions `$unionWith` or server-side fusion (`grep -rniE 'unionWith|server-side'` over `skills/` and `knowledge-base/` finds two unrelated lines). The Learn page [Hybrid search in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/full-text-search-hybrid) documents both a client-side helper and "Server-side RRF with `$unionWith`", recommending server-side for one round trip and no fusion code, and client-side when fusing more ranked lists. Per-arm weighting works in both.

## Why it matters

Before reading any guidance, the agent was asked "How are full-text search and hybrid search done?", then built each sample.

- **External search service (K17): 67 of 100 samples.** The cold answer used the external-search pattern (69 findings: about 42 wrong, 27 partly wrong), for example "integrate Cosmos DB with Azure Cognitive Search (sync via change feed or an indexer)" and "hybrid/vector+text needs external search service". Attribution: Cosmos DB for NoSQL 39, Cosmos DB for MongoDB RU 18, doubt whether the hosted service exposes open-source DocumentDB's search 11 (one unattributed). Impact was limited: once the agent loaded the skill its answers were correct, and no generated app wired up Azure AI Search (49 of 100 used `createSearchIndexes` / `$search`). The fix is preventive for agents that skim `SKILL.md` or pick an architecture before opening the skill.
- **Client-side-only hybrid fusion (K18): 14 of 100 samples.** The cold answer said hybrid search is a two-step fusion in the application, usually vector kNN for candidate ids then filter or BM25 re-rank "in application code" (some reversed the order). Grounding corrected each answer from Learn, and several readiness reports asked the kit for a `$unionWith` / server-side RRF example. None of the 14 apps used `$unionWith`; apps that implemented hybrid search copied the kit's client-side `rrf()`. The skill the agent loads for the task reinforces the client-side-only belief.
- **Missing preview enablement (K19): 5 of 100 samples** (2 backed by finding ids, 3 found in run artifacts).
  - 2 flagged the gap at readiness. One still believed full-text search needs an external search service; the other warned the sample "will fail" if the cluster lacks "tier/preview flags". Learn lists no tier restriction, only the preview flag.
  - 1 hit code 115 on a live cluster; its seed script printed "command may not be available" and continued, leaving search broken.
  - 1 caught the same error and silently fell back to a legacy `{ text: "text" }` index (`$text`), which the skill itself says is not the DocumentDB search path.
  - 1 shipped a `createSearchIndexes` template and README with no enablement step, so a user on a fresh cluster gets code 115 with no explanation.

Together: the kit should say in one place that search runs in the cluster (no AI Search), that it must be switched on first (and what the error looks like when it is not), and that hybrid fusion can run server-side in one pipeline.

## Proposed change

### 1. `skills/full-text-search/SKILL.md`

**a. Insert after the intro paragraph, before "Key syntax points"** (from K19; this replaces K17's conditional preview paragraph, which said the same thing):

```markdown
## Prerequisite: enable the full-text search preview on the cluster

Full-text search (`createSearchIndexes` + `$search`) is a **preview** feature and is **off by default**. Enable it once per cluster before creating a search index or running `$search`:

- **Azure portal:** open the cluster > **Settings** > **Features** > **Full-text search** > **Enable**.
- **ARM / CLI / IaC:** add `"FullTextSearch"` to `properties.previewFeatures` on the `Microsoft.DocumentDB/mongoClusters` resource (api-version `2024-07-01`), preserving any other preview features already listed. Exact `az rest`, Terraform (AzAPI) and Bicep snippets: https://learn.microsoft.com/azure/documentdb/full-text-search-overview#enable-full-text-search
- **Wait ~10 minutes** after enabling. Seeing `FullTextSearch` in the resource configuration does not mean activation has finished.

Learn documents no cluster-tier restriction for full-text search (unlike HNSW/DiskANN vector indexes); the preview flag is the documented prerequisite. The GA `$text` operator and `{ field: "text" }` indexes are unaffected by the flag and are **not** a substitute.

**In generated samples:** do not assume the flag is on. Treat `createSearchIndexes` failing with `code: 115` / `codeName: "CommandNotSupported"` (errmsg `Search index creation is not supported yet`) as "feature not enabled yet": fail fast with a message that names the portal path and the Learn anchor above, and do not silently fall back to a `{ field: "text" }` index.
```

If open question 1 finds full-text search is GA, reword this section to whatever enablement remains and drop the "preview" wording.

**b. Add after the "Key syntax points" list, before `## Rules`** (from K17):

```markdown
## No external search service needed

Azure DocumentDB ships the full-text engine inside the cluster. BM25 search indexes (`createSearchIndexes` + `$search`) and vector indexes (`cosmosSearch`: vector-ivf / vector-hnsw / vector-diskann) live on the **same collection** and are included with the cluster at no extra cost. Hybrid retrieval is single-store: run both queries against the one collection and fuse with RRF (server-side with `$unionWith`, or client-side).

The Azure Cosmos DB for NoSQL / RU pattern of syncing documents into **Azure AI Search** (formerly Azure Cognitive Search) through a change feed, sync pipeline or custom ETL does **not** apply here. Azure AI Search remains an optional alternative for cross-source or enterprise search. It is not a prerequisite for full-text or hybrid search on Azure DocumentDB.

**Incorrect**: provision Azure AI Search, build a sync pipeline from the DocumentDB collection, run keyword and hybrid queries there, keep two stores in sync.

**Correct**: `runCommand({ createSearchIndexes })` + `$search` for BM25, `createIndex` with a `cosmosSearch` key for vectors, both on the same collection; fuse with RRF ([fts-hybrid-search](fts-hybrid-search.md)).
```

("no extra cost" is subject to open question 3.)

**c. Replace the `fts-hybrid-search` rule line** (from K18) with:

> - [fts-hybrid-search](fts-hybrid-search.md) — Combine BM25 and vector search on the same collection; fuse with RRF server-side (`$unionWith` + `$group`, one pipeline) or client-side when fusing additional ranked lists.

**d. Optional, frontmatter `description`** (from K18): append "server-side `$unionWith` RRF or client-side fusion", so the skill triggers on prompts that mention "server-side hybrid" or "RRF pipeline".

### 2. `skills/full-text-search/fts-create-search-index.md` (from K19)

**a. Add before `## Incorrect`:**

```markdown
## Prerequisite

Full-text search is in preview and must be enabled on the cluster first (portal: Settings > Features > Full-text search > Enable, or `previewFeatures: ["FullTextSearch"]` via ARM). Allow ~10 minutes after enabling. See https://learn.microsoft.com/azure/documentdb/full-text-search-overview#enable-full-text-search. On a cluster without the flag, `createSearchIndexes` returns `code 115 CommandNotSupported: "Search index creation is not supported yet"`.
```

**b. Append to `## Correct`** (Node.js shown; in pymongo check `OperationFailure.code`):

```javascript
try {
  await db.command({ createSearchIndexes: "products_10M", indexes: [/* ... */] });
} catch (err) {
  if (err.code === 115 /* CommandNotSupported */) {
    throw new Error(
      "Full-text search is not enabled on this Azure DocumentDB cluster. " +
      "Enable it (portal: Settings > Features > Full-text search > Enable, or add " +
      "\"FullTextSearch\" to previewFeatures), wait ~10 minutes, then rerun. " +
      "https://learn.microsoft.com/azure/documentdb/full-text-search-overview#enable-full-text-search"
    );
  }
  throw err;
}
```

**c. Add to the guidelines list:** "**Check the preview flag before you debug index syntax.** `CommandNotSupported` means the feature is off (or still activating), not that the index definition is wrong."

**d. Add to `## References`:**

- `[Full-text search overview: enable full-text search](https://learn.microsoft.com/azure/documentdb/full-text-search-overview#enable-full-text-search)`
- `[Full-text search limitations (preview)](https://learn.microsoft.com/azure/documentdb/limitations#full-text-search-limitations-preview)`

### 3. `skills/full-text-search/fts-hybrid-search.md`

**a. Replace the intro sentence** that starts "Azure DocumentDB supports both index types on the same collection..." with (from K18; also carries K17's "no external search service" point):

> Azure DocumentDB supports both index types on the same collection, so hybrid search needs no external search service. Fuse the two arms with Reciprocal Rank Fusion (RRF) in one of two ways. **Server-side** fusion runs in one aggregation pipeline (`$unionWith` + `$group`): one round trip and no fusion code. **Client-side** fusion runs both arms and fuses them in the app, which makes it easy to add more ranked lists. `$search` `compound` is not yet available (see `fts-multifield-index`), so the keyword arm is a single `text` clause either way.

The last sentence is subject to open question 2; if `compound` is now available, drop it.

**b. Rename the existing step 2** to "Option A: client-side RRF (extra ranked lists)". Leave its code unchanged.

**c. Add step 3, "Option B: server-side RRF with `$unionWith` (one round trip)"**, directly after Option A. The pipeline mirrors the one on Learn:

```javascript
// One aggregation, one round trip, no fusion code in the app.
// Each arm: $search -> collect hits in $search order -> rank -> 1/(k + rank + 1); $unionWith merges the arms.
const K = 60, DEPTH = 50, TOP_N = 10;
const qv = await embed(userQuery);

const fused = await db.products.aggregate([
  // Vector arm
  { $search: { cosmosSearch: { path: "embedding", vector: qv, k: DEPTH } } },
  { $group: { _id: null, hits: { $push: "$$ROOT" } } },          // preserves $search order
  { $unwind: { path: "$hits", includeArrayIndex: "rank" } },
  { $project: { _id: "$hits._id", title: "$hits.title",
                rrf: { $divide: [1, { $add: ["$rank", K, 1] }] } } },

  // Keyword arm, inlined on the same collection
  { $unionWith: {
      coll: "products",
      pipeline: [
        { $search: { index: "idx_description_fts", text: { query: userQuery, path: "description" } } },
        { $limit: DEPTH },
        { $group: { _id: null, hits: { $push: "$$ROOT" } } },
        { $unwind: { path: "$hits", includeArrayIndex: "rank" } },
        { $project: { _id: "$hits._id", title: "$hits.title",
                      rrf: { $divide: [1, { $add: ["$rank", K, 1] }] } } }
      ]
  }},

  // Fuse: sum the per-arm RRF contributions, rank, cut
  { $group: { _id: "$_id", title: { $first: "$title" }, score: { $sum: "$rrf" } } },
  { $sort: { score: -1 } },
  { $limit: TOP_N }
]).toArray();
```

To weight an arm, multiply that arm's `$divide` expression by a weight `w`, for example `{ $multiply: [w, { $divide: [...] }] }`, before the final `$group`.

**d. Add a "Which option?" table** after the code:

| Prefer | When |
|---|---|
| Server-side `$unionWith` (Option B) | Default for two arms, weighted or not. One round trip, no fusion code, and only the projected fields of the fused top N leave the server. |
| Client-side `rrf()` (Option A) | You fuse a third list (a phrase arm, another retriever, business signals) without rewriting the pipeline each time, or you cache one arm's results separately. |

**e. Tips.** Keep the existing tips (20-100 candidates per arm, weight multiplier, embedding cache, and the "when `compound` ships" tip, which is subject to open question 2). Say that `DEPTH` and `K` apply to both options. The weight tip today reads `score += w / (k + rank)`; rewrite it with the same formula the helper uses: `score += w / (k + rank + 1)`. Add one tip: each arm can use its own RRF `k`. Do not say which arm should get the larger `k` (open question 4).

**f. Replace the References section** (K17's list, which also covers K18's request to link the Learn hybrid page):

```markdown
## References

- [Full-text search overview](https://learn.microsoft.com/azure/documentdb/full-text-search-overview)
- [Hybrid search: combining BM25 and vector retrieval](https://learn.microsoft.com/azure/documentdb/full-text-search-hybrid): see "Architecture: two indexes, one collection" and the server-side `$unionWith` RRF variant
- [Vector search in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search)
```

### 4. `skills/indexing/index-text-prefer-textsearch.md` (from K17)

In "Why it matters", after the sentence "Don't reach for `"text"`-type indexes by reflex...", add:

```markdown
Likewise, don't reach for Azure AI Search (Cognitive Search) by reflex: that pattern comes from Cosmos DB for NoSQL / RU. On DocumentDB the BM25 engine is in the cluster, on the same collection as your documents and vector index.
```

In References, replace the bare `https://learn.microsoft.com/azure/documentdb/` link with `https://learn.microsoft.com/azure/documentdb/full-text-search-overview`.

### Out of scope

- Samples that used `createSearchIndexes` to create vector indexes (those belong to `createIndexes` + `cosmosSearch`); separate vector-search item.
- The `compound` drift between `SKILL.md` / `fts-multifield-index.md` / `fts-hybrid-search.md` ("not available yet") and the current Learn overview (lists `compound` with `equals`, `range`, `exists`, `in`); fix separately once open question 2 is answered.

## Evidence

Run folders in the experiment harness repository:

1. `runs/01-product-catalog-with-vector-search/20261124-175429/02-readiness.json`: Q09 wrong, confused with Cosmos DB for MongoDB RU; recommends change-feed sync into Cognitive Search (K17)
2. `runs/13-product-q-a-chatbot-rag/20261124-184527/02-readiness.json`: Q09 partly wrong; "hybrid/vector+text needs external search service" (K17)
3. `runs/01-unified-customer-profile-store/20261124-203120/02-readiness.json`: Q09 partly wrong; would replicate data into Azure Cognitive Search unnecessarily (K17)
4. `runs/19-insider-threat-detection-pipeline/20261124-202818/02-readiness.json`: Q09 cold answer fuses "in application"; grounded answer names `$unionWith` + `$group` (K18)
5. `runs/06-order-history-timeline-agent/20261124-183612/02-readiness.json`: improvement request asks for a kit example of server-side RRF with `$unionWith` (K18)
6. `runs/05-appointment-scheduling-assistant/20261124-193733/02-readiness.json`: Q09 cold answer "two-step (vector then re-rank)" (K18)
7. `runs/11-correspondent-banking-risk-screener/20261124-201541/` (`events.jsonl`, `04-decisions.md`): live code 115 from `createSearchIndexes`, script continued (K19)
8. `runs/07-voice-of-customer-sentiment-hub/20261124-204049/` (`doc-gaps.md`, `app/src/ingest.py`): error swallowed, fallback to `$text` index (K19)
9. `runs/10-support-ticket-rag-assistant/20261124-204529/02-readiness.json`: Q09 partly wrong; unsure whether the hosted service exposes the open-source engine's search (K17)
10. `runs/06-credit-risk-multi-agent-scorer/20261124-190546/02-readiness.json`: Q09 wrong; also notes the preview feature must be enabled (K17)
11. `runs/03-substitute-product-finder/20261124-183232/02-cold-answers.json`: Q09 reads "vector KNN ... re-ranking ... client-side" (K18)
12. `runs/05-churn-prediction-pipeline/20261124-203754/02-cold-answers.json`: Q09 reads "run two queries ... merge results in the app" (K18)
13. `runs/12-abandoned-cart-recovery-orchestration/20261125-054042/02-readiness.json`: readiness answer asks for the enablement step (K19)
14. `runs/15-financial-advisor-chatbot-rag/20261124-192021/02-readiness.json`: build-risk note about missing preview flag (K19)
15. `runs/04-natural-language-product-search/20261124-183232/app/indexes/README.md`: template with no enablement step (K19)

## Open questions

1. Is full-text search still in preview, and does it still need `FullTextSearch` enabled under `previewFeatures` with a ~10-minute wait, or has it reached GA (or a GA date been set)? Learn shows it as preview today. If GA, change the prerequisite text in changes 1a and 2a to whatever enablement remains and drop the "preview" wording. [needs SME confirmation]
2. Is `$search` `compound` still unavailable? `SKILL.md`, `fts-multifield-index.md` and `fts-hybrid-search.md` say it is not available yet, and the proposed hybrid intro (3a) repeats that, but the current Learn `full-text-search-overview` lists `compound` (with `equals`, `range`, `exists`, `in`) as available. [needs SME confirmation]
3. Are full-text and vector indexes included at no extra cost on every vCore tier, as the Learn hybrid page says, so the kit can state this without a qualifier (change 1b)? [needs SME confirmation]
4. The Learn tuning bullet says to use "larger k for the keyword query", but its example gives the keyword arm the smaller value (k = 10). Which direction is correct? Until engineering answers, this PR leaves the direction out (change 3e), and the Learn page may need its own fix. [needs SME confirmation]
5. Is `code 115 CommandNotSupported` / "Search index creation is not supported yet" the stable, intended error for a cluster without the feature, and also during the ~10-minute activation window? It was observed in run logs only; Learn does not document it. [needs SME confirmation]
6. Is there truly no tier or SKU restriction on full-text search? Learn's limitations page lists none; the proposed text says only that Learn documents none. [needs SME confirmation]

## Source drafts

- 022-believes-full-text-hybrid-search-requires-an-external-azure-.md
- 024-believes-hybrid-fusion-must-be-a-two-step-client-side-re-ran.md
- 025-skill-gap-full-text-search-is-a-preview-feature-that-must-be.md

## Merged from

- K17: full-text-search skill: say Azure AI Search is not required for full-text or hybrid search (P1, needs_sme, 67 samples)
- K18: fts-hybrid-search: add the server-side $unionWith RRF pipeline and when to prefer it (P1, needs_sme, 14 samples)
- K19: full-text-search skill: document the preview-enablement prerequisite and CommandNotSupported fail-fast (P2, needs_sme, 2 samples by finding id, 5 in run artifacts)
