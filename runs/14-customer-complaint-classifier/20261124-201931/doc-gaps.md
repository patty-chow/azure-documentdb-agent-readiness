# Documentation and tooling gaps: 14-customer-complaint-classifier

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Missing env vars in .env.example

- **What was missing:** The repo's .env.example does not list environment variables that the code reads (EMBEDDING_MODEL, EMBEDDING_DIMENSIONS/EMBEDDING_DIMS, LLM_MODEL, optional connection tuning variables).
- **Where the agent looked:** Inspected repository files (src/app/pipeline.py, src/app/db.py, scripts/create_indexes.py) and app/.env.example.
- **Effect on this build:** Caused a mismatch between expected runtime configuration and the example; a user copying .env.example may miss setting EMBEDDING_MODEL or LLM_MODEL and not realize the index dimensions should match the model.
- **Suggested fix (learn_doc):** Update .env.example to include: EMBEDDING_MODEL (placeholder), EMBEDDING_DIMENSIONS (1536), LLM_MODEL (gpt-4o-mini), optional DB client tuning vars (MAX_POOL_SIZE, MAX_IDLE_MS). Provide a short comment on each variable.

## [high] Index hyperparameter guidance & README scaling notes

- **What was missing:** README and create_indexes.py lack explicit guidance on choosing HNSW/DiskANN/IVF and tuning hyperparameters (m/efConstruction/lBuild/lSearch/maxDegree) for different corpus sizes.
- **Where the agent looked:** README and scripts/create_indexes.py in the repository; documentdb-vector-search skill resources were loaded by the builder but guidance wasn't surfaced in the repo.
- **Effect on this build:** Users can create an index that is syntactically correct but misconfigured for their dataset; silent mismatches can produce incorrect search behavior or poor performance.
- **Suggested fix (discoverability):** Add a README subsection 'Vector index sizing for production' with a table: small demo (<=10k) -> IVF settings example; medium (10k-50k) -> HNSW example with efConstruction/m; large (>50k/M30+) -> DiskANN with example maxDegree/lBuild and a note on PQ and fp16. Provide an example createSearchIndexes JSON with commented hyperparameters.

## [high] LangChain usage example

- **What was missing:** The prompt required building a LangChain agent; the repo uses direct OpenAI calls. There is no in-repo example of using LangChain PromptTemplate / LLMChain for classification.
- **Where the agent looked:** src/app/pipeline.py, src/pipeline.py, README.
- **Effect on this build:** The sample does not demonstrate the requested LangChain usage; reviewers expecting a LangChain-based agent will not find it.
- **Suggested fix (sample_or_quickstart):** Add a short code snippet showing how to convert the existing prompt into a LangChain PromptTemplate and LLMChain, and replace the classify_text_with_llm implementation with a LangChain-based call. Put a complete LangChain example in src/app/pipeline_langchain.py and update README to reference it.

## [high] Search endpoint input validation and error behavior

- **What was missing:** No explicit handling for empty queries or embedding failures in the app's /search endpoint.
- **Where the agent looked:** src/app/main.py search endpoint code and tests.
- **Effect on this build:** An empty q could produce an unhelpful result or a no-op; if embedding fails the endpoint may surface a vague error or return wrong results. Tests do not cover this runtime path.
- **Suggested fix (agent_kit_rule):** Add an app rule: all public search endpoints must return HTTP 400 for empty query strings and must catch embedding errors and return HTTP 500 with a short error message. Add a unit test that mocks embed_text raising an exception and asserts the endpoint returns a 500 with a clear message.

## [high] Explicit note differentiating vCore DocumentDB vs Cosmos DB databaseAccounts

- **What was missing:** The repo does not explicitly call out the resource type distinction or show the exact connection string SRV example for the vCore cluster.
- **Where the agent looked:** README and .env.example; found partial hostnames in earlier write attempts but current .env.example uses a cosmos.azure.com host pattern which could confuse.
- **Effect on this build:** Implementers may use wrong connection host/port or assume Cosmos DB databaseAccounts connection strings (port 10255) and fail to connect to the vCore mongoClusters endpoint (which uses different host patterns and local gateway port 10260).
- **Suggested fix (naming_or_disambiguation):** Add a short 'Connection string quick reference' to README and update .env.example to show the correct SRV example for mongoClusters and a local gateway example (port 10260) with a note 'Do not paste real credentials'.

## [medium] Infrastructure-as-code example for Microsoft.DocumentDB/mongoClusters

- **What was missing:** No Bicep/Terraform templates or az cli examples that create an Azure DocumentDB mongoCluster resource in the repository.
- **Where the agent looked:** Repo tree and README; documentdb-azure-deployment skill available but no template committed.
- **Effect on this build:** Users cannot reproduce a matching vCore cluster from the repo alone; they must rely on separate docs or ask infra to create the right resource type.
- **Suggested fix (mcp_tool_or_description):** Provide a minimal Bicep file and a Terraform example that create Microsoft.DocumentDB/mongoClusters (small tier default), with parameters for region, tier and a link to how to retrieve the connection string, and add a README section 'Provisioning test cluster'.

## [medium] Retry wrappers for DB/network operations

- **What was missing:** No retry-with-backoff helper or guidance in the repo for transient network errors when talking to the cluster or embedding/LLM APIs.
- **Where the agent looked:** src/app code and scripts; no retry helper present.
- **Effect on this build:** Transient network issues during seeding or enrichment can cause partial failures; the builder's MCP writes also failed in this run but for an unrelated tool opt-in reason.
- **Suggested fix (agent_kit_rule):** Add a small retry utility (async) that wraps DB writes and external API calls; document which operations are retried and which are not (idempotent vs non-idempotent).

