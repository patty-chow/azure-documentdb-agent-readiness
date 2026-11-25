# Documentation and tooling gaps: 13-product-q-a-chatbot-rag

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Embedding model selection & index dimensions

- **What was missing:** No authoritative guidance recommending a default embedding provider/model and the embedding dimensionality to use in samples (e.g., when to pick OpenAI text-embedding-3-small (1536) vs another model).
- **Where the agent looked:** Microsoft Learn docs and installed DocumentDB skills (documentdb-vector-search, documentdb-indexing).
- **Effect on this build:** The builder picked OpenAI text-embedding-3-small (1536) as a reasonable default (decision D007). Without an explicit recommended default, different builders may pick incompatible dims or forget to document the required index dimensions, causing mismatch or silent failures.
- **Suggested fix (learn_doc):** A short 'Embedding & index dimensions' page that: (1) lists recommended embedding models and their output dimensions for sample usage (e.g., OpenAI text-embedding-3-small → 1536), (2) shows the exact createIndexes JSON with cosmosSearchOptions.dimensions set to the EMBEDDING_DIMS value, and (3) includes a checklist: set EMBEDDING_MODEL / EMBEDDING_DIMS in .env and ensure index dimensions match before seeding embeddings.

## [high] Index creation examples (pymongo runCommand)

- **What was missing:** A copy-pasteable Python (pymongo) example that calls createIndexes/runCommand with cosmosSearchOptions for vector-hnsw / vector-diskann and the exact JSON used to create such an index.
- **Where the agent looked:** Azure docs (vector-search pages) and MCP skill resources; examples exist in prose but no minimal pymongo code snippet was obvious to an agent.
- **Effect on this build:** The builder attempted to create an index via the MCP helper but the helper failed; a small pymongo example in the docs would have allowed an alternate automated creation path or a clearer manual step.
- **Suggested fix (sample_or_quickstart):** Publish a 'create vector index with pymongo' quickstart: a short Python script that connects using pymongo, runs db.command({'createIndexes': '<coll>', 'indexes': [{ 'name': 'embedding_vec', 'key': {'embedding': 'cosmosSearch'}, 'cosmosSearchOptions': {...}}]}) and then runs explain() on a small kNN aggregation. Include the minimal permission/role required.

## [high] Guidance for management-tool opt-in and MCP index creation failures

- **What was missing:** Clear public instruction that the MCP management tools are opt-in (ENABLE_MANAGEMENT_TOOLS) and what operators must set to allow automated create-index operations from agent tooling.
- **Where the agent looked:** MCP toolkit docs and skill resources; events showed an opt-in error but documentation linkage for this opt-in is sparse in an agent-discoverable location.
- **Effect on this build:** Automated index creation failed with 'Management tools are disabled by default.' This prevented the sample from fully exercising the vector-search path during verification.
- **Suggested fix (discoverability):** Add a short 'Management tool opt-in' note on the MCP Toolkit docs and the create-index quickstarts: explain ENABLE_MANAGEMENT_TOOLS usage, security implications, and an example CLI command to enable it for a given session or profile.

## [medium] Fallback search guidance when vector index missing

- **What was missing:** Explicit guidance that samples should implement a clear server-side text-search fallback via createSearchIndexes/$search (or show recommended local fallback behavior) and include example code for both.
- **Where the agent looked:** Azure vector-search and full-text docs; the docs describe createSearchIndexes but do not give a combined code snippet showing fallback strategies.
- **Effect on this build:** The sample implements a client-side substring-scoring fallback. That works for tiny demos but is inefficient and could encourage bad patterns when builders assume the server handles text search.
- **Suggested fix (learn_doc):** A 'RAG sample fallback' section that shows: (a) server-side text index createSearchIndexes example, (b) how to detect index presence and use $search textSearch as fallback, and (c) how to degrade to a safe client-side fallback with a clear note about performance/cost.

## [medium] Bulk ingestion and batch-size recommendations

- **What was missing:** Documentation stating recommended batch sizes, use of AllowBulkExecution/bulk APIs, and safe concurrency limits for seed scripts when ingesting vectors into DocumentDB.
- **Where the agent looked:** Microsoft Docs and vector-search tips pages; agent searches returned general advice but not concrete small-sample defaults.
- **Effect on this build:** seed.py uses per-document upserts which is fine for tiny data sets but may mislead builders creating larger datasets into non-performant ingestion patterns.
- **Suggested fix (learn_doc):** Add a small 'Seeding large datasets' page: recommended insert_many batch sizes (e.g., 500–2000 depending on cluster tier), sample code for pymongo bulk API with ordered=False, and notes on AllowBulkExecution toggles if applicable.

## [medium] Embedding dtype & normalization guidance

- **What was missing:** Public guidance that states whether embeddings should be stored as float32, float16, or another dtype in DocumentDB, and whether they should be L2-normalized for cosine similarity queries.
- **Where the agent looked:** Microsoft docs and installed skills (documentdb-vector-search) — skill mentions normalization in resources but public docs do not give a quick, agent-discoverable statement about dtype choices.
- **Effect on this build:** The sample stores embeddings as lists of floats and computes cosine in client; missing dtype guidance may cause mismatches for some drivers or indexes (and affects storage/perf choices).
- **Suggested fix (discoverability):** A short note in the vector-search docs: recommend storing vectors as dense number[] in the DB (float32 preferred), and recommend L2-normalizing vectors when using COS metric with an example normalization snippet.

## [medium] Embedding model & LLM provider example for samples

- **What was missing:** A short canonical paragraph in the 'build-rag-applications' doc that lists example embedding and LLM provider choices (OpenAI, Azure OpenAI, local Llama), with sample .env entries and expected dims.
- **Where the agent looked:** RAG guidance and DocumentDB samples; this guidance was found in disparate places but not consolidated for sample authors.
- **Effect on this build:** Builder made reasonable defaults (OpenAI embeddings + gpt-4o-mini) but had to choose versions and dims without a canonical suggested default; this led to inconsistent dependency choices and removal of LlamaIndex due to environment mismatch.
- **Suggested fix (learn_doc):** A brief 'Choose your embedding & LLM' section in the RAG quickstart showing three recommended example stacks (A: OpenAI embeddings + OpenAI Chat, B: Azure OpenAI embeddings + Azure OpenAI Chat, C: local Llama + local embedding model), and .env templates for each.

## [medium] Token-budgeting example for RAG prompt engineering

- **What was missing:** A compact example function showing how to estimate tokens (heuristic or using tiktoken) and progressively truncate lower-ranked chunks to fit a model's token budget.
- **Where the agent looked:** RAG prompt-engineering docs on Microsoft Learn; they discuss theory but have no code snippet the agent could easily reuse for a Python sample.
- **Effect on this build:** The sample omitted token-trimming logic; a ready-to-copy example would make adding this check trivial.
- **Suggested fix (sample_or_quickstart):** Provide a 20–40 line Python helper that uses a simple char→token heuristic and demonstrates dropping/truncating chunks until under budget; include a comment recommending replacement with tiktoken when available.

