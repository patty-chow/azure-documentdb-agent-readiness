# Documentation and tooling gaps: 14-loan-origination-workflow-orchestration

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Driver-choice guidance (Motor vs AsyncMongoClient)

- **What was missing:** Clear, prominent documentation stating the recommended async Python driver (AsyncMongoClient vs Motor) for Beanie/Beanie+async usage and migration examples.
- **Where the agent looked:** documentdb-agent-kit skills (documentdb-connection), Microsoft Learn compatibility pages, web searches for 'Motor vs AsyncMongoClient Azure DocumentDB'.
- **Effect on this build:** Builder used Motor (AsyncIOMotorClient) in app/src/db.py even though the connection skill recommends AsyncMongoClient; this yields a mismatch between installed-skill guidance and the sample's implementation.
- **Suggested fix (discoverability):** Add a short 'Python async drivers' page to the documentdb-connection skill and the agent kit README. Content: why prefer PyMongo's AsyncMongoClient for new async code, example get_client() using AsyncMongoClient, migration notes from Motor to AsyncMongoClient, and sample code showing init_beanie(database=client.get_database(...)) with AsyncMongoClient.

## [high] Optimistic concurrency guidance for orchestrators

- **What was missing:** An explicit, Azure-DocumentDB-specific recommendation and code snippet for optimistic concurrency (use version int or expected_state in filter; handling conflict by retry/re-read).
- **Where the agent looked:** documentdb-agent-kit skills, Microsoft Learn; searches for 'Azure DocumentDB optimistic concurrency version field' returned no single canonical guidance.
- **Effect on this build:** The sample filters on expected current_state (acceptable) but does not include a version field or documented retry policy. Agents can't reliably implement best-practice optimistic-concurrency without a canonical example.
- **Suggested fix (learn_doc):** A one-page doc 'Orchestrator concurrency patterns' describing two patterns: (1) Filter-on-expected-state (example find_one_and_update) and (2) version-field pattern (schema: schema_version/int), with example update filter, atomic $set/$inc/$push, and retry loop pseudocode.

## [high] Cap or externalize transition history

- **What was missing:** A short recommendation and example for capping transition arrays or moving transition history to a separate collection to avoid the 16 MB document limit.
- **Where the agent looked:** documentdb-data-modeling skill & general docs; although the skill mentions the 16 MB limit, there was no short cookbook snippet showing the $push $slice option or transitions collection pattern.
- **Effect on this build:** The sample app pushes transitions into an unbounded array (transitions: List[Transition] = []), which risks document size growth with no guidance in-code on capping.
- **Suggested fix (learn_doc):** An 'Audit logs and event history' snippet in data-modeling skill showing (a) $push with $each + $slice examples to keep N last events, (b) schema and index sample for a separate transitions collection keyed by application_id, and (c) cost/performance trade-offs.

## [high] Unit tests that do not require a live cluster

- **What was missing:** A small testing guide and a reusable test fixture (or mocking helper) showing how to unit-test Beanie models and orchestrator logic without connecting to a live DocumentDB cluster (e.g., mocking get_client or using the local DocumentDB gateway Docker image for integration tests).
- **Where the agent looked:** local-deployment skill and test frameworks; no concise example combining Beanie model unit tests with a mocked DB was found in the discovered docs.
- **Effect on this build:** The included test calls init_beanie and therefore requires a live cluster; CI or gallery reviewers expecting offline unit tests will find the sample failing unless they supply a DB or modify tests.
- **Suggested fix (sample_or_quickstart):** Add tests/unit/README explaining techniques: (1) pure-Pydantic model tests that never call init_beanie, (2) pytest fixture that monkeypatches src.db.get_client to return a mocked client, and (3) an optional docker-compose snippet using the DocumentDB local gateway for integration tests.

## [high] Tool availability & MCP management tools opt-in

- **What was missing:** The build assumed the documentdb MCP server's management tools (create_index/insert) would be available; in this environment management tools are opt-in and failed with an explicit exception.
- **Where the agent looked:** events.jsonl shows documentdb_create_index attempted and failed with 'Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true to opt in.'
- **Effect on this build:** The attempt to create indexes via the MCP server failed; as a result indexes were not created via management tooling in this run, and the builder left index creation to Beanie/assumptions.
- **Suggested fix (mcp_tool_or_description):** In the documentdb MCP documentation and the agent kit, document when management tools are disabled by default, how to opt in (ENABLE_MANAGEMENT_TOOLS), and recommend programmatic, idempotent index creation in sample code so builds do not rely on management-tool availability.

## [medium] Index creation idempotent examples and discoverability

- **What was missing:** Clear example showing index creation approaches (init_beanie index creation vs explicit pymongo create_index) and which indexes Beanie will auto-create.
- **Where the agent looked:** Beanie docs, documentdb-indexing skill, repository code. The discovery found no authoritative one-line confirmation that init_beanie will create all Indexed() fields as MongoDB indexes for Azure DocumentDB.
- **Effect on this build:** The builder declared an Indexed field (current_state) but also attempted to call the MCP create_index tool which failed due to environment restrictions. Buyers of the sample may be uncertain whether to rely on Beanie's startup index creation or to programmatically create indexes.
- **Suggested fix (discoverability):** Add a short item in the documentdb-indexing skill: 'Beanie and indexes' that says what init_beanie creates (with example), and include a minimal programmatic fallback snippet (await db.get_collection(...).create_index(...)) and the recommended idempotent pattern.

## [medium] Model-default decision: LLM provider unspecified

- **What was missing:** The starter prompt and run-environment left open which LLM provider to use; the builder defaulted to stub agents. There is no public guidance / agent-kit rule telling builders whether samples should prefer stubbed determinism or real LLM calls for gallery samples.
- **Where the agent looked:** Prompt, README, installed skills; no agent-kit rule found.
- **Effect on this build:** The builder implemented deterministic stubs (good for reproducibility), but the decision was recorded with reason_source 'model_default' which requires product-team guidance in the agent kit to be reproducible across builders.
- **Suggested fix (agent_kit_rule):** An agent-kit rule: 'For gallery samples that reference LLMs, default to deterministic/stub agents for CI and local runs; provide optional real-provider configuration documented in README. If real LLM calls are included, require explicit README steps and env-vars and mark tests as integration that require live keys.'

## [medium] Driver-version pin guidance for Python

- **What was missing:** Although requirements.txt is pinned, there is no authoritative guidance page with tested combinations of Python / beanie / motor / pymongo / langchain for the sample runtime (Python 3.13).
- **Where the agent looked:** Project files and installed skills; no explicit 'tested pinned stacks' doc in the agent kit.
- **Effect on this build:** The builder had to iteratively pick working package versions (events show pip failures and successive adjustments). A small compatibility matrix would reduce iteration and CI friction.
- **Suggested fix (learn_doc):** Add a 'tested matrix' page to the agent kit listing recommended versions for sample stacks (for example: Python 3.13 → beanie==1.21.0, motor==3.1.1, pymongo==4.4.0, langchain==X). Include notes about platform-specific wheels and macOS/ARM caveats.

