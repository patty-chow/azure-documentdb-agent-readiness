# Documentation and tooling gaps: 12-clv-prediction-pipeline

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] LLM output audit trail

- **What was missing:** No public guidance or sample code for recording LLM outputs and rationale as an append-only audit/history subdocument for Azure DocumentDB was found. The builder could not find authoritative documentation on this pattern for DocumentDB.
- **Where the agent looked:** Searched Microsoft Learn and installed skills (search string: 'Azure DocumentDB record LLM outputs rationale append-only'); discovered no useful public result.
- **Effect on this build:** Sample overwrote top-level clv fields (clv_score, clv_tier, clv_rationale) rather than writing an append-only history. This loses change history and makes audits harder.
- **Suggested fix (learn_doc):** Page title: 'Recording model outputs and audit history in Azure DocumentDB'. Outline: (1) Motivation and audit requirements; (2) Recommended schema (clv_history array entries with timestamp, model, score, tier, rationale); (3) Example code: $push update pattern, idempotent append-only writes, retention strategies and compaction; (4) Example migration to backfill historic single-field writes into history subdocument; (5) Guidance on storing PII and sensitive rationale.

## [high] Sanitizing LLM outputs

- **What was missing:** No public guidance specific to Azure DocumentDB advising to sanitize/validate LLM-generated fields (enums, numeric ranges, lengths) before writes was found.
- **Where the agent looked:** Searched Microsoft Learn and installed skills (search string: 'Azure DocumentDB sanitize LLM outputs validate before write'); no useful public result.
- **Effect on this build:** The sample writes LLM outputs back to customer documents without explicit validation; malformed LLM output could corrupt fields or violate types.
- **Suggested fix (learn_doc):** Page title: 'Validating and sanitizing model outputs before database writes'. Outline: (1) Why validate (integrity, safety); (2) Enumerated validation rules (allowed tiers, numeric bounds, length caps); (3) Example Python code validating/parsing JSON and rejecting/normalizing bad outputs; (4) Logging/audit guidance and recovery steps.

## [high] Tests without a live cluster

- **What was missing:** No example test harness demonstrating how to run unit tests without connecting to a real DocumentDB cluster (mocking/mongomock) was found in the sample or product docs.
- **Where the agent looked:** Repo test files and installed skills; general search for 'DocumentDB python tests mongomock' returned community patterns but no official sample.
- **Effect on this build:** The repo's unit tests require the DOCUMENTDB_URI and a reachable cluster; CI that cannot access the cluster will fail integration tests.
- **Suggested fix (sample_or_quickstart):** Add a 'Testing' quickstart showing (1) how to run integration tests against a dev cluster; (2) how to run unit tests locally with mongomock or by monkeypatching get_customers_collection; include example pytest fixtures.

## [high] Retry & bulk-write best-practices for examples

- **What was missing:** The sample and product docs do not include a short, copy-pasteable pattern showing a safe retry policy and a bulkWrite pattern for applying model outputs at scale.
- **Where the agent looked:** Installed connection and connection-retry guidance exists in skills but there is no short example in the gallery template demonstrating retries + bulkWrite for CLV updates.
- **Effect on this build:** The sample lacks retries (risking transient failures) and lacks a bulk-write update path (inefficient for many customers).
- **Suggested fix (sample_or_quickstart):** Add a 'Safe write patterns' quick snippet: (1) idempotent bulk_write example; (2) retry wrapper template with exponential backoff and idempotency notes; (3) when to use bulk_write vs per-customer updates.

## [medium] MCP management tool opt-in discoverability

- **What was missing:** The MCP tool returned an error indicating management tools are disabled by default (ToolExecutionException referencing ENABLE_MANAGEMENT_TOOLS). There was no prominent, discoverable guidance in the sample that told a developer the MCP server may require opt-in for management commands or how to fallback.
- **Where the agent looked:** Events showed the tool failure; README and code did not document MCP opt-in. Searched the documentdb skills and Microsoft Learn for 'ENABLE_MANAGEMENT_TOOLS' references (no concise developer guidance surfaced in repo).
- **Effect on this build:** The index creation MCP tool failed during the run and the builder had to create the index via a pymongo workaround. This added friction and required a manual workaround.
- **Suggested fix (discoverability):** Agent-kit rule or README note: 'If documentdb_create_index fails with management-tools disabled, set ENABLE_MANAGEMENT_TOOLS=true for MCP or fall back to pymongo client-based create_index. Example command and environment variable explanation.'

## [medium] Default LLM/model selection guidance

- **What was missing:** There is no single product-level recommendation for which hosted model/provider to use for small gallery samples (OpenAI vs Azure OpenAI vs local). The builder used a model_default to pick gpt-3.5-turbo.
- **Where the agent looked:** Installed skills and project docs; no prescriptive guidance on default LLM choice for samples.
- **Effect on this build:** The builder chose gpt-3.5-turbo as a default; that choice is reasonable but leaves reproducibility and credential env-var naming to the builder. OPENAI_API_KEY was not set in this run so the LLM step did not execute.
- **Suggested fix (agent_kit_rule):** Rule: 'Samples using an LLM must declare the provider and environment variable name (OPENAI_API_KEY or AZURE_OPENAI_KEY) in .env.example and README; prefer provider X for gallery samples and include a note how to switch providers.'

## [medium] Dependency pinning guidance

- **What was missing:** No sample-level guidance or template enforcing exact pinned dependencies for reproducible builds (requirements-lock.txt) was present.
- **Where the agent looked:** Repo files; no lock file present.
- **Effect on this build:** requirements.txt uses >= ranges; different runs may resolve different upstream versions causing non-deterministic behavior.
- **Suggested fix (agent_kit_rule):** Agent-kit rule: 'Gallery samples must include pinned dependency artifact (requirements-lock.txt or constraints) for reproducible CI; include instructions to regenerate with pip-compile.'

## [medium] Transactions naming/compatibility clarification

- **What was missing:** Public prior beliefs contradicted by the product docs on multi-document transactions. This mismatch risks a model or developer assuming transactions behave like another product.
- **Where the agent looked:** DocumentDB product docs (compatibility) and installed skills; prior belief confusion between Cosmos DB RU model and DocumentDB vCore model was observed in readiness notes.
- **Effect on this build:** No transaction usage in this sample, but developers could be misled when designing multi-document updates for CLV across collections/partitions.
- **Suggested fix (naming_or_disambiguation):** Add a short 'Transactions and compatibility' note to the quickstart clarifying that this vCore DocumentDB offering supports multi-document transactions and linking to the exact docs and examples.

