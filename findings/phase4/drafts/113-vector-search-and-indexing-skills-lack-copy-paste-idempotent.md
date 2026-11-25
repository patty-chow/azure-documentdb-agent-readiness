---
title: "Add copy-paste vector index templates (IVF/HNSW/DiskANN) and an idempotent driver-side createIndexes + verification pattern"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 14
findings: 16
bucket: mcp-server
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Add copy-paste vector index templates (IVF / HNSW / DiskANN) and an idempotent driver-side `createIndexes` + verification pattern

## What happens today

`skills/vector-search/` explains *which* index to pick (`vector-choose-index-type.md`) and shows one mongosh `createIndex` example for DiskANN (`vector-create-diskann-index.md`). IVF appears only in an "Incorrect" example, and the HNSW build keys (`m`, `efConstruction`) and query keys (`efSearch`, `nProbes`) appear nowhere in the kit. There is no side-by-side minimal payload for all three `cosmosSearch` kinds, no placeholder that ties `dimensions` to the embedding model, and no Python / Node.js code that creates the index from application code. `skills/indexing/` covers index *shape* but has no "create the index idempotently from the app and verify it" rule. `skills/mcp-setup/SKILL.md` (lines 154-155) notes that management tools are off unless `ENABLE_MANAGEMENT_TOOLS=true`, but nothing tells a builder what to do when they are off.

## Why it matters

In a 100-sample build experiment (gpt-5-mini + this kit + the DocumentDB MCP server), **32 runs called the MCP `documentdb_create_index` tool and all 32 got "Management tools are disabled by default"**. With no documented driver-side fallback, builders improvised. Across the 14 samples where this surfaced as an audit finding:

- `11-correspondent-banking-risk-screener`: `db.py` put Atlas-style `path` inside `cosmosSearchOptions`, then tried `createSearchIndexes` (server: `CommandNotSupported: Search index creation is not supported yet`), then hit `IndexOptionsConflict`. Vector queries fell back to an app-level metadata search.
- `02-clinical-trial-matching-orchestration`: requested `kind: "vector-hnsw"` with DiskANN tunables (`maxDegree`, `lBuild`) instead of `m` / `efConstruction`; no index ever created; seed script not idempotent for the index.
- `12-invoice-matching-reconciliation`: computed embeddings but never created a vector index; the "dimensions match the model" requirement could only be asserted from a `.env` default.
- `12-cross-border-payment-audit-trail`: relied on a Mongoose schema `index()` declaration that was never applied; filter queries showed COLLSCAN in `explain()`.
- `19-cross-sell-recommendation-beanie`, `19-proactive-outreach-orchestration`, `10-drug-formulary-semantic-search`, `15-digital-onboarding-orchestration`: index creation left as a manual README step; builders reported they could not find a ready-to-run `createIndexes` snippet in the kit.

Several runs also hit the server error `Similarity index was not found for a vector similarity search query` at query time, which is what a missing vector index actually produces.

The audits filed these against the MCP server (`tool_unavailable`), but the durable fix is in the kit: a generated sample must be correct whether or not MCP management tools are enabled.

## Proposed change

### 1. New `skills/vector-search/vector-index-templates.md` (register in `SKILL.md` rule list)

Three minimal `createIndexes` command documents, same field (`embedding`), differing only in `cosmosSearchOptions` (these mirror the templates on https://learn.microsoft.com/en-us/azure/documentdb/vector-search). `EMBEDDING_DIM` is the single source of truth and must come from the same config that selects the embedding model.

```json
{ "createIndexes": "<collection>", "indexes": [{
  "name": "embedding_vector_ivf", "key": { "embedding": "cosmosSearch" },
  "cosmosSearchOptions": { "kind": "vector-ivf", "dimensions": "<EMBEDDING_DIM>", "similarity": "COS", "numLists": 1 } }] }
```
```json
{ "createIndexes": "<collection>", "indexes": [{
  "name": "embedding_vector_hnsw", "key": { "embedding": "cosmosSearch" },
  "cosmosSearchOptions": { "kind": "vector-hnsw", "dimensions": "<EMBEDDING_DIM>", "similarity": "COS", "m": 16, "efConstruction": 64 } }] }
```
```json
{ "createIndexes": "<collection>", "indexes": [{
  "name": "embedding_vector_diskann", "key": { "embedding": "cosmosSearch" },
  "cosmosSearchOptions": { "kind": "vector-diskann", "dimensions": "<EMBEDDING_DIM>", "similarity": "COS", "maxDegree": 32, "lBuild": 50 } }] }
```

Tunables table (values and ranges from the Learn vector-search page):

| kind | tier | build-time keys (range, default) | query-time key in `$search.cosmosSearch` | demo | larger datasets |
|---|---|---|---|---|---|
| `vector-ivf` | M10+ (under ~10k vectors) | `numLists` | `nProbes` (default 1, must be ≤ `numLists`) | `numLists: 1` (brute force, most accurate) | `numLists = documentCount/1000` up to 1M docs; above 1M use DiskANN |
| `vector-hnsw` | M30+ (up to ~50k vectors) | `m` (2-100, default 16), `efConstruction` (4-1000, default 64, must be ≥ 2*m) | `efSearch` (default 40) | defaults | raise `m` / `efConstruction` / `efSearch` for recall; large HNSW builds can exhaust memory, prefer DiskANN |
| `vector-diskann` | M30+ (500k+ vectors) | `maxDegree` (20-2048, default 32), `lBuild` (10-500, default 50) | `lSearch` (10-1000, default 40, must be ≥ `k`) | defaults | raise `maxDegree` / `lBuild` / `lSearch` for recall |

Plus a short "common mistakes" list taken from the runs and the Learn page:
- `path` belongs in the `$search.cosmosSearch` query, not in `cosmosSearchOptions`.
- `createSearchIndexes` / Atlas `$vectorSearch` are not supported; use `createIndexes` with a `cosmosSearch` key.
- DiskANN keys (`maxDegree`, `lBuild`) on an HNSW index, or HNSW keys on DiskANN, are wrong; use the template for the kind you chose.
- `dimensions` must equal `len(embedding)`; without compression the maximum indexed dimension is 2,000 (up to 4,000 with half-precision on HNSW/IVF, up to 16,000 with DiskANN + product quantization), so e.g. a 3,072-dim model needs one of those options.
- Vectors must be stored as `number[]`; other types (BSON binary vectors, `double[]`) leave the document unindexed and absent from results.
- Only one vector index per path is allowed; `IndexOptionsConflict` means an index on the same key already exists with a different name/options. Reuse its name or drop and recreate it.

### 2. New `skills/indexing/index-create-from-app-code.md` (register in `SKILL.md` rule list)

"Idempotent index creation from application code." Core pattern, Python (pymongo):

```python
import os
from pymongo.errors import OperationFailure

EMBEDDING_DIM = int(os.environ["EMBEDDING_DIM"])   # same var the embedding client uses

def _vector_opts(ix):
    # listIndexes reports the options under "cosmosSearch"; accept either spelling
    return ix.get("cosmosSearch") or ix.get("cosmosSearchOptions") or {}

def ensure_vector_index(db, coll, name="embedding_vector_hnsw"):
    existing = list(db[coll].list_indexes())
    for ix in existing:
        if ix.get("key", {}).get("embedding") == "cosmosSearch":
            got = _vector_opts(ix).get("dimensions")
            if got != EMBEDDING_DIM:
                raise SystemExit(f"{coll}: vector index {ix['name']} has dimensions={got}, "
                                 f"EMBEDDING_DIM={EMBEDDING_DIM}; drop and recreate it")
            return  # one vector index per path; already present and correct
    try:
        db.command({"createIndexes": coll, "indexes": [{
            "name": name, "key": {"embedding": "cosmosSearch"},
            "cosmosSearchOptions": {"kind": "vector-hnsw", "dimensions": EMBEDDING_DIM,
                                    "similarity": "COS", "m": 16, "efConstruction": 64}}]})
    except OperationFailure as e:
        if e.code == 85:   # IndexOptionsConflict
            raise SystemExit(f"{coll}: an index on 'embedding' already exists with different options: "
                             f"{e.details.get('errmsg')}")
        raise
```

Node.js equivalent using `collection.listIndexes().toArray()` and `db.command({ createIndexes: ... })` (or `collection.createIndexes([...])` for scalar filter indexes), with the same env var and error branch. Both variants are guarded by `if os.environ.get("CREATE_INDEXES", "true") == "true"` so a seed run can be re-executed safely. State explicitly that ORM schema declarations (Mongoose `autoIndex`, Beanie `Indexed()`) are not a substitute for a vector index: call this routine from the seed/startup script.

Verification step (also suitable as a dev/CI check, cross-referencing `skills/query-optimizer`):

```python
# 1. Index exists with the right shape
ix = next(i for i in db[coll].list_indexes() if i.get("key", {}).get("embedding") == "cosmosSearch")
assert _vector_opts(ix).get("dimensions") == EMBEDDING_DIM

# 2. A probe vector query runs; a missing index raises
#    "Similarity index was not found for a vector similarity search query"
probe = embed("probe")
assert len(probe) == EMBEDDING_DIM, "embedding model output does not match EMBEDDING_DIM"
hits = list(db[coll].aggregate([{"$search": {"cosmosSearch":
        {"path": "embedding", "vector": probe, "k": 3}}}]))
assert hits, "vector query returned no results (are vectors stored as number[]?)"
```

For the scalar filter / pre-filter indexes created alongside the vector index, run `explain("executionStats")` on the representative filter query and fail if the winning plan is `COLLSCAN` (the existing `index-pattern-cookbook.md` guidance). Do not use a `COLLSCAN` string check as the vector-index test: a `$search` without a vector index errors instead of scanning.

Ship the two snippets as ready-to-run files referenced from the rule: `skills/indexing/examples/create_index.py`, `skills/indexing/examples/create_index.js`, and `skills/indexing/examples/index_example.json` holding the three payloads with demo / larger-dataset parameter sets from the table above.

### 3. One-line additions

- `skills/mcp-setup/SKILL.md` after the `ENABLE_MANAGEMENT_TOOLS` note (lines 154-155): "Generated applications must not depend on MCP management tools being enabled. Create indexes from the app's seed/startup code (see `indexing/index-create-from-app-code`) and use the MCP tools only to inspect."
- `skills/vector-search/vector-create-diskann-index.md` and `vector-choose-index-type.md`: link to the templates file so HNSW/IVF readers are not left with DiskANN-only key names.

## Evidence (run folders)

- `runs/11-correspondent-banking-risk-screener/20261124-201541/doc-gaps.md` and `events.jsonl` (wrong `path` key, `CommandNotSupported`, `IndexOptionsConflict`)
- `runs/02-clinical-trial-matching-orchestration/20261124-193208/05-audit.json` and `events.jsonl` (HNSW with DiskANN params; management tools disabled)
- `runs/12-invoice-matching-reconciliation/20261124-191603/05-audit.json` (embeddings computed, no index, dims unverified)
- `runs/12-cross-border-payment-audit-trail/20261124-201744/doc-gaps.md` (Mongoose schema index never applied, COLLSCAN)
- `runs/19-cross-sell-recommendation-beanie/20261125-055705/doc-gaps.md` (asked for `create_index.py` + `index_example.json`)

## Verification

### 1. Already covered? partially_covered

- Learn (https://learn.microsoft.com/en-us/azure/documentdb/vector-search) already has `createIndexes` templates for all three kinds with exact keys, parameter ranges/defaults, a pymongo `db.command({"createIndexes": ...})` DiskANN example and a `getIndexes()` example. So the facts exist, but not in the kit where the agent looked.
- Agent kit: `skills/vector-search/vector-create-diskann-index.md` and `vector-choose-index-type.md` show DiskANN (`maxDegree`, `lBuild`) and IVF only as an "Incorrect" example (`kind: "vector-ivf", numLists: 100`). A grep of `skills/` and `knowledge-base/` for `efConstruction`, `efSearch`, `nProbes` returns nothing, and there is no driver-side (Python/Node) index-creation code or idempotent list-then-create rule. `skills/indexing/index-pattern-cookbook.md` line 250 covers `explain("executionStats")` / COLLSCAN for scalar indexes only.
- `skills/mcp-setup/SKILL.md` lines 154-155: "To allow write or management tools, add ... `"ENABLE_MANAGEMENT_TOOLS": "true"` to `env`. Read tools are on by default." There is no fallback guidance. documentdb-mcp `tool_list.md` line 9 confirms management tools require `ENABLE_MANAGEMENT_TOOLS=true`; `.env.example` defaults it to false.

### 2. Premise true? confirmed (with corrections applied)

The core premise holds: the kit lacks the templates and the driver-side pattern, and the run evidence checks out (32 run folders' `events.jsonl` contain both a `create_index` call and "Management tools are disabled"; the 11-correspondent-banking events show `CommandNotSupported: Search index creation is not supported yet`). Corrections applied to the body, against the Learn vector-search page and the run logs:
- `listIndexes`/`getIndexes` reports vector options under `cosmosSearch`, not `cosmosSearchOptions`. The draft's code read `cosmosSearchOptions` and would always see `dimensions=None`. Fixed to accept either key.
- The draft verified the vector index with `explain` + "no COLLSCAN". A `$search` with no vector index fails with "Similarity index was not found for a vector similarity search query" (seen in several run logs) instead of scanning. Replaced it with a listIndexes shape check plus a probe query, and kept the COLLSCAN check for scalar filter indexes only.
- The draft's tunables replaced IVF "`numLists ≈ sqrt(N)` for >1M" with Learn's guidance: `documentCount/1000` up to 1M, use DiskANN above 1M, `numLists: 1` for demos. HNSW "production m 16-64, efConstruction 128-400" was unsourced. Replaced it with the documented ranges (m 2-100, efConstruction 4-1000 and ≥ 2*m). Added the DiskANN ranges, `nProbes ≤ numLists` and the tier guidance.
- Added the documented dimension limits (2,000 uncompressed; 4,000 with half-precision; 16,000 with DiskANN+PQ) and "one index per vector path".
- "Vectors must be number[]" is kept. It matches Learn ("Vectors must be a `number[]` to be indexed").
- The idempotency check now matches on the key `embedding: cosmosSearch` rather than the index name, because only one vector index per path is allowed.

### 3. Maintainer skeptic: confirmed

The PR names concrete new files (`skills/vector-search/vector-index-templates.md`, `skills/indexing/index-create-from-app-code.md`, `skills/indexing/examples/*`) and concrete edits (`SKILL.md` rule lists, `mcp-setup/SKILL.md` one-liner, cross-links). It is specific to Azure DocumentDB (`cosmosSearch` kinds, DocumentDB-specific errors, MCP management-tool gating). It fits the kit's existing rule-file format (Why it matters / Incorrect / Correct). The kit is the right repo, not documentdb-mcp: the MCP default-off gating is intentional and documented.

## Finding ids

F0067, F0252, F0253, F0868, F1364, F1604, F2037, F2047, F1774, F1811, F1846, F2102, F2533, F3242, F3340, F1507
