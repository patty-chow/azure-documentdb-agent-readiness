# Documentation and tooling gaps: 07-mortgage-application-multi-agent

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Programmatic vector-index creation and dimension mapping

- **What was missing:** No programmatic example or idempotent seed step that creates a DocumentDB vector index with cosmosSearchOptions matching the chosen embedding model dimension.
- **Where the agent looked:** Repo README and seed.js; Microsoft Learn vector-search docs were discovered in practice discovery but the sample did not use them.
- **Effect on this build:** The sample leaves vector-index creation manual; embedding-based features and $search/cosmosSearch examples were not demonstrated. This prevents agents or other authors from running an end-to-end semantic search demo without extra manual steps.
- **Suggested fix (sample_or_quickstart):** Add a 'Create vector index' section to the seed script or a separate script that: (1) reads EMBEDDING_MODEL (or EMBEDDING_DIM) from env, (2) constructs a createIndexes command with cosmosSearchOptions: { kind: 'vector-hnsw'|'vector-ivf'|'vector-diskann', dimensions: <dims>, similarity: 'COS' }, and (3) calls db.runCommand({ createIndexes: 'applications', indexes: [...] }) idempotently (check for existing index name). Also add a README subsection with recommended parameter values for small/demo datasets and a table explaining how to adjust lBuild/lSearch/numLeaves for larger datasets.

## [high] Search endpoint behavior and error handling

- **What was missing:** No /search endpoint; no validation for empty queries; no error handling for embedding provider failures; search results (if added) would not include similarity scores.
- **Where the agent looked:** Repo files and README; no /search route implemented.
- **Effect on this build:** Search-related checklist items (error cases and returning similarity scores) are unimplemented, so the sample cannot show vector/semantic search behavior or demonstrate robust error handling for production-like usage.
- **Suggested fix (sample_or_quickstart):** Add an Express route POST /search that: validates non-empty query (returns 400 with clear message), requests embeddings in try/catch and returns 500 with a helpful message on failure, runs cosmosSearch $search, and returns hits with their similarity score. Provide unit tests that mock the embedding provider and the DB.

## [medium] Retry/backoff helper and sample usage

- **What was missing:** Although connection options (retryReads) are set, the app lacks a bounded exponential-backoff retry wrapper for transient errors and handling of 429 throttling.
- **Where the agent looked:** documentdb-connection skill and reliability docs; src/db.js and pipeline.js show no retry wrapper around operations.
- **Effect on this build:** Without bounded retries the sample may not demonstrate resilience to transient network or throttling errors; builders copying the sample may leave production apps vulnerable to repeated failures.
- **Suggested fix (agent_kit_rule):** Ship a small helper (library function) 'withRetries(operationFn, options)' that implements bounded exponential backoff, inspects error codes for transient errors and 429, and allows callers to wrap DB operations. Include an example in seed.js and pipeline.js showing usage.

## [medium] Entra ID (MONGODB-OIDC) vs native user guidance

- **What was missing:** README does not document Microsoft Entra ID/OIDC authentication or when to use it vs native DB users; sample only demonstrates DOCUMENTDB_URI usage.
- **Where the agent looked:** Repo README and src/db.js; documentdb-security skill notes Entra ID support.
- **Effect on this build:** Authors may not realize the more secure Entra ID option is available or how to configure it; sample encourages connection-string secrets rather than managed identities.
- **Suggested fix (learn_doc):** Add a 'Authentication' subsection to README with (1) example SRV strings for SCRAM-SHA-256 and for MONGODB-OIDC (Entra ID), (2) brief steps to configure Entra ID, and (3) when to prefer Entra ID or native users for the sample scenario.

## [medium] LangChain example artifact

- **What was missing:** The starter prompt asked for a LangChain multi-agent sample but the repository implements module-based agents and does not include LangChain wiring or examples (prompts, tools, chains, or MultiAgentChain).
- **Where the agent looked:** Repo files and package.json; no 'langchain' dependency or LangChain constructs are present.
- **Effect on this build:** An agent looking for a canonical Node.js LangChain multi-agent example will not find a literal LangChain usage; the sample is a LangChain-style architecture but not LangChain code.
- **Suggested fix (sample_or_quickstart):** Either add LangChain as a dependency and implement the agents as LangChain Tools/Agents or make README explicit that this is a LangChain-style sample (not using the LangChain library).

## [low] Driver-version pinning discoverability

- **What was missing:** While package-lock.json exists, the sample did not explicitly call out the exact mongodb driver version tested against DocumentDB or recommend 'npm ci' for reproducible installs.
- **Where the agent looked:** Repo package.json and package-lock.json; Microsoft quickstarts note 'tested driver versions'.
- **Effect on this build:** Authors might install a different driver version via non-deterministic installs and encounter compatibility differences; reproducibility could be improved.
- **Suggested fix (discoverability):** Add one line in README: 'This sample was tested with mongodb X.Y.Z; use npm ci to reproduce the exact dependency tree (package-lock.json included).'

## [low] IaC snippet for mongoClusters

- **What was missing:** No infrastructure-as-code snippet using Microsoft.DocumentDB/mongoClusters is bundled in the sample to create the cluster (the environment provided a cluster).
- **Where the agent looked:** Repo root and README
- **Effect on this build:** Users who want to reproduce the full stack cannot do so from this sample alone; they'd need to author their own Bicep/ARM/Terraform template.
- **Suggested fix (mcp_tool_or_description):** Add a minimal Bicep or ARM example that creates a low-cost M10/M20 mongoCluster with variables for region and tier, and document policy/cost warnings.

