# Documentation and tooling gaps: 02-real-time-event-stream-ingestion

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Driver-version recommendation & sample pinning

- **What was missing:** There is no single, authoritative driver version recommended for Node.js 24 + MongoDB 7.0 in Microsoft Learn; the builder initially chose ^5.10.0 which failed to install and then settled on ^5.9.0. The docs and quickstarts show tested driver versions in some tutorials but no single pinned recommendation.
- **Where the agent looked:** Microsoft Learn quickstarts and compatibility docs (quickstart-nodejs, Mongoose quickstarts) and readiness findings.
- **Effect on this build:** The builder attempted to pin to a non-existent npm version, delaying installs and requiring a follow-up decision (D009). Consumers copying the sample may be unsure which major driver version to pin for full change-stream support.
- **Suggested fix (discoverability):** Add a short 'Tested driver versions' section in the quickstart README that states the driver major/minor tested with Node 24 (e.g., 'Tested with mongodb@5.9.x; update to the latest 5.x if available; see the Node quickstart for per-driver notes'). Also add a line in the documentdb-driver skill referencing an explicit recommended npm driver version for Node 24.

## [high] Change-stream resume-token guidance and sample code

- **What was missing:** The sample opens a change stream but does not persist resume tokens or implement a restart/backoff policy; the quick verification timed out in this environment. Public docs explain resumeAfter/startAtOperationTime but the sample does not demonstrate checkpointing.
- **Where the agent looked:** Inspected app/src/watch.js and scripts/watch_once.js; reviewed Microsoft Learn 'Change streams in Azure DocumentDB' and documentdb-change-streams guidance.
- **Effect on this build:** Caused incomplete verification of end-to-end change-stream behavior in this run; a developer following the sample may run into missed events or inability to resume after process failure without extra code.
- **Suggested fix (agent_kit_rule):** Add a short sample to src/watch.js (or src/watch_persistent.js) that writes the last resume token to a durable 'watch_checkpoints' collection after processing each change; on startup the watcher should read the last token and call coll.watch({ }, { resumeAfter: token }). Also provide a small README section explaining resumability, example token schema, and how to test locally (watch_once with token snapshot).

## [high] Bulk-write partial-failure handling

- **What was missing:** The ingest path does unordered bulk writes but does not inspect individual writeErrors to retry only retryable failures (it only logs the error). The public guidance recommends inspecting BulkWriteResult/writeErrors and not re-running whole batches.
- **Where the agent looked:** Inspected app/src/ingest.js and searched Microsoft Learn bulk-write guidance and the documentdb-agent-kit for best-practice handling of bulk failures.
- **Effect on this build:** Leaves production ingestion fragile: transient or rate-limit failures are not retried in an idempotent, selective way; duplicate-key errors are not explicitly counted or surfaced for monitoring.
- **Suggested fix (agent_kit_rule):** Add a helper that, given a BulkWriteResult or MongoBulkWriteError, extracts writeErrors and partitions them into non-retryable (duplicate-key 11000) and retryable sets. Retry only the retryable operations with backoff; record metrics for duplicate-key counts. Provide example code and tests.

## [high] DocumentDB vs Cosmos naming & CLI guidance

- **What was missing:** Agent readiness analysis found frequent confusion between Azure DocumentDB (vCore mongoClusters) and Azure Cosmos DB (databaseAccounts/RU). Quickstarts and agent skills should make this distinction more prominent.
- **Where the agent looked:** Readiness findings and Microsoft Learn; several CLI/Bicep docs differ between mongoClusters and databaseAccounts.
- **Effect on this build:** Risk that a user following an IaC example or CLI guidance could deploy or target the wrong resource type.
- **Suggested fix (naming_or_disambiguation):** Add a brief 'Which service is this sample for?' note in README and agent skills that explicitly maps: 'use Microsoft.DocumentDB/mongoClusters for vCore DocumentDB; use Microsoft.DocumentDB/databaseAccounts for Cosmos DB RU-based API' with links.

## [medium] Complete .env.example

- **What was missing:** The repository's .env.example lists only DOCUMENTDB_URI, DATABASE_NAME, EVENTS_BATCH_SIZE, EVENTS_FLUSH_INTERVAL_MS, and PORT. It omits optional and recommended tunables referenced in code (e.g., MAX_POOL_SIZE) and connection-timeout settings.
- **Where the agent looked:** Inspected app/.env.example and app/src/db.js. Reviewed documentdb-connection skill docs for recommended env tunables.
- **Effect on this build:** Led to a partly-complete configuration example; users copying .env.example may miss important tuning knobs such as MAX_POOL_SIZE or timeout env variables, potentially causing suboptimal connection behavior.
- **Suggested fix (learn_doc):** Add an expanded .env.example that lists required and optional settings with placeholders and short comments: DOCUMENTDB_URI, DATABASE_NAME, EVENTS_BATCH_SIZE, EVENTS_FLUSH_INTERVAL_MS, PORT, MAX_POOL_SIZE, MAX_IDLE_TIME_MS, SERVER_SELECTION_TIMEOUT_MS, SOCKET_TIMEOUT_MS, LOG_LEVEL, AUTH_MODE_HINT. Include a one-paragraph note in README explaining which to tune for local dev vs production.

## [medium] IaC: example for Microsoft.DocumentDB/mongoClusters

- **What was missing:** The sample repo contains no Bicep/Terraform example using the Microsoft.DocumentDB/mongoClusters resource type. Readiness findings show several agents confuse databaseAccounts (Cosmos/RU) with the vCore mongoClusters resource.
- **Where the agent looked:** Repo files, and Microsoft Learn 'mongoClusters' docs during readiness scanning.
- **Effect on this build:** No direct effect on the runtime sample (build used an existing cluster), but omission can mislead users about how to provision the vCore DocumentDB product or cause them to use the wrong resource type.
- **Suggested fix (mcp_tool_or_description):** Add infra/examples/mongocluster.bicep (and a Terraform example) that shows minimal mongoClusters creation with parameters for tier (M30), storage, and firewall/Private Endpoint options. Include a README note 'Do not run without explicit approval' and explain how to get a pre-provisioned cluster for sample verification.

## [medium] Tests without live cluster

- **What was missing:** No unit tests or test fixtures that can run without a live cluster (e.g., mocked MongoDB or in-memory server).
- **Where the agent looked:** Repository 'tests' or 'spec' directories; none found. Reviewed local-deployment skill for recommended local gateway image.
- **Effect on this build:** Makes CI/testability harder; contributors cannot run automated tests without a cluster or extra local infra.
- **Suggested fix (sample_or_quickstart):** Add a lightweight test suite using jest/mocha that uses mongodb-memory-server or sinon/mocks for the MongoClient to exercise addEvents, flush, and error paths. Document commands in README.

