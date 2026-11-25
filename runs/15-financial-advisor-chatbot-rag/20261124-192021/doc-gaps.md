# Documentation and tooling gaps: 15-financial-advisor-chatbot-rag

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Management tools opt-in

- **What was missing:** The MCP/documentdb management tools required an explicit opt-in (ENABLE_MANAGEMENT_TOOLS) to create indexes in this execution environment. The builder attempted to create a vector index but the tool refused with 'Management tools are disabled by default.'
- **Where the agent looked:** events.jsonl (documentdb_create_index calls and error), documentdb-vector-search skill resources
- **Effect on this build:** Index creation failed; the sample could not exercise DB-side vector retrieval and fell back to client-side ranking, changing the demonstration from DB-native RAG to an in-process demo.
- **Suggested fix (mcp_tool_or_description):** Document the management-tools opt-in requirement prominently in the MCP skill and quickstart, and provide a fallback: a packaged create-index JSON and a driver-based idempotent index-creation snippet that authors can include in the seed script. Also add a short troubleshooting note explaining the ENABLE_MANAGEMENT_TOOLS opt-in and its security rationale.

## [high] Vector storage format (Float32)

- **What was missing:** No authoritative example in DocumentDB docs explains whether to store vectors as JSON arrays or as binary Float32 typed arrays and how to pack/unpack them in Node.js for DocumentDB indexing.
- **Where the agent looked:** documentdb-vector-search skill resources and public searches (relevant queries returned no useful result)
- **Effect on this build:** Seeded vectors are stored as JS arrays of numbers (works for small demos) but authors cannot be sure whether binary Float32 is required or preferred for performance/space in production.
- **Suggested fix (learn_doc):** A short page 'Vector storage format' explaining recommended storage formats (Float32Array -> BSON Binary approach), sample Node.js code to write/read binary vectors, and how to create an index that expects the stored format. Include note about mixing models/dimensions and the need for a dimension metadata field.

## [high] Avoid returning internal vectors in responses

- **What was missing:** The sample returns the embedding payload in normal responses. Public guidance (documentdb-vector-search) recommends not returning raw vectors in normal query responses.
- **Where the agent looked:** documentdb-vector-search skill resources and the app source
- **Effect on this build:** Potential information exposure and inefficient response sizes; the sample violates the discovered best practice P12.
- **Suggested fix (agent_kit_rule):** Add a rule in the agent kit: 'Do not include embedding fields in assistant-facing responses; only include identifiers and scores. For admin tools, add a flag `--include-vectors`.' Also add a short snippet showing how to project out the embedding field in driver queries.

## [high] Tests without live cluster

- **What was missing:** No unit tests that mock out DocumentDB and embeddings are present; test script runs the demo which needs a live cluster.
- **Where the agent looked:** app/package.json and repo test files (none found)
- **Effect on this build:** CI or gallery reviewers cannot run automated tests without a live cluster; this reduces confidence in sample correctness.
- **Suggested fix (sample_or_quickstart):** Add a small 'test' directory with unit tests that mock MongoClient and embedding/LLM functions (examples using sinon/jest). Document how tests simulate the seed and retrieval behaviors and how to run them in CI without secrets.

## [high] Index lifecycle and idempotent index creation docs

- **What was missing:** Although vector-index docs exist, authors need a short, copy-paste Node.js snippet that performs idempotent create-if-missing for a cosmosSearch vector index.
- **Where the agent looked:** documentdb-indexing and documentdb-vector-search skill resources; repo lacked an idempotent create-index snippet
- **Effect on this build:** Builder tried to create index via MCP, which failed in this environment; absence of an idempotent driver-based snippet increased fragility of the build.
- **Suggested fix (sample_or_quickstart):** Provide a small Node.js helper `ensureVectorIndex(db, collection, spec)` that checks existing indexes and issues the DocumentDB-specific createIndexes/createSearchIndexes call when missing, with a safe env switch for management-tool opt-in.

## [medium] Node LlamaIndex guidance

- **What was missing:** There is no authoritative Microsoft guidance or skill describing how to build a 'LlamaIndex' integration in Node.js. Builders will choose ad-hoc approaches or reimplement LlamaIndex semantics, which leads to inconsistent samples.
- **Where the agent looked:** readiness report, installed skills, Microsoft Learn (no Node LlamaIndex guidance found)
- **Effect on this build:** The builder implemented a LlamaIndex-like flow in Node instead of using an official LlamaIndex, which is defensible but diverges from the exact starter-prompt wording and may confuse authors expecting a Python-based LlamaIndex example.
- **Suggested fix (agent_kit_rule):** Add a short 'LlamaIndex integration' guidance page to the agent kit: (1) If an official Node library exists, reference it; (2) otherwise provide a recommended pattern (Node-side retriever + prompt composition, or a small Python LlamaIndex microservice example) and code snippets to implement it.

## [medium] Decision reasons from model_default

- **What was missing:** Several build decisions (e.g., using deterministic local embeddings, choice of embedding model dims, fallback LLM behavior) have reason_source 'model_default'; no public source was cited that would allow an agent to reproduce or verify those defaults.
- **Where the agent looked:** decisions.jsonl (D004, D005, D018)
- **Effect on this build:** Agents or builders reading only the skills may not know whether to choose local deterministic embeddings vs a particular external embedding model; this leaves subtle choices implicit in the sample.
- **Suggested fix (discoverability):** Add a short 'Sample defaults' section to the sample README and to the agent-kit that enumerates default choices (embedding model & dims, LLM provider env var names, fallback behavior) and explains rationale and how to override them.

