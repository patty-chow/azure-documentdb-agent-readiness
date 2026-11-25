# 5. Best-practice audit: 07-mortgage-application-multi-agent

**Verdict: pass_with_findings** (8 followed, 4 not assessable, 1 violated, 1 not applicable)

The sample is a working Node.js Express app that implements a clear multi-step mortgage pipeline, reads/writes from the provided Azure DocumentDB cluster, includes an idempotent seeder, unit tests that run without a live cluster, and documents how to run and test. The builder intentionally avoided creating vector indexes programmatically (documented in README) and used deterministic fallbacks when LLM credentials are missing. Major missing items that the owner should fix before publishing: (1) the implementation does not use the LangChain library even though the prompt asked for a LangChain multi-agent sample; (2) the compliance agent was not passed the underwriting result; (3) no programmatic vector-index creation or search endpoint exists (so vector-dimension correctness and search error handling are not implemented); (4) no decisions about retry/backoff were implemented although the connection skill was loaded. These do not make the sample non-functional for demonstrations without LLMs, but they are important checklist and discoverability gaps the product team should address for future agents.

## Review of the builder's decisions

| Decision | What was decided | Reason came from | Assessment | Comment |
|---|---|---|---|---|
| D001 | I approved the build with readiness 'ready_with_gaps' | operator | sound | The decision to approve with readiness 'ready_with_gaps' is supported by the builder_report and the run logs that show tests, seeding and an end-to-end demo run. The reason is operator-sourced and acceptable. |
| D002 | I chose Node.js (v24) with Express for the sample app and LangChain-style agents in Node. | prompt | sound | The builder chose Node.js/Express; package.json and src/index.js confirm that choice and the environment provided Node.js 24. Events log shows npm install and test runs. |
| D003 | I chose the official MongoDB Node.js driver 'mongodb' at version '^5.0.0'. | model_default | sound | The choice of the 'mongodb' driver is reflected in package.json ("mongodb": "^5.0.0"). The reason was marked model_default but the code matches the decision. |
| D004 | I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime. | prompt | sound | The code reads process.env.DOCUMENTDB_URI in src/db.js and .env.example is present; events show this decision and the files created accordingly. |
| D005 | I chose to use the existing pre-provisioned cluster and not to provision any Azure resources. | prompt | sound | The run used the existing cluster (documentdb_list_databases and documentdb_find_documents events) and run policy forbade provisioning; logs back the decision to not provision. |
| D006 | I chose not to create a shard key; collections will be single-shard for this sample. | model_default | sound | The decision to not shard is evidenced by the absence of sharding code and the repo's seed and pipeline working on unsharded collections. |
| D007 | I chose OpenAI for the embedding and chat models, with embedding model 'text-embedding-3-small' (1536 dims) and a chat model placeholder 'gpt-4o-mini' for agents. | model_default | questionable | The builder logged OpenAI model choices and the embedding model/dimensions in .env.example and decisions.jsonl, but the sample never computes embeddings or creates vector indexes programmatically. The choice is recorded and present in files, but it is not exercised in the app. |
| D008 | I chose Jest for unit testing and simple mocking of DB/LLM. | model_default | sound | Jest was chosen and used. events.jsonl shows npm test passing and test/pipeline.test.js exists and uses mocked DB/LLM. |
| D009 | I chose NOT to create a vector index programmatically in the seed script and instead documented the manual step in README. | model_default | sound | The builder explicitly opted not to create a vector index programmatically (decision recorded) and documented the reason in the README. The events show the decision was logged and the README/seed do not create vector indexes. |

Documentation gaps: 7 (see `doc-gaps.md`).

## Appendix

### Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

### Public availability of best practices

| Outcome | Count | What it means |
|---|---|---|
| On the checklist, no public source found | 0 | Not public, or not written down. A documentation gap. |
| On the checklist, found only when searched for by name | 1 | Public but hard to find. A discoverability gap. |
| Found publicly, not on the checklist | 0 | Add it to the checklist, or check that the public guidance is what the team intends. |
| Known to the model, no public source, not on the checklist | 1 | Agents will act on it from memory. Decide whether it holds for this service, then document it either way. |
| On the checklist and found by open discovery | 12 | Public and discoverable. |

#### On the checklist, found only when searched for by name

| Topic | Searched for | Sources |
|---|---|---|
| Driver version pinning | The driver version is pinned and is one the service supports.<br>**Searches:** Searched Learn quickstarts for tested driver versions; docs list tested driver versions and compatibility guidance. | [Quickstart: Connect Mongoose to Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/quickstart-nodejs) |

#### Known to the model, no public source, not on the checklist

| Topic | Description | What would help |
|---|---|---|
| Sanitize PII before LLM | Perform input validation and sanitize free-text prior to passing it to an LLM and avoid storing unnecessary PII; for data-at-rest encryption of sensitive fields prefer customer-managed keys (CMK) where compliance requires it. | A Learn page or sample README note describing recommended PII sanitization and examples of fields to scrub before calling an LLM. |

#### On the checklist and found by open discovery

| Topic | Description | Sources |
|---|---|---|
| Client singleton | Create and reuse a single MongoClient instance (process-wide singleton) rather than creating a new client per request; initialize it once and reuse across handlers (cache on module/global scope). | documentdb-driver (driver-singleton-client)<br>documentdb-driver (driver-singleton-client) |
| TLS enforcement | Always use TLS for connections to Azure DocumentDB (connection strings include tls=true) and do not disable certificate validation in production. | [Connect to Azure DocumentDB using MongoDB Shell](https://learn.microsoft.com/azure/documentdb/how-to-connect-mongo-shell#connect-with-interactive-password-authentication)<br>[Quickstart: Connect Mongoose to Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/quickstart-nodejs-mongoose#create-the-project) |
| Connection timeouts & retries | Connection settings (timeouts, retry options, TLS) follow the service's recommendation for the chosen driver. | documentdb-driver (driver-singleton-client)<br>[documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md)<br>[documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| No secrets in repo | Read the DocumentDB connection string from environment variables and keep a .env.example placeholder rather than committing secrets into the repo. | [Quickstart: Connect Mongoose to Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/quickstart-nodejs-mongoose#create-the-project) |
| Least-privilege credentials | Use least-privilege credentials: prefer Microsoft Entra ID / RBAC or create DB users with only necessary privileges rather than a full admin key; rotate secrets and prefer Key Vault references for deployment-time secrets. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Index for queries | Create indexes on frequently filtered or sorted fields used by the pipeline (e.g., applicationId, status, createdAt, credit_score). | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Explain/avoid COLLSCAN | Avoid unindexed queries and full-collection scans in production; use explain('executionStats') to verify queries use indexes. | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |
| Idempotent writes | Make pipeline output idempotent—use upsert keyed by applicationId or decisionId so retries don't create duplicate documents. | [Build a Node.js console app with Azure DocumentDB (perform common operations / upsert example)](https://learn.microsoft.com/azure/documentdb/how-to-build-nodejs-console-app#perform-common-operations) |
| 16 MB document limit | Observe the maximum BSON document size (16 MB) and avoid embedding very large blobs—store large binary or long text in external storage (e.g., Azure Blob Storage). | [Document size and batch write limits in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/max-document-size) |
| Retries and backoff | Handle transient errors with bounded exponential-backoff retries and detect 429 throttling. | [Reliability in Azure DocumentDB](https://learn.microsoft.com/azure/reliability/reliability-documentdb#resilience-to-transient-faults) |
| Monitoring & alerts | Instrument and monitor cluster metrics (CPU, memory, IOPS, storage), query/slow-query logs, connection pool metrics and throttling (429) via Azure Monitor / Log Analytics and alert on high throttling or resource saturation. | [documentdb-monitoring](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md) |
| Local gateway for development | Run the DocumentDB Gateway Docker image (port 10260, TLS) for local development rather than a vanilla mongo:latest image on 27017. | [documentdb-local-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md) |

### How the app measures up

#### Violations

| Practice | Category | Evidence | Fix | Source |
|---|---|---|---|---|
| Handle transient errors with bounded exponential-backoff retries and detect 429 throttling. | retries | src/db.js sets retryReads: true but the application code does not implement bounded exponential-backoff around operations or special handling for 429s; no retry wrapper is present. | Implement a small retry wrapper for transient operations (bounded exponential backoff, check for 429 status and network errors) or use a helper from documentdb-connection skill. | [Reliability in Azure DocumentDB](https://learn.microsoft.com/azure/reliability/reliability-documentdb#resilience-to-transient-faults) |

#### Could not be assessed

| Practice | Category | What was searched and missing | Source |
|---|---|---|---|
| Use least-privilege credentials: prefer Microsoft Entra ID / RBAC or create DB users with only necessary privileges rather than a full admin key; rotate secrets and prefer Key Vault references for deployment-time secrets. | authentication_and_secrets | Inspected README and src/db.js for Entra/OIDC usage and KeyVault integration; none found. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Avoid unindexed queries and full-collection scans in production; use explain('executionStats') to verify queries use indexes. | queries_and_explain | - | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |
| Perform input validation and sanitize free-text prior to passing it to an LLM and avoid storing unnecessary PII; for data-at-rest encryption of sensitive fields prefer customer-managed keys (CMK) where compliance requires it. | security_and_compliance | Searched docs for explicit Azure DocumentDB guidance on LLM PII sanitization; found no specific page. | prior_knowledge_only (no public address recorded) |
| Instrument and monitor cluster metrics (CPU, memory, IOPS, storage), query/slow-query logs, connection pool metrics and throttling (429) via Azure Monitor / Log Analytics and alert on high throttling or resource saturation. | monitoring | - | [documentdb-monitoring](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md) |

#### Followed

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Create and reuse a single MongoClient instance (process-wide singleton) rather than creating a new client per request; initialize it once and reuse across handlers (cache on module/global scope). | connection_handling | src/db.js:11-17 (getClient() creates a module-scoped client and returns it on subsequent calls). | documentdb-driver (driver-singleton-client)<br>documentdb-driver (driver-singleton-client) |
| Always use TLS for connections to Azure DocumentDB (connection strings include tls=true) and do not disable certificate validation in production. | network_security | The app reads the connection URI from DOCUMENTDB_URI (src/db.js:4) and README instructs to include tls=true in the URI (app/README.md:11-14). | [Connect to Azure DocumentDB using MongoDB Shell](https://learn.microsoft.com/azure/documentdb/how-to-connect-mongo-shell#connect-with-interactive-password-authentication)<br>[Quickstart: Connect Mongoose to Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/quickstart-nodejs-mongoose#create-the-project) |
| Connection settings (timeouts, retry options, TLS) follow the service's recommendation for the chosen driver. | connection_handling | src/db.js sets connectTimeoutMS, socketTimeoutMS, maxPoolSize and retryReads when constructing MongoClient (src/db.js:11-17). | documentdb-driver (driver-singleton-client)<br>[documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md)<br>[documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| The driver version is pinned and is one the service supports. | connection | package-lock.json exists in repo (provides exact versions). package.json uses "mongodb": "^5.0.0" (app/package.json). | [Quickstart: Connect Mongoose to Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/quickstart-nodejs) |
| Read the DocumentDB connection string from environment variables and keep a .env.example placeholder rather than committing secrets into the repo. | authentication_and_secrets | .env.example present with placeholders (app/.env.example) and src/db.js reads process.env.DOCUMENTDB_URI (src/db.js:4). | [Quickstart: Connect Mongoose to Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/quickstart-nodejs-mongoose#create-the-project) |
| Create indexes on frequently filtered or sorted fields used by the pipeline (e.g., applicationId, status, createdAt, credit_score). | indexing | src/seed.js creates indexes: apps.createIndex({ applicationId: 1 }, { unique: true }); apps.createIndex({ name: 'text' }); apps.createIndex({ credit_score: 1 }); | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Make pipeline output idempotent—use upsert keyed by applicationId or decisionId so retries don't create duplicate documents. | data_integrity | src/pipeline.js performs decisions.updateOne({ applicationId }, { $set: decisionDoc }, { upsert: true }); | [Build a Node.js console app with Azure DocumentDB (perform common operations / upsert example)](https://learn.microsoft.com/azure/documentdb/how-to-build-nodejs-console-app#perform-common-operations) |
| Observe the maximum BSON document size (16 MB) and avoid embedding very large blobs—store large binary or long text in external storage (e.g., Azure Blob Storage). | data_modeling | Seeded application documents are small and README warns about storing large content; no large blobs are embedded in documents (src/seed.js sample schemas). | [Document size and batch write limits in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/max-document-size) |

#### Not applicable

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Run the DocumentDB Gateway Docker image (port 10260, TLS) for local development rather than a vanilla mongo:latest image on 27017. | local_deployment | The run environment states no local gateway is running and the sample is designed to run against the live cluster; the sample README documents the expectation to use a reachable cluster (app/README.md:11-14). | [documentdb-local-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md) |

### Reference requirements

12 of 20 met. The builder never saw these; this measures the starter prompt and the skills.

| Requirement | Status | Cause | Evidence | Smallest fix |
|---|---|---|---|---|
| The vector index dimensions match the embedding model's output. | not_met | prompt_silent | No programmatic vector-index creation is present; the README documents vector index creation as a manual step and the seed script does not create vector indexes (README notes and events.log entries). | Add vector-index creation to the seed script using EMBEDDING_MODEL/EMBEDDING_DIM env vars (or read a dimension value from EMBEDDING_MODEL mapping) and create the index with createIndexes + cosmosSearchOptions matching that dimension. |
| The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. | not_met | prompt_silent | README states vector-index creation is left as a manual step but does not supply concrete index parameters or tuning guidance for different dataset sizes (app/README.md notes). | Add a short section showing sensible default cosmosSearchOptions (kind, dimensions, lBuild/lSearch/maxCandidate parameters) for the demo and example adjustments for larger datasets. |
| /search returns a clear error for an empty query and when the embedding call fails. | not_met | prompt_silent | No /search endpoint is implemented in src/index.js or elsewhere; search operations and embedding storage are not present. | Implement a /search route that validates queries, returns 400 for empty queries, wraps embedding calls in try/catch, and returns meaningful 500-level errors when the embedding provider fails. |
| Search results include the similarity score. | not_met | prompt_silent | No search endpoint or embedding-based ranking exists in the codebase. | When adding /search, include the vector match similarity score in the response (fetch score from $search / cosmosSearch response and return it with each hit). |
| Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. | not_met | prompt_silent | No IaC (Bicep/ARM/Terraform) files are present in the repository. The builder decided to use an existing cluster (decision D005) and README documents manual inspection via MCP rather than providing IaC. | Add a minimal Bicep or Terraform example using Microsoft.DocumentDB/mongoClusters (documentdb-azure-deployment skill can be used to provide the template) with cheap default tier parameters and instructions on safe provisioning. |
| The pipeline is written in Node.js and built with LangChain: an orchestrator coordinates three LangChain agents, one each for underwriting, compliance and customer communications. | partly_met | builder_error | package.json (dependencies) shows Node.js project and src/pipeline.js orchestrates three local agent modules (src/agents/underwriting.js, src/agents/compliance.js, src/agents/comms.js); no 'langchain' package is present in package.json or the code. | Either add LangChain as a dependency and re-implement the agents as LangChain agents, or change the prompt/README to describe this as a LangChain-style (module-based) demo rather than a literal LangChain example. |
| The compliance agent receives the application together with the underwriting assessment, checks regulatory requirements, and returns its result to the orchestrator. | partly_met | builder_error | src/pipeline.js:14-16 calls compliance.check(app) (passes only the application). src/agents/compliance.js exposes async function check(application) and performs deterministic checks. | Pass the underwriting result into the compliance agent (change pipeline to await compliance.check(app, uw) and update the compliance.check signature to accept the underwriting payload). |
| The orchestrator runs the agents in sequence, underwriting then compliance then comms, with each agent receiving the previous agent's output. | partly_met | builder_error | src/pipeline.js runs underwriting then compliance then comms in order, but compliance does not receive underwriting output (see pipeline.js:6-16 and compliance.check signature). | Update pipeline and compliance agent to pass and accept the underwriting result. |
| The orchestrator reads a mortgage application document from Azure DocumentDB with the MongoDB Node.js driver and hands it to the underwriting agent. | met | - | src/pipeline.js:6-13 (calls getDb(), apps.collection('applications'), apps.findOne({ applicationId })) and then calls underwriting.assess(app). | - |
| The underwriting agent assesses the applicant's affordability from the application document and returns its assessment to the orchestrator. | met | - | src/agents/underwriting.js (assess function implements rule-based affordability calculation and returns decision, score, rationale). | - |
| The comms agent receives the application plus the underwriting and compliance results and drafts the decision letter. | met | - | src/pipeline.js calls comms.draft(app, uw, comp) and src/agents/comms.js drafts a template-based or LLM-generated letter. | - |
| After the comms agent finishes, the orchestrator writes the outcome (e.g. the affordability assessment, compliance result and decision letter) back to Azure DocumentDB. | met | - | src/pipeline.js: decisionDoc is constructed and decisions.updateOne({ applicationId }, { $set: decisionDoc }, { upsert: true }) is executed (upsert ensures idempotent write). | - |
| The connection string and model credentials come from environment variables; none appear in the repository. | met | - | .env.example contains placeholders for DOCUMENTDB_URI, OPENAI_API_KEY, OPENAI_MODEL, EMBEDDING_MODEL, DB_NAME, PORT; src/db.js reads process.env.DOCUMENTDB_URI and agents read OPENAI_API_KEY / OPENAI_MODEL. | - |
| A .env.example lists every setting with placeholder values. | met | - | .env.example created (contains DOCUMENTDB_URI, OPENAI_API_KEY, OPENAI_MODEL, EMBEDDING_MODEL, DB_NAME, PORT). | - |
| One database client is created and reused across requests. | met | - | src/db.js defines a module-scoped client and getClient/getDb functions that reuse the client (src/db.js:11-17 and getDb uses the single client). | - |
| A seed script loads sample data and creates the index, and can be run twice without duplicating data. | met | - | src/seed.js uses updateOne(..., { upsert: true }) for each sample and creates indexes (applicationId unique, text index on name, credit_score index). | - |
| Dependencies are pinned in requirements.txt. | met | - | package-lock.json exists in the repository (provides an exact snapshot of installed dependency versions). | Optionally pin package.json to exact versions or document reliance on package-lock.json in README. |
| Unit tests run without a live cluster. | met | - | test/pipeline.test.js mocks getDb and the mongodb package; npm test passed in the run trace (events.jsonl run_command for npm test shows PASS). | - |
| The README covers what the sample shows, prerequisites, setup, run, and clean-up. | met | - | app/README.md includes sections What this sample shows, Prerequisites, Setup, Seed sample data, Run the pipeline, Testing, and Cleanup. | - |
| The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name. | met | - | README and code reference 'Azure DocumentDB' and DOCUMENTDB_URI; no Cosmos DB or legacy product name appears in the sample files. | - |

