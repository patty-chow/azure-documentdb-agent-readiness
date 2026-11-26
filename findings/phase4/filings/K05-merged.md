---
id: K05
title: "vector-search skill: number[] storage rule, copy-paste IVF/HNSW/DiskANN index templates with $search as the primary query path, idempotent ensure-index from app code, and a response-shape rule (score, no raw vectors)"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P1
sample_count: 73
member_drafts:
  - 113-vector-search-and-indexing-skills-lack-copy-paste-idempotent.md
  - 019-believes-vector-indexes-use-mongodb-atlas-community-syntax-k.md
  - 021-agent-kit-gap-vector-search-skill-shows-a-full-createindex-e.md
  - 039-believes-vector-indexes-queries-use-atlas-or-upstream-syntax.md
  - 114-samples-fell-back-to-client-side-cosine-similarity-instead-o.md
  - 097-vector-rag-samples-bypass-server-side-cosmossearch-index-nev.md
  - 086-seed-and-index-recipe-idempotent-seed-bootstrap-index-lifecy.md
  - 099-indexes-do-not-match-the-sample-s-actual-query-workload-esr-.md
  - 094-http-and-search-rag-response-contract-for-samples-input-vali.md
merged_from:
  - K05
  - K06
  - K31
open_questions: 3
---

# vector-search skill: `number[]` storage rule, copy-paste IVF/HNSW/DiskANN index templates with `$search` as the primary query path, idempotent ensure-index from app code, and a response-shape rule (score, no raw vectors)

> **Suggested split.** Everything under `skills/vector-search/` is one PR. The reviewer may split the indexing half that came from K06 (`skills/indexing/*`, `skills/mcp-setup/SKILL.md`, `skills/query-optimizer/SKILL.md`, `skills/query-optimization/query-explain-plan.md`, `skills/local-deployment/local-prod-parity.md`) into a second PR. The two halves cross-link but neither one needs the other to merge first.

## What happens today

In one experiment run, gpt-5-mini built 100 Azure DocumentDB sample apps. It used this kit and the DocumentDB, Azure and Learn MCP servers, with the DocumentDB MCP server configured from the kit's own `mcp.json` (`ENABLE_MANAGEMENT_TOOLS` and `ENABLE_WRITE_TOOLS` both `"false"`). `events.jsonl` shows the agents loaded `documentdb-vector-search` and `documentdb-indexing`. The query side of `skills/vector-search/` is mostly right: `vector-knn-query.md` marks Atlas `$vectorSearch` as unsupported and shows `$search` + `cosmosSearch`. The gaps:

1. **Only DiskANN has a create example.** `vector-create-diskann-index.md` is complete. `vector-hnsw` appears only in tier tables (`SKILL.md`, `vector-choose-index-type.md`, `skills/query-optimizer/references/core-indexing-principles.md`), and so does `vector-ivf`; `numLists` appears only in the "Incorrect" block of `vector-choose-index-type.md`. `efConstruction`, `efSearch` and `nProbes` appear nowhere in `skills/` or `knowledge-base/`. Every example is mongosh JavaScript, but most generated samples used PyMongo.
2. **No create-side "wrong surface" warning.** Nothing says that `createSearchIndex(es)`, `knnVector`, `knnBeta` or `type: "vector"` do not create a vector index. The two surfaces are separated only by two comments in `skills/full-text-search/fts-hybrid-search.md`. The full-text-search skill (correctly) teaches `createSearchIndexes` for BM25, so models merge the two.
3. **No storage-type rule.** No file says vectors must be stored as `number[]`. Learn says that "Vectors must be a `number[]` to be indexed", and documents of other types are not indexed and not returned.
4. **No rule that the database does the search, and no rule for creating the index from app code.** Nothing says that `$search` is the required query path, how to check that the index exists, or what to do when it is missing. The MCP `create_index` tool is management-gated, and agents got `Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true to opt in.` The flag is mentioned in `mcp-setup/SKILL.md` (lines 154-155), but no skill an agent reads while creating an index names the gate, the error text or the driver fallback. `query-optimizer/SKILL.md` line 65 lists `create_index` with no mention of the gate. Agents retried two to four times, then wrote "create the index manually in the portal" or fell back to `find({})` + cosine. None used a driver `createIndexes`.
5. **No seed/index lifecycle.** Agents created indexes in query helpers, in an aggregation path, after bulk upserts, or through Mongoose `autoIndex`. One build combined `autoIndex:false`, a schema `index: true` and a field missing from `create_indexes.js`, so the index was never created. Indexes had default names and no manifest. A seed that called itself idempotent generated random ids and duplicated its data on re-run. In three samples, placeholder embeddings already in a collection made `createIndex` fail with `expected 1536 dimensions, not 3` (code 2, BadValue), and the agent moved on. The kit covers index shapes (ESR, cookbook, partial indexes) and `local-prod-parity.md` has a `schema/01_indexes.js` example, but nothing ties them into a create-and-verify lifecycle.
6. **Declared indexes did not match the queries.** Indexes were declared from the cookbook up front, the queries were written afterwards, and the two were never reconciled. Examples: single-field indexes where queries filter on two fields, a compound index whose equality prefix the query never supplies, indexed fields no query touches, filter fields with no index, and a `$facet` pipeline that `explain` showed as COLLSCAN.
7. **No response contract.** The only related text is `vector-knn-query.md` line 64: "Always project `searchScore` if you plan to rerank or threshold." Agents read the condition literally and skipped it. Nothing says to project the embedding out, to flag a fallback path, or how a search/RAG endpoint should fail on an empty query or an embedding-provider error. (`fts-basic-search.md` asks for `searchScore`, but only for BM25.) The Learn IVF examples project `"document": "$$ROOT"`, which also returns the vector, so agents had no counter-example to copy.

## Why it matters

Each member's sample count is kept below. All counts come from a single experiment run and should not be quoted as rates.

- **Wrong create command, cold quiz (K05: 74 findings, 72 samples).** Asked cold "which vector index types are supported, and what does the create command look like?", the model answered with Atlas or MongoDB 7 shapes: `createSearchIndex` with `knnVector`, `createIndex({embedding: "vector"})`, or HNSW `M`/`efConstruction: 200` inside a `knnVector` block. Most answers were corrected once a skill loaded, but two shipped anyway with the skill loaded. In run 07, `createSearchIndexes` was used for the vector index, the call failed with `CommandNotSupported`, the error was swallowed, and the app shipped with no vector index. In run 14, `createSearchIndexes` was used too, the query was `$search: { knn: ... }`, and the audit marked both as met. Where HNSW was built correctly, the parameters came from Learn, not the kit.
- **Atlas/upstream priors and BSON Binary storage (K05: 90 findings, 69 samples).** 87 were further cold-quiz answers (`knnVector`, `$vectorSearch`, `createSearchIndexes` for vectors, `$text`) that the skill corrected. Three prompts asked for "BSON binary vectors". In 4 of the 5 builds of those prompts, the floats were packed into BSON Binary (`bson.Binary(vec.tobytes(), subtype=0x09)`). `cosmosSearch` does not index those documents, so `$search` never returns them. Two builds fell back to client-side ranking, and one audit records "Invalid type: expected an array type field".
- **Improvised index creation and query paths (K05: 16 findings in 14 samples, plus 2 findings in 2 samples).** Builds put DiskANN keys on an HNSW index, put `path` inside `cosmosSearchOptions`, tried `createSearchIndexes`, or left index creation as a manual README step. Two builds shipped `find()` + in-process cosine as their only query path.
- **Index creation and verification from app code (K06: 107 findings, 55 samples; the member drafts counted 26, 14 and 29 samples, which overlap).** The management-gate error appears in 32 of 100 samples' `events.jsonl`, and 36 hit it or the matching write-tools gate. Without a `cosmosSearch` index, `listIndexes` showed only `_id`, retrieval became `find({})` + cosine, and some apps returned the 1536-float arrays. Other mistakes: the key `{ cosmosSearch: "cosmosSearch" }` (fails with `Similarity index not found`), `vector-ivf` with `numLists: 100` on 5 documents, and HNSW with no `m`/`efConstruction` chosen or recorded. The seed-and-index audit requirement scored below `met` in 43 of 115 audits (39 samples), and 29 samples shipped indexes that do not match their queries.
- **Response shape (K31: 7 findings, 7 samples in scope).** Ranked results came back with no score (one risk screener derived its "risk score" from match counts), raw vectors went back to a chat client, fallbacks were indistinguishable from real vector hits, and an empty `q` or a provider outage surfaced as an unhandled 500. A keyword scan of all audit files suggests the problem is wider (about 31 samples dropped the score, 7 returned raw vectors and 22 fell back silently). The scan is not hand-verified. Out of scope and not counted: six more findings from five samples (one with no auth or rate limiting on LLM endpoints, one with ad-hoc multi-agent JSON shapes, and four from a harness audit item that expected a `/search` endpoint the prompt never asked for).

These samples are meant to be copied. Today some of them demonstrate client-side cosine instead of server-side `cosmosSearch`, indexes that don't serve their own queries, and search APIs that hide whether the vector path ran.

**About the counts.** The member findings do not overlap (182 + 107 + 7 ids), but their sample sets do, so the sample count is not a sum. 73 is a firm floor. It is K05's 72 distinct cold-quiz samples plus `01-patient-record-summarizer-rag`, which K06's draft 086 cites for the `expected 1536 dimensions, not 3` failure and which has no cold-quiz vector finding. A recount of `findings.jsonl` (default-arm runs only) finds a Q08 vector-index cold-quiz finding in 97 of the 100 samples, so the true union is probably between 73 and 98. The 97 cannot be attributed to these drafts with certainty. All figures come from one run.

## Proposed change (file by file)

### `skills/vector-search/SKILL.md`

1. Directly under the sub-type/tier table, add a **Hard rules** block. It combines K05's "Not the API" bullet with draft 097's hard rules:

```markdown
## Hard rules
- **Not the API:** a vector index is always `createIndex`/`createIndexes` with key
  `{ <field>: "cosmosSearch" }` + `cosmosSearchOptions` (`kind`: `vector-ivf`, `vector-hnsw`,
  `vector-diskann`), queried with `$search: { cosmosSearch: {...} }`. Not `createSearchIndexes`
  (BM25 full-text only), Atlas `createSearchIndex`, `knnVector`, `type: "vector"` /
  `type: "vectorSearch"`, `knnBeta` or `$vectorSearch`. `{ cosmosSearch: "cosmosSearch" }` is wrong:
  it targets a field literally named `cosmosSearch`.
- Store vectors as `number[]`. BSON Binary / packed / base64 vectors are not indexed.
- Create and verify the vector index from your own seed/startup code with `createIndexes` +
  `cosmosSearchOptions`, then `listIndexes` (see vector-ensure-index). Do not depend on the MCP
  `create_index` tool (management-gated, off by default).
- Never fall back to client-side cosine over `find({})` in production (see vector-prefer-server-side-search).
- Always project `{ $meta: "searchScore" }` and leave the embedding field out of results; push
  metadata predicates into `cosmosSearch.filter` (backed by a regular index on the filter field)
  (see vector-search-response-shape).
- Lexical / hybrid retrieval is a search index (`createSearchIndexes`) queried with `$search`
  (`documentdb-full-text-search`), not `$regex`, `$text` or Atlas Search.
```

2. In the **Rules** list:
   - Add `- [vector-index-templates](vector-index-templates.md) — Copy-paste createIndexes for all three kinds, with per-kind build and query keys.`
   - Add `- [vector-ensure-index](vector-ensure-index.md) — Create the vector index idempotently from seed/startup code with the driver and verify it (listIndexes + probe query); never depend on the MCP tool.`
   - Directly above `vector-knn-query`, add `- [vector-prefer-server-side-search](vector-prefer-server-side-search.md) — Check the index exists (\`listIndexes\`) and create it with the driver if it is missing; query with \`$search\`/\`cosmosSearch\`. Client-side cosine is a labelled test-only fallback, never the default path.`
   - Extend the `vector-normalize-embeddings` line with "store vectors as `number[]`, never BSON Binary; probe the embedding dimension at startup."
   - After the `vector-normalize-embeddings` line, add `- [vector-search-response-shape](vector-search-response-shape.md) — Return \`searchScore\` on every hit, project the embedding field out, flag fallback paths, and return 400/502 instead of 500 for empty queries / embedding failures.`
3. In the front-matter `description`, replace "and normalizing embeddings for cosine similarity." with "normalizing embeddings for cosine similarity, `number[]` storage, idempotent index creation from application code (never falling back to client-side similarity in production), and shaping search/RAG responses (score, no raw vectors, fallback flag, clear errors)." Routing then picks the skill up when an agent plans a seed script or asks what `/search` should return.

### `skills/vector-search/vector-index-templates.md` (new)

Use the existing rule format (Category/Priority, Why it matters, Incorrect, Correct, References). It merges the separate HNSW and IVF rule files proposed in draft 021.

**Correct:** three `createIndexes` documents on the same field that differ only in `cosmosSearchOptions`. `EMBEDDING_DIM` must come from the same config that selects the embedding model.

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

The mongosh helper form `db.<coll>.createIndex({ embedding: "cosmosSearch" }, { name, cosmosSearchOptions: {...} })` is equivalent; show it once next to the command form. `similarity` is `COS`, `L2` or `IP`. For app code, link to vector-ensure-index.

**Tunables** (every range and default is from the Learn vector-search page's per-algorithm tabs, https://learn.microsoft.com/en-us/azure/documentdb/vector-search; the M30 floor for HNSW and DiskANN is from the limitations page):

| kind | recommended tier / scale | build keys (range, default) | query key in `$search.cosmosSearch` | for more recall |
|---|---|---|---|---|
| `vector-ivf` | M10/M20, under ~10k vectors | `numLists`: 1 for demos (brute force, most accurate); `documentCount/1000` up to 1M docs; above 1M use DiskANN (the page's Important box; its field table says `sqrt(documentCount)`, see open question 1). Sized from the document count, so create it after loading and re-tune (drop and recreate) as the collection grows | `nProbes` (default 1, ≤ `numLists`) | raise `nProbes` |
| `vector-hnsw` | M30+, up to ~50k vectors; can be built on an empty collection | `m` 2-100 (default 16); `efConstruction` 4-1000 (default 64, ≥ 2*`m`) | `efSearch` (default 40) | raise `m` / `efConstruction` / `efSearch`; large HNSW builds can exhaust memory, so prefer DiskANN or a larger tier |
| `vector-diskann` | M30+, 500k+ vectors | `maxDegree` 20-2048 (default 32); `lBuild` 10-500 (default 50) | `lSearch` 10-1000 (default 40, ≥ `k`) | raise `maxDegree` / `lBuild` / `lSearch` |

Local parity: the `documentdb-local` container has only `vector-ivf` and `vector-hnsw` (no DiskANN, no `pq` compression; 2,000 dimensions uncompressed, 4,000 with `compression: "half"`), so the templates and the ensure helper must let `kind` be configured (see local-prod-parity).

**Incorrect** (these are Atlas / MongoDB 7 shapes, not DocumentDB vector indexes):

```javascript
db.runCommand({ createSearchIndexes: "products",   // BM25 full-text indexes only; never vectors
  indexes: [{ name: "vec", type: "vector", fields: [{ path: "embedding", type: "vector", dimensions: 1536 }] }] });
db.products.createIndex({ embedding: "vector" }, { engine: "hnsw", dimensions: 1536 });
db.products.createIndex({ embedding: "knnVector" }, { knnVector: { dimensions: 1536, method: "hnsw", m: 16, efConstruction: 200 } });
db.products.createSearchIndex({ name: "vec", definition: { mappings: { fields: { embedding: { type: "knnVector", dimensions: 1536 } } } } });
db.products.createSearchIndex({ name: "vec", type: "vectorSearch",
  definition: { fields: [{ type: "vector", path: "embedding", numDimensions: 1536, similarity: "cosine" }] } });
db.products.createIndex({ cosmosSearch: "cosmosSearch" }, { cosmosSearchOptions: { kind: "vector-diskann", dimensions: 1536, similarity: "COS" } });
// ^ indexes a field literally named "cosmosSearch"; queries on "embedding" fail with "Similarity index was not found for a vector similarity search query."
```

Follow it with one sentence: a vector index is an ordinary `createIndex` / `createIndexes` call whose key is `{ <field>: "cosmosSearch" }` with `cosmosSearchOptions`, queried with `$search: { cosmosSearch: {...} }`. `createSearchIndexes` is the full-text search index command. Full-text search is in preview and is enabled per cluster (portal: Settings > Features > Full-text search > Enable, or add `FullTextSearch` to `properties.previewFeatures` with the Azure CLI, Bicep or Terraform). On a cluster where it is not enabled, `createSearchIndexes` fails with `CommandNotSupported` (code 115, "Search index creation is not supported yet"); that is a configuration state, not a reason to retry with another index shape. Right after enabling, the same message comes back under 115 and then 67 `CannotCreateIndex` until activation finishes (about 210 s in one managed test), so retry the same call with backoff; Learn's ten minutes is an upper bound, not a fixed wait. The two meet only at query time, in hybrid search (see `fts-hybrid-search`).

**Common mistakes** (each one occurred in the experiment's builds):
- `path` belongs in the `$search.cosmosSearch` query, not in `cosmosSearchOptions`.
- DiskANN keys (`maxDegree`, `lBuild`) on an HNSW index, or HNSW keys on DiskANN: use the template for the kind you chose.
- `vector-ivf` with a large `numLists` (for example 100) on a handful of demo documents: use `numLists: 1` and re-tune as the collection grows.
- `dimensions` must equal the embedding length. Without compression the maximum is 2,000 dimensions. Half-precision (`compression: "half"`, HNSW/IVF) raises it to 4,000 (the engine rejects 4,001 with "field cannot have more than 4000 dimensions for vector index"), and DiskANN with product quantization raises it to 16,000 (Learn vector-search, half-precision, product-quantization and limitations pages; the managed test of 2026-11-25 confirmed every ceiling on the service, and 16,001 fails with 67). `compression: "half"` is rejected on DiskANN (67 "Compression type 'half' is not supported for diskann index"). A 3,072-dimension model therefore needs one of those options. The 8,000 figure on the select-algorithm quickstarts is wrong (product owner, 2026-11-25); the Learn vector filing asks for the correction.
- Vectors must be stored as `number[]` (see vector-normalize-embeddings).
- Only one vector index is allowed per path ("You can create only one index per vector path", Learn vector-search and limitations pages). If `createIndexes` fails because an index on the same key already exists, reuse its name, or drop and recreate it deliberately: a second vector index on the path fails with 85 `IndexOptionsConflict`, and the same name with other options fails with 86 `IndexKeySpecsConflict` (managed service and documentdb-local; undocumented on Learn).

### `skills/vector-search/vector-ensure-index.md` (new)

Category Vector Search, Priority HIGH. Rule: create the vector index in seed/startup code with the driver, idempotently, and verify it. Don't depend on the MCP tool. Call the helper from the seed script and, cheaply, at app startup. Guard the call with `if os.environ.get("CREATE_INDEXES", "true") == "true"` so a seed run can be re-run safely. If the index is missing at query time, fail with an explicit error; never fall back to scanning the collection.

**Incorrect:** relying on the MCP `create_index` tool, then catching the exception and falling back to `find({})` + client-side cosine, or telling the user to "create the index manually in the portal".

**Correct (Python, raw command so it works on every driver):**

```python
import os

def _opts(ix):
    # listIndexes reports the options under "cosmosSearchOptions" (managed service and documentdb-local);
    # Learn's "Get vector index definitions" sample, which shows "cosmosSearch", is wrong.
    return ix.get("cosmosSearchOptions") or {}

def ensure_vector_index(db, coll, field, dims, similarity="COS", kind=None, name=None):
    assert isinstance(dims, int) and dims > 0, "derive dims from an embedding probe / EMBEDDING_DIMS"
    kind = kind or os.getenv("VECTOR_INDEX_KIND", "vector-diskann")
    c = db[coll]
    bad = c.count_documents({field: {"$exists": True}, "$expr": {"$or": [
        {"$not": [{"$isArray": f"${field}"}]},
        {"$ne": [{"$size": {"$cond": [{"$isArray": f"${field}"}, f"${field}", []]}}, dims]}]}})
    if bad:
        raise SystemExit(f"{bad} docs have {field} that is not a number[] of length {dims}; re-embed first")
    for ix in c.list_indexes():                      # one vector index per path: match on the key
        if ix["key"].get(field) == "cosmosSearch":
            o = _opts(ix)
            assert (o.get("kind"), o.get("dimensions"), o.get("similarity")) == (kind, dims, similarity), \
                f"{ix['name']} has {o}; drop and recreate deliberately"
            return ix["name"]
    opts = {"kind": kind, "dimensions": dims, "similarity": similarity}
    if kind == "vector-ivf":
        # numLists is sized from the document count: create the IVF index after loading (Learn vector-search)
        opts["numLists"] = int(os.getenv("IVF_NUM_LISTS", max(1, c.estimated_document_count() // 1000)))
    elif kind == "vector-hnsw":
        m = int(os.getenv("HNSW_M", 16))
        opts.update(m=m, efConstruction=max(2 * m, int(os.getenv("HNSW_EF_CONSTRUCTION", 64))))  # >= 2*m
    else:  # vector-diskann
        opts.update(maxDegree=int(os.getenv("DISKANN_MAX_DEGREE", 32)), lBuild=int(os.getenv("DISKANN_L_BUILD", 50)))
    name = name or f"{coll}_{field}_{kind.replace('vector-', '')}"
    db.command({"createIndexes": coll, "indexes": [
        {"key": {field: "cosmosSearch"}, "name": name, "cosmosSearchOptions": opts}]})
    assert name in {ix["name"] for ix in c.list_indexes()}, f"{name} not listed after createIndexes"
    return name
```

Add a short Node.js equivalent with the same env vars and error branch, using `await db.command({ createIndexes: coll, indexes: [...] })` and `await db.collection(coll).indexes()` (or `listIndexes().toArray()`).

**Verification step** (from draft 113; also usable as a dev/CI check):

```python
# 1. Index exists with the right shape
ix = next(i for i in db[coll].list_indexes() if i.get("key", {}).get("embedding") == "cosmosSearch")
assert _opts(ix).get("dimensions") == EMBEDDING_DIM
# 2. A probe vector query runs; a missing index raises code 2
#    "Similarity index was not found for a vector similarity search query."
probe = embed("probe")
assert len(probe) == EMBEDDING_DIM, "embedding model output does not match EMBEDDING_DIM"
hits = list(db[coll].aggregate([{"$search": {"cosmosSearch":
        {"path": "embedding", "vector": probe, "k": 3}}}]))
assert hits, "vector query returned no results (are vectors stored as number[]?)"
```

Text bullets in the file:
- The key is `{ <field>: "cosmosSearch" }`. Payloads per kind are in vector-index-templates, and storage rules are in vector-normalize-embeddings.
- Use one `EMBEDDING_DIMS` value for both the embedder and this function. Run the dimension check before `createIndexes` so placeholder vectors (for example 3 floats against 1536) fail with a clear message, not `expected 1536 dimensions, not 3`.
- Only one vector index per path (Learn vector-search, limitations), so changing `dimensions` or `kind` means drop and recreate.
- HNSW can be built on an empty collection (Learn vector-search, HNSW column). IVF's `numLists` depends on the document count, so create or re-create the IVF index after loading the data (start with `numLists: 1` for a demo and recreate it later); a product-quantization index should also be created after the collection has data (Learn product-quantization page, note).
- Learn says a newly created index can return empty results for 2 to 3 minutes while it builds (quickstart-nodejs-select-algorithm, Troubleshooting); on the managed service, HNSW, DiskANN and IVF indexes on 5-document collections returned complete results on the first query (large collections were not tested). Retry the probe query a few times on an empty result instead of failing app startup at once.
- For the scalar filter/pre-filter indexes created alongside the vector index, run the `explain` command with `verbosity: "executionStats"` on the representative filter query and fail unless the leaf scan stage is an `IXSCAN` on that index (see the explain note under index-ensure-script-lifecycle). Do not use a COLLSCAN string check to test the vector index, because a `$search` without a vector index errors (code 2, "Similarity index was not found ...") instead of scanning.
- ORM schema declarations (Mongoose `autoIndex`, Beanie `Indexed()`) do not replace this call for a vector index. Call it from the seed/startup script.
- The MCP tool is fine for interactive work once `ENABLE_MANAGEMENT_TOOLS=true`, but a repository must not depend on it (see mcp-setup → Gated tools).

### `skills/vector-search/vector-prefer-server-side-search.md` (new)

Same rule format, Category Vector Search, Priority HIGH. **Why it matters:** a `cosmosSearch` index exists so that Azure DocumentDB does the nearest-neighbour search. Pulling documents with `find()` and ranking them in the app reads the whole collection on every query, ignores the index and teaches the wrong pattern. It is acceptable only as an explicitly labelled fallback for offline tests with a mocked collection.

Rule:
1. Check that a `cosmosSearch` index exists on the embedding field with `listIndexes` (`collection.list_indexes()` in PyMongo, `collection.indexes()` in Node.js). It appears as `key: { <field>: "cosmosSearch" }`, with its options, including `kind`, under `cosmosSearchOptions` (managed service and documentdb-local; the Learn vector-search sample "Get vector index definitions", which shows them under `cosmosSearch`, is wrong).
2. If it exists, query with `$search` + `cosmosSearch` and project `searchScore` (see vector-knn-query and vector-search-response-shape). This is the only production path. Choose the search parameter by kind: `lSearch` for `vector-diskann`, `efSearch` for `vector-hnsw`, `nProbes` for `vector-ivf`.
3. If it is missing, create it from the app with the driver (see vector-ensure-index) or fail loudly. An unavailable MCP tool is not a reason to skip the index, because the driver can create it. Do not fall back silently.
4. Client-side cosine is allowed only behind an explicit opt-in (for example `VECTOR_SEARCH_MODE=client` or a test fixture). It must log a WARNING naming the missing index, the response must carry `search_source: "fallback"` (see vector-search-response-shape), and the README must label it a test-only fallback.

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
        kind = ix.get("cosmosSearchOptions", {}).get("kind")
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
        return {"search_source": "cosmosSearch", "results": list(coll.aggregate(pipeline))}

    if os.getenv("VECTOR_SEARCH_MODE") != "client":
        raise RuntimeError(
            "No cosmosSearch index on 'embedding'. Create it with createIndexes "
            "(see vector-ensure-index) or set VECTOR_SEARCH_MODE=client "
            "for the test-only client-side fallback.")
    logging.warning("TEST-ONLY FALLBACK: ranking client-side; no cosmosSearch index found")
    return {"search_source": "fallback", "results": _client_side_cosine(coll, query_vector, k)}  # offline tests only
```

Node.js equivalent: `const ix = (await coll.indexes()).find(i => i.key?.embedding === "cosmosSearch")`, read `ix.cosmosSearchOptions.kind`, then `await coll.aggregate([...]).toArray()`.

References: the Learn vector-search page (query syntax per index kind; its "Get vector index definitions" sample shows the options under `cosmosSearch`, while the service reports `cosmosSearchOptions`), vector-knn-query, vector-index-templates, vector-ensure-index, vector-search-response-shape.

### `skills/vector-search/vector-search-response-shape.md` (new)

````markdown
# vector-search-response-shape

**Category:** Vector Search · **Priority:** HIGH

## Why it matters

A `$search` + `cosmosSearch` pipeline is only half of a search feature; the other half is
what your API hands back. Return the score, never the vector, say which path produced the
results, and fail before you hit the database when the input is unusable. Callers (UIs,
tests, downstream agents) can then threshold, explain and trust the results.

Rules:
- **Always project `score: { $meta: "searchScore" }`** and return it on every hit, not only
  when you rerank. For RAG, return a `sources` list of `{ _id, score, ...display fields }`
  next to the answer so citations can be checked.
- **Project the embedding field out.** Never return raw vectors in user- or agent-facing
  responses. Fetch vectors only for reindexing/admin paths, behind an explicit flag.
- **Flag any fallback.** If your code can fall back from `$search` to client-side cosine
  or a metadata `find` (e.g. the index is missing), return `search_source: "cosmosSearch" |
  "fallback"`. Prefer failing loudly when the index is missing over silently degrading
  (see vector-prefer-server-side-search).
- **Validate before you embed.** Empty/whitespace query → `400 { "error": "empty query" }`
  before any embedding call. Embedding-provider failure → `502 { "error": ..., "code":
  "embedding_failed" }`, never an unhandled 500. Log the full exception server-side only.

## Incorrect

```javascript
// Returns the raw 1536-float vector to the chat client, no score, no origin
const docs = await coll.find({}, { projection: { title: 1, content: 1, embedding: 1 } }).toArray();
return docs.map(d => ({ ...d, score: cosine(qEmb, d.embedding) }));  // silent client-side fallback
```

```python
@app.post("/search")
def search(req: Query):
    qvec = embed(req.q)            # empty string embedded; provider error -> 500
    hits = coll.aggregate([{"$search": {"cosmosSearch": {"path": "embedding", "vector": qvec, "k": 5}}}])
    return list(hits)              # no score; embedding field returned on every hit
```

## Correct

```python
from fastapi import FastAPI, HTTPException
app = FastAPI()

@app.post("/search")
def search(req: Query, include_vectors: bool = False):
    q = (req.q or "").strip()
    if not q:
        raise HTTPException(400, {"error": "empty query", "code": "empty_query"})
    try:
        qvec = embed(q)
    except Exception:                 # provider/network/quota error
        log.exception("embedding failed")
        raise HTTPException(502, {"error": "embedding provider failed",
                                  "code": "embedding_failed",
                                  "remediation": "check EMBEDDING_* settings and provider status"})
    project = {"_id": 1, "title": 1, "score": {"$meta": "searchScore"}}
    if include_vectors:               # admin/reindex use only
        project["embedding"] = 1
    hits = list(coll.aggregate([
        # lSearch is the DiskANN knob (k <= lSearch); use efSearch for vector-hnsw, nProbes for vector-ivf
        {"$search": {"cosmosSearch": {"path": "embedding", "vector": qvec, "k": min(req.k, 100), "lSearch": 100}}},
        {"$project": project},
    ]))
    return {"search_source": "cosmosSearch", "results": hits}
```

Test it: mock `embed` to raise and assert a 502 with `code == "embedding_failed"`; post an
empty query and assert 400; assert no result contains an `embedding` key by default.

## References

- [vector-knn-query](vector-knn-query.md) — the pipeline this rule shapes the output of
- [vector-prefer-server-side-search](vector-prefer-server-side-search.md) — when a fallback may exist at all
- [Vector search queries](https://learn.microsoft.com/azure/documentdb/vector-search)
````

The query-time knob names in the Correct example's comment (`lSearch` for `vector-diskann`, `efSearch` for `vector-hnsw`, `nProbes` for `vector-ivf`) and their defaults come from the Learn vector-search page's per-algorithm tabs. Maintainers may keep or drop the HTTP status mapping (open question 2).

### `skills/vector-search/vector-normalize-embeddings.md`

1. Add a rule bullet:

```markdown
- Store the vector as a plain array of numbers (`number[]`: `vec.tolist()` / `[float(x) for x in vec]`
  in Python, `Array.from(float32)` in Node.js). BSON Binary / packed-float32 vectors (Atlas
  "BinData vector" style) and packed/base64 strings are not indexed by `cosmosSearch`; those
  documents are left out of every `$search` result, with no error at insert or index time
  (the value is stored and returned intact; only indexing skips it). A BSON Binary *query*
  vector is rejected with "expected an array type field".
```

2. Add an Incorrect/Correct pair:

```python
# Incorrect: document is not indexed; $search never returns it
doc["embedding"] = bson.Binary(np.asarray(vec, dtype=np.float32).tobytes(), subtype=0x09)
# Correct
doc["embedding"] = [float(x) for x in vec]
```

3. Add a startup probe bullet: "At startup, embed one string and assert `len(vec)` equals the index `dimensions` before serving. If `EMBEDDING_MODEL` is configurable, derive the dimension count from the probe rather than hard-coding `1536`. Note the 2,000-dimension default limit without half-precision or product quantization (see vector-index-templates)."
4. Extend the existing provenance document shape with chunk lineage, keeping the kit's camelCase names:

```json
{ "sourceId": "...", "chunkIndex": 0, "text": "...",
  "embedding": [0.0123, ...],
  "embeddingModel": "text-embedding-3-small", "embeddingDims": 1536,
  "embeddingVersion": 1, "embeddedAt": "2026-11-25T00:00:00Z" }
```

### `skills/vector-search/vector-choose-index-type.md`

1. Link to vector-index-templates, so HNSW/IVF readers are not left with DiskANN-only key names.
2. Add after the table (ranges and defaults from the Learn vector-search page):

```markdown
### Sizing at creation time
| `vector-ivf` documents | `numLists` |
|---|---|
| small demo / new scenario | `1` (brute force), then tune |
| up to 1M | `documentCount / 1000` (minimum 1) |
| above 1M | use `vector-diskann` (the page's Important box; see open question 1) |

`nProbes` defaults to 1 and cannot exceed `numLists`. HNSW: `m` default 16 (2-100), `efConstruction` default 64 (4-1000, at least `2*m`), query `efSearch` default 40; defaults are valid, but choose and record values deliberately. Compute it, don't guess it: `n = coll.count_documents({}); num_lists = max(1, n // 1000)`. Re-tune by drop and recreate.
```

### `skills/vector-search/vector-knn-query.md`

1. Line 64: replace "Always project `searchScore` if you plan to rerank or threshold." with "Always project `searchScore` and return it to the caller; see [vector-search-response-shape](vector-search-response-shape.md)."
2. Add `knnBeta` to the Incorrect block next to `$vectorSearch`.
3. Add an Incorrect block: `find({}, {embedding: 1})` + cosine in the app, "with a fallback if the index is missing". State that client-side ranking is acceptable only for unit tests with a mocked collection, never as a runtime path.
4. Make the Correct pipeline canonical and complete: `$search.cosmosSearch { path, vector, k, lSearch | efSearch | nProbes, filter }` → `$project { _id: 1, title: 1, sourceId: 1, score: { $meta: "searchScore" } }` → `$limit k`. The inclusion projection already leaves out the embedding, so do **not** add `embedding: 0` to it, because mixing inclusion and exclusion is rejected. If an exclusion-style projection is preferred, use exclusion only (`{ embedding: 0 }` in a separate `$project`, or `$unset: "embedding"`). Say why the embedding is left out: several samples returned 1536 floats per hit.
5. Add a short query-key table next to the existing DiskANN table: `vector-hnsw` → `efSearch` (default 40); `vector-ivf` → `nProbes` (default 1, ≤ `numLists`); `vector-diskann` → `lSearch` (10-1000, default 40, `k` ≤ `lSearch`). Build keys stay in vector-index-templates. Replace the kit's existing "verify exact names against current docs" hedge with a link to the Learn vector-search page's per-algorithm tabs, which are the source of these names.
6. Add a PyMongo version of the pipeline under the JS one (`list(coll.aggregate([...]))`).
7. Tips: "Never replace this stage with `find()` + in-process cosine; if the index is missing, see vector-prefer-server-side-search." and "`lSearch` applies to `vector-diskann`; use `efSearch` for `vector-hnsw` and `nProbes` for `vector-ivf`."

### `skills/vector-search/vector-create-diskann-index.md`

1. Link to vector-index-templates (other kinds) and vector-ensure-index (app code).
2. Parameter table only: add the row `| Field type | number[] | — | BSON Binary / other types are not indexed; those documents are excluded from $search |`.

### `skills/indexing/SKILL.md`

Add `index-query-to-index-worksheet` (first) and `index-ensure-script-lifecycle` to the `## Rules` list. After the index-engine note, add the sentence: "Index design is not finished until the worksheet has been run against the final code."

### `skills/indexing/index-ensure-script-lifecycle.md` (new, Priority HIGH)

- Every app ships one version-controlled, idempotent `scripts/ensure_indexes.{py,js}` (or `schema/01_indexes.js`). It uses driver `createIndexes` with explicit names and runs as a deploy or seed step. B-tree, compound, TTL and 2dsphere indexes (and `vector-hnsw`) can be created before the bulk load. `vector-ivf` (and any product-quantization index) is created after the load, because `numLists` is sized from the document count (see vector-ensure-index).
- Seeds are idempotent by construction: use a deterministic `_id` (for example `f"order-{i:06d}"`) or `UpdateOne(filter, {"$set": doc}, upsert=True)` inside `bulk_write(ops, ordered=False)`, in batches of 500-1000. Never call `insert_many` with generated ids and label it idempotent.
- An identical `createIndexes` call (same name, same options in the same key order, defaults included) is a no-op; the same name with other options fails with 86 `IndexKeySpecsConflict`, and a second vector index on a path that already has one fails with 85 `IndexOptionsConflict` (managed service and documentdb-local agree; Learn documents neither). So the script sends each spec with a fixed key order and every value explicit (or compares against `listIndexes` before creating), and treats 85 and 86 as stop signals that are surfaced, never swallowed: drop or rename deliberately.
- Runtime code only verifies (`listIndexes`) and fails fast or warns. It never calls `createIndex` in query helpers, aggregation paths or workers.
- ODMs: Mongoose `mongoose.connect(..., { autoIndex: false })` + `await Model.syncIndexes(); // do not rely on autoIndex` in the script. Beanie: do not rely on `init_beanie` creating indexes in production. Call out the trap seen in the run: `autoIndex:false` + schema `index: true` + field missing from the script = the index never exists.
- **MCP fallback:** `create_index` is a management tool and is off by default (`ENABLE_MANAGEMENT_TOOLS=true`, see mcp-setup → Gated tools). If it errors, don't retry the payload or defer to "manual portal creation". Write the index into the ensure script with the driver and run it.
- Include 5-line PyMongo and Node.js driver `createIndexes` snippets.
- Verification: `listIndexes` shows every expected name, then `explain("executionStats")` for each worksheet row.
- Correct example (from draft 086):

```python
from pymongo import IndexModel, UpdateOne, ASCENDING

def bootstrap(db, docs, batch=500):
    coll = db.orders
    coll.create_indexes([
        IndexModel([("customerId", ASCENDING), ("orderedAt", -1)], name="orders_customer_date"),
    ])
    for i in range(0, len(docs), batch):
        coll.bulk_write(
            [UpdateOne({"_id": d["_id"]}, {"$set": d}, upsert=True) for d in docs[i:i+batch]],
            ordered=False,
        )
    names = {ix["name"] for ix in coll.list_indexes()}
    assert "orders_customer_date" in names, names
    plan = db.command("explain", {"find": "orders", "filter": {"customerId": "c-1"}},
                      verbosity="executionStats")
    # read the plan: for find it is at queryPlanner.winningPlan; for aggregate it sits at
    # stages[0].$cursor.queryPlanner.winningPlan (Learn how-to-read-explain-output describes the
    # stages array; the exact path was observed in the experiment's explains). Check that the
    # leaf scan uses the index: right after a bulk load an unindexed find can explain as FETCH
    # over a bitmap IXSCAN on _id_ instead of COLLSCAN, so a "COLLSCAN" string check passes it.
    assert "orders_customer_date" in str(plan["queryPlanner"]["winningPlan"]), "query is not using orders_customer_date"
```

`COLLSCAN` does appear on Azure DocumentDB: Learn's explain page lists `COLLSCAN`, `IXSCAN` and `FETCH` as the common `winningPlan.stage` values, and the experiment observed `winningPlan.stage: "COLLSCAN"` for both a find explain (`runs/01-anti-money-laundering-pattern-detector/20261124-200112`) and an aggregate explain (`runs/12-cross-border-payment-audit-trail/20261124-201744`) on the managed cluster. A string check for it is still not a reliable full-scan test (managed test, 2026-11-25; DECISIONS.md topic 10): whether `COLLSCAN` shows depends on the collection's vacuum state and the explain verbosity. Just after a bulk load an unindexed find explains as `FETCH` over a bitmap `IXSCAN` on `_id_` at the default, `queryPlanner` and `executionStats` verbosities, and top-level `totalDocsExamined` can understate a scan (a `LIMIT` root reported 1 document examined over a scan that examined 12,346). Read the scan stage's index name, and compare `totalDocsExamined` with `nReturned` on the `FETCH` or `COLLSCAN` stage that reports both, not on the top-level totals or on a bitmap `IXSCAN` leaf, which reports keys only; treat an `IXSCAN` on `_id_` for a filter that is not on `_id` as a full scan (inferred from the observed plans). No plan check right after a bulk load is reliable: until autovacuum has run, an indexed find can explain as `IXSCAN` with 1 document examined while the cursor runs a full primary-key scan (shown only by `allPlansExecution`), so do not time queries or judge plans right after a load. PyMongo's `Cursor.explain()` sends no verbosity and returns no `executionStats` on the service; send the `explain` command with `verbosity: "executionStats"`, as above. Walk the `stages[].$cursor` branch for aggregate explains. A `$search`/`cosmosSearch` pipeline on IVF explains as `FETCH` (with `cosmosSearchCustomParams`) over `IXSCAN` on the vector index, then `LIMIT` and `PROJECT`, with no `SORT` or `COLLSCAN`.

### `skills/indexing/index-query-to-index-worksheet.md` (new, Priority CRITICAL)

Run this after the app code is written:
1. List every `find`/`aggregate`/`update*`/`countDocuments` filter, sort and `$group._id`, by collection.
2. Derive an ESR shape for each row: one compound index per distinct prefix, and drop single-field indexes that are a prefix of it.
3. If the predicate is a fixed value (`status: "abandoned"`, `llmTags.tier: {$exists: true}`), add `partialFilterExpression` and make sure the query repeats the predicate. Use only the forms partial indexes accept (equality, `$exists: true`, `$gt/$gte/$lt/$lte`, `$type`, `$and`/`$or`/`$in`). `$exists: false` and "field is missing" predicates are not accepted, so model those as an explicit boolean or status field instead (for example `categorized: false`).
4. If the query groups or filters on a derived value (`$dateToString`, a lower-cased name), store the precomputed field (`day`, `normalized_name`) at write time and index that. Never index and then `$regex`.
5. Delete every declared index that no row uses.
6. Run `explain("executionStats")` for every row and require an IXSCAN on the intended index (an IXSCAN on `_id_` counts only for a query on `_id`) with no blocking SORT.

Worked example (the most common failure):

```javascript
// Declared up front:
db.carts.createIndex({ customerId: 1, updatedAt: 1, processedAt: 1 });
// Written later:
db.carts.find({ status: "open", updatedAt: { $lt: cutoff } }).sort({ updatedAt: 1 });
// explain: COLLSCAN + SORT — the query never supplies customerId, so the index prefix is broken.
// Fix: index the shape you wrote (equality first, then sort/range):
db.carts.createIndex({ status: 1, updatedAt: 1 }, { name: "idx_carts_status_updated" });
// Or, if only open carts are ever scanned, a smaller partial index the query must repeat:
db.carts.createIndex({ updatedAt: 1 },
  { name: "idx_open_carts_by_updated", partialFilterExpression: { status: "open" } });
// Then confirm: explain("executionStats") shows an IXSCAN on that index and no blocking SORT.
```

Output artefact: a `## Indexes` table in the README that maps each query to a named index.

### `skills/indexing/examples/` (new, optional; from draft 113)

Ship the snippets as ready-to-run files referenced from vector-ensure-index and index-ensure-script-lifecycle: `create_index.py`, `create_index.js`, and `index_example.json`, which holds the three vector payloads with demo and larger-dataset parameter sets from the vector-index-templates table.

### `skills/mcp-setup/SKILL.md`

After the `ENABLE_MANAGEMENT_TOOLS` note (lines 154-155), add a **"Gated tools: expected error and fallback"** subsection:

```markdown
### Gated tools: expected error and fallback

Generated applications must not depend on MCP management tools being enabled. Create indexes
from the app's seed/startup code (see `vector-search/vector-ensure-index` and
`indexing/index-ensure-script-lifecycle`) and use the MCP tools only to inspect.

Management tools (`create_index`, `drop_index`, `drop_collection`, `drop_database`,
`rename_collection`, `current_ops`) require `ENABLE_MANAGEMENT_TOOLS=true`. Write tools
(`insert_documents`, `update_documents`, `delete_documents`, `find_and_modify`) require
`ENABLE_WRITE_TOOLS=true`. The kit's `mcp.json` ships both as `"false"`.
When gated, the server returns exactly:

    Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true to opt in.
    Write tools are disabled by default. Set ENABLE_WRITE_TOOLS=true to opt in.

(On an authenticated HTTP deployment a caller without the role instead gets
`Caller is not authorized for '<role>' MCP tools.`; treat it the same way.)

Rule for agents: this error is a configuration state, not a transient failure. Do not retry.
1. Use `list_indexes` (read, on by default) to confirm the profile is reachable.
2. Attempt the gated tool once.
3. On the message above, switch to the driver in the project's seed/bootstrap script
   (`collection.create_indexes([...])` / `db.command({"createIndexes": ...})` / `Model.syncIndexes()`)
   and say so in the README. Only tell the user to flip the flag if they asked for
   MCP-managed index operations.
```

### `skills/query-optimizer/SKILL.md`

Line 65: after `create_index`, add "(requires `ENABLE_MANAGEMENT_TOOLS=true`; see mcp-setup → Gated tools)".

### `skills/query-optimizer/references/core-indexing-principles.md` (optional)

Its tier table lists `vector-hnsw` and `vector-ivf` with no parameters. Mirror the HNSW/IVF parameter rows from vector-index-templates, or link to that file.

### `skills/query-optimization/query-explain-plan.md`

Link to `indexing/index-query-to-index-worksheet` and `indexing/index-ensure-script-lifecycle`. Also link https://learn.microsoft.com/en-us/azure/documentdb/how-to-read-explain-output (the rule currently links only MongoDB's explain docs) and state that an aggregate explain's plan sits at `stages[].$cursor.queryPlanner.winningPlan`. Related kit text contradicted by Learn and by the experiment's explains: `scripts/perf-advisor.sh` lines 406-407 and `testing/scenarios/ecommerce-missing-index/SCENARIO.md` line 21 say DocumentDB "never emits a literal COLLSCAN stage"; it does, although whether it shows depends on the collection's vacuum state and the explain verbosity (see the explain note under index-ensure-script-lifecycle), so correct that sentence in the same PR.

### `skills/local-deployment/local-prod-parity.md`

Next to the `schema/01_indexes.js` example, link to `indexing/index-ensure-script-lifecycle` and `vector-search/vector-ensure-index`. Add one parity sentence: the `documentdb-local` image supports only `vector-ivf` and `vector-hnsw` (no `vector-diskann`, no `pq` compression; 2,000 dimensions uncompressed, 4,000 with `compression: "half"`), so an ensure script that defaults to `vector-diskann` on Azure needs `VECTOR_INDEX_KIND=vector-hnsw` locally (OSS `$vectorSearch` reference, https://documentdb.io/docs/reference/operators/aggregation/$vectorsearch/; engine `pg_documentdb/src/vector/vector_index_kind_impl.c`).

### `skills/full-text-search/fts-basic-search.md` (optional)

Cross-link to `vector-search/vector-search-response-shape` next to the existing `searchScore` guidance.

### `docs/SKILLS.md`

- `vector-search/` row (line 25): change the description to "`cosmosSearch` with DiskANN / HNSW / IVF (copy-paste templates), PQ, fp16, number[] storage, idempotent index creation from app code, response shape (score / no raw vectors / fallback flag)".
- `indexing/` row: add "query-to-index worksheet, ensure_indexes lifecycle".
- `mcp-setup/` row: add "gated tools and driver fallback".

### `CHANGELOG.md`

"vector-search: index templates for all kinds; Incorrect Atlas/MongoDB 7 create shapes (`createSearchIndexes`, `knnVector`, `knnBeta`, `type: 'vector'`); number[] storage rule and startup dimension probe; vector-ensure-index (idempotent create + verify from app code); server-side search rule; response-shape rule. indexing: query-to-index worksheet and ensure_indexes lifecycle. mcp-setup: gated tools, expected errors and driver fallback."

### Out of scope (kept so they are not lost)

- `CONTRIBUTING.md` still points at `skills/documentdb-best-practices/rules/`, which no longer exists. This belongs in a separate small PR.
- From K31: missing auth/rate limiting on LLM-backed endpoints (app hardening), ad-hoc multi-agent JSON shapes (sample-template concern), and four harness audit findings about an unrequested `/search` endpoint.
- Note for the experiment owner, not part of this PR: the run-14 audit marked a `createSearchIndexes` vector index and a `$search.knn` query as met, so the audit does not check the command surface.

## Evidence

- `runs/07-voice-of-customer-sentiment-hub/20261124-204049/`: `createSearchIndexes` used for the vector index, `CommandNotSupported` swallowed, no vector index created
- `runs/14-customer-complaint-classifier/20261124-201931/`: `createSearchIndexes` for the vector index plus a `$search.knn` query, which the audit marked as met; `/search` has no empty-query handling
- `runs/11-visual-similarity-search-image-embeddings/20261124-184225/`: `bson.Binary(..., subtype=0x09)` in `app/scripts/seed.py`; "expected an array type field"
- `runs/01-product-catalog-with-vector-search/20261124-175429/05-audit.json`: BSON Binary embeddings, `/search` ranks client-side, `numLists: 100` for 5 documents, no index verification
- `runs/15-financial-advisor-chatbot-rag/20261124-192021/events.jsonl`: two gated `create_index` calls (lines 66-69), `list_indexes` shows only `_id`, then client-side ranking with the embedding returned to the caller
- `runs/13-chronic-disease-risk-predictor/20261124-194916/doc-gaps.md`: `expected 1536 dimensions, not 3`; server-side search never exercised
- `runs/12-abandoned-cart-recovery-orchestration/20261124-184507/05-audit.json`: compound index prefix never supplied by the query; the sort cannot use it
- `runs/02-clinical-trial-matching-orchestration/20261124-193208/`: HNSW with DiskANN keys, then `find()` + cosine as the only query path
- `runs/04-earnings-call-rag-assistant/20261124-190247/`: `find()` + `np.dot` over the whole collection; the documented `vector-diskann` index is never queried
- `runs/20-provider-directory-semantic-search/20261124-200008/02-readiness.json`: cold `knnVector` answer; the shipped HNSW parameters came from Learn
- `runs/16-subscription-billing-engine/20261124-192251/05-audit.json`: `autoIndex:false` trap; index never created
- `runs/17-ai-survey-response-analyzer/20261124-205518/events.jsonl`: gate error, then "manual portal creation"
- `runs/17-rare-disease-literature-search/20261124-195633/05-audit.json`: no empty-query check; embedding call uncaught
- `runs/13-product-q-a-chatbot-rag/20261124-184527/doc-gaps.md`: no guidance on a citation/sources format for RAG
- `runs/11-correspondent-banking-risk-screener/20261124-201541/doc-gaps.md`: `$search` without `searchScore`; fallback not flagged to callers

## Resolved

- Vector index ranges, defaults and query knobs (was open question 1): settled from the Learn vector-search page's per-algorithm tabs: HNSW `m` 2-100 (default 16), `efConstruction` 4-1000 (default 64, at least `2*m`), `efSearch` default 40; IVF `numLists` = documentCount/1000 up to 1M documents (start at 1 for demos), `nProbes` default 1 and at most `numLists`; DiskANN `maxDegree` 20-2048 (default 32), `lBuild` 10-500 (default 50), `lSearch` 10-1000 (default 40) with `k` at most `lSearch`; HNSW and DiskANN need M30 or higher. Sources: https://learn.microsoft.com/en-us/azure/documentdb/vector-search; https://learn.microsoft.com/en-us/azure/documentdb/limitations (vector search section; release note 2025-07-15). Only the IVF-above-1M rule stays open (open question 1).
- Dimension limits (was part of open question 1): 2,000 without compression, 4,000 with `compression: "half"` on HNSW or IVF, 16,000 with product quantization on DiskANN; confirmed by the DocumentDB product owner on 2026-11-25, and the team reported an engine test on the same day: the engine rejects a half-precision HNSW index with 4,001 dimensions ("field cannot have more than 4000 dimensions for vector index") and accepts 4,000; the 8,000 figure on the select-algorithm quickstarts is wrong (it comes from `ai/includes/choosing-algorithm.md` in github.com/Azure-Samples/documentdb-samples). Sources: https://learn.microsoft.com/en-us/azure/documentdb/vector-search; https://learn.microsoft.com/en-us/azure/documentdb/half-precision; https://learn.microsoft.com/en-us/azure/documentdb/product-quantization; https://learn.microsoft.com/en-us/azure/documentdb/limitations; product owner answer 2026-11-25. The managed test (2026-11-25) confirmed every ceiling on the service and found `compression: "half"` rejected on DiskANN (DECISIONS.md topic 6).
- IVF build order (was open question 2): HNSW can be created on an empty collection; IVF `numLists` depends on the document count, so create or re-create it after loading; a product-quantization index should be created after the collection has data; Learn says a new index can return empty results for 2 to 3 minutes while it builds, which the managed test did not see on 5-document collections (complete results on the first query; large collections untested; ENGINE-TESTS.md, Managed service). Sources: https://learn.microsoft.com/en-us/azure/documentdb/vector-search (HNSW column); https://learn.microsoft.com/en-us/azure/documentdb/product-quantization (note); https://learn.microsoft.com/en-us/azure/documentdb/quickstart-nodejs-select-algorithm (Troubleshooting).
- Full-text search status and the `CommandNotSupported` error (was open question 3): full-text search is in preview, enabled per cluster self-serve (portal Settings > Features > Full-text search > Enable, or Azure CLI PATCH of `properties.previewFeatures` adding `FullTextSearch`, or Bicep/Terraform), and Learn says to wait ten minutes before creating a search index; `createSearchIndexes` on a cluster without the preview returns `CommandNotSupported`, code 115, "Search index creation is not supported yet" (observed; no Learn page documents the error). The activation window is now observed (managed test, 2026-11-25, one observation): `createSearchIndexes` returned 115 for about 90 s after enabling, then 67 `CannotCreateIndex` with the same message, and succeeded at about 210 s, so the rule retries on that message and treats ten minutes as an upper bound (DECISIONS.md topic 7). Sources: https://learn.microsoft.com/en-us/azure/documentdb/full-text-search-overview (2026-11-04, updated 2026-11-17); https://devblogs.microsoft.com/documentdb/?p=259; `runs/07-voice-of-customer-sentiment-hub/20261124-204049`.
- `listIndexes` key for vector options (was open question 4): corrected by the managed test (2026-11-25): the options are reported under `cosmosSearchOptions` only, with no `cosmosSearch` key, for HNSW, IVF and DiskANN indexes through both hosts, and options sent under a `cosmosSearch` key in `createIndexes` fail with 197. The Learn sample that shows `cosmosSearch` is wrong. Sources: ENGINE-TESTS.md, Managed service; DECISIONS.md topic 6; https://learn.microsoft.com/en-us/azure/documentdb/vector-search ("Get vector index definitions", the wrong sample).
- BSON Binary vectors (was open question 5): Learn requires an array of numbers and says a document whose vector has another type is not indexed and is silently absent from results; the engine stores and returns BSON binary subtype 9 intact and index-side search on it is a separate, untracked feature; the experiment saw binary vectors inserted but never returned and a binary query vector rejected with "expected an array type field". Sources: https://learn.microsoft.com/en-us/azure/documentdb/vector-search (DiskANN field table; IVF Important box); https://github.com/documentdb/documentdb/issues/109 (closed completed 2026-04-28); `runs/11-visual-similarity-search-image-embeddings/20261124-184225`.
- One vector index per path (was open question 6): current behaviour, "Indexing applies to only one vector per path. You can create only one index per vector path." Observed on the managed service: a second vector index on a path fails with 85 `IndexOptionsConflict` (ENGINE-TESTS.md, Managed service). Sources: https://learn.microsoft.com/en-us/azure/documentdb/vector-search (features list); https://learn.microsoft.com/en-us/azure/documentdb/limitations.
- Whole-plan `COLLSCAN` check (was open question 8): it works, provided the walker descends into `stages[].$cursor` for aggregate explains; Learn lists `COLLSCAN`, `IXSCAN` and `FETCH` as the common `winningPlan.stage` values and the experiment observed `COLLSCAN` for find and aggregate explains on the managed cluster. Qualified by the managed test (2026-11-25): whether `COLLSCAN` appears depends on the collection's vacuum state and the explain verbosity, and neither it nor top-level `totalDocsExamined` is a reliable full-scan check, so the rules read the scan stage's index name and compare documents examined with `nReturned` on the `FETCH` or `COLLSCAN` stage that reports both; a `cosmosSearch` pipeline on IVF explains as `FETCH` over `IXSCAN` on the vector index (DECISIONS.md topic 10). Sources: https://learn.microsoft.com/en-us/azure/documentdb/how-to-read-explain-output; https://learn.microsoft.com/en-us/azure/documentdb/how-to-index; `runs/01-anti-money-laundering-pattern-detector/20261124-200112`; `runs/12-cross-border-payment-audit-trail/20261124-201744`.
- Same-name index error and identical repeat (former open question 2, a maintainer item): now observed on the managed service, matching documentdb-local. A same-name index with other options fails with 86 `IndexKeySpecsConflict`, a second vector index on a path fails with 85 `IndexOptionsConflict`, and an identical `createIndexes` is a no-op only when the options are identical, key order and defaults included (reordered keys, or the `m`/`efConstruction` defaults left out, get 86). DECISIONS.md (topic 6, "Not an SME item, now observed") says filings may cite these codes, so the rules name them and the helper sends a fixed, fully explicit spec or checks `listIndexes` first. Sources: ENGINE-TESTS.md, Managed service; DECISIONS.md topic 6.

## Open questions

1. [needs SME confirmation] IVF above one million documents: the Learn vector-search IVF field table says `numLists = sqrt(documentCount)` above 1M, while the Important box under it says to use DiskANN instead. The filing follows the Important box (`documentCount/1000` up to 1M, DiskANN above). Confirm which rule the kit should state.
2. Maintainers: should the HTTP status mapping (400 for an empty query, 502 for an embedding failure) live in this kit, or should the response-shape rule keep only the score, no-vectors and fallback-flag parts and leave error mapping to sample templates?
3. Maintainers: land this as one PR, or split the indexing half (`skills/indexing/*`, `mcp-setup`, `query-optimizer`, `query-explain-plan`, `local-prod-parity`) into its own PR, as the reviewer allowed?

## Source drafts

- 113-vector-search-and-indexing-skills-lack-copy-paste-idempotent.md (templates lead; verification probe, `CREATE_INDEXES` guard, ORM caveat, `skills/indexing/examples/`, mcp-setup one-liner)
- 019-believes-vector-indexes-use-mongodb-atlas-community-syntax-k.md (Incorrect block and the SKILL.md "Not the API" bullet)
- 021-agent-kit-gap-vector-search-skill-shows-a-full-createindex-e.md (its separate HNSW and IVF rule files are merged into vector-index-templates)
- 039-believes-vector-indexes-queries-use-atlas-or-upstream-syntax.md
- 114-samples-fell-back-to-client-side-cosine-similarity-instead-o.md (vector-prefer-server-side-search)
- 097-vector-rag-samples-bypass-server-side-cosmossearch-index-nev.md (ensure_vector_index, number[] rule, knnBeta, canonical projection, PyMongo pipeline, chunk lineage, Hard rules)
- 086-seed-and-index-recipe-idempotent-seed-bootstrap-index-lifecy.md (bootstrap recipe, gated-tools subsection, dimension pre-check)
- 099-indexes-do-not-match-the-sample-s-actual-query-workload-esr-.md (worksheet, ensure_indexes lifecycle)
- 094-http-and-search-rag-response-contract-for-samples-input-vali.md (vector-search-response-shape)

## Merged from

- K05: vector-search skill: number[] storage rule and copy-paste cosmosSearch index templates (vector-ivf, vector-hnsw, vector-diskann), with $search as the primary query path
- K06: vector-search and indexing skills: create and verify indexes from application code (ensure_vector_index, ensure_indexes lifecycle)
- K31: vector-search: add a response-shape rule (return the score, never raw vectors)
