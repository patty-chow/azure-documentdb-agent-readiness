---
title: "Vector search page: add an embedding-model-to-dimensions table, make the number[] storage rule unambiguous, and give complete starting index payloads by collection size"
repo: learn-docs
type: learn-feedback
status: ready_with_edits
priority: P1
sample_count: 61
findings: 88
bucket: learn-information_gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Vector search page: add embedding-model-to-dimensions guidance, an unambiguous number[] storage rule, and complete starting index payloads by collection size

**Page:** https://learn.microsoft.com/en-us/azure/documentdb/vector-search (source: `azure/documentdb/vector-search.md` in MicrosoftDocs/nosql-docs-pr)
**Also cross-link from:** `quickstart-nodejs-vector-search` (and the other language vector-search quickstarts), `build-rag-applications`, the Azure OpenAI integration page.

## What happens today

The page explains `vector-ivf`, `vector-hnsw` and `vector-diskann`, their tuning knobs and defaults, the dimension limits (2,000 uncompressed; 4,000 with half-precision on HNSW/IVF; 16,000 with product quantization on DiskANN), a vector-count / cluster-tier table at the top of "Perform vector similarity search" (IVF under 10,000 on M10/M20; HNSW up to 50,000 on M30+; DiskANN, recommended, 500,000+ on M30+), and a "Filtered vector search" section. It does not:

1. Name any embedding model or its output size. The only pointers are generic links to "Azure OpenAI embeddings" and "Hugging Face on Azure", and every code sample uses 3-dimensional toy vectors. The language quickstarts (for example `quickstart-nodejs-vector-search`) do use `text-embedding-3-small` with `EMBEDDING_DIMENSIONS=1536`, but the concept page agents land on never links model to `dimensions`, and no page lists other common models.
2. Show, on this page, how to produce a real embedding and write it to a document as a `number[]`. (The quickstarts do this, but inside a large multi-file app and without a length check.)
3. State the storage rule clearly. The DiskANN field table and the IVF "Important" box both say: "Vectors must be a `number[]` to be indexed ... A vector using another type, such as `double[]`, prevents the document from being indexed." Read literally, that says an array of doubles (which is exactly what every driver produces from a float list) is *not* indexable. The real non-indexable case, a BSON `Binary` of packed float bytes, is never named.
4. Give a complete starting payload per index kind tied to the size table. The size/tier table gives no parameters; the small-demo hint (`numLists: 1`) is only in the IVF tab; HNSW and DiskANN defaults (m=16 / efConstruction=64 / efSearch=40; maxDegree=32 / lBuild=50 / lSearch=40) are only in parameter tables. The page's own DiskANN example uses `lBuild: 64` and the Node quickstart uses `maxDegree: 20, lBuild: 10`, so a reader sees three different "starting" values.
5. Say which similarity metric to use for which model normalisation, or suggest environment variable names for the embedding provider on this page.

## Why it matters

In an experiment that ran gpt-5-mini through a readiness quiz and a build over 100 Azure DocumentDB sample prompts (with the DocumentDB Agent Kit skills and the DocumentDB, Azure and Learn MCP servers), this was the single largest information gap: **88 readiness findings across 61 of the 100 samples** (RAG, semantic search, KYC, churn, catalog, analytics). The common thread: "the Learn vector-search docs explain how to create the index but not which model or dimension to use."

Concrete effects on the generated samples:

- Of 187 build decisions about the embedding model or dimensions, **97 (52%) were made from model priors** (`reason_source=model_default`), not from the docs or the prompt. `text-embedding-3-small` / 1536 was picked 77 times, with no concept-page text to cite.
- `runs/04-medical-imaging-metadata-store/20261124-193446/02-readiness.json`: the cold answer for "how should embeddings be stored" was `Binary(struct.pack('<' + 'f'*dim, *vec))`. Grounding corrected it to `number[]`, but the agent then logged the `double[]` sentence as a gap because it could not tell whether a float array is allowed.
- `runs/01-product-catalog-with-vector-search/20261125-061803/app/utils.py`: the built app returns `Binary(arr.tobytes())` for the `embedding` field, so the cosmosSearch index would not index those documents. The audit (`05-audit.json`) marked the storage requirement `partly_met`.
- `runs/20-identity-resolution-multi-agent/20261124-210002/05-audit.json`: `DIM = 1536` hardcoded with no runtime check; changing the model env var silently mismatches the index.
- `runs/13-product-q-a-chatbot-rag/20261124-184527/doc-gaps.md` asks for a short "choose an embedding model and set EMBEDDING_DIM" cookbook.
- Env var names drifted across the 111 generated `.env.example` files: `EMBEDDING_DIMS` (11), `EMBEDDING_DIM` (6), `EMBEDDING_DIMENSIONS` (2), `EMBED_DIMENSIONS` (1); `EMBEDDING_MODEL` (20) vs `OPENAI_EMBEDDING_MODEL` (10) vs `EMBED_MODEL` (1). The quickstarts already use `AZURE_OPENAI_EMBEDDING_MODEL` / `EMBEDDING_DIMENSIONS`, but agents did not find them from the concept page.

## Proposed change

Two new H2 sections on `vector-search.md`, placed before "Perform vector similarity search", plus a wording fix in two places. Documentation only; no index behaviour changes.

### Section 1: "Choose an embedding model and set `dimensions`"

**a. Model table.** Lead with: "`dimensions` must equal the length of the vectors your embedding model returns. Common values:"

| Provider / model | Default output dimensions | `dimensions` to pass |
|---|---|---|
| Azure OpenAI / OpenAI `text-embedding-3-small` (used by the vector-search quickstarts) | 1536 (can be reduced with the `dimensions` request parameter) | 1536 |
| Azure OpenAI / OpenAI `text-embedding-3-large` | 3072 (can be reduced) | 3072, or the reduced value |
| Azure OpenAI / OpenAI `text-embedding-ada-002` | 1536 (fixed) | 1536 |
| Sentence-Transformers `all-MiniLM-L6-v2` | 384 | 384 |
| OpenAI CLIP ViT-B/32 (image + text) | 512 | 512 |

Add: "If you request a smaller `dimensions` from the embedding API, create the index with that smaller value." And: "3,072 is above the 2,000-dimension uncompressed limit, so `text-embedding-3-large` at full size needs `compression: \"half\"` on HNSW or IVF (up to 4,000) or DiskANN with product quantization (up to 16,000)", linking the existing half-precision and product-quantization pages.

**b. Short Python and Node snippets** that call Azure OpenAI, store the result as a plain array, and assert the length once at startup. Use the same environment variable names as the vector-search quickstarts and keyless (Microsoft Entra ID) auth, consistent with them:

```python
# Python (openai>=1.x, azure-identity, pymongo)
import os
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI

token_provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
client = AzureOpenAI(azure_endpoint=os.environ["AZURE_OPENAI_EMBEDDING_ENDPOINT"],
                     azure_ad_token_provider=token_provider,
                     api_version=os.environ["AZURE_OPENAI_EMBEDDING_API_VERSION"])
DIMENSIONS = int(os.environ["EMBEDDING_DIMENSIONS"])  # 1536 for text-embedding-3-small

def embed(text: str) -> list[float]:
    vec = client.embeddings.create(model=os.environ["AZURE_OPENAI_EMBEDDING_MODEL"], input=text).data[0].embedding
    assert len(vec) == DIMENSIONS, f"model returned {len(vec)} dims, index expects {DIMENSIONS}"
    return vec  # a plain list of floats; do NOT pack into bson.Binary

collection.insert_one({"title": title, "embedding": embed(title), "embeddingModel": "text-embedding-3-small"})
```

```javascript
// Node (openai, @azure/identity, mongodb) - client created as in quickstart-nodejs-vector-search
const vec = (await client.embeddings.create({ model: process.env.AZURE_OPENAI_EMBEDDING_MODEL, input: text })).data[0].embedding;
if (vec.length !== DIMENSIONS) throw new Error(`model returned ${vec.length} dims, index expects ${DIMENSIONS}`);
await collection.insertOne({ title, embedding: vec, embeddingModel: "text-embedding-3-small" }); // number[], not Binary
```

**c. Rewrite the storage rule** (the DiskANN field table and the IVF "Important" box) to:

> Store the vector as an array of numbers (`[0.12, -0.04, ...]`). Documents whose vector field holds any other BSON type, for example a `Binary` of packed float32 bytes, are stored but not indexed and aren't returned by a vector search. If your embeddings arrive as bytes or a NumPy array, convert them with `.tolist()` (Python) or `Array.from()` (Node) before inserting.

The current "such as `double[]`" wording should be removed; an array of doubles is exactly what a reader should store.

**d. Similarity note.** One sentence: "Use `COS` for text-embedding models that return unit-normalised vectors (OpenAI and Azure OpenAI embeddings do; check your model's documentation), for which `COS` and `IP` produce the same ranking; use `L2` when the model's documentation recommends Euclidean distance. The metric is set at index creation; to change it, drop and re-create the index."

**e. `.env` block**, matching the names the vector-search quickstarts already use, so samples converge on one convention:

```ini
# Azure DocumentDB (Microsoft Entra ID; no password in the file)
MONGO_CLUSTER_NAME=
# Embedding provider (Azure OpenAI, keyless)
AZURE_OPENAI_EMBEDDING_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-3-small
AZURE_OPENAI_EMBEDDING_API_VERSION=
EMBEDDING_DIMENSIONS=1536
```

### Section 2: extend the existing size/tier table with "Starting parameters"

Rather than adding a second table, add two columns ("Starting index parameters", "Query-time") to the existing IVF / HNSW / DiskANN table at the top of "Perform vector similarity search", using the page's own documented defaults, and state: "These are starting points; tune with your own recall measurements."

| Vector count (existing row) | Index | Starting parameters | Query-time |
|---|---|---|---|
| Under 10,000, M10/M20 | `vector-ivf` | `numLists: 1` for a demo (exact search); then `documentCount/1000` | `nProbes: 1` (default) |
| Up to 50,000, M30+ | `vector-hnsw` | `m: 16`, `efConstruction: 64` (defaults) | `efSearch: 40` (default; raise for recall) |
| 500,000+ (recommended at any scale), M30+ | `vector-diskann` | `maxDegree: 32`, `lBuild: 50` (defaults) | `lSearch: 40` (default), must be >= `k` |

Then give one complete `createIndexes` payload per kind with realistic `dimensions` (1536) that also creates the standard index for a filter field, for example:

```javascript
db.runCommand({
  createIndexes: "products",
  indexes: [
    { name: "products_embedding", key: { embedding: "cosmosSearch" },
      cosmosSearchOptions: { kind: "vector-hnsw", m: 16, efConstruction: 64, similarity: "COS", dimensions: 1536 } },
    { name: "products_category", key: { category: 1 } }   // standard index required to prefilter on category
  ]
});
```

Repeat the page's existing rule next to these payloads: "To use prefiltering, define a standard index on every property you pass in `cosmosSearch.filter`, in addition to the vector index." Add: "If a workload only needs exact matches, ranges or sorting, it needs ordinary indexes, not a vector index." Align the DiskANN example (`lBuild: 64`) and the Node quickstart (`maxDegree: 20, lBuild: 10`) with the stated defaults, or say why they differ. Cross-link the hybrid-search how-to for fusion defaults instead of restating them here.

## Evidence (run folders from the experiment; no connection strings)

- `runs/04-medical-imaging-metadata-store/20261124-193446/02-readiness.json` - confusions S01, S03, S04 and the "Embedding storage precision vs index method" gap.
- `runs/01-product-catalog-with-vector-search/20261125-061803/app/utils.py`, `05-audit.json` - vectors written as BSON `Binary`; storage requirement `partly_met`.
- `runs/13-product-q-a-chatbot-rag/20261124-184527/doc-gaps.md` - request for an "embedding model + index-dimension" cookbook.
- `runs/20-identity-resolution-multi-agent/20261124-210002/doc-gaps.md`, `05-audit.json` - hardcoded DIM=1536, no runtime check, no tuning guidance.
- `runs/10-drug-formulary-semantic-search/20261124-194440/doc-gaps.md` - model and dims chosen as `model_default` for lack of a documented default.

## Verification

### 1. Already covered? partially_covered

- https://learn.microsoft.com/en-us/azure/documentdb/vector-search (fetched 2026-11-25, git commit 5cbb02e7): names no embedding model; all examples use `dimensions: 3`. Storage rule reads "Vectors must be a `number[]` to be indexed ... A vector using another type, such as `double[]`, prevents the document from being indexed." (DiskANN field table and IVF Important box). Defaults are documented in parameter tables: `maxDegree` "default is 32", `lBuild` "default is 50", `lSearch` "default value is 40", HNSW `m` "16 by default", `efConstruction` "64 by default", `efSearch` "40 by default", `nProbes` "default value of 1"; IVF demo hint "start with `numLists` set to 1". The page already HAS a vector-count / recommended-tier table (IVF under 10,000 on M10/M20; HNSW up to 50,000 on M30+; DiskANN up to 500,000+ on M30+) and a "Filtered vector search" section saying "To use prefiltering, you first need to define a standard index on the property you want to filter by". The original draft said the only small-corpus hint was in the IVF tab; corrected to extend the existing table instead of adding a new one.
- https://learn.microsoft.com/en-us/azure/documentdb/quickstart-nodejs-vector-search: uses `text-embedding-3-small`, `.env` with `AZURE_OPENAI_EMBEDDING_MODEL`, `AZURE_OPENAI_EMBEDDING_ENDPOINT`, `EMBEDDING_DIMENSIONS=1536`, keyless auth, and creates standard indexes alongside the vector index. So model/dims and env names ARE documented for one model, but only in the quickstart, not on the concept page, with no multi-model table and no length check. The draft's `.env` block (which used `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`) was changed to the quickstart's names and keyless auth.
- https://learn.microsoft.com/en-us/azure/documentdb/half-precision: half-precision is HNSW/IVF, max 4,000; PQ is DiskANN, max 16,000.
- Agent kit (not the target): `skills/vector-search/vector-create-diskann-index.md` and `vector-normalize-embeddings.md` use 1536 / text-embedding-3-small in examples but have no model-to-dims table.
- Net: model-to-dims table, unambiguous Binary-vs-array rule and complete per-kind starting payloads are not on Learn.

### 2. Premise true? confirmed (with wording corrections applied)

- Vectors must be number[]; BSON binary vectors are not indexed: matches the facts given for this review and the page's own rule. The `double[]` phrasing is genuinely confusing (BSON has no separate double-array type; a float list from any driver is an array of doubles).
- Model output sizes: text-embedding-3-small 1536, text-embedding-3-large 3072, ada-002 1536, all-MiniLM-L6-v2 384, CLIP ViT-B/32 512 (public model documentation); text-embedding-3 models accept a `dimensions` request parameter.
- Limits: 2,000 uncompressed, 4,000 half-precision (HNSW/IVF), 16,000 PQ (DiskANN) per vector-search and half-precision pages.
- Size/tier rows taken from the page's existing table; the draft's "50,000 and above" for DiskANN was changed to the page's wording (recommended; 500,000+).
- Removed an unverified claim from the draft ("without [a filter index] the filter is applied after the ANN search and can return fewer than k results"); replaced with the page's documented rule that a standard index is required for prefiltering.
- Softened "the metric cannot be changed after index creation" to "set at index creation; drop and re-create to change", and "never returned by `$search`" to "aren't returned by a vector search" (page wording).
- Noted that OpenAI embeddings are unit-normalised so COS and IP rank identically (OpenAI embeddings FAQ); qualified with "check your model's documentation".

### 3. Maintainer skeptic: confirmed

Names one page and source file (`azure/documentdb/vector-search.md`), quotes the exact confusing sentence and gives replacement text, specifies a table, two short snippets and payloads that reuse the page's own defaults and the quickstart's env names. It is Azure DocumentDB specific (cosmosSearch, dimension limits, number[] rule), documentation-only, and backed by 88 findings in 61 samples plus one built sample that would silently not index. A docs maintainer would accept it, possibly trimming the snippets to a link to the quickstart.

## Finding ids

- F0013
- F0051
- F0052
- F0083
- F0086
- F0122
- F0123
- F0189
- F0224
- F0228
- F0432
- F0506
- F0507
- F0566
- F0610
- F0611
- F0612
- F0641
- F0643
- F0670
- F0735
- F0737
- F0773
- F0774
- F0776
- F0805
- F0862
- F0897
- F0980
- F0984
- F1012
- F1172
- F1175
- F1209
- F1235
- F1273
- F1309
- F1346
- F1497
- F1533
- F1599
- F1602
- F1634
- F1692
- F1728
- F1732
- F1801
- F1841
- F1930
- F1995
- F2095
- F2197
- F2255
- F2258
- F2298
- F2335
- F2369
- F2399
- F2468
- F2469
- F2527
- F2562
- F2565
- F2601
- F2720
- F2818
- F2851
- F2885
- F2918
- F2951
- F2987
- F2989
- F3049
- F3051
- F3081
- F3121
- F3154
- F3157
- F3188
- F3236
- F3237
- F3269
- F3332
- F3369
- F3370
- F3372
- F3469
- F3472
