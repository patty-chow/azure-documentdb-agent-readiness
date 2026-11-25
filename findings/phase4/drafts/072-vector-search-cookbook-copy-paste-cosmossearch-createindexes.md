---
title: "Learn docs: add a copy-paste \"Create a vector index and run a similarity query\" how-to (idempotent per-kind createIndexes in Python/Node, number[] storage rule, embedding-model-to-dimensions table, tuning presets, score projection, error decoding)"
repo: learn-docs
type: learn-feedback
status: ready_with_edits
priority: P1
sample_count: 54
findings: 99
bucket: learn-doc_gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Add a copy-paste "Create a vector index and run a similarity query" how-to page for Azure DocumentDB

**Target:** MicrosoftDocs/nosql-docs-pr, `azure/documentdb/` (new page + TOC entry + inbound links + one small edit to `vector-search.md` + one consistency fix)
**Live pages involved:** https://learn.microsoft.com/azure/documentdb/vector-search , https://learn.microsoft.com/azure/documentdb/quickstart-python-vector-search (and the TypeScript, .NET, Go, Java siblings), https://learn.microsoft.com/azure/documentdb/quickstart-python-select-algorithm , https://learn.microsoft.com/azure/documentdb/quickstart-nodejs-select-algorithm , https://learn.microsoft.com/azure/documentdb/full-text-search-hybrid , https://learn.microsoft.com/azure/documentdb/half-precision , https://learn.microsoft.com/azure/documentdb/product-quantization

## What happens today

The vector-search content is correct but not sample-ready:

- `vector-search.md` ("Integrated vector store", TOC label "Vector database") is a ~5,000-word concept article. The three `createIndexes` templates live inside DiskANN/HNSW/IVF tabs; the rule that vectors must be `number[]` appears only in a field-table cell (DiskANN tab) and in an "Important" box inside the IVF tab, and it never mentions BSON Binary; the `$meta: "searchScore"` projection appears only in the IVF tab and the *Filtered vector search* section, both paired with `document: "$$ROOT"`. There is no Node code, no idempotent create, no model-to-dimensions table, and no tuning presets beyond the IVF `numLists` guidance.
- The "Build an AI vector search app" quickstarts (`quickstart-python-vector-search`, ~4,200 words, plus TypeScript, .NET, Go and Java) do show driver-only `createIndexes` per kind, but each script drops and recreates the vector index, projects `document: "$$ROOT"` (so the embedding travels back with every hit), hardcodes `text-embedding-3-small` / 1536, and uses DiskANN `maxDegree: 20, lBuild: 10` (the minimums, not the documented defaults of 32/50) without saying so.
- The two "select algorithm" quickstarts (Python, TypeScript, ~2,900 words each) are framed as "compare 9 algorithm x metric combinations"; they also drop and recreate indexes and project `$$ROOT`.
- `full-text-search-hybrid.md` has the RRF recipe but creates the vector index with the shell `db.products.createIndex()` helper and points to `vector-search.md` only in a code comment.

So when an agent (or a developer) searches Learn for "create vector index Azure DocumentDB", nothing short and pasteable comes back first, and none of the existing pages states the storage rule or the dimensions rule in a place a builder sees before writing code.

## Why it matters (what the agents did because of this)

In a 100-sample build experiment (gpt-5-mini, DocumentDB Agent Kit skills + DocumentDB/Azure/Learn MCP servers), **54 of the 100 samples** logged at least one documentation gap in this area (99 findings). The failure modes, with run folders as evidence:

| What the builder did | Why | Example run |
|---|---|---|
| Issued `$search: { knnBeta: {...} }` (Atlas shape), fell back to client-side cosine over all documents | No DocumentDB `cosmosSearch` query snippet found next to the index snippet | `runs/03-substitute-product-finder/20261124-183232/app/app/routes.py` |
| Called `createSearchIndexes` to create the *vector* index, got `CommandNotSupported` (code 115, "Search index creation is not supported yet") and treated vector search as unavailable | No statement next to the vector templates that `createSearchIndexes` is the BM25 full-text command (preview, must be enabled on the cluster) and vector indexes always go through `createIndexes` + `cosmosSearchOptions` | `runs/07-voice-of-customer-sentiment-hub/20261124-204049/events.jsonl` |
| Stored embeddings as BSON Binary (packed float32, subtype 9); server-side search silently never used, or query failed with `BadValue: Invalid type: expected an array type field, but received object instead` | The `number[]` rule is buried in a table cell and a tab-scoped note, and does not mention Binary | `runs/01-product-catalog-with-vector-search/20261124-175429/doc-gaps.md`, `runs/11-visual-similarity-search-image-embeddings/20261124-184225/events.jsonl` |
| Left `EMBEDDING_MODEL`/`EMBEDDING_DIMS` optional and **skipped vector indexing entirely** to avoid a dimensions mismatch (11 samples) | No model-to-dimensions table anywhere on Learn | `runs/04-regulatory-reporting-orchestration/20261124-200545/doc-gaps.md`, `runs/18-chargeback-dispute-multi-agent/20261124-192501/doc-gaps.md` |
| Tried the MCP `documentdb_create_index` tool, got "Management tools are disabled by default", and had no short driver-only recipe to fall back to (8 samples) | Existing quickstarts are long and drop/recreate; no 20-line idempotent snippet | `runs/08-regulatory-compliance-rag-checker/20261124-190949/events.jsonl` |
| Created an index with default parameters it could not explain, and the README gives no tuning guidance (about 20 samples) | No demo/small/production preset table | `runs/05-churn-prediction-pipeline/20261124-203754/doc-gaps.md` |

The Agent Kit's `vector-search` skill covers index choice, DiskANN parameters, `lSearch`/`k`, normalization and storing model + dimensions with each vector, but it also lacks the `number[]`/BSON Binary rule and a model-to-dimensions table (tracked separately for the kit). The public Learn pages are what both agents (via the Learn MCP server) and developers search, so the fix belongs there first.

## Proposed change

### 1. New page: `azure/documentdb/how-to-create-vector-index.md`

Title: **Create a vector index and run a similarity query**. `ms.topic: how-to`. One screen of prose, mostly code. TOC: under *Vector search*, immediately after *Vector database* (`vector-search`), before *Exact Nearest Neighbor (ENN) Vector Search*. (Alternative if the team prefers fewer pages: add the same content as a "Copy-paste recipe" section at the top of `vector-search.md`; the content list below is the same.)

Suggested sections and content:

**How to store vectors** (callout at the top)
> Store each embedding as a dense array of numbers (`embedding: [0.0123, -0.2041, ...]`). Documents whose vector field holds another type (BSON Binary, nested objects, strings) are not indexed by the `cosmosSearch` index and are not returned by vector search; a query vector sent as BSON Binary fails with `BadValue: ... expected an array type field`. For `similarity: "COS"`, L2-normalize vectors at ingest if your model does not (OpenAI `text-embedding-3-*` and `ada-002` output is already unit length). One vector index per vector path. Half-precision (`"compression": "half"`, HNSW and IVF) and product quantization (DiskANN) are index options, not a storage format you choose in your documents.

**Pick the embedding model, fix the dimensions**

| Model | Output dimensions | Notes |
|---|---|---|
| OpenAI / Azure OpenAI `text-embedding-3-small` | 1536 | Default in the quickstarts; normalized, use `COS` |
| OpenAI / Azure OpenAI `text-embedding-3-large` | 3072 | Above the 2,000-dimension uncompressed limit: use HNSW or IVF with `"compression": "half"` (up to 4,000) or DiskANN with product quantization (up to 16,000), or request fewer dimensions from the model |
| OpenAI / Azure OpenAI `text-embedding-ada-002` | 1536 | Legacy |
| `sentence-transformers/all-MiniLM-L6-v2` | 384 | Local/offline demos |
| `openai/clip-vit-base-patch32` (images) | 512 | Multimodal samples |

> `cosmosSearchOptions.dimensions` must equal the length of every vector you insert. If you pass the OpenAI `dimensions` parameter to shorten vectors, the index must use the shortened length. Do not mix models in one collection; store `embeddingModel`, `embeddingDims`, `embeddingVersion` on each document and bump the version when you re-embed.

```python
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMS = int(os.environ.get("EMBEDDING_DIMS", "1536"))

probe = embed("dimension probe")          # your embedding call
assert len(probe) == EMBEDDING_DIMS, (
    f"{EMBEDDING_MODEL} returned {len(probe)} dims; set EMBEDDING_DIMS={len(probe)} "
    "and recreate the index")
```

**Create the index (idempotent, driver only)** - Python tab:

```python
def ensure_vector_index(db, coll, field="embedding", name="embedding_vec",
                        kind="vector-diskann", dims=EMBEDDING_DIMS,
                        similarity="COS", **params):
    """Create the cosmosSearch index if missing; fail loudly on a spec mismatch."""
    existing = {ix["name"]: ix for ix in db[coll].list_indexes()}
    if name in existing:
        spec = existing[name].get("cosmosSearch", {})
        if spec.get("kind") != kind or spec.get("dimensions") != dims:
            raise RuntimeError(f"{name} exists with {spec}; drop it before changing kind/dims")
        return "exists"
    db.command({
        "createIndexes": coll,
        "indexes": [{
            "name": name,
            "key": {field: "cosmosSearch"},
            "cosmosSearchOptions": {"kind": kind, "dimensions": dims,
                                    "similarity": similarity, **params},
        }],
    })
    return "created"

# Pick ONE of these per vector path (only one vector index per path is allowed):
ensure_vector_index(db, "products", kind="vector-diskann", maxDegree=32, lBuild=50)   # M30+
ensure_vector_index(db, "products", kind="vector-hnsw", m=16, efConstruction=64)     # M30+
ensure_vector_index(db, "products", kind="vector-ivf", numLists=1)                   # M10+, demos
```

Node tab (same shape, `await db.command({ createIndexes: coll, indexes: [...] })` after `await db.collection(coll).listIndexes().toArray()`). State explicitly: this needs only the MongoDB driver and `retryWrites=false` on the connection; no portal step, CLI, or MCP tool is required.

**Query it**

```python
pipeline = [
    {"$search": {"cosmosSearch": {
        "path": "embedding", "vector": query_vector, "k": 10,
        # DiskANN: "lSearch": 40 (>= k) | HNSW: "efSearch": 40 | IVF: "nProbes": 1 (<= numLists)
        # optional pre-filter: "filter": {"category": {"$eq": "jackets"}}
    }}},
    # Inclusion projection: list the fields you need; never include the embedding path.
    {"$project": {"_id": 1, "name": 1, "category": 1, "score": {"$meta": "searchScore"}}},
]
hits = list(db.products.aggregate(pipeline))
```

Note under the snippet: projecting `document: "$$ROOT"` (as the existing quickstarts do) ships the whole vector back on every hit (1536 doubles is about 12 KB per result); project the fields you need. Pre-filter fields need their own ordinary index.

**Tuning presets** (documented defaults plus the next step up; product team to confirm the "small" and "production" columns)

| Kind | Demo (< 10k vectors) | Small production (10k-100k) | Production (100k+) | Tier |
|---|---|---|---|---|
| `vector-ivf` | `numLists: 1` (brute force, exact), `nProbes: 1` (default) | `numLists ~ docs/1000`, `nProbes: 4-8` | Move to DiskANN (the IVF guidance already says so above 1M docs) | M10+ |
| `vector-hnsw` | `m: 16, efConstruction: 64` (defaults), `efSearch: 40` (default) | `m: 16-32, efConstruction: 128-200` (must be >= 2*m), `efSearch: 100` | Move to DiskANN or a larger M-tier if the graph exhausts memory | M30+ |
| `vector-diskann` | `maxDegree: 32, lBuild: 50` (defaults), `lSearch: 40` (default) | `maxDegree: 32-64, lBuild: 100`, `lSearch: 100` | `maxDegree: 64+, lBuild: 100-200`, `lSearch >= k`, product quantization for > 2,000 dims | M30+ |

Add: raise `lSearch`/`efSearch`/`nProbes` before touching build-time parameters; rebuilding is the expensive step. Verify with `explain()` that the `$search` stage uses the index, and expect empty results for a minute or two after creation while the index builds (retry, do not recreate). Describe cost in terms of tier memory and vCores, not request units.

**Errors you will see and what they mean**

| Error | Meaning | Fix |
|---|---|---|
| `CommandNotSupported` (115) "Search index creation is not supported yet" | You called `createSearchIndexes`, which is the BM25 full-text command (preview; the `FullTextSearch` feature must be enabled on the cluster) | Vector indexes always use `createIndexes` + `cosmosSearchOptions` |
| `BadValue` (2) "Invalid type: expected an array type field, but received object instead" | Query vector (or stored vector) is BSON Binary or an object | Pass a plain list/array of numbers |
| Unknown operator `knnBeta` / `knnVector` / `$vectorSearch` | Atlas Search syntax | Use `$search: { cosmosSearch: {...} }` |
| Hits returned but a document is missing | That document's vector is not `number[]` or has the wrong length | Re-embed and store as an array of `EMBEDDING_DIMS` numbers |
| No results right after creation | Index still building | Wait and retry; do not drop/recreate |
| (MCP) "Management tools are disabled by default" | DocumentDB MCP server opt-in setting, not a service limit | Use the driver snippet above |

**Next steps** (one line each): hybrid BM25 + vector with RRF (`full-text-search-hybrid`), half-precision and product quantization pages, and a 15-line LangChain binding that builds the `AzureDocumentDBVectorSearch` store from the same `EMBEDDING_MODEL`/`EMBEDDING_DIMS` variables and the same `kind`/`similarity`, ending in `.as_retriever(search_kwargs={"k": 5})`.

### 2. Links into the new page

- `vector-search.md`: first paragraph of *Perform vector similarity search*: "For a pasteable Python/Node version with idempotent index creation and tuning presets, see Create a vector index and run a similarity query."
- `full-text-search-hybrid.md`, Step 1 comment on the vector index: replace "See vector-search.md for the full option matrix" with a link to the new page.
- `vector-search.md`, *Use large language model (LLM) orchestration tools*: link to the new page's LangChain snippet.
- `quickstart-*-vector-search` and `quickstart-*-select-algorithm` (Next steps): link to the new page for production-style (idempotent, explicit-projection) code.

### 3. Small edit to `vector-search.md`

Move the existing "Important: Vectors must be a `number[]` to be indexed..." box from inside the IVF tab to directly above the DiskANN/HNSW/IVF tab set, and extend it with one sentence: "Vectors stored as BSON Binary are not indexed."

### 4. Consistency notes found while checking the pages

- `quickstart-*-select-algorithm` state HNSW supports up to 8,000 dimensions; `vector-search.md` *Features and limitations* and `half-precision.md` say 4,000 with half-precision and 2,000 uncompressed. One of these should be corrected when the new page is added so the dimensions table can cite a single number.
- `quickstart-python-vector-search` uses DiskANN `maxDegree: 20, lBuild: 10` (the allowed minimums) while `vector-search.md` documents defaults of 32 and 50; either use the defaults or add a comment saying the values are minimal for a 50-document demo.

## Evidence (run folders; no connection strings)

- `runs/03-substitute-product-finder/20261124-183232/app/app/routes.py` and `.../05-audit.json` (knnBeta payload, requirement marked partly_met with cause skill_guidance_not_followed)
- `runs/01-product-catalog-with-vector-search/20261124-175429/doc-gaps.md` (BSON Binary storage, server-side index unused)
- `runs/11-visual-similarity-search-image-embeddings/20261124-184225/events.jsonl` (BadValue on Binary query vector)
- `runs/07-voice-of-customer-sentiment-hub/20261124-204049/events.jsonl` (createSearchIndexes used for a vector index, CommandNotSupported 115)
- `runs/08-regulatory-compliance-rag-checker/20261124-190949/events.jsonl` (MCP management tools disabled; needed driver-only path)
- `runs/04-regulatory-reporting-orchestration/20261124-200545/doc-gaps.md` (vector search dropped because no model-to-dims mapping)

## Verification

### 1. Already covered? - partially_covered

The building blocks exist on Learn but not in the sample-ready form the draft asks for, and the two rules that caused the worst failures (storage type, dimensions) are not where builders look.

- https://learn.microsoft.com/en-us/azure/documentdb/vector-search (word_count 4958): has per-kind `createIndexes` templates in DiskANN/HNSW/IVF tabs, defaults (`maxDegree` "default is 32", `lBuild` "default is 50", `m` "16 by default", `efConstruction` "64 by default", `efSearch` "40 by default", `lSearch` "default value is 40", `nProbes` "default value of 1"), IVF `numLists` = `documentCount/1000` guidance, tier guidance (IVF M10/M20, HNSW and DiskANN M30+), and the storage rule: "Vectors must be a `number[]` to be indexed." That rule sits in a DiskANN field-table cell and an IVF-tab Important box and does not mention BSON Binary. The `searchScore` projection always pairs with `"document" : "$$ROOT"`. No Node code, no idempotent create, no model-to-dimensions table, no error table.
- https://learn.microsoft.com/en-us/azure/documentdb/quickstart-python-vector-search (word_count 4171; TOC "Build an AI vector search app", also TypeScript/.NET/Go/Java): driver-only `createIndexes` per kind, but each one calls `drop_vector_indexes` first, projects `"document": "$$ROOT"`, hardcodes 1536 dims, and has no number[] rule. The original draft did not mention these pages; the body now does.
- https://learn.microsoft.com/en-us/azure/documentdb/quickstart-python-select-algorithm (word_count 2870): a comparison runner that drops and recreates indexes and projects `$$ROOT`. It already has an "Empty search results ... Wait 2-3 minutes after index creation" troubleshooting row.
- https://learn.microsoft.com/en-us/azure/documentdb/full-text-search-hybrid: RRF recipe exists; the vector index is created with `db.products.createIndex(...)` and only a code comment points to vector-search.md.
- Agent kit (`/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/phase4/documentdb-agent-kit/skills/vector-search/`): `vector-create-diskann-index.md` ("dimensions ... Must match embedding model output exactly"), `vector-normalize-embeddings.md` ("Store the embedding model name and dimensions alongside the vector"). A grep for `number[]` or `binary` in `skills/vector-search` returns nothing, and `vector-choose-index-type.md` uses `numLists: 100` with no explanation. The original draft said the kit "already states most of these rules"; the body now says what it does not cover.

### 2. Is the premise true? - confirmed (with factual corrections applied)

Core claims verified against Learn: `createIndexes` + `key: {<path>: "cosmosSearch"}` + `cosmosSearchOptions.kind` in `vector-ivf|vector-hnsw|vector-diskann`; `$search: {cosmosSearch: {vector, path, k}}` with `{$meta: "searchScore"}`; vectors must be `number[]`; one index per vector path; uncompressed max 2,000 dims; `k <= lSearch`; `efConstruction >= 2*m`; `nProbes <= numLists`; `listIndexes` returns a `cosmosSearch` sub-document with `kind`/`dimensions` (so the idempotency check works); `createSearchIndexes` is the BM25 full-text command, which is in preview and needs the `FullTextSearch` feature enabled (https://learn.microsoft.com/en-us/azure/documentdb/full-text-search-overview). The cited error strings are in the run events (`expected an array type field` in run 11, `Search index creation is not supported yet` in run 07, `Management tools are disabled by default` in run 08, `knnBeta` x3 in run 03 routes.py). Model dimensions (3-small 1536, 3-large 3072, ada-002 1536, MiniLM-L6-v2 384, CLIP ViT-B/32 512) are the published model output sizes. Capacity is framed as vCore tiers, not RUs.

Corrections applied to the body:
- The `text-embedding-3-large` row said "DiskANN or HNSW with half-precision". https://learn.microsoft.com/en-us/azure/documentdb/half-precision says half-precision is supported for "HNSW, IVF" (up to 4,000 dims) and product quantization for "DiskANN" (up to 16,000). The row now says that.
- "`$meta: \"searchScore\"` appears only in the IVF tab" was changed: it also appears in the *Filtered vector search* section (and on half-precision.md).
- The Agent Kit sentence was changed: the kit lacks the number[]/Binary rule and a dimensions table.
- Added the existing `quickstart-*-vector-search` pages (missed by the draft) and their non-default DiskANN values (`maxDegree: 20, lBuild: 10`).
- The TOC label for `vector-search` is "Vector database", and the full-text-search enablement is the `FullTextSearch` preview feature. Both are now named.

### 3. Maintainer skeptic - confirmed

As a MicrosoftDocs/nosql-docs-pr maintainer, I would accept this with small edits. It names the files (new `how-to-create-vector-index.md`, `vector-search.md`, `full-text-search-hybrid.md`, the quickstarts), gives exact content and code, includes a concrete 3-line move of an existing note, and flags two real inconsistencies (HNSW 8,000 vs 4,000 dims; DiskANN minimum values used as if they were defaults). It is specific to Azure DocumentDB (`cosmosSearch`, M-tier guidance, `createSearchIndexes` vs `createIndexes`) and is backed by 54 samples. Likely review pushback: reviewers may prefer folding the recipe into `vector-search.md` rather than adding a page (the alternative is written into the body), and the "small/production" tuning columns need product-team sign-off (also flagged in the body). It is in scope for Learn; the Agent Kit gaps belong in a separate kit issue.

## Finding ids

- F0018
- F0024
- F0057
- F0059
- F0060
- F0093
- F0096
- F0130
- F0132
- F0137
- F0169
- F0195
- F0196
- F0231
- F0232
- F0235
- F0238
- F0402
- F0438
- F0440
- F0512
- F0514
- F0517
- F0572
- F0573
- F0615
- F0647
- F0678
- F0741
- F0742
- F0778
- F0780
- F0785
- F0837
- F0988
- F1118
- F1150
- F1181
- F1182
- F1184
- F1186
- F1243
- F1244
- F1283
- F1313
- F1352
- F1353
- F1357
- F1389
- F1453
- F1503
- F1509
- F1541
- F1606
- F1640
- F1702
- F1741
- F1812
- F1909
- F1912
- F2208
- F2210
- F2265
- F2304
- F2305
- F2309
- F2343
- F2410
- F2474
- F2571
- F2575
- F2605
- F2795
- F2828
- F2857
- F2858
- F2861
- F2891
- F2892
- F2893
- F2965
- F2997
- F3054
- F3055
- F3133
- F3135
- F3160
- F3161
- F3197
- F3243
- F3276
- F3277
- F3279
- F3281
- F3377
- F3378
- F3478
- F3480
- F3481
