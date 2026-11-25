# Documentation and tooling gaps: 20-interest-accrual-batch-processor

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Index creation at deployment vs runtime

- **What was missing:** Guidance emphasizing that large index builds should be performed at deployment/migration time (idempotently) and not triggered automatically in high-load job runtime without caution.
- **Where the agent looked:** Indexing guidance exists (P12) but sample created indexes at worker startup. The docs discuss idempotent index creation but the sample did not follow deployment-time practice.
- **Effect on this build:** Worker creates indexes at run-time via ensureIndexes(). For small sample datasets that's fine, but in production this pattern risks starting index builds during job runs. An agent following sample code could recommend a pattern that is risky at scale.
- **Suggested fix (discoverability):** Add a prominent paragraph to the indexing guidance and the sample quickstart: 'Create indexes as part of deployment/migration (idempotent script). If the sample creates indexes at runtime, mark this as a convenience for small datasets and provide an alternative migrate script.' Provide a code snippet for an idempotent index migration script.

## [high] Retry + backoff example for bulkWrite

- **What was missing:** A small, copy-pasteable code example showing how to implement retries with exponential backoff, respect Retry-After headers and suppress duplicate-key 11000 errors for unordered bulkWrite workflows.
- **Where the agent looked:** Installed skills discuss retries and throttling (P06) but do not include a concise, sample-level code snippet for bulkWrite + backoff + duplicate-key handling.
- **Effect on this build:** Worker catches bulkWrite errors but does not implement backoff/retry logic or inspect writeErrors; adopters of the sample may not handle partial failures correctly under throttling.
- **Suggested fix (sample_or_quickstart):** Provide a short code sample (Node.js) implementing: call bulkWrite, on error inspect err.writeErrors, filter out duplicate-key codes (11000), retry transient errors with exponential backoff + jitter, and log the final outcome. Include guidance on respecting Retry-After headers.

## [medium] Complete .env.example

- **What was missing:** .env.example omitted optional env vars used by scripts (for example SEED_COUNT used by scripts/seed.js).
- **Where the agent looked:** Inspected repository files app/.env.example and scripts/seed.js; verified seed reads process.env.SEED_COUNT (scripts/seed.js line 37).
- **Effect on this build:** Builder provided a working .env.example for the critical connection string and common parameters but missed documenting SEED_COUNT; consumers might not know how to change seed size or that seed supports SEED_COUNT.
- **Suggested fix (learn_doc):** Update .env.example to list all environment variables used by repository (DOCUMENTDB_URI, DB_NAME, BATCH_SIZE, CRON_SCHEDULE, SEED_COUNT). Add short comments for each variable explaining purpose and sensible defaults (e.g., SEED_COUNT=100).

## [medium] Driver & Mongoose tested versions (discoverability)

- **What was missing:** A clear documented, discoverable recommendation for which Mongoose / mongodb-driver versions the quickstart/sample was tested with that agents can find without relying on model defaults.
- **Where the agent looked:** I ran a targeted Microsoft docs search (Quickstart: Connect Mongoose to Azure DocumentDB quickstart and related docs) and found tested-driver notes on the quickstart page (mentions Mongoose 9 / driver 7.8.0 in some docs), but the sample's decisions relied on model defaults rather than linking to that page.
- **Effect on this build:** The builder chose Mongoose 7.x (package.json^7.5.0). That choice works for the sample, but an agent operating from model defaults might pick an older/unsupported combination. This reduces reproducibility and may cause compatibility issues in other environments.
- **Suggested fix (discoverability):** Add a short 'Tested driver versions' paragraph to the Node/Mongoose quickstart for Azure DocumentDB naming the tested Mongoose and Node driver versions and link it from the agent skill. Also update the sample README to cite the tested driver pairing to justify the package.json pin.

## [medium] Bulk-write batch-size guidance

- **What was missing:** Public docs and the agent skills do not specify a single recommended exact unordered bulkWrite batch size (e.g., '500' vs '200–1000') for DocumentDB; prior knowledge gave a range but we lacked an authoritative numeric recommendation an agent can follow.
- **Where the agent looked:** Searched Microsoft Learn and installed skills; discovery step left two searches with no useful numeric-result 'Azure DocumentDB recommended bulkWrite batch size 200-1000 exact guidance'.
- **Effect on this build:** Builder picked BATCH_SIZE=500 (a sensible default). However the choice came from model-default reasoning rather than a documented guidance; agents may make inconsistent picks unless guidance is explicit.
- **Suggested fix (learn_doc):** Add a short sentence to the bulk-write guidance page stating recommended batch-size ranges for unordered bulkWrite (e.g., 'Start with 200–1000 ops per bulkWrite for most clusters; tune down if you see 429s or transient errors; test requestCharge per batch with explain/profiling'). Include an example showing how to expose BATCH_SIZE via environment and ramp it up/down.

## [medium] IaC example for mongoClusters

- **What was missing:** An example Bicep/ARM or Terraform snippet that creates an Azure DocumentDB mongoClusters resource (Microsoft.DocumentDB/mongoClusters) for sample authors to copy.
- **Where the agent looked:** Searched IaC docs during readiness; the correct resource type is documented but the repo lacks an example (see readiness findings).
- **Effect on this build:** The sample assumes an existing cluster. Lack of an IaC snippet means users who want to reproduce the environment must discover the correct resource type themselves and risk targeting the wrong resource API surface.
- **Suggested fix (mcp_tool_or_description):** Publish a minimal Bicep and Terraform example that provisions a mongoClusters resource (Microsoft.DocumentDB/mongoClusters) with parameterized tier, region, and storage. Include commands to list connection strings (`az documentdb mongocluster list-connection-strings`) and a note warning about Cosmos DB (RU) vs DocumentDB (vCore) resource types.

## [low] Default cron schedule policy for samples

- **What was missing:** The agent made a model-default decision to use midnight UTC as a succinct sample default, but there's no team-wide rule documented for what default cron/timezone to use in sample gallery jobs.
- **Where the agent looked:** Checked repository README and the available agent skill docs; no authoritative gallery-style guidance on default cron timezone was found.
- **Effect on this build:** Builder chose midnight UTC; that's reasonable. However different sample authors may choose local time or another default leading to inconsistency across gallery samples.
- **Suggested fix (agent_kit_rule):** Add an agent-kit rule: 'When a sample implements a daily scheduled job and the author does not specify timezone, default to midnight UTC and provide a --once CLI switch and an explicit CRON_SCHEDULE env var in .env.example.'

