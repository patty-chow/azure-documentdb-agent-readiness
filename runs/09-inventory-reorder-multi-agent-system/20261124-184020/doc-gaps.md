# Documentation and tooling gaps: 09-inventory-reorder-multi-agent-system

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] .env.example contents discoverability

- **What was missing:** The checklist expects a .env.example listing every runtime setting; no installed skill or public doc provides a template for sample repos.
- **Where the agent looked:** discovered skills, repo templates, Microsoft Learn quickstarts
- **Effect on this build:** The builder planned to read env vars (D004) but did not author .env.example; future builders may omit required variables or use inconsistent names (OPENAI_API_KEY vs AZURE_OPENAI_KEY).
- **Suggested fix (discoverability):** Add a short agent-kit rule and a sample .env.example template to the sample scaffolding docs showing canonical env names (DOCUMENTDB_URI, MODEL_PROVIDER, MODEL_KEY, EMBEDDING_MODEL) and notes on secrets handling.

## [high] Offline unit-test patterns for DocumentDB samples

- **What was missing:** No public guidance in the discovered skills that demonstrates a standard approach to write unit tests for DocumentDB-backed samples that run without a live cluster (e.g., mongomock usage patterns, connection patching).
- **Where the agent looked:** documentdb skills, Microsoft Learn, sample templates
- **Effect on this build:** The reference requires tests run without a live cluster; the builder left tests unimplemented. Lack of a standard pattern increases the chance samples omit tests or write flaky integration tests.
- **Suggested fix (sample_or_quickstart):** A quickstart 'Testing DocumentDB samples offline' showing pytest + mongomock examples, patching MongoClient, and CI snippet to run tests without cloud access.

## [high] Explicit guidance for mapping vector index dims to embedding models

- **What was missing:** While vector index creation examples exist, a short explicit sample page tying popular embedding models (OpenAI/others) to index 'dimensions' recommended values for sample authors was not found.
- **Where the agent looked:** documentdb-vector-search skill and Microsoft Learn vector-search pages
- **Effect on this build:** Without explicit mapping, builders may create indexes with wrong dimensions causing silent wrong search results.
- **Suggested fix (learn_doc):** Add a 'Embeddings and index dimensions' page listing recommended embedding models and corresponding dimensions (e.g., text-embedding-3-small -> 1536), plus a seed script snippet that asserts dimension matches before inserting documents.

## [high] readConcern / writeConcern mapping (prior_knowledge_only)

- **What was missing:** Public docs did not explicitly map MongoDB readConcern/writeConcern semantic guidance to the Azure DocumentDB vCore product; this was left as prior knowledge only (P14).
- **Where the agent looked:** Microsoft Learn queries for readConcern/writeConcern and service compatibility pages (search query included in discovery results).
- **Effect on this build:** An implementer might apply MongoDB majority-read/write semantics without verifying the service mapping, potentially creating incorrect assumptions about durability ordering in orchestrator flows.
- **Suggested fix (discoverability):** A short page in the 'compatibility' docs explicitly stating which readConcern/writeConcern modes are supported, their mapping to Azure DocumentDB durability/replica semantics, and sample pymongo options.

## [high] Discoverability: product-name and CLI mapping

- **What was missing:** The readiness findings show confusion between Cosmos DB (databaseAccounts/az cosmosdb) and the vCore DocumentDB (mongoClusters/az documentdb).
- **Where the agent looked:** learn.microsoft.com CLI and resource docs (readiness findings).
- **Effect on this build:** Builders could run wrong CLI commands or template types and fail to provision or target the wrong service.
- **Suggested fix (naming_or_disambiguation):** Add a 'Which product is this?' banner in quickstarts stating: 'Azure DocumentDB (vCore) -> Microsoft.DocumentDB/mongoClusters; do not use az cosmosdb or databaseAccounts for vCore clusters' with a short mapping table.

## [medium] Driver-version pinning guidance

- **What was missing:** No public guidance surfaced in the discovered practices that explicitly instructs sample authors to pin driver package versions (exact pinned constraints) for Azure DocumentDB sample repositories.
- **Where the agent looked:** documentdb skills, Microsoft Learn, general packaging docs
- **Effect on this build:** Builder chose a pinned pymongo range by assumption (D003). Without a documented recommended package matrix, different builders may pick incompatible pins (too new/too old).
- **Suggested fix (learn_doc):** A short 'Supported client versions' page listing recommended driver package versions for Python, Node, Java with example requirements.txt entries and rationale (e.g., pymongo>=4.3,<5.0), plus guidance for when to change pins.

## [medium] Infrastructure examples for Microsoft.DocumentDB/mongoClusters

- **What was missing:** The checklist expects infra-as-code examples for the vCore cluster type (mongoClusters); while some learn results exist, a concise sample template in the agent kit scaffolding for sample authors was not present.
- **Where the agent looked:** learn.microsoft.com search and documentdb-azure-deployment skill resources
- **Effect on this build:** Builder decided not to provision (run policy), and no infra artifacts were produced. Future builders may accidentally create the wrong resource type (databaseAccounts) if examples aren't explicit.
- **Suggested fix (sample_or_quickstart):** Add a minimal Bicep and Terraform (AzAPI) example that creates Microsoft.DocumentDB/mongoClusters with low-cost defaults and parameterized tier/region, plus an example cleanup command.

