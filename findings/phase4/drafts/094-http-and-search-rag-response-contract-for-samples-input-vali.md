---
title: "vector-search: add `vector-search-response-shape` rule (return searchScore, never return raw vectors, flag fallback, fail clearly on empty query / embedding error)"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 12
findings: 13
bucket: kit-doc-gap
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# vector-search: add `vector-search-response-shape` rule (return `searchScore`, never return raw vectors, flag fallback, fail clearly)

## What happens today

`skills/vector-search/` explains how to build a `$search` + `cosmosSearch` pipeline, but nothing in the kit says what the application should return to its caller once it has the hits. The only related guidance is one tip at the bottom of `vector-knn-query.md`: "Always project `searchScore` if you plan to rerank or threshold." Agents read the conditional literally and skip it. There is no rule about projecting out the embedding field, none about flagging a fallback path, and none about how a search/RAG endpoint should fail when the query is empty or the embedding provider errors.

In an experiment that built 100 Azure DocumentDB samples with gpt-5-mini using this kit, 13 audit findings across 12 samples showed four recurring shapes (the larger counts below come from a keyword scan of all audit files and are indicative, not hand-verified):

1. **Score dropped.** About 31 samples (keyword scan) returned ranked results with no similarity score; several were explicit audit violations of the skill's own tip even though `events.jsonl` shows the skill was loaded (e.g. `11-correspondent-banking-risk-screener`: two `$search` pipelines in `app/src/agent.py`, neither projects `{$meta:'searchScore'}`, so the "risk score" was derived from match counts instead).
2. **Raw vectors returned.** About 7 samples (keyword scan) sent the full embedding array back in normal responses. `15-financial-advisor-chatbot-rag` projects `{ title: 1, content: 1, embedding: 1, metadata: 1 }` and returns `{ ...s.doc, score }` to the chat caller — a 1536-float array per hit. The auditor flagged this as violating a kit practice "P12: do not return full vector payloads"; no such practice exists anywhere in `skills/` or `knowledge-base/`; the model assumed it did. Note that the Learn vector-search page's own IVF examples project `"document": "$$ROOT"`, which returns the vector field to the caller, so agents have no counter-example to copy.
3. **Silent fallback.** Roughly 22 samples (keyword scan of audits) fell back from `$search` to client-side cosine or a plain metadata `find` — usually because index creation failed (management tools disabled, wrong `createIndexes` key shape) — and returned those results indistinguishably from real vector hits. `11-correspondent-banking-risk-screener` implements fallback in `app/src/agent.py` but exposes nothing in the response; callers cannot tell which path ran.
4. **Unhelpful failures.** `17-rare-disease-literature-search` (`app/src/app.py` query handler) and `14-customer-complaint-classifier` (`src/app/main.py` search endpoint) call the embedding API on whatever string arrives, with no empty-query check and no try/except, so an empty `q` or a provider outage surfaces as an unhandled 500. `06-symptom-triage-chatbot-rag` had no try/except around `get_embedding`. `13-product-q-a-chatbot-rag`'s audit noted that no kit or doc guidance states a citation format for grounded answers, so the builder had to invent one; `19-cross-sell-recommendation-beanie` returned an opaque rank with no score components.

## Why it matters

The vector-search skill is routed for "building RAG / semantic-search applications". The response shape is where those applications meet their users and tests: without the score, callers cannot threshold or explain results; returning raw vectors inflates payloads and leaks internal state; an unflagged fallback makes an index-creation failure look like a working vector search (the exact failure mode that hid broken `cosmosSearch` indexes in several runs); and a 500 on empty input hides a client bug behind what looks like a database problem. These are cheap to prevent with one rule file, and they are DocumentDB-adjacent: the embedding call feeds `cosmosSearch`, the fallback replaces `cosmosSearch`, and `searchScore` is a DocumentDB `$meta` field.

## Proposed change

### 1. New rule file: `skills/vector-search/vector-search-response-shape.md`

```markdown
# vector-search-response-shape

**Category:** Vector Search · **Priority:** HIGH

## Why it matters

A `$search` + `cosmosSearch` pipeline is only half of a search feature; the other half is
what your API hands back. Return the score, never the vector, say which path produced the
results, and fail before you hit the database when the input is unusable. Callers (UIs,
tests, downstream agents) can then threshold, explain and trust the results.

Rules:
- **Always project `score: { $meta: "searchScore" }`** and return it on every hit — not only
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
    except Exception as e:            # provider/network/quota error
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
```

### 2. `skills/vector-search/SKILL.md`

- Add to **Rules**: `- [vector-search-response-shape](vector-search-response-shape.md) — Return \`searchScore\` on every hit, project the embedding field out, flag fallback paths, and return 400/502 instead of 500 for empty queries / embedding failures.`
- Extend the `description:` front matter with "…normalizing embeddings for cosine similarity, and shaping search/RAG responses (score, no raw vectors, fallback flag, clear errors)." so routing picks it up for "what should my /search return" questions.
- In `vector-knn-query.md`, change the tip to "Always project `searchScore` and return it to the caller — see [vector-search-response-shape](vector-search-response-shape.md)."

### 3. `docs/SKILLS.md`

Append "response shape (score / no raw vectors / fallback flag)" to the `vector-search/` row (line 25). Optionally cross-link the rule from `skills/full-text-search/fts-basic-search.md`, which already asks for `searchScore` projection.

## Explicitly out of scope for this kit (noted so they are not lost)

- One sample (`05-branch-performance-analytics`) exposed LLM-backed `/ask` and `/summaries/refresh` with no auth or rate limiting. That is application hardening, not DocumentDB guidance; it belongs in the sample gallery's publishing checklist, not here.
- One sample (`18-returns-refund-workflow-orchestration`) invented ad-hoc JSON shapes for three agents' outputs. Canonical schemas for a specific scenario are a sample-template concern.
- Four of the thirteen underlying findings (06-omnichannel, 06-order-history, 17-seasonal-trend, 18-returns) arose because the experiment's own hidden checklist expected a `/search` endpoint the starter prompt never asked for; they are not evidence against the kit and are not counted above.

## Evidence (run folders from the experiment; no secrets)

- `runs/15-financial-advisor-chatbot-rag/20261124-192021/05-audit.json` — check "Do not return vectors": `embedding: 1` projected and returned (`app/src/agent.js` ~lines 59-67); client-side ranking fallback after index creation failed
- `runs/11-correspondent-banking-risk-screener/20261124-201541/doc-gaps.md` — `$search` pipelines without `searchScore`; fallback implemented but not flagged to callers
- `runs/17-rare-disease-literature-search/20261124-195633/05-audit.json` — `/query` handler: no empty-query check, embedding and chat calls uncaught
- `runs/13-product-q-a-chatbot-rag/20261124-184527/doc-gaps.md` — audit gap "Citation/grounding format for RAG responses": no guidance on a sources format
- `runs/14-customer-complaint-classifier/20261124-201931/doc-gaps.md` — `/search` endpoint: no empty-query handling, embedding failure path untested
- `runs/05-branch-performance-analytics/20261124-200647/doc-gaps.md` — unauthenticated `/ask` and `/summaries/refresh` (out-of-scope note above)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

## Verification

### 1. Already covered? — confirmed (not there)
- `skills/vector-search/vector-knn-query.md` line 64 is the only related text: "Always project `searchScore` if you plan to rerank or threshold." It is conditional, and the rule's Correct example projects only `_id, title, price, score` without saying why the embedding is left out.
- `skills/full-text-search/fts-basic-search.md` line 14: "Project `score: { $meta: \"searchScore\" }` so callers can rank, threshold, or rerank." That covers BM25 only.
- Grepping `skills/` and `knowledge-base/` for raw-vector exclusion, fallback flagging, citation format, or HTTP 400/502 error mapping finds nothing. The only "rate limited" hit is the connection skill's retry loop, `skills/connection/SKILL.md:231`. The "P12: do not return full vector payloads" practice that the auditor cited does not exist.
- Learn (https://learn.microsoft.com/en-us/azure/documentdb/vector-search) documents `$meta: "searchScore"` projection but says nothing on response shape, and its examples return the vector via `$$ROOT`.

### 2. Premise true? — confirmed, with one correction applied
- `cosmosSearch` under `$search` and `{$meta:"searchScore"}` are correct per the Learn vector-search page.
- Correction: `lSearch` is a DiskANN-only query parameter, with `k <= lSearch` (range 10–1000). HNSW uses `efSearch` and IVF uses `nProbes` (same Learn page). The Correct snippet now says so and caps `k` at `lSearch`.
- Correction: the evidence for `13-product-q-a-chatbot-rag` is the audit `doc-gaps.md`, not `02-readiness.json`. The 31/7/22 counts come from a keyword scan, not the 13 underlying findings, so they are now labeled as indicative.
- The claims about existing kit files were checked against the clone: SKILL.md Rules list, the description front matter, the `docs/SKILLS.md` line 25 vector-search row, and the `fts-basic-search.md` searchScore text. All are accurate.

### 3. Maintainer skeptic — confirmed
The draft names one new rule file in the kit's existing template (Category/Priority, Why it matters, Incorrect, Correct, References) and gives exact edits to `skills/vector-search/SKILL.md`, `vector-knn-query.md` and `docs/SKILLS.md`. It has a DocumentDB angle: `searchScore` `$meta`, projecting out the `cosmosSearch` path, and flagging when `cosmosSearch` was bypassed. It already drops the generic parts (auth/rate limiting, multi-agent schemas) as out of scope, which is right. I would accept it with the small edits above.

## Finding ids
- F0744
- F0934
- F0958
- F0989
- F1814
- F2573
- F2266
- F1817
- F2345
- F2895
- F2927
- F3198
- F3089
