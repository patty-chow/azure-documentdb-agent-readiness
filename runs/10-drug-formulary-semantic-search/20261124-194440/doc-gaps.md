# Documentation and tooling gaps: 10-drug-formulary-semantic-search

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Index creation & verification

- **What was missing:** A sample-level script or seed step that programmatically creates the cosmosSearch vector index (using createIndexes with cosmosSearchOptions) and immediately verifies via explain() or MCP that the index is effective and the 'dimensions' parameter matches the embedding model.
- **Where the agent looked:** Repo files; documentdb-vector-search skill resources; Microsoft Learn examples in events (vector-create-diskann-index.md and vector-knn-query.md).
- **Effect on this build:** Index creation was left as a manual step. Without programmatic creation/verification, the sample cannot be end-to-end verified and may run full-collection scans or fail at query time if index dims mismatch.
- **Suggested fix (mcp_tool_or_description):** Provide a 'create_index.py' or extend the seed script with: 1) check for existing index and its cosmosSearchOptions; 2) if missing or mismatched, createIndexes with {key:{embedding:'cosmosSearch'}, cosmosSearchOptions:{kind:'vector-hnsw', dimensions: EMBED_DIM, similarity:'COS', maxDegree:32, lBuild:50}}; 3) run explain() on a sample query and print executionStats. Document default parameters and how to tune them for larger datasets.

## [high] LlamaIndex usage for embeddings

- **What was missing:** Public, sample-level guidance and an example showing how to use LlamaIndex as the embedding provider for both seed and runtime code (the prompt asked for LlamaIndex but the builder used openai directly).
- **Where the agent looked:** Repo files; installed skills; general web search via learn_microsoft_docs_search returned no sample LlamaIndex usage tied to DocumentDB in the sample.
- **Effect on this build:** Builder defaulted to direct OpenAI calls; the sample does not demonstrate the starter prompt's requested LlamaIndex integration. This makes the sample inconsistent with the starter prompt and the gallery expectations.
- **Suggested fix (sample_or_quickstart):** Add a short code snippet and a 'Using LlamaIndex' section in the README and seed script demonstrating creating a LlamaIndex embedding object and using it for both seed_data and main runtime. Show fallback to OpenAI calls and environment variables for provider keys.

## [high] Unit tests without live cluster

- **What was missing:** A set of unit tests and examples showing how to run them without a live cluster (mocking pymongo, mocking embedding provider) so tests can run in CI and locally without secrets.
- **Where the agent looked:** Repo tests and installed skills; no sample-level guidance or test mocks found in the repository.
- **Effect on this build:** Current tests skip unless environment variables are present; CI or reviewers cannot run tests without provisioning secrets or a live cluster.
- **Suggested fix (sample_or_quickstart):** Add tests using mongomock or pytest monkeypatch to mock get_collection(), and mock LlamaIndex/OpenAI embedding calls. Provide example tox/pytest configuration and a short doc section describing running unit tests vs integration tests.

## [medium] Guidance on index parameters for sample scale

- **What was missing:** A README subsection describing recommended index parameters for the small demo dataset and how to change them for larger datasets (e.g., HNSW: maxDegree, lBuild; DiskANN/IVF: numLists, lBuild).
- **Where the agent looked:** Repo README and skills (documentdb-vector-search) were consulted. The skill docs contain the guidance but the sample README does not surface it.
- **Effect on this build:** Builder shipped an example index shape in a run report but did not embed that guidance in the sample README. A user may create an index with unsuitable defaults for scale.
- **Suggested fix (discoverability):** Add a 'Tuning the vector index' section with explicit defaults for the demo and instructions for scaling, with links to the vector-search skill docs and example createIndexes payloads.

## [medium] Dependency pinning guidance

- **What was missing:** A statement in the README or sample policy that dependencies should be fully pinned for reproducible builds, plus a pinned requirements.txt example.
- **Where the agent looked:** requirements.txt in repo and sample packaging guidance in skills.
- **Effect on this build:** requirements.txt uses ranges for some packages; reproducible installation may vary across environments.
- **Suggested fix (agent_kit_rule):** Add an agent-kit rule or README note: 'Pin all runtime dependencies in requirements.txt; use pip-tools or constraints files for reproducible installs.' Update requirements.txt to exact versions.

## [medium] Entra ID authentication examples

- **What was missing:** A short example showing how to connect using Microsoft Entra ID (authMechanism=MONGODB-OIDC) or a note explaining why the sample uses connection-string auth and how to switch to Entra ID for production.
- **Where the agent looked:** documentdb-security skill and Microsoft Learn docs were consulted; sample README uses connection string but does not show Entra ID example.
- **Effect on this build:** Sample uses connection-string auth by default; users looking to follow production best practices may not see an example to swap to Entra ID.
- **Suggested fix (discoverability):** Add an 'Authentication' subsection describing how to use Entra ID (example driver code snippet) and when to prefer managed identity & RBAC.

## [low] Decision provenance for model & framework defaults

- **What was missing:** A public guidance page or agent-kit rule that documents the sample-level defaults (preferred web framework and default embedding model/dimension) so agents do not rely on unstated model defaults.
- **Where the agent looked:** decisions.jsonl and events.jsonl show many decisions used reason_source='model_default'.
- **Effect on this build:** Several builder choices (FastAPI, text-embedding-3-small, 1536 dims) were model defaults rather than explicit user-provided inputs. That is acceptable but should be documented so subsequent builders and agents choose consistently.
- **Suggested fix (learn_doc):** Add a short 'Sample defaults' page listing preferred framework, default embedding model and dim, and reasoning. Cross-link from the sample README.

