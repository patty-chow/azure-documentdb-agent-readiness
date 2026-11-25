# Documentation and tooling gaps: 11-market-news-sentiment-orchestration

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] LLM provider & credentials guidance

- **What was missing:** No agent-kit page or public quickstart that explicitly prescribes a default LLM provider for DocumentDB samples, the env var names to use, and example fallbacks or test-mode heuristics.
- **Where the agent looked:** Readiness findings, documentdb skills, and Microsoft docs (learn.microsoft.com) for DocumentDB did not prescribe an LLM provider. The run's readiness_findings also flagged this gap.
- **Effect on this build:** The builder made a model_default choice (OpenAI) documented as D004; OpenAI calls could not be verified in the run because OPENAI_API_KEY was not present. Without guidance, different builders may pick incompatible providers or env var names, harming consistency.
- **Suggested fix (agent_kit_rule):** Agent-kit rule + short doc: 'LLM selection for sample gallery: prefer OpenAI (OPENAI_API_KEY) for portability; for Azure OpenAI use AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_KEY, and include a code snippet for both. Provide an explicit 'test-mode' fallback implementation example and an env var naming convention. Include a short automated test (mock) pattern.)'

## [high] Webhook payload & observable delivery

- **What was missing:** No recommended JSON schema for watchlist-alert webhook payload, no guidance on test harness to verify webhook delivery (e.g., local receiver or recorded webhook events).
- **Where the agent looked:** Readme, skills and public docs; readiness_findings noted the notification JSON shape is unspecified.
- **Effect on this build:** The builder chose a payload shape (type, tickers, headline, sentiment, docId) and a bearer-token header. Outgoing webhook delivery was not verified in the run because no WEBHOOK_URL was provided. Different builders may choose incompatible shapes or insecure auth.
- **Suggested fix (learn_doc):** A page 'Webhook schema for DocumentDB samples' with: canonical JSON payload example, required fields, recommended headers (Authorization: Bearer), examples for HMAC vs bearer, and a tiny test harness (node script) showing how to run a local webhook receiver (eg, using http.createServer) to validate delivery and payload shape.

## [high] Concrete vector index creation examples (createSearchIndexes)

- **What was missing:** A concrete, copy-pasteable example of the DocumentDB 'createSearchIndexes' / index-def JSON for HNSW/IVF/DiskANN vector indexes was not present in the agent-kit quick examples.
- **Where the agent looked:** documentdb-vector-search skill and learn.microsoft.com vector-search pages; the skill explains concepts but lacks minimal copy-paste index JSON for quick samples.
- **Effect on this build:** No vector indexes were created by this sample (the sample did not include embeddings), but future samples would risk issuing Atlas-style createIndex calls that DocumentDB rejects. This is a common source of build errors.
- **Suggested fix (mcp_tool_or_description):** A small page showing a minimal createSearchIndexes JSON for a vector field (embedding) for DiskANN, HNSW, and IVF, with sample engineParams and dimension placeholder (e.g., 'dimensions': 1536). Include a snippet that uses the documentdb MCP tool or driver helper to apply the index.

## [high] Unit-test patterns and a local gateway image for CI

- **What was missing:** A small canonical test pattern and instructions for running tests without a live cluster (use the DocumentDB local Gateway Docker image or mongodb-memory-server and a sample config).
- **Where the agent looked:** documentdb-local-deployment skill and repo; readiness flagged local gateway docs but the sample lacks tests.
- **Effect on this build:** There are no unit tests; the demo had to run against a live cluster for verification. This increases verification friction in CI and among reviewers with restricted network access.
- **Suggested fix (sample_or_quickstart):** Add a tests/ folder with a simple mocha/jest test that uses mongodb-memory-server or the DocumentDB Gateway image and a short docker-compose snippet in the repo showing how to run it locally; show how to mock the OpenAI client in tests.

## [high] Retry design & guidance for DocumentDB (retryWrites=false)

- **What was missing:** A clear, prominent statement in the DocumentDB quickstarts emphasising that retryWrites should be set to false for DocumentDB clusters and showing an application-level retry pattern with idempotent keys.
- **Where the agent looked:** learn.microsoft.com quickstarts and documentdb-driver skill; discovered_practices showed prior-knowledge-contradicted behavior (K05).
- **Effect on this build:** The sample did set retryWrites=false (src/db.js:21-23) but it does not have an application-level retry wrapper for main writes to sentiment_signals (insertOne). A builder might mistakenly rely on driver-managed retries.
- **Suggested fix (discoverability):** Add a short cookbook snippet demonstrating normalizeUri(...)?retryWrites=false and an application-level retry helper with exponential backoff and idempotent write example (e.g., upsert with article_id).

## [medium] Driver version & LangChain import guidance

- **What was missing:** A short, discoverable note listing recommended Node.js driver major versions and the LangChain versions/subpath import patterns known to work in the sample environment.
- **Where the agent looked:** documentdb-driver skill and quickstart docs; the builder ran into a LangChain subpath export error and had to choose to drop it.
- **Effect on this build:** The build had to remove LangChain (D010) because of an import/export mismatch; this changes the sample's API surface and the sample no longer demonstrates LangChain orchestration as requested.
- **Suggested fix (discoverability):** Add a short 'Node.js dependencies' snippet to the agent-kit and the documentdb-driver skill: the exact npm versions tested with the sample, the working LangChain import pattern, and a pin recommendation (or a small helper file showing the correct imports).

## [medium] Idempotent seed + seed-as-script guidance

- **What was missing:** The team expects an explicit seed script that can be run separately for CI/demo purposes, with idempotency guarantees and a documented CLI. The sample seeds within demo.js but has no dedicated seed script or documented 'seed-only' command.
- **Where the agent looked:** sample repo, README and documentdb-data-modeling skill docs.
- **Effect on this build:** Seeding was implemented in demo.js and is idempotent, but CI authors or reviewers expecting a separate seed script must run the demo to seed data and indexes.
- **Suggested fix (sample_or_quickstart):** Add a small 'scripts/seed.js' that calls ensureIndexes() and performs idempotent upserts for watchlist and optionally sample signals; add npm script 'npm run seed' and document it in README.

## [medium] IaC quickstart for Microsoft.DocumentDB/mongoClusters

- **What was missing:** A simple Bicep/Terraform example in the agent-kit using the new Microsoft.DocumentDB/mongoClusters resource type with minimal parameters and default low-cost tiers for samples.
- **Where the agent looked:** documentdb-azure-deployment skill; readiness findings highlighted confused examples referencing databaseAccounts vs mongoClusters.
- **Effect on this build:** No infrastructure-as-code was included in the sample; if a later builder tries to add IaC and follows older Cosmos DB examples they risk using the wrong resource type.
- **Suggested fix (sample_or_quickstart):** Add a `deploy/bicep/main.bicep` and a tiny Terraform example that creates a small test cluster (or documents the exact CLI extension az documentdb usage), with notes about cost and teardown.

