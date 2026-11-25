# Documentation and tooling gaps: 15-prescription-refill-agent

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Embedding model dims and provider

- **What was missing:** The starter prompt and repository contain no statement of which embedding model (provider and specific model) to use and therefore no guidance that ties embedding dimensionality to the vector-index dimensions or how to set the index accordingly.
- **Where the agent looked:** Inspected repository (no embedding code) and searched installed skills (documentdb-vector-search) and Microsoft Learn (vector search docs) via learn_microsoft_docs_search.
- **Effect on this build:** The sample did not implement any vector-index or embedding-based features (the builder left vector search out of the demo). Without explicit model/dimension guidance a later contributor may create a mismatched vector index that fails or degrades recall/latency.
- **Suggested fix (learn_doc):** A short page titled 'Choosing embeddings and vector-index dimensions for Azure DocumentDB' that includes: 1) recommended embedding providers and example models (OpenAI ada/xxx, Azure OpenAI text-embedding-3-small/large, etc.) and their dimensionality; 2) example createIndexes JSON for DiskANN/HNSW/IVF using that dimensionality; 3) a matrix advising which index kind to use for demos vs medium vs large corpora; 4) a short 'how to change the index dimension' subsection for the sample's seed script and README.

## [high] Explain() / MCP explain usage for index verification

- **What was missing:** Although the query-optimizer skill documents explain() and MCP tools, the sample does not include a developer workflow that runs explain('executionStats') for the agent's critical queries (prescription lookup, eligibility check).
- **Where the agent looked:** Inspected repository (no explain() calls) and the documentdb-query-optimizer skill.
- **Effect on this build:** No deterministic check that the created indexes actually cover the sample queries; developers may ship an index that does not prevent COLLSCANs or high docExamined counts.
- **Suggested fix (discoverability):** Ship a small 'verify-indexes.js' script (or extend scripts/test-eligibility.js) that runs explain('executionStats') for the sample's key lookups and prints totalKeysExamined / totalDocsExamined / executionTimeMillis; document how to interpret the output in README.

## [high] Tests that run offline (mocked DB)

- **What was missing:** The repository lacks unit tests that run without a live DocumentDB cluster (no in-memory or mocking strategy provided).
- **Where the agent looked:** Inspected repository (scripts/test-eligibility.js uses real DB) and README (no offline test instructions).
- **Effect on this build:** Continuous integration and quick local validation are harder; contributors must have access to an Azure cluster to run tests.
- **Suggested fix (sample_or_quickstart):** Add a 'tests' folder with unit tests that mock Mongoose models (or use mongodb-memory-server) and update README with instructions to run tests locally and in CI. Include an example GitHub Actions workflow that runs tests using the in-memory server.

## [high] Agent memory TTL / PHI guidance

- **What was missing:** The sample uses a DB-backed agent memory collection but does not create a TTL index or document retention policy or give guidance about PHI storage/encryption for memory.
- **Where the agent looked:** Inspected app/src/models/AgentMemory.js and README; searched documentdb-indexing and documentdb-security skills.
- **Effect on this build:** Agent memory may grow without bound and may store medication identifiers in cleartext without documented retention or encryption guidance.
- **Suggested fix (learn_doc):** Add a short subsection to README: 'Agent memory retention & PHI handling' that shows how to create a TTL index, how to store only canonical identifiers instead of detailed PHI, and what disclaimers to include. Also add a sample seed/upgrade script that creates the TTL index: AgentMemory.collection.createIndex({ updatedAt: 1 }, { expireAfterSeconds: <n> }).

## [medium] Beanie / Node mismatch guidance

- **What was missing:** The prompt asked for 'Beanie ODM' together with Node.js, a cross-language mismatch. There is no prominent guidance telling builders what to do when the starter prompt requests an ODM that exists only in a different language.
- **Where the agent looked:** Readiness report, repository, and skills. Searched docs for Beanie references and for guidance about choosing an ODM for Node samples.
- **Effect on this build:** The builder made a pragmatic substitution (Mongoose) and documented it in README. Without clear guidance agents or builders may blindly attempt an impossible combination or choose an inconsistent stack.
- **Suggested fix (naming_or_disambiguation):** Add a short 'ODM guidance for cross-language prompts' rule to the agent-kit: when a starter prompt names an ODM not available in the requested runtime, prefer the native ODM for that runtime and document the substitution in README and in the decisions log. Example language: 'If the prompt requests Beanie for a Node.js sample, substitute Mongoose and record the decision.'

