# Documentation and tooling gaps: 04-customer-journey-mapper

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Driver version compatibility and pinning

- **What was missing:** Authoritative guidance that lists supported Node driver major versions (e.g., mongodb 5.x vs 6.x), the minimum compatible versions for DocumentDB cluster serverVersion values, and a short rule for which version to pin in samples.
- **Where the agent looked:** Searched installed skills (documentdb-driver, documentdb-connection) and Microsoft Learn quickstarts; no single concise 'which driver versions to pin' sentence was found for this new vCore DocumentDB offering.
- **Effect on this build:** The builder chose mongodb ^5.7.0 sensibly, but reviewers and future builders may pick an incompatible major version that exposes different client API shapes or breaks tests. The tests initially failed because of OpenAI SDK shape differences, illustrating how small SDK changes cause test breakage.
- **Suggested fix (learn_doc):** A short 'Driver compatibility' page or section in the DocumentDB quickstart: (1) recommended Node driver major version(s) for each advertised serverVersion; (2) sample package.json snippet showing pinned version and a 'why' paragraph; (3) a brief troubleshooting note explaining common errors when using other driver majors and how to update code for API changes.

## [high] Server-side aggregation / safe timeline patterns

- **What was missing:** A short example page that shows how to implement an index-backed timeline aggregation pipeline with $match/$sort/$group and how to make it safe for large event histories (use allowDiskUse, ranged pagination, cursors).
- **Where the agent looked:** documentdb-query-optimizer and aggregation docs; examples exist for $match/$sort but not a compact, sample-friendly 'customer timeline' pipeline plus pagination pattern.
- **Effect on this build:** The sample implemented grouping client-side which is unsafe for large timelines; a canonical example would have guided the builder to use a server-side pipeline and pagination from the start.
- **Suggested fix (sample_or_quickstart):** A short 'Customer timeline' recipe page: (1) recommended compound index; (2) aggregation pipeline example for timeline + channel grouping; (3) variant for streaming/paged server-side results; (4) note about allowDiskUse and RU impact and a sample explain() showing index usage.

## [high] IaC example for DocumentDB clusters

- **What was missing:** A minimal Bicep/ARM/Terraform example that provisions Microsoft.DocumentDB/mongoClusters (vCore DocumentDB), with defaults for low-cost tiers and clear comments distinguishing it from older databaseAccounts/azurerm_cosmosdb_account examples.
- **Where the agent looked:** Microsoft Learn docs for mongoClusters and readiness notes; no sample IaC template was present in the repository to copy.
- **Effect on this build:** The sample omitted IaC because the run policy forbade provisioning; without an example, other builders may use older resource types (databaseAccounts) and fail to deploy the intended vCore cluster.
- **Suggested fix (sample_or_quickstart):** Add a 'deploy/mongoClusters.bicep' and 'deploy/terraform' example that declares Microsoft.DocumentDB/mongoClusters and exposes parameters for tier/region/storage. Include a README subsection: 'Note: use mongoClusters resource, not databaseAccounts — see link.'

## [medium] .env.example completeness

- **What was missing:** .env.example does not enumerate optional pool-tuning environment variables (MAX_POOL_SIZE, MIN_POOL_SIZE, MAX_IDLE_MS) that the code reads/defaults to.
- **Where the agent looked:** Repo files (.env.example) and src/db.js; reviewed documentdb-connection skill for recommended knobs.
- **Effect on this build:** Users copying .env.example may be unaware of tunable settings in src/db.js and will not know how to adjust pool sizing for their runtime environment.
- **Suggested fix (sample_or_quickstart):** Add optional entries to .env.example with comments explaining intent, e.g.:
MAX_POOL_SIZE=20 # increase for long-lived servers with high concurrency
MIN_POOL_SIZE=0
MAX_IDLE_MS=300000
Also add a 1-paragraph note in README explaining when to change them.

## [medium] README: clean-up and test guidance

- **What was missing:** Explicit clean-up instructions for removing seed data / indexes and guidance on running unit tests without a live cluster (use local DocumentDB gateway image or mock patterns).
- **Where the agent looked:** Repo README and documentdb-local-deployment skill; README has setup/run but not teardown or local gateway usage instructions.
- **Effect on this build:** Users may be left with sample data in their cluster and may not be able to run integration tests locally with feature parity.
- **Suggested fix (sample_or_quickstart):** Add sections: 'Clean up' (commands to drop the sample database or remove seed_metadata marker), and 'Run tests locally' (how to run the DocumentDB local gateway Docker image including port 10260, and how to run tests against it or how to mock the DB for unit tests).

## [medium] Tests without live cluster (mocking guidance)

- **What was missing:** Concrete guidance or a small helper for writing unit tests that do not require a live DocumentDB cluster (e.g., a lightweight mock of getDb/getClient or a test fixture that starts the local DocumentDB gateway).
- **Where the agent looked:** documentdb-local-deployment skill and repository tests; the repo's tests cover only buildPrompt and do not demonstrate mocking DB calls.
- **Effect on this build:** Builder added a unit test for the prompt builder only; additional tests for aggregation/seed would require either a live cluster or a documented mocking approach.
- **Suggested fix (agent_kit_rule):** Provide a test-utils module and README example showing how to stub getDb/getClient with an in-memory collection shim or how to run the DocumentDB local Docker image for integration tests. Include sample jest setup/teardown code.

