# Documentation and tooling gaps: 09-inventory-reorder-multi-agent-system

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Embedding model & index-dimension mapping

- **What was missing:** A canonical sample-level recommendation mapping a chosen embedding model to vector index dimensionality and a sample index-creation snippet (cosmosSearch) was not present. The sample chose a model by convention (OpenAI 1536 dims) but seed.py does not create a vector index and README does not give exact index-creation commands.
- **Where the agent looked:** documentdb-vector-search skill, azure docs on vector search, sample repo files (.env.example, seed.py, README)
- **Effect on this build:** The sample deliberately did not create or test vector indexes. If a user enables vectors they would have to create a matching cosmosSearch index manually; an agent could pick the wrong index syntax (e.g., MongoDB knnVector) or wrong dimensionality, causing index creation or query failures.
- **Suggested fix (learn_doc):** A short page titled 'Vector search: model ↔ index mapping' that (1) lists recommended sample embedding models (e.g., OpenAI text-embedding-3-small: 1536 dims) and shows a concrete cosmosSearch vector index JSON snippet to create for that dimension and chosen algorithm (HNSW/IVF/DiskANN). Include a seed.py example flag (--create-vector-index) and a note: 'Dimensions must match the embedding model output'.

## [high] LangChain multi-agent memory pattern for DocumentDB

- **What was missing:** No public, discoverable example showing a canonical LangChain multi-agent shared memory pattern backed by DocumentDB (schema for agent_memory, dedupe keys, upsert patterns, and an example mapping to LangChain memory API).
- **Where the agent looked:** documentdb skills (documentdb-data-modeling, documentdb-driver, documentdb-local-deployment) and public Azure docs; no single LangChain+DocumentDB memory example was found.
- **Effect on this build:** The builder implemented a pragmatic agent_memory collection, but an agent or new builder could implement memory incorrectly (in-memory only, or without uniqueness keys), leading to duplicate orders in concurrent runs.
- **Suggested fix (agent_kit_rule):** Add an 'Agent memory' sample to the agent-kit showing a persisted memory collection schema, recommended unique dedupe key (e.g., (agent_name, item_id, event_hash)), example upsert patterns and a LangChain memory adapter snippet that persists/retrieves memory from DocumentDB.

## [high] DocumentDB vs Cosmos naming / deployment guidance

- **What was missing:** Clear, prominent guidance (discoverable from the agent-kit) that Azure DocumentDB clusters use Microsoft.DocumentDB/mongoClusters and the az CLI group 'az documentdb mongocluster' (not az cosmosdb), plus a short paragraph on billing model (vCore tiers M10/M20/M30 vs RU model).
- **Where the agent looked:** documentdb-azure-deployment skill, Azure docs and the agent-kit. Many short docs exist but discovery is error-prone and model-default answers often conflate Cosmos and DocumentDB.
- **Effect on this build:** A builder or automated agent might author IaC or CLI examples targeting Microsoft.DocumentDB/databaseAccounts or az cosmosdb, which would be incorrect for this product.
- **Suggested fix (naming_or_disambiguation):** Add a 'Deployment notes' page to the agent-kit and the sample README that (1) states Microsoft.DocumentDB/mongoClusters is the correct resource type, (2) shows a minimal az documentdb mongocluster create snippet and a minimal Bicep fragment, and (3) explains the vCore (M-tier) billing model vs RU-based Cosmos guidance.

## [high] cosmosSearch vector index creation examples

- **What was missing:** Concrete index-creation snippets for DocumentDB's cosmosSearch vector indexes (the product's supported API) so builders do not try MongoDB knnVector syntax.
- **Where the agent looked:** documentdb-vector-search skill and public vector docs; the conceptual guidance exists but sample commands/snippets are not easy to find.
- **Effect on this build:** If a builder follows generic MongoDB 7 examples (knnVector createIndex) the commands will be incompatible with DocumentDB and fail.
- **Suggested fix (discoverability):** Add example JSON for createSearchIndexes and a short note in documentdb-vector-search describing method choices (HNSW/IVF/DiskANN), with an example index payload for 1536-d vectors and a seed script flag to create it.

## [medium] Recommended client options & pinned driver versions for samples

- **What was missing:** A short, discoverable recommendation listing exact client-timeout and pool defaults used in official samples and recommended pinned versions for drivers (e.g., pymongo==4.x.y used in CI).
- **Where the agent looked:** documentdb-driver skill docs and Azure public docs; guidance exists for connection options but not a one-line 'official sample pins' reference.
- **Effect on this build:** The builder used permissive ranges in requirements.txt and omitted explicit timeouts/pool sizes; an agent following only training priors may not pin or may pick incompatible versions.
- **Suggested fix (discoverability):** Add a small 'Sample runtime config' fragment to documentdb-driver: recommended exact pip pins (the CI-tested versions) and a canonical MongoClient options snippet (retryWrites=false, serverSelectionTimeoutMS, socketTimeoutMS, maxPoolSize) to copy into samples.

## [medium] Seed schema and suggested demo sizes

- **What was missing:** Concrete, discoverable guidance on the sample document shapes (field names, types, required fields) and suggested seed counts for demo vs stress testing.
- **Where the agent looked:** documentdb-local-deployment and sample repos; no single sample schema for 'inventory reorder' pattern was found.
- **Effect on this build:** The builder made reasonable choices (30 SKUs, 14 days of sales) but an agent could pick inconsistent schemas or wrong field names and create mismatches between agents and indexes.
- **Suggested fix (sample_or_quickstart):** A short 'inventory-reorder' quickstart document describing exact sample documents for sales_velocity, lead_times and purchase_orders (field list and types), and a seed script template with flags for small/medium/large demo sizes.

## [medium] Explain() & index verification in CI

- **What was missing:** A recommended small CI/dev script or README step that runs explain('executionStats') on the sample's hot queries and captures the plan for developer review.
- **Where the agent looked:** documentdb-query-optimizer skill docs and CI examples; not present as a turnkey sample step.
- **Effect on this build:** The sample lacks a programmatic way to verify index usage; authors or automated agents won't detect regressions in index coverage without manual MCP/console checks.
- **Suggested fix (mcp_tool_or_description):** Add a dev/ci script (e.g., tools/verify_indexes.py) that calls explain('executionStats') for key queries and fails CI if a COLLSCAN is detected; document how to run it with the MCP server profile.

