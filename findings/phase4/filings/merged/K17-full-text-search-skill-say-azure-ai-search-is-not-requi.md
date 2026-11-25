---
id: K17
title: "full-text-search skill: say Azure AI Search is not required for full-text or hybrid search"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P1
sample_count: 67
member_drafts:
  - 022-believes-full-text-hybrid-search-requires-an-external-azure-.md
open_questions: 3
---

# full-text-search skill: say Azure AI Search is not required for full-text or hybrid search

## What happens today

The `documentdb-full-text-search` skill teaches the right API (`createSearchIndexes`, `$search`, `searchScore`, `cosmosSearch` vector indexes, RRF fusion), but it never names the wrong architecture that coding agents bring over from Azure Cosmos DB for NoSQL and Cosmos DB for MongoDB (RU): sync documents into Azure AI Search (formerly Azure Cognitive Search) through a change feed, indexer or custom ETL, and run BM25 and hybrid ranking there.

`grep -rniE 'ai search|cognitive|cosmos db for nosql|external search' skills/` returns no hits. The single-store fact is present only implicitly: the `SKILL.md` rule list says "Combine BM25 and vector search (RRF) on the same collection", and `fts-hybrid-search.md` says both index types work on the same collection. Nothing says that no external search service is needed. The references are also thin: `fts-hybrid-search.md` links only `vector-search` and `overview`, and `skills/indexing/index-text-prefer-textsearch.md` links the bare `https://learn.microsoft.com/azure/documentdb/` root. Neither links the Learn pages that state the point directly.

Microsoft Learn already says it: `full-text-search-overview` says the engine works without a separate search cluster, and `full-text-search-hybrid` has an "Architecture: two indexes, one collection" section saying there is no replication or synchronization layer and both index types are included at no extra cost. The gap is in the kit.

## Why it matters

We ran gpt-5-mini through an automated pipeline over 100 Azure DocumentDB sample prompts, with this kit installed. Before reading any guidance, the agent was asked "How are full-text search and hybrid search done?" In **67 of the 100 samples** it answered with the external-search pattern (69 findings: about 42 wrong, 27 partly wrong). Typical answers: "integrate Cosmos DB with Azure Cognitive Search (sync via change feed or an indexer)" and "hybrid/vector+text needs external search service". Of the 69 findings, the confusion was attributed to Cosmos DB for NoSQL in 39, Cosmos DB for MongoDB RU in 18, and doubt about whether the hosted service exposes open-source DocumentDB's search in 11 (68 in all; the source draft gives no attribution for the remaining one).

Impact was limited. Once the agent loaded this skill its answers were correct, and none of the generated apps actually wired up Azure AI Search (49 of 100 used `createSearchIndexes` / `$search`). So this change is preventive: an agent that skims `SKILL.md`, or that picks an architecture before opening the skill, is never told that the AI Search pattern does not apply. A few sentences fix that.

Counts come from one experiment run and some runs were repeated. Treat them as indicative.

## Proposed change

### 1. `skills/full-text-search/SKILL.md`

Add after the "Key syntax points" list (before `## Rules`):

```markdown
## No external search service needed

Azure DocumentDB ships the full-text engine inside the cluster. BM25 search indexes (`createSearchIndexes` + `$search`) and vector indexes (`cosmosSearch`: vector-ivf / vector-hnsw / vector-diskann) live on the **same collection** and are included with the cluster at no extra cost. Hybrid retrieval is single-store: run both queries against the one collection and fuse with RRF (client-side or with `$unionWith`).

The Azure Cosmos DB for NoSQL / RU pattern of syncing documents into **Azure AI Search** (formerly Azure Cognitive Search) through a change feed, sync pipeline or custom ETL does **not** apply here. Azure AI Search remains an optional alternative for cross-source or enterprise search. It is not a prerequisite for full-text or hybrid search on Azure DocumentDB.

**Incorrect**: provision Azure AI Search, build a sync pipeline from the DocumentDB collection, run keyword and hybrid queries there, keep two stores in sync.

**Correct**: `runCommand({ createSearchIndexes })` + `$search` for BM25, `createIndex` with a `cosmosSearch` key for vectors, both on the same collection; fuse with RRF ([fts-hybrid-search](fts-hybrid-search.md)).
```

Conditional on open question 1, add to the same section:

```markdown
Full-text search is a preview feature and must be enabled on the cluster first: portal Settings > Features > Full-text search, or add `FullTextSearch` to `properties.previewFeatures` on the `Microsoft.DocumentDB/mongoClusters` resource. Wait 10 minutes before creating a search index or running `$search`.
```

### 2. `skills/indexing/index-text-prefer-textsearch.md`

In "Why it matters", after the sentence "Don't reach for `"text"`-type indexes by reflex...", add:

```markdown
Likewise, don't reach for Azure AI Search (Cognitive Search) by reflex: that pattern comes from Cosmos DB for NoSQL / RU. On DocumentDB the BM25 engine is in the cluster, on the same collection as your documents and vector index.
```

In References, replace the bare `https://learn.microsoft.com/azure/documentdb/` link with `https://learn.microsoft.com/azure/documentdb/full-text-search-overview`.

### 3. `skills/full-text-search/fts-hybrid-search.md`

Replace the References section with:

```markdown
## References

- [Full-text search overview](https://learn.microsoft.com/azure/documentdb/full-text-search-overview)
- [Hybrid search: combining BM25 and vector retrieval](https://learn.microsoft.com/azure/documentdb/full-text-search-hybrid): see "Architecture: two indexes, one collection" and the server-side `$unionWith` RRF variant
- [Vector search in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search)
```

## Evidence

Each `02-readiness.json` holds the entry under `confusions[]` with the cold answer, grounded answer, `confused_with` and build risk. Paths are in the experiment harness repository:

- `runs/01-product-catalog-with-vector-search/20261124-175429/02-readiness.json`: wrong, confused with Cosmos DB for MongoDB RU; recommends change-feed sync into Cognitive Search
- `runs/13-product-q-a-chatbot-rag/20261124-184527/02-readiness.json`: partly wrong; "hybrid/vector+text needs external search service"
- `runs/10-support-ticket-rag-assistant/20261124-204529/02-readiness.json`: partly wrong; unsure whether the hosted service exposes the open-source engine's search
- `runs/06-credit-risk-multi-agent-scorer/20261124-190546/02-readiness.json`: wrong; also notes the preview feature must be enabled
- `runs/01-unified-customer-profile-store/20261124-203120/02-readiness.json`: partly wrong; would replicate data into Azure Cognitive Search unnecessarily

## Open questions

1. Is full-text search still in preview, and does it still need `FullTextSearch` enabled under `previewFeatures`, with a 10-minute wait? Learn shows it as preview today. If it is now GA, drop the conditional paragraph in change 1. [needs SME confirmation]
2. Learn `full-text-search-overview` now lists the `$search` `compound` operator (with `equals`, `range`, `exists`, `in`) as available, but `SKILL.md`, `fts-multifield-index.md` and `fts-hybrid-search.md` say `compound` is not available yet. Which is current? This is out of scope for this PR but should be fixed separately. [needs SME confirmation]
3. Can a maintainer confirm that full-text and vector indexes are included at no extra cost on every vCore tier, as the Learn hybrid page says, so the kit can state this without a qualifier? [needs SME confirmation]

## Source drafts

- 022-believes-full-text-hybrid-search-requires-an-external-azure-.md
