---
id: K18
title: "fts-hybrid-search: add the server-side $unionWith RRF pipeline and when to prefer it"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P1
sample_count: 14
member_drafts:
  - 024-believes-hybrid-fusion-must-be-a-two-step-client-side-re-ran.md
open_questions: 3
---

# fts-hybrid-search: add the server-side `$unionWith` RRF pipeline and when to prefer it

## What happens today

`skills/full-text-search/fts-hybrid-search.md` teaches hybrid search in three steps: run the keyword `$search` arm, run the `cosmosSearch` vector arm, then fuse the two result arrays with a JavaScript `rrf()` helper. Its intro says you can "execute both queries in one round trip and combine them in the application". The example actually makes two aggregation calls and fuses the results in the app, so it is not one round trip. Nothing in the kit mentions `$unionWith` or server-side fusion. `grep -rniE 'unionWith|server-side'` over `skills/` and `knowledge-base/` finds only two unrelated lines. `SKILL.md` describes the rule only as "Combine BM25 and vector search (RRF) on the same collection". The References list does not link the Learn hybrid-search page.

The Learn page [Hybrid search in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/full-text-search-hybrid) documents both options. One is a client-side `rrf()` helper. The other is a section called "Server-side RRF with `$unionWith`", which fuses both arms in one aggregation pipeline. The page recommends the server-side variant when you want a single round trip and no fusion code in the app. It recommends the client-side helper when you also need to fuse more ranked lists. Per-arm weighting works in both variants.

## Why it matters

This came out of one experiment run: 100 sample apps built by an agent (gpt-5-mini) that had this kit plus the DocumentDB, Azure and Learn MCP servers. All counts below come from that single run. Before grounding, the agent was asked "How are full-text search and hybrid search done?". In **14 of the 100 samples**, it answered that hybrid search is a two-step fusion done in the application. Typically it ran vector kNN for candidate ids and then filtered or BM25-re-ranked them "in application code". Some answers reversed the order. The grounding step corrected each of these answers from the Learn page. Several of the 14 readiness reports explicitly asked the kit for a `$unionWith` / server-side RRF example. None of the 14 built apps used `$unionWith`. The apps that implemented hybrid search copied the kit's client-side `rrf()` pattern. This skill is the file the agent loads for the task, and today it reinforces the client-side-only belief.

## Proposed change

### `skills/full-text-search/fts-hybrid-search.md`

**1. Replace the intro sentence** that starts "Azure DocumentDB supports both index types on the same collection..." with:

> Azure DocumentDB supports both index types on the same collection, so hybrid search needs no external search service. Fuse the two arms with Reciprocal Rank Fusion (RRF) in one of two ways. **Server-side** fusion runs in one aggregation pipeline (`$unionWith` + `$group`): one round trip and no fusion code. **Client-side** fusion runs both arms and fuses them in the app, which makes it easy to add more ranked lists. `$search` `compound` is not yet available (see `fts-multifield-index`), so the keyword arm is a single `text` clause either way.

**2. Rename the existing step 2** to "Option A: client-side RRF (extra ranked lists)". Leave its code unchanged.

**3. Add step 3, "Option B: server-side RRF with `$unionWith` (one round trip)"**, directly after Option A. The pipeline mirrors the one on Learn:

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

**4. Add a "Which option?" table** after the code:

| Prefer | When |
|---|---|
| Server-side `$unionWith` (Option B) | Default for two arms, weighted or not. One round trip, no fusion code, and only the projected fields of the fused top N leave the server. |
| Client-side `rrf()` (Option A) | You fuse a third list (a phrase arm, another retriever, business signals) without rewriting the pipeline each time, or you cache one arm's results separately. |

**5. Tips.** Keep the existing tips (20-100 candidates per arm, weight multiplier, embedding cache). Say that `DEPTH` and `K` apply to both options. Write the weight tip with the same formula the helper uses: `score += w / (k + rank + 1)`. Add one tip: each arm can use its own RRF `k`. Do not say which arm should get the larger `k` (see Open questions).

**6. References.** Add `[Hybrid search in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/full-text-search-hybrid)`.

### `skills/full-text-search/SKILL.md`

Replace the rule line with:

> - [fts-hybrid-search](fts-hybrid-search.md) — Combine BM25 and vector search on the same collection; fuse with RRF server-side (`$unionWith` + `$group`, one pipeline) or client-side when fusing additional ranked lists.

Optionally, append "server-side `$unionWith` RRF or client-side fusion" to the frontmatter `description`, so the skill triggers on prompts that mention "server-side hybrid" or "RRF pipeline".

## Evidence

Run folders in the experiment harness, under `runs/`:

- `runs/05-appointment-scheduling-assistant/20261124-193733/02-readiness.json`: confusion Q09. The cold answer is "two-step (vector then re-rank)".
- `runs/19-insider-threat-detection-pipeline/20261124-202818/02-readiness.json`: confusion Q09. The cold answer fuses "in application". The grounded answer names `$unionWith` + `$group`.
- `runs/03-substitute-product-finder/20261124-183232/02-cold-answers.json`: Q09 reads "vector KNN ... re-ranking ... client-side".
- `runs/06-order-history-timeline-agent/20261124-183612/02-readiness.json`: the improvement request asks for a kit example of server-side RRF with `$unionWith`.
- `runs/05-churn-prediction-pipeline/20261124-203754/02-cold-answers.json`: Q09 reads "run two queries ... merge results in the app".

## Open questions

1. [needs SME confirmation] Full-text search (`$search` with BM25 indexes) still carries a "preview" label on Learn. Is it GA now? The skill's wording should match the current status.
2. [needs SME confirmation] Is `$search` `compound` still unavailable? The proposed intro repeats the kit's existing statement that it is.
3. [needs SME confirmation] The Learn tuning bullet says to use "larger k for the keyword query", but its example gives the keyword arm the smaller value (k = 10). Which direction is correct? Until engineering answers, this PR leaves the direction out, and the Learn page may need its own fix.

## Source drafts

- 024-believes-hybrid-fusion-must-be-a-two-step-client-side-re-ran.md
