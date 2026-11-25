# Documentation and tooling gaps: 18-sanctions-list-screening-agent

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Embedding model & embedding-dimension guidance

- **What was missing:** No public DocumentDB guidance tells a sample which embedding model/provider to pick or which embedding dimension to use; the sample must assume a model (the builder chose OpenAI text-embedding-3-small / 1536).
- **Where the agent looked:** Searches for 'embedding model dimensions DocumentDB' and the vector-search docs; installed skills were consulted (documentdb-vector-search).
- **Effect on this build:** The build committed to 1536 dims and created an index with dimensions=1536. If a user picks a different embedding model, index creation or queries may fail or return errors (dimension mismatch).
- **Suggested fix (agent_kit_rule):** Agent-kit rule: 'Samples MUST set EMBEDDING_MODEL and EMBEDDING_DIM in .env.example and use EMBEDDING_DIM when creating vector indexes; if the embedding provider is unspecified, default to text-embedding-3-small with 1536 dims and document that this default is only for the sample.'

## [high] Index-creation idempotency and verification

- **What was missing:** No explicit public DocumentDB guidance on idempotent createIndexes handling (error semantics when index exists) surfaced in quick discovery; builder created a create-vector-index script but seed.py does not create or verify the index.
- **Where the agent looked:** Searches for 'createIndexes idempotent Azure DocumentDB' and review of createIndexes examples in vector-search docs.
- **Effect on this build:** The builder attempted the MCP automation, it failed, and they used a PyMongo createIndexes fallback. The repo now contains two separate steps (seed, create_index) which a user must run in order. This increases friction and risk of out-of-sync index parameters.
- **Suggested fix (agent_kit_rule):** A sample 'bootstrap' script that idempotently (a) creates the collection (if missing), (b) calls createIndexes with cosmosSearchOptions and handles 'index already exists' responses, and (c) waits/verifies index readiness via listIndexes or a helper; include a short code snippet showing the createIndexes payload and the check for existing index.

## [high] Regex vs full-text recommendations for fuzzy matching

- **What was missing:** The public docs do show createSearchIndexes and analyzers, but the sample relied on unprefiltered regex searches without a documented mitigation in README. Guidance that an agent could use to prefer createSearchIndexes (edgeGram/ASCII-folding analyzers) over raw regex for large datasets should be surfaced.
- **Where the agent looked:** Full-text search docs and vector-search docs (learn.microsoft.com 'full-text search custom analyzers' and 'vector-search').
- **Effect on this build:** The app issues unbounded regex finds that could cause COLLSCAN on larger datasets; the sample's README does not warn users to create a text/search index or to prefilter, increasing the risk that a user will run costly queries in production.
- **Suggested fix (learn_doc):** A short README section: 'Avoid full-collection regex in production' with (1) an example of creating a createSearchIndexes text index with an edgeGram analyzer for name prefix matching, (2) show how to materialize a normalized_name field and index it, and (3) show the preferred pattern of prefiltering by country or partition key before running cosmosSearch.

## [high] Retry/backoff guidance and central policy

- **What was missing:** The sample lacks a centrally configured retry/backoff policy for DB or embedding calls; DocumentDB best-practices note retries and idempotency but a ready-to-use sample policy was not included.
- **Where the agent looked:** Reliability in Azure DocumentDB docs and retries best-practices pages.
- **Effect on this build:** Transient network or service errors (embedding API, DB aggregation) are not handled uniformly; this increases flakiness and exposes users to unhelpful 500s.
- **Suggested fix (agent_kit_rule):** Provide an 'http_db_retry' helper in the agent kit demonstrating exponential backoff + jitter for DB/HTTP calls (configurable via env: RETRY_MAX, RETRY_BASE_MS), and example usage in seed.py and app.py around network calls.

## [high] Infrastructure examples for mongoClusters resource type

- **What was missing:** The sample lacks an infra-as-code example targeting Microsoft.DocumentDB/mongoClusters. Readiness findings flagged confusion between databaseAccounts (Cosmos RU model) and mongoClusters (vCore-managed DocumentDB).
- **Where the agent looked:** ARM/Bicep templates and CLI docs (learn.microsoft.com searches found mongoClusters templates).
- **Effect on this build:** Without infra examples, builders may attempt to provision the wrong resource type (databaseAccounts) and create an incompatible cluster; this is a high-risk point for publishable samples.
- **Suggested fix (mcp_tool_or_description):** Add an infra/ folder with a minimal Bicep file that deploys Microsoft.DocumentDB/mongoClusters with parameters for tier/region, plus a README paragraph: 'This sample targets the vCore DocumentDB mongoClusters resource; do not use databaseAccounts.'

## [medium] README guidance for index parameter tuning & scaling

- **What was missing:** Although the vector index parameters are in code, README lacks a short explanation of what to change as data size grows (numLists, nProbes for IVF; m/efConstruction for HNSW; DiskANN when dataset becomes large) and how to change cluster tier.
- **Where the agent looked:** Vector search docs (learn.microsoft.com 'vector-search' and 'perform-vector-similarity-search').
- **Effect on this build:** Users may run the sample, then try to scale without understanding which parameters to change or when to increase cluster tier; they might pick incorrect parameters and run into memory limits or poor recall/latency.
- **Suggested fix (learn_doc):** Add a 'Tuning vector index parameters' README subsection that (a) explains m/efConstruction/efSearch/nlist/nProbes tradeoffs, (b) gives numeric examples for 200, 10k, 100k+ docs, and (c) shows how to change createIndexes JSON and when to prefer DiskANN and to scale the cluster tier (M30+).

## [medium] Embedding metadata & versioning guidance (prior-knowledge-only)

- **What was missing:** No DocumentDB-specific guidance was found to confirm or deny the pattern of storing embedding_model/embedding_version with each document and enforcing compatibility at query time.
- **Where the agent looked:** Searches for 'DocumentDB embedding_version per document' and similar queries returned no decisive guidance.
- **Effect on this build:** The sample does not store embedding version metadata. If users later change embedding model, older vectors and the index may become incompatible, causing subtle failures or poor matches.
- **Suggested fix (learn_doc):** A short doc page recommending storing embedding metadata (model name, version, timestamp) alongside embeddings, recommending a reindex/recompute workflow, and showing sample fields and a query-time guard.

## [medium] Agent-kit guidance: prefer createSearchIndexes and analyzers over raw regex

- **What was missing:** Although DocumentDB docs show custom analyzers, the agent-kit lacks a succinct recipe for building name-matching analyzers (lowerCase + asciiFolding + edgeGram) for sanctions lists.
- **Where the agent looked:** Full-text custom analyzers docs and the vector-search skill resources.
- **Effect on this build:** Builder used simple regex matching in the sample; a compact example in the agent-kit would have guided them to a more efficient approach and avoided full-collection scans.
- **Suggested fix (sample_or_quickstart):** Add a short sample showing createSearchIndexes JSON that defines a 'name-search' index using lowerCase + asciiFolding + edgeGram filters and an example $search query that uses the index for fuzzy/prefix matching.

