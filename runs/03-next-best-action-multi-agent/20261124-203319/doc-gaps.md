# Documentation and tooling gaps: 03-next-best-action-multi-agent

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Embedding model & dimensions guidance

- **What was missing:** No authoritative recommendation in installed skills or repo about which embedding model to choose as a default for samples and the corresponding dimensions; builders used a model_default (text-embedding-3-small / 1536) but that choice was not grounded in a skill.
- **Where the agent looked:** Installed skills (documentdb-vector-search, documentdb-azure-deployment), README, .env.example, Microsoft Learn searched during discovery.
- **Effect on this build:** The sample chose a default embedding model by convention. The vector index dimensions and seed embeddings were set to 1536 to match that choice, but this is a model-default choice rather than an authored team recommendation.
- **Suggested fix (learn_doc):** Add a 'Embeddings and vectors' page to the sample-guide describing recommended embedding providers/models for samples (e.g., OpenAI text-embedding-3-small 1536), the reasons for the choice (cost/quality/compatibility), and the required EMBEDDING_DIMS. Include a short table of alternatives and the dimensions required, and update .env.example with a comment linking to this page.

## [high] Programmatic vector-index creation examples & fallbacks

- **What was missing:** A tested, in-repo script that reliably creates a cosmosSearch vector index (cosmosSearchOptions) and falls back to clear manual instructions if the MCP helper call fails.
- **Where the agent looked:** documentdb-vector-search skill, seed.py and builder_report; MCP server logs (events) show the tool failed.
- **Effect on this build:** The MCP call to create the vector-diskann index failed during verification and the vector index was not created; vector queries will not function until the index is created manually. This impacts any semantic/vector-enabled runs.
- **Suggested fix (mcp_tool_or_description):** Add a seed_and_indexes.py script that attempts createIndex(...) with cosmosSearchOptions and, on failure, prints the exact mongosh command and a link to portal/CLI instructions. Include example parameters (dimensions from EMBEDDING_DIMS, similarity, maxDegree, lBuild) and a verification step (query explain or documentdb MCP verification call).

## [high] Retry/backoff & throttling guidance in sample

- **What was missing:** The sample did not include an application-level retry wrapper (exponential backoff + jitter) or guidance to honor Retry-After for 429s.
- **Where the agent looked:** documentdb reliability docs, documentdb-monitoring skill, repository code.
- **Effect on this build:** Transient errors and throttling are not handled at the application level; in real runs this could cause failures or poor reliability under load.
- **Suggested fix (agent_kit_rule):** Ship an agent-kit rule and a small library (retry_util.py) demonstrating exponential backoff + jitter, honoring Retry-After, and using idempotent upserts for retriable operations. Include one-line guidance in README pointing to the retry helper.

## [high] IaC example for Microsoft.DocumentDB/mongoClusters

- **What was missing:** An example IaC template (Bicep/Terraform) targeting Microsoft.DocumentDB/mongoClusters was not included in the repo.
- **Where the agent looked:** repository root and documentdb-azure-deployment skill docs.
- **Effect on this build:** Builders who want to provision reproducible test clusters must author IaC themselves; using incorrect resource types risks provisioning the wrong service (Cosmos DB vs DocumentDB).
- **Suggested fix (agent_kit_rule):** Ship a small Bicep example (mongoCluster.bicep) showing Microsoft.DocumentDB/mongoClusters with parameters (tier, storage, region) and defaults for low-cost dev; include a README pointer explaining the difference between mongoClusters and older databaseAccounts examples.

## [medium] README index-parameter tuning & scaling guidance

- **What was missing:** The README lacks concrete guidance on how to change vector-index parameters for larger datasets, and does not document the trade-offs (recall vs latency) or where to adjust EMBEDDING_DIMS and maxDegree/lBuild.
- **Where the agent looked:** app/README.md, documentdb-vector-search skill materials, and discovery notes.
- **Effect on this build:** Users will not know how to reconfigure the vector index for larger data sizes and may attempt to create incompatible indexes. The sample's index-creation fallback is documented only in the open_issues/builder_report text, not in the README.
- **Suggested fix (learn_doc):** Extend README with a 'Vector index tuning' subsection showing example parameters for small, medium, and large datasets, recommended lBuild/lSearch values, and pointers to the documentdb-vector-search skill and portal UI for index creation and monitoring.

## [medium] Dependency pinning guidance / constraints

- **What was missing:** The repo's requirements.txt uses >= bounds rather than exact pins. There is no constraints file or note showing which tested versions the sample was validated against.
- **Where the agent looked:** app/requirements.txt and builder_report.
- **Effect on this build:** Reproducibility risk: different installs may pull incompatible versions leading to test or runtime failures.
- **Suggested fix (discoverability):** Provide a pinned requirements.txt (exact versions) and an optional constraints.txt. Add a README note that records the working versions used during verification and a command to freeze them (pip freeze > requirements.txt) for CI.

## [medium] Seed batching guidance

- **What was missing:** The seed script performs per-document upserts in a loop rather than batching writes (bulk_write) for larger seeds.
- **Where the agent looked:** app/seed.py and documentdb-query-optimizer / documentdb-local-deployment skills.
- **Effect on this build:** For the small demo data set this is acceptable, but for larger sample data it would be inefficient and slow.
- **Suggested fix (sample_or_quickstart):** Provide an alternative seed_bulk.py that uses insert_many/bulk_write in size-limited batches and documents when to use upserts vs insert_many.

## [medium] Unit test mocking strategy for LLM/cluster

- **What was missing:** No documented mocking strategy for LLM/embedding calls or for MongoDB MCP when running unit tests offline; the sample's single test is synthetic and does not demonstrate how to mock the DB or LLM.
- **Where the agent looked:** app/tests, README, and installed skills; no sample test guidelines found.
- **Effect on this build:** Tests passed in this run because they are minimal, but maintainers will need guidance to write robust offline tests that exercise agents when LLM/cluster are not available.
- **Suggested fix (sample_or_quickstart):** Add testing examples using mongomock for DB interactions and monkeypatching/mocking for LangChain/embedding calls. Include an example pytest fixture that sets up mongomock.DB and environment variables for offline runs.

## [low] README cleanup steps

- **What was missing:** Explicit cleanup instructions (how to drop collections or the sample database) are not present in README.
- **Where the agent looked:** app/README.md and seed.py.
- **Effect on this build:** Users may leave demo artifacts in their cluster; cleanup steps make it safe to re-run samples and free resources.
- **Suggested fix (learn_doc):** Add a short 'Clean-up' section showing mongosh/mongo client commands to drop nba_recommendations, interactions and preferences or a provided cleanup.py script to drop the sample database.

