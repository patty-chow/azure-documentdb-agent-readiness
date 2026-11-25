# Documentation and tooling gaps: 01-product-catalog-with-vector-search

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Embedding storage type and indexing

- **What was missing:** A short, prominent statement in the vector-search docs and sample quickstarts that explicitly says: 'Vectors must be stored as number[] (an array of numbers) to be indexed by cosmosSearch; packing embeddings into BSON Binary will not be indexed.' The repository README mentions packed-Binary but does not make this caution prominent.
- **Where the agent looked:** documentdb-vector-search skill, 'Integrated vector store' Microsoft docs, sample README and code; discover step found the number[] requirement but the sample still stored Binary.
- **Effect on this build:** The builder followed the prompt and stored binary-packed embeddings; as a result server-side vector indexing will likely not work and the sample falls back to in-memory ranking. This reduces the sample's value as a demonstration of server-side vector-ivf search.
- **Suggested fix (discoverability):** Add a short 'Indexable vector storage' note to the top of the 'Vector search' documentation and to the sample README. Example text: 'Important: To be indexed by DocumentDB's cosmosSearch vector indexes, store vectors as an array of numbers (e.g., embedding: [0.123, ...]). Storing embeddings as BSON Binary (packed float32) is compact but will not be indexed. If you must store Binary for offline use, also persist a number[] copy or use a separate index pipeline.'

## [high] Index creation verification example

- **What was missing:** A companion example that shows how to create a vector index idempotently and then verify the index is present/usable (listIndexes/getIndexes) before accepting search traffic.
- **Where the agent looked:** documentdb-vector-search examples and scripts; the create_vector_index.py script attempts db.command but does not verify readiness.
- **Effect on this build:** The sample will attempt searches that may fail or return nothing until the index is built; there's no startup/check logic to prevent responses that mislead users.
- **Suggested fix (sample_or_quickstart):** Provide a small index-creation helper that: (1) issues createSearchIndexes, (2) polls db.getCollectionInfos()/listIndexes or a documented admin status endpoint until index is reported as 'ready', and (3) logs the admin payload and response for manual troubleshooting. Include example output and failure handling.

## [high] Microsoft Entra ID examples for data-plane auth

- **What was missing:** A short, copy-paste example showing how to configure Microsoft Entra ID / MONGODB-OIDC authentication in PyMongo (or how to use azure-identity for managed identities) targeted at sample authors.
- **Where the agent looked:** documentdb-security and connection skills; docs mention Entra ID support but example code snippets for the driver were limited or scattered.
- **Effect on this build:** The author defaulted to connection-string auth and did not document Entra ID usage. Authors and sample readers may assume Entra ID is unavailable or may not know how to wire it into the driver.
- **Suggested fix (discoverability):** Add a short 'Using Microsoft Entra ID for data-plane' subsection in the documentdb-connection skill with a PyMongo example, environment variables needed, and when the sample should use Entra vs connection-string (and include a link to the portal setting to enable Entra ID on the cluster).

## [high] Guidance for retry/backoff for demo code

- **What was missing:** A tiny helper or code snippet to add retries with exponential backoff and 429 handling around DocumentDB driver calls and embedding API calls.
- **Where the agent looked:** documentdb-connection skill contains retry guidance but the sample author did not include a code snippet or helper in the repo.
- **Effect on this build:** No retries are implemented; transient errors will cause exceptions or full fallback to in-memory ranking, reducing robustness of the demo when tested against a live cluster or rate-limited embedding provider.
- **Suggested fix (sample_or_quickstart):** Add a small retry helper (e.g., using tenacity) to the agent kit and a one-line example in the sample: 'with retry_on_transient_errors(max_attempts=5): coll.aggregate(pipeline)'. Include special-case handling for 429 and respect Retry-After header.

## [high] RU/provisioning mapping for authors

- **What was missing:** A short page that explicitly states 'DocumentDB uses compute tiers and storage sizing for clusters (M10..M200). Do not use Cosmos DB RU assumptions.' and maps common Cosmos RU advice to the equivalent DocumentDB guidance.
- **Where the agent looked:** readiness findings and quickstarts; searches returned Cosmos RU docs but no authoritative DocumentDB RU mapping.
- **Effect on this build:** Risk of confusion when sample authors or agents try to apply Cosmos RU guidance and pick the wrong provisioning model.
- **Suggested fix (learn_doc):** A one-page 'Provisioning model for DocumentDB' that contrasts Cosmos RU vs DocumentDB tiers, gives recommended dev defaults (M10), and shows a Bicep example with tier and storage parameters.

## [medium] Conservative IVF defaults for demos

- **What was missing:** The vector-search skill provides algorithm guidance (IVF/HNSW/DiskANN) but does not supply a conservative default for IVF parameters for small demo datasets (e.g., for N < 10k).
- **Where the agent looked:** documentdb-vector-search skill and the integrated vector store docs; readiness notes flagged the absence.
- **Effect on this build:** The builder chose nlist=100 arbitrarily; that value is not tuned to the tiny demo dataset and may be suboptimal or confusing to readers.
- **Suggested fix (agent_kit_rule):** Add a short rule in documentdb-vector-search: 'Demo defaults: when N < 10k, use vector-ivf with nlist=8..32 (choose 8 for N<100, 32 for N~10k). For production datasets compute nlist ~ max(1, N/1000) and document the heuristic.' Include a small code snippet showing how to compute nlist from collection.count_documents({}).

## [medium] Pinned Python driver versions

- **What was missing:** An explicit recommended and tested PyMongo version for samples in the driver guidance and/or in sample templates. The quickstarts include tested versions in some pages, but the documentdb-driver skill doesn't prescribe a single pinned version in code templates.
- **Where the agent looked:** documentdb-driver skill, quickstarts discovered via docs search; quickstart pages show tested driver versions but the agent kit guidance lacks a canonical pin.
- **Effect on this build:** The sample's requirements.txt uses ranges (pymongo>=4.4). Consumers and CI users benefit from pinned versions for reproducible installs; the builder had to pick a version without a single authoritative recommendation.
- **Suggested fix (learn_doc):** Add a brief 'Tested driver versions' section to the documentdb-driver skill and the quickstart templates showing exact pip pins for a stable reference (e.g., 'This sample was tested with PyMongo==4.19.0; pin that in requirements.txt or supply a constraints file for reproducible installs').

## [low] Agent discoverability for 'do not return embeddings' guidance

- **What was missing:** Although a vector-search example uses projection to omit embeddings (P20), a short explicit sentence in the public docs and agent-kit quickstarts encouraging authors not to return embeddings would reduce ambiguity for agents and builders.
- **Where the agent looked:** learn.microsoft.com vector-search docs, sample READMEs; search results returned examples but not a short explicit rule targeted at sample authors.
- **Effect on this build:** The sample does omit embeddings already, but explicit guidance would prevent accidental leakage in other samples.
- **Suggested fix (discoverability):** Add a one-line rule in the vector-search quickstart: 'Never return raw vector values in API responses; project out embedding fields.'

