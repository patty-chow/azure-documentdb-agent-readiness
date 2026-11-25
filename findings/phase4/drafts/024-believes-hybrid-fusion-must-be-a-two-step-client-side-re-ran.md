---
title: "fts-hybrid-search: add the server-side $unionWith RRF pipeline and say when to prefer it over client-side rrf()"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 14
findings: 14
bucket: confusion-Q09
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# fts-hybrid-search: add the server-side `$unionWith` RRF pipeline and say when to prefer it over client-side `rrf()`

## What happens today

`skills/full-text-search/fts-hybrid-search.md` teaches hybrid search as: run the keyword `$search` arm, run the `cosmosSearch` arm, then fuse the two arrays with a JavaScript `rrf()` helper. The intro sentence says Azure DocumentDB lets you "execute both queries in one round trip and combine them in the application". As written, the example is two aggregation calls plus fusion code in the app, not one round trip. Nothing in the kit mentions `$unionWith` or server-side fusion:

```
$ grep -rniE 'unionWith|server-side' skills/ knowledge-base/
skills/full-text-search/fts-multifield-index.md:141: ... switch fan-out merge to a server-side `should` ...
skills/natural-language-querying/SKILL.md:101: ... server-side implementation is `aggregate([{ $sample: { size } }])`
```

The Learn page [Hybrid search in Azure DocumentDB](https://learn.microsoft.com/en-us/azure/documentdb/full-text-search-hybrid) documents two fusion options: a client-side `rrf()` helper (Step 3) and a section titled **Server-side RRF with `$unionWith`** that fuses both arms in one aggregation pipeline using standard stages plus `$search`. It recommends the server-side variant when you want a single round trip and no client-side fusion code. It recommends the client-side helper when you also want to fuse more ranked lists, such as phrase results or a third retriever. Per-arm weighting works in both variants: in the `$unionWith` variant, you multiply the per-query `$divide` expression by the weight.

## Why it matters

The experiment ran 100 samples with gpt-5-mini, this kit, and the DocumentDB, Azure and Learn MCP servers. In **14 of 100 samples**, the model's cold answer to "How are full-text search and hybrid search done?" said hybrid search is a two-step fusion done in the application. Usually the model ran vector kNN for candidate ids, then filtered or BM25-re-ranked them "in application code". Some answers ran text first and vector second. Representative cold answers:

- "Use MongoDB text indexes and two-step (vector then re-rank) approach" (05-appointment-scheduling-assistant)
- "run a vector KNN to get candidates and then applying text filtering or BM25 re-ranking in a subsequent stage or client-side" (03-substitute-product-finder)
- "execute vector NN then run text index queries or combine both results in application" (19-insider-threat-detection-pipeline)
- "run two queries ... and merge results in the app" (05-churn-prediction-pipeline)

The grounding stage corrected every one of these from the Learn hybrid page. Several of the 14 readiness reports explicitly asked for a `$unionWith` / server-side RRF example in the agent kit. None of the 14 built apps used `$unionWith`. The apps that implemented hybrid search copied the kit's client-side `rrf()` pattern. The kit skill is the artifact the agent loads for this task. Today it confirms the client-side-only prior instead of showing the server-side option.

## Proposed change

### 1. `skills/full-text-search/fts-hybrid-search.md`

**a. Reword the intro.** Replace the sentence that starts "Azure DocumentDB supports both index types on the same collection..." with:

> Azure DocumentDB supports both index types on the same collection, so hybrid search needs no external search service. Fuse the two arms with Reciprocal Rank Fusion (RRF) in one of two ways. **Server-side** fusion runs in one aggregation pipeline (`$unionWith` + `$group`): one round trip and no fusion code. **Client-side** fusion runs both arms and fuses them in the app, which makes it easy to add more ranked lists. `$search` `compound` is not yet available (see `fts-multifield-index`), so the keyword arm is a single `text` clause either way.

**b. Rename the existing step 2** to "Option A: client-side RRF (extra ranked lists)" and keep its code as is.

**c. Add step 3, "Option B: server-side RRF with `$unionWith` (one round trip)"**, after it. The code below mirrors the Learn pipeline:

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

To weight one arm, multiply that arm's `$divide` expression by a weight `w` (for example, `{ $multiply: [w, { $divide: [...] }] }`) before the final `$group`.

**d. Add a "Which option?" block** after the code:

| Prefer | When |
|---|---|
| Server-side `$unionWith` (Option B) | Default for two arms, weighted or not. One round trip, no fusion code, and only the projected fields of the fused top N leave the server. |
| Client-side `rrf()` (Option A) | You fuse a third list (phrase arm, another retriever, business signals) without rewriting the pipeline each time, or you cache one arm's results separately. |

**e. Keep the Tips list** (depth 20-100 per arm, weight multiplier, embedding cache) and state that `DEPTH` and `K` apply to both options. Harmonize the weight tip with the helper's formula as `score += w / (k + rank + 1)`. Add one tip: a different RRF `k` can be used per arm.

**f. Add to References:** `[Hybrid search in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/full-text-search-hybrid)`. Today only the vector-search and overview pages are linked.

### 2. `skills/full-text-search/SKILL.md`

Change the rule line to:

> - [fts-hybrid-search](fts-hybrid-search.md) — Combine BM25 and vector search on the same collection; fuse with RRF server-side (`$unionWith` + `$group`, one pipeline) or client-side when fusing additional ranked lists.

Optionally, append "server-side `$unionWith` RRF or client-side fusion" to the frontmatter `description` so the skill triggers on prompts about "server-side hybrid" or "RRF pipeline".

This change can ship in the same PR as the "no external search service needed" note, because both touch the same skill folder.

## Evidence (run folders under azure-documentdb-agent-readiness/runs/)

- `runs/05-appointment-scheduling-assistant/20261124-193733/02-readiness.json`: confusions[Q09]. The cold answer is "two-step (vector then re-rank)". The grounded answer says hybrid search is supported server-side with fusion.
- `runs/19-insider-threat-detection-pipeline/20261124-202818/02-readiness.json`: confusions[Q09]. The cold answer fuses "in application". The grounded answer names server-side RRF / `$unionWith` + `$group`.
- `runs/03-substitute-product-finder/20261124-183232/02-cold-answers.json`: Q09 answer is "vector KNN to get candidates ... re-ranking ... client-side".
- `runs/06-order-history-timeline-agent/20261124-183612/02-readiness.json`: confusions[Q09].improvements asks for a "dedicated example in the agent kit showing server-side RRF fusion with $unionWith".
- `runs/05-churn-prediction-pipeline/20261124-203754/02-cold-answers.json`: Q09 answer is "run two queries ... merge results in the app".

Other affected samples (same Q09 confusion): 02-clinical-trial-matching-orchestration, 02-transaction-categorization-agent, 03-medication-interaction-checker, 03-next-best-action-multi-agent, 04-earnings-call-rag-assistant, 05-branch-performance-analytics, 09-inventory-reorder-multi-agent-system, 19-option-chain-data-store, 19-proactive-outreach-orchestration.

## Verification

### 1. Already covered? confirmed (not in the target)

- Agent kit: `grep -rniE 'unionWith|server-side'` over `skills/` and `knowledge-base/` finds no hybrid or `$unionWith` content. The only hits are an unrelated `compound`/`should` note in `fts-multifield-index.md:141` and `$sample` in `natural-language-querying/SKILL.md:101`. `skills/full-text-search/fts-hybrid-search.md` line 12 reads: "you can execute both queries in one round trip and combine them in the application". It shows only the client-side `rrf()` helper. Its References list does not link the Learn hybrid page. `SKILL.md:28` says only "Combine BM25 and vector search (RRF) on the same collection."
- Learn already covers the content, in the section "Server-side RRF with `$unionWith`" on https://learn.microsoft.com/en-us/azure/documentdb/full-text-search-hybrid (updated 2026-11-17). That page is the source to mirror. The gap is in the kit, which is the fix target.

### 2. Premise true? confirmed (with corrections applied)

- Confirmed against the Learn hybrid page: both indexes live on the same collection (`createSearchIndexes` for BM25, `createIndex` with `cosmosSearch` for vectors). The page documents a single-pipeline fusion: vector `$search` (cosmosSearch) -> `$group` `$push: "$$ROOT"` -> `$unwind` with `includeArrayIndex: "rank"` -> `$project` `rrf: 1/(rank + k + 1)`, then `$unionWith` that inlines the keyword `$search` arm (with `$limit`) shaped the same way, then `$group` `$sum` + `$sort` + `$limit`. Guidance from the page: "Use the server-side variant when you want a single round-trip and no client-side fusion code. Use the client-side rrf() helper when you also want to fuse in additional ranked lists."
- Corrections applied to the body:
  - (a) The draft said per-arm weighting is a reason to stay client-side. Learn says weighting works in the `$unionWith` variant by multiplying the per-query `$divide` expression by the weight. The "Which option?" table and the weighting note now reflect this.
  - (b) The code now mirrors Learn's `$push: "$$ROOT"` shaping with `title` carried through. The earlier version pushed only ids and then added a `$lookup` rehydrate stage.
  - (c) The draft said "8 of the 14" reports asked for the example and that exactly three apps did hybrid. These counts were not re-verified, so they were softened to "several" and "the apps that implemented hybrid search". The `$unionWith` requests were spot-checked in 06-order-history-timeline-agent and 19-insider-threat-detection-pipeline.
  - (d) The per-arm `k` tip no longer gives a direction. The Learn tuning bullet is internally inconsistent: it says "larger k for the keyword query" but its example gives the keyword arm k = 10, the smaller value. The kit should not copy that example. This is a possible separate Learn fix.
- The draft's other claims are consistent with the facts given: cosmosSearch vector index, `$search` text index (not Atlas Search), and the `compound` operator not yet available.

### 3. Maintainer skeptic: confirmed

- The change names exact files (`skills/full-text-search/fts-hybrid-search.md`, `skills/full-text-search/SKILL.md`) and gives concrete text and code mirrored from the official Learn page. The ask is specific to Azure DocumentDB and fixes a misleading sentence ("one round trip ... combine them in the application"). It fits the kit's existing rule format (Incorrect/Correct, Tips, References). As a maintainer I would accept it as a PR.

## Finding ids

- F0217
- F0318
- F0390
- F0424
- F0498
- F0560
- F0698
- F0729
- F0767
- F0946
- F1437
- F3260
- F3300
- F3326
