# Documentation and tooling gaps: 04-regulatory-reporting-orchestration

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Regulatory filing schema

- **What was missing:** No authoritative regulatory filing schema (XBRL or jurisdictional JSON schema) was available in the prompt, skills, or repo. The builder used a synthetic JSON shape.
- **Where the agent looked:** Installed skills, README and search for 'regulatory schema' in project files and skills; readiness findings note the missing schema.
- **Effect on this build:** The filing format is synthetic; validators and filing agent produce a demo JSON rather than a schema-validated filing. This limits the sample's usefulness for users who expect a real regulator-compliant output.
- **Suggested fix (learn_doc):** A short 'Regulatory filing' page describing example schemas to target, one or two minimal JSON/XBRL fragments the sample can use, and a 'How to swap in a real schema' guide (validation rules, strict schema validation steps, sample XSD/JSONSchema files).

## [high] Embedding model and index dimension pairing

- **What was missing:** No explicit public guidance (in skills/docs) or sample convention that ties an embedding model choice to the vector-index dimension used when creating indexes.
- **Where the agent looked:** Installed vector-search skill, readiness searches, and repo files.
- **Effect on this build:** Builder omitted vector-index creation to avoid dimension/model coupling and left EMBEDDING_MODEL/DIMS as optional in .env.example; sample therefore does not demonstrate vector search.
- **Suggested fix (discoverability):** Add a short 'Embedding → Index dimension' doc that lists common embedding models (provider + model name) and their output dimensions and an example createIndexes payload that uses EMBEDDING_DIMS from config. Include copy-paste code to create an HNSW/IVF index with the correct 'dimensions' value.

## [high] Workflow-run resumability examples

- **What was missing:** Public examples that show a minimal workflow-run document schema and an authoritative example of how to resume a run after a failure (state transitions, idempotency keys).
- **Where the agent looked:** Installed skills and public docs; searches returned no specific DocumentDB-hosted examples.
- **Effect on this build:** The sample logs steps and timestamps (good) but there is no guide demonstrating resume/retry logic or dedup keys; an agent might not implement safe retries without a concrete pattern.
- **Suggested fix (agent_kit_rule):** A short rule and example document (fields: run_id, start_ts, steps[], step.status, last_checkpoint, dedup_key) and a code snippet showing how an orchestrator resumes from the last successful step by reading workflow_runs and conditionally skipping already-completed operations.

## [high] Public guidance for P21/P22/P23/P24 (prior_knowledge_only items)

- **What was missing:** Several practices (workflow-run resumability, transaction cautions, PII redaction guidance, and the limits of mongomock for vector/index/transaction testing) were present as reasonable prior knowledge but not documented specifically for Azure DocumentDB in the installed skills.
- **Where the agent looked:** Installed skills and public searches listed in discovered_practices 'searches_with_no_useful_result'.
- **Effect on this build:** Agents and builders may assume MongoDB-like behavior; lacking explicit DocumentDB docs for these items risks subtle mistakes (PII logged, incorrect assumptions about transactions, or tests that miss service-level behaviors).
- **Suggested fix (learn_doc):** Short pages or callouts in the indexing/monitoring/security/ testing docs that (a) define a recommended workflow-run document pattern and resume logic, (b) warn about mongomock limitations and show integration-test recipes, (c) specify PII-handling recommendations for workflow logs, and (d) state the transactional semantics caveat and when to test on live clusters.

## [high] Discoverability: default model env var naming

- **What was missing:** The repository contains inconsistent environment variable names for the chat/model variable (agents.py reads MODEL_NAME while .env.example lists CHAT_MODEL), reducing discoverability and causing potential runtime confusion.
- **Where the agent looked:** Repository files (.env.example, app/src/agents.py) and events trace showing .env.example was written with CHAT_MODEL.
- **Effect on this build:** Risk of user-facing misconfiguration: filling CHAT_MODEL as in .env.example will not affect agents.py which reads MODEL_NAME, making LLM features silent/confusing.
- **Suggested fix (naming_or_disambiguation):** Fix .env.example to include MODEL_NAME or change agents.py to read CHAT_MODEL. Add a one-line check in startup that prints configured/expected env names (without secrets) so misconfigurations are obvious.

## [medium] Local dev & integration test guidance for DocumentDB

- **What was missing:** A concise recipe showing the DocumentDB local gateway image, the port (10260), and how to run integration tests that exercise explain(), indexes and vector features (mongomock misses these).
- **Where the agent looked:** documentdb-local-deployment skill and readiness searches.
- **Effect on this build:** Builders might use mongomock for everything and miss important service-level behaviors; the sample mixes mongomock unit tests and live-cluster integration runs but lacks a clear 'local dev' guide.
- **Suggested fix (learn_doc):** A 'Local development and integration tests' page including Docker commands for the DocumentDB local gateway, connection-string examples (port 10260), and an integration-test scaffold that runs only when a live/local gateway is reachable.

## [medium] Entra ID authentication patterns for application code

- **What was missing:** Clear code examples demonstrating how to use Microsoft Entra ID (managed identity) for data-plane authentication with DocumentDB (if enabled) and how to wire Azure.Identity into PyMongo or a wrapper.
- **Where the agent looked:** documentdb-security skill and Microsoft docs; some enabling docs exist but code patterns are sparse.
- **Effect on this build:** The sample defaults to a connection string in DOCUMENTDB_URI. If teams want an RBAC/managed-identity example, there is no copy-paste snippet.
- **Suggested fix (discoverability):** A short how-to page showing how to enable Microsoft Entra ID on a cluster, how to obtain a token in Python (Azure.Identity) and inject it into the driver or a proxy, and an example Bicep snippet that enables auth-allowed-modes.

