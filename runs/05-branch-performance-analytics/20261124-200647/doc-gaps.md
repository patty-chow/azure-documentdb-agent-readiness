# Documentation and tooling gaps: 05-branch-performance-analytics

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Embedding model & vector dimension

- **What was missing:** Public, sample-ready guidance that maps an embedding model name to the exact numeric dimension expected by DocumentDB vector indexes (example: text-embedding-3-small -> 1536 dims).
- **Where the agent looked:** Installed documentdb-vector-search skill and Microsoft Learn 'Integrated vector store' pages (events.jsonl searches).
- **Effect on this build:** Builder deferred vector index creation and implemented a lexical fallback. Without a clear model->dimension mapping an agent cannot safely create vector indexes (dimension mismatch causes errors).
- **Suggested fix (learn_doc):** A short 'Embedding model to vector-dimension mapping' page in the DocumentDB docs, listing common model names (OpenAI text-embedding-* family, provider equivalents) and the exact vector dimension to use when creating a DocumentDB vector index. Include an example createSearchIndexes payload using that dimension.

## [high] DocumentDB vector-index creation examples

- **What was missing:** Concrete, copy-paste examples showing the exact createIndexes/createSearchIndexes JSON payload for vector-hnsw / vector-diskann / vector-ivf, with parameters tuned for small-sample vs larger datasets.
- **Where the agent looked:** documentdb-vector-search skill and Microsoft Learn vector-search docs (events.jsonl).
- **Effect on this build:** Builder avoided implementing vector search to prevent producing an incorrect index. Agents will hesitate to create vector indexes without examples and tuned defaults.
- **Suggested fix (discoverability):** Add a cookbook page showing createSearchIndexes payloads for 'small sample' (e.g., sample_k=10k vectors), 'medium' and 'large' datasets and explain which parameters (numLists, maxDegree, lBuild, lSearch) to change and how. Include the model -> dimension mapping and an example script to create the index.

## [high] mongoClusters vs databaseAccounts naming & CLI

- **What was missing:** Clear, prominent note in quickstarts and agent guidance that the vCore-managed MongoDB clusters use resource type Microsoft.DocumentDB/mongoClusters and CLI group az documentdb mongocluster (not az cosmosdb), plus quick commands to list connection strings.
- **Where the agent looked:** Microsoft Learn (events.jsonl) and agent-kit readiness traces that showed confusion between databaseAccounts and mongoClusters.
- **Effect on this build:** If an agent or builder follows older Cosmos DB examples (databaseAccounts), they will create or target the wrong resource type and possibly fail to create the cluster or get a correct connection string for mongoClusters.
- **Suggested fix (naming_or_disambiguation):** Add a short 'Terminology and CLI mapping' section to the sample README and the documentdb agent skill: list canonical resource types (Microsoft.DocumentDB/mongoClusters), az CLI commands (az documentdb mongocluster list-connection-strings), and an example to retrieve the connection string.

## [medium] LangChain install / pydantic-core binary guidance

- **What was missing:** Clear install guidance for langchain and pydantic-core (how to avoid native build failures by using platform wheels, constrained versions, or enabling a prebuilt binary distribution).
- **Where the agent looked:** pip install traces in events.jsonl and readiness notes; no authoritative one-line recipe was found in the skill docs for avoiding pydantic native builds.
- **Effect on this build:** LangChain was intentionally not installed due to a pydantic-core native build failure and the builder implemented a local fallback. Without short install guidance, agents will remove LangChain from samples or produce fragile installs.
- **Suggested fix (discoverability):** A small 'Installing LangChain safely' note in the agent-kit: recommended langchain and pydantic-core pinned combinations that have prebuilt wheels for common platforms, and an alternate pip command example (e.g., pip install --only-binary=:all: pydantic-core) and CI hints.

## [medium] Endpoint hardening (rate-limit & auth) for expensive operations

- **What was missing:** Application-level guidance for protecting expensive endpoints (/summaries/refresh, /ask) including recommended auth patterns and rate-limiting libraries and defaults for samples.
- **Where the agent looked:** Installed skills and Microsoft docs; no DocumentDB-specific public guidance for protecting sample endpoints was found (P17 basis = prior_knowledge_only).
- **Effect on this build:** The sample exposes /summaries/refresh and /ask without auth or rate-limiting; an agent-built sample could be abused in a public gallery or by users running it without protection.
- **Suggested fix (agent_kit_rule):** An agent-kit rule: all gallery samples that execute expensive/long-running or LLM-backed operations must (a) require an API key or Entra ID auth for refresh endpoints, (b) return 401 when not authorized, and (c) include a default rate-limit configuration (requests/min) with code examples (e.g., FastAPI + slowapi).

## [medium] Local development gateway instructions

- **What was missing:** A compact local dev recipe (docker-compose or single docker run) and the exact connection string example (port 10260, TLS caveats) for running the DocumentDB gateway locally for offline tests and CI.
- **Where the agent looked:** documentdb-local-deployment skill and Microsoft Learn local gateway docs (events.jsonl).
- **Effect on this build:** Tests require DOCUMENTDB_URI; without local dev gateway instructions agents cannot author offline tests or CI that runs without a live cloud cluster.
- **Suggested fix (learn_doc):** A short local-dev page with a docker run command for the official DocumentDB gateway image, the example connection string (mongodb://user:pass@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true), and an example .env.example entry for local dev.

