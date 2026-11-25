---
id: K05
title: "vector-search skill: number[] storage rule and copy-paste cosmosSearch index templates (vector-ivf, vector-hnsw, vector-diskann), with $search as the primary query path"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P1
sample_count: 72
member_drafts:
  - 113-vector-search-and-indexing-skills-lack-copy-paste-idempotent.md
  - 019-believes-vector-indexes-use-mongodb-atlas-community-syntax-k.md
  - 021-agent-kit-gap-vector-search-skill-shows-a-full-createindex-e.md
  - 039-believes-vector-indexes-queries-use-atlas-or-upstream-syntax.md
  - 114-samples-fell-back-to-client-side-cosine-similarity-instead-o.md
open_questions: 4
---

# vector-search skill: `number[]` storage rule and copy-paste `cosmosSearch` index templates (`vector-ivf`, `vector-hnsw`, `vector-diskann`), with `$search` as the primary query path

## What happens today

`skills/vector-search/` gets the query side mostly right (`vector-knn-query.md` marks Atlas `$vectorSearch` as unsupported and shows `$search` + `cosmosSearch`). It still has four gaps:

1. **Only DiskANN has a create example.** `vector-create-diskann-index.md` is complete. `vector-hnsw` appears only in tier tables (`SKILL.md`, `vector-choose-index-type.md`, `skills/query-optimizer/references/core-indexing-principles.md`), and `vector-ivf`/`numLists` appears only inside the "Incorrect" block of `vector-choose-index-type.md`. `efConstruction`, `efSearch` and `nProbes` do not appear anywhere in `skills/` or `knowledge-base/`.
2. **No create-side "wrong surface" warning.** Nothing in the skill says that `createSearchIndex(es)`, `knnVector` or `type: "vector"` do not create a vector index. The only place the kit separates the two surfaces is a pair of comments in `skills/full-text-search/fts-hybrid-search.md` ("BM25 on the searchable text (createSearchIndexes, not createIndexes)" and "Vector on the embedding (cosmosSearch, unchanged)"). The full-text-search skill also (correctly) teaches `createSearchIndexes` for BM25, so models merge the two.
3. **No storage-type rule.** No file says that vectors must be stored as `number[]`. Learn says that "Vectors must be a `number[]` to be indexed" and that documents of another type are not indexed and are not returned.
4. **No rule that the database does the search.** Nothing says that `$search` is the required query path, how to check that the index exists, or what to do when it does not.

## Why it matters

In one experiment run, gpt-5-mini built 100 Azure DocumentDB sample apps with this kit and the DocumentDB, Azure and Learn MCP servers. 182 distinct findings fall in this group:

- **Wrong create command, cold quiz (74 findings, 72 samples).** Asked cold "which vector index types are supported, and what does the create command look like?", the model answered with Atlas or MongoDB 7 shapes such as `createSearchIndex` with `knnVector`, `createIndex({embedding: "vector"})` or HNSW options like `M`/`efConstruction: 200` inside a `knnVector` block. Most of these answers were corrected after the model read a skill. Two shipped anyway with the skill loaded. In run 07, `createSearchIndexes` was sent for the vector index; the call failed with `CommandNotSupported`, the error was swallowed, and the app shipped with no vector index. In run 14, `createSearchIndexes` was also used for the vector index, the app queried with `$search: { knn: ... }` instead of `$search: { cosmosSearch: ... }`, and its audit marked both requirements as met. Where an HNSW index was built correctly, the parameters came from Learn, not from the kit.
- **Atlas/upstream priors and BSON Binary storage (90 findings, 69 samples).** 87 of these are further cold-quiz answers that reached for `knnVector`, `$vectorSearch`, `createSearchIndexes` for the vector index, or `$text`; the skill corrected them once loaded. The other 3 concern storage type and dimensions. Separately, three prompts asked for "BSON binary vectors". In 4 of 5 builds of those prompts the agent packed the floats into BSON Binary (for example `bson.Binary(vec.tobytes(), subtype=0x09)`). Those documents are not indexed by `cosmosSearch`, so server-side search does not return them: two builds fell back to unpacking the Binary and ranking client-side, and one audit records "Invalid type: expected an array type field". Only one build caught it, because its readiness step happened to read the Learn page.
- **Improvised index creation and queries (16 findings in 14 samples, plus 2 findings in 2 samples).** These builds put DiskANN keys on an HNSW index, put `path` inside `cosmosSearchOptions`, tried `createSearchIndexes`, or left index creation as a manual README step. Two builds shipped `find()` plus in-process cosine as their only query path.

**About the counts:** the member drafts' finding ids do not overlap (182 ids in total). Their sample sets do overlap, so the sample count is not a sum. 72 is the number of distinct samples behind the 74 cold-quiz vector-index findings alone (60 + 12; none of the 12 samples has a second run with that finding, so the two sets cannot share a sample), and it is a floor for the whole group. All counts come from a single experiment run and should not be quoted as rates.

## Proposed change

This PR covers storage, templates and the query path. App-side idempotent `ensure_vector_index` code, the index verification step and the MCP-gating note go in the companion PR (K06).

### 1. New `skills/vector-search/vector-index-templates.md`

Use the existing rule format (Category/Priority, Why it matters, Incorrect, Correct, References). Register it in the `SKILL.md` Rules list.

**Correct**: three `createIndexes` documents on the same field that differ only in `cosmosSearchOptions`. `EMBEDDING_DIM` must come from the same config that selects the embedding model.

```javascript
db.runCommand({ createIndexes: "<collection>", indexes: [{ name: "embedding_vector_ivf",
  key: { embedding: "cosmosSearch" },
  cosmosSearchOptions: { kind: "vector-ivf", dimensions: EMBEDDING_DIM, similarity: "COS", numLists: 1 } }] });
db.runCommand({ createIndexes: "<collection>", indexes: [{ name: "embedding_vector_hnsw",
  key: { embedding: "cosmosSearch" },
  cosmosSearchOptions: { kind: "vector-hnsw", dimensions: EMBEDDING_DIM, similarity: "COS", m: 16, efConstruction: 64 } }] });
db.runCommand({ createIndexes: "<collection>", indexes: [{ name: "embedding_vector_diskann",
  key: { embedding: "cosmosSearch" },
  cosmosSearchOptions: { kind: "vector-diskann", dimensions: EMBEDDING_DIM, similarity: "COS", maxDegree: 32, lBuild: 50 } }] });
```

The mongosh helper form `db.<coll>.createIndex({ embedding: "cosmosSearch" }, { name, cosmosSearchOptions: {...} })` is equivalent; show it once next to the command form. `similarity` is `COS`, `L2` or `IP`.

**Tunables** [needs SME confirmation] (from the Learn vector-search page; see open question 1):

| kind | recommended tier / scale | build keys (range, default) | query key in `$search.cosmosSearch` | for more recall |
|---|---|---|---|---|
| `vector-ivf` | M10/M20, under ~10k vectors | `numLists`: 1 for demos (brute force, most accurate); `documentCount/1000` up to 1M docs; use DiskANN above 1M. Sized from the document count, so re-tune (drop and recreate) as the collection grows | `nProbes` (default 1, ≤ `numLists`) | raise `nProbes` |
| `vector-hnsw` | M30+, up to ~50k vectors; can be built on an empty collection | `m` 2-100 (default 16); `efConstruction` 4-1000 (default 64, ≥ 2*`m`) | `efSearch` (default 40) | raise `m` / `efConstruction` / `efSearch`; large HNSW builds can exhaust memory, so prefer DiskANN or a larger tier |
| `vector-diskann` | M30+, 500k+ vectors | `maxDegree` 20-2048 (default 32); `lBuild` 10-500 (default 50) | `lSearch` 10-1000 (default 40, ≥ `k`) | raise `maxDegree` / `lBuild` / `lSearch` |

**Incorrect** (these are Atlas / MongoDB 7 shapes, not DocumentDB vector indexes):

```javascript
db.runCommand({ createSearchIndexes: "products",   // BM25 full-text indexes only; never vectors
  indexes: [{ name: "vec", type: "vector", fields: [{ path: "embedding", type: "vector", dimensions: 1536 }] }] });
db.products.createIndex({ embedding: "vector" }, { engine: "hnsw", dimensions: 1536 });
db.products.createIndex({ embedding: "knnVector" }, { knnVector: { dimensions: 1536, method: "hnsw", m: 16, efConstruction: 200 } });
db.products.createSearchIndex({ name: "vec", definition: { mappings: { fields: { embedding: { type: "knnVector", dimensions: 1536 } } } } });
db.products.createSearchIndex({ name: "vec", type: "vectorSearch",
  definition: { fields: [{ type: "vector", path: "embedding", numDimensions: 1536, similarity: "cosine" }] } });
```

Follow it with one sentence: a vector index is an ordinary `createIndex` / `createIndexes` call whose key is `{ <field>: "cosmosSearch" }` with `cosmosSearchOptions`, queried with `$search: { cosmosSearch: {...} }`. `createSearchIndexes` is the full-text search index command (preview, enabled per cluster [needs SME confirmation], see open question 3); the two meet only at query time in hybrid search (see `fts-hybrid-search`).

**Common mistakes** (each one occurred in the experiment's builds):
- `path` belongs in the `$search.cosmosSearch` query, not in `cosmosSearchOptions`.
- DiskANN keys (`maxDegree`, `lBuild`) on an HNSW index, or HNSW keys on DiskANN: use the template for the kind you chose.
- `dimensions` must equal the embedding length. [needs SME confirmation] Without compression the maximum is 2,000 dimensions. Half-precision (HNSW/IVF) raises it to 4,000, and DiskANN with product quantization raises it to 16,000. A 3,072-dimension model therefore needs one of those options.
- Vectors must be stored as `number[]` (see vector-normalize-embeddings).
- Only one vector index is allowed per path. `IndexOptionsConflict` means an index on the same key already exists with a different name or options: reuse its name, or drop and recreate it.

### 2. `skills/vector-search/vector-normalize-embeddings.md`: add a rule bullet and an Incorrect/Correct pair

```markdown
- Store the vector as a plain array of numbers (`number[]`). BSON Binary / packed-float32
  vectors (Atlas "BinData vector" style) are not indexed by `cosmosSearch`; those
  documents are left out of every `$search` result, with no error at insert or index time.
```

```python
# Incorrect: document is not indexed; $search never returns it
doc["embedding"] = bson.Binary(np.asarray(vec, dtype=np.float32).tobytes(), subtype=0x09)
# Correct
doc["embedding"] = [float(x) for x in vec]
```

### 3. New `skills/vector-search/vector-prefer-server-side-search.md`

Same rule format, Category Vector Search, Priority HIGH. Why it matters: a `cosmosSearch` index exists so that Azure DocumentDB does the nearest-neighbour search. Pulling documents with `find()` and ranking them in the app reads the whole collection on every query, ignores the index and teaches the wrong pattern. It is acceptable only as an explicitly labelled fallback for offline tests.

Rule:
1. Check that a `cosmosSearch` index exists on the embedding field with `listIndexes` (`collection.list_indexes()` in PyMongo, `collection.indexes()` in Node.js). It appears as `key: { <field>: "cosmosSearch" }`, with its options, including `kind`, under `cosmosSearch` [needs SME confirmation, see open question 4].
2. If it exists, query with `$search` + `cosmosSearch` and project `searchScore` (see vector-knn-query). This is the only production path. Choose the search parameter by kind: `lSearch` for `vector-diskann`, `efSearch` for `vector-hnsw`, `nProbes` for `vector-ivf`.
3. If it is missing, create it from the app with the driver (`createIndexes`, see vector-index-templates) or fail loudly. An unavailable MCP tool is not a reason to skip the index, because the driver can create it. Do not fall back silently.
4. Client-side cosine is allowed only behind an explicit opt-in (for example `VECTOR_SEARCH_MODE=client` or a test fixture). It must log a WARNING naming the missing index, and the README must label it a test-only fallback.

Incorrect:

```python
# "Works" on a 20-doc seed, reads the whole collection on every query, never uses the index.
docs = list(coll.find({}, {"embedding": 1, "text": 1}))
scored = sorted(((cosine(q, d["embedding"]), d) for d in docs), key=lambda t: t[0], reverse=True)[:k]
```

Correct:

```python
import logging, os

SEARCH_PARAM = {"vector-diskann": ("lSearch", 40),
                "vector-hnsw":    ("efSearch", 40),
                "vector-ivf":     ("nProbes", 1)}

def vector_index(coll, field="embedding"):
    for ix in coll.list_indexes():                      # listIndexes
        if ix.get("key", {}).get(field) == "cosmosSearch":
            return ix
    return None

def search(coll, query_vector, k=5, filter=None):
    ix = vector_index(coll)
    if ix is not None:
        kind = ix.get("cosmosSearch", {}).get("kind")
        cs = {"path": "embedding", "vector": query_vector, "k": k}
        if kind in SEARCH_PARAM:
            name, default = SEARCH_PARAM[kind]
            # lSearch must be >= k; efSearch/nProbes keep their defaults unless tuned
            cs[name] = max(default, 4 * k) if name == "lSearch" else default
        if filter:
            cs["filter"] = filter
        pipeline = [
            {"$search": {"cosmosSearch": cs}},
            {"$project": {"_id": 1, "text": 1, "source": 1,
                          "score": {"$meta": "searchScore"}}},
        ]
        return list(coll.aggregate(pipeline))

    if os.getenv("VECTOR_SEARCH_MODE") != "client":
        raise RuntimeError(
            "No cosmosSearch index on 'embedding'. Create it with createIndexes "
            "(see vector-index-templates) or set VECTOR_SEARCH_MODE=client "
            "for the test-only client-side fallback.")
    logging.warning("TEST-ONLY FALLBACK: ranking client-side; no cosmosSearch index found")
    return _client_side_cosine(coll, query_vector, k)   # offline tests only
```

Node.js equivalent: `const ix = (await coll.indexes()).find(i => i.key?.embedding === "cosmosSearch")`, read `ix.cosmosSearch.kind`, then `await coll.aggregate([...]).toArray()`.

References: the Learn vector-search page (query syntax per index kind; "Get vector index definitions" shows the `listIndexes` output shape), vector-knn-query, vector-index-templates.

### 4. `skills/vector-search/SKILL.md`

Add this under the sub-type table:

```markdown
- **Not the API:** a vector index is always `createIndex`/`createIndexes` with key
  `{ <field>: "cosmosSearch" }` + `cosmosSearchOptions` (`kind`: `vector-ivf`, `vector-hnsw`,
  `vector-diskann`), queried with `$search: { cosmosSearch: {...} }`. Not `createSearchIndexes`
  (BM25 full-text only), Atlas `createSearchIndex`, `knnVector`, `type: "vector"` /
  `type: "vectorSearch"` or `$vectorSearch`. Store vectors as `number[]`; BSON Binary vectors are not indexed.
```

Add two entries to the Rules list:
- `vector-index-templates`: "Copy-paste createIndexes for all three kinds, with per-kind build and query keys."
- `vector-prefer-server-side-search`, directly above `vector-knn-query`: "Check the index exists (`listIndexes`) and create it with the driver if it is missing; query with `$search`/`cosmosSearch`. Client-side cosine is a labelled test-only fallback, never the default path."

Extend the `vector-normalize-embeddings` line with "store vectors as `number[]`, never BSON Binary." Optionally extend the front-matter `description` with "...and never falling back to client-side similarity in production."

### 5. Small edits

- `vector-knn-query.md` Tips: "Never replace this stage with `find()` + in-process cosine; if the index is missing, see vector-prefer-server-side-search." Also: "`lSearch` applies to `vector-diskann`; use `efSearch` for `vector-hnsw` and `nProbes` for `vector-ivf`."
- `vector-create-diskann-index.md` and `vector-choose-index-type.md`: link to vector-index-templates so HNSW/IVF readers are not left with DiskANN-only key names.
- `vector-create-diskann-index.md` parameter table only: add the row `| Field type | number[] | — | BSON Binary / other types are not indexed; those documents are excluded from $search |`.
- Optional: mirror the HNSW/IVF parameter rows into `skills/query-optimizer/references/core-indexing-principles.md`, whose tier table lists `vector-hnsw` and `vector-ivf` with no parameters.
- `CHANGELOG.md`: "vector-search: index templates for all kinds, Incorrect Atlas/MongoDB 7 create shapes (`createSearchIndexes`, `knnVector`, `type: 'vector'`), number[] storage rule, server-side search rule."

## Evidence

- `runs/07-voice-of-customer-sentiment-hub/20261124-204049/`: `createSearchIndexes` used for the vector index, `CommandNotSupported` swallowed, no vector index created
- `runs/14-customer-complaint-classifier/20261124-201931/`: `createSearchIndexes` for the vector index plus a `$search.knn` query; the audit marked both as met
- `runs/11-visual-similarity-search-image-embeddings/20261124-184225/`: `bson.Binary(..., subtype=0x09)` in `app/scripts/seed.py`; "expected an array type field"
- `runs/01-product-catalog-with-vector-search/20261124-175429/`: BSON Binary embeddings, `/search` ranks client-side
- `runs/02-clinical-trial-matching-orchestration/20261124-193208/`: HNSW with DiskANN keys, then `find()` + cosine as the only query path
- `runs/04-earnings-call-rag-assistant/20261124-190247/`: `find()` + `np.dot` over the whole collection; the documented `vector-diskann` index is never queried
- `runs/20-provider-directory-semantic-search/20261124-200008/02-readiness.json`: cold `knnVector` answer; the shipped HNSW parameters came from Learn

Side note for the experiment owner, not part of this PR: the audit in run 14 marked a `createSearchIndexes` vector index and a `$search.knn` query as met, so the audit does not check the command surface.

## Open questions

1. [needs SME confirmation] Please confirm the HNSW and IVF limits and defaults in the tunables table: `m` 2-100/16, `efConstruction` 4-1000/64 and ≥ 2*`m`, `efSearch` default 40, IVF `numLists` = documentCount/1000 up to 1M, `nProbes` default 1 and ≤ `numLists`, the tier guidance (IVF on M10/M20, HNSW/DiskANN on M30+, about 50k vectors for HNSW), and the 2,000/4,000/16,000 dimension limits.
2. [needs SME confirmation] Learn names `double[]` as the example of a non-indexed type. Are BSON Binary vectors (subtype 0x09) definitely excluded in the same way? Should the error builds saw ("expected an array type field") be documented?
3. [needs SME confirmation] Is full-text search (`createSearchIndexes`) still in preview and enabled per cluster? Is `CommandNotSupported` ("Search index creation is not supported yet") the expected response when it is off?
4. [needs SME confirmation] Does `listIndexes` always report vector options under `cosmosSearch` (not `cosmosSearchOptions`) on current server versions? The existence check depends on this.

## Source drafts

- 113-vector-search-and-indexing-skills-lack-copy-paste-idempotent.md (lead for the templates). Moved to K06: its `skills/indexing/index-create-from-app-code.md` rule (`ensure_vector_index`, Python and Node.js), the ORM caveat (Mongoose `autoIndex`, Beanie `Indexed()`), the `listIndexes` shape check plus probe query verification, the `skills/indexing/examples/` files, and the `mcp-setup/SKILL.md` one-liner.
- 019-believes-vector-indexes-use-mongodb-atlas-community-syntax-k.md (the Incorrect block and `SKILL.md` bullet; placed in the templates file, as the draft suggested if templates land)
- 021-agent-kit-gap-vector-search-skill-shows-a-full-createindex-e.md (its separate HNSW and IVF rule files are merged into vector-index-templates)
- 039-believes-vector-indexes-queries-use-atlas-or-upstream-syntax.md
- 114-samples-fell-back-to-client-side-cosine-similarity-instead-o.md
