# Documentation and tooling gaps: 04-earnings-call-rag-assistant

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Embedding model & index-dimension selection

- **What was missing:** No canonical guidance page that tells sample builders which embedding models and dimensions to pick for DocumentDB RAG samples (e.g., 'use all-MiniLM-L6-v2 → dims=384' vs OpenAI 1536-dim models) and how to change the vector index dims.
- **Where the agent looked:** DocumentDB skills, Microsoft Learn quickstarts, and the agent-kit skill resources (documentdb-vector-search, vector-create-diskann-index.md).
- **Effect on this build:** Builder picked all-MiniLM-L6-v2 by default and documented dims=384 in README; index creation was left to the operator. The lack of a single recommended model+dims made the builder log a model_default decision (D005) and reduced automation.
- **Suggested fix (learn_doc):** A short 'Embedding model choices for RAG on DocumentDB' page that (a) lists example models (local miniLM 384, OpenAI 1536), (b) maps each model to the index 'dimensions' value, (c) includes a sample createIndexes JSON for each dims value and index kind, and (d) recommends which models to use for small demo vs production.

## [high] Create vector index: exact createIndexes JSON and how to run it

- **What was missing:** A discoverable example that copies the exact createIndexes payload for DocumentDB (cosmosSearchOptions) and a small script that runs it idempotently via MCP or mongosh.
- **Where the agent looked:** documentdb-vector-search skill, Microsoft Learn vector-search docs, sample repo README.
- **Effect on this build:** Builder recorded the required JSON in the run notes and README, but could not create the index via MCP in this environment. Without a copy-paste-able createIndexes JSON and an idempotent script the user must hand-construct index creation steps in the portal.
- **Suggested fix (discoverability):** Add an example file 'examples/create_vector_index.json' with the exact createIndexes payload for DiskANN/HNSW/IVF, a small Python script that calls the MCP helper if enabled, and a README section 'How to create the vector index (pasteable JSON)'.

## [high] Context-engineering heuristics for DocumentDB RAG

- **What was missing:** No documented, service-specific guidance on assembling passages within the LLM token budget (rank by score, distinct timestamps, token-counting examples).
- **Where the agent looked:** General RAG literature and DocumentDB skills; searches for 'context engineering' and 'DocumentDB RAG context window' returned no service-specific guidance.
- **Effect on this build:** Builder did not implement token-budget-aware selection (requirement missed) and instead concatenated top-k passages, risking out-of-context or truncated prompts when used with real LLMs.
- **Suggested fix (learn_doc):** A page 'Context assembly for RAG on DocumentDB' with a recommended algorithm (token estimator, answer buffer, score-based greedy selection with timestamp diversity), code snippet (Python) and an example with tiktoken to compute tokens.

## [high] Idempotent seed-ingest pattern

- **What was missing:** A canonical, idempotent ingestion pattern (bulk upserts or bulk ReplaceOne with upsert=True) and sample code for doing bulk upserts efficiently against DocumentDB.
- **Where the agent looked:** Quickstart insert docs and agent-kit skills; no small canonical example for idempotent chunked ingestion was found.
- **Effect on this build:** Builder implemented deterministic chunk_id and a unique index (good), but insert_many produces DuplicateKeyErrors on rerun (caught but noisy).
- **Suggested fix (sample_or_quickstart):** A short 'Idempotent ingestion' sample illustrating creating deterministic chunk IDs and using pymongo.bulk_write with ReplaceOne(filter={'chunk_id':...}, replacement=doc, upsert=True) and showing how to batch and resume.

## [high] Index/management tool discoverability & opt-in flags

- **What was missing:** Clear guidance on when and how to enable the DocumentDB MCP management/write tools (ENABLE_MANAGEMENT_TOOLS / ENABLE_WRITE_TOOLS) that the agent helpers rely on.
- **Where the agent looked:** Events and MCP skill docs; the run environment reported management tools are disabled and the error message refers to environment flags but the README doesn't say how to opt in.
- **Effect on this build:** Builder attempted to create indexes and insert documents using MCP helpers and those calls failed in this environment; the lack of opt-in docs prevented the build from fully verifying index creation and server-side vector queries.
- **Suggested fix (agent_kit_rule):** An agent-kit rule and small README section: 'To allow automation to create indexes and insert test data, set ENABLE_MANAGEMENT_TOOLS=true and ENABLE_WRITE_TOOLS=true in your environment (only enable in trusted contexts). Example: export ENABLE_MANAGEMENT_TOOLS=true'.

## [high] Retry/backoff guidance for SDK & embedding calls

- **What was missing:** An explicit, service-specific retry/backoff recipe for DocumentDB writes, index builds and embedding-provider calls (include 429 handling and idempotent writes).
- **Where the agent looked:** documentdb-connection skill and general docs; no ready-to-copy recipe for sample authors.
- **Effect on this build:** No retry/backoff is implemented in sample; transient failures will surface as unhandled exceptions or noisy messages.
- **Suggested fix (learn_doc):** Add a short page 'Retries and idempotency for DocumentDB' with example code (tenacity wrapper), recommended retry counts and backoff policy, and example of combining retries with upsert semantics.

## [high] Clarify product naming & CLI/Bicep snippets

- **What was missing:** Some older docs and snippets in the ecosystem confuse DocumentDB with Cosmos DB databaseAccounts. Builders need a single authoritative note indicating 'use Microsoft.DocumentDB/mongoClusters for vCore clusters' and 'use az documentdb mongocluster' CLI group.
- **Where the agent looked:** readiness findings and the 'service confusions' entries in the readiness report.
- **Effect on this build:** If builders copy generic Cosmos DB examples they will choose wrong IaC resource types and incorrect CLI groups. The sample avoids auto-provisioning, so the immediate build was not broken, but automation could fail.
- **Suggested fix (naming_or_disambiguation):** Add a one-paragraph 'Which resource to use' note to the README plus exact Bicep/az CLI example(s) showing Microsoft.DocumentDB/mongoClusters and az documentdb mongocluster commands.

## [medium] Context: LLM provider & local dev guidance (token budgets)

- **What was missing:** Repository doesn't document the LLM model choices, token budgets, or how to adapt the context-engineering logic to local vs hosted LLMs.
- **Where the agent looked:** repo README and skills.
- **Effect on this build:** Builder left LLM selection to a model_default decision and did not implement token-aware assembly.
- **Suggested fix (discoverability):** Add a short 'LLM choices and token budgets' README subsection describing OpenAI/davinci vs local LlamaIndex, expected context sizes, and example token budgets/answer buffer sizes.

## [medium] PDF ingestion example

- **What was missing:** A tiny, permissively licensed PDF transcript example and an in-repo PDF->text example (pdfminer.six) so builders can demonstrate PDF ingestion in a minimal, legal way.
- **Where the agent looked:** repo samples and public quickstarts.
- **Effect on this build:** Builder included a plaintext sample only and documented that PDF support is not implemented; users must supply PDFs and implement parsing themselves.
- **Suggested fix (sample_or_quickstart):** Provide an example script 'tools/pdf_to_text.py' that demonstrates extracting timestamped lines from a sample PDF using pdfminer.six (with instructions about licensing).

## [medium] Unit tests & offline mocks for DocumentDB RAG samples

- **What was missing:** A recommended test scaffold (pytest) and examples that mock MongoDB and embedding models so tests run without a live cluster.
- **Where the agent looked:** repo and skill docs.
- **Effect on this build:** No tests exist; this makes CI for the sample harder and forces manual verification against a live cluster.
- **Suggested fix (sample_or_quickstart):** Add a tests/ directory with pytest tests that use mongomock for collection behavior and a stubbed embedding provider that returns deterministic vectors. Show how to run tests (pytest) without cloud access.

