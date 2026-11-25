# Documentation and tooling gaps: 20-open-banking-api-cache-layer

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Explicit index-creation in seed/startup

- **What was missing:** An explicit example in the quickstart/agent-kit guidance showing model.createIndexes() or syncIndexes() in a seed/startup script to guarantee index creation rather than relying on Mongoose autoIndex behavior.
- **Where the agent looked:** Searched the documentdb-indexing and Mongoose quickstart (events.jsonl reading documentdb-indexing skill and the quickstart page).
- **Effect on this build:** The sample's seed script relies implicitly on schema-defined indexes and Mongoose behavior. In practice the indexes were present during verification, but relying on autoIndex can cause surprise in production (autoIndex may be disabled) and risks index-build races on large collections.
- **Suggested fix (agent_kit_rule):** Add an agent-kit rule/snippet: 'Always call await Model.createIndexes() at application startup or in seeding scripts and log the result; do not rely on autoIndex in production. Example code snippet included.'

## [high] Unit test strategy for local runs

- **What was missing:** Clear recommendation and example in the agent-kit or quickstart for unit/integration tests that run without a live cluster (use the DocumentDB local gateway Docker image or mongodb-memory-server for unit tests).
- **Where the agent looked:** Searched documentdb-local-deployment skill and quickstart docs (events.jsonl).
- **Effect on this build:** The builder verified against the live cluster and did not add unit tests that run offline. This slows CI and may make reproducing test failures harder for contributors without access to a cluster.
- **Suggested fix (sample_or_quickstart):** A README/Test section and a small test scaffold demonstrating (a) a unit test that uses mongodb-memory-server or the DocumentDB local gateway Docker image, (b) CI guidance to skip live tests when no cluster is available, and (c) a small example Jest test that exercises getOrUpdate with a mock fetcher.

## [medium] Driver version guidance discoverability

- **What was missing:** Quick, prominent guidance in the Mongoose quickstart or the agent-kit driver skill that states the recommended Mongoose major/version for Node 24 (the quickstart does have this, but an agent could miss it).
- **Where the agent looked:** Searched Microsoft Learn 'Quickstart: Connect Mongoose to Azure DocumentDB' and the Mongoose compatibility notes (events.jsonl: learn_microsoft_docs_search queries).
- **Effect on this build:** The builder chose Mongoose ^7.5.0. That choice is workable but diverges from the quickstart's tested Mongoose 9.x recommendation and makes the sample less aligned with the official examples and tested driver matrix.
- **Suggested fix (discoverability):** Add a short boxed note to the Mongoose quickstart and the documentdb-driver skill: 'Recommended: Mongoose 9.x (tested: 9.12.1). If you must use Mongoose 7.x, verify compatibility with your chosen serverVersion.'

## [medium] Pinning and lockfile policy

- **What was missing:** A short policy in the agent-kit or quickstart indicating how samples should pin dependencies for the gallery (exact versions in package.json or committing lockfile) and what format to use for different languages.
- **Where the agent looked:** Searched repository for existing policy and README (app/README.md) and Microsoft docs; none govern gallery-specific pinning policy in this project.
- **Effect on this build:** The project used caret ranges in package.json. Without explicit gallery guidance a builder may assume lockfile is sufficient; reviewers may expect exact pins in package.json or a requirements.txt for Python samples.
- **Suggested fix (learn_doc):** A single-page gallery policy: 'For Node samples commit package-lock.json and prefer exact versions in package.json for gallery releases; for Python provide requirements.txt with pins.' Include a one-line example and recommended CLI to produce deterministic lockfiles.

## [medium] Retry guidance for fetcher

- **What was missing:** Specific guidance on application-level bounded retries for upstream fetches (e.g., axios retry wrapper) and idempotency considerations for non-idempotent writes.
- **Where the agent looked:** documentdb-driver and quickstart docs (events.jsonl); the driver skill discusses retryWrites but not an application-level fetcher retry pattern.
- **Effect on this build:** The sample fetcher (axios) does not implement bounded retries; background refresh swallows errors which is acceptable for a demo but a production sample should show bounded retries and idempotency safeguards.
- **Suggested fix (learn_doc):** Add a short example in the driver/connection skill: 'Wrap upstream fetches with a bounded retry (exponential backoff) for transient network errors and ensure idempotency or deduplication for writes; example axios-retry wrapper with max attempts = 3 and jitter.'

## [low] Middleware vs wrapper choice guidance

- **What was missing:** No public guidance on whether a sample should expose middleware, an HTTP-client wrapper, or both for cache patterns.
- **Where the agent looked:** Searched quickstarts and agent-kit skills; nothing prescribes the recommended sample API surface.
- **Effect on this build:** The builder implemented both middleware and wrapper. This decision was recorded with reason_source 'model_default' and implemented, but agents may make differing interface choices without central guidance.
- **Suggested fix (agent_kit_rule):** Add a short guideline in the documentdb-agent-kit: 'For caching samples, offer both an Express middleware and a fetch-wrapper when feasible; include a minimal demo for each.' Provide code skeletons for both patterns.

## [low] Demo TTL default guidance

- **What was missing:** No authoritative guidance on demo-friendly TTL values for caching examples (how short is safe/representative).
- **Where the agent looked:** Searches for 'cache TTL demo values' and quickstart pages; none prescribe demo TTLs.
- **Effect on this build:** The builder used TTL=5s and staleWindow=10s for a short one-shot demo (reasonable). A sample consumer might prefer slightly longer values or an explicit note about how to set production values.
- **Suggested fix (learn_doc):** Add a short cookbook paragraph: 'For quick demos use TTL=5-10s and staleWindow ~2x TTL; for production choose TTL based on freshness needs, and record expected load patterns.'

