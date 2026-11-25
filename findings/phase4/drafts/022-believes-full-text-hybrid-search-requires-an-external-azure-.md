---
title: "full-text-search skill: say explicitly that Azure AI Search / Cognitive Search is not required for full-text or hybrid search on Azure DocumentDB"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 67
findings: 69
bucket: confusion-Q09
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# full-text-search skill: state explicitly that Azure AI Search is not required for full-text or hybrid search

## What happens today

The `documentdb-full-text-search` skill teaches the right API (`createSearchIndexes`, `$search`, `searchScore`, `cosmosSearch`, RRF) but never names the wrong architecture that models carry over from Azure Cosmos DB for NoSQL / RU: push documents into Azure AI Search (formerly Azure Cognitive Search) via change feed or indexer, run BM25 and hybrid ranking there, and treat anything built in as "if offered".

`grep -rniE 'ai search|cognitive|cosmos db for nosql|external search' skills/` returns zero hits. The only cross-product contrast anywhere in the kit is the `$vectorSearch` (Atlas) note in `skills/vector-search/vector-knn-query.md`. The kit does say hybrid runs "on the same collection" (`SKILL.md` rule list and `fts-hybrid-search.md` "Why it matters"), so the single-store fact is present but implicit; it never says no external service is needed.

## Why it matters

In an experiment that ran gpt-5-mini through a readiness pipeline over 100 Azure DocumentDB sample prompts (with this kit installed plus the DocumentDB, Azure and Learn MCP servers), the cold-quiz question "How are full-text search and hybrid search done?" was answered with the external-search pattern in **67 of 100 samples** (42 wrong, 27 partly wrong). Typical cold answers:

- "For advanced/hybrid/full-text/semantic search, integrate Cosmos DB with Azure Cognitive Search (sync via change feed or an indexer)."
- "Usually by integrating Cosmos DB with Azure Cognitive Search or by using MongoDB text indexes; hybrid/vector+text needs external search service."
- "Use the service's integrated search or Azure Cognitive Search; combine text $search and vector kNN in application code; if $search exists you can combine."

The confusion was attributed to Cosmos DB for NoSQL in 39 cases, Cosmos DB for MongoDB RU in 18, and "unsure the hosted service exposes the engine's search" (open-source DocumentDB) in 11.

To be clear about impact: once the agent loaded this skill, the grounded answers were correct and **no built sample actually wired up Azure AI Search** (49 of the 100 generated apps used `createSearchIndexes` / `$search`). So the kit already fixes the behaviour once it is read. The gap is that the skill fixes it implicitly: an agent that only skims `SKILL.md`, or that decides architecture before opening the skill, is never told "the AI Search pattern you know from Cosmos DB does not apply here". Two sentences close that.

The Learn docs are not the gap. `full-text-search-overview` already says the engine works "without a separate search cluster", and `full-text-search-hybrid` has an "Architecture: two indexes, one collection" section that says there is no replication or synchronization layer to manage and both are included at no extra cost. The kit should carry the same sentence and link to those pages (today `fts-hybrid-search.md` links only to `vector-search` and `overview`, and `index-text-prefer-textsearch.md` links to the bare `/azure/documentdb/` root).

## Proposed change

### 1. `skills/full-text-search/SKILL.md`

Add after the "Key syntax points" list:

```markdown
## No external search service needed

Azure DocumentDB ships the full-text engine inside the cluster. BM25 search indexes (`createSearchIndexes` + `$search`) and vector indexes (`cosmosSearch`: vector-ivf / vector-hnsw / vector-diskann) live on the **same collection** and are included with the cluster at no extra cost. Hybrid retrieval is single-store: run both queries against the one collection and fuse with RRF (client-side or with `$unionWith`).

The Azure Cosmos DB for NoSQL / RU pattern of syncing documents into **Azure AI Search** (formerly Azure Cognitive Search) through a change feed, indexer or custom ETL does **not** apply here. Azure AI Search remains an optional alternative for cross-source or enterprise search; it is not a prerequisite for full-text or hybrid search on Azure DocumentDB.

**Incorrect** — provision Azure AI Search, build a sync pipeline from the DocumentDB collection, run keyword and hybrid queries there, keep two stores in sync.

**Correct** — `runCommand({ createSearchIndexes })` + `$search` for BM25, `createIndex({ field: "cosmosSearch" })` for vectors, both on the same collection; fuse with RRF ([fts-hybrid-search](fts-hybrid-search.md)).
```

Optional, same section: full-text search is in preview and must be enabled on the cluster first (portal Settings > Features > Full-text search, or add `FullTextSearch` to `properties.previewFeatures` on the `Microsoft.DocumentDB/mongoClusters` resource; wait 10 minutes before creating a search index or running `$search`). The kit does not mention this anywhere today, and the Learn overview page leads with it.

### 2. `skills/indexing/index-text-prefer-textsearch.md`

In "Why it matters", after "Don't reach for `"text"`-type indexes by reflex", add:

```markdown
Likewise, don't reach for Azure AI Search (Cognitive Search) by reflex: that pattern comes from Cosmos DB for NoSQL / RU. On DocumentDB the BM25 engine is in the cluster, on the same collection as your documents and vector index.
```

Also fix the References list: replace the bare `https://learn.microsoft.com/azure/documentdb/` link with `https://learn.microsoft.com/azure/documentdb/full-text-search-overview`.

### 3. `skills/full-text-search/fts-hybrid-search.md`

Replace the References section with:

```markdown
## References

- [Full-text search overview](https://learn.microsoft.com/azure/documentdb/full-text-search-overview)
- [Hybrid search: combining BM25 and vector retrieval](https://learn.microsoft.com/azure/documentdb/full-text-search-hybrid) — see "Architecture: two indexes, one collection" and the server-side `$unionWith` RRF variant
- [Vector search in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search)
```

(The Learn hybrid page also shows a server-side `$unionWith` RRF pipeline; the rule could link to it rather than duplicate it.)

Side note for the maintainer, not part of this PR: Learn `full-text-search-overview` now lists `compound` (with `equals`, `range`, `exists`, `in`) as available, while `SKILL.md` and `fts-hybrid-search.md` still say `$search` `compound` is not available yet. Worth a separate check.

## Evidence (run folders from the experiment)

Each `02-readiness.json` has the Q09 entry under `confusions[]` with `cold_answer`, `grounded_answer`, `confused_with` and `build_risk`:

- `runs/01-product-catalog-with-vector-search/20261124-175429/02-readiness.json` — wrong, confused with Cosmos DB for MongoDB RU; cold answer recommends change-feed sync into Cognitive Search
- `runs/13-product-q-a-chatbot-rag/20261124-184527/02-readiness.json` — partly wrong; "hybrid/vector+text needs external search service"
- `runs/10-support-ticket-rag-assistant/20261124-204529/02-readiness.json` — partly wrong, open-source DocumentDB variant; "if $search exists you can combine"
- `runs/06-credit-risk-multi-agent-scorer/20261124-190546/02-readiness.json` — wrong; also flags that the preview feature must be enabled
- `runs/01-unified-customer-profile-store/20261124-203120/02-readiness.json` — partly wrong; "replicate data into Azure Cognitive Search unnecessarily"

Full list: 69 findings across 67 distinct samples in bucket confusion-Q09 of the experiment's findings set.

## Verification

### 1. Already covered? partially_covered

- Agent kit: `grep -rniE 'ai search|cognitive|cosmos db for nosql|external search|separate search|previewFeatures|FullTextSearch' skills knowledge-base` in the Azure/documentdb-agent-kit clone returns no relevant hit (only an unrelated "separate search index per field" line in `skills/full-text-search/fts-multifield-index.md`). The single-store idea is present only implicitly: `skills/full-text-search/SKILL.md` rule list says "Combine BM25 and vector search (RRF) on the same collection", and `skills/full-text-search/fts-hybrid-search.md` says "Azure DocumentDB supports both index types on the same collection". Nothing names or rejects the Azure AI Search pattern, and nothing mentions enabling the preview.
- References: `fts-hybrid-search.md` cites `vector-search` and `overview`; `skills/indexing/index-text-prefer-textsearch.md` cites the bare `https://learn.microsoft.com/azure/documentdb/` root. Neither links `full-text-search-overview` or `full-text-search-hybrid`.
- Learn already covers it: https://learn.microsoft.com/en-us/azure/documentdb/full-text-search-overview (search works "without a separate search cluster"; Enable full-text search section) and https://learn.microsoft.com/en-us/azure/documentdb/full-text-search-hybrid ("Architecture: two indexes, one collection": no replication or synchronization layer, included at no extra cost). So the gap is in the kit, which is the draft's target.
- documentdb-mcp: no search-related guidance (grep for AI Search / Cognitive / createSearchIndexes found nothing); not the right place.

### 2. Premise true? confirmed

- Built-in BM25 full-text search via `createSearchIndexes` + `$search`, `searchScore` via `$meta`: confirmed by full-text-search-overview.
- Same cluster and collection as `cosmosSearch` vector indexes, no sync layer, no extra cost, RRF client-side or server-side with `$unionWith`: confirmed by full-text-search-hybrid.
- Preview and enablement: confirmed; overview says enable via portal Features, `az rest` PATCH adding `FullTextSearch` to `properties.previewFeatures` on `Microsoft.DocumentDB/mongoClusters`, Terraform or Bicep, then "wait 10 minutes". Draft's "~10 minutes" tightened to 10 minutes and enablement wording made concrete.
- Small corrections applied: the draft said the kit links "only to vector-search"; `fts-hybrid-search.md` also links `overview` (fixed). "Indexer" softened to "sync pipeline / custom ETL" in the Incorrect example so the kit does not imply a ready-made AI Search indexer for DocumentDB. Added a side note that Learn now lists `$search` `compound` as available, contradicting the kit's "No compound operator yet" (kept out of scope of this PR).
- Experiment counts (67 of 100 samples, 69 findings) come from the theme record in the experiment's findings set.

### 3. Maintainer skeptic: confirmed

Names exact files (`skills/full-text-search/SKILL.md`, `skills/indexing/index-text-prefer-textsearch.md`, `skills/full-text-search/fts-hybrid-search.md`), gives paste-ready text, is specific to Azure DocumentDB versus Cosmos DB for NoSQL / RU, matches Learn wording, and is small and low risk. As maintainer I would accept it; the change is preventive (no generated app used Azure AI Search), which the draft states honestly.

## Finding ids

- F0043
- F0074
- F0111
- F0151
- F0182
- F0261
- F0290
- F0352
- F0459
- F0528
- F0600
- F0663
- F0796
- F0827
- F0850
- F0891
- F0920
- F0972
- F1003
- F1043
- F1077
- F1105
- F1134
- F1164
- F1201
- F1227
- F1262
- F1301
- F1341
- F1373
- F1404
- F1490
- F1525
- F1627
- F1720
- F1756
- F1792
- F1829
- F1893
- F1924
- F2020
- F2055
- F2086
- F2124
- F2246
- F2291
- F2361
- F2428
- F2489
- F2520
- F2593
- F2651
- F2686
- F2781
- F2809
- F2911
- F2978
- F3044
- F1686
- F2188
- F2219
- F2715
- F2749
- F3147
- F3179
- F3362
- F3395
- F3428
- F3501
