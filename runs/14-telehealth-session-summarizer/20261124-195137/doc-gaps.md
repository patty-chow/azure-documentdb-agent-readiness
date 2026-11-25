# Documentation and tooling gaps: 14-telehealth-session-summarizer

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Vector-index creation examples and parameter defaults

- **What was missing:** The public guidance explains index kinds (DiskANN/HNSW/IVF) but a concise sample showing exact JSON createIndex/createSearchIndexes payloads with recommended defaults for small (<=1k), medium (~50k) and large (>100k) corpora was not discoverable as a one-line recipe in this repo.
- **Where the agent looked:** Installed documentdb-vector-search skill and Microsoft Learn vector-search docs; README includes a short note but not parameter defaults.
- **Effect on this build:** Builder omitted vector-index creation by default to avoid misconfiguring a live cluster. Users will need clear examples to create appropriate indexes safely.
- **Suggested fix (learn_doc):** Ship a short 'vector-index quick recipe' page: example createSearchIndexes JSON for DiskANN/HNSW/IVF, mapping of dataset size -> recommended algorithm, example parameters (m, efConstruction, numLists, lBuild, lSearch), and a short snippet showing how to validate embedding dimensions and trigger index rebuilds when model/dimension changes.

## [high] Search endpoint error-handling guidance

- **What was missing:** The checklist expected /search to return specific error responses for empty queries and embedding failures; no small, public pattern page shows a recommended API signature and exact error codes/messages for embedding failures or empty queries in a DocumentDB sample.
- **Where the agent looked:** Repo README, installed skills, and Microsoft Learn; did not find a single small example HTTP handler illustrating the exact failure modes and codes.
- **Effect on this build:** The sample does not include a /search endpoint; when authors add search they may omit clear, consistent error handling.
- **Suggested fix (sample_or_quickstart):** Add a minimal FastAPI 'search' quickstart: endpoint signature, JSON schema for request/response, 400 response for empty query with example body, 502/503 for embedding service failures, and an example of returning the similarity score along with results.

## [high] Test patterns for unit tests without a live cluster

- **What was missing:** A succinct example showing how to write unit tests for a DocumentDB-backed sample that run without a live cluster (e.g., using mongomock or pytest fixtures, or the local DocumentDB gateway image).
- **Where the agent looked:** Repo and installed skills; while local gateway docs exist, there is no short recipe demonstrating the common pattern of mocking PyMongo calls for unit tests.
- **Effect on this build:** The provided tests skip when DOCUMENTDB_URI is absent; the sample lacks isolated unit tests that CI can run without secrets or live clusters.
- **Suggested fix (sample_or_quickstart):** Add a 'Testing' quickstart page that includes: (A) an example pytest fixture using mongomock to mock PyMongo, (B) an optional docker-compose for the DocumentDB local gateway for integration tests, and (C) guidance for CI (use mocked tests by default; run integration tests only when credentials are available).

## [medium] LlamaIndex pipeline examples for samples

- **What was missing:** The starter prompt required a 'Python LlamaIndex pipeline' but public guidance and the installed skills do not include a short, canonical example that shows exactly how to plug LlamaIndex into Azure DocumentDB vCore clusters for this demo (simple example: ingest transcript text, construct prompt context engineering, call LlamaIndex LLM predictor, parse JSON output, upsert to clinical_summaries).
- **Where the agent looked:** Inspected installed skills and Microsoft Learn quickstarts; searched for LlamaIndex + Azure DocumentDB examples (learn search results include general LlamaIndex guidance but not a one-page sample for this pipeline).
- **Effect on this build:** Builder opted to call OpenAI directly rather than use LlamaIndex APIs. That made the sample simpler but deviated from the prompt; an agent following the prompt strictly might have implemented LlamaIndex instead.
- **Suggested fix (agent_kit_rule):** Provide a short 'LlamaIndex + Azure DocumentDB' recipe in the agent kit: a code snippet showing how to create a LlamaIndex Document store backed by Azure DocumentDB, build a PromptHelper that enforces the four-section structure, call the LLM via LlamaIndex's LLMPredictor, and parse/validate the JSON. Include an example that uses text-embedding-3-small and how to wire optional vector indexes.

## [medium] Dependency pinning guidance for gallery samples

- **What was missing:** Gallery guidance asking for exact pinned dependency versions or a recommended constraints/pip-compile workflow. repos often use loose ranges which can cause reproducibility issues.
- **Where the agent looked:** Repo requirements.txt and installed skills docs; no single page prescribes exact pinning policy for DocumentDB samples.
- **Effect on this build:** requirements.txt uses ranges (>= / <). This is workable but reduces reproducibility for gallery verification.
- **Suggested fix (discoverability):** Add a short README subsection: 'Pin dependencies for the gallery' that recommends either exact pins in requirements.txt or a secondary constraints.txt lockfile produced by pip-compile, plus commands to regenerate pinned constraints.

## [medium] Index-migration and compound-index examples

- **What was missing:** A short migration pattern example that shows adding a compound index safely (create if not exists, background build considerations) and how to include such changes in a versioned seed/migration script.
- **Where the agent looked:** doc indexing and local-deployment skills; no single migration snippet in this repo.
- **Effect on this build:** The sample creates a single-field patientId index; compound indexes expected for sorted queries are not included and authors may not know how to roll them out safely.
- **Suggested fix (learn_doc):** Provide an 'index migration' example describing idempotent index creation, background building, monitoring index build progress, and a sample script to add a compound patientId+createdAt index as a migration step.

