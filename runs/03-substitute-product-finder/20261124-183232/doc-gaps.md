# Documentation and tooling gaps: 03-substitute-product-finder

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Explicit DocumentDB cosmosSearch examples for Python FastAPI samples

- **What was missing:** A concise, copy-paste-ready example that shows the exact $search aggregation pipeline using the 'cosmosSearch' operator for vector search (including similarity:'COS', path, k and how to project $meta 'searchScore').
- **Where the agent looked:** Microsoft Learn vector-search docs and quickstarts were examined (events show vector-search skill and learn_microsoft_docs_search results), but the builder implemented a knnBeta-style payload from prior knowledge rather than the DocumentDB cosmosSearch JSON.
- **Effect on this build:** Builder implemented a $search pipeline using 'knnBeta' which is not the DocumentDB 'cosmosSearch' shape; this likely prevents server-side vector search on DocumentDB and forced reliance on inefficient client-side fallback.
- **Suggested fix (discoverability):** Add a short 'Vector search example for Python' snippet to the docs/quickstart that includes a working $search{'cosmosSearch': {...}} aggregation example, showing similarity:'COS', vector path, k and $project of $meta: 'searchScore'. Include a small Python helper function that returns the pipeline object.

## [high] Index creation helper that is safe and idempotent

- **What was missing:** A small helper script / library snippet that safely creates or verifies a DocumentDB vector index and returns a friendly error if management tools are required or disabled. The builder's ensure_index is best-effort but the environment-specific MCP flags blocked verification.
- **Where the agent looked:** Search of DocumentDB vector-search quickstarts and MCP skill resources.
- **Effect on this build:** Index creation attempts could not be verified in this run (management tools disabled); users may run the sample and find the index missing or misconfigured.
- **Suggested fix (mcp_tool_or_description):** Provide a helper script 'create_vector_index.py' that (1) reads EMBEDDING_DIMS from config, (2) checks existing indexes and whether a vector index with matching dimensions exists, (3) creates the index via createIndexes if allowed, and (4) prints a clear instruction for how to create it via the portal or MCP if management tools are disabled.

## [high] Idempotent ingestion guidance for samples

- **What was missing:** Example code or guidance showing an idempotent ingestion pattern (upsert by product_id or dedupe by deterministic id), and a worked example batch size for 10k inserts that is safe for typical dev tiers.
- **Where the agent looked:** DocumentDB ingestion and vector performance docs mention bulk but do not include a simple idempotent sample for product catalogs in gallery samples.
- **Effect on this build:** The ingest script is not idempotent and the README/warnings note this; users re-running ingest may get duplicates unexpectedly.
- **Suggested fix (sample_or_quickstart):** Add an 'idempotent ingestion' recipe that uses bulk upserts (replaceOne with upsert:true) in batches and documents trade-offs and a --force flag to clear and re-seed if desired.

## [medium] Embedding model & dimension guidance for samples

- **What was missing:** A short authoritative sentence in the sample docs saying which embedding model the sample was built for (e.g., 'text-embedding-3-small, 1536 dims') and why, with instructions how to change embedding dims consistently (model config, index creation constant).
- **Where the agent looked:** No single doc in the sample pointed to a canonical embedding model choice; the builder made an implementation choice. Public docs mention index dimensions but not a default embedding model for samples.
- **Effect on this build:** The builder selected 1536 dims and used it everywhere; without explicit doc a different builder might pick different dims and create a mismatched index.
- **Suggested fix (learn_doc):** Add a README subsection 'Embedding model and index dimensions' that states the chosen default model, its dimensionality, where to change EMBEDDING_DIMS in code, and how to recreate the index when switching models.

## [medium] Clear guidance about management/write MCP tool opt-ins

- **What was missing:** An explicit note in sample README that MCP management/write tools may be disabled by default in some agent environments and must be enabled via environment variables (ENABLE_MANAGEMENT_TOOLS / ENABLE_WRITE_TOOLS) before the repository's verification scripts can run.
- **Where the agent looked:** Events show documentdb_create_index and documentdb_insert_documents failed with explicit errors about opt-in flags.
- **Effect on this build:** Automated verification attempts failed in this environment; maintainers may be confused why MCP calls error with 'Management tools are disabled by default.'
- **Suggested fix (discoverability):** Add a short paragraph to README explaining MCP tool opt-in flags and how to run verification locally, including example commands to enable the tools and warnings about running write operations.

## [low] Public clarification on vector numeric formats

- **What was missing:** Because prior beliefs sometimes assume float32-only embeddings, highlight in public docs that DocumentDB supports half-precision / product quantization and when to prefer reduced precision.
- **Where the agent looked:** The vector-search docs already state DiskANN/PQ and reduced-precision support, but this is a gap for agents trained on float32-only priors.
- **Effect on this build:** No direct build impact, but agents may pick float32 unnecessarily; explicit note would prevent incorrect assumptions.
- **Suggested fix (naming_or_disambiguation):** Add a small note near the vector-search quickstart: 'DocumentDB supports half-precision and product quantization — for very large indexes prefer PQ/fp16; see DiskANN options.'

