# Documentation and tooling gaps: 13-product-q-a-chatbot-rag

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Optimistic concurrency / etag guidance for DocumentDB

- **What was missing:** No DocumentDB-specific documentation was found describing etag/_etag or an official optimistic concurrency pattern for upserts in the vCore-managed DocumentDB offering (searches returned Cosmos DB pages but not DocumentDB-specific ones).
- **Where the agent looked:** learn.microsoft.com search for 'etag', 'optimistic concurrency' and 'DocumentDB' (events.jsonl shows searches around these terms), agent-kit resources.
- **Effect on this build:** Unclear guidance increases the risk of creating non-idempotent seed scripts or unsafe update patterns; the builder cannot confidently pick a safe concurrency approach without potentially using the wrong semantics.
- **Suggested fix (learn_doc):** A short page describing optimistic concurrency options for Azure DocumentDB, whether an _etag-like mechanism is exposed to the MongoDB API, and patterns for idempotent upserts including example pymongo code.

## [high] Embedding model + index-dimension guidance (discoverability)

- **What was missing:** The sample must choose an embedding model and then create the index with matching dimensions. While the docs explain how to create indexes they do not present a short 'choose an embedding model and set EMBEDDING_DIM' cookbook for sample authors.
- **Where the agent looked:** learn.microsoft.com vector-search pages and agent-kit vector-search skill resources (events.jsonl).
- **Effect on this build:** The builder picked text-embedding-3-small and EMBEDDING_DIM=1536 by model default; without a clear example in docs, other authors may mismatch model dims and index dimensions and cause index creation/query failures.
- **Suggested fix (discoverability):** Add a short 'Embedding model to index dimension' note to the vector-search quickstart: list common embedding models and dims (e.g., text-embedding-3-small=1536, text-embedding-3-large=3072), and show the exact JSON snippet for createSearchIndexes using dimensions=${EMBEDDING_DIM}.

## [high] Citation/grounding format for RAG responses

- **What was missing:** The starter prompt requested 'grounded answers' but did not specify a citation format (inline bracketed id, list of sources array, show product_id/chunk_id, etc.). No authoritative sample guidance states the preferred citation format for DocumentDB-backed RAG samples.
- **Where the agent looked:** agent-kit skills, vector-search docs, sample gallery guidance; events.jsonl searches for 'citation format' and 'grounding' returned no definitive template.
- **Effect on this build:** Without a specified citation format the builder may omit explicit identifiers or produce inconsistent grounding; test harnesses expecting product_id/chunk_id in the LLM output cannot assert structure.
- **Suggested fix (agent_kit_rule):** Add an agent-kit rule for gallery RAG samples: require answers to include a 'sources' list with objects {product_id, chunk_id, source_type, score} and an inline bracketing style like '[source: product_id:chunk_id]' where the LLM can insert at each supporting sentence.

## [high] Unit tests that run offline (how-to)

- **What was missing:** No public sample pattern documenting how to author unit tests for DocumentDB-backed vector stores that run without a live cluster (mocking pymongo, embedding provider, and the LlamaIndex vector store).
- **Where the agent looked:** learn.microsoft.com, agent-kit skills, quickstarts; searches for 'unit tests mock pymongo' returned examples for other services but not a concise pattern for DocumentDB + vector stores.
- **Effect on this build:** The reference expects offline tests but the builder had no guidance on mocking DocumentDB vector features and searchScore projection; this raises barrier for test authors and may cause them to skip tests or write brittle integration tests.
- **Suggested fix (sample_or_quickstart):** A short 'Testing' appendix showing pytest examples that mock pymongo.collection.Collection.find/aggregate, stub embedding calls, and assert LlamaIndex uses precomputed vectors; include a template 'tests/test_seed.py' and 'tests/test_api.py' using pytest-mock.

## [high] Naming clarification: Azure DocumentDB vs Cosmos DB

- **What was missing:** The product naming has historically caused confusion. The team should publish a short, prominent naming note clarifying 'Azure DocumentDB (vCore-managed mongoClusters) vs Azure Cosmos DB (databaseAccounts, RU-based) vs Amazon DocumentDB'.
- **Where the agent looked:** readiness findings and cold-answers revealed multiple confusions (readiness_findings S02..S05), and developer-run searches in events.jsonl returned both mongoClusters and databaseAccounts pages.
- **Effect on this build:** Naming confusion can cause authors to pick the wrong CLI commands, resource types or example connection strings (e.g., using mongodb://:10255 instead of mongodb+srv).
- **Suggested fix (naming_or_disambiguation):** A short 'Which product is this?' note at the top of DocumentDB quickstarts and the sample README: show correct resource type (Microsoft.DocumentDB/mongoClusters), example CLI group (az documentdb mongocluster), SRV connection-string examples and portal steps.

## [medium] Bulk upload ordered:false guidance (prior knowledge gap)

- **What was missing:** No authoritative Azure DocumentDB-specific guidance was found for using unordered/bulkWrite (ordered:false) inserts when ingesting many documents; searches returned Cosmos DB for MongoDB guidance or generic MongoDB guidance but not DocumentDB-specific docs.
- **Where the agent looked:** learn.microsoft.com (DocumentDB vector search, quickstarts), agent kit skills, events.jsonl searches for 'ordered: false' and related terms.
- **Effect on this build:** The builder could not rely on a DocumentDB-specific recommendation for using unordered bulk writes; this affects seed script design decisions (batch sizes and error semantics) and may lead the author to pick a pattern based on non-DocumentDB sources.
- **Suggested fix (learn_doc):** A short 'Bulk ingestion' guidance page under Azure DocumentDB ingestion docs describing batch size recommendations, whether insertMany/BulkWrite supports ordered:false and best-practice error semantics for large-scale ingestion; include example code for Python/pymongo with recommended batch sizes for M10/M20/M30 tiers.

## [medium] Prior-knowledge-only practices (bulk inserts, optimistic concurrency)

- **What was missing:** Two discovered items (bulk insert ordered:false and optimistic concurrency / _etag) had no DocumentDB-specific public docs and were marked prior_knowledge_only by the discovery agent.
- **Where the agent looked:** learn.microsoft.com searches (events.jsonl) and agent-kit docs.
- **Effect on this build:** Agents may apply MongoDB or Cosmos DB patterns that do not precisely apply to Azure DocumentDB and cause incorrect ingestion or update logic.
- **Suggested fix (learn_doc):** Add short clarifications in the ingestion and data-modeling docs that state whether unordered bulkWrite is supported and how optimistic concurrency should be implemented (or a note that drivers' Mongo semantics apply), with code examples for pymongo.

