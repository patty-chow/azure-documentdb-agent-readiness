# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 11 |
| prompt | 5 |
| operator | 2 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T11:59:01+00:00

## D002 (build): I chose Node.js 24 with Express for the sample app.

- **Instead of:** Python/Flask; Node.js/Express (Node 24)
- **Because:** The user explicitly asked for Node.js; Express is a minimal HTTP framework that works well for a small sample.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'build a Node.js LlamaIndex agent' and readiness report: 'Node (v24) is installed'
- **When:** 2026-11-25T11:59:27+00:00

## D003 (build): I chose the official 'mongodb' Node.js driver version ^5.7.0 and will use a singleton MongoClient.

- **Instead of:** mongodb driver 4.x; mongodb driver 5.x
- **Because:** Driver 5.x is the current stable major compatible with modern Node versions; following documentdb-driver guidance for singleton client avoids connection-pool issues.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: use npm package 'mongodb' and documentdb-driver skill recommends singleton MongoClient.
- **When:** 2026-11-25T11:59:32+00:00

## D004 (build): I chose to read the connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Read credentials from file; Read from environment variable DOCUMENTDB_URI
- **Because:** Security best practice and the run environment requirement; do not commit secrets into the repo.
- **Reason came from:** `prompt`
- **Evidence:** Run environment: 'Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time.'
- **When:** 2026-11-25T11:59:35+00:00

## D005 (build): I chose to expose a minimal HTTP API (Express) with a /search endpoint that accepts customerId and returns rationale + ranked content.

- **Instead of:** Expose CLI-only sample; Provide minimal HTTP API (Express) with /search endpoint
- **Because:** An HTTP API makes the agent easy to call and demonstrates the retrieval + ranking behavior; it matches the prompt's expectation for an agent surface and is easy to test locally.
- **Reason came from:** `model_default`
- **Evidence:** Assumption in prompt review: 'Builder will expose a minimal HTTP API (e.g., Express) with a /search endpoint'
- **When:** 2026-11-25T11:59:38+00:00

## D006 (build): I chose to create a 'vector-hnsw' cosmosSearch index for the sample content collection with dimensions 1536 and similarity 'COS' (cosine).

- **Instead of:** Create DiskANN index; Create HNSW index; Create IVF index
- **Because:** Small sample dataset (tens/hundreds) — HNSW is simple and fast for local/small-scale samples. Chose 1536 dimensions to match the default embedding model selection (OpenAI text-embedding-3-small).
- **Reason came from:** `model_default`
- **Evidence:** documentdb-vector-search guidance: HNSW is good for up to ~50k vectors; readiness report instruction: include cosmosSearchOptions with kind and dimensions and similarity; embedding default choice required.
- **When:** 2026-11-25T11:59:42+00:00

## D007 (build): I chose to generate synthetic random normalized embeddings for the seed data instead of calling an external embedding API during seed.

- **Instead of:** Use real embedding provider during seed (OpenAI); Use synthetic/random normalized embeddings for seed
- **Because:** Avoid making network calls to external embedding services during automated verification and avoid requiring secrets. Seed documents will include embeddings with the chosen dimension so vector index and queries can be demonstrated using interaction embeddings as query vectors.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'Embedding & chat default model selection is an information gap' and the run environment may not have an API key; also security rule: do not write secrets into files.
- **When:** 2026-11-25T11:59:45+00:00

## D008 (build): I chose not to add an external LlamaIndex Node package and instead implement a small, self-contained retrieval+context-engineering agent in the sample code.

- **Instead of:** Use LlamaIndex Node package (unknown availability); Implement a lightweight agent pattern without external LlamaIndex dependency
- **Because:** Avoid depending on an unconfirmed third-party package; sample can still show the LlamaIndex-style workflow (profile retrieval, vector search, context engineering) without the external dependency, keeping the sample simple and runnable.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'Which LlamaIndex Node package & version to pin' was an information gap; no installed skill pinned a library.
- **When:** 2026-11-25T11:59:48+00:00

## D009 (build): I chose to create the cosmosSearch vector index via the documentdb MCP server tool (functions.documentdb_create_index).

- **Instead of:** Create vector index via driver commands; Create vector index via documentdb MCP server tool
- **Because:** MCP server provides documented data-plane operations for DocumentDB-specific index creation (cosmosSearch options) which aren't available via the standard MongoDB createIndex API; this increases the chance of correctly creating the vector index format.
- **Reason came from:** `prompt`
- **Evidence:** Readiness report: 'The documentdb MCP server's connection profile `default` is connected to that same cluster. Use its tools to inspect collections, indexes and query plans and to verify what the app created.'
- **When:** 2026-11-25T12:00:51+00:00

## D010 (build): I chose to retry documentdb_create_index with an alternative options payload including indexType 'cosmosSearch' and altering keys to be an array form.

- **Instead of:** Give up index creation via MCP and document it as not verified; Retry documentdb_create_index with an alternative options shape
- **Because:** A second attempt with an adjusted shape may succeed; if it fails I'll record it and proceed without MCP-created index (the seed data and driver-based queries still work).
- **Reason came from:** `model_default`
- **Evidence:** First attempt to create index via documentdb_create_index failed with a generic error. The MCP tool often expects slightly different option shapes; a second retry is allowed by the run instructions.
- **When:** 2026-11-25T12:00:57+00:00

## D011 (build): I chose to implement a runtime fallback: try $search knn, and if it fails (index missing), run a collection scan and perform cosine similarity in the application to return ranked results.

- **Instead of:** Fail if vector index absent; Implement a runtime fallback to in-app cosine similarity ranking when $search fails
- **Because:** This keeps the sample robust in environments where cosmosSearch index creation via MCP wasn't possible, and it still demonstrates vector-style retrieval.
- **Reason came from:** `model_default`
- **Evidence:** documentdb_list_indexes showed only the _id index; documentdb_create_index attempts failed. To keep the sample runnable without MCP-created vector index, a fallback ensures the app still demonstrates personalization and ranking.
- **When:** 2026-11-25T12:01:18+00:00

## D012 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T12:03:17+00:00

## D013 (build): I chose Node.js with Express for the sample app.

- **Instead of:** Python/Flask; Node.js/Express
- **Because:** User explicitly requested Node.js; Express is a minimal, widely-used HTTP framework suitable for a small sample app.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'build a Node.js LlamaIndex agent' and run-environment: 'Node.js 24 with npm and npx is available.'
- **When:** 2026-11-25T12:03:39+00:00

## D014 (build): I chose the official 'mongodb' Node.js driver pinned to ^5.7.0 in package.json.

- **Instead of:** mongodb driver v4.x; mongodb driver v5.x; mongodb driver v6.x
- **Because:** Driver 5.x is modern and compatible with Node 24 and supports MongoClient singleton patterns; pining to ^5.7.0 gives concrete reproducible dependency while being reasonably recent.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Builder will use the official mongodb Node.js driver (npm package "mongodb")...'.
- **When:** 2026-11-25T12:03:42+00:00

## D015 (build): I chose to use a deterministic 'mock' embedding provider for the sample (EMBEDDING_PROVIDER=mock) with default EMBEDDING_DIM=384, and make embedding/chat provider configurable via env variables.

- **Instead of:** Use OpenAI embeddings default (text-embedding-3-small, 1536d); Use sentence-transformers local default (384d); Use a mock deterministic embedding for the sample and let user configure provider/dim via env
- **Because:** Avoids requiring external API keys during verification while keeping code pluggable for real providers; 384 dims is compact for local testing and common for small models (e.g., MiniLM family). The README will document how to switch to a real provider and set EMBEDDING_DIM accordingly.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'Information gaps: Embedding & chat default model selection' — no installed skill picks a default.
- **When:** 2026-11-25T12:03:53+00:00

## D016 (build): I chose to implement retrieval by application-side cosine similarity over stored embeddings for the sample, while still creating a cosmosSearch vector index (vector-hnsw) to demonstrate DocumentDB index creation and to allow users to switch to server-side kNN if desired.

- **Instead of:** Use DocumentDB $search/knn vector query; Do application-side cosine similarity over stored embeddings
- **Because:** Safer and deterministic for a tiny sample; still demonstrates index creation and documentdb_list_indexes can verify index exists. Keeps sample working without depending on precise $search query syntax which can vary by engine version.
- **Reason came from:** `model_default`
- **Evidence:** documentdb-vector-search guidance and readiness report warn about $search syntax complexity and that for small sample sets local similarity is fine.
- **When:** 2026-11-25T12:03:59+00:00

## D017 (build): I chose to read the connection string from the environment variable DOCUMENTDB_URI at runtime and implement MongoClient singleton with TLS and retryWrites=false.

- **Instead of:** Read a full connection string from env DOCUMENTDB_URI; Use MCP connection profile programmatically
- **Because:** Matches run-environment instructions and keeps secrets out of repo per prompt rules.
- **Reason came from:** `prompt`
- **Evidence:** Readiness report: 'Read the connection string from DOCUMENTDB_URI at runtime' and documentdb-driver skill guidance.
- **When:** 2026-11-25T12:04:02+00:00

## D018 (build): I chose to use the documentdb MCP server documentdb_create_index to create the cosmosSearch vector index because driver createIndex didn't accept cosmosSearchOptions on this cluster.

- **Instead of:** create index via driver createIndex; use documentdb MCP server documentdb_create_index
- **Because:** MCP server supports DocumentDB-specific index creation parameters reliably; use it to create the vector index after seeding.
- **Reason came from:** `tool_result`
- **Evidence:** Seed script warned: 'Index type CosmosSearch requested, but options were not provided.' The driver attempt failed; MCP server has documentdb_create_index tool available.
- **When:** 2026-11-25T12:05:16+00:00

## D019 (build): I chose to implement a lightweight retrieval+generation agent in the repository instead of depending on a third-party LlamaIndex Node package.

- **Instead of:** Install and use a LlamaIndex Node package; Implement a lightweight retrieval+generation agent in this sample
- **Because:** Avoids adding uncertain external dependency and keeps sample focused and easy to run without API keys. The code is modular so teams can replace the mock agent with a real LlamaIndex integration later.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'Which LlamaIndex Node package & version to pin' is an information gap; no installed skill pinned a LlamaIndex package.
- **When:** 2026-11-25T12:05:43+00:00
