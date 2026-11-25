# Documentation and tooling gaps: 06-order-history-timeline-agent

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Search API behavior (/search)

- **What was missing:** Checklist expects a /search HTTP endpoint that returns clear, machine-readable errors (empty query and embedding-failure cases). No public sample or guidance in the agent kit shows the exact HTTP error format for /search in DocumentDB sample apps.
- **Where the agent looked:** Searched installed skills and repo templates; no authoritative example for a gallery sample's /search error semantics was found.
- **Effect on this build:** Developer did not implement an HTTP search endpoint (the sample is CLI/scripted). Without a standard example, other builders may implement inconsistent error messages and status codes.
- **Suggested fix (agent_kit_rule):** An agent-kit rule and short sample showing a minimal /search endpoint (FastAPI) that returns 400 for missing query (JSON: {error: 'empty query'}), 502 for embedding service failures, and includes 'score' in search result items. Include a text snippet and a one-file example.

## [high] Unit tests that run offline / local gateway guidance

- **What was missing:** There is not a standard gallery recipe showing how to run the repository's tests without a live Azure DocumentDB cluster (mocking or local Gateway usage).
- **Where the agent looked:** Searched installed skills (documentdb-local-deployment) and Microsoft docs; local Gateway is described but there is no short cookbook that shows test fixtures or mongomock usage for gallery samples.
- **Effect on this build:** Tests in this sample run only against the live cluster; CI authors or gallery reviewers might expect unit-tests to run in CI without access to a cluster.
- **Suggested fix (sample_or_quickstart):** A quickstart page titled 'Testing DocumentDB samples offline' showing two patterns: (1) run the DocumentDB Gateway container (docker-compose) with env vars to mimic production, with example docker-compose.yml and how to point tests at it; (2) a small Pytest fixture that swaps in mongomock for the pymongo client for pure-unit tests. Include code snippets and an example CI job step.

## [high] Pin tested dependency versions

- **What was missing:** Gallery expects pinned dependencies for reproducibility; no authoritative guidance in the agent kit on how to choose pinned versions for DocumentDB + LangChain samples was found.
- **Where the agent looked:** Searched sample templates and skills for a dependency pinning policy; none provided a standard constraints file or pinned requirements sample.
- **Effect on this build:** The builder relaxed pins to allow pip to resolve packages (decisions D009/D010). This reduces reproducibility and may lead to future surprises in CI.
- **Suggested fix (agent_kit_rule):** A short rule: 'All gallery samples must include exact pinned requirements.txt (or constraints.txt) matching the tested runtime; update pins when revalidating the sample and include a 'tested-on' entry in README.' Provide an example requirements.txt and CI step to freeze versions.

## [medium] Normalize NL time in agent memory

- **What was missing:** No public Azure DocumentDB or agent-kit guidance documenting the recommended pattern for normalizing natural-language time expressions (e.g., 'last month') into deterministic ISO date ranges stored in an agent's conversation state.
- **Where the agent looked:** Searched installed skills and Microsoft docs; practice P27 recorded as prior_knowledge_only (no public source found). Tools loaded: documentdb-* skills; searches: 'Azure DocumentDB agent memory normalize last month' returned no useful result.
- **Effect on this build:** Builder implemented normalization from application knowledge (SimpleContext) but an agent that relies on training-memory only cannot confirm this pattern from public docs.
- **Suggested fix (learn_doc):** A short agent-kit page titled 'Normalize natural-language time in agent memory' describing: (1) recommended canonicalization (ISO 8601 ranges, timezone policy), (2) examples for 'last month', 'yesterday', 'last 7 days', (3) how to store in conversation state and use in tool calls, and (4) how to test this logic. Put this in the agent-kit 'patterns' section.

## [medium] Seeding performance/batching guidance

- **What was missing:** Best-practice guidance recommending bulk_write/insert_many for seeding sample data and an example for idempotent bulk upserts was not present in the seed templates used by the builder (the local-deployment skill mentions idempotent seeding but not an explicit bulk-write sample).
- **Where the agent looked:** Searched documentdb-local-deployment skill and public docs; bulk-executor docs exist (P12) but a concise seeded-sample example for insert_many/upsert in the agent-kit repo is absent.
- **Effect on this build:** The seed uses per-document upserts which are correct and idempotent but slower and more RU/round-trip intensive than batched writes.
- **Suggested fix (sample_or_quickstart):** Add a short 'Efficient seeding' recipe showing insert_many with ordered=False and a bulk_write upsert example, plus a note on idempotence and how to combine index creation with bulk loads.

