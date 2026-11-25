---
id: K31
title: "vector-search: add a response-shape rule (return the score, never raw vectors)"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P1
sample_count: 7
member_drafts:
  - 094-http-and-search-rag-response-contract-for-samples-input-vali.md
open_questions: 2
---

# vector-search: add a response-shape rule (return the score, never raw vectors)

## What happens today

`skills/vector-search/` explains how to build a `$search` + `cosmosSearch` pipeline but says nothing about what an application should hand back to its caller. The only related text is one tip in `vector-knn-query.md` (line 64): "Always project `searchScore` if you plan to rerank or threshold." Coding agents read the condition literally and skip it. Nothing in `skills/` or `knowledge-base/` says to project the embedding field out, to flag a fallback path, or how a search/RAG endpoint should fail on an empty query or an embedding-provider error. (`skills/full-text-search/fts-basic-search.md` asks for `searchScore`, but only for BM25.)

We had a coding agent (gpt-5-mini, with this kit installed) build 100 Azure DocumentDB sample apps, then audited each one. Four failure shapes kept appearing in search/RAG samples:

1. **Score dropped.** Ranked results came back with no similarity score, even where the run log shows the skill was loaded. In one risk-screener sample, neither of two `$search` pipelines projected `{$meta: "searchScore"}`, so the "risk score" was derived from match counts.
2. **Raw vectors returned.** A chat sample projected `embedding: 1` and returned a 1536-float array per hit to the chat client. Its auditor cited a kit rule "do not return full vector payloads" that does not exist. The Learn vector-search IVF examples project `"document": "$$ROOT"`, which also returns the vector, so agents have no counter-example to copy.
3. **Silent fallback.** When index creation failed, samples fell back to client-side cosine or a plain `find` and returned those results indistinguishably from real vector hits, which hid broken `cosmosSearch` indexes.
4. **Unhelpful failures.** Search handlers embedded whatever string arrived, with no empty-query check and no try/except, so an empty `q` or a provider outage surfaced as an unhandled 500. One RAG sample had to invent its own citation format, and a recommender returned an opaque rank with no score.

## Why it matters

These samples raised 13 related audit findings across 12 of the 100 samples. Seven samples (seven findings) show the problems this PR addresses; the other six findings, from five samples, were out of scope (listed below). A keyword scan of all audit files suggests the pattern is wider: roughly 31 samples dropped the score, 7 returned raw vectors and 22 fell back silently. Those scan numbers are indicative, not hand-verified, and all counts come from one experiment run.

The vector-search skill is routed for "building RAG / semantic-search applications", and the response is where those apps meet users and tests. Without the score, callers cannot threshold or explain results. Raw vectors bloat payloads and expose internal state. An unflagged fallback makes a failed index look like working vector search. A 500 on empty input makes a client bug look like a database problem. One rule file prevents all four, and each is DocumentDB-specific: `searchScore` is a `$meta` field, the embedding is the `cosmosSearch` path, and the fallback replaces `cosmosSearch`.

## Proposed change

### 1. New file `skills/vector-search/vector-search-response-shape.md`

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
  "fallback"`. Prefer failing loudly when the index is missing over silently degrading.
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
- [Vector search queries](https://learn.microsoft.com/azure/documentdb/vector-search)
````

[needs SME confirmation] The query-time knob names in the Correct example's comment (`efSearch` for `vector-hnsw`, `nProbes` for `vector-ivf`) and their limits must be confirmed by engineering before merge; see Open questions.

### 2. `skills/vector-search/SKILL.md`

- Under **Rules**, after the `vector-normalize-embeddings` line, add:
  `- [vector-search-response-shape](vector-search-response-shape.md) — Return \`searchScore\` on every hit, project the embedding field out, flag fallback paths, and return 400/502 instead of 500 for empty queries / embedding failures.`
- In the `description:` front matter, replace "and normalizing embeddings for cosine similarity." with "normalizing embeddings for cosine similarity, and shaping search/RAG responses (score, no raw vectors, fallback flag, clear errors)." so routing picks the skill up for "what should my /search return" questions.

### 3. `skills/vector-search/vector-knn-query.md`

Line 64: replace "Always project `searchScore` if you plan to rerank or threshold." with "Always project `searchScore` and return it to the caller; see [vector-search-response-shape](vector-search-response-shape.md)."

### 4. `docs/SKILLS.md`

In the `vector-search/` row (line 25), change the description to "`cosmosSearch` with DiskANN / HNSW / IVF, PQ, fp16, response shape (score / no raw vectors / fallback flag)". Optionally cross-link the new rule from `skills/full-text-search/fts-basic-search.md`.

### Out of scope (noted so they are not lost)

- One sample exposed LLM-backed endpoints with no auth or rate limiting; that is app hardening, not DocumentDB guidance.
- One sample invented ad-hoc JSON shapes for multi-agent outputs; that is a sample-template concern.
- Four findings (from four samples, one of which also raised the multi-agent finding) came from the experiment's own audit checklist expecting a `/search` endpoint that the build prompt never asked for. They are a harness artifact and are not counted above.

## Evidence

Run folders from the experiment (no secrets):

- `runs/15-financial-advisor-chatbot-rag/20261124-192021/05-audit.json`: embedding projected and returned; client-side ranking after index creation failed
- `runs/11-correspondent-banking-risk-screener/20261124-201541/doc-gaps.md`: `$search` without `searchScore`; fallback not flagged to callers
- `runs/17-rare-disease-literature-search/20261124-195633/05-audit.json`: no empty-query check; embedding call uncaught
- `runs/14-customer-complaint-classifier/20261124-201931/doc-gaps.md`: `/search` has no empty-query handling; embedding failure path untested
- `runs/13-product-q-a-chatbot-rag/20261124-184527/doc-gaps.md`: no guidance on a citation/sources format for RAG

## Open questions

1. [needs SME confirmation] The Correct example's comment names the query-time knob for each index type: `lSearch` for `vector-diskann` (with `k <= lSearch`, range 10–1000), `efSearch` for `vector-hnsw`, `nProbes` for `vector-ivf`. The reviewer flagged the HNSW and IVF limits as needing engineering confirmation. Please confirm the parameter names and ranges before merge.
2. Maintainers: should the HTTP status mapping (400 for empty query, 502 for embedding failure) live in this kit, or should the rule keep only the score, no-vectors and fallback-flag parts and leave error mapping to sample templates?

## Source drafts

- 094-http-and-search-rag-response-contract-for-samples-input-vali.md
