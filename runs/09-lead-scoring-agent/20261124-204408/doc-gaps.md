# Documentation and tooling gaps: 09-lead-scoring-agent

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Optimistic concurrency for scoring writes

- **What was missing:** No Microsoft Learn page explicitly showing the recommended optimistic-concurrency pattern (version field or conditional findOneAndUpdate) for scoring/update workflows in Azure DocumentDB's MongoDB API.
- **Where the agent looked:** Microsoft Learn (DocumentDB MongoDB API), skill docs, and general web searches (see discovered_practices 'searches_with_no_useful_result').
- **Effect on this build:** The sample performs unconditional updateOne on the lead document when writing scores; without OCC the sample risks clobbering concurrent updates in multi-writer scenarios.
- **Suggested fix (learn_doc):** A short Learn page titled 'Implement optimistic concurrency for data-plane updates (MongoDB API on Azure DocumentDB)'. Outline: why OCC matters for scoring writes, example using a version field and findOneAndUpdate filter, an example using conditional $set with previous version, guidance on when to use multi-document transactions vs idempotent patterns, and a small code snippet in Node.js showing findOneAndUpdate with version check.

## [high] LLM PII & operational guardrails

- **What was missing:** There is no Azure DocumentDB-specific guidance on redacting PII before sending documents to LLMs, or example site patterns for feature-flagging LLM calls and deterministic fallbacks in the context of DocumentDB-hosted data.
- **Where the agent looked:** Microsoft Learn, DocumentDB skills, general web (no vendor-specific page found).
- **Effect on this build:** The sample sends full lead fields (name, email) to the LLM by default. Builders will likely do the same; without guidance they may expose PII to LLM providers or lack deterministic fallbacks for offline runs.
- **Suggested fix (learn_doc):** A guidance page 'Using LLMs safely with Azure DocumentDB data' describing: recommended redaction/hashed identifiers, examples of minimal prompts, a recipe for feature flags and fallbacks (heuristic scoring), and an example Node.js middleware that strips or hashes PII fields before prompt-building.

## [high] Discoverability: 'use environment vars' guidance

- **What was missing:** Although the quickstart demonstrates reading DOCUMENTDB_URI from env, a single authoritative agent-kit rule for env-var name conventions and examples for LLM env names (OPENAI_API_KEY, OPENAI_CHAT_MODEL, OPENAI_EMBEDDING_MODEL) is missing.
- **Where the agent looked:** Agent skills, README examples, and sample repos. There are examples but no consistent centralized convention.
- **Effect on this build:** Env var name mismatches in code (.env.example uses OPENAI_MODEL while scoreLead.js expects OPENAI_CHAT_MODEL) caused a small but real usability problem.
- **Suggested fix (agent_kit_rule):** An agent-kit rule 'Env var naming conventions' listing canonical names (DOCUMENTDB_URI, DB_NAME, OPENAI_API_KEY, OPENAI_CHAT_MODEL, OPENAI_EMBEDDING_MODEL, EMBEDDING_DIMS, SCORER_ID, MODEL_VERSION) and requiring .env.example to include all names used in code.

## [medium] Vector-index quick reference for samples

- **What was missing:** Builders need a small, copy-pasteable example of createIndexes with cosmosSearchOptions, and a short table of recommended algorithm/parameter defaults for small vs large datasets (HNSW vs IVF vs DiskANN, dims mapping to common embedding models).
- **Where the agent looked:** DocumentDB vector docs and skill pages (found vector docs but no tiny 'sample-ready' snippet targeted at gallery authors).
- **Effect on this build:** Builder chose to avoid creating vector indexes to preserve seed reliability. Without concise examples a future builder may create incorrect index commands or pick wrong dimensions.
- **Suggested fix (sample_or_quickstart):** A 1-page 'Vector index quickstart' with a db.runCommand({createIndexes:...}) example for HNSW/IVF/DiskANN, environment variable EMBEDDING_DIMS usage, and recommended defaults: small sample (dims=1536, kind=vector-hnsw, M=16, efConstruction=100), production hints, and a note to create vector indexes after bulk ingestion.

## [medium] Index Advisor quick diagnostic

- **What was missing:** A tiny example script and README instructions showing how to run $indexStats and connect Index Advisor to a sample workload, focused on small gallery data.
- **Where the agent looked:** DocumentDB Index Advisor docs were present but no 'one-click' sample in the agent kit.
- **Effect on this build:** Builders don't exercise index-advisor checks in small seeds; missing guidance reduces likelihood they'll validate index usefulness before publishing.
- **Suggested fix (discoverability):** A sample diagnostic script index-check.js that runs explain() and $indexStats for the sample queries, and README steps to run it after seeding.

