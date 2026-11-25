# Documentation and tooling gaps: 17-esg-scoring-pipeline

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] CreateIndexes payload examples for cosmosSearch vector indexes

- **What was missing:** A concise, copy-paste 'createIndexes' JSON payload for each supported vector kind (vector-hnsw, vector-ivf, vector-diskann) with recommended demo parameters and a brief explanation of each numeric parameter.
- **Where the agent looked:** Microsoft Learn 'Integrated vector store in Azure DocumentDB' had an example but not a compact table of recommended demo parameters; searches in readiness logs show partial examples (events.jsonl).
- **Effect on this build:** The builder used an MCP tool to attempt index creation but the verification environment blocked it. Authors will often try to create the index programmatically; small differences in the JSON shape or missing example parameters cause uncertainty.
- **Suggested fix (discoverability):** Add a short 'Vector index JSON examples' appendix to the vector-search docs that includes (1) explicit createIndexes JSON for vector-hnsw with fields: key:{'<path>':'cosmosSearch'}, options:{name, cosmosSearchOptions:{kind:'vector-hnsw', dimensions:<dims>, similarity:'COS', m:<>, efConstruction:<>, lBuild:<>, maxDegree:<>}}; and parallel examples for vector-ivf and vector-diskann with recommended values for small/medium/large corpora.

## [high] Embedding model selection & dimension guidance for samples

- **What was missing:** No authoritative recommendation in the sample docs for which embedding model to default to (OpenAI text-embedding-3-small chosen by the builder) and no guidance that maps common embedding models to dims used in vector-index creation.
- **Where the agent looked:** Readiness scans and Microsoft Learn vector-search pages; no sample-level recommendation for an embedding model & dims was found.
- **Effect on this build:** The builder selected text-embedding-3-small (1536 dims) by assumption. If a different model/dims is later chosen by a user, the vector index dims could be mismatched causing runtime failures.
- **Suggested fix (learn_doc):** A short 'Embeddings & index dims' page describing recommended default embedding models (e.g., OpenAI text-embedding-3-small → 1536 dims) and instructions to set EMBEDDING_DIMS to the model's output size, plus sample code to verify vector length before creating an index.

## [high] Missing /search example using $search/cosmosSearch

- **What was missing:** A small, copy-paste example of a $search aggregation pipeline that performs a cosmosSearch vector query over an embedding field and returns similarity scores.
- **Where the agent looked:** Vector search documentation has general examples but the sample author lacked a minimal example ready to paste into sample/search.py.
- **Effect on this build:** Because the builder did not include a server-side search snippet, the sample lacks a documented semantic-search usage example tied to the stored vectors. Verification could not confirm server-side similarity queries because index creation failed.
- **Suggested fix (sample_or_quickstart):** A minimal 'search' code snippet showing the aggregation pipeline with $search:{cosmosSearch:{kind:'vector-hnsw', vector:{path:'rationale_embedding', queryVector: <vector>, k:10, similarity:'COS'}}}, and showing how to read the similarity score from results.

## [medium] Bulk write guidance for DocumentDB (PyMongo)

- **What was missing:** No Microsoft Learn page was found that explicitly recommends PyMongo bulk_write usage patterns or how to inspect upserted_ids for idempotency with DocumentDB; the earlier search produced no useful result.
- **Where the agent looked:** Azure docs search for 'Azure DocumentDB bulk_write pymongo bulk_write', 'Azure DocumentDB bulk writes best practices' (05a-practice-discovery search logs).
- **Effect on this build:** The builder used bulk_write (process.py) from prior knowledge; lack of public guidance meant the agent marked this practice as prior_knowledge_only and could not provide robust error-handling guidance. The sample uses bulk_write but does not handle BulkWriteError explicitly.
- **Suggested fix (learn_doc):** A short Learn page titled 'Bulk writes and idempotent seeding with PyMongo on Azure DocumentDB' outlining: when to use bulk_write, example PyMongo code (ordered=False), how to handle BulkWriteError and inspect result.upserted_ids for idempotency, and recommended write concerns for cluster tiers.

## [medium] Publishing MONGODB-OIDC / Microsoft Entra ID example for clients

- **What was missing:** An example showing how an application should connect using Microsoft Entra ID (MONGODB-OIDC) via a driver or code snippet and how to set authMechanismProperties.
- **Where the agent looked:** Microsoft Learn auth docs and readiness search for 'MONGODB-OIDC' examples; some docs exist but a short sample for Python + PyMongo is not prominent.
- **Effect on this build:** The sample uses a connection string via DOCUMENTDB_URI (likely master user). Without a short Entra ID example, authors may avoid the recommended least-privilege approach.
- **Suggested fix (discoverability):** An 'Authenticate with Microsoft Entra ID' quickstart showing a PyMongo connection string example using MONGODB-OIDC and an outline of steps to obtain tokens/permissions.

## [medium] Prior-knowledge-only practice: bulk_write recommendation

- **What was missing:** Public guidance specific to Azure DocumentDB for bulk writes was not found. Agents may assume a MongoDB-style bulk_write but cannot find a DocumentDB-specific confirmation.
- **Where the agent looked:** Azure docs and quickstarts; searches for 'bulk_write' returned no DocumentDB-specific best-practice page.
- **Effect on this build:** The agent treated bulk_write as prior knowledge and used it, but couldn't provide DocumentDB-specific recommendations (timeouts/retry wrappers) from official docs.
- **Suggested fix (learn_doc):** Short doc 'Bulk writes on Azure DocumentDB' confirming compatibility with PyMongo's bulk_write, illustrating idempotent patterns and how to inspect results for upserted_ids and handle BulkWriteError.

## [medium] README clean-up steps

- **What was missing:** Explicit commands to delete sample documents and remove the vector index (or how to teardown the sample's artifacts) were not present.
- **Where the agent looked:** README and quickstart in the repo, events and seed/verify logs.
- **Effect on this build:** Users may leave sample data and indexes in a live cluster; authors should be able to clean up easily.
- **Suggested fix (learn_doc):** Add a 'Clean up' section with pymongo commands to drop the sample collection, and if management tools are enabled, the exact createIndexes/deleteIndexes JSON or MCP commands to remove the vector index.

