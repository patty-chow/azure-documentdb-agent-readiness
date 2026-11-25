---
title: "vector-search skill: make $search/cosmosSearch the primary query path and gate client-side cosine behind an index-existence check"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P3
sample_count: 2
findings: 2
bucket: mcp-server
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# vector-search skill: make `$search`/`cosmosSearch` the primary query path and gate client-side cosine behind an index-existence check

## What happens today

`skills/vector-search/vector-knn-query.md` shows the correct `$search` + `cosmosSearch` aggregation, and `vector-create-diskann-index.md` shows how to create the index. But nothing in the skill says:

- that the aggregation is the *required* query path for a vector-search app,
- how an app should check whether a `cosmosSearch` index actually exists (`listIndexes` / `getIndexes()`), or
- what to do when it does not exist.

`grep -rn -iE 'listIndexes|fallback|client-side|in-process' skills/vector-search/` returns nothing.

In an experiment that built 100 Azure DocumentDB gallery samples with gpt-5-mini using this kit plus the DocumentDB/Azure/Learn MCP servers, the vector-index create call failed in at least two runs: the DocumentDB MCP server's `create_index` tool is in the `management` category, which is off unless `ENABLE_MANAGEMENT_TOOLS=true`. With no rule to lean on, the model fell back to pulling documents with `find()` and ranking them in Python with cosine similarity, and shipped that as the app's only query path. It did not try to create the index itself through the driver (`createIndexes`), which was still possible.

- `02-clinical-trial-matching-orchestration`: `app/app/main.py` (around lines 137-164) runs `coll.find(filter_q).limit(200)` followed by a Python `cosine_similarity` loop. Decision D009 in `decisions.jsonl` records that the MCP create-index call (for a `vector-hnsw` index) failed and that the build continued with client-side ranking as a fallback. There is no `$search` stage anywhere in the app. Audit result: requirement `not_met`.
- `04-earnings-call-rag-assistant`: `src/query.py` `retrieve_local()` runs `coll.find({...})` over the whole collection with the embedding projected, then ranks with `np.dot`. The README documents a `vector-diskann` index that the code never queries. Audit result: requirement `partly_met`.

Both runs were audited as `cause: tool_unavailable`, so the root cause is MCP gating (tracked separately). But the kit is the layer that should have told the model: *the database does the search. If the index is missing, create it or label the fallback. Do not quietly switch to a client-side scan.*

## Why it matters

A gallery sample whose query path is `find()` + NumPy shows nothing about Azure DocumentDB vector search. It never uses a `cosmosSearch` index, never sets the index-specific search parameter (`lSearch`, `efSearch` or `nProbes`), `k` or `filter`, and never projects `searchScore`. It also reads the whole collection on every query, so cost grows linearly with collection size. A developer who copies it learns the wrong pattern, and the index-tuning guidance in the rest of this skill becomes dead text. Nothing flags the problem: the app "works" on a 20-document seed, and neither the build nor the README shows that the database is not doing the search.

## Proposed change

### 1. New rule: `skills/vector-search/vector-prefer-server-side-search.md`

````markdown
# vector-prefer-server-side-search

**Category:** Vector Search · **Priority:** HIGH

## Why it matters

The whole point of a `cosmosSearch` index is that Azure DocumentDB performs the
nearest-neighbour search. Pulling documents with `find()` and ranking them in the
application (NumPy / a cosine loop) reads the entire collection on every query,
ignores the index, and teaches readers the wrong pattern. It is acceptable only as
an explicitly labelled fallback for offline unit tests, and it must never be the
default production path.

## Rule

1. Before querying, check that a `cosmosSearch` index exists on the embedding field
   (`listIndexes`: `collection.list_indexes()` in PyMongo, `collection.indexes()` in
   Node.js). A vector index shows up as `key: { <field>: "cosmosSearch" }`, with its
   options (including `kind`) under `cosmosSearch`.
2. If it exists, query with `$search` + `cosmosSearch` and project `searchScore`
   (see vector-knn-query). This is the only production path. Use the search parameter
   that matches the index kind: `lSearch` for `vector-diskann`, `efSearch` for
   `vector-hnsw`, `nProbes` for `vector-ivf`.
3. If it does not exist, **create it from the app with the driver** (`createIndexes`,
   see vector-create-diskann-index) or fail loudly. An MCP tool being unavailable is
   not a reason to skip the index, because the driver can create it. Do not silently fall back.
4. Client-side cosine is permitted only behind an explicit opt-in (e.g.
   `VECTOR_SEARCH_MODE=client` or a test fixture). It must log a WARNING naming the
   missing index, and the README must document it as a "test-only fallback".

## Incorrect

```python
# "Works" on a 20-doc seed, reads the whole collection on every query, never uses the index.
docs = list(coll.find({}, {"embedding": 1, "text": 1}))
scored = sorted(((cosine(q, d["embedding"]), d) for d in docs), key=lambda t: t[0], reverse=True)[:k]
```

## Correct

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
            "(see vector-create-diskann-index) or set VECTOR_SEARCH_MODE=client "
            "for the test-only client-side fallback.")
    logging.warning("TEST-ONLY FALLBACK: ranking client-side; no cosmosSearch index found")
    return _client_side_cosine(coll, query_vector, k)   # offline tests only
```

Node.js equivalent: `const ix = (await coll.indexes()).find(i => i.key?.embedding === "cosmosSearch")`,
read `ix.cosmosSearch.kind`, then `await coll.aggregate([...]).toArray()`.

## References

- [Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search) (query syntax per index kind; "Get vector index definitions" shows the `listIndexes` output shape)
- vector-knn-query, vector-create-diskann-index
````

### 2. Link it from `skills/vector-search/SKILL.md`

Add this line to the `## Rules` list, directly above `vector-knn-query`:

```markdown
- [vector-prefer-server-side-search](vector-prefer-server-side-search.md) — Check the index exists (`listIndexes`) and create it with the driver if it is missing; query with `$search`/`cosmosSearch`. Client-side cosine is a labelled test-only fallback, never the default path.
```

Optionally, extend the front-matter `description` with "...and never falling back to client-side similarity in production."

### 3. Two small fixes in `skills/vector-search/vector-knn-query.md`

Append to the Tips list:

```markdown
- Never replace this stage with `find()` + in-process cosine; if the index is missing, see vector-prefer-server-side-search.
- `lSearch` applies to `vector-diskann`; use `efSearch` for `vector-hnsw` and `nProbes` for `vector-ivf`.
```

## Evidence (run folders from the experiment)

- `runs/02-clinical-trial-matching-orchestration/20261124-193208/05-audit.json`: requirement "find candidate trials by running a $search / cosmosSearch aggregation" is `not_met`, cause `tool_unavailable`
- `runs/02-clinical-trial-matching-orchestration/20261124-193208/decisions.jsonl`: D007/D009 record the explicit fallback to client-side ranking after the MCP create-index call failed
- `runs/02-clinical-trial-matching-orchestration/20261124-193208/app/app/main.py`: `find()` + cosine loop, no `$search`
- `runs/04-earnings-call-rag-assistant/20261124-190247/05-audit.json`: requirement "runs a $search / cosmosSearch vector similarity query" is `partly_met`, cause `tool_unavailable`
- `runs/04-earnings-call-rag-assistant/20261124-190247/app/src/query.py`: `retrieve_local()` does a full-collection `find()` + `np.dot`

## Verification

### 1. Already covered? confirmed (not covered)

I searched the local clone of Azure/documentdb-agent-kit with `grep -rn -iE 'listIndexes|fallback|client-side|in-process|cosine|numpy|index_information|list_indexes' skills knowledge-base`. Nothing in `skills/vector-search/` mentions an index-existence check, a fallback policy or client-side scoring. The only "cosine" hits are about the `COS` similarity metric and embedding normalisation (`SKILL.md`, `vector-normalize-embeddings.md`, `vector-create-diskann-index.md`). `list_indexes` appears only in `skills/query-optimizer/SKILL.md` and `skills/natural-language-querying/SKILL.md`, where it is used as an MCP tool for query tuning, not as an app-side guard before vector search. `vector-knn-query.md` shows the aggregation but does not say it must be the only production path. On Learn, https://learn.microsoft.com/en-us/azure/documentdb/vector-search documents the `$search`/`cosmosSearch` syntax and shows the `getIndexes()` output, but it gives no guidance on fallbacks. Agents load the kit skill, so the kit is the right place for the rule.

### 2. Premise true? confirmed (with corrections applied)

- The `$search` + `cosmosSearch` syntax, the `$meta: "searchScore"` projection, the `filter` pre-filter and the `listIndexes` output shape (`key: { <field>: 'cosmosSearch' }`, options under `cosmosSearch` including `kind`) all match https://learn.microsoft.com/en-us/azure/documentdb/vector-search ("Get vector index definitions" section).
- DocumentDB MCP gating is confirmed: in microsoft/documentdb-mcp, `tool_list.md` lists "`create_index` (`management`)" and states that management tools require `ENABLE_MANAGEMENT_TOOLS=true`. The README says that by default only read tools are exposed.
- **Correction applied:** the original draft's example always set `lSearch`. Per Learn, `lSearch` is the DiskANN query parameter; HNSW uses `efSearch` and IVF uses `nProbes`. Sample 02 had attempted a `vector-hnsw` index, so the snippet would have been wrong for that exact case. The rule and snippet now choose the parameter from the index `kind` returned by `listIndexes`, and a tip was added to `vector-knn-query.md` (whose Tips mention only `lSearch`).
- **Correction applied:** the rule now says the app can and should create the index with the driver (`createIndexes`) when the MCP tool is unavailable. The original said only "fail loudly or create it", which left the MCP-gated path ambiguous.
- **Correction applied:** I removed the unverified claim that "roughly nine other samples" had the same shape. Only the two findings in this theme have evidence.
- I removed the specific `events.jsonl` line-number citation, which was not re-verified. The code locations in `main.py` (`find(...).limit(200)` at line 137, cosine at 154-159) and `query.py` (`find` at line 29, `np.dot` at line 37) were checked by grep.

### 3. Maintainer skeptic: confirmed

The draft names exact files (a new `vector-prefer-server-side-search.md`, plus edits to `SKILL.md` and `vector-knn-query.md`) and follows the existing rule-file format (Category/Priority, Why it matters, Incorrect, Correct, References). It is specific to Azure DocumentDB (`cosmosSearch` index kinds, `searchScore`, per-kind search parameters). It belongs in this repository: the MCP gating is a separate theme for microsoft/documentdb-mcp, and this PR only adds kit guidance. I would accept it with the edits above.

## Finding ids

- F0251
- F0592
