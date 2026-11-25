# Documentation and tooling gaps: 12-invoice-matching-reconciliation

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Connection defaults for samples (TLS, timeouts, pool sizing, retry behavior)

- **What was missing:** A canonical sample-level recipe that recommends safe default connection options (serverSelectionTimeoutMS, maxPoolSize, tls and tlsAllowInvalidCertificates handling, retryWrites policy) and an explanation when Microsoft Entra ID vs connection-string auth should be used for samples.
- **Where the agent looked:** DocumentDB quickstarts, local deployment docs and the documentdb-connection skill; none provided a single succinct 'use these defaults in samples' snippet.
- **Effect on this build:** db.js left options minimal, missing recommended retry/timeouts/TLS flags. This increases the chance of connection-time surprises in sample verification or in CI.
- **Suggested fix (agent_kit_rule):** Agent-kit rule and a one-paragraph doc: recommended default options and env vars (e.g., DB_MAX_POOL_SIZE, SERVER_SELECTION_TIMEOUT_MS, RETRY_WRITES=false). Show example db.js snippet and reasons (connection leaks, TTL on server selection).

## [high] Vector-index creation and embedding-dimension guidance for samples

- **What was missing:** Explicit sample code or a README section showing how to create a vector index on the cluster (algorithm choices, dimensions param matching embedding model, and minimal recommended parameters for demo vs production).
- **Where the agent looked:** Integrated vector store docs and quickstarts; those pages describe index JSON but there wasn't a short sample seed snippet the agent could apply automatically to seed a demo index with the chosen embedding model.
- **Effect on this build:** The sample computes embeddings but does not create a vector index. As a result, embedding-based retrieval cannot be verified end-to-end without manual index creation, which the builder flagged in verification.
- **Suggested fix (mcp_tool_or_description):** Add to the documentdb-vector-search skill a seed-snippet and a sample src/seed-vector-index.js that reads EMBEDDING_MODEL and EMBEDDING_DIM from env and runs createIndexes/createSearchIndexes with a minimal HNSW (or IVF) config for demos, plus a README section on scaling these parameters.

## [high] Normalize vendor name guidance and a canonical field

- **What was missing:** Public, easily discoverable guidance recommending storing a normalized vendor field (vendor_normalized) at write-time for reliable indexed equality lookups, with a small code example.
- **Where the agent looked:** Indexing and query docs; the pattern is commonly used in prior knowledge but not shown as a concise recipe in DocumentDB quickstarts.
- **Effect on this build:** The app implements runtime normalization for scoring but does not persist a normalized field, which prevents efficient indexed equality lookups and makes some queries rely on regex that may not use indexes.
- **Suggested fix (learn_doc):** A short page: 'Canonicalizing and indexing free-text keys (vendor names)' with code examples (Mongoose middleware to set vendor_normalized) and an index recommendation. Example: add pre('save') hook to set vendor_normalized = normalize(vendorName) and create compound index on vendor_normalized + totalAmount.

## [high] Recommendation for monetary types (Decimal128 or integer cents)

- **What was missing:** An explicit sample-recommendation page stating 'store money as Decimal128 or integer cents with examples in Mongoose' for DocumentDB.
- **Where the agent looked:** Aggregation and Decimal docs; there are examples for $toDecimal but no single-page 'money storage' guidance.
- **Effect on this build:** The sample used Number for amounts (JS floats). For financial examples this risks precision issues and is not best-practice.
- **Suggested fix (learn_doc):** Short doc 'Representing money' with Mongoose examples (Decimal128 field or integer cents), seeding examples, and migration notes.

## [high] Tests that run without a live cluster (test harness)

- **What was missing:** An example test harness (jest + mocked mongoose or an in-memory DocumentDB gateway configuration) that agents can copy into samples to run unit tests offline.
- **Where the agent looked:** Sample repos and quickstarts; no standard sample harness was found for offline tests of DocumentDB/Mongoose apps.
- **Effect on this build:** No tests were added; this makes CI and pull-request validation harder for the sample.
- **Suggested fix (sample_or_quickstart):** Add tests/ using jest + mongodb-memory-server or a mock for mongoose, a sample test for reconciliation logic (scoreCandidate, thresholding, and manual-correction handling).

## [medium] Driver-version pinning & supported driver guidance

- **What was missing:** A short, public guidance page that states which MongoDB/Mongoose driver versions are recommended/guaranteed for Azure DocumentDB (vCore mongoClusters) and how to pin them in sample package manifests.
- **Where the agent looked:** Quickstarts and compatibility pages (learn.microsoft.com DocumentDB quickstarts and Mongoose guides) did not present a concise 'pin to X.Y' statement for samples.
- **Effect on this build:** The builder chose Mongoose 7.x by convention; lack of explicit pinned-version guidance left the implementer to assume a safe major. This could lead to breakage if incompatible driver versions are chosen.
- **Suggested fix (discoverability):** A short doc page: 'Recommended Node.js driver versions for Azure DocumentDB (Mongo-compatible)'. Outline: supported Mongoose major/minor matrix, Node.js compatibility table, recommended pinning practices (use package-lock or exact versions), and a sample package.json snippet for samples.

## [medium] Agent memory persistence choices

- **What was missing:** A short page/rule explaining the tradeoffs between in-process ephemeral session memory vs persisted memory (DocumentDB or Redis) for agent corrections, and a recommended default for gallery samples.
- **Where the agent looked:** No single DocumentDB doc covers agent memory; this is application-level guidance missing from product docs.
- **Effect on this build:** Implementer defaulted to an in-process Map (ephemeral). That meets 'within a session' but is easy to misuse in multi-process deployments.
- **Suggested fix (agent_kit_rule):** A short note in the agent kit: 'Use ephemeral memory for single-process demos; use persistent store (DocumentDB/Redis) if you want cross-process persistence; provide examples for both.'

## [medium] Clear procedure to use Microsoft Entra ID for data-plane auth (when applicable)

- **What was missing:** A short example showing how to configure a sample to authenticate with Microsoft Entra ID (OIDC / managed identity) rather than using a connection string, or an explicit note explaining why the sample uses connection-string auth.
- **Where the agent looked:** Auth and quickstart docs; there are references but not a small 'how-to' snippet for Node/Mongoose consumers in sample quickstarts.
- **Effect on this build:** The sample uses a connection string and README does not explain how to use Entra ID; operators might not know whether it's supported for this scenario.
- **Suggested fix (discoverability):** Add a short README subsection 'Using Microsoft Entra ID for data-plane auth' with example commands / links and a note when connection string is acceptable for demos.

