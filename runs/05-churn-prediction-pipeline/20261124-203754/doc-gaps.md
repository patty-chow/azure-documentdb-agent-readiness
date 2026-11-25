# Documentation and tooling gaps: 05-churn-prediction-pipeline

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Embedding model and dims

- **What was missing:** A documented default embedding model and its dimensionality for the sample (authoritative statement in README or a skill resource).
- **Where the agent looked:** README, .env.example, skills loaded in events.jsonl and the Microsoft Learn docs; readiness_findings flagged this gap.
- **Effect on this build:** The builder picked a model by convention (text-embedding-3-small / 1536 dims) but there is no public authoritative instruction for an agent to choose model/dims. This led to a model_default decision (D007) and risk of index/dimension mismatch or inconsistent implementations.
- **Suggested fix (learn_doc):** A short README section: 'Embedding model selection' that states the sample's default embedding provider/model (e.g., OpenAI text-embedding-3-small, 1536 dims), why it was chosen, and how to change EMBEDDING_MODEL and --dimensions to another provider/model. Include a one-line example and validation checks to guard dimension mismatches.

## [high] Vector-index creation example (exact createIndexes form)

- **What was missing:** A concrete createIndexes runCommand example with cosmosSearchOptions and example algorithm-specific params suitable for small samples.
- **Where the agent looked:** create_vector_index.py, README, Microsoft Learn 'Vector search' docs; readiness_findings S05 highlighted that many models show incorrect createIndex forms.
- **Effect on this build:** The builder used the correct runCommand form, but a future agent or contributor might attempt an incorrect db.createIndex(...) call with 'engine' options (MongoDB-Atlas style) and fail. The sample's create_vector_index.py excludes algorithm-specific parameters and guidance.
- **Suggested fix (sample_or_quickstart):** Add a 'create index' example in README showing the exact db.command({createIndexes:...}) JSON to run via pymongo or mongosh, with two example parameter sets: small-dev HNSW defaults and a production DiskANN example with notes about memory/CPU impact.

## [high] Tests and mock strategy

- **What was missing:** A test harness or example tests that run without a live cluster (mocks or local gateway) were not present.
- **Where the agent looked:** Repository files and README.
- **Effect on this build:** No automated tests shipped; maintainers and CI cannot validate sample behavior without a live DocumentDB cluster.
- **Suggested fix (agent_kit_rule):** Provide a tests/ folder with unit tests that mock pymongo collections (using unittest.mock or mongomock) and an example of running the sample against the local DocumentDB gateway Docker image for integration tests.

## [high] Return similarity score in search results

- **What was missing:** The sample does not include the $search score in the projection or printed output.
- **Where the agent looked:** app/run_agent.py
- **Effect on this build:** Users cannot see similarity scores, which are useful to interpret neighbor relevance and build decision thresholds.
- **Suggested fix (sample_or_quickstart):** Update run_agent.py to include {'score': {'$meta': 'searchScore'}} in projection and print the score along with returned neighbors; include an example output in README.

## [medium] .env discoverability

- **What was missing:** While .env.example exists, a single line in the README explaining which env vars are mandatory for which features (RFM only vs embedding/LLM) and examples for Azure OpenAI vs OpenAI providers is missing.
- **Where the agent looked:** README and .env.example
- **Effect on this build:** Users may set DOCUMENTDB_URI but not OPENAI_API_KEY and be surprised that embeddings/LLM steps are skipped; an agent may also choose the wrong env var names for Azure vs OpenAI providers.
- **Suggested fix (discoverability):** Add a short table in README listing env vars (DOCUMENTDB_URI required; OPENAI_API_KEY optional; OPENAI_EMBEDDING_MODEL default value; (optional) AZURE_OPENAI_* examples) and which sample steps need them.

## [medium] RetryWrites guidance for vector operations

- **What was missing:** Clear guidance whether to include retryWrites=false for data-plane connection strings when performing vector-index operations.
- **Where the agent looked:** README, .env.example, vector-search quickstarts.
- **Effect on this build:** No explicit setting in .env.example; the builder left retryWrites unspecified, and some DocumentDB guidance recommends retryWrites=false for vector operations (discovered_practices P05).
- **Suggested fix (discoverability):** Add a short note in README on connection-string parameters recommending retryWrites=false for vector index writes where appropriate and reference the vector quickstart docs.

## [medium] Pinned dependency versions

- **What was missing:** requirements.txt uses >= constraints rather than pinned exact versions.
- **Where the agent looked:** app/requirements.txt
- **Effect on this build:** Reproducibility is reduced; the exact environment used during verification is not captured, making future builds brittle.
- **Suggested fix (discoverability):** Provide a pinned requirements.txt (==) or add a requirements-lock.txt produced from pip freeze used during verification, and a short note on how to update them safely.

## [medium] Infrastructure IaC example

- **What was missing:** An example Bicep/Terraform snippet using Microsoft.DocumentDB/mongoClusters for the cluster resource was not present.
- **Where the agent looked:** Repository and README; readiness findings indicated confusion between mongoClusters and databaseAccounts.
- **Effect on this build:** The sample is explicit about not provisioning, but readers who want to reproduce the exact environment lack an IaC starting point and may use the wrong resource type (databaseAccounts) if they follow older docs.
- **Suggested fix (learn_doc):** Add an optional 'infrastructure' folder with a minimal Bicep or Terraform AzAPI example that creates a Microsoft.DocumentDB/mongoClusters cluster with low-cost defaults, and a note distinguishing this resource from Cosmos DB databaseAccounts.

