# Documentation and tooling gaps: 11-visual-similarity-search-image-embeddings

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Model choice & preprocessing guidance

- **What was missing:** No public guidance in installed skills or Learn docs prescribing a specific CLIP checkpoint (model name) and the exact preprocessing steps required to guarantee a 512-dim output and the normalization used by the sample.
- **Where the agent looked:** Installed skills (documentdb-vector-search, documentdb-driver, documentdb-connection) and Microsoft Learn were searched (see readiness findings).
- **Effect on this build:** Builder selected 'openai/clip-vit-base-patch32' by default (decision D003). A mismatch between model output dimension and index dimensions would silently produce incorrect results; the sample is consistent, but a different model could break the index.
- **Suggested fix (learn_doc):** Add a short 'AI model' guidance page in the sample template recommending a specific checkpoint (e.g., openai/clip-vit-base-patch32), state its output dimension (512), show minimal preprocessing code (resize, normalization), and mention that embeddingDim must match the index 'dimensions' parameter.

## [high] .env.example completeness and model credentials

- **What was missing:** .env.example lists DOCUMENTDB_URI only. It does not list optional model-provider environment variables (e.g., HF_TOKEN) or toggles the MCP tools use (ENABLE_MANAGEMENT_TOOLS) used in this environment.
- **Where the agent looked:** Repo files, installed skills, and builder notes. The HF transformers warning seen in events indicates HF_TOKEN may be relevant.
- **Effect on this build:** Missing HF_TOKEN placeholder may confuse builders who hit HF Hub rate limits or need to use a private model; missing ENABLE_MANAGEMENT_TOOLS placeholder hides the MCP opt-in required by the environment and led to a management-tool failure at runtime.
- **Suggested fix (discoverability):** Extend .env.example with placeholders: HF_TOKEN="<hf-token-or-empty>", ENABLE_MANAGEMENT_TOOLS="false", ENABLE_WRITE_TOOLS="false" and document in the README why and when to set them (e.g., when running MCP tools in CI you may opt in).

## [high] Pin dependencies guidance / example requirements

- **What was missing:** requirements.txt uses version ranges rather than pinned, exact tested versions.
- **Where the agent looked:** app/requirements.txt and quickstart docs found tested PyMongo versions in Microsoft Learn quickstarts.
- **Effect on this build:** Unpinned dependencies can lead to install-time surprises or incompatibilities with the cluster (driver wire-protocol compatibility).
- **Suggested fix (agent_kit_rule):** Provide a template requirements.txt with exact pinned versions that match the verification environment (for example, include the exact PyPI versions used during test runs) and add a short note in README 'Pinned dependency versions were tested against the cluster and Python X.Y'.

## [high] Unit tests that run without a live cluster

- **What was missing:** No unit tests with mocked DB or model were provided.
- **Where the agent looked:** Repo tests: only scripts/test_search.py exists which calls the real model and cluster.
- **Effect on this build:** CI and local developers cannot run tests offline; verification cannot run lightweight test suites without provisioning a cluster or heavy downloads.
- **Suggested fix (sample_or_quickstart):** Add pytest-based unit tests using fixtures that monkeypatch get_db() to return a mongomock (or patch the collection) and patch image_to_embedding() to return a deterministic vector. Include a CI job example that runs these tests without a live cluster.

## [high] Explicit guidance: DocumentDB vector field encoding (array vs binary)

- **What was missing:** The public docs emphasize numeric arrays for vectors and documented encodings rather than arbitrary BSON binary subtype packing. The sample stores embeddings as bson.Binary subtype 0x09, which conflicts with examples that use numeric arrays.
- **Where the agent looked:** Integrated vector store docs and vector-search examples on Microsoft Learn and documentdb-vector-search skill.
- **Effect on this build:** The app stored embeddings as binary subtype 0x09 and the cluster returned type errors when querying in some experiments (events include 'Invalid type: expected an array type field' and '$search must appear as the initial stage' errors). Without explicit guidance, agents may pick unsupported encodings and fail at query time.
- **Suggested fix (naming_or_disambiguation):** Add a prominent doc section titled 'How to store vectors' that states: 'Prefer embedding fields as arrays of numbers (float32) for cosmosSearch vector indexes, or use the documented binary encoding options — do not assume arbitrary BSON binary subtype 0x09 will work. Include code examples for storing arrays and for the one supported binary encoding if applicable.'

## [medium] Index parameter tuning guidance in README

- **What was missing:** README explains how to create an index but does not explain how index parameters (numLists, nProbes, lSearch, dimensions) should be tuned as data grows.
- **Where the agent looked:** app/README.md and vector-search skill docs.
- **Effect on this build:** The sample created an IVF index with numLists=100 which is fine for 20 items, but without tuning guidance a user might leave defaults for larger datasets and get poor recall or high latency.
- **Suggested fix (learn_doc):** Add a 'Index tuning' subsection explaining numLists ~ (#docs/1000) heuristic for IVF, how to increase nProbes/efSearch to improve recall, and point to vector-search skill docs for HNSW/DiskANN tradeoffs.

## [medium] MCP management-tools opt-in and diagnostics

- **What was missing:** The environment requires ENABLE_MANAGEMENT_TOOLS=true to allow MCP create-index and other management tools; this opt-in and its consequences are not obvious in README.
- **Where the agent looked:** events.jsonl shows MCP create-index failed with 'Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true to opt in.'
- **Effect on this build:** Builder attempted to use MCP tool; the tool failed due to environment opt-in, causing a fallback to PyMongo. This added complexity and required the builder to implement a PyMongo createIndexes fallback.
- **Suggested fix (discoverability):** Document the MCP opt-in flag and recommended CI/Dev settings in README: explain when to set ENABLE_MANAGEMENT_TOOLS and ENABLE_WRITE_TOOLS and the security tradeoffs.

