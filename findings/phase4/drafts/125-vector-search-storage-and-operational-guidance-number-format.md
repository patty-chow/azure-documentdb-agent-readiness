---
title: "Vector search page: make the number[] rule explicit about BSON Binary, and add short guidance on embedding metadata, projection and backfill"
repo: learn-docs
type: learn-feedback
status: ready_with_edits
priority: P1
sample_count: 12
findings: 13
bucket: learn-practice_not_public
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Vector search page: name BSON Binary in the number[] rule, and add an "Operating embeddings" section (metadata, re-embedding, projection, backfill)

**Page:** https://learn.microsoft.com/en-us/azure/documentdb/vector-search
**Proposed change:** (a) reword the existing `number[]` notes; (b) add a short "Operating embeddings" section after "Get vector index definitions".

## What the page already covers
The page already gives `createIndexes` templates with the `{ <path>: "cosmosSearch" }` key and `cosmosSearchOptions` (kind `vector-ivf` / `vector-hnsw` / `vector-diskann`, `dimensions`, `similarity`). It shows insert examples with plain number arrays in Python and JavaScript, shows `getIndexes()` / `listIndexes` output, and explains that the integrated store keeps vectors next to the source data. It also says twice that "Vectors must be a `number[]` to be indexed" and that "a vector using another type, such as `double[]`, prevents the document from being indexed."

## What happens today
An AI coding agent (gpt-5-mini with the DocumentDB Agent Kit, DocumentDB MCP and Learn MCP) built 100 sample apps. In 12 of them it searched for vector storage and operations guidance and fell back on what it already knew:

- **Wrong storage format.** Two samples (15-financial-advisor-chatbot-rag, 19-insider-threat-detection-pipeline) asked for, or proposed, packing embeddings as `Float32Array` / float32 into **BSON Binary**. The page's warning names only `double[]` as the bad example. Arrays of numbers sent by most drivers are stored as BSON doubles, so that example is confusing. It never names BSON Binary or typed arrays, which are the encodings agents and developers coming from other vector stores actually reach for.
- **Vector search moved to the app.** In sample 07 the agent called `createSearchIndexes`, got CommandNotSupported, and built a client-side nearest-neighbor fallback. In sample 15 vector index creation failed and the app ranked documents in process. In Azure DocumentDB, `createSearchIndexes` is the full-text search command. Vector indexes are created with `createIndexes` and `cosmosSearch`. The vector-search page does not mention the full-text command, so nothing tells a reader which of the two commands to use.
- **Unconfirmed practices.** Storing the model name and dimensions with each vector, re-embedding and rebuilding when the model changes, not returning raw vectors, and backfilling documents when the embedder is down were all marked "prior knowledge only". Samples 10 and 12 asked for exactly this guidance.

## Why it matters
An unsupported vector type fails silently: inserts succeed and the document is simply missing from vector results. One explicit sentence naming BSON Binary closes the most damaging mistake. A few lines of operating guidance stop agents from guessing.

## Proposed content
1. **Reword the `number[]` notes** (DiskANN field table and the IVF "Important" box). Suggested text: "Store vectors as an array of numbers (for example a JavaScript `number[]` or a Python `list[float]`). Vectors stored as BSON Binary (for example a packed `Float32Array`) or in any other non-array type aren't indexed, and those documents aren't returned by vector search." Remove or explain the `double[]` example.
2. **Which command.** Add one sentence: "Vector indexes are created with `createIndexes` and a `cosmosSearch` key. `createSearchIndexes` is used for [full-text search](full-text-search) and doesn't create vector indexes." Add a short idempotent pattern: check `listIndexes` for an index on the path before creating it, because only one index per vector path is allowed.
3. **Dimensions and metadata.** `dimensions` must equal the embedding model's output size. Store `embeddingModel` and `embeddingDimensions` (or a version field) on each document, plus chunk size and token count for RAG. When the model changes, re-embed, drop the index and recreate it with the new `dimensions`.
4. **Responses.** In the `$project` after `$search`, exclude the vector field and return metadata plus `{ $meta: "searchScore" }`, rather than projecting `$$ROOT` with the full vector.
5. **Embedder outages.** Insert the document without the vector field, set a flag such as `embeddingPending: true`, and backfill later. Documents without a vector are just left out of vector results until they're backfilled.

## Evidence (experiment run folders)
- runs/15-financial-advisor-chatbot-rag/20261124-192021/05-audit.json (asked how to pack Float32Array into BSON Binary; fell back to client-side ranking after index creation failed)
- runs/19-insider-threat-detection-pipeline/20261124-202818/05-audit.json (asked whether to store float32 vs JSON doubles and how to pack into BSON binary; client-side computation)
- runs/07-voice-of-customer-sentiment-hub/20261124-204049/05-audit.json (`createSearchIndexes` returned CommandNotSupported; client-side fallback)
- runs/12-invoice-matching-reconciliation/20261124-191603/05-audit.json (no source for embedding model/dimension metadata; mixed createIndexes/createSearchIndexes)
- runs/10-support-ticket-rag-assistant/20261124-204529/05-audit.json (asked what metadata to store per vector and how to reindex when the model changes)

## Verification

### 1. Already covered? partially_covered
The vector-search page (fetched 2026-11-25, ms.date 2025-11-05) already has the `createIndexes` + `cosmosSearch` + `cosmosSearchOptions` templates for all three kinds, number-array insert examples in Python and JavaScript, `getIndexes()` output under "Get vector index definitions", and the point about keeping vectors next to the source data. It states: "Vectors must be a `number[]` to be indexed and used in vector search results. A vector using another type, such as `double[]`, prevents the document from being indexed." So the original draft's points 1 (format), 2 (index creation and listIndexes) and 4 (layout) are mostly already there, and I removed them or narrowed them to rewording. The page does not name BSON Binary or typed arrays and does not contrast `createSearchIndexes`. It has nothing on per-document embedding metadata, re-embedding on a model change, projecting the vector out, or backfill. The Agent Kit partly covers metadata and rebuilds: `skills/vector-search/vector-normalize-embeddings.md` says "Store the embedding model name and dimensions alongside the vector" and "bump `embeddingVersion` and run a backfill", and `vector-create-diskann-index.md` says "If you change embedding models, rebuild the index". But the kit has no number[]/BSON Binary rule and no guidance on pending embeddings or projection, and Learn (where the agents looked) has none of it. The documentdb-mcp clone has no matches for this guidance.
Citations: https://learn.microsoft.com/en-us/azure/documentdb/vector-search ; documentdb-agent-kit/skills/vector-search/vector-normalize-embeddings.md ; documentdb-agent-kit/skills/vector-search/vector-create-diskann-index.md.

### 2. Is the premise true? confirmed (framing corrected)
- Vectors must be number arrays, and other types (including BSON binary vectors) aren't indexed and drop out of results: consistent with the Learn page text above and with the service facts.
- Vector indexes use `createIndexes` with `cosmosSearch` and kinds `vector-ivf` / `vector-hnsw` / `vector-diskann`: confirmed by the page templates.
- `createSearchIndexes` is not the vector index command: correct. I changed the framing from "Atlas-style createSearchIndexes" because `createSearchIndexes` does exist in Azure DocumentDB for full-text search (Agent Kit `skills/full-text-search/SKILL.md`: "Index command is `createSearchIndexes` (not `createIndexes`)").
- `dimensions` must match the model output, and the index must be rebuilt on a model change: confirmed by the kit (`vector-create-diskann-index.md`). The page also says only one index per vector path is allowed, which supports drop-and-recreate.
- `{ $meta: "searchScore" }`: confirmed by the page examples.
- Corrected statement: the original draft said the docs "do not say how to store" embeddings. The page does state the `number[]` rule. The real gap is that it doesn't name BSON Binary or typed arrays, and that its `double[]` example is confusing.

### 3. Maintainer skeptic: confirmed
As a docs maintainer I'd accept this with the edits applied. It names one page and two exact spots for rewording (the DiskANN field table and the IVF "Important" note), proposes replacement text, and adds a short section of DocumentDB-specific operating guidance: which index command to use, the one-index-per-path rule, the BSON Binary pitfall, and `searchScore` projection. It no longer asks for content the page already has. The embedding-metadata and backfill items are generic, but each is tied to a DocumentDB behavior (the `dimensions` parameter, documents without vectors dropping out of results), so they belong here and not in a separate repo.

## Finding ids
F0102, F0374, F0242, F1189, F0623, F1711, F1748, F1916, F2116, F2580, F2902, F3285, F3290
