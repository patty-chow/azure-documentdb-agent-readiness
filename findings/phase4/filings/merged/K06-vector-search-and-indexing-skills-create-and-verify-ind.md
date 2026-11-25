---
id: K06
title: "vector-search and indexing skills: create and verify indexes from application code (ensure_vector_index, ensure_indexes lifecycle)"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P1
sample_count: 55
member_drafts:
  - 097-vector-rag-samples-bypass-server-side-cosmossearch-index-nev.md
  - 086-seed-and-index-recipe-idempotent-seed-bootstrap-index-lifecy.md
  - 099-indexes-do-not-match-the-sample-s-actual-query-workload-esr-.md
open_questions: 6
---

# vector-search and indexing skills: create and verify indexes from application code (ensure_vector_index, ensure_indexes lifecycle)

## What happens today

We had gpt-5-mini build 100 Azure DocumentDB sample apps. It used this kit's skills plus the DocumentDB MCP server, configured with the kit's own `mcp.json`, which ships `ENABLE_MANAGEMENT_TOOLS` and `ENABLE_WRITE_TOOLS` as `"false"`. The agents loaded `documentdb-vector-search` and `documentdb-indexing` (this shows in `events.jsonl`), but they still failed at the step those skills don't cover: **creating and verifying indexes from the app's own code.**

1. **The gated MCP tool had no fallback.** Agents called `create_index` and got `Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true to opt in.` A recount of `events.jsonl` across all run folders finds this management-gate error in 32 of the 100 samples; 36 hit it or the matching write-tools gate (`insert_documents` etc.). Many retried the call two to four times. Some then wrote "create the index manually in the portal". None fell back to a driver `createIndexes`. The flag appears in `mcp-setup/SKILL.md` (lines 154-155), but no skill an agent reads while creating an index names the gate, the error text or the fallback. `query-optimizer/SKILL.md` line 65 lists `create_index` with no mention of the gate.
2. **Vector search silently degraded.** With no `cosmosSearch` index, `listIndexes` showed only `_id`, and retrieval became `find({})` plus cosine similarity in Python or JS. Some apps returned the 1536-float arrays in API responses. In three samples, placeholder embeddings already in the collection made `createIndex` fail with `expected 1536 dimensions, not 3` (code 2, BadValue), and the agent moved on. Other mistakes: index key `{ cosmosSearch: "cosmosSearch" }`, which fails with `Similarity index not found`; `vector-ivf` with `numLists: 100` on a 5-document demo; HNSW created with no `m`/`efConstruction` chosen (valid, since defaults apply, but never decided or recorded).
3. **Seeds were not idempotent and indexes were created in the wrong place.** Agents created indexes in query helpers, in an aggregation path or after bulk upserts. Some relied on Mongoose `autoIndex`. One combined `autoIndex:false`, a schema `index: true` and a field missing from `create_indexes.js`, so the index was never created. Default index names, no manifest. A seed that called itself idempotent generated random ids and duplicated its data on re-run.
4. **Declared indexes did not match the queries.** Agents declared indexes from the cookbook up front, wrote the queries afterwards and never reconciled the two. Examples: single-field indexes where queries filter on two fields; a compound index whose equality prefix the query never supplies, so the sort can't use it; indexed fields the queries never touch; filter fields with no index; a `$facet` pipeline that `explain` showed as COLLSCAN.

The kit already covers index shapes (ESR, cookbook, partial indexes, DiskANN parameters) and `local-prod-parity.md` has a `schema/01_indexes.js` example. Nothing links these into an app-side create-verify lifecycle.

## Why it matters

**55 of the 100 samples** show at least one of these defects (107 findings). The member drafts counted 26, 14 and 29 samples; the groups overlap. All counts come from one run of the experiment and may shift on a re-run. The samples are meant to be copied, and these ones demonstrate client-side cosine instead of server-side `cosmosSearch`, plus indexes that don't serve their own queries.

## Proposed change (one PR)

**1. New `skills/vector-search/vector-ensure-index.md`.** Rule: create the vector index in seed/startup code with the driver, idempotently, and verify it. Don't depend on the MCP tool. Call it from the seed script and, cheaply, at app startup. If the index is missing at query time, fail with an explicit error; never fall back to scanning the collection for retrieval. Correct example:

```python
import os

def _opts(ix):
    return ix.get("cosmosSearch") or ix.get("cosmosSearchOptions") or {}

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
        opts["numLists"] = int(os.getenv("IVF_NUM_LISTS", max(1, c.estimated_document_count() // 1000)))
    elif kind == "vector-hnsw":
        m = int(os.getenv("HNSW_M", 16))
        opts.update(m=m, efConstruction=max(2 * m, int(os.getenv("HNSW_EF_CONSTRUCTION", 64))))
    else:
        opts.update(maxDegree=int(os.getenv("DISKANN_MAX_DEGREE", 32)), lBuild=int(os.getenv("DISKANN_L_BUILD", 50)))
    name = name or f"{coll}_{field}_{kind.replace('vector-', '')}"
    db.command({"createIndexes": coll, "indexes": [
        {"key": {field: "cosmosSearch"}, "name": name, "cosmosSearchOptions": opts}]})
    assert name in {ix["name"] for ix in c.list_indexes()}, f"{name} not listed after createIndexes"
    return name
```

Add a short Node equivalent (`db.command({ createIndexes, indexes })` + `collection.indexes()`). Also add these bullets: the key is `{ <field>: "cosmosSearch" }`; vectors must be `number[]`, and storage and query templates are covered in the companion vector storage-plus-templates PR; use one `EMBEDDING_DIMS` value for both the embedder and this function; only one vector index per path, so changing `dimensions` or `kind` means drop and recreate [needs SME confirmation, see open question 4]; the MCP tool is fine for interactive work once `ENABLE_MANAGEMENT_TOOLS=true`, but a repo must not depend on it.

The companion storage-plus-templates PR (per the reviewer's merge plan) carries the rest of draft 097, so it is not repeated here: the new `vector-store-number-array.md` rule (number[] only, never BSON Binary; startup dimension probe; chunk lineage `sourceId`/`chunkIndex` linked to `vector-normalize-embeddings`), and the `vector-knn-query.md` extensions (`knnBeta` in the Incorrect block, a `find({})` + client-side cosine Incorrect block, a canonical inclusion projection with `{ $meta: "searchScore" }` that leaves the embedding out, and a PyMongo version of the pipeline). Draft 097's optional `CONTRIBUTING.md` fix (it still points at `skills/documentdb-best-practices/rules/`) is a separate small PR.

**2. `skills/vector-search/vector-choose-index-type.md`: add after the table.** [needs SME confirmation: HNSW and IVF limits, see open question 1]

```markdown
### Sizing at creation time
| `vector-ivf` documents | `numLists` |
|---|---|
| small demo / new scenario | `1` (brute force), then tune |
| up to 1M | `documentCount / 1000` (minimum 1) |
| above 1M | use `vector-diskann` |

`nProbes` defaults to 1 and cannot exceed `numLists`. HNSW: `m` default 16 (2-100), `efConstruction` default 64 (4-1000, at least `2*m`), query `efSearch` default 40; defaults are valid, but choose and record values deliberately. Compute it, don't guess it: `n = coll.count_documents({}); num_lists = max(1, n // 1000)`. Re-tune by drop and recreate.
```

**3. `skills/vector-search/SKILL.md`:** list `vector-ensure-index` under Rules. Add the hard rule "create and verify the vector index from your own seed/startup code; never fall back to client-side cosine over `find({})`". Add "idempotent index creation from application code" to the `description`.

**4. New `skills/indexing/index-ensure-script-lifecycle.md`** (HIGH):
- Every app ships one version-controlled, idempotent `scripts/ensure_indexes.{py,js}` (or `schema/01_indexes.js`). It uses driver `createIndexes` with explicit names and runs as a deploy or seed step. B-tree, compound, TTL and 2dsphere indexes can go before the bulk load (see open question 2 for IVF).
- Seeds use deterministic `_id`s or `UpdateOne(..., upsert=True)` in `bulk_write(ordered=False)` batches of 500-1000. Never `insert_many` with random ids.
- A same-name call with different options must fail loudly, never be swallowed.
- Runtime code only verifies (`listIndexes`) and never calls `createIndex` in query helpers. Mongoose: `autoIndex: false` + `await Model.syncIndexes()` in the script; Beanie: don't rely on `init_beanie`. Call out the `autoIndex:false` + schema `index: true` + missing-from-script trap.
- Include 5-line PyMongo and Node driver `createIndexes` snippets, and the Mongoose Correct line `await Model.syncIndexes(); // do not rely on autoIndex`.
- Include the `bootstrap()` example from draft 086 (`create_indexes` → upsert batches → assert names → `explain` with no COLLSCAN anywhere in the plan).

**5. New `skills/indexing/index-query-to-index-worksheet.md`** (CRITICAL). Run it after the app code is written:
1. List every `find`/`aggregate`/`update*`/`countDocuments` filter, sort and `$group._id` by collection.
2. Derive an ESR shape per row and drop prefix-redundant single-field indexes.
3. Add `partialFilterExpression` only with accepted forms (equality, `$exists: true`, comparisons, `$type`, `$and`/`$or`/`$in`), never `$exists: false`; model "field is missing" as an explicit boolean or status field instead. The query must repeat the partial predicate.
4. Store derived keys (day, normalized name) at write time and index those; never index and then `$regex`.
5. Delete unused indexes.
6. Require IXSCAN and no blocking SORT in `explain("executionStats")`.

Include the carts example from draft 099 (`{customerId, updatedAt, processedAt}` → `{status:1, updatedAt:1}` or a partial index on `status: "open"`). Output: a `## Indexes` table in the README mapping each query to a named index.

**6. Wiring.**
- `skills/indexing/SKILL.md`: add both rules and the sentence "Index design is not finished until the worksheet has been run against the final code."
- Link the new rules from `query-optimization/query-explain-plan.md` and `local-deployment/local-prod-parity.md`.
- `skills/mcp-setup/SKILL.md`: add a "Gated tools: expected error and fallback" subsection. It lists the management tools (`create_index`, `drop_index`, `drop_collection`, `drop_database`, `rename_collection`, `current_ops`) and the write tools (`insert_documents`, `update_documents`, `delete_documents`, `find_and_modify`), quotes both error strings verbatim, and notes that on an authenticated HTTP deployment a caller without the role gets `Caller is not authorized for '<role>' MCP tools.` instead. Rule: this is a configuration state, not a transient failure. Confirm the profile with `list_indexes`, attempt the gated tool once, then use the driver in the seed script and say so in the README. Tell the user to flip the flag only if they asked for MCP-managed index operations.
- `skills/query-optimizer/SKILL.md` line 65: add "(requires `ENABLE_MANAGEMENT_TOOLS=true`; see mcp-setup → Gated tools)".
- `docs/SKILLS.md`: update the rows.
- `CHANGELOG.md`: add an entry.

## Evidence

- `runs/15-financial-advisor-chatbot-rag/20261124-192021/events.jsonl` (lines 66-69: two gated `create_index` calls; `list_indexes` shows only `_id`)
- `runs/13-chronic-disease-risk-predictor/20261124-194916/doc-gaps.md` (`expected 1536 dimensions, not 3`; server-side search never exercised)
- `runs/01-product-catalog-with-vector-search/20261124-175429/05-audit.json` (`numLists: 100` for 5 documents; no index verification)
- `runs/12-abandoned-cart-recovery-orchestration/20261124-184507/05-audit.json` (compound index prefix never supplied)
- `runs/16-subscription-billing-engine/20261124-192251/05-audit.json` (`autoIndex:false` trap; index never created)
- `runs/17-ai-survey-response-analyzer/20261124-205518/events.jsonl` (gate error → "manual portal creation")

## Open questions

1. [needs SME confirmation] HNSW and IVF limits and defaults (`m` 2-100/16, `efConstruction` 4-1000/64 and ≥ 2·m, `efSearch` 40, `numLists` = n/1000, `nProbes` ≤ `numLists`), and whether DiskANN is the only recommendation above 1M documents. Draft 086 also suggested `sqrt(n)` for IVF above 1M; draft 097 says use DiskANN instead.
2. [needs SME confirmation] IVF build order. Draft 097 says to build IVF after loading data, because `numLists` depends on the document count. Draft 086 says Learn's own examples create the index on an empty collection. Which should the kit recommend?
3. [needs SME confirmation] Does `listIndexes` report vector options under `cosmosSearch`, `cosmosSearchOptions` or both? The helper reads both.
4. [needs SME confirmation] Is "only one vector index per path" current behaviour? The helper relies on it.
5. [needs SME confirmation] What error does DocumentDB return for a same-name index with different options (`IndexOptionsConflict`, code 85?), and is an identical `createIndexes` call a no-op?
6. [needs SME confirmation] Does checking that `explain` contains no `COLLSCAN` anywhere in the plan work reliably with DocumentDB's explain layout?

## Source drafts

- 097-vector-rag-samples-bypass-server-side-cosmossearch-index-nev.md
- 086-seed-and-index-recipe-idempotent-seed-bootstrap-index-lifecy.md
- 099-indexes-do-not-match-the-sample-s-actual-query-workload-esr-.md
