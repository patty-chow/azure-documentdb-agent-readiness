# Documentation and tooling gaps: 13-household-grouping-linkage

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] retryWrites guidance for DocumentDB

- **What was missing:** Prominent guidance in quickstarts explaining that some DocumentDB workflows and samples set retryWrites=false and when setting retryWrites=true may cause issues (vector index workflows or server features).
- **Where the agent looked:** Microsoft Learn DocumentDB quickstarts and tutorial pages, and installed documentdb-connection/driver skills.
- **Effect on this build:** The sample set retryWrites:true in src/db.js, which contradicts many Azure examples that set retryWrites=false; this could silently break index-related or management workflows if users follow the sample without understanding implications.
- **Suggested fix (discoverability):** Add a short note to the Node.js quickstart and driver skill README: explain default retryWrites behavior, document cases that require retryWrites=false (with examples), and provide a one-line snippet showing how to set retryWrites=false in the connection URI or options.

## [high] Index creation idempotency and MCP tooling opt-in

- **What was missing:** Create-index path: the MCP create_index tool attempted to run but failed because management tools are disabled by default in this environment. There is no documented fallback in the MCP docs for 'management tools disabled' wiring.
- **Where the agent looked:** events.jsonl (documentdb_create_index exceptions), README and seed/link scripts.
- **Effect on this build:** Index creation via MCP failed; the builder used Mongoose ensureIndexes as a fallback. Without explicit guidance, other builders may retry MCP calls unnecessarily or be confused by the management-tools opt-in requirement.
- **Suggested fix (agent_kit_rule):** Agent-kit rule: before calling documentdb_create_index, check ENABLE_MANAGEMENT_TOOLS env var or call listIndexes to detect management tool availability; fallback to model.createIndexes() if MCP management is disabled. Add a sample script that performs idempotent createIndexes() prior to seeding.

## [high] Unit test guidance for DocumentDB samples

- **What was missing:** Concrete, sample-backed guidance / scaffolding demonstrating how to run unit tests for DocumentDB samples without a live cluster (e.g., using mongodb-memory-server, or a recommended mocking/stubbing pattern for Mongoose).
- **Where the agent looked:** Installed skills and Microsoft Learn; no authoritative sample for this repository pattern found.
- **Effect on this build:** No unit tests were added; contributors may struggle to add offline tests and will rely on live-cluster verification, which is heavier and potentially flaky.
- **Suggested fix (sample_or_quickstart):** A short 'Testing' quickstart showing how to add mocha/jest tests that use mongodb-memory-server or sinon to stub Mongoose models, with examples of asserting aggregation pipelines and route handlers without a live cluster.

## [medium] Complete .env.example

- **What was missing:** The .env.example includes DOCUMENTDB_URI and DATABASE_NAME but omits other environment variables the app reads or supports (PORT, MAX_POOL_SIZE, SEED_TAG).
- **Where the agent looked:** Inspected app/.env.example, app/src/db.js, app/README.md and repository files.
- **Effect on this build:** User had to infer missing env variables (PORT) from README; missing config examples can cause runtime surprises and inconsistent local setups.
- **Suggested fix (learn_doc):** A .env.example that lists: DOCUMENTDB_URI (placeholder), DATABASE_NAME (sample_customer_360_13), PORT (3000), MAX_POOL_SIZE (example value 50), MIN_POOL_SIZE (example), SEED_TAG (sample13-v1). Include a short comment for each variable explaining when to change it and security note not to commit secrets.

## [medium] DB-level JSON Schema validator examples

- **What was missing:** A short example showing how to create collection-level JSON Schema validators that match the Mongoose schema (required linking keys like normalizedAddress/phone/surname) was not present in public quickstarts.
- **Where the agent looked:** Microsoft Learn $jsonSchema docs and documentdb-data-modeling skill resources.
- **Effect on this build:** The app uses Mongoose schemas but does not apply server-side validators. This reduces data-integrity guarantees if other clients write documents to the same database.
- **Suggested fix (learn_doc):** A sample page: 'Applying collection validators for Node.js + Mongoose samples' with example db.createCollection({ validator: { $jsonSchema: ... } }) matching the Mongoose schema and an idempotent script to apply/upgrade validators.

## [medium] IaC example for DocumentDB mongoClusters

- **What was missing:** A minimal Bicep/ARM/Terraform snippet using Microsoft.DocumentDB/mongoClusters (vCore) for sample provisioning was not included in the repo; many docs are present but quickstarter examples for the agent-kit are scarce.
- **Where the agent looked:** Microsoft Learn templates (mongoClusters) and readiness notes.
- **Effect on this build:** Builder used an existing cluster per policy; but gallery consumers may expect an optional IaC example to reproduce the environment.
- **Suggested fix (mcp_tool_or_description):** Add a bicep/az cli example in the repo (example parameters: tier=M30, region, storage type) that creates Microsoft.DocumentDB/mongoClusters and documents that this is optional and may incur cost.

