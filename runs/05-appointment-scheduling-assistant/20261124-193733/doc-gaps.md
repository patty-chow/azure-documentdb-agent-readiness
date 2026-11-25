# Documentation and tooling gaps: 05-appointment-scheduling-assistant

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Persisted-memory guidance (prior_knowledge_only)

- **What was missing:** No public DocumentDB-specific guidance was found that explicitly recommends what minimal conversation identifiers to persist (conversationId, lastAppointmentId) or how to store them safely for agent memory.
- **Where the agent looked:** Searched installed skills, and web searches: 'azure documentdb conversation memory persistence', 'azure documentdb agent memory persist conversation identifiers best practice'.
- **Effect on this build:** The builder used in-memory BufferMemory (ephemeral). Without explicit guidance, implementers may persist full conversational context or PII inadvertently.
- **Suggested fix (learn_doc):** A short guidance page: 'Agent memory with Azure DocumentDB' that: (1) explains recommended minimal persisted keys for conversational memory (conversationId, lastAppointmentId), (2) gives a small DocumentDB-backed memory example storing only identifiers, (3) lists PII redaction guidance and encryption recommendations, and (4) shows how to resume an agent using stored identifiers.

## [high] Retry/429 guidance discoverability

- **What was missing:** The sample did not implement retries/429 handling. Although retry guidance exists in the documentdb-connection skill, it is not highlighted in the sample README as a must-have for production booking flows.
- **Where the agent looked:** Checked installed skill documentdb-connection and sample README.
- **Effect on this build:** This build runs correctly against a live cluster in a test run, but a production-like workload or RU throttling could cause transient failures that the sample does not demonstrate handling for.
- **Suggested fix (discoverability):** Add a 'Reliability' subsection to README referencing the documentdb-connection guidance and a short code snippet showing a retryWithBackoff wrapper and how to handle 429/Retry-After.

## [high] Unit-test mocking guidance

- **What was missing:** No example tests that mock the MongoDB driver or a local DocumentDB Gateway container were present in the repo; the README does not point to a recommended mock strategy.
- **Where the agent looked:** Repo README and installed skills (documentdb-local-deployment) and general repo files.
- **Effect on this build:** The verification relies on a live cluster; the repo lacks offline tests suitable for CI and gallery validation.
- **Suggested fix (sample_or_quickstart):** Add a short 'Testing' page that includes: (a) a lightweight unit test that stubs the mongodb module (example using sinon or jest mocks), (b) an optional docker-compose snippet to run the DocumentDB Gateway locally (documentdb-local-deployment skill), and (c) CI guidance to run tests without network access.

## [medium] Overlapping-slot reschedule guidance (prior_knowledge_only)

- **What was missing:** No authoritative DocumentDB-specific page described the recommended application-level pattern for preventing overlapping slot times when rescheduling or creating slots (e.g., indexed overlap queries and why DB-level partial unique constraints are insufficient).
- **Where the agent looked:** Searched installed skills and performed web searches: 'azure documentdb enforce non-overlapping time ranges unique constraint', 'documentdb prevent overlapping time ranges booking constraint'.
- **Effect on this build:** The sample uses discrete slot documents for fixed times (no slot-time rewriting), so it avoided the problem. Future samples that alter slot boundaries could accidentally create overlapping bookings if they rely on DB uniqueness semantics alone.
- **Suggested fix (learn_doc):** A 'Preventing overlapping time ranges' how-to that shows example queries (start < newEnd && end > newStart), recommended indexes and code patterns to enforce this atomically (transaction + conditional checks), and sample JS snippets for DocumentDB.

## [medium] LLM provider & model selection (decision defaults)

- **What was missing:** The starter prompt left model/provider unspecified; the builder defaulted to OpenAI (model_default). There is no central guidance in the sample or skills that instructs which model or environment variables to prefer for DocumentDB samples (OpenAI vs Azure OpenAI vs on-prem).
- **Where the agent looked:** Checked the repo README and installed skills; searched product docs for sample conventions.
- **Effect on this build:** The builder chose OpenAI and documented OPENAI_API_KEY; other implementers might pick Azure OpenAI or provider-specific env names, causing inconsistency across samples and making discovery by an agent harder.
- **Suggested fix (agent_kit_rule):** An agent-kit rule that standardizes LLM env var names across samples (e.g., OPENAI_API_KEY, OPENAI_MODEL, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY) and a README subsection offering examples for OpenAI and Azure OpenAI with minimal configuration examples.

## [medium] Memory persistence default (decision default)

- **What was missing:** The builder defaulted to in-memory BufferMemory for simplicity (decision reason_source=model_default). There is no product guidance telling builders when to prefer ephemeral memory vs durable memory for samples that demonstrate appointment workflows.
- **Where the agent looked:** Checked README and installed skills for memory persistence guidance; none gave a default for sample builds.
- **Effect on this build:** The sample demonstrates conversational continuity but the memory is ephemeral; readers might assume persistence across restarts and build fragile demos.
- **Suggested fix (agent_kit_rule):** A short rule in the agent kit that says: 'Samples should default to ephemeral in-memory memory for demos; if persistence is required, add a second example that persists only identifiers (conversationId, lastAppointmentId) to DocumentDB or Redis and document security considerations.'

## [medium] Cleanup instructions in README

- **What was missing:** The README shows how to seed and run verification but lacks explicit cleanup steps to remove seeded documents or indexes.
- **Where the agent looked:** app/README.md and seed.js
- **Effect on this build:** Users may not know how to remove sample data from a live test cluster and may accidentally leave sample documents/indexes in test accounts.
- **Suggested fix (learn_doc):** Add a 'Clean-up' section to README that provides a small script or a mongo CLI snippet that deletes seeded documents (deleteMany on slots/appointments) and how to remove sample indexes and collections.

