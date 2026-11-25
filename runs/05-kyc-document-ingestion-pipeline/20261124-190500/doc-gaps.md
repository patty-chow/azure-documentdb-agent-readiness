# Documentation and tooling gaps: 05-kyc-document-ingestion-pipeline

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Complete .env.example for runtime settings

- **What was missing:** The .env.example omits an explicit DB_NAME / MONGODB_DATABASE variable and does not document MCP opt-in flags (ENABLE_MANAGEMENT_TOOLS / ENABLE_WRITE_TOOLS) that the build environment required to run management operations.
- **Where the agent looked:** Repository (.env.example, README) and Microsoft Learn quickstarts for Beanie and MongoDB connection patterns.
- **Effect on this build:** Small: the sample runs but verification steps relying on environment flags and an explicit DB name were not automated; index creation via MCP failed in this run and the README leaves DB selection implicit.
- **Suggested fix (learn_doc):** Update .env.example with DB_NAME=MONGODB_DATABASE=sample_fintech_05 and document optional flags for MCP verification (e.g., 'To allow automated MCP index creation during CI/local verification set ENABLE_MANAGEMENT_TOOLS=true and ENABLE_WRITE_TOOLS=true in your verification environment; this is opt-in by design'). Add a short README subsection 'Runtime variables' listing each env var, default, and example.

## [high] Idempotent seed and index-creation script

- **What was missing:** The seed script uploads sample documents but is not fully idempotent (two sample documents lack government_id so re-running the seed creates duplicates). There is no programmatic, idempotent index creation script that works in the default verification environment without enabling MCP write/management flags.
- **Where the agent looked:** Repository scripts/seed.py and events.jsonl (MCP create_index tool call failed).
- **Effect on this build:** Medium: prevented automated verification of index creation and made seed runs non-idempotent in some cases; the builder had to leave index creation as a manual step in README.
- **Suggested fix (sample_or_quickstart):** Provide a seed-and-init script that: (1) uses deterministic government_id values for all seed records (so upserts are idempotent), (2) creates declared indexes via Beanie init_beanie (documented) or via the MCP API but only after a runtime opt-in check, and (3) can be re-run safely without duplicating data. Document how to run the script and the expected result (e.g., 'After running init_seed.py twice the collection still contains three customers').

## [high] Beanie + async client authoritative guidance (Motor vs AsyncMongoClient)

- **What was missing:** Public guidance about exact recommended async client patterns for Beanie (Motor vs PyMongo's AsyncMongoClient) and the tested Beanie + driver combinations is scattered; prior-knowledge choices led to differing sample implementations.
- **Where the agent looked:** Microsoft Learn Beanie quickstarts, documentdb-driver and documentdb-connection skill resources, and general searches for 'Azure DocumentDB Beanie Motor'.
- **Effect on this build:** Medium: the builder chose Motor + Beanie (Beanie 1.x pattern) and pinned motor==3.5.3; quickstarts show Beanie 2 with AsyncMongoClient as a tested combination. This ambiguity may lead readers to mismatch versions or run into subtle incompatibilities.
- **Suggested fix (discoverability):** A one-page 'Beanie + Azure DocumentDB' note in product docs or the documentdb-connection skill that: (a) lists recommended Beanie versions and the corresponding async client (Motor vs AsyncMongoClient), (b) shows a minimal init example for each supported pattern, and (c) lists known tested combinations (Beanie 2 + PyMongo AsyncMongoClient with specific tested versions).

## [high] MCP tool opt-in discoverability and verification fallback

- **What was missing:** The build's programmatic attempts to create indexes and insert seed docs via MCP failed because management and write tools are disabled by default and require opt-in flags (events.jsonl shows ToolExecutionException with guidance to set ENABLE_MANAGEMENT_TOOLS/ENABLE_WRITE_TOOLS).
- **Where the agent looked:** events.jsonl MCP tool failure logs and the MCP skill docs.
- **Effect on this build:** High for automated verification: it prevented automated index creation and seed insertion during this run, which forced the builder to leave index creation as a manual step.
- **Suggested fix (discoverability):** Document the MCP opt-in requirements prominently in the MCP skill and in the sample README, including the exact env vars (ENABLE_MANAGEMENT_TOOLS, ENABLE_WRITE_TOOLS) and recommended security considerations for enabling them in CI or local debugging. Provide a fallback approach for verification that uses the app's init_db() to create indexes if MCP calls fail.

## [high] Unit testing without a live cluster

- **What was missing:** No unit tests or mocking harness were included to allow offline verification of parsing, schema validation, and logic.
- **Where the agent looked:** Repository (no tests folder) and requirements.txt showing pytest present.
- **Effect on this build:** Medium: maintainers and reviewers cannot run behavior-preserving tests offline; missing tests reduce confidence in behavior changes.
- **Suggested fix (sample_or_quickstart):** Add a tests/ directory with pytest-based unit tests that mock openai.Client responses and mock or stub Beanie/Motor operations (or use a simple in-memory replacement). Include instructions in README how to run tests locally without a live cluster.

## [medium] Connection timeout & retry guidance for async clients

- **What was missing:** The product skill and quickstarts describe TLS and provide examples for timeouts, but the sample did not add explicit driver timeout/query settings or example code showing safe defaults (serverSelectionTimeoutMS, socketTimeoutMS).
- **Where the agent looked:** documentdb-connection skill, quickstart docs (learn.microsoft.com references), repo code (app/src/app/db.py).
- **Effect on this build:** Low/Medium: lack of driver timeouts can cause long-hanging requests in poor-network conditions; the sample leaves this to readers rather than demonstrating recommended settings.
- **Suggested fix (agent_kit_rule):** Add a short rule or code snippet to the documentdb-connection skill and sample README showing how to instantiate an AsyncIOMotorClient with safe defaults, for example: AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000, socketTimeoutMS=60000, maxPoolSize=50). Explain the trade-offs and point to the skill for tuning guidance.

## [medium] Recommended OpenAI model & embedding dimension mapping

- **What was missing:** The build made a model choice (gpt-4o-mini) via a model_default decision; product documentation does not state a recommended extraction/embedding model or embedding dimensionality to use in samples.
- **Where the agent looked:** decisions.jsonl (D004), openai_client.py (OPENAI_MODEL default), and discovered practice searches for embedding dims.
- **Effect on this build:** Low: the sample defaults to gpt-4o-mini; if a future sample adds embeddings, not pinning the embedding model and dims may cause mismatch with vector-index parameters.
- **Suggested fix (learn_doc):** Add guidance in the sample README or a product 'LLM integrations' page recommending a default text-extraction model for structured extraction and the embedding model (with explicit output dimensions) to use for vector indexes. If you do not want to mandate a model, document that the embedding dimension must be set to the model's output vector size and show examples for common choices (e.g., OpenAI 'text-embedding-3-small' -> 1536 dims).

