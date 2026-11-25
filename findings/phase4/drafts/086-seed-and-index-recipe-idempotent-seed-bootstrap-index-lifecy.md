---
title: "Add seed-and-index bootstrap recipe, ensure_vector_index(), IVF numLists defaults, and a gated-MCP-tool fallback rule"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 14
findings: 14
bucket: kit-doc-gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Add seed-and-index bootstrap recipe, `ensure_vector_index()`, IVF `numLists` defaults, and a gated-MCP-tool fallback rule

## What happens today

We ran 100 Azure DocumentDB sample prompts through gpt-5-mini with this kit's 17 skills plus the DocumentDB MCP server, using the kit's own `mcp.json` (which ships `ENABLE_WRITE_TOOLS` and `ENABLE_MANAGEMENT_TOOLS` as `"false"`). Four things went wrong repeatedly, all in the same place: the seed/bootstrap step.

1. **Gated MCP tools with no fallback rule.** 36 of 100 samples called `create_index` or `insert_documents` and got `Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true to opt in.` (58 occurrences) or `Write tools are disabled by default. Set ENABLE_WRITE_TOOLS=true to opt in.` (19). 25 runs hit the error two to four times, so the agent retried before giving up. The README (lines 166-169) and `mcp-setup/SKILL.md` (lines 154-155) do mention the flags, but the skills an agent is actually reading when it creates an index (`indexing`, `vector-search`, `full-text-search`, and `query-optimizer/SKILL.md` line 65, which lists `create_index` as "only after user approval") never name the capability gate, the error text, or the driver fallback.
2. **No idempotent seed/bootstrap pattern.** The audit requirement "seed script loads sample data, creates the index, and can be run twice without duplicating data" scored below `met` in 43 of 115 audits (39 samples). Index creation ended up inside the aggregation code path (08-interest-rate-scenario-modeler), inside `run_attribution` instead of the seed (16-multi-touch-attribution-model), left to Mongoose `autoIndex` (20-open-banking-api-cache-layer), or split into a second manual step (18-sanctions-list-screening-agent). A seed that comments itself "idempotent" generated random order ids and duplicated on re-run (19-cross-sell-recommendation-beanie). The only seeding rule in the kit is `local-deployment/local-sample-data-management.md`, which is about the Docker image's `INIT_DATA_PATH`.
3. **Dimension mismatch not caught before `createIndex`.** Three samples (01-patient-record-summarizer-rag, 13-chronic-disease-risk-predictor, 18-sanctions-list-screening-agent) hit `expected 1536 dimensions, not 3` (`code: 2, codeName: BadValue`) because placeholder embeddings were already in the collection. `vector-create-diskann-index.md` says `dimensions` and `similarity` "must match" the embeddings but gives no check. In 13-chronic the agent moved on and the server-side `$search`/`cosmosSearch` path was never exercised.
4. **No `numLists` default for small data.** `vector-choose-index-type.md` shows `numLists: 100` only as the *Incorrect* example and never shows a correct value; 01-product-catalog-with-vector-search's readiness stage flagged this gap explicitly, and the builder used 100 for a ~200-document demo. Learn's vector-search page has the guidance (`documentCount/1000`, and `numLists: 1` for a small demo) but the kit does not carry it.

## Why it matters

The 14 findings behind this PR span 14 distinct samples, and the broader seed-and-index requirement failed in 39. The net effect is that the thing the samples are supposed to demonstrate (server-side `cosmosSearch` kNN via `$search`, and text search) was silently replaced by in-app cosine similarity or `$regex` in several builds, because the index was never created or verified. This is a kit-level gap, not a model prior: the agents had nowhere in the kit to copy a bootstrap pattern from.

## Proposed change (4 files, one PR)

### a) `skills/mcp-setup/SKILL.md`: new subsection after the "Notes" list (line ~160)

```markdown
### Gated tools: expected error and fallback

`create_index`, `drop_index`, `drop_collection`, `drop_database`, `rename_collection`, `current_ops`
require `ENABLE_MANAGEMENT_TOOLS=true`; `insert_documents`, `update_documents`, `delete_documents`,
`find_and_modify` require `ENABLE_WRITE_TOOLS=true`. The kit's `mcp.json` ships both as `"false"`.
When gated, the server returns exactly:

    Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true to opt in.
    Write tools are disabled by default. Set ENABLE_WRITE_TOOLS=true to opt in.

(On an authenticated HTTP deployment a caller without the role instead gets
`Caller is not authorized for '<role>' MCP tools.`; treat it the same way.)

Rule for agents: this error is a configuration state, not a transient failure. Do not retry.
1. Use `list_indexes` (read, on by default) to confirm the profile is reachable.
2. Attempt the gated tool once.
3. On the message above, switch to the driver in the project's seed/bootstrap script
   (`collection.create_indexes([...])` / `Model.syncIndexes()`) and say so in the README.
   Only tell the user to flip the flag if they asked for MCP-managed index operations.
```

Add one sentence to `skills/query-optimizer/SKILL.md` line 65: "`create_index` (requires `ENABLE_MANAGEMENT_TOOLS=true`; see mcp-setup -> Gated tools)".

### b) New `skills/indexing/index-bootstrap-idempotent.md`, linked from `skills/indexing/SKILL.md`

Rule text (abridged; full Incorrect/Correct format as other rules):

- Seeds are idempotent by construction: deterministic `_id` (e.g. `f"order-{i:06d}"`) or `UpdateOne(filter, {"$set": doc}, upsert=True)` inside `bulk_write(ops, ordered=False)` in batches of 500-1000. Never `insert_many` with generated ids and call it idempotent.
- Indexes are created in the seed/bootstrap script, never in a query path and never via Mongoose `autoIndex`. Name every index explicitly.
- Ordering: creating indexes before the bulk load is fine for B-tree/compound/TTL/2dsphere indexes and for `vector-hnsw` (Learn: HNSW "can be created on an empty table"); Learn's own IVF and HNSW examples create the vector index on an empty collection and insert afterwards. For `vector-ivf`, `numLists` depends on the document count, so either create it after the load (count known) or start with `numLists: 1` for a demo and recreate it with a tuned value once the collection has grown. Say which in a comment.
- Idempotent `createIndexes`: an identical name+spec is a no-op (`note: "all indexes already exist"`); a same-name/different-options call raises `IndexOptionsConflict` (code 85) and must fail loudly, not be swallowed. Maintainers: please confirm the exact code DocumentDB returns before merging.
- Verify with `list_indexes()` / `getIndexes()` and gate with explain:

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
    # check the whole plan: DocumentDB's explain layout differs from MongoDB's
    assert "COLLSCAN" not in str(plan), "query is not using an index"
```

Mongoose one-liner for the Correct section: `await Model.syncIndexes(); // do not rely on autoIndex`.

### c) New `skills/vector-search/vector-ensure-index.md`, linked from `skills/vector-search/SKILL.md`

```python
def ensure_vector_index(coll, field, dims, kind="vector-diskann", name=None, **opts):
    """Create the cosmosSearch index only if existing embeddings match `dims`."""
    bad = coll.count_documents({field: {"$exists": True}, "$expr": {"$or": [
        {"$not": [{"$isArray": f"${field}"}]},
        {"$ne": [{"$size": {"$cond": [{"$isArray": f"${field}"}, f"${field}", []]}}, dims]},
    ]}})
    if bad:
        raise SystemExit(
            f"{bad} documents have a {field} that is not a number[] of length {dims}. "
            f"Re-embed them or seed into a fresh collection; the server would reject the index "
            f"with 'expected {dims} dimensions, not N' (code 2 BadValue).")
    # Azure DocumentDB allows only one vector index per path: match on the key, not the name.
    for ix in coll.list_indexes():
        if ix["key"].get(field) == "cosmosSearch":
            return ix["name"]
    name = name or f"{coll.name}_{field}_{kind.replace('vector-', '')}"
    coll.create_index([(field, "cosmosSearch")], name=name,
                      cosmosSearchOptions={"kind": kind, "dimensions": dims, "similarity": "COS", **opts})
    return name
```

Rule bullets: vectors are `number[]` (BSON binary vectors are not indexed, and nonindexed documents are not returned by vector search); only one vector index per path, so changing `dimensions`/`kind` means drop and recreate; store `embeddingModel` and `embeddingDims` on the document (ties to `vector-normalize-embeddings`); read `dims` from one `EMBEDDING_DIMS` env var used by both the embedder and this function.

### d) `skills/vector-search/vector-choose-index-type.md`: add after the table

```markdown
### `numLists` for `vector-ivf`

| Documents | `numLists` |
|---|---|
| new scenario / small demo | `1` (brute force: most accurate, slowest), then tune |
| up to 1M | `documentCount / 1000` (minimum 1) |
| above 1M | switch to `vector-diskann`; if you must stay on IVF, `sqrt(documentCount)` |

Compute it, don't guess it: `n = coll.count_documents({}); num_lists = max(1, n // 1000)`.
`nProbes` at query time defaults to 1 and cannot exceed `numLists`.
Re-tune (drop and recreate the index) as the collection grows.
```

Source: https://learn.microsoft.com/en-us/azure/documentdb/vector-search (IVF tab).

## Evidence (run folders from the experiment; no connection strings)

- `runs/13-chronic-disease-risk-predictor/20261124-194916/doc-gaps.md` and `events.jsonl` line ~145: `expected 1536 dimensions, not 3`, three gate errors, agent proceeds without server-side vector search.
- `runs/04-natural-language-product-search/20261124-183232/05-audit.json`: vector index requirement `not_met` ("no code in the repository executes index creation"), `$search` and kNN requirements `partly_met`, seed requirement `partly_met`.
- `runs/01-anti-money-laundering-pattern-detector/20261124-200112/doc-gaps.md`: gate error, PyMongo fallback, asks for the opt-in note and expected error text.
- `runs/19-cross-sell-recommendation-beanie/20261125-055705/doc-gaps.md`: seed claims idempotency but random ids duplicate on re-run; no index JSON applied.
- `runs/01-product-catalog-with-vector-search/20261124-175429/02-readiness.json`: information gap "no conservative default hyperparameters (nlist...) for a small demo dataset".

Other samples in this set: 04-earnings-call-rag-assistant, 08-interest-rate-scenario-modeler, 13-household-grouping-linkage, 14-dynamic-pricing-engine, 16-multi-touch-attribution-model, 18-sanctions-list-screening-agent, 19-proactive-outreach-orchestration, 20-open-banking-api-cache-layer, 20-store-locator-with-geospatial-search.

## Verification

### 1. Already covered? partially_covered

- Kit `mcp.json` sets `"ENABLE_WRITE_TOOLS": "false"` and `"ENABLE_MANAGEMENT_TOOLS": "false"`. `README.md` lines 168-169 and `skills/mcp-setup/SKILL.md` lines 154-155 say "To allow write or management tools, add `ENABLE_WRITE_TOOLS: true` and/or `ENABLE_MANAGEMENT_TOOLS: true` to `env`." No skill quotes the error text or gives a detect-and-fall-back rule; `skills/query-optimizer/SKILL.md` line 65 lists `create_index` as "(only after user approval)" with no mention of the gate.
- No kit file covers idempotent seeding, upsert bulk writes, `syncIndexes`/`autoIndex`, or index-before/after-load (grep of `skills/` and `knowledge-base/` for idempot/upsert/bulkWrite/syncIndexes/autoIndex hits only `storage-disk-hydration-sequencing.md` (retry advice) and `local-sample-data-management.md` (Docker init data)).
- No dimension-validation helper; `vector-create-diskann-index.md` line 7 only says dimensions "must match".
- `vector-choose-index-type.md` line 22 shows `numLists: 100` only in the Incorrect example; no correct value. Learn (https://learn.microsoft.com/en-us/azure/documentdb/vector-search, IVF tab) does cover it: "Set `numLists` to `documentCount/1000` for up to 1 million documents" and "If you're ... creating a small demo, you can start with `numLists` set to 1". So item (d) is covered on Learn but not in the kit where the agent looked.

### 2. Premise true? confirmed (with corrections applied)

- Error strings verified verbatim in `documentdb-mcp/src/security/authorization.ts` lines 47 and 50. Tool tiers verified in `src/tools/*.ts` (`requiredRole`): management = create_index, drop_index, drop_collection, drop_database, rename_collection, current_ops; write = insert_documents, update_documents, delete_documents, find_and_modify; read = list_indexes, explain_operation, etc. The draft's `drop_*`/`update_*` shorthand was expanded to the exact tool names; the HTTP-mode `Caller is not authorized` error was added from the same file.
- Corrected: the draft's `numLists` table (`max(4, N // 1000)`, "a 200-doc demo gets 4") contradicted Learn, which recommends `numLists: 1` for a small demo, `documentCount/1000` up to 1M, and DiskANN above 1M. Table rewritten to match Learn.
- Corrected: the draft said `vector-ivf` must be created after the load. Learn does not require that, and its own IVF example creates the index on an empty collection before `insertMany`. Rule rewritten as "after load, or start with numLists 1 and recreate when tuned".
- Corrected: Learn's Features and limitations section says "You can create only one index per vector path", so `ensure_vector_index()` now checks for an existing `cosmosSearch` key on the path instead of matching by name. The function also got an `$isArray` guard so `$size` does not error on non-array values.
- Corrected: the explain check now looks for COLLSCAN in the whole plan instead of only `queryPlanner.winningPlan`, because DocumentDB's explain output is laid out differently from MongoDB's.
- Confirmed: vectors must be `number[]` to be indexed (Learn vector-search, DiskANN field table and IVF note). HNSW "can be created on an empty table" (Learn comparison table). `IndexOptionsConflict` code 85 stays flagged for maintainer confirmation.

### 3. Maintainer skeptic: confirmed

The PR names exact files and line anchors in Azure/documentdb-agent-kit, adds rules in the kit's existing Incorrect/Correct format, and each item is specific to DocumentDB (MCP capability gates in this kit's shipped `mcp.json`, `cosmosSearch` dimension and one-index-per-path rules, IVF `numLists`). It belongs in the kit, not documentdb-mcp: the server's behavior and error text are correct and documented in `docs/permission-model.md`; what's missing is agent guidance. I would accept it, possibly split into two PRs (MCP gate + bootstrap, vector helpers).

## Finding ids

F0021, F0576, F0646, F0131, F1282, F2209, F2231, F2376, F2735, F3130, F3342, F3446, F3244, F3518
