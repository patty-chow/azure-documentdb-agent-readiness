# Documentation and tooling gaps: 01-product-catalog-with-vector-search

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Authoritative index creation command

- **What was missing:** A vendor-tested, exact createIndexes command and an example of the server-side query pipeline ($search / vector stage) that the provided Azure DocumentDB cluster accepts for IVF/knn indexes.
- **Where the agent looked:** Local repo files; no external documentation server was reachable in this run.
- **Effect on this build:** Seed script used a plausible MongoDB-7-style 'knnVector' createIndexes body which the cluster rejected. As a result server-side vector index creation and server-side vector querying were not demonstrated; the app falls back to client-side ranking.
- **Suggested fix (mcp_tool_or_description):** Provide a short 'Index creation' page in the agent kit and README that includes: (1) the exact createIndexes JSON accepted by the vendor for IVF and HNSW (example for the supported cluster), (2) the exact aggregation or $search stage to run top-k vector queries (with a k=10 example), and (3) a one-line command operators can paste into the seed script. Include a small test snippet in seed.py that runs only that command and prints the server response. Priority: high.

## [high] Embedding storage compatibility (Binary vs numeric array)

- **What was missing:** A clear statement about which embedding storage form (BSON Binary float32 bytes vs numeric-array field) the managed Azure DocumentDB cluster expects for server-side vector indexing.
- **Where the agent looked:** Local repo files; no external docs reachable.
- **Effect on this build:** The repo follows prompt by storing embeddings as BSON Binary bytes. If the target cluster requires numeric-array fields, the index attempt will fail or indexing will be impossible without changing the seed. This introduces friction for operators and requires manual adaptation.
- **Suggested fix (learn_doc):** Add a short 'Embedding storage' page to the sample README/agent kit that: (1) states which storage forms the cluster supports for vector indexes, (2) shows seed.py snippets for both Binary and numeric-array storage (with code to populate both fields), and (3) recommends adding an 'embedding_vector' array field when the cluster requires arrays. Priority: high.

## [high] Authentication method documentation

- **What was missing:** A statement of which authentication method the provided cluster uses (SCRAM credentials embedded in DOCUMENTDB_URI vs Microsoft Entra/Azure AD), and example connection-string format (with redacted credentials).
- **Where the agent looked:** Local run-environment files and repo; no external docs reachable.
- **Effect on this build:** The sample reads DOCUMENTDB_URI and defers to the URI; operators may be uncertain whether they must supply SCRAM credentials or a different auth flow. This can cause connection failures when operators supply the wrong credential type.
- **Suggested fix (learn_doc):** Add a short 'Connection string and auth' section to README describing the expected DOCUMENTDB_URI format (example redacted URI), and note how to adapt the code if using Azure AD or other auth methods. Priority: high.

## [high] Unit tests that run offline

- **What was missing:** Unit tests or a test harness that validate behavior without a live DocumentDB cluster (e.g., tests using mocks or mongomock).
- **Where the agent looked:** Local repo; no test files present.
- **Effect on this build:** The sample currently has no unit tests and verify_search.py requires a live cluster; this reduces confidence and increases friction for reviewers and contributors.
- **Suggested fix (sample_or_quickstart):** Add pytest tests that mock pymongo (or use mongomock) to exercise embed_text error handling, /search input validation, and the local ranking path; include instructions in README on how to run tests without a cluster. Priority: high.

## [medium] Embedding-provider env var and example

- **What was missing:** Before the run there was no authoritative statement of which env var to use for embeddings. The sample chose OPENAI_API_KEY and added .env.example, but the run lacked an external doc confirming this mapping.
- **Where the agent looked:** Local repo files; no external docs reachable.
- **Effect on this build:** The code and .env.example are consistent (OPENAI_API_KEY). This was a model-default decision and is implementable, but agents need an explicit local doc to avoid choosing a different env var (e.g., AZURE_OPENAI_KEY) in other contexts.
- **Suggested fix (discoverability):** Add a short note in README (or agent-kit rule) that the sample uses OpenAI text-embedding-ada-002 and expects OPENAI_API_KEY, and where to change it if using another provider. Priority: medium.

## [medium] Index tuning guidance

- **What was missing:** Practical guidance for choosing index parameters (nlist/nprobe/efConstruction, etc.) relative to dataset size and latency/recall trade-offs.
- **Where the agent looked:** Local repo files; no external docs reachable.
- **Effect on this build:** seed.py uses nlist=100 which is fine for a tiny sample but operators lack guidance on how to change it for larger datasets. Without guidance, users may choose poor defaults for production.
- **Suggested fix (learn_doc):** Add a README subsection 'Index tuning' that explains what nlist/efConstruction/efSearch (or the vendor equivalents) do, gives recommended ranges for small/medium/large datasets, and shows where to change parameters in seed.py. Priority: medium.

## [medium] Infrastructure as code

- **What was missing:** An example IaC snippet (Bicep/Terraform/ARM) showing the resource/provider that creates a DocumentDB cluster equivalent to the run environment, or an explicit statement that infra is out-of-scope.
- **Where the agent looked:** Local repo; no IaC files found.
- **Effect on this build:** Operators who want an end-to-end reproducible sample cannot create the required cluster from the repo; the sample relies on a pre-provisioned cluster.
- **Suggested fix (learn_doc):** Provide a small Bicep or Terraform example showing the resource-type and minimal options to create a comparable cluster (or clearly state in README that infra is out-of-scope and provide links to vendor docs). Priority: medium.

