# Documentation and tooling gaps: 18-chargeback-dispute-multi-agent

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Embedding model & index dimension guidance

- **What was missing:** There is no authoritative guidance in the sample or the prompt about which embedding model to use and therefore what vector-dimension to create in DocumentDB indexes. The builder intentionally omitted vector-index creation to avoid dimension mismatches.
- **Where the agent looked:** Repository README, seed script, and discovered Azure DocumentDB vector quickstarts (agent discovery).
- **Effect on this build:** The builder omitted vector index creation and semantic search from the default sample; users who add embeddings may create indexes with incorrect 'dimensions' and break semantic search.
- **Suggested fix (learn_doc):** A short documentation page: 'Choosing an embedding model and matching DocumentDB vector index dimensions' that explains (a) recommended example model(s) (e.g., OpenAI text-embedding-3-small => 1536 dims), (b) environment variable mapping (EMBEDDING_MODEL, EMBEDDING_DIM), (c) how to parameterize seed/index creation, and (d) a sample createIndexes payload for cosmosSearchOptions showing dimensions and algorithm defaults.

## [high] Vector-index create snippet

- **What was missing:** An exact, copy-paste seed/createIndexes example using the DocumentDB 'cosmosSearch' index spec and cosmosSearchOptions (kind, dimensions, method) so builders don't invent incompatible knn syntax.
- **Where the agent looked:** Repository and DocumentDB vector docs.
- **Effect on this build:** Absent; would have allowed the seed script to create vector indexes that work on the live cluster.
- **Suggested fix (sample_or_quickstart):** Add to the documentdb-vector-search skill and to the sample's seed script a parameterized createIndexes JSON (example for vector-ivf and vector-hnsw) with placeholders for dimensions, M/efConstruction, and a CLI flag to create or skip vector indexes.

## [high] Retry and throttling guidance for samples

- **What was missing:** A small agent-kit rule or sample module that shows how to detect 429/Retry-After and implement exponential backoff with jitter around driver calls.
- **Where the agent looked:** Repository code and DocumentDB best-practice pages.
- **Effect on this build:** No retry/backoff code was added; a sample in production could fail under throttling or behave unpredictably.
- **Suggested fix (agent_kit_rule):** A reusable Node.js helper (backoff/retry wrapper) that wraps MongoDB client operations, respects Retry-After if present, and exposes a simple async call pattern. Include a unit test that simulates 429 responses.

## [high] Connection-string and SRV vs legacy shapes

- **What was missing:** Clear sample guidance to tell users to obtain the exact connection string from 'az documentdb mongocluster list-connection-strings' or the portal rather than hand-crafting a cosmos.azure.com:10255 URI. The quickstarts sometimes still show cosmos-style strings which confuses builders.
- **Where the agent looked:** Prompt, README and the DocumentDB quickstarts; readiness_findings listed several confusing examples.
- **Effect on this build:** Risk of builders hardcoding an incorrect host/port and failing to connect to vCore mongoClusters.
- **Suggested fix (discoverability):** Add a short 'How to get your connection string' paragraph to the quickstart and to the documentdb-mcp-setup skill showing the exact CLI command and portal location (az documentdb mongocluster list-connection-strings) and recommend storing it in DOCUMENTDB_URI.

## [high] IaC examples for DocumentDB (mongoClusters)

- **What was missing:** Example Bicep/Terraform templates that deploy Microsoft.DocumentDB/mongoClusters with low-cost defaults and optional CMK/Private Endpoint settings.
- **Where the agent looked:** Repo and discovered resource-type documentation; readiness findings show confusion between databaseAccounts and mongoClusters.
- **Effect on this build:** No IaC shipped; sample readers expecting an IaC template will be left to invent resource types and risk deploying the wrong resource (Cosmos DB vs DocumentDB vCore).
- **Suggested fix (mcp_tool_or_description):** Provide a small 'infra' directory with an example Bicep file (or Terraform/AzAPI) that creates Microsoft.DocumentDB/mongoClusters with parameters for tier, region, and storage, and a README section describing safe defaults for trying the sample.

## [medium] Testing guidance for DocumentDB

- **What was missing:** A short, DocumentDB-specific testing guide showing the recommended local gateway Docker image (ghcr.io/documentdb/documentdb/documentdb-local) and mocking patterns for Node.js MongoDB clients so tests can be run without the live cloud cluster.
- **Where the agent looked:** Repository and general testing docs; discovered_practices searches returned general testing docs but not DocumentDB-specific guidance.
- **Effect on this build:** The sample includes Jest mocks which suffice, but many builders will default to plain mongo images (27017) and miss DocumentDB-specific behaviors.
- **Suggested fix (learn_doc):** A short page 'Testing DocumentDB apps locally' in the documentdb-local-deployment skill describing the official gateway image, default port (10260), env flags, and a mocking recipe for Jest that intercepts getDb() to return a mock client.

## [medium] PII redaction guidance for decision traces

- **What was missing:** A concrete note or small utility to redact or pseudonymize PII before storing decision rationale or logs; discovered_practices search did not find a DocumentDB-specific decision-trace guideline.
- **Where the agent looked:** Repository, DocumentDB logging and PII pages.
- **Effect on this build:** Sample writes rationale and createdAt to the decisions collection without redaction; in real deployments this could lead to PII being stored or logged unredacted.
- **Suggested fix (discoverability):** Add to the documentdb-security skill a short 'Redacting PII in decision traces' section with examples of fields to remove/transform and a small helper library for redaction.

