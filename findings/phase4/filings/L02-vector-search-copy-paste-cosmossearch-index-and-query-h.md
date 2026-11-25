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
open_questions: 6
---

# Vector search: copy-paste cosmosSearch index and query how-to, explicit number[] storage rule and embedding-dimensions table

**Pages:** https://learn.microsoft.com/azure/documentdb/vector-search (source `azure/documentdb/vector-search.md`, MicrosoftDocs/nosql-docs-pr), plus the `quickstart-*-vector-search`, `quickstart-*-select-algorithm` and `full-text-search-hybrid` pages.

## What happens today

The vector-search content is accurate but not usable as a starting point:

- `vector-search.md` (TOC "Vector database") is a ~5,000-word concept article. The `createIndexes` templates sit inside DiskANN/HNSW/IVF tabs and all use 3-dimensional toy vectors. There is no Node code, no idempotent create, and no tuning guidance beyond IVF `numLists`.
- **The storage rule is ambiguous.** It appears only in a DiskANN field-table cell and an IVF-tab "Important" box: "Vectors must be a `number[]` to be indexed ... A vector using another type, such as `double[]`, prevents the document from being indexed." An array of doubles is exactly what every driver sends, and the real failure case, BSON Binary (packed float32, typed arrays), is never named.
- **No page lists an embedding model and its dimensions.** The quickstarts hardcode `text-embedding-3-small` / 1536. The concept page links only generically to Azure OpenAI and Hugging Face.
- **Nothing says which command builds a vector index.** `createSearchIndexes` (the full-text search command) is not mentioned on the page, so readers cannot tell that vector indexes always use `createIndexes` with `cosmosSearchOptions`.
- The quickstarts drop and recreate the index on every run and project `document: "$$ROOT"`, so the full vector is returned with every hit. They use DiskANN `maxDegree: 20, lBuild: 10` (the minimums), while the concept page documents defaults of 32/50 and its own example uses `lBuild: 64`.
- No guidance on per-document embedding metadata, re-embedding after a model change, or inserting documents while the embedder is unavailable.

## Why it matters

In one experiment run, an AI coding agent (gpt-5-mini with the DocumentDB Agent Kit skills and the DocumentDB, Azure and Learn MCP servers) built 100 Azure DocumentDB sample apps. **71 of the 100 samples** logged a vector-search documentation gap (200 distinct findings: 99 + 88 + 13 across the three drafts, no shared ids). The three source drafts counted 54, 61 and 12 samples, and their samples overlap. 71 is a recount of distinct samples from the experiment's findings file. All counts come from one run and may shift on a re-run.

What the agent did:

- Stored embeddings as BSON Binary. The inserts succeeded, but those documents never appeared in vector results. A Binary query vector failed with `BadValue: ... expected an array type field`.
- Called `createSearchIndexes` for a vector index, got `CommandNotSupported` (115), and fell back to client-side cosine over every document. Other samples used Atlas `knnBeta` syntax.
- Skipped vector indexing entirely (11 samples) or hardcoded 1536 with no length check, because no page ties a model to `dimensions`. Of 187 model or dimension decisions, 97 came from model priors, not from documentation.
- Created indexes with parameters it could not explain (about 20 samples), and returned whole vectors in API responses.
- Tried the DocumentDB MCP `documentdb_create_index` tool, got "Management tools are disabled by default", and had no short driver-only recipe to fall back to (8 samples). This refusal comes from the MCP server's opt-in setting as configured in this run, not from the service.
- Invented its own environment-variable names (`EMBEDDING_DIMS`, `EMBEDDING_DIM`, `EMBED_DIMENSIONS`, `OPENAI_EMBEDDING_MODEL`, ...) because the concept page does not point to the names the quickstarts use.

## Proposed change

### 1. New how-to page: `azure/documentdb/how-to-create-vector-index.md`

Title: "Create a vector index and run a similarity query" (`ms.topic: how-to`). TOC: under *Vector search*, after *Vector database*. If the team prefers fewer pages, this can instead be a "Copy-paste recipe" section at the top of `vector-search.md`. The page should be mostly code, with Python and Node tabs:

- A short "How to store vectors" callout at the top (same text as the storage rule in section 2), plus: for `similarity: "COS"`, L2-normalize vectors at ingest if the model does not already return unit-length vectors; only one vector index per vector path; half-precision (`compression: "half"`, HNSW and IVF) and product quantization (DiskANN) are index options, not a storage format you choose in your documents.
- A dimension probe and an `embed()` helper in Python and Node: call Azure OpenAI with keyless Microsoft Entra ID auth, assert `len(vector) == EMBEDDING_DIMENSIONS` once at startup, and insert the returned list unchanged (not wrapped in BSON Binary). Use the env names the quickstarts already use, and show them as a `.env` block with names only and no secrets: `AZURE_OPENAI_EMBEDDING_ENDPOINT`, `AZURE_OPENAI_EMBEDDING_MODEL`, `AZURE_OPENAI_EMBEDDING_API_VERSION`, `EMBEDDING_DIMENSIONS`.
- An idempotent `ensure_vector_index` function. It reads `listIndexes`, returns if an index on the path already has the same `cosmosSearch.kind` and `dimensions`, raises an error if the spec differs (only one vector index per path is allowed), and otherwise runs `createIndexes` with `key: {embedding: "cosmosSearch"}` and `cosmosSearchOptions` for one of `vector-diskann`, `vector-hnsw` or `vector-ivf`. It needs only the driver and the standard connection string from the quickstarts, with no portal, CLI or MCP step. Also create an ordinary index on each pre-filter field (the page's existing prefiltering rule), and add: "If a workload only needs exact matches, ranges or sorting, it needs ordinary indexes, not a vector index."
- A query: `$search: {cosmosSearch: {path, vector, k, lSearch | efSearch | nProbes, filter}}`, then an inclusion `$project` of the needed fields plus `score: {$meta: "searchScore"}`. Note: "Don't project `$$ROOT`. It returns the full vector, about 12 KB per hit at 1,536 dimensions."
- A starting-parameters table, based on the page's documented defaults, extending the existing vector-count/tier table. IVF on M10/M20: `numLists: 1` for demos, then `documentCount/1000`, `nProbes: 1`. HNSW on M30+: `m: 16`, `efConstruction: 64`, `efSearch: 40`. DiskANN on M30+: `maxDegree: 32`, `lBuild: 50`, `lSearch: 40` (and `lSearch` >= `k`). Add: "Raise query-time values before you rebuild; rebuilding is the expensive step. Verify with `explain()` that the `$search` stage uses the index. Size capacity by vCore tier and memory." Add "small production" and "production" columns only after the product team signs off.
- An error table. `CommandNotSupported` 115 means `createSearchIndexes` was used, so use `createIndexes`. `BadValue` "expected an array type field" means a Binary or object vector, so pass an array. `knnBeta`/`$vectorSearch` is Atlas syntax, so use `cosmosSearch`. A document missing from results has a vector that isn't an array or has the wrong length. No results right after creation means the index may still be building, so retry instead of recreating [needs SME confirmation]. "Management tools are disabled by default" from the DocumentDB MCP server is that server's opt-in setting, not a service limit, so use the driver snippet.
- Next steps: hybrid BM25 + vector with RRF (`full-text-search-hybrid`), the half-precision and product-quantization pages, and a short LangChain snippet that builds the `AzureDocumentDBVectorSearch` store from the same model and `dimensions` variables and the same `kind`/`similarity`, ending in `.as_retriever(search_kwargs={"k": 5})`.

### 2. Edits to `vector-search.md`

- **Storage rule.** Replace both `number[]` notes with one callout above the DiskANN/HNSW/IVF tabs: "Store each vector as an array of numbers (a JavaScript `number[]` or a Python `list[float]`). Documents whose vector field holds another BSON type, for example a Binary of packed float32 bytes or a typed array, are stored but not indexed, and aren't returned by vector search. Convert bytes or NumPy arrays with `.tolist()` (Python) or `Array.from()` (Node) before you insert." Remove the `double[]` example.
- **New H2, "Choose an embedding model and set `dimensions`"**, before *Perform vector similarity search*. Lead sentence: "`dimensions` must equal the length of every vector you insert." Then this table:

  | Model | Output dimensions |
  |---|---|
  | Azure OpenAI / OpenAI `text-embedding-3-small` | 1536 (reducible with the `dimensions` request parameter) |
  | `text-embedding-3-large` | 3072 (above the 2,000 uncompressed limit: use `compression: "half"` on HNSW/IVF, up to 4,000, or DiskANN with product quantization, up to 16,000, or request fewer dimensions) [needs SME confirmation: HNSW/IVF limits, see Open question 2] |
  | `text-embedding-ada-002` | 1536 |
  | `all-MiniLM-L6-v2` | 384 |
  | CLIP ViT-B/32 | 512 |

  Add: "If you request a smaller `dimensions` from the embedding API, create the index with that smaller value." And: "Use `COS` for text-embedding models that return unit-normalized vectors (OpenAI and Azure OpenAI embeddings do; check your model's documentation), for which `COS` and `IP` give the same ranking. Use `L2` when the model's documentation recommends Euclidean distance. The metric is set at index creation; to change it, drop and re-create the index."
- **Which command.** Add: "Vector indexes are created with `createIndexes` and a `cosmosSearch` key. `createSearchIndexes` is for full-text search and doesn't create vector indexes."
- **New short section, "Operating embeddings,"** after *Get vector index definitions*. Store `embeddingModel`, `embeddingDimensions` and `embeddingVersion` on each document (plus chunk size and token count for RAG chunks), and never mix models in one collection. When the model changes, re-embed, then drop and recreate the index with the new `dimensions`. If the embedder is down, insert the document without the vector and with `embeddingPending: true`, then backfill. Such documents are left out of vector results until then.
- Link the new page from *Perform vector similarity search* and from *LLM orchestration tools* (to the LangChain snippet). Also cross-link it from `build-rag-applications` and the Azure OpenAI integration page.

### 3. Consistency fixes

- The `quickstart-*-select-algorithm` pages give 8,000 dimensions for HNSW. `vector-search.md` and `half-precision.md` give 2,000 uncompressed and 4,000 with half-precision. Make all pages state one number [needs SME confirmation: which limit is correct, see Open question 2].
- `vector-search.md`'s own DiskANN example uses `lBuild: 64`, while the page documents a default of 50. Use the default or say why the example differs.
- In `quickstart-*-vector-search`, use the DiskANN defaults or add a comment that `maxDegree: 20, lBuild: 10` are minimums sized for a demo. Link the new page from Next steps, in both the `quickstart-*-vector-search` and `quickstart-*-select-algorithm` pages.
- In `full-text-search-hybrid.md`, replace the code comment "See vector-search.md" with a link to the new page.

## Evidence

- `runs/01-product-catalog-with-vector-search/20261125-061803/app/utils.py` and `05-audit.json`: vectors written as BSON Binary; the storage requirement was marked `partly_met`.
- `runs/11-visual-similarity-search-image-embeddings/20261124-184225/events.jsonl`: `BadValue` on a Binary query vector.
- `runs/07-voice-of-customer-sentiment-hub/20261124-204049/events.jsonl`: `createSearchIndexes` used for a vector index, then a client-side fallback.
- `runs/03-substitute-product-finder/20261124-183232/app/app/routes.py`: Atlas `knnBeta` payload.
- `runs/04-regulatory-reporting-orchestration/20261124-200545/doc-gaps.md`: vector search dropped for lack of a model-to-dimensions mapping.
- `runs/10-support-ticket-rag-assistant/20261124-204529/05-audit.json`: the agent asked what metadata to store per vector and how to reindex.
- `runs/08-regulatory-compliance-rag-checker/20261124-190949/events.jsonl`: MCP management tools disabled; the agent needed a driver-only path.

## Open questions

1. [needs SME confirmation] Is the behavior for non-array vectors as described: a document with a BSON Binary or typed-array vector is stored but silently not indexed, and a Binary query vector returns `BadValue`?
2. [needs SME confirmation] What are the HNSW and IVF dimension limits and defaults? The quickstarts say 8,000 for HNSW. The concept and half-precision pages say 2,000 uncompressed and 4,000 with half-precision (HNSW/IVF), and 16,000 with product quantization (DiskANN). Please also confirm `efConstruction` >= 2*`m`, `nProbes` <= `numLists`, and the M10/M20 versus M30+ tier guidance.
3. [needs SME confirmation] What values should the "small production" and "production" tuning columns use, if any?
4. [needs SME confirmation] Is full-text search (`createSearchIndexes`, the `FullTextSearch` cluster feature) still in preview? The error-table wording depends on this.
5. [needs SME confirmation] Retryable writes: draft 072 says the snippet needs `retryWrites=false` on the connection, and the canonical connection string sets it. Other drafts from this experiment disagree on why. Some say retryable writes are unsupported and cause write errors. Others say Learn makes no such claim. What should the docs say about whether retryable writes are supported and why `retryWrites=false` is set?
6. [needs SME confirmation] Can a newly created vector index return empty results while it builds, and for how long?

## Source drafts

- 072-vector-search-cookbook-copy-paste-cosmossearch-createindexes.md
- 043-vector-search-page-lacks-an-embedding-model-to-dimensions-ta.md
- 125-vector-search-storage-and-operational-guidance-number-format.md
