# Documentation and tooling gaps: 01-unified-customer-profile-store

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Authoritative Mongoose connection options for DocumentDB

- **What was missing:** A short authoritative snippet showing the recommended mongoose.connect invocation and a list of driver options (tls/ssl, replicaSet, retryWrites, connectTimeoutMS, serverSelectionTimeoutMS, maxPoolSize) appropriate for this managed Azure DocumentDB product.
- **Where the agent looked:** Local repo files only; documentation search unavailable in this environment.
- **Effect on this build:** The sample deliberately avoids hardcoding flags and asks the operator to supply a correct DOCUMENTDB_URI. Without a canonical snippet, builders may either omit required flags or accidentally hardcode deprecated driver options.
- **Suggested fix (learn_doc):** Page title: 'Connecting to Azure DocumentDB with Mongoose'
Outline: brief explanation of using DOCUMENTDB_URI, an annotated sample mongoose.connect(process.env.DOCUMENTDB_URI, { /* recommended options */ }) pinning options known to be required for the product and explanation of which options to avoid; recommended maxPoolSize guidance and example for low/high concurrency; note on driver versions. Include tested snippet pinned to Mongoose 7.x.

## [high] Authentication methods and whether Microsoft Entra ID is supported

- **What was missing:** Authoritative statement of supported data-plane authentication methods (account keys / username+password vs Microsoft Entra (AAD) token authentication) for the managed MongoDB-compatible DocumentDB product.
- **Where the agent looked:** Local repo files only; documentation search unavailable.
- **Effect on this build:** The sample uses DOCUMENTDB_URI (username/password) but the README does not explain whether AAD is supported; users might try unsupported authentication mechanisms or miss recommended secure methods.
- **Suggested fix (learn_doc):** Short page titled 'Authentication options for Azure DocumentDB (MongoDB-compatible)'. Describe supported methods, example connection string forms, and recommended practice (use connection string stored in secret store for CI; mention whether AAD data-plane auth is supported or not).

## [high] Exact vector-index creation API and examples

- **What was missing:** Concrete examples showing how to create DiskANN/HNSW/IVF vector indexes (API call or createIndex invocation), and the mapping between embedding model dimensions and index dims.
- **Where the agent looked:** Local repo files only; documentation search unavailable.
- **Effect on this build:** The run environment mentions a vector-capable cluster, but the sample omitted vector handling because the correct create-index call and parameters are not documented locally. Builders may either omit vector index creation or attempt incorrect Atlas-style options.
- **Suggested fix (learn_doc):** Page titled 'Creating vector indexes on Azure DocumentDB'. Include exact index creation commands (db.collection.createIndex(...)) or management API calls accepted by this product, the index options format (metric, dims, algorithm_config), example parameters for small sample vs larger datasets, and guidance on RU costs for dims and algorithm choices.

## [high] Test strategy for samples that require a live cluster

- **What was missing:** Guidance and a small test harness example showing how to unit test DB-related code without a live managed cluster (mock Mongoose or use an in-memory stub) and what to document for integration tests that do require a live cluster.
- **Where the agent looked:** Local repo only; documentation search unavailable.
- **Effect on this build:** No unit tests were provided; adding a standard pattern would let agents and builders include tests that run offline.
- **Suggested fix (sample_or_quickstart):** Quickstart 'Testing' showing two options: 1) unit tests that mock Mongoose using sinon + proxyquire (example test for upsertEvent), 2) optional integration tests that read DOCUMENTDB_URI from env and are gated with an environment variable. Provide npm test script examples.

## [medium] CLI / ARM resource type for provisioning examples

- **What was missing:** Authoritative CLI/ARM/Terraform snippet showing the correct resource provider and resource type to provision this managed DocumentDB cluster (so README IaC examples are accurate).
- **Where the agent looked:** Local repo files and readiness notes; documentation search unavailable.
- **Effect on this build:** README currently states the sample does not provision resources. If an IaC example is later added, it must use the correct resource type; otherwise README would mislead readers who attempt to automate provisioning.
- **Suggested fix (discoverability):** A small doc 'Provisioning examples' with az CLI example, an ARM/Bicep snippet, and a Terraform example using the correct provider/resource type. Mark them optional and include placeholders only.

## [medium] Change-stream and feature support matrix

- **What was missing:** A short matrix stating support for key MongoDB features (change streams, transactions, server-side JS, aggregation operator support) for the specific managed DocumentDB product and the reported MongoDB wire protocol version.
- **Where the agent looked:** Local repo and readiness notes; documentation search unavailable.
- **Effect on this build:** Builders may assume change streams or other features are/are not available and design samples that break on the live cluster. This sample avoided change-streams but a README note would reduce confusion.
- **Suggested fix (discoverability):** Page 'Feature compatibility' listing the product's supported MongoDB wire protocol versions (e.g., 7.0 as in the run environment), and per-feature supported/unsupported status with short examples where relevant.

## [medium] Agent discoverability: driver version pinning guidance

- **What was missing:** A clear note in the agent kit or sample README about dependency pinning strategy for Node samples (either pin in package.json or require npm ci and commit package-lock.json).
- **Where the agent looked:** Local files only; documentation search unavailable.
- **Effect on this build:** package-lock.json exists but package.json uses caret ranges. An explicit recommendation would help agents and builders pick a consistent, reproducible approach.
- **Suggested fix (agent_kit_rule):** Agent-kit rule: 'For Node samples pin either in package.json exact versions OR require contributors to use npm ci and commit package-lock.json; include a README badge/instruction to 'npm ci' for reproducible builds.'

