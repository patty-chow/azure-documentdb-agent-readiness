# Documentation and tooling gaps: 20-provider-directory-semantic-search

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Enable/choose Microsoft Entra ID vs connection-string

- **What was missing:** README uses DOCUMENTDB_URI by default but does not document Microsoft Entra ID / OIDC as an alternative nor explain when to prefer it.
- **Where the agent looked:** documentdb security docs, readiness findings (Q06).
- **Effect on this build:** Sample defaults to static connection string, which is simpler but less secure for production. Builders may not realize Entra ID is available.
- **Suggested fix (discoverability):** Add an 'Optional: Use Microsoft Entra ID (OIDC)' subsection to README with: how to enable MicrosoftEntraID in cluster authConfig, sample mongodb+srv connection string parameters for MONGODB-OIDC, and a link to the 'Connect to Azure DocumentDB using role-based access control' doc.

## [high] Index tuning & query-time knobs

- **What was missing:** README mentions the HNSW index but gives no guidance on tuning m/efConstruction/efSearch for larger datasets or how to change them in seed.py.
- **Where the agent looked:** documentdb-vector-search skill and vector search docs.
- **Effect on this build:** Seed script uses conservative defaults appropriate for demo; users may not know how to adapt them for larger datasets, risking poor recall or excessive build time if copied unchanged.
- **Suggested fix (learn_doc):** An 'Index tuning' section in README: explain m/efConstruction semantics, suggested presets for demo/10k/100k+ vectors, how to change DIMS and algorithm in seed.py, and an example of how to run a small recall vs latency experiment.

## [high] Retry/backoff and honoring Retry-After

- **What was missing:** The public quickstarts and sample did not include a small retry utility or example showing how to honor Retry-After (x-ms-retry-after-ms) for both DocumentDB queries and external embedding APIs.
- **Where the agent looked:** Optimize throughput and Retry-After docs; events show no retry implementation in code.
- **Effect on this build:** Sample has no retry/backoff; a user copying the sample into production may experience 429 throttling and unbounded retries or poor resilience.
- **Suggested fix (agent_kit_rule):** Add a small retry helper in the agent-kit: a decorator that implements exponential backoff with jitter and reads Retry-After/x-ms-retry-after-ms headers; include example usage around seed/createIndexes and around embedding provider calls.

## [high] Projection to exclude embeddings

- **What was missing:** Quickstart sample code examples often demonstrate returning entire documents which include embeddings; the best-practice of projecting out embedding vectors before returning results is not prominent.
- **Where the agent looked:** documentdb-vector-search skill and sample code.
- **Effect on this build:** The sample's API response schema excludes embedding, but the aggregation pipeline still retrieves and transports the embedding from the server, causing unnecessary RU and bandwidth cost.
- **Suggested fix (learn_doc):** Add a short note and code snippet to the vector-search quickstart showing $project usage that excludes the embedding field (e.g., { $project: { score: { $meta: 'searchScore' }, name: 1, specialty: 1, languages: 1, insurance: 1 } }).

## [high] Local guidance for LlamaIndex/OpenAI installs

- **What was missing:** Pip dependency resolution pitfalls for llama-index/openai combinations are common; the sample's README mentions optional LlamaIndex but there is no tested extras/install recipe that guarantees compatibility.
- **Where the agent looked:** events.jsonl shows repeated pip resolver failures when attempting to install llama-index; agent attempted several version pins.
- **Effect on this build:** Builder removed llama-index from runtime to make the sample runnable. Users following the README might still fail to install llama-index if versions are not specified precisely.
- **Suggested fix (discoverability):** Provide an explicit 'Optional: install LlamaIndex and OpenAI' section in README that pins a tested set of versions (e.g., llama-index==0.14.26, openai==1.8.0) and includes a virtualenv/constraints file and a note about incompatibilities with older Python versions; include a small 'tox' or CI job that verifies the extras install.

## [high] Missing IaC sample for mongoClusters

- **What was missing:** The sample lacks a Bicep/Terraform example showing how to create an Azure DocumentDB mongoClusters resource; quickstarts confuse databaseAccounts vs mongoClusters in other docs.
- **Where the agent looked:** readiness_findings and template docs (learn.microsoft.com) indicate Microsoft.DocumentDB/mongoClusters is the correct resource type.
- **Effect on this build:** No IaC was included; teams copying the sample may attempt to use the wrong resource type and fail to provision cluster properties needed for vector search.
- **Suggested fix (sample_or_quickstart):** Add a minimal Bicep file (or Terraform) that creates Microsoft.DocumentDB/mongoClusters with parameters (sku, region, storage) and a short note: 'Use this only with approval — the demo uses an existing cluster.'

## [medium] When to shard vs single-shard for samples

- **What was missing:** No short guidance in quickstarts/agent-kit rules explaining when a small sample should avoid sharding vs when to demonstrate a shard key, and no advice recorded in skills that a builder would find automatically.
- **Where the agent looked:** documentdb-sharding skill and readiness findings; events show the builder used model_default for this decision (D006).
- **Effect on this build:** Builder used a model_default choice to keep the sample single-shard. This is acceptable for a tiny demo but leaves ambiguity for builders who might copy the sample into production IaC without a shard decision.
- **Suggested fix (learn_doc):** A short 'Sharding guidance for samples' page in the Vector Search quickstart: 1) When dataset <100k docs prefer single-shard for simplicity; 2) Provide example shard-key choices (e.g., tenantId or hashed userId) and a small example Bicep snippet for a sharded collection; 3) Link to the documentdb-sharding skill for deep guidance.

## [medium] Embedding metadata (model & dims)

- **What was missing:** No explicit demonstration of storing embeddingModel/embeddingDims metadata with documents in the quickstart sample, making it harder to track model drift.
- **Where the agent looked:** documentdb-vector-search guidance and agent-kit resources.
- **Effect on this build:** Sample uses a consistent embedding size but does not record metadata per-document; future reindexing or drift detection would be harder.
- **Suggested fix (discoverability):** Add a one-paragraph recommendation in the vector-search quickstart and a code snippet: store embeddingModel, embeddingDims and embeddingVersion fields in each document at ingest time.

## [medium] Public guidance on multi-document transactions (prior_knowledge_only)

- **What was missing:** The public docs do not state a clear recommendation about avoiding multi-document transactions for vector-search read-heavy paths (the agent's prior knowledge came from other MongoDB practices).
- **Where the agent looked:** search for transaction guidance and change-stream docs; discovered_practices flagged K22 as prior_knowledge_only.
- **Effect on this build:** The sample does not use transactions; however, builders relying on MongoDB memory might either overuse transactions or avoid them unnecessarily. Agents have no authoritative guidance to rely on.
- **Suggested fix (learn_doc):** A short FAQ entry: when to use multi-document transactions in Azure DocumentDB, trade-offs for read-heavy vector-search workloads, and example code recommending single-document upserts for ripple-safe ingest.

