# Documentation and tooling gaps: 06-collateral-management-store

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Optimistic concurrency / versioning guidance

- **What was missing:** Public guidance on whether to prefer an application-level version field (incrementing version) vs using database transactions / provided concurrency controls for versioned documents in Azure DocumentDB was not found. The earlier search for 'version optimistic concurrency' returned no useful public docs.
- **Where the agent looked:** Searches for 'Azure DocumentDB optimistic concurrency version', 'version field optimistic concurrency Azure DocumentDB', and the DocumentDB compatibility docs; agent-kit skills and Microsoft Learn were consulted.
- **Effect on this build:** The builder implemented application-level versions (version field) by choice; an agent working from prior knowledge could choose either approach. Lack of clear public guidance risks inconsistent patterns across samples (some using transactions or 'findAndModify' with optimistic checks and others using version documents).
- **Suggested fix (learn_doc):** A short learn.microsoft.com page titled 'Versioned documents and concurrency for Azure DocumentDB (Mongo-compatible)' that: 1) states the official recommendation (e.g., use application-level version field for append-only history, show examples for optimistic concurrency and when to prefer transactions), 2) gives code examples in Node.js (find highest version then insert vs findOneAndUpdate with upsert and safe dedup), 3) shows explain() traces for both approaches, and 4) notes any compatibility or performance tradeoffs. Include a sample Mongoose code snippet demonstrating a safe upsert or a versioned insert and how to verify uniqueness with a unique index.

## [high] Vector-index setup & embedding-dimension configuration

- **What was missing:** A concise example in the agent-kit or docs showing how to create a cosmosSearch vector index with explicit dims and algorithm options (IVF/HNSW/DiskANN), and guidance that the sample must set EMBEDDING_DIM to match the chosen embedding model before index creation.
- **Where the agent looked:** documentdb-vector-search skill and the readme; no sample-level index creation script or instructions were present in the repository.
- **Effect on this build:** The builder sensibly left embeddings optional. However, without a short 'how to create a vector index for this sample' doc and a matching EMBEDDING_DIM placeholder, an agent might create an index with the wrong dimension or algorithm, causing index creation to fail or produce unusable results.
- **Suggested fix (mcp_tool_or_description):** Add a short doc or tool in the agent kit: 'Sample: Create a vector index for collateral_assets' that lists the minimal createIndex/createSearchIndexes command, shows where to set dims (ENV variable EMBEDDING_DIM) and suggests default algorithms for small sample size (IVF for <10k, HNSW <50k). Include an example command and a script that reads EMBEDDING_DIM and issues the index create via MCP or the driver.

## [high] Sample naming and resource-type disambiguation

- **What was missing:** Clear, prominent note distinguishing 'Azure DocumentDB (managed Mongo vCore, resource type Microsoft.DocumentDB/mongoClusters)' from older Cosmos DB 'databaseAccounts' and from Amazon DocumentDB. The agent kit had bits of this but a single prominent banner or short paragraph is missing in samples.
- **Where the agent looked:** Agent kit readiness notes and documentdb-azure-deployment skill; community docs.
- **Effect on this build:** Agents and builders may accidentally craft IaC or CLI commands targeting the wrong resource type (databaseAccounts) which will fail or produce a different service model. This is a high-risk area for automated agentic builds.
- **Suggested fix (naming_or_disambiguation):** Add a short 'Which DocumentDB is this?' banner to sample README and agent kit guidance clarifying 'This sample uses Azure DocumentDB (managed Mongo vCore / mongoClusters). It is NOT Amazon DocumentDB nor Cosmos DB SQL/Core API. For IaC use Microsoft.DocumentDB/mongoClusters and the mongocluster CLI group.'

## [medium] Entra ID / OIDC connection examples

- **What was missing:** A discoverable example showing how to connect with Microsoft Entra ID (OIDC/MONGODB-OIDC or managed identity flows) in Node.js Mongoose for the vCore-managed DocumentDB offering.
- **Where the agent looked:** Microsoft Learn connect docs and the documentdb-azure-deployment skill; agent-kit contains some references but a short, copy-paste example was not in the sample repo.
- **Effect on this build:** The sample defaults to a password-style DOCUMENTDB_URI. Users deploying to production might prefer Entra/Manged Identity; missing examples reduce discoverability for secure production patterns.
- **Suggested fix (discoverability):** Add a README subsection 'Auth options' with two copy-paste examples: (1) SCRAM connection string example for local dev and (2) OIDC / Entra example with a reference to how to obtain credentials or to configure a managed identity. Link to Microsoft Learn's Entra docs.

## [medium] .env.example completeness (DB_NAME)

- **What was missing:** DB_NAME is used by code (DB_NAME env var as fallback to sample_banking_06) but is not listed in .env.example.
- **Where the agent looked:** app/.env.example and app/src/index.js and app/scripts/seed.js.
- **Effect on this build:** If a user copies .env.example without adding DB_NAME the seed may have previously connected to a different database if the connection string provided a different default DB; this caused an earlier open_issues note from the builder.
- **Suggested fix (agent_kit_rule):** Update .env.example to include DB_NAME=sample_banking_06 with a comment: '# name of the database the sample uses; default sample_banking_06'. Agent-kit rule: require DB_NAME be present in .env.example for all DocumentDB samples.

## [low] Tests README mismatch

- **What was missing:** README claims unit tests use mongodb-memory-server but the test suite in this environment uses Jest mocks because mongodb-memory-server failed to start; the README lacks fallbacks or CI notes.
- **Where the agent looked:** app/README.md and app/tests/*; events.jsonl shows the memory-server failure and switch to mocks.
- **Effect on this build:** A developer reading README might expect to run mongodb-memory-server locally and be confused when the tests have been implemented to use mocks in CI. This is a minor but actionable documentation mismatch.
- **Suggested fix (learn_doc):** Update README testing section to say: 'Unit tests run offline; tests prefer mongodb-memory-server where the platform supports spawning mongod, but the repo uses mocks for CI-friendly behavior. To run integration tests with an embedded server, set TEST_USE_REAL_MONGODB=true and ensure dependencies and native binaries are available.'

