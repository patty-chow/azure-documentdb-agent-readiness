# Documentation and tooling gaps: 19-proactive-outreach-orchestration

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Resume-token persistence & writeConcern naming

- **What was missing:** Clear, prominent guidance stating that while consumers should persist resume tokens to durable storage, client-side writeConcern:majority may be ignored by the service and should not be relied on for checkpoint durability.
- **Where the agent looked:** Learn docs on change streams, documentdb change-streams page; discovered in 'Change streams in Azure DocumentDB' (see discovered practice P19).
- **Effect on this build:** Builder did not implement resume-token persistence or follow-up guidance; sample's change-stream listener can lose events after restarts and a builder might attempt to set client writeConcern expecting it to change server behavior.
- **Suggested fix (naming_or_disambiguation):** A short 'Change-stream consumer checklist' page under DocumentDB docs: (1) explicit example Node.js snippet that persists resume tokens to a durable collection and reads them at startup; (2) a clear note 'do not rely on client writeConcern — the service manages replication quorum; set up durable checkpoints regardless'; (3) sample code for resumeAfter and startAtOperationTime usage.

## [high] Vector index creation snippet

- **What was missing:** A ready-to-run, idempotent Node.js example that creates a DocumentDB vector index using the createIndexes command with cosmosSearchOptions and reads embedding dimensions from env.
- **Where the agent looked:** DocumentDB vector search docs and installed documentdb-vector-search skill; no ready-to-run Node.js createIndexes snippet was found in the repo.
- **Effect on this build:** Builder did not create a vector index programmatically; the repo lacks the exact createIndexes JSON shape required by the service and left index creation as a manual step.
- **Suggested fix (mcp_tool_or_description):** A small Node.js script (idempotent) named tools/create_vector_index.js that constructs the createIndexes payload with cosmosSearchOptions (kind, dimensions, metric, algorithm params) using EMBEDDING_MODEL / EMBEDDING_DIMS env values, and runs the DB command via the driver. Include README instructions and a sample default parameter set suitable for small demo datasets.

## [high] Sample IaC for mongoClusters

- **What was missing:** A small Bicep or Terraform example that creates Microsoft.DocumentDB/mongoClusters (the service's actual resource type) with low-cost defaults and parameters for tier, region and storage.
- **Where the agent looked:** Repository (no IaC present) and readiness notes pointing to the mongoClusters docs.
- **Effect on this build:** The sample assumes an existing cluster; without IaC a user may create the wrong resource (databaseAccounts) or use cosmosdb CLI group incorrectly.
- **Suggested fix (learn_doc):** Add 'infra/bicep/mongoCluster.bicep' and 'infra/terraform/mongocluster.tf' example templates that create a mongoCluster with parameterized tier, region and minimal defaults, plus README instructions and a one-line az CLI example (az documentdb mongocluster create...).

## [medium] .env.example completeness

- **What was missing:** .env.example omitted optional/operational env keys the code reads (MAX_POOL_SIZE, MIN_POOL_SIZE) and did not provide placeholders for common send-provider settings (SMTP/TWILIO placeholders).
- **Where the agent looked:** Repo files (.env.example) and code (app/src/db.js, app/src/sendAgent.js).
- **Effect on this build:** Developers may copy .env.example and later discover required env variables at runtime; missing provider placeholders reduce discoverability of how to enable real sends.
- **Suggested fix (discoverability):** Update .env.example to include MAX_POOL_SIZE, MIN_POOL_SIZE, and example provider env names with placeholders (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, TWILIO_SID, TWILIO_AUTH_TOKEN) plus a short README subsection describing how and when to set them.

## [medium] Idempotent seed / vector and explain verification

- **What was missing:** An explain() check in seeding/tests to verify that created indexes actually serve the intended queries and a demonstration of idempotent vector index creation.
- **Where the agent looked:** Repo seed script and code; documentdb-indexing and monitoring skill docs.
- **Effect on this build:** Indexes were created but not automatically validated with explain(); for larger samples this could let a missing index go undetected.
- **Suggested fix (agent_kit_rule):** Add a test script step that runs explain('executionStats') for key queries and fails the CI step if a COLLSCAN is observed for an important query. Add the vector index creation tool described above as an idempotent step.

## [medium] Tests that run without a live cluster

- **What was missing:** A small test harness and examples showing how to run unit tests without a live DocumentDB (mocking the MongoClient or using a recommended test dependency).
- **Where the agent looked:** Repo test_runner.js (which runs seed and run-once) and the codebase for any mocking examples (none present).
- **Effect on this build:** Current smoke tests require a live cluster; CI for gallery samples should be able to run fast unit tests without external resources.
- **Suggested fix (sample_or_quickstart):** A short 'Testing' page and example tests using mongodb-memory-server or a small mock wrapper around getClient(); include an npm script 'test:unit' that runs these mocked tests and document what environment variables to stub.

## [medium] Send-agent integration examples & safe defaults

- **What was missing:** A concrete provider example (one or two) for the send agent (e.g., SMTP for email, Twilio for SMS) with env var names, and an explicit pattern for enabling real sends safely.
- **Where the agent looked:** Repo sendAgent.js (contains TODO) and README notes; no provider examples present.
- **Effect on this build:** Send-agent is sandboxed by default; a developer enabling real sends might not know which env vars to add and how to avoid committing secrets or accidentally enabling sends in CI.
- **Suggested fix (sample_or_quickstart):** Add example provider implementations under src/providers/ (smtpProvider.js, twilioProvider.js) with clear env var names and a README subsection 'How to enable real sends safely' describing SANDBOX_SEND toggle and CI guard rails.

## [low] Naming map & product disambiguation

- **What was missing:** A short 'Naming map' section clarifying Azure DocumentDB (mongoClusters) vs Azure Cosmos DB vs Amazon DocumentDB and historical 'DocumentDB' naming to avoid agent or human confusion.
- **Where the agent looked:** README and readiness notes where naming confusion was observed.
- **Effect on this build:** Reduces risk of an agent or developer applying Cosmos DB examples or CLI commands incorrectly; the README currently does not include a naming map.
- **Suggested fix (discoverability):** A one-paragraph 'Naming & compatibility' note in the README with links to Learn pages illustrating the differences and correct resource types ('Microsoft.DocumentDB/mongoClusters').

