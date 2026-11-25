---
title: "vector-search skill: add copy-paste createIndex rules for vector-hnsw and vector-ivf, plus an explicit 'Atlas knnVector/createSearchIndex is not the vector API' call-out"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 12
findings: 12
bucket: confusion-Q08
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# vector-search skill: add copy-paste `createIndex` rules for `vector-hnsw` and `vector-ivf`, and call out that Atlas `knnVector` / `createSearchIndex` is not the vector-index API

## What happens today

`skills/vector-search` gives a complete, parameterised `createIndex` example for one of the three supported kinds only:

- `vector-create-diskann-index.md` — full example with `dimensions`, `similarity`, `maxDegree`, `lBuild` and a parameter table. Good.
- `vector-hnsw` — **no example anywhere**. The strings `efConstruction` and `m` do not appear in any file under `skills/vector-search`; `vector-hnsw` appears only in the tier tables of `SKILL.md` and `vector-choose-index-type.md`.
- `vector-ivf` — `numLists` appears exactly once, inside the **Incorrect** block of `vector-choose-index-type.md` (the "don't use IVF for 200k vectors" example). There is no Correct IVF example.
- The only Atlas-shape warning is the query-time `$vectorSearch` block in `vector-knn-query.md`. Nothing in the skill says that Atlas `createSearchIndex` with a `knnVector` / `vectorSearch` mapping is not how a DocumentDB vector index is created. This matters doubly because the kit's `full-text-search` skill (correctly) tells the model that `createSearchIndexes` *is* a real DocumentDB command, so a model has to infer on its own that it is the BM25 command and not the vector one.

## Why it matters

In an experiment that ran 100 Azure DocumentDB sample prompts through gpt-5-mini with this kit plus the DocumentDB/Azure/Learn MCP servers, the cold-quiz question "Which vector index types are supported, and what does the command that creates one look like?" was answered wrong or partly wrong in 12 samples with the same failure shape: the model knew HNSW/IVF/DiskANN exist, then wrote an Atlas-style command because it had no DocumentDB parameter names for the kind it picked. Verbatim cold answers include:

- `createIndex({ embedding: 'knnVector' }, { knnVector: { dimensions: 1536, similarity: 'cosine', method: { name: 'hnsw', parameters: { efConstruction: 200, M: 16 } } } })` (20-provider-directory-semantic-search, outcome **wrong**)
- `db.runCommand({ createSearchIndex: "formulary_index", definition: { mappings: { fields: { embedding: { type: "knn_vector", method: { name: "hnsw", M: 16, efConstruction: 200 } } } } } })` (10-drug-formulary-semantic-search)
- `createIndex({ embedding: 'knnVector' }, { knnVector: { dimensions: 1536, method: 'hnsw', m: 16, efConstruction: 200 } })` (13-chronic-disease-risk-predictor, outcome **wrong**)

In every one of the 12 runs the grounded correction came from a Learn MCP search of the vector-search page, not from the kit — the kit had nothing to offer for HNSW. Builders do legitimately pick the non-DiskANN kinds: two of these samples shipped `vector-hnsw` indexes (`m: 16, efConstruction: 64`) assembled from Learn, and the 10-drug-formulary audit found the "semantic search" sample shipped with **no** index-creation code at all. Both are the predictable result of the skill naming the kind but not its parameters.

Learn already documents all three kinds, so this is a kit completeness gap, not a docs gap.

## Proposed change (PR)

Two new rule files in `skills/vector-search/`, same shape as `vector-create-diskann-index.md`, plus a short addition to `SKILL.md`.

### 1. `skills/vector-search/vector-create-hnsw-index.md`

```markdown
# vector-create-hnsw-index

**Category:** Vector Search · **Priority:** HIGH

## Why it matters

HNSW fits up to ~50k vectors on M30+ and can be built on an empty collection. Large HNSW indexes can exhaust cluster memory; move to DiskANN or a larger tier if that happens. The DocumentDB
parameter names are `m` and `efConstruction` (build time) and `efSearch` (query time). Atlas
`knnVector` / `createSearchIndex` shapes are rejected by DocumentDB.

| Parameter | Range | Default | Notes |
|---|---|---|---|
| `dimensions` | up to 2,000 (4,000 with half-precision) | — | Must match the embedding model exactly; product quantization (16,000 dims) is DiskANN-only |
| `similarity` | `COS`, `L2`, `IP` | — | `COS` for normalized text embeddings |
| `m` | 2–100 | 16 | Max connections per layer; higher → recall, memory |
| `efConstruction` | 4–1000, and at least `2 * m` | 64 | Build-time candidate list; higher → quality, slower build |
| `efSearch` (query-time) | integer | 40 | Set inside `cosmosSearch` in `$search`; higher → better recall, slower; keep it ≥ `k` |

## Incorrect

Atlas Search index definition — DocumentDB does not create vector indexes this way:

```javascript
db.products.createSearchIndex({
  name: "vec", type: "vectorSearch",
  definition: { fields: [{ type: "vector", path: "embedding", numDimensions: 1536, similarity: "cosine" }] }
});
// Also wrong: createIndex({ embedding: "knnVector" }, { knnVector: {...} })
```

## Correct

```javascript
db.products.createIndex(
  { embedding: "cosmosSearch" },
  {
    name: "products_embedding_hnsw",
    cosmosSearchOptions: { kind: "vector-hnsw", dimensions: 1536, similarity: "COS", m: 16, efConstruction: 64 }
  }
);

// Equivalent database command (drivers without createIndex options passthrough):
db.runCommand({
  createIndexes: "products",
  indexes: [{
    name: "products_embedding_hnsw",
    key: { embedding: "cosmosSearch" },
    cosmosSearchOptions: { kind: "vector-hnsw", dimensions: 1536, similarity: "COS", m: 16, efConstruction: 64 }
  }]
});
```

Store vectors as plain `number[]` arrays — BSON binary vectors are not indexed. Query with
`$search: { cosmosSearch: { path, vector, k, efSearch } }` (see vector-knn-query).

## References

- [Vector search — HNSW](https://learn.microsoft.com/azure/documentdb/vector-search)
```

### 2. `skills/vector-search/vector-create-ivf-index.md`

Same layout. Parameter table: `dimensions` (up to 2,000; 4,000 with half-precision), `similarity`, `numLists` (number of clusters; Learn's guidance is `documentCount/1000` up to 1M documents, and DiskANN above 1M; `numLists: 1` is effectively brute-force search, fine for a small demo), query-time `nProbes` (default 1, must not exceed `numLists`). Note that IVF is the recommended kind on M10/M20 (HNSW and DiskANN need M30+), and that `numLists` is sized from the document count, so re-tune it (or rebuild the index) as the collection grows. Correct block:

```javascript
db.products.createIndex(
  { embedding: "cosmosSearch" },
  {
    name: "products_embedding_ivf",
    cosmosSearchOptions: { kind: "vector-ivf", dimensions: 1536, similarity: "COS", numLists: 100 }
  }
);
```

plus the `db.runCommand({ createIndexes: ... })` equivalent and the same Atlas Incorrect block.

### 3. `skills/vector-search/SKILL.md`

Add under the tier table:

```markdown
**Not the API:** a DocumentDB vector index is always `createIndex`/`createIndexes` with key
`{ <field>: "cosmosSearch" }` and a `cosmosSearchOptions` block whose `kind` is `vector-ivf`,
`vector-hnsw` or `vector-diskann`. Atlas `createSearchIndex` / `knnVector` / `type: "vectorSearch"`
are rejected. DocumentDB's own `createSearchIndexes` command is for BM25 full-text indexes only
(see the full-text-search skill) and never creates a vector index. Vectors must be `number[]`;
BSON binary vectors are not indexed.
```

and two Rules entries:

```markdown
- [vector-create-hnsw-index](vector-create-hnsw-index.md) — Create a `vector-hnsw` index with `m` / `efConstruction`; tune `efSearch` at query time.
- [vector-create-ivf-index](vector-create-ivf-index.md) — Create a `vector-ivf` index with `numLists` (M10/M20); tune `nProbes` at query time.
```

Optionally mirror the parameter rows into `skills/query-optimizer/references/core-indexing-principles.md`, which already lists `vector-hnsw` in a tier table with no parameters.

All values above were checked against the Learn vector-search page (https://learn.microsoft.com/en-us/azure/documentdb/vector-search): HNSW `m` 2–100 default 16, `efConstruction` 4–1000 default 64 and at least `2 * m`, `efSearch` default 40; IVF `numLists` = documentCount/1000, `nProbes` default 1 and ≤ `numLists`; COS/L2/IP; IVF on M10/M20, HNSW/DiskANN on M30+; 2,000 dims max without compression, 4,000 with half-precision for HNSW/IVF, 16,000 with PQ for DiskANN only; vectors must be `number[]`.

## Evidence (run folders from the experiment)

- `runs/20-provider-directory-semantic-search/20261124-200008/02-readiness.json` — confusions[Q08], outcome wrong (knnVector + `efConstruction: 200, M: 16`); `app/seed.py` ends up with `vector-hnsw { m: 16, efConstruction: 64 }` sourced from Learn.
- `runs/10-drug-formulary-semantic-search/20261124-194440/02-readiness.json` — confusions[Q08] (`createSearchIndex` + `knn_vector`); `05-audit.json` — no `createIndexes`/`cosmosSearchOptions` call anywhere in the shipped app.
- `runs/13-chronic-disease-risk-predictor/20261124-194916/02-readiness.json` — confusions[Q08], outcome wrong.
- `runs/18-sanctions-list-screening-agent/20261124-202645/doc-gaps.md` and `app/scripts/create_vector_index.py` — builder picked `vector-hnsw`, then asked for `m`/`efConstruction`/`efSearch` tuning guidance the kit does not have.
- `runs/15-cohort-analysis-backend/20261124-205336/02-readiness.json` — confusions[Q08], outcome wrong.

Other samples hitting the same gap: 09-trade-settlement-tracker, 14-loan-origination-workflow-orchestration, 16-atm-network-status-monitor, 16-subscription-billing-engine, 17-esg-scoring-pipeline, 19-care-coordination-multi-agent, 20-open-banking-api-cache-layer.

## Verification

### 1. Already covered? confirmed (not in the kit)

I grepped the kit clone (`skills/` and `knowledge-base/`) for `efConstruction`, `vector-hnsw`, `numLists`, `nProbes`, `efSearch`, `knnVector` and `createSearchIndex`:
- `skills/vector-search/` holds SKILL.md, vector-choose-index-type.md, vector-create-diskann-index.md, vector-half-precision.md, vector-knn-query.md, vector-normalize-embeddings.md and vector-product-quantization.md. No HNSW or IVF creation rule exists.
- `efConstruction`, `efSearch`, `nProbes` and `knnVector` have no matches anywhere in `skills/` or `knowledge-base/`.
- `vector-hnsw` appears only in tier tables: `skills/vector-search/SKILL.md:14`, `skills/vector-search/vector-choose-index-type.md:12` and `skills/query-optimizer/references/core-indexing-principles.md:174`.
- `numLists` appears only once, in the Incorrect block at `skills/vector-search/vector-choose-index-type.md:22`.
- Every `createSearchIndexes` match is in the full-text-search, indexing and query-optimizer files and teaches BM25 search indexes. No file says that this command, or Atlas `createSearchIndex`/`knnVector`, is not how you create a vector index.

Learn already has full HNSW and IVF templates (https://learn.microsoft.com/en-us/azure/documentdb/vector-search, HNSW and IVF tabs). That is why the agents in these runs got their corrections from the Learn MCP server. The kit itself has the gap, so the fix belongs in the kit and not in Learn.

### 2. Is the premise true? confirmed, with corrections applied

The core premise holds. The kit has no HNSW or IVF creation example, and the correct shape is `createIndexes` with key `{ <field>: "cosmosSearch" }` and `cosmosSearchOptions.kind` set to vector-ivf, vector-hnsw or vector-diskann. I checked the draft's numbers against https://learn.microsoft.com/en-us/azure/documentdb/vector-search (updated 2026-11-25) and corrected these:
- HNSW `dimensions` was given as "1-2,000 (16,000 with PQ)". This is wrong: the page says "With DiskANN and product quantization, you can index vectors up to 16,000 dimensions" and "Using HNSW or IVF with half-precision allows indexing of vectors up to 4,000 dimensions". I changed it to 2,000 max, or 4,000 with half-precision, and noted that PQ is DiskANN-only.
- `efConstruction`: added the Learn constraint that it "has to be at least `2 * m`".
- `efSearch`: Learn gives only the default (40), not a 1-1000 range, so I removed the invented range.
- IVF `numLists`: Learn gives no range and no default of 100. Its guidance is `documentCount/1000` up to 1M documents, DiskANN above 1M, and `numLists: 1` acts as brute-force search. I replaced the invented range and default with this guidance.
- IVF "must be built after the data is loaded (it trains on existing vectors)": Learn does not say this, and its own IVF example creates the index before inserting documents. I reworded it to say that `numLists` is sized from document count and should be re-tuned as the collection grows.
- "IVF is the only kind available on M10/M20": I softened this to match Learn's recommended tiers (IVF on M10 or M20, HNSW and DiskANN on M30 and higher).

These claims were checked and kept: m is 2-100 with default 16; efConstruction is 4-1000 with default 64; nProbes defaults to 1 and can't exceed numLists; similarity is COS, L2 or IP; vectors must be `number[]` (Learn says another type "prevents the document from being indexed"); HNSW can be built on an empty collection; and the kit's full-text-search skill documents `createSearchIndexes` as the BM25 command (`skills/full-text-search/SKILL.md:13`).

### 3. Maintainer skeptic: confirmed

As a maintainer of Azure/documentdb-agent-kit, I would accept this PR. It names exact new files (`skills/vector-search/vector-create-hnsw-index.md` and `vector-create-ivf-index.md`) and the edits to `SKILL.md`. It copies the structure of the existing `vector-create-diskann-index.md`, it is specific to DocumentDB (cosmosSearch parameters and the contrast with the Atlas API), and 12 sample runs back it. After the corrections above, the parameter values match Learn. The only edit I would expect in review is the optional mirror into `core-indexing-principles.md`.

## Finding ids

- F1559
- F1591
- F2187
- F2427
- F2488
- F2650
- F2780
- F2843
- F3112
- F3146
- F3427
- F3460
