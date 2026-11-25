# Documentation and tooling gaps: 11-visual-similarity-search-image-embeddings

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Exact vector index creation syntax

- **What was missing:** An authoritative example of the exact createIndex/create_index call (JSON keys and option names) that this Azure DocumentDB cluster accepts for IVF/HNSW/DiskANN vector indexes.
- **Where the agent looked:** Local repository files (app/db.py, seed.py, README.md) and the run environment; external documentation search was not available in this run.
- **Effect on this build:** The seed script attempted a plausible create_index but the server rejected the option names. No vector-ivf index could be programmatically created/verified during the build; server-side search could not be fully validated.
- **Suggested fix (mcp_tool_or_description):** Ship a short 'How to create a vector index' page in the agent kit showing an exact pymongo/python snippet that creates an IVF index on field 'embedding' with dims=512 and a minimal set of vendor-accepted options. Include sample server responses for common errors and a snippet that lists indexes (list_indexes) to verify success. Also add an example CLI/mongosh snippet.

## [high] Aggregation API differences ($search vs $vectorSearch)

- **What was missing:** Public guidance distinguishing the supported aggregation stage(s) or command for server-side vector KNN queries in this DocumentDB product (e.g., whether to use $search/cosmosSearch, $vectorSearch, or vendor-specific stage names and the exact query shape).
- **Where the agent looked:** Repository and run environment; external docs not reachable from this run.
- **Effect on this build:** The builder implemented $vectorSearch aggregation as a best-effort and logged server-side failures; without authoritative examples the sample cannot reliably demonstrate server-side visual search on all clusters.
- **Suggested fix (discoverability):** Add a short 'Vector search query examples' doc that shows both the $search/cosmosSearch and $vectorSearch variants (with example pymongo aggregator pipeline payloads) and guidance on how to test them interactively (mongosh) and what error messages to expect.

## [high] DOCUMENTDB_URI canonical form & auth options

- **What was missing:** A canonical example of the DOCUMENTDB_URI string format (host suffix, port, required query params) and the supported authentication modes (connection-string SCRAM vs Microsoft Entra ID data-plane flows).
- **Where the agent looked:** Local repo (.env.example and README) and run environment; external docs not available in this run.
- **Effect on this build:** The sample correctly reads DOCUMENTDB_URI from the environment, but builders may guess a legacy Cosmos-style connection string and get connection errors if the cluster expects a different format or Entra-based flow.
- **Suggested fix (discoverability):** Add an 'Auth & connection string' page to the agent kit with: (A) canonical DOCUMENTDB_URI examples with placeholders; (B) a note about Entra/AD options if supported and how to obtain tokens for pymongo if the product supports it; (C) example pymongo connect snippet.

## [high] Idempotent index creation & verification

- **What was missing:** A rule or example showing how to create vector indexes idempotently: check list_indexes, adapt to existing index params, and verify after creation.
- **Where the agent looked:** app/db.py and seed.py; external docs not reachable.
- **Effect on this build:** ensure_vector_index attempts create_index with guessed keys and relies on catching exceptions. Because the server rejected the attempt, no verification path was available to adapt to the server's accepted syntax.
- **Suggested fix (agent_kit_rule):** Add an agent-kit rule: 'When creating vector indexes: call list_indexes, if desired index absent then attempt create_index with candidate option-sets, and after create call list_indexes again to verify. Log server error and the server's accepted option keys.' Include a short code snippet implementing the rule.

## [medium] Embedding metadata guidance

- **What was missing:** Advice on whether to store per-document metadata indicating embedding_dim and dtype (embedding_dim=512, embedding_dtype='float32') or where to store collection-level schema info.
- **Where the agent looked:** Repository and run environment; no external docs reachable.
- **Effect on this build:** The sample omits per-document embedding metadata. This risks silent mismatches if multiple encoders or dimensionalities are used when seeding or later updating documents.
- **Suggested fix (learn_doc):** Add a short note to the data-model docs recommending storing embedding_dim and embedding_dtype on documents or in a dedicated schema document and include a seed script check that validates vector length before insert/upsert.

## [medium] Retry/backoff best practices

- **What was missing:** Guidance and a small example for exponential-backoff retries with jitter for transient DocumentDB errors and recommended driver-level retry settings.
- **Where the agent looked:** Repository (no retries found) and run environment; no external docs reachable.
- **Effect on this build:** The sample does not implement retries; transient network hiccups could cause operations to fail in the wild and the sample's seed and query code offer no guidance to builders.
- **Suggested fix (learn_doc):** Publish a short 'Retries & backoff' guidance page with code examples (a retry decorator with jitter, recommended pymongo options) and a note on idempotency considerations (which operations may be retried safely).

## [low] Monitoring & index build guidance

- **What was missing:** Guidance or example instrumentation to emit vector-search-specific metrics (index size, index build time, ANN memory/IO, query latency) and notes about scheduling index builds during maintenance windows.
- **Where the agent looked:** Repository and run environment; no external docs reachable.
- **Effect on this build:** No instrumentation is present in the sample. For production use, lack of monitoring guidance increases the risk of unobserved cost/latency issues during index builds or large queries.
- **Suggested fix (learn_doc):** Add a short 'Monitoring & index-build' page describing what to monitor (index size, build time, query latency), example metrics to emit, and recommended scheduling/backoff for large index builds.

## [low] Decisions recorded from model defaults

- **What was missing:** When the builder used model-default assumptions (e.g., selecting a CLIP model or generating placeholder images) the run did not have authoritative local docs to confirm the choice.
- **Where the agent looked:** decisions.jsonl and the repository; no external docs reachable.
- **Effect on this build:** These model-default choices are reasonable but should be surfaced in kit docs so future builders understand the rationale and alternatives (e.g., what CLIP variant to choose).
- **Suggested fix (discoverability):** In the agent kit README, add a short 'default choices' section explaining the chosen CLIP model (openai/clip-vit-base-patch32), why placeholders were used, and where to change them. Mark these as defaults not requirements.

