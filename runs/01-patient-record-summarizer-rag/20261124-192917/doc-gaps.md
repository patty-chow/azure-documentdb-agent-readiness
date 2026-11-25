# Documentation and tooling gaps: 01-patient-record-summarizer-rag

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] PHI logging guidance

- **What was missing:** No DocumentDB-specific public page explicitly states how to handle PHI in application logs (redaction/masking guidance) for DocumentDB-based sample apps.
- **Where the agent looked:** Searched Microsoft Learn and public docs for 'do not log PHI azure documentdb' and related terms; no authoritative page found.
- **Effect on this build:** The sample README includes a general 'Do not use for PHI' line but the sample does not include logging filters or examples of redaction. An agent cannot confirm whether a sample is safe for PHI without a document stating expectations.
- **Suggested fix (learn_doc):** Page titled 'Handling PHI in Azure DocumentDB samples' with: 1) short policy: never log PHI; 2) example logging configuration showing redaction middleware and redaction of patientId/embeddings/clinical text; 3) example code snippets for Python logging filters and how to enable structured logging without PHI; 4) placement in the 'Security' section of the DocumentDB docs.

## [high] Application-layer patient authorization

- **What was missing:** No DocumentDB-specific guidance explicitly states that application-layer checks are required to verify an authenticated user is authorized to read a given patientId before issuing DB queries.
- **Where the agent looked:** Searched docs for 'application-layer patientId authorization azure documentdb' and related phrases; found RBAC/auth docs but not a page addressing document-level patient authorization for clinical workloads.
- **Effect on this build:** The sample relies on patientId pre-filters but does not include authentication/authorization; an agent may assume DB filter alone suffices for access control.
- **Suggested fix (learn_doc):** Add a 'Protecting patient data' guidance page that explains: 1) use DB filters as a data-layer safeguard, 2) always enforce app-layer authorization (example middleware) and map authenticated identities to allowed patientIds, and 3) provide a minimal code example for FastAPI demonstrating auth checks before querying.

## [high] Exact createIndexes JSON examples

- **What was missing:** Copy-paste createIndexes/runCommand JSON for vector indexes was not obvious to an agent without searching; the model initially suggested a generic createIndex form which would fail.
- **Where the agent looked:** Integrated vector store doc and vector-search skill; the helpful example exists but should be more prominent in quickstarts and sample repos.
- **Effect on this build:** The MCP tool failed; the builder fell back to issuing a createIndexes runCommand via pymongo and succeeded. Clearer copy-paste examples would reduce trial-and-error and prevent MCP/tool fallbacks.
- **Suggested fix (discoverability):** Add a 'Create a vector index' snippet to the vector-search quickstart and a one-line copy-paste JSON block labeled 'createIndexes runCommand for HNSW/IVF/DiskANN' with placeholders for name/dimensions/params.

## [high] Service naming & resource-type clarification

- **What was missing:** Agents confused resource types and CLI groups (mongoClusters vs databaseAccounts / az documentdb vs az cosmosdb) and billing model differences between vCore DocumentDB and RU-based Cosmos DB in readiness checks.
- **Where the agent looked:** Multiple Quickstarts and template docs; the confusion arises from historical naming overlap.
- **Effect on this build:** Potential build risk: an agent could generate IaC targeting Microsoft.DocumentDB/databaseAccounts or az cosmosdb commands which are incorrect for vCore mongoClusters.
- **Suggested fix (naming_or_disambiguation):** Add a 'Which DocumentDB product is this?' banner on the Overview and Quickstart pages that: 1) states current product name(s), 2) maps resource types (Microsoft.DocumentDB/mongoClusters) and CLI commands (az documentdb mongocluster) for vCore clusters, 3) warns about databaseAccounts/azurerm_cosmosdb_account being for RU-based accounts, and 4) supply example Bicep/Terraform snippets for mongoClusters.

## [high] Local gateway/dev image discoverability

- **What was missing:** The guidance on the local DocumentDB gateway Docker image and port (10260) is not prominent enough; agents sometimes default to running a generic MongoDB container which misses DocumentDB-specific features (vector search, createIndexes shape).
- **Where the agent looked:** documentdb-local-deployment skill and local-deployment docs exist but are not always surfaced.
- **Effect on this build:** A developer following a generic Mongo docker-compose could produce tests that pass locally but fail against the real DocumentDB cluster because of missing vector search features.
- **Suggested fix (discoverability):** Add a short 'Local development' section to the Quickstart with the exact docker-compose snippet for the DocumentDB Gateway image (port 10260), SKIP_INIT_DATA and TLS notes, and a note on using the gateway for vector/index testing.

## [medium] Vector index reproducibility

- **What was missing:** No public DocumentDB doc recommending that vector index metadata and embedding pre-processing steps be versioned in source control.
- **Where the agent looked:** Searched Microsoft Learn sites and vector-search docs for 'index metadata source control embedding normalization' with no authoritative result.
- **Effect on this build:** The sample places parameters in scripts and environment variables but does not provide a single versioned config; an agent might change embedding model or dims and not realize index and preprocess steps must remain aligned.
- **Suggested fix (learn_doc):** Short guidance page 'Vector index reproducibility' describing recommended config keys (algorithm, dimensions, similarity, m/efConstruction/numLists) and a versioned JSON snippet to check into repo; show where to store and how to reference the config during ingestion and index creation.

## [medium] Driver recommendation discoverability (model_default decisions)

- **What was missing:** The builder logged a driver choice with reason_source 'model_default' (D003). Although public Quickstarts recommend pymongo, the agent relied on default model assumptions to pick a driver version and installation form.
- **Where the agent looked:** Quickstart examples and documentdb-driver skill were found but not surfaced automatically to the decision maker before the choice.
- **Effect on this build:** The decision was reasonable and matched public guidance, but recording 'model_default' as the reason indicates an agent may make that choice without citing the authoritative page, reducing auditability.
- **Suggested fix (discoverability):** Promote the Quickstart 'Use Azure DocumentDB with MongoDB driver for Python' page in the documentdb-driver skill as an explicit recommended link and add an agent-kit rule: 'When selecting a Python Mongo-compatible driver, use pymongo and cite the Quickstart.'

## [medium] Offline unit tests example

- **What was missing:** No example test harness for running unit tests without a live cluster (mocking pymongo/embedding provider).
- **Where the agent looked:** Repo and public samples; general testing guidance exists but no DocumentDB-specific sample test.
- **Effect on this build:** Verification required a live cluster for some steps; offline tests would increase reliability of CI and reviewer confidence.
- **Suggested fix (sample_or_quickstart):** Add a tests/ folder with pytest tests that mock get_db() and embed_text() (using monkeypatch or mongomock) demonstrating how to unit-test the /search logic and prompt-assembly without a live cluster.

