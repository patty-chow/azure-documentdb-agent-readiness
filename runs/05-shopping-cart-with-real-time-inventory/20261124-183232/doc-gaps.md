# Documentation and tooling gaps: 05-shopping-cart-with-real-time-inventory

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Mongoose optimistic-concurrency guidance for DocumentDB

- **What was missing:** A focused, public page showing how Mongoose optimisticConcurrency (__v / VersionError) surfaces on Azure DocumentDB, example code that demonstrates catching VersionError/WriteConflict and the recommended retry pattern (including which error labels/codes the DocumentDB driver returns).
- **Where the agent looked:** Microsoft Learn (optimistic concurrency, Mongoose docs), documentdb skills and the repo; searches recorded in the discovery step returned general optimistic-concurrency descriptions but no DocumentDB-specific Mongoose examples.
- **Effect on this build:** The builder implemented optimisticConcurrency and added a retry loop correctly, but relied on model defaults and did not implement precise error-code mapping (e.g., specific handling for WriteConflict or DuplicateKey). Authors will likely implement different retry semantics unless a canonical example is published.
- **Suggested fix (learn_doc):** Title: 'Optimistic concurrency with Mongoose on Azure DocumentDB'
Outline:
- Why optimistic concurrency matters on Azure DocumentDB
- How Mongoose optimisticConcurrency (__v) maps to DocumentDB behavior
- Example model config (optimisticConcurrency: true)
- Example transaction + save flow that demonstrates VersionError on conflict
- Example error handling code mapping DocumentDB/Mongoose errors to domain errors (VersionError -> Conflict, E11000 -> DuplicateKey, labels for transient/UnknownTransactionCommitResult -> retryable)
- Recommended retry/backoff parameters and when to stop retrying
- Small integration test pattern to reproduce/verify no-oversell
Priority: high

## [high] Integration/concurrency test harness

- **What was missing:** A small, copy-pasteable concurrency simulation or integration test that issues parallel add-to-cart requests (or direct service calls) and asserts that no overselling occurs under concurrent load.
- **Where the agent looked:** Repo, Microsoft Learn quickstarts, and documentdb-agent-kit skills; no dedicated concurrency-simulation test harness for cart+inventory patterns was found.
- **Effect on this build:** The builder demonstrated the OutOfStock handling with a manual demo script, but did not include an automated parallel stress test. This leaves a gap in the gallery sample for demonstrating correctness under concurrency and is a likely omission by builders following a short prompt.
- **Suggested fix (sample_or_quickstart):** Title: 'Concurrent add-to-cart test for DocumentDB samples'
Outline:
- Purpose: show no oversell under concurrent requests
- Tooling: node script using Promise.all to fire N concurrent requests to POST /cart/:userId/add or call addToCart() directly
- Assertions: final inventory stock >= 0 and sum of items added cannot exceed original stock
- Optional: use mongodb-memory-server for offline mode and a separate script that runs against a live cluster
Priority: high

## [high] Billing & product-name disambiguation

- **What was missing:** A short, prominent statement on public pages clarifying that Azure DocumentDB (vCore Mongo-compatible clusters) is billed by compute tier (vCores) + storage and is not the RU-based Cosmos DB offering.
- **Where the agent looked:** Product quickstarts, pricing pages and the agent skills; discovery logs show models and authors conflate RU guidance with DocumentDB vCore behavior.
- **Effect on this build:** Builders could pick incorrect scaling/monitoring semantics or example code that mentions RU/s. This build used a live vCore cluster and did not rely on RU guidance, but confusion in docs will cause authoring mistakes in other samples.
- **Suggested fix (naming_or_disambiguation):** A short 'Billing & capacity model' note on the Azure DocumentDB landing/quickstart pages: clearly state 'Azure DocumentDB (vCore) — billed by compute tier and storage; not RU/s'. Add a tiny table comparing vCore DocumentDB vs RU-based Cosmos DB to prevent conflation.

## [medium] Vector createIndex code snippets for Node

- **What was missing:** Concrete, copy-pasteable Node.js examples that create DocumentDB vector indexes with the service's createIndexes/createSearchIndexes JSON payload and the correct cosmosSearchOptions fields (for DiskANN/HNSW/IVF) and example parameter values tuned for small sample datasets.
- **Where the agent looked:** Microsoft Learn vector-search pages and the documentdb skills; the docs show JSON templates but there were no short Node copy-paste snippets to drop into samples.
- **Effect on this build:** If the sample were to be extended with vector search, lack of ready-made createIndex code risks authors writing the wrong Mongo-style createIndex and failing to create the index on DocumentDB. The current sample does not use vectors, so this gap did not break the build, but it is a common authoring pitfall.
- **Suggested fix (discoverability):** Title: 'Create a vector index in Node.js (copy/paste)'
Outline:
- Short Node.js snippet using db.command({ createIndexes: '<coll>', indexes: [...] }) with cosmosSearchOptions.kind: 'vector-hnsw' (or 'vector-ivf' / 'vector-diskann')
- Example parameter values for small/medium/large datasets and recommended dims/metric
- Example query showing $search usage and reading scores
Priority: medium

## [medium] Explain() verification quickstart

- **What was missing:** A small verification script or README step that runs explain('executionStats') against the sample's critical queries and explains how to interpret IXSCAN vs COLLSCAN output.
- **Where the agent looked:** Indexing and explain pages on Microsoft Learn and documentdb skills; guidance exists but no repository-level example that authors can run in a sample.
- **Effect on this build:** The builder created appropriate indexes but did not run explain() as part of seed/verification. A discoverability gap means authors may forget this verification step.
- **Suggested fix (discoverability):** Title: 'Verify indexes with explain() (sample script)'
Outline:
- Node script example that calls collection.find(query).explain('executionStats') and prints key parts
- README snippet describing how to read executionStats and what to change if COLLSCAN appears
Priority: medium

