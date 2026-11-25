# Documentation and tooling gaps: 01-anti-money-laundering-pattern-detector

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Vector-index & embedding alignment

- **What was missing:** No guidance in the sample or a single public quickstart stating which embedding model to pick for sample code, and no automated step to create vector indexes sized to the embedding dimension.
- **Where the agent looked:** Read installed skills (documentdb-vector-search, documentdb-full-text-search) and Microsoft vector-search docs via learn_microsoft_docs_search.
- **Effect on this build:** Builder left embeddings optional and did not implement vector index creation; sample has embedding env defaults but no index creation and README has no vector-index tuning advice.
- **Suggested fix (learn_doc):** A short 'Embeddings & vector index' page: state a default embedding model (e.g., text-embedding-3-small, 1536 dims), show createIndexes JSON with cosmosSearchOptions that sets dimensions, algorithm (HNSW/IVF/DiskANN) and minimal tuning params, and a note on when to change numLists/efConstruction/M for larger datasets.

## [high] Test isolation guidance (unit tests without live cluster)

- **What was missing:** No guidance or template for authoring unit tests that mock the DocumentDB client (e.g., mongomock or monkeypatch get_db) so tests run without a live cluster.
- **Where the agent looked:** Searched skills and Microsoft docs; installation and local-gateway docs exist but not a quick recipe for test isolation.
- **Effect on this build:** Tests in this repo require running seed against a live cluster; CI or consumers expecting offline unit tests will be surprised.
- **Suggested fix (discoverability):** A short agent-kit rule or README section showing 1) how to monkeypatch get_db to return a mongomock client for pytest, 2) a minimal example fixture, and 3) an integration-test marker for tests that require a live cluster.

## [high] Management tools opt-in (MCP) and index creation

- **What was missing:** The MCP/documentdb_create_index tool fails unless the run environment opts in (ENABLE_MANAGEMENT_TOOLS=true). There was no discoverable note in the sample telling builders this or explaining the fallback.
- **Where the agent looked:** Events show the MCP tool error; looked at documentdb-agent-kit skills and quickstarts but no single opt-in note in repo.
- **Effect on this build:** The MCP index-creation call failed during the run; the builder fell back to PyMongo index creation. This could break CI pipelines that expect MCP-managed index operations.
- **Suggested fix (agent_kit_rule):** Add a rule and README note: 'To use MCP management tools set ENABLE_MANAGEMENT_TOOLS=true in your environment or use the MCP proper connection profile; otherwise the sample will fall back to driver-based index creation. Provide sample commands and expected error message.'

## [high] Which IaC resource to use for vCore clusters (mongoClusters vs databaseAccounts)

- **What was missing:** Clear, short guidance that modern vCore DocumentDB clusters use Microsoft.DocumentDB/mongoClusters (not the legacy Microsoft.DocumentDB/databaseAccounts), with example Bicep/ARM snippets.
- **Where the agent looked:** learn.microsoft.com resource-type docs (events: microsoft_docs_search results on mongoClusters and databaseAccounts), readiness findings
- **Effect on this build:** Risk of a builder authoring templates for the wrong resource type; this sample used an existing cluster so it didn't block the build but is a common agent failure mode.
- **Suggested fix (naming_or_disambiguation):** A short 'Which resource type to use' micro-page: show the mongoClusters ARM/Bicep snippet, call out databaseAccounts is the legacy RU model, and provide the CLI snippet (az documentdb mongocluster create) for vCore clusters.

## [high] Connection-string examples for vCore clusters and AAD/OIDC connection string examples

- **What was missing:** A short, canonical SRV connection-string snippet for vCore clusters (global.mongocluster.cosmos.azure.com) and an OIDC example for Microsoft Entra ID authentication.
- **Where the agent looked:** learn.microsoft.com connection docs and readiness findings
- **Effect on this build:** Potential for builder mistakes when copying legacy cosmos host/port examples; this repo uses a sample SRV in .env.example but a dedicated microdoc would prevent confusion.
- **Suggested fix (discoverability):** A small connect.md reference with two canonical examples: SRV for SCRAM-SHA-256 and OIDC connection string example with authMechanism=MONGODB-OIDC and authMechanismProperties usage.

## [medium] Seed data shape and acceptance criteria

- **What was missing:** No canonical sample dataset or acceptance criteria document describing minimal transactions to exercise structuring/rapid pass-through/cycle detection.
- **Where the agent looked:** Checked installed skills and sample code; no public sample dataset guidance found.
- **Effect on this build:** Builder created small, sensible seed data, but an authoring standard would make results more consistent across builds and tests.
- **Suggested fix (sample_or_quickstart):** A short sample-data page: list document examples for each typology (example transactions and accounts), expected detection outputs, and idempotent seeding rules. Include JSON fixtures and a seed acceptance checklist for tests.

## [medium] Azure CLI command group disambiguation (az documentdb vs az cosmosdb)

- **What was missing:** A short note in CLI docs clarifying that vCore/mongoClusters uses az documentdb mongocluster and some older cosmosdb commands target databaseAccounts.
- **Where the agent looked:** Azure CLI docs and readiness findings
- **Effect on this build:** Builder attempted to use MCP and Azure CLI guidance could confuse automation authors; not a blocking problem for this sample but dangerous for infra authors.
- **Suggested fix (discoverability):** Add a one-liner and examples to quickstarts and CLI pages: 'For vCore clusters use az documentdb mongocluster ...; az cosmosdb targets legacy databaseAccounts.'

## [medium] Vector index creation JSON template

- **What was missing:** Examples showing the exact createIndexes JSON payload for cosmosSearchOptions (HNSW/IVF/DiskANN) and minimal params so authors don't copy Atlas-style APIs.
- **Where the agent looked:** Vector-search docs (learn.microsoft.com) and documentdb-agent-kit; some examples exist but a minimal snippet is missing from quickstarts.
- **Effect on this build:** Builder did not implement vector indexes; a wrong createIndex payload would be rejected by the service.
- **Suggested fix (learn_doc):** A minimal 'createIndexes' JSON example for each algorithm, showing only required keys (name, key, cosmosSearchOptions.kind, dims, metric) and a short note where to tune parameters for scale.

## [medium] Test isolation vs local gateway guidance

- **What was missing:** Clear advice: when to use the DocumentDB local gateway Docker image for local parity vs using mongomock for unit tests, with example docker run and test fixture.
- **Where the agent looked:** documentdb-local-deployment skill and quickstarts
- **Effect on this build:** Builder used live cluster for tests in run; maintainers may assume tests pass offline.
- **Suggested fix (discoverability):** A 'local dev & tests' quick page: show docker command for gateway image (port 10260), an example .env for local gateway (TLS/port adjustments), and a pytest fixture to switch between mongomock (unit) and real gateway (integration).

