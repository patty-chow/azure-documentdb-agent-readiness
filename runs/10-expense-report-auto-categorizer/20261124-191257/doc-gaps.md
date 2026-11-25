# Documentation and tooling gaps: 10-expense-report-auto-categorizer

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Embedding model & index dims guidance

- **What was missing:** No public guidance (or sample instruction) provided to pick an embedding model and its output dimensionality; the sample therefore avoided creating any vector indexes.
- **Where the agent looked:** installed skills (documentdb-vector-search) and Microsoft Learn; readiness search queries for 'LLM and embeddings model choice & embedding dimension' returned no prescriptive default.
- **Effect on this build:** Vector indexes were not created; embedding-based features were disabled to avoid creating indexes with wrong dimensionality.
- **Suggested fix (learn_doc):** A short 'Embeddings & Vector Index' page that: 1) recommends a set of embedding models (OpenAI text-embedding-3-small/large or an Azure OpenAI mapping), 2) lists their output dimensions, 3) shows the createIndex JSON with 'dimensions' and a recommended DiskANN/HNSW/IVF template, and 4) documents how to change parameters for larger datasets. Include an example environment variables snippet (EMBEDDING_MODEL, EMBEDDING_DIM) and a small script that creates the matching vector index.

## [high] Beanie + Motor + PyMongo tested pins

- **What was missing:** No canonical tested version matrix (exact package micro-versions) for Beanie + Motor + PyMongo against Azure DocumentDB MongoDB 7.0.
- **Where the agent looked:** installed skills (documentdb-driver) and Microsoft Learn; no authoritative pinned combos were found.
- **Effect on this build:** The builder used constrained ranges and made small compatibility decisions (pydantic v1 constraint). Without exact pins, language/runtime dependency mismatches required iterative fixes during the build.
- **Suggested fix (learn_doc):** A small compatibility page showing a tested matrix of exact package versions (Beanie, Motor, PyMongo, Pydantic) that are known to work against MongoDB 7.0 wire protocol and a minimal reproduction snippet for init_beanie + AsyncIOMotorClient. Include CI-tested constraints and how to reproduce the import-time errors.

## [high] Agent memory persistence guidance (TTL + deterministic fallback)

- **What was missing:** No public guidance on whether and how to persist ephemeral agent/session memory in Azure DocumentDB (schema for TTL, versioning, deterministic fallback flags).
- **Where the agent looked:** documentdb-vector-search, documentdb-data-modeling, ad-hoc web searches (see readiness 'searches_with_no_useful_result').
- **Effect on this build:** The builder chose an in-process SessionMemory and implemented a deterministic fallback option, but there is no documented recommended pattern for storing short-lived memory with TTL nor a standard deterministic-fallback flag for replayable tests.
- **Suggested fix (naming_or_disambiguation):** A guidance page titled 'Agent Memory Patterns for Azure DocumentDB' describing: schema for decisions collection (merchant, category, decided_at, schema_version, model_id, ttl_seconds), examples for ephemeral TTL indexes, and a deterministic_fallback boolean flag to allow deterministic offline tests (example: deterministic_fallback: true in runtime config). Include sample Beanie Document model and example seed/cleanup scripts.

## [high] Idempotent processing pattern (atomic claim)

- **What was missing:** A short example demonstrating atomic claim semantics (findOneAndUpdate/processing_status or optimistic concurrency) for worker pipelines that process 'submitted' documents exactly-once.
- **Where the agent looked:** Microsoft Learn optimistic concurrency docs and installed skills; no sample code snippet for the exact 'claim-and-process' pattern was present in the sample or docs used by the builder.
- **Effect on this build:** The sample processes documents by reading and then saving them; this can lead to double-processing on concurrent runs or retries. The builder left idempotent-claim logic unimplemented.
- **Suggested fix (sample_or_quickstart):** Add a short sample 'claim-and-process' function showing findOneAndUpdate({'status':'submitted'}, {'$set':{'status':'processing','locked_at':now}}, return_document=...) followed by processing and finally an atomic update to 'processed' or revert on failure. Include a note on optimistic concurrency (etag/_etag) and a small unit test that simulates concurrent workers.

## [medium] Search endpoint and similarity-score examples

- **What was missing:** No example /search API showing error handling for empty/failed embeddings and no example of returning similarity scores with results.
- **Where the agent looked:** project repo and installed skills (vector-search), and general web search (no single authoritative sample surfaced that fits the sample's shape).
- **Effect on this build:** Search features were omitted from the sample; if the gallery author wants search, they must implement standard error handling and ensure scores are surfaced.
- **Suggested fix (sample_or_quickstart):** Add a FastAPI example /search route that: 1) returns 400 when query is empty, 2) calls embedders behind a try/except and returns a clear 502/500 on embed failure, and 3) returns items with a similarity_score float. Provide an example unit test mocking the embedder and vector query to assert error handling.

## [medium] Unit tests that run offline (mock Motor/Beanie)

- **What was missing:** A small test harness and examples showing how to mock Motor/Beanie so tests run without a live DocumentDB instance.
- **Where the agent looked:** repo and installed skills; no test fixtures included in this sample.
- **Effect on this build:** No tests exist; CI and verification rely on the live cluster. This reduces the sample's portability for contributors without cloud access.
- **Suggested fix (sample_or_quickstart):** Add pytest-asyncio tests and a utilities file demonstrating monkeypatching AsyncIOMotorClient or injecting a fake client, plus one deterministic unit test for classify_item using the deterministic fallback. Document how to run tests locally without a cloud account.

## [medium] IaC example for mongoClusters

- **What was missing:** No Bicep/Terraform example using the Microsoft.DocumentDB/mongoClusters resource type to create a DocumentDB cluster.
- **Where the agent looked:** repo and Microsoft Learn; the readiness findings highlight the common confusion between older databaseAccounts and new mongoClusters resource types.
- **Effect on this build:** The sample left out infrastructure-as-code; authors following older samples might create the wrong resource type.
- **Suggested fix (sample_or_quickstart):** Add a Bicep snippet to the repo demonstrating Microsoft.DocumentDB/mongoClusters with parameters for tier and storage, defaults that minimize cost for samples, and a short note advising users to prefer existing clusters where available.

## [medium] Dependency pinning guidance

- **What was missing:** A recommended exact pinset or a constraints file tested by CI for the combination Beanie+Motor+PyMongo+Pydantic that this sample uses.
- **Where the agent looked:** repo and installed skills; developer notes indicated runtime import issues that required constrained ranges.
- **Effect on this build:** The builder used constrained ranges rather than exact pins, which left potential for installation-time surprises; import-time errors were encountered in early iterations.
- **Suggested fix (learn_doc):** Provide a small 'Dependencies & Pins' document listing exact versions tested in CI (e.g., pydantic==1.10.12, beanie==1.19.1, motor==3.1.2, pymongo==4.4.0) and a short note how to regenerate pins (pip-compile or poetry lock).

