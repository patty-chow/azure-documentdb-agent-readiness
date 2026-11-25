# Documentation and tooling gaps: 14-hyper-personalized-content-engine

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Enable MCP management tools for automated index creation

- **What was missing:** A short note / automation flag explaining that the documentdb MCP server's management tools are disabled by default and must be enabled (ENABLE_MANAGEMENT_TOOLS=true) or an alternative management-plane method be used to create cosmosSearch indexes automatically.
- **Where the agent looked:** Events/logs (documentdb_create_index tool calls in events.jsonl) and documentdb-mcp-setup skill.
- **Effect on this build:** Index creation failed in this run (documentdb_create_index raised 'Management tools are disabled by default'), preventing server-side $search/knn verification and causing the sample to fallback to client-side ranking.
- **Suggested fix (mcp_tool_or_description):** Add a short 'MCP management tools' section to README and seed script: (1) explain the opt-in, (2) show how to set ENABLE_MANAGEMENT_TOOLS=true for MCP calls or show the equivalent portal/az CLI steps to create the cosmosSearch index, and (3) add a seed fallback that prints exact commands to run manually if the automated index creation fails.

## [high] Embedding & chat model defaults and dimensionality

- **What was missing:** Authoritative guidance on which embedding/chat provider and default embedding dimension to use for samples (so index dimensions can be set correctly).
- **Where the agent looked:** Readiness findings and documentdb-vector-search skill; general Microsoft Learn vector-search pages do not prescribe a default embedding model and dimension for sample apps.
- **Effect on this build:** Inconsistent defaults across scripts (384 vs 1536) created ambiguity and led to attempted index requests with inconsistent dimensions. This contributed to a fragile index-creation flow and risk of silent mismatch between embeddings and index dimensions.
- **Suggested fix (learn_doc):** A short policy page in the agent-kit: 'Default embedding & chat models for samples' that (a) recommends a default embedding provider & model (and its dims) for small samples (e.g., provide 'mock:384' or 'OpenAI text-embedding-3-small:1536' choices), (b) shows how to wire EMBEDDING_PROVIDER/EMBEDDING_DIM in .env.example and seed scripts, and (c) includes a snippet to validate stored embedding_dim before creating the index.

## [high] Agent-memory persistence guidance for samples

- **What was missing:** Practical example for storing agent memory (raw turns + summaries + embeddings) and using TTL for short-term memory in sample code.
- **Where the agent looked:** documentdb-data-modeling and documentdb-monitoring skill docs; no sample code in the repository demonstrates a full memory persistence pattern.
- **Effect on this build:** Agent memory was requested in the starter prompt but not implemented; a canonical example would have let the builder implement it correctly (TTL + summaries + embeddings).
- **Suggested fix (sample_or_quickstart):** Ship a short 'agent-memory' quickstart: code snippets that show (a) a document shape for raw_turns (with occurredAt and TTL index), (b) a summarization step that writes a long-term summary doc with embedding and embedding_dim, and (c) retrieval code to include memory summaries in the model prompt.

## [high] Document the management-plane vs data-plane createIndex limitations

- **What was missing:** A page explaining when createIndex via the MongoDB driver will be rejected and when the management plane (createSearchIndexes / MCP / portal) is required to create cosmosSearch indexes.
- **Where the agent looked:** documentdb-vector-search and MCP setup skill; no short, prominent note was found in the sample repository.
- **Effect on this build:** The driver createIndex attempt reported that cosmosSearch options were not accepted and MCP createIndex calls failed due to management-tools opt-in. Builders need guidance to pick the right path.
- **Suggested fix (discoverability):** Add a short 'Creating cosmosSearch indexes' note in the README clarifying: 'You may need portal / management-plane privileges for cosmosSearch indexes; driver createIndex may fail; use MCP/documentdb_create_index or portal when needed' plus a step-by-step example.

## [medium] Index-parameter tuning guidance & README examples

- **What was missing:** A concise README section explaining when to choose DiskANN/HNSW/IVF, the key parameters (lBuild/lSearch/maxDegree/m/numLists), and sample parameter choices for demo vs production data sizes.
- **Where the agent looked:** documentdb-vector-search skill resources and Microsoft Learn vector-search pages; the sample README did not include parameter tuning guidance.
- **Effect on this build:** The seed script selected vector-hnsw (reasonable), but README lacked instructions on tuning these parameters for larger datasets; operators may not know how to change index params when scaling-up.
- **Suggested fix (discoverability):** Add a 'Tuning the vector index' subsection to README with a short table: {small dataset → HNSW defaults; medium → DiskANN defaults with example lBuild/lSearch; very small → IVF example}, and show the exact createIndex/cosmosSearchOptions snippet with placeholders for parameters.

## [medium] Client-side rerank numeric guidance (fetch_k)

- **What was missing:** Authoritative numeric guidance on candidate-fetch sizes for client-side reranking in Azure DocumentDB context (there is no Microsoft Learn doc stating specific numeric ranges).
- **Where the agent looked:** Microsoft Learn vector search docs and the documentdb-vector-search skill; searches for '500-5000 candidates' returned no authoritative result (discovery notes).
- **Effect on this build:** The sample's in-process fallback scans the collection which is fine for tiny datasets but would not scale; lacking numeric guidance makes it hard for authors to pick safe defaults for larger demos.
- **Suggested fix (learn_doc):** A short example on when to use client-side rerank and suggested candidate sizes by embedding dimension and latency target (e.g., 'for demo sets <5k items use full-scan; for larger sets fetch_k 500–2000; prefer server-side $search otherwise').

## [medium] Infrastructure as code example (mongoClusters resource)

- **What was missing:** An example Bicep / Terraform snippet that deploys Microsoft.DocumentDB/mongoClusters with minimal parameters suitable for samples.
- **Where the agent looked:** documentdb-azure-deployment skill and Microsoft Learn; the sample repo contains no IaC files.
- **Effect on this build:** The run used an existing cluster. Without an IaC snippet, operators may copy wrong ARM types (databaseAccounts) and fail to create a correct cluster.
- **Suggested fix (sample_or_quickstart):** Provide a small 'infra' folder with Bicep and Terraform examples that create a mongoClusters resource (default to M30 and low-cost region), plus a note about not using databaseAccounts for this product.

## [low] Driver-version & wire-protocol compatibility guidance

- **What was missing:** A pinned driver-version recommendation and an explicit compatibility matrix for Node driver versions vs supported MongoDB wire protocol/version for Azure DocumentDB clusters.
- **Where the agent looked:** documentdb-driver skill, documentdb-azure-deployment resources; no single authoritative 'which driver version to pin' page was found in the sample kit.
- **Effect on this build:** The builder picked mongodb ^5.7.0 (which works) but the repo lacks explicit guidance about matching driver versions to cluster wire protocol versions; this could confuse builders choosing other driver majors.
- **Suggested fix (discoverability):** Add a short compatibility section to the driver skill README mapping recommended Node mongodb versions to DocumentDB supported wire protocol versions and include a pinned example in new sample templates.

