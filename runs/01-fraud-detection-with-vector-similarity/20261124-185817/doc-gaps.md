# Documentation and tooling gaps: 01-fraud-detection-with-vector-similarity

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Binary embedding storage format

- **What was missing:** Clarification whether Azure DocumentDB supports a binary/compressed embedding storage format or requires number[] float arrays; guidance on recommended storage format and examples for Python.
- **Where the agent looked:** Azure DocumentDB vector-search docs (learn.microsoft.com), documentdb-vector-search skill resources, repository files.
- **Effect on this build:** Builder defaulted to storing float arrays (number[]) in documents (seed.py & embeddings.py). If a developer assumed a binary/compressed format was supported they might store incompatible data and fail to get indexed by cosmosSearch.
- **Suggested fix (learn_doc):** A short 'Embedding storage formats' doc on the vector-search docs page that states: (1) DocumentDB expects vectors as number[] for cosmosSearch indexing; (2) show Python example: vec.tolist() then createIndexes cosmosSearchOptions; (3) discuss compression tradeoffs (product quantization) and link to product-quantization doc; (4) show how to store model metadata and dims.

## [high] Seed script should create index idempotently

- **What was missing:** An example in the docs or a seed script that shows idempotent createIndexes for cosmosSearch vector indexes (so seed.py both creates the index and upserts docs).
- **Where the agent looked:** Repository seed.py, documentdb-vector-search skill and Microsoft Learn vector-index pages.
- **Effect on this build:** Index creation was attempted via MCP and failed in this run; because seed.py lacks index-creation code a user re-running seed.py wouldn't reliably build the index automatically.
- **Suggested fix (sample_or_quickstart):** A code snippet to include in seed.py that calls db.command({ 'createIndexes': '<collection>', 'indexes': [ { 'name': '...', 'key': {'vector': 'cosmosSearch'}, 'cosmosSearchOptions': { 'kind': 'vector-ivf', 'dimensions': <dims>, 'similarity':'COS', 'numLists': <n> } } ] }) and handles IndexExists gracefully. Document expected parameter choices for demo vs larger datasets.

## [high] Tests that run without a live cluster

- **What was missing:** An offline unit test scaffold that runs without a live DocumentDB cluster (e.g., using mongomock or mocking the MongoClient).
- **Where the agent looked:** Repository tests (none) and test guidance in skills.
- **Effect on this build:** No tests exist; CI or a local contributor cannot validate compute_risk/explain behavior without provisioning a cluster.
- **Suggested fix (sample_or_quickstart):** Add pytest tests: (1) unit tests for compute_risk and explain() using synthetic results; (2) integration-style tests using mongomock for seed upserts and vector_search pipeline shape (mock aggregate results), and a small test that asserts run_agent CLI handles empty input and embedding exceptions.

## [high] IaC example for DocumentDB

- **What was missing:** A minimal Bicep/Terraform template using Microsoft.DocumentDB/mongoClusters to provision an Azure DocumentDB cluster for the sample.
- **Where the agent looked:** Repository (no IaC) and Microsoft Learn (found examples but none included with sample).
- **Effect on this build:** Builder relied on an existing cluster and did not provide IaC; repository cannot be used as a full reproducible sample for users who want to provision a test cluster.
- **Suggested fix (mcp_tool_or_description):** Add 'iac/' with a Bicep file and a short Terraform/az API snippet that creates a low-cost cluster (e.g., small test tier) and documents how to retrieve connection strings (az documentdb mongocluster list-connection-strings) and set DOCUMENTDB_URI.

## [medium] .env.example completeness

- **What was missing:** A canonical .env.example listing every setting the sample needs (model name, model dims, index knobs, optional OpenAI key and toggles).
- **Where the agent looked:** Repository .env.example and README; installer skills and docs for embedding/index examples.
- **Effect on this build:** The builder included DOCUMENTDB_URI and OPENAI_API_KEY but omitted explicit placeholders for MODEL_NAME, EMBEDDING_DIMS and index parameters. This caused guesswork and local edits by the developer.
- **Suggested fix (agent_kit_rule):** An agent-kit rule and a sample .env.example template that includes: DOCUMENTDB_URI, MODEL_NAME, EMBEDDING_DIMS (or MODEL_DIMS), INDEX_KIND, INDEX_NUM_LISTS, USE_LOCAL_EMBEDDING (true/false), OPENAI_API_KEY, and an explanation line for each variable.

## [medium] Index tuning guidance in README

- **What was missing:** Concrete guidance and example parameter ranges in the README for how to change index kind and tuning parameters when moving from demo to production.
- **Where the agent looked:** README.md and documentdb-vector-search public docs.
- **Effect on this build:** The README mentions tuning at a high level but does not give explicit change instructions; a developer may pick unsafe defaults for larger datasets.
- **Suggested fix (sample_or_quickstart):** A README section with example createIndexes JSON for IVF/HNSW/DiskANN, recommended numLists/m/efConstruction/lBuild ranges for small/medium/large datasets, and commands to update or drop/recreate indexes.

## [medium] Agent-tool integration example

- **What was missing:** An explicit, minimal example that demonstrates wrapping the vector_search function as a LangChain Tool and invoking it from an Agent.
- **Where the agent looked:** Repository run_agent.py (no LangChain Tool), LangChain docs (not packaged in sample).
- **Effect on this build:** The sample is runnable as a CLI script but does not demonstrate LangChain integration requested by the starter prompt; consumers expecting a LangChain Agent example won't find it.
- **Suggested fix (sample_or_quickstart):** Add agent_wrapper.py showing from langchain.tools import Tool (or the current LangChain Tool pattern) that wraps vector_search, then construct an Agent (or simple LLMChain) that calls the Tool; include an integration example in README.

