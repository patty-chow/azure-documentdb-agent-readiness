# Documentation and tooling gaps: 01-anti-money-laundering-pattern-detector

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Server feature and operator compatibility for DocumentDB

- **What was missing:** Authoritative, discoverable guidance that states which MongoDB aggregation operators ($graphLookup, explain, server-side JS, etc.) and vector-index createIndex options the managed DocumentDB cluster supports and the exact parameter names/syntax.
- **Where the agent looked:** Local code and readiness notes; no external docs reachable (documentation_search_available=false).
- **Effect on this build:** Implementer added a runtime supports_graph_lookup check and a client-side fallback. Without official operator support docs, implementers must rely on runtime checks and cannot author guaranteed server-side pipelines or index creation snippets.
- **Suggested fix (discoverability):** A small 'Feature matrix' page listing supported aggregation operators, the exact createIndex syntax for vector indexes and the recommended engine options and example commands tested against the validated cluster SKU; include an index-creation sample and an explain-based operator-test snippet.

## [high] Secrets best practices (Key Vault / managed identity)

- **What was missing:** Clear guidance for storing/rotating long-lived secrets (DOCUMENTDB_URI, OPENAI_API_KEY) in Azure Key Vault and how to use a managed identity for least-privilege access for data-plane where supported.
- **Where the agent looked:** Local repository, readiness notes; external docs not reachable.
- **Effect on this build:** Sample correctly avoids committing secrets but provides only .env-based usage. Operators may expect a recommended production path to Key Vault/managed identity.
- **Suggested fix (learn_doc):** Short 'Secrets & production config' page showing (1) example of reading secrets from Azure Key Vault using DefaultAzureCredential where supported, (2) fallback to env var for local dev, (3) explanation of which data-plane auth methods are supported for the validated cluster SKU.

## [high] Offline unit-testing guidance

- **What was missing:** A recommended pattern and example tests that run without a live cluster (e.g., using mongomock or patching MongoClient) so CI can run tests offline.
- **Where the agent looked:** Local tests and README; external docs not reachable.
- **Effect on this build:** Current test requires a live cluster and therefore will not run in an offline CI job; developers will be unable to get quick feedback without a cluster.
- **Suggested fix (sample_or_quickstart):** Add 'tests_offline.md' and a small test module demonstrating how to patch the pymongo.MongoClient to use mongomock or a fake collection for unit tests; include a tox/pytest marker example.

## [high] Index and createIndex syntax for vector indexes (naming/disambiguation)

- **What was missing:** A clear, authoritative example showing exact createIndex keys and accepted parameter names for HNSW/IVF/DiskANN on the managed DocumentDB SKU (names and allowed ranges).
- **Where the agent looked:** Local repo; no external docs available.
- **Effect on this build:** Without exact option names, a script that attempts to create vector indexes may fail at runtime on some SKUs.
- **Suggested fix (naming_or_disambiguation):** A minimal 'create_vector_index.py' sample with validated syntax and annotated parameter descriptions for the supported index types; include a short README paragraph about compatibility caveats.

## [medium] Single shared MongoClient

- **What was missing:** Guidance in public docs or an explicit sample-level rule advising that a single MongoClient instance should be created and reused for the life of the process (module-level client or cached factory).
- **Where the agent looked:** Local code only (documentation_search_available=false). I inspected src/db.py, src/seed_data.py, src/run_detector.py.
- **Effect on this build:** The sample constructs a new MongoClient in get_client() each call; this is functional but not optimal for connection pooling and can lead to extra connections.
- **Suggested fix (agent_kit_rule):** Add a short rule in the agent kit: 'Create and reuse a single MongoClient per process; expose get_client() that returns a cached client. Example code snippet and rationale.'

## [medium] Vector index parameters and embedding-dimension guidance

- **What was missing:** Explicit, public guidance connecting embedding model output dimensions to the vector index 'dims' parameter and recommended HNSW/IVF/DiskANN tuning values for small sample datasets vs production.
- **Where the agent looked:** Local repository and prior-belief searches recorded in discovery; external docs were not reachable (documentation_search_available=false).
- **Effect on this build:** The sample does not implement vector indexes; if vector search is added later, implementers will lack authoritative defaults to choose safe parameters or to tune them for recall/latency.
- **Suggested fix (learn_doc):** A page titled 'Vector search on Azure DocumentDB — dimensions and index tuning' that states: the tested embedding dimensions for recommended models, how to create indexes with exact `createIndex` fields, and suggested efConstruction/efSearch/nprobe equivalents for small vs large datasets.

