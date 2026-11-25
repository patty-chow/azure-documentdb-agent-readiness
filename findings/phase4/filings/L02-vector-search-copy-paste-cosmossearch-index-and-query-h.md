---
id: L02
title: "Vector search: copy-paste cosmosSearch index and query how-to, explicit number[] storage rule and embedding-dimensions table"
repo: learn-docs
type: learn-feedback
status: needs_sme
priority: P1
sample_count: 71
member_drafts:
  - 072-vector-search-cookbook-copy-paste-cosmossearch-createindexes.md
  - 043-vector-search-page-lacks-an-embedding-model-to-dimensions-ta.md
  - 125-vector-search-storage-and-operational-guidance-number-format.md
open_questions: 2
---

# Vector search: copy-paste cosmosSearch index and query how-to, explicit number[] storage rule and embedding-dimensions table

**Pages:** https://learn.microsoft.com/azure/documentdb/vector-search (source `azure/documentdb/vector-search.md`, MicrosoftDocs/nosql-docs-pr), plus the `quickstart-*-vector-search`, `quickstart-*-select-algorithm` and `full-text-search-hybrid` pages.

## What happens today

The vector-search content is accurate but not usable as a starting point:

- `vector-search.md` (TOC "Vector database") is a ~5,000-word concept article. The `createIndexes` templates sit inside DiskANN/HNSW/IVF tabs and all use 3-dimensional toy vectors. There is no Node code, no idempotent create, and no tuning guidance beyond IVF `numLists`.
- **The storage rule is ambiguous.** It appears only in a DiskANN field-table cell and an IVF-tab "Important" box: "Vectors must be a `number[]` to be indexed ... A vector using another type, such as `double[]`, prevents the document from being indexed." An array of doubles is exactly what every driver sends, and the real failure case, BSON Binary (packed float32, typed arrays), is never named. The behaviour itself is documented and confirmed: a document whose vector is not an array of numbers is stored but not indexed and is silently absent from results, and a Binary query vector is rejected (engine issue documentdb/documentdb#109 confirms binary subtype 9 is stored and returned intact while index-side search on it is a separate, untracked feature).
- **No page lists an embedding model and its dimensions.** The quickstarts hardcode `text-embedding-3-small` / 1536. The concept page links only generically to Azure OpenAI and Hugging Face.
- **Nothing says which command builds a vector index.** `createSearchIndexes` (the full-text search command) is not mentioned on the page, so readers cannot tell that vector indexes always use `createIndexes` with `cosmosSearchOptions`.
- The quickstarts drop and recreate the index on every run and project `document: "$$ROOT"`, so the full vector is returned with every hit. They use DiskANN `maxDegree: 20, lBuild: 10` (the documented minimums of the 20 to 2048 and 10 to 500 ranges), while the concept page documents defaults of 32/50 and its own example uses `lBuild: 64`.
- No guidance on per-document embedding metadata, re-embedding after a model change, or inserting documents while the embedder is unavailable.

## Why it matters

In one experiment run, an AI coding agent (gpt-5-mini with the DocumentDB Agent Kit skills and the DocumentDB, Azure and Learn MCP servers) built 100 Azure DocumentDB sample apps. **71 of the 100 samples** logged a vector-search documentation gap (200 distinct findings: 99 + 88 + 13 across the three drafts, no shared ids). The three source drafts counted 54, 61 and 12 samples, and their samples overlap. 71 is a recount of distinct samples from the experiment's findings file. All counts come from one run and may shift on a re-run.

What the agent did:

- Stored embeddings as BSON Binary. The inserts succeeded, but those documents were stored without being indexed and never appeared in vector results. A Binary query vector failed with `BadValue: ... expected an array type field`.
- Called `createSearchIndexes` for a vector index, got `CommandNotSupported` (115), and fell back to client-side cosine over every document. Other samples used Atlas `knnBeta` syntax.
- Skipped vector indexing entirely (11 samples) or hardcoded 1536 with no length check, because no page ties a model to `dimensions`. Of 187 model or dimension decisions, 97 came from model priors, not from documentation.
- Created indexes with parameters it could not explain (about 20 samples), and returned whole vectors in API responses.
- Tried the DocumentDB MCP `documentdb_create_index` tool, got "Management tools are disabled by default", and had no short driver-only recipe to fall back to (8 samples). This refusal comes from the MCP server's opt-in setting as configured in this run, not from the service.
- Invented its own environment-variable names (`EMBEDDING_DIMS`, `EMBEDDING_DIM`, `EMBED_DIMENSIONS`, `OPENAI_EMBEDDING_MODEL`, ...) because the concept page does not point to the names the quickstarts use.

## Proposed change

### 1. New how-to page: `azure/documentdb/how-to-create-vector-index.md`

Title: "Create a vector index and run a similarity query" (`ms.topic: how-to`). TOC: under *Vector search*, after *Vector database*. If the team prefers fewer pages, this can instead be a "Copy-paste recipe" section at the top of `vector-search.md`. The page should be mostly code, with Python and Node tabs:

- A short "How to store vectors" callout at the top (same text as the storage rule in section 2), plus: for `similarity: "COS"`, L2-normalize vectors at ingest if the model does not already return unit-length vectors; only one vector index per vector path ("Indexing applies to only one vector per path. You can create only one index per vector path."); half-precision (`compression: "half"`, HNSW and IVF, up to 4,000 dimensions) and product quantization (DiskANN, up to 16,000 dimensions) are index options, not a storage format you choose in your documents; without compression the limit is 2,000 dimensions.
- A dimension probe and an `embed()` helper in Python and Node: call Azure OpenAI with keyless Microsoft Entra ID auth, assert `len(vector) == EMBEDDING_DIMENSIONS` once at startup, and insert the returned list unchanged (not wrapped in BSON Binary). Use the env names the quickstarts already use, and show them as a `.env` block with names only and no secrets: `AZURE_OPENAI_EMBEDDING_ENDPOINT`, `AZURE_OPENAI_EMBEDDING_MODEL`, `AZURE_OPENAI_EMBEDDING_API_VERSION`, `EMBEDDING_DIMENSIONS`.
- An idempotent `ensure_vector_index` function. It reads `listIndexes` (which reports the options under `cosmosSearch`), returns if an index on the path already has the same `cosmosSearch.kind` and `dimensions`, raises its own error if the spec differs (only one vector index per path is allowed, so the caller must drop and re-create), and otherwise runs `createIndexes` with `key: {embedding: "cosmosSearch"}` and `cosmosSearchOptions` for one of `vector-diskann`, `vector-hnsw` or `vector-ivf`. The helper must not rely on a specific server error code: the response to a same-name index with different options, and whether an identical `createIndexes` call is a no-op, are undocumented, so treat both a success and an error from a duplicate name as a prompt to re-read `listIndexes` and compare. Say when to run it: an HNSW index can be created on an empty collection; an IVF index's `numLists` depends on document count, so create or re-create it after loading; a product-quantization index should be created after the collection has data. It needs only the driver and the standard connection string from the quickstarts (keep its `retrywrites=false`; retryable writes are not supported by Azure DocumentDB), with no portal, CLI or MCP step. Also create an ordinary index on each pre-filter field (the page's existing prefiltering rule), and add: "If a workload only needs exact matches, ranges or sorting, it needs ordinary indexes, not a vector index."
- A query: `$search: {cosmosSearch: {path, vector, k, lSearch | efSearch | nProbes, filter}}`, then an inclusion `$project` of the needed fields plus `score: {$meta: "searchScore"}`. Note: "Don't project `$$ROOT`. It returns the full vector, about 12 KB per hit at 1,536 dimensions."
- A starting-parameters table, based on the page's documented ranges and defaults, extending the existing vector-count/tier table. IVF on M10/M20: `numLists: 1` for demos, then `documentCount/1000` up to one million documents, `nProbes: 1` (the default; `nProbes` is at most `numLists`); above one million documents follow the page's Important box and use DiskANN instead (the IVF field table's `sqrt(documentCount)` text is an open inconsistency, see Open question 1). HNSW and DiskANN need M30 or higher (limitations page, vector-search section; release note 2025-07-15). HNSW on M30+: `m: 16` (range 2 to 100), `efConstruction: 64` (range 4 to 1000 and at least `2 * m`), `efSearch: 40` (default). DiskANN on M30+: `maxDegree: 32` (range 20 to 2048), `lBuild: 50` (range 10 to 500), `lSearch: 40` (range 10 to 1000, and `k` at most `lSearch`). Add: "Raise query-time values before you rebuild; rebuilding is the expensive step. Verify with `explain()` that the `$search` stage uses the index. Size capacity by vCore tier and memory." Add "small production" and "production" columns only after the product team signs off.
- An error table. `CommandNotSupported` 115, "Search index creation is not supported yet", means `createSearchIndexes` ran on a cluster where the full-text search preview isn't enabled (observed in run 07; no Learn page documents the error). For a vector index the fix is always `createIndexes` with a `cosmosSearch` key. `createSearchIndexes` is only for full-text search, which is in preview and is enabled per cluster (portal Settings > Features > Full-text search > Enable, then wait 10 minutes before creating a search index). `BadValue` "expected an array type field" means a Binary or object vector, so pass an array. `knnBeta`/`$vectorSearch` is Atlas syntax, so use `cosmosSearch`. A document missing from results has a vector that isn't an array of numbers or has the wrong length. No results right after creation means the index may still be building, which the select-algorithm quickstart's Troubleshooting section puts at 2 to 3 minutes, so retry instead of recreating. "Management tools are disabled by default" from the DocumentDB MCP server is that server's opt-in setting, not a service limit, so use the driver snippet.
- Next steps: hybrid BM25 + vector with RRF (`full-text-search-hybrid`), the half-precision and product-quantization pages, and a short LangChain snippet that builds the `AzureDocumentDBVectorSearch` store from `langchain-azure-cosmosdb` (the `langchain-azure-ai` class `AzureCosmosDBMongoVCoreVectorSearch` is a deprecation shim since langchain-azure PR #870) from the same model and `dimensions` variables and the same `kind`/`similarity`, ending in `.as_retriever(search_kwargs={"k": 5})`.

### 2. Edits to `vector-search.md`

- **Storage rule.** Replace both `number[]` notes with one callout above the DiskANN/HNSW/IVF tabs that names BSON Binary explicitly: "Store each vector as an array of numbers (a JavaScript `number[]` or a Python `list[float]`). Documents whose vector field holds another BSON type, for example a BSON Binary of packed float32 bytes (subtype 9) or a typed array, are stored but not indexed, and aren't returned by vector search. A query vector that isn't an array is rejected with `BadValue`. Convert bytes or NumPy arrays with `.tolist()` (Python) or `Array.from()` (Node) before you insert." Remove the `double[]` example.
- **New H2, "Choose an embedding model and set `dimensions`"**, before *Perform vector similarity search*. Lead sentence: "`dimensions` must equal the length of every vector you insert." Then this table:

  | Model | Output dimensions |
  |---|---|
  | Azure OpenAI / OpenAI `text-embedding-3-small` | 1536 (reducible with the `dimensions` request parameter) |
  | `text-embedding-3-large` | 3072 (above the 2,000 uncompressed limit: use `compression: "half"` on HNSW/IVF, up to 4,000, or DiskANN with product quantization, up to 16,000, or request fewer dimensions) |
  | `text-embedding-ada-002` | 1536 |
  | `all-MiniLM-L6-v2` | 384 |
  | CLIP ViT-B/32 | 512 |

  The 2,000 / 4,000 / 16,000 limits are the figures the concept, half-precision, product-quantization and limitations pages agree on, confirmed by the product owner on 2026-11-25; the select-algorithm quickstarts' 8,000 figure for HNSW is wrong (the engine rejects a half-precision HNSW index with 4,001 dimensions: "field cannot have more than 4000 dimensions for vector index") and is corrected in section 3. Add: "If you request a smaller `dimensions` from the embedding API, create the index with that smaller value." And: "Use `COS` for text-embedding models that return unit-normalized vectors (OpenAI and Azure OpenAI embeddings do; check your model's documentation), for which `COS` and `IP` give the same ranking. Use `L2` when the model's documentation recommends Euclidean distance. The metric is set at index creation; to change it, drop and re-create the index."
- **Which command.** Add: "Vector indexes are created with `createIndexes` and a `cosmosSearch` key. `createSearchIndexes` is for full-text search, which is in preview and enabled per cluster, and doesn't create vector indexes."
- **New short section, "Operating embeddings,"** after *Get vector index definitions*. Store `embeddingModel`, `embeddingDimensions` and `embeddingVersion` on each document (plus chunk size and token count for RAG chunks), and never mix models in one collection. When the model changes, re-embed, then drop and recreate the index with the new `dimensions`. If the embedder is down, insert the document without the vector and with `embeddingPending: true`, then backfill. Such documents are left out of vector results until then.
- Link the new page from *Perform vector similarity search* and from *LLM orchestration tools* (to the LangChain snippet). Also cross-link it from `build-rag-applications` and the Azure OpenAI integration page.

### 3. Consistency fixes

- The `quickstart-*-select-algorithm` pages give 8,000 dimensions for HNSW. `vector-search.md`, `half-precision.md` and `limitations.md` give 2,000 uncompressed and 4,000 with half-precision. The product owner confirmed on 2026-11-25 that 2,000/4,000 (HNSW and IVF) and 16,000 (DiskANN with product quantization) are correct and the 8,000 figure must go. The quickstarts embed `ai/includes/choosing-algorithm.md` from github.com/Azure-Samples/documentdb-samples: fix line 12 (the HNSW table row), line 25 ("some already exceed 8,000 dimensions") and line 30 ("supports embeddings up to 8,000 dimensions"), plus the DiskANN "Why default" sentence, and line 152 of the same repo's `.github/copilot-instructions.md` ("HNSW's 8,000"). One PR to that repository fixes every language's quickstart at once.
- The IVF field table in `vector-search.md` says `numLists` = `sqrt(documentCount)` above one million documents, while the Important box under it says to use DiskANN instead. This filing follows the Important box; reconcile the two once engineering answers (Open question 1).
- `vector-search.md`'s own DiskANN example uses `lBuild: 64`, while the page documents a default of 50. Use the default or say why the example differs.
- In `quickstart-*-vector-search`, use the DiskANN defaults or add a comment that `maxDegree: 20, lBuild: 10` are the documented minimums, sized for a demo. Link the new page from Next steps, in both the `quickstart-*-vector-search` and `quickstart-*-select-algorithm` pages.
- The quickstart's code comment "no two vector indexes of the same kind on the same field" is narrower than the concept and limitations pages' rule of one index per vector path; align it with the pages.
- In `full-text-search-hybrid.md`, replace the code comment "See vector-search.md" with a link to the new page.
- Tier for HNSW and DiskANN: the limitations page's vector-search section says both are available on M30 and greater (matching the 2025-07-15 release note), but the same page's free-tier list still says HNSW is "available in M40+", and `quickstart-agent-nodejs`'s cluster tier table says DiskANN needs "M40 or higher". Change both to M30.

## Evidence

- `runs/01-product-catalog-with-vector-search/20261125-061803/app/utils.py` and `05-audit.json`: vectors written as BSON Binary; the storage requirement was marked `partly_met`.
- `runs/11-visual-similarity-search-image-embeddings/20261124-184225/events.jsonl`: `BadValue` on a Binary query vector.
- `runs/07-voice-of-customer-sentiment-hub/20261124-204049/events.jsonl`: `createSearchIndexes` used for a vector index, then a client-side fallback.
- `runs/03-substitute-product-finder/20261124-183232/app/app/routes.py`: Atlas `knnBeta` payload.
- `runs/04-regulatory-reporting-orchestration/20261124-200545/doc-gaps.md`: vector search dropped for lack of a model-to-dimensions mapping.
- `runs/10-support-ticket-rag-assistant/20261124-204529/05-audit.json`: the agent asked what metadata to store per vector and how to reindex.
- `runs/08-regulatory-compliance-rag-checker/20261124-190949/events.jsonl`: MCP management tools disabled; the agent needed a driver-only path.

## Resolved

retryWrites: answered 2026-11-25, see findings/phase4/DECISIONS.md. Retryable writes are not supported; retrywrites=false is required; the server does not de-duplicate retried writes (documentdb/documentdb#767).

- Vector-index facts: settled 2026-11-25 from the Learn vector-search, half-precision, product-quantization and limitations pages and engine issue documentdb/documentdb#109, see findings/phase4/DECISIONS.md.
  - A document whose vector is a BSON Binary or typed array is stored but not indexed and is silently absent from results; a Binary query vector is rejected with "expected an array type field" (vector-search DiskANN field table and IVF Important box; documentdb/documentdb#109).
  - HNSW `m` 2 to 100 (default 16), `efConstruction` 4 to 1000 and at least `2m` (default 64), `efSearch` default 40; IVF `numLists` = documentCount/1000 up to one million documents, start at 1 for demos, `nProbes` default 1 and at most `numLists`; DiskANN `maxDegree` 20 to 2048 (default 32), `lBuild` 10 to 500 (default 50), `lSearch` 10 to 1000 (default 40) with `k` at most `lSearch` (vector-search page, per-algorithm tabs).
  - Dimension limits: 2,000 without compression, 4,000 with `compression: "half"` on HNSW or IVF, 16,000 with product quantization on DiskANN (vector-search "Features and limitations", half-precision, product-quantization and limitations pages).
  - Build order: HNSW can be created on an empty collection; IVF after loading because `numLists` depends on document count; product quantization after the collection has data; a new index can return empty results for 2 to 3 minutes while it builds (vector-search HNSW column, product-quantization note, quickstart-nodejs-select-algorithm Troubleshooting).
  - One vector index per vector path; the quickstart's "same kind on the same field" comment is imprecise (vector-search features list and the limitations page).
  - `listIndexes` reports the options under `cosmosSearch` (vector-search, "Get vector index definitions").
  - The error for a same-name index with different options, and whether an identical `createIndexes` call is a no-op, are undocumented and not an SME item; the ensure-index helper is described as tolerant of either outcome (DECISIONS.md, "Not an SME item").
- HNSW dimension limit (former Open question 1): answered by the product owner on 2026-11-25; 2,000 uncompressed and 4,000 with half-precision for HNSW and IVF, 16,000 only with product quantization on DiskANN, is correct, and the select-algorithm quickstarts' 8,000 figure is wrong and must be changed in `ai/includes/choosing-algorithm.md` and `.github/copilot-instructions.md` of Azure-Samples/documentdb-samples; an engine test on 2026-11-25 rejected a half-precision HNSW index with 4,001 dimensions ("field cannot have more than 4000 dimensions for vector index") and accepted 4,000 (DECISIONS.md, Vector indexes, "Answered by the product owner").
- Tier split in the starting-parameters table (part of former Open question 3): HNSW and DiskANN need M30 or higher, so IVF on M10/M20 and HNSW/DiskANN on M30+ is right; the limitations page's free-tier line ("HNSW ... M40+") and `quickstart-agent-nodejs`'s "DiskANN M40 or higher" are stale (limitations page vector-search section; release note 2025-07-15; DECISIONS.md, Full-text and hybrid search, "Cost and tiers", and topic 13 Learn fixes).
- Full-text search preview status (former Open question 4): still in preview, not GA; `$text` and classic text indexes are GA; enablement is self-serve (portal Settings > Features > Full-text search > Enable, or Azure CLI/Bicep/Terraform PATCH of `previewFeatures` adding `FullTextSearch`), then wait 10 minutes; `CommandNotSupported` 115 "Search index creation is not supported yet" was observed when `createSearchIndexes` ran against a cluster without the preview enabled and is undocumented on Learn (full-text-search-overview, dated 2026-11-04 and updated 2026-11-17; DocumentDB blog post 2026-11-17; run 07 events.jsonl; DECISIONS.md, Full-text and hybrid search).

## Open questions

1. [needs SME confirmation] IVF above one million documents: the vector-search IVF field table says `numLists` = sqrt(documentCount) above 1M; the Important box under it says to use DiskANN instead. Which is right? This filing follows the Important box.
2. [needs SME confirmation] What values, if any, should the "small production" and "production" tuning columns in the starting-parameters table use? The tier split itself (IVF on M10/M20, HNSW and DiskANN on M30+) is settled, see Resolved.

## Source drafts

- 072-vector-search-cookbook-copy-paste-cosmossearch-createindexes.md
- 043-vector-search-page-lacks-an-embedding-model-to-dimensions-ta.md
- 125-vector-search-storage-and-operational-guidance-number-format.md
