---
title: "vector-search skill: create and verify the cosmosSearch index from application code (never only via the MCP tool), store vectors as number[], and ship one canonical $search pipeline"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 26
findings: 57
bucket: sample-violated-practice
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# vector-search skill: create the cosmosSearch index from application code (never only via the MCP tool), store vectors as number[], and ship one canonical $search pipeline

## What happens today

In an experiment that built 100 Azure DocumentDB samples with gpt-5-mini using this kit's skills plus the documentdb MCP server, **26 samples** (the vector/RAG samples) shared one defect family: server-side `cosmosSearch` was treated as optional.

1. **Index never created, no fallback.** 12 of the 26 hit the documentdb-mcp management gate while trying to create the vector index with `create_index` (exposed as `documentdb_create_index`). That tool has `requiredRole: 'management'` (documentdb-mcp `src/tools/index-tools.ts`) and management tools are off by default (`ENABLE_MANAGEMENT_TOOLS=false`, also in this kit's own `mcp.json`). The call failed with `Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true to opt in.`, the seed script and README contained no `createIndexes` command, and `documentdb_list_indexes` later showed only `_id`. Retrieval then degraded to `find({})` pulling every embedding over the wire and computing cosine similarity in Python/JS, with 1536-float arrays returned in user-facing responses.
2. **Atlas / community priors in the queries that were written:** `$search: { knnBeta: ... }` instead of `$search: { cosmosSearch: { vector, path, k, ... } }`; index key `{ cosmosSearch: "cosmosSearch" }` instead of `{ embedding: "cosmosSearch" }` (runtime error `Similarity index not found`); no `{ $meta: "searchScore" }` projection and no `filter` inside `cosmosSearch` even though the kit's `vector-knn-query` rule shows both; lexical fallback via `$regex` instead of a search index queried with `$search`.
3. **Vectors stored as BSON Binary** (packed float32, even documented in the README as the storage format). Learn states vectors must be a `number[]` to be indexed; documents with other vector types are not indexed and are not returned by vector search.
4. **Parameters copied blindly:** `vector-ivf` with `numLists: 100` for a 5-document collection (Learn: `documentCount/1000`, and `numLists: 1` is the intended brute-force setting for small demos); DiskANN/HNSW created with no `maxDegree`/`lBuild`/`m`/`efConstruction` exposed or documented.
5. **Ingest hygiene:** one sample hardcodes `DIM = 1536` while letting the embedding model be overridden by env; no L2 normalization for `COS`; no `embeddingModel` / `embeddingDims` / `embeddingVersion` on documents (the kit's `vector-normalize-embeddings` rule already asks for these, but samples skipped it); chunks with no source id or chunk index.

The skill already contains correct syntax (`vector-create-diskann-index`, `vector-knn-query` with `filter` and `searchScore`, `vector-normalize-embeddings` with model/dims/version provenance), but: there is no rule that index creation belongs in the app's seed/startup path with verification; nothing says "number[] only"; `knnBeta` is not named as an anti-pattern (only `$vectorSearch` is); there is no rule against client-side cosine over `find({})`; HNSW (`m`, `efConstruction`, `efSearch`) and IVF (`numLists`, `nProbes`) parameters are never tabulated; the knn example does not exclude the embedding from results; and every example is mongosh JavaScript, while most generated samples were PyMongo.

## Why it matters

26 of 100 samples hit this; 12 hit the MCP management gate and, with no driver-side fallback, ran without a vector index. A sample that computes cosine in the client demonstrates the opposite of what the service offers, and a README that documents BSON Binary storage teaches a format that cannot be indexed. Agents loaded `documentdb-vector-search` in these runs (visible in `events.jsonl`) and still did this, so the gap is in the skill's content, not its discovery.

## Proposed change (one PR, `skills/vector-search/`)

### 1. New rule: `vector-ensure-index-from-app.md`

**Why it matters:** The MCP `create_index` tool is management-gated and off by default. A sample or app must create and verify its own index with the driver, idempotently, at seed/startup time.

**Incorrect:** relying on the MCP tool, then catching the exception and falling back to `find({})` + client-side cosine.

**Correct (Python, raw command so it works on every driver):**

```python
import os

def _cosmos_opts(ix):
    # listIndexes reports the options under "cosmosSearch" (see Learn "Get vector index definitions");
    # fall back to "cosmosSearchOptions" defensively.
    return ix.get("cosmosSearch") or ix.get("cosmosSearchOptions") or {}

def ensure_vector_index(db, coll, dims, field="embedding", kind=None, similarity="COS", name=None):
    assert isinstance(dims, int) and dims > 0, "dims must come from the embedding model (probe it)"
    kind = kind or os.getenv("VECTOR_INDEX_KIND", "vector-diskann")
    name = name or f"{coll}_{field}_{kind}"
    existing = {ix["name"]: ix for ix in db[coll].list_indexes()}
    if name in existing:
        opts = _cosmos_opts(existing[name])
        assert opts.get("kind") == kind and opts.get("dimensions") == dims and opts.get("similarity") == similarity, \
            f"index {name} has {opts}, app expects kind={kind} dims={dims} similarity={similarity}; drop and recreate"
        return name
    opts = {"kind": kind, "dimensions": dims, "similarity": similarity}
    if kind == "vector-ivf":
        n = db[coll].estimated_document_count()   # build IVF after the data is loaded
        opts["numLists"] = int(os.getenv("IVF_NUM_LISTS", max(1, n // 1000)))  # >1M docs: use DiskANN instead
    elif kind == "vector-hnsw":
        m = int(os.getenv("HNSW_M", 16))
        opts["m"] = m
        opts["efConstruction"] = max(2 * m, int(os.getenv("HNSW_EF_CONSTRUCTION", 64)))  # must be >= 2*m
    else:  # vector-diskann
        opts["maxDegree"] = int(os.getenv("DISKANN_MAX_DEGREE", 32))
        opts["lBuild"] = int(os.getenv("DISKANN_L_BUILD", 50))
    db.command({"createIndexes": coll,
                "indexes": [{"key": {field: "cosmosSearch"}, "name": name, "cosmosSearchOptions": opts}]})
    assert name in {ix["name"] for ix in db[coll].list_indexes()}, f"createIndexes returned but {name} is not listed"
    return name
```

Plus a short Node equivalent using `db.command({ createIndexes, indexes: [...] })` and `db.collection(c).indexes()`. Text rules in the file: call this from the seed script and (cheaply) at app startup; HNSW can be built on an empty collection, while IVF's `numLists` is sized from the document count, so build IVF after loading data; `numLists ~= documentCount/1000` up to 1M documents (Learn recommends DiskANN above that), and `numLists: 1` (brute force) is fine for a tiny demo; if the index is missing at query time, **fail or return an explicit error, never scan the collection**. Mention that the MCP tool is fine for interactive exploration once `ENABLE_MANAGEMENT_TOOLS=true`, but a repo must not depend on it.

### 2. New rule: `vector-store-number-array.md`

- Vectors are stored as a plain `number[]` (`vec.tolist()` in Python, `Array.from(float32)` in Node). **Never BSON Binary, never a packed/base64 string**: Learn says only `number[]` vectors are indexed and non-indexed documents are not returned by vector search, so the failure is silent.
- Index key is `{ <embeddingField>: "cosmosSearch" }`. `{ cosmosSearch: "cosmosSearch" }` targets a field literally named `cosmosSearch`, and queries on the real embedding path fail with `Similarity index not found`.
- The vector query is `$search: { cosmosSearch: {...} }`. **Never `knnBeta`, never `$vectorSearch`** (Atlas syntax), never `$text` for the lexical arm (see `documentdb-full-text-search`, which uses `createSearchIndexes` + `$search`).
- Startup probe: embed one string and assert `len(vec) == index dimensions` before serving; if `EMBEDDING_MODEL` is configurable, derive the dimension count from the probe rather than hardcoding `1536` (and note the 2,000-dimension default limit without half-precision or product quantization).
- Link to `vector-normalize-embeddings` for provenance instead of redefining it, and extend its document shape with chunk lineage, keeping the kit's existing camelCase names:

```json
{ "sourceId": "...", "chunkIndex": 0, "text": "...",
  "embedding": [0.0123, ...],
  "embeddingModel": "text-embedding-3-small", "embeddingDims": 1536,
  "embeddingVersion": 1, "embeddedAt": "2026-11-25T00:00:00Z" }
```

### 3. Extend `vector-knn-query.md`

- Add `knnBeta` to the Incorrect block next to `$vectorSearch`.
- Add an Incorrect block: `find({}, {embedding:1})` + cosine in the app, "with a fallback if the index is missing". State: client-side ranking is acceptable only for unit tests with a mocked collection, never as a runtime path.
- Make the Correct pipeline canonical and complete: `$search.cosmosSearch { path, vector, k, lSearch | efSearch | nProbes, filter }` -> `$project { _id: 1, title: 1, sourceId: 1, score: { $meta: "searchScore" } }` (an inclusion projection, which already leaves out the embedding; do **not** add `embedding: 0` to an inclusion projection, since mixing inclusion and exclusion is rejected) -> `$limit k`. Note explicitly why the embedding is left out (several samples returned 1536 floats per hit), and that if an exclusion-style projection is preferred it must be exclusion-only (e.g. `{ embedding: 0 }` in a separate `$project` / `$unset: "embedding"` stage).
- Add a short parameter table for HNSW (`m` default 16, range 2-100; `efConstruction` default 64, range 4-1000, at least `2*m`; query `efSearch` default 40) and IVF (`numLists`; query `nProbes` default 1, at most `numLists`) alongside the existing DiskANN table; keep the kit's existing "verify exact names against current docs" hedge.
- Add a PyMongo version of the pipeline under the JS one (`list(coll.aggregate([...]))`).

### 4. `SKILL.md`

Add the two new rule lines to **Rules** and a short **Hard rules** block directly under the tier table:

```
## Hard rules
- Create the vector index from your own seed/startup code with `createIndexes` + `cosmosSearchOptions` and verify it with `listIndexes`. Do not depend on the MCP `create_index` tool (management-gated, off by default).
- Store vectors as `number[]`. BSON Binary / packed vectors are not indexed.
- Index key is `{ <field>: "cosmosSearch" }`; query with `$search: { cosmosSearch: ... }`. Never `knnBeta`, `$vectorSearch`, or client-side cosine over `find({})`.
- Always project `{ $meta: "searchScore" }` and leave the embedding field out of results; push metadata predicates into `cosmosSearch.filter` (backed by a regular index on the filter field).
- Lexical / hybrid fallback is a search index (`createSearchIndexes`) queried with `$search` (`documentdb-full-text-search`), not `$regex`, `$text`, or Atlas Search.
```

Update the skill `description` to mention "idempotent index creation from application code" and "number[] storage" so the rules trigger when an agent plans a seed script.

### 5. Housekeeping

- `docs/SKILLS.md`: extend the `vector-search/` row with "idempotent index creation from app code; number[] storage".
- `CHANGELOG.md` entry.
- (Separate, optional) `CONTRIBUTING.md` still points at `skills/documentdb-best-practices/rules/`, which no longer exists; worth fixing so outside PRs land in the right folder.

## Evidence (run folders under the experiment repo; no connection strings)

- `runs/15-financial-advisor-chatbot-rag/20261124-192021/events.jsonl` lines 66-69 (list_indexes shows only `_id`; two `documentdb_create_index` calls with a `cosmosSearchOptions` payload rejected by the management gate) and `doc-gaps.md` ("Index lifecycle and idempotent index creation docs", "Avoid returning internal vectors in responses").
- `runs/01-fraud-detection-with-vector-similarity/20261124-185817/events.jsonl` lines 35 and 37 plus `05-audit.json` (no `createIndexes` anywhere in the repo after the MCP failure).
- `runs/11-correspondent-banking-risk-screener/20261124-201541/05-audit.json` (`key: { cosmosSearch: "cosmosSearch" }` -> `Similarity index not found`; `$search` pipelines with no `searchScore` projection).
- `runs/01-product-catalog-with-vector-search/20261124-175429/05-audit.json` (embeddings written as BSON Binary packed float32 and documented in README; `nlist: 100` for 5 documents; no index verification before serving).
- `runs/03-substitute-product-finder/20261124-183232/05-audit.json` (`$search` with `knnBeta`), `runs/04-earnings-call-rag-assistant/20261124-190247/05-audit.json` (client-side cosine over all documents, no prefilter).

Aggregate: 26 of 100 samples carry findings in this family; 12 of those 26 hit the documentdb-mcp management-tools gate in `events.jsonl` (32 of 100 samples overall hit that gate).

## Verification

### 1. Already covered? — partially_covered

The kit's `skills/vector-search/` already covers part of the ask, so the PR must extend it, not duplicate it:
- `skills/vector-search/vector-knn-query.md` already shows `$search` + `cosmosSearch` with `filter` and projects `score: { $meta: "searchScore" }` ("Always project `searchScore` if you plan to rerank or threshold."), and names `$vectorSearch` as unsupported. It does **not** name `knnBeta`, does not exclude the embedding, has no client-side-cosine anti-pattern, and has no PyMongo example.
- `skills/vector-search/vector-normalize-embeddings.md` already requires L2 normalization for `COS` and stores `embeddingModel`, `embeddingDims`, `embeddingVersion` on documents. Draft item 2 originally re-specified these with snake_case names; corrected to link to that rule and reuse its camelCase names.
- `skills/vector-search/vector-create-diskann-index.md` tabulates DiskANN `maxDegree`/`lBuild`/`lSearch`; `vector-choose-index-type.md` uses `numLists: 100` only in an Incorrect example. No HNSW/IVF parameter table, no `numLists` sizing rule.
- Grep of `skills/` and `knowledge-base/` for `knnBeta`, `number[]`, `Binary`, `listIndexes` verification, `client-side`: no matches in vector-search. No rule about creating the index from application code or about the MCP gate; `skills/mcp-setup/SKILL.md` lines 154-155 only say to add `ENABLE_MANAGEMENT_TOOLS: "true"` to allow management tools, and the kit's `mcp.json` line 13 sets `"ENABLE_MANAGEMENT_TOOLS": "false"`.
- `CONTRIBUTING.md` lines 8-15 still reference `skills/documentdb-best-practices/rules/` (confirmed stale).

### 2. Premise true? — confirmed (with precision edits applied)

Checked against https://learn.microsoft.com/en-us/azure/documentdb/vector-search (updated 2026-11-25) and the documentdb-mcp clone:
- Index key `{ "<path_to_property>": "cosmosSearch" }` with `cosmosSearchOptions` in `createIndexes`: confirmed (all three templates).
- "Vectors must be a `number[]` to be indexed ... Nonindexed documents aren't returned in the result of a vector search." confirmed; matches the BSON-Binary claim.
- HNSW: `m` default 16 (2-100), `efConstruction` default 64 (4-1000, at least `2 * m`), `efSearch` default 40; HNSW "can be created on an empty table". IVF: `numLists` = `documentCount/1000` up to 1M documents, DiskANN recommended above 1M, `numLists: 1` acceptable for small demos; `nProbes` default 1, not larger than `numLists`. DiskANN `maxDegree` default 32, `lBuild` default 50, `lSearch` default 40, `k <= lSearch`. Draft's parameter defaults confirmed; added the `2*m`, `nProbes <= numLists` and "DiskANN above 1M / numLists 1 for demos" nuances.
- `$meta: "searchScore"` and `filter` inside `cosmosSearch` (backed by a standard index on the filter property): confirmed.
- MCP: `src/tools/index-tools.ts` line 17-20 `name: 'create_index'`, `requiredRole: 'management'`; `src/security/authorization.ts` line 50 throws "Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true to opt in." confirmed.
- Counts: 57 finding ids map to 26 distinct samples (scratchpad `phase4/findings-default.json`); `events.jsonl` shows the management-gate error in 12 of those 26 samples and in 32 sample folders overall. Spot checks: `15-financial-advisor-chatbot-rag` events lines 66-69 contain two `create_index` calls and one `list_indexes`; `03-substitute-product-finder` audit mentions `knnBeta`; `01-product-catalog-with-vector-search` audit mentions Binary storage.

Corrections applied to the body (technical precision in the proposed code, not a wrong premise):
- `listIndexes` reports vector options under `cosmosSearch` (Learn "Get vector index definitions" output), not `cosmosSearchOptions`; the reference code read the wrong key and would never match an existing index. Fixed with a helper that reads `cosmosSearch` first.
- The proposed `$project { title:1, ..., score: {$meta}, embedding: 0 }` mixes inclusion and exclusion, which MongoDB-compatible engines reject. Rewritten as an inclusion projection that omits the embedding, with an exclusion-only alternative.
- `numLists` above 1M: Learn recommends DiskANN rather than `sqrt(n)`; small demos can use `numLists: 1`. `efConstruction` clamped to `>= 2*m`. `dims` made required and `kind` also verified.
- Provenance fields renamed to the kit's existing camelCase and linked to `vector-normalize-embeddings`; full-text fallback named as `createSearchIndexes` + `$search`, consistent with `skills/full-text-search/SKILL.md`.

### 3. Maintainer skeptic — confirmed

As a maintainer of Azure/documentdb-agent-kit I would accept this: it names exact files (`skills/vector-search/SKILL.md`, `vector-knn-query.md`, two new rule files, `docs/SKILLS.md`, `CHANGELOG.md`), gives concrete rule text and code, is specific to DocumentDB's `cosmosSearch` contract and to this kit's own default `mcp.json`, and is backed by 26 samples. It is in scope for the kit (skill content, not MCP behavior; the MCP gate is working as designed). The optional `CONTRIBUTING.md` fix should be a separate small PR.

## Finding ids

F0066, F0241, F0142, F0138, F0203, F0249, F0139, F0143, F0205, F0206, F0519, F0448, F0585, F0588, F0586, F0654, F0655, F0757, F0589, F0787, F0788, F0879, F0909, F1192, F1193, F1360, F1361, F1611, F1612, F1613, F1617, F1707, F1818, F1819, F1914, F1917, F2313, F2315, F2316, F2317, F2351, F2352, F2416, F2417, F2419, F2577, F2578, F3248, F3252, F3291, F3287, F3284, F3486, F3487, F3488, F3491, F3386
