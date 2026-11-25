# Documentation and tooling gaps: 11-correspondent-banking-risk-screener

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Embedding model & dimensions

- **What was missing:** No authoritative guidance in the repo or public DocumentDB docs about which embedding model to choose for the sample and the matching vector dimension to use. The builder picked text-embedding-3-small (1536 dims) by default but that was a model_default decision.
- **Where the agent looked:** Readiness search over Microsoft Learn vector-search pages and installed documentdb-vector-search skill; events.jsonl show learn_microsoft_docs_search queries around vector index examples.
- **Effect on this build:** The sample assumed 1536 dims in .env.example and index creation, which is fine for that model but requires a clear README note when substituting a different model (e.g., OpenAI vs Azure OpenAI vs HuggingFace). Incorrect dims would cause index creation or query-time mismatches.
- **Suggested fix (learn_doc):** A short README section titled 'Choosing an embedding model' listing supported providers, default model (text-embedding-3-small -> 1536 dims), how to override EMBEDDING_MODEL and EMBEDDING_DIMS, and a verification command to ensure dimensions match before creating indexes.

## [high] Vector index creation payload example

- **What was missing:** A canonical, copy-paste example of the exact runCommand payload shape for createIndexes with cosmosSearchOptions (including mapping the embedding path, dimensions, kind and algorithm params).
- **Where the agent looked:** Searched Microsoft Learn vector-search docs and loaded documentdb-vector-search skill; the sample's db.py used an incorrect key mapping in one place which led to index recognition problems.
- **Effect on this build:** Index creation attempted but either was created with an unexpected name or not usable for queries on some collections; this caused vector queries to fall back to metadata searches during verification.
- **Suggested fix (mcp_tool_or_description):** Add a 'Create a vector index' subsection to the README containing an exact db.command(...) JSON example: createIndexes: <coll>, indexes:[{name:..., key:{'embedding':'cosmosSearch'}, cosmosSearchOptions:{kind:'vector-hnsw', dimensions:1536, similarity:'COS', m:16, efConstruction:200}}]. Explain common errors (IndexOptionsConflict, CommandNotSupported) and how to inspect indexes via the MCP or portal.

## [high] Search result projection of similarity score

- **What was missing:** Public examples showing projection of {$meta:'searchScore'} in $search + cosmosSearch pipelines are in docs, but the sample did not return or persist the score despite the docs recommending it.
- **Where the agent looked:** Integrated vector store docs and documentdb-vector-search skill (found examples), events.jsonl show that the skill was loaded.
- **Effect on this build:** Risk scoring and auditability suffer because the raw similarity/searchScore is not returned or stored; current score derivation uses match counts instead.
- **Suggested fix (agent_kit_rule):** A rule for agent-kit: 'Always include searchScore in $search results and persist it with review runs for auditability' plus a small code snippet showing the $project stage to include searchScore.

## [high] Unit tests without live cluster

- **What was missing:** No tests were added and there is no example for mocking DocumentDB for CI. The README did not explain test strategy.
- **Where the agent looked:** Repo and README; no tests directory found.
- **Effect on this build:** Consumers cannot run automated tests in CI without providing a cluster; this reduces confidence in refactors and in PR gating.
- **Suggested fix (sample_or_quickstart):** Add a tests/ folder with unit tests using mongomock or pytest monkeypatch to mock get_db() and test embed/score logic; document how to run tests in README.

## [high] Infrastructure as code for mongoClusters

- **What was missing:** No IaC templates showing Microsoft.DocumentDB/mongoClusters resource were included, and the readiness findings note developers often confuse this with databaseAccounts.
- **Where the agent looked:** Repo content; Microsoft docs were found but no sample IaC in repo.
- **Effect on this build:** Gallery consumers expecting an IaC example will not find one and might attempt to use databaseAccounts resource incorrectly.
- **Suggested fix (mcp_tool_or_description):** Provide a small Bicep (and optionally Terraform/AzAPI) snippet that creates Microsoft.DocumentDB/mongoClusters with param defaults for 'tier' and 'storage', and a note in README showing az documentdb mongocluster CLI examples.

## [medium] Index-tuning guidance & README instructions

- **What was missing:** No guidance in the README about picking index kind (HNSW/DiskANN/IVF) and algorithm parameters for demo vs production or how to change them when scaling.
- **Where the agent looked:** Searched installed documentdb-vector-search skill and Microsoft vector-search docs.
- **Effect on this build:** The sample used HNSW defaults without algorithm parameters; users running larger datasets may choose a suboptimal index or run out of memory.
- **Suggested fix (discoverability):** README section: 'Index choices and tuning' describing DiskANN/HNSW/IVF recommendations (P30), recommended parameters for demo (e.g., HNSW M=16, efConstruction=200, efSearch tunable at query time), examples to change cosmosSearchOptions in src/db.py.

## [medium] Seed data & seed tagging

- **What was missing:** No public guidance in DocumentDB docs for sample-data tagging conventions (seeded=true, seed_version). The sample did not tag seeded docs beyond schemaVersion.
- **Where the agent looked:** Searches for 'how to mark seeded data azure documentdb' returned no useful results (discovered_practices.searches_with_no_useful_result).
- **Effect on this build:** Seeder is idempotent but seeded documents are indistinguishable from real documents except for schemaVersion; this complicates cleanup and filtering in mixed environments.
- **Suggested fix (learn_doc):** Add a short note to README and seed scripts to tag seeded docs with seeded=true and seed_version=N and provide a cleanup script that removes seeded docs by this tag.

## [medium] Fallback documentation and marking

- **What was missing:** No public guidance page in the repo documenting how fallback results are flagged; fallback logic is implemented but not documented to callers.
- **Where the agent looked:** README and code; fallback paths present in code (app/src/agent.py lines 59-66, 80-86) but not explained.
- **Effect on this build:** Callers cannot programmatically tell whether results came from vector search or fallback metadata search; this affects auditability and user expectations.
- **Suggested fix (agent_kit_rule):** Add README note and change API to include 'search_source' or 'fallback': true/false in response; include a short example of when fallbacks run and how they are flagged.

