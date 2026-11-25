---
title: "vector-search: add an \"Incorrect\" example that names createSearchIndexes / knnVector / type:'vector' as the wrong surface for vector indexes"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 60
findings: 62
bucket: confusion-Q08
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# vector-search: name `createSearchIndexes` / `knnVector` / `type: 'vector'` as the wrong surface for vector indexes

## What happens today

The `vector-search` rules show the correct call (`db.coll.createIndex({ embedding: "cosmosSearch" }, { cosmosSearchOptions: {...} })`) and `vector-knn-query.md` already lists Atlas `$vectorSearch` under **Incorrect**. But nothing in `skills/vector-search/` says what *not* to use on the create side. The only place the kit draws the line is one comment in `skills/full-text-search/fts-hybrid-search.md` ("createSearchIndexes, not createIndexes" for BM25; "cosmosSearch, unchanged" for vectors), which an agent building a vector-only sample never opens.

Models arrive with the MongoDB Atlas / MongoDB 7 prior: `createSearchIndex(es)` with `type: "knnVector"` or `"vector"`, `createIndex({ embedding: "vector" })` with `engine`/`method` options, and `$vectorSearch` at query time. Because the kit also (correctly) teaches `createSearchIndexes` for full-text search, the two surfaces get merged into "DocumentDB vector indexes are created with createSearchIndexes".

## Why it matters

In a 100-sample readiness run with gpt-5-mini (DocumentDB Agent Kit + DocumentDB/Azure/Learn MCP servers), 62 findings across **60 of the 100 samples** had the cold answer to "which vector index types are supported, and what does the create command look like?" graded wrong or partly wrong with exactly this shape.

Most of those were corrected once the skill was read. Two were not, and the skill was loaded in both:

- **07-voice-of-customer-sentiment-hub**: `ingest.py` and `seed.py` send `createSearchIndexes` with `type: "vector-hnsw"`. The decision log says this was chosen "per documentdb-vector-search guidance". The live M30 cluster answered `CommandNotSupported` (code 115, "Search index creation is not supported yet" — the cluster did not have the Full-text search preview enabled, so the command itself was unavailable). The code caught the error and continued, so the sample shipped with no vector index and no error visible to the user ("Index creation verified: False" in the seed output).
- **14-customer-complaint-classifier**: `create_indexes.py` sends `createSearchIndexes` for the vector index, and `main.py` queries with `$search: { knn: ... }` instead of `$search: { cosmosSearch: ... }`. The audit stage marked the vector-index and vector-query requirements as **met**, so nothing caught it.

A negative example in the rule the agent actually reads is the cheapest way to stop this. The kit already uses that pattern for `$vectorSearch`.

## Proposed change

**1. `skills/vector-search/vector-create-diskann-index.md`** — add a second block under `## Incorrect`, before the existing "wrong dimensions" example:

```javascript
// Wrong command surface. These are Atlas / MongoDB 7 vector-index shapes, not
// Azure DocumentDB vector indexes. They either fail (createSearchIndexes is the
// full-text search preview command and returns CommandNotSupported when that
// preview is off) or never produce a cosmosSearch vector index.
db.runCommand({
  createSearchIndexes: "products",            // full-text (BM25) search indexes only, never vectors
  indexes: [{ name: "vec", type: "vector", fields: [{ path: "embedding", type: "vector", dimensions: 1536 }] }]
});
db.products.createIndex({ embedding: "vector" }, { engine: "hnsw", dimensions: 1536 });
db.products.createSearchIndex({ name: "vec", definition: { mappings: { fields: { embedding: { type: "knnVector", dimensions: 1536 } } } } });
```

followed by one sentence: *A vector index is an ordinary `createIndex` / `createIndexes` call whose key is `{ <field>: "cosmosSearch" }` with `cosmosSearchOptions` (`kind`: `vector-ivf`, `vector-hnsw` or `vector-diskann`), queried with `$search: { cosmosSearch: {...} }`. `createSearchIndexes` is the full-text search index command (preview, enabled per cluster); the two meet only at query time in hybrid search (see `fts-hybrid-search`).*

**2. `skills/vector-search/SKILL.md`** — add one bullet directly under the sub-type table:

> - Create it with `createIndex` / `createIndexes` and key `{ <field>: "cosmosSearch" }` + `cosmosSearchOptions` — **not** `createSearchIndexes`, `knnVector`, `type: "vector"` or `$vectorSearch`. Store vectors as `number[]`.

**3. `CHANGELOG.md`** — one entry: "vector-search: add Incorrect example for Atlas/MongoDB 7 vector-index shapes (`createSearchIndexes`, `knnVector`, `type: 'vector'`)."

Not proposed: changes to Microsoft Learn. The vector-search page already shows IVF/HNSW/DiskANN with `createIndexes` + `cosmosSearchOptions`; the confusion arises before any page is read. Several of the raw findings asked for a `createSearchIndexes` example on Learn — that wording is itself wrong and should not be filed.

## Evidence (run folders under `azure-documentdb-agent-readiness/runs/`)

- `07-voice-of-customer-sentiment-hub/20261124-204049` — `app/src/ingest.py:62-89`, `app/src/scripts/seed.py:20-40`; `decisions.jsonl` D008/D014; `events.jsonl` build `run_command` result with `codeName: CommandNotSupported`, `code: 115`
- `14-customer-complaint-classifier/20261124-201931` — `app/scripts/create_indexes.py:20-37`; `app/src/app/main.py:43` (`$search.knn`); `05-audit.json` requirement_results marked met
- `04-customer-journey-mapper/20261124-203553/02-readiness.json` — confusions[Q08], outcome wrong (`createIndex({embedding:'vector'})`, `algorithm:'hnsw'`)
- `08-personalized-email-campaign-builder/20261124-183709/02-readiness.json` — confusions[Q08] (`engine:'hnsw'`, `vector.dim`, `vector.metric`)
- `13-product-q-a-chatbot-rag/20261125-055422/02-readiness.json` — confusions[Q08], outcome wrong

Related: a separate theme proposes per-kind (HNSW/IVF) create templates for the same skill; if that lands first, this Incorrect block should go into the same file. Side note for the pipeline owner (not part of this PR): the audit in run 14 marked a `createSearchIndexes` vector index and a `$search.knn` query as met, so the audit does not validate the command surface.

## Verification

### 1. Already covered? — partially_covered

The correct create and query shapes are documented in both targets, but no kit rule names the wrong create-side surfaces, which is the specific gap.

- Kit `skills/vector-search/SKILL.md`: "Azure DocumentDB's native vector index type is `cosmosSearch`." Table of kinds; no create-side negative.
- Kit `skills/vector-search/vector-create-diskann-index.md`: the only `## Incorrect` block is the wrong-dimensions example; no mention of `createSearchIndexes`, `knnVector` or `type: "vector"`.
- Kit `skills/vector-search/vector-knn-query.md:11`: "Using Atlas Vector Search syntax (`$vectorSearch`) — not supported in DocumentDB" (query side only).
- Kit `skills/full-text-search/fts-hybrid-search.md:25`: "BM25 on the searchable text (createSearchIndexes, not createIndexes)" and "Vector on the embedding (cosmosSearch, unchanged)" — the only place the surfaces are separated, in a different skill.
- grep of `skills/` and `knowledge-base/` for `knnVector` and vector-typed `createSearchIndexes`: no hits.
- Learn https://learn.microsoft.com/en-us/azure/documentdb/vector-search documents `createIndexes` with key `"<path_to_property>": "cosmosSearch"` and `cosmosSearchOptions` kinds `vector-ivf`, `vector-hnsw`, `vector-diskann`, queried with `$search` + `cosmosSearch`. Learn needs no change, as the draft says.

### 2. Is the premise true? — confirmed (wording tightened)

- Vector index = `createIndexes` with `cosmosSearch` key + `cosmosSearchOptions`; query = `$search.cosmosSearch`; vectors must be `number[]` — confirmed on the Learn vector-search page ("Vectors must be a `number[]` to be indexed").
- `createSearchIndexes` is the full-text search command — confirmed on https://learn.microsoft.com/en-us/azure/documentdb/full-text-search-overview: "You create it with the `createSearchIndexes` database command"; hybrid is "Separate keyword and `cosmosSearch` queries combined with RRF".
- Correction applied: the draft attributed run 07's `CommandNotSupported` to the server rejecting a vector shape. The same Learn page says full-text search "remains in preview" and must be enabled per cluster (`previewFeatures: FullTextSearch`); the error "Search index creation is not supported yet" means the command itself was unavailable on that cluster. The Incorrect-block comment and the run-07 narrative now say this. Also replaced "fell back to a plain text index" (not supported by the run output) with "continued without a vector index" (seed output: "Index creation verified: False"), and corrected run-14's query description to `$search.knn` vs `$search.cosmosSearch`.
- Evidence spot-checked in run folders 07 and 14 (file/line references match; line ranges adjusted to 62-89 and 20-37).

### 3. Maintainer skeptic — confirmed

Names exact files (`skills/vector-search/vector-create-diskann-index.md`, `skills/vector-search/SKILL.md`, `CHANGELOG.md`), gives the exact block and bullet, follows the kit's existing Incorrect/Correct convention (same as the `$vectorSearch` example), is DocumentDB-specific, and is backed by two shipped builds where the loaded skill did not prevent the error. Small, low-risk docs PR I would accept.

## Finding ids

- F0006
- F0042
- F0150
- F0181
- F0216
- F0289
- F0317
- F0389
- F0423
- F0497
- F0527
- F0559
- F0630
- F0662
- F0697
- F0728
- F0766
- F0795
- F0826
- F0971
- F1002
- F1200
- F1300
- F1340
- F1372
- F1436
- F1489
- F1524
- F1133
- F1163
- F1658
- F1685
- F1719
- F1791
- F1828
- F1862
- F1892
- F1923
- F1953
- F1984
- F2019
- F2155
- F2218
- F2290
- F2327
- F2390
- F2461
- F2519
- F2592
- F2622
- F2714
- F2748
- F2877
- F2910
- F2942
- F3015
- F3043
- F3074
- F3228
- F3259
- F3325
- F3500
