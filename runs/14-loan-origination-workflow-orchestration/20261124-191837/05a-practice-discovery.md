# 5a. Best practices: prior knowledge against the public record: 14-loan-origination-workflow-orchestration

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**25 practices, 22 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 2 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 3 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 20 | Memory and documentation line up. |
| Found in public sources only | 0 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

## Where public sources contradict the model

### P02: Create one MongoClient per process and reuse it (singleton client pattern) rather than creating a client per request; for Python async prefer PyMongo's AsyncMongoClient (newer async API) rather than Motor.

- **The model believed:** Create a single Motor (AsyncIOMotorClient) instance per process and reuse it across the app (do not create a new client per request). Configure connection pooling (e.g., maxPoolSize) and sensible timeouts (connectTimeoutMS, serverSelectionTimeoutMS) via the client URI or options. (knowledge of `mongodb`)
- **The source says:** Create one MongoClient per process and reuse it (singleton client pattern) rather than creating a client per request; for Python async prefer PyMongo's AsyncMongoClient (newer async API) rather than Motor.
- **Source:** [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md)

### P24: When using Python ODMs, prefer the supported async driver (PyMongo's AsyncMongoClient) and ensure startup registers models/indexes; Motor is deprecated for new async Python code and should be replaced where possible.

- **The model believed:** When using Beanie + Motor, ensure the client is created with consistent UUID/ObjectId handling (e.g., set uuidRepresentation if required) and call init_beanie(database=...) at app startup to register document models and create indexes if desired. (knowledge of `mongodb`)
- **The source says:** When using Python ODMs, prefer the supported async driver (PyMongo's AsyncMongoClient) and ensure startup registers models/indexes; Motor is deprecated for new async Python code and should be replaced where possible.
- **Source:** [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md)

## Known to the model, with no public source for this service

| Id | Practice | Knowledge of | Searches tried |
|---|---|---|---|
| P05 | Design a loan-application document to contain the application id, current state, a version or schema version, a transitions log and timestamps, and separate scheduled-action timestamps if the orchestrator queries by schedule (or store these scheduling items separately). | general | searches: "Azure DocumentDB loan application schema", "loan application document schema state machine Azure DocumentDB", "Beanie loan application model Azure DocumentDB" |
| P07 | Implement optimistic concurrency control by including an expected state or version in update filters (or using service-provided version/ETag checks); treat a non-match as a conflict and retry or re-read rather than relying on last-write-wins. | general | searches: "Azure DocumentDB optimistic concurrency version field", "Azure DocumentDB MongoDB optimistic concurrency pattern" |
| P10 | When using Beanie or another ODM, register document models and create indexes at startup (e.g., call init_beanie / create_indexes) so the app's expected indexes exist when the app runs. | mongodb | searches: "Beanie init_beanie create_indexes Azure DocumentDB", "Beanie create_indexes startup best practice" |

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Do not commit connection strings or secrets to source control: read DOCUMENTDB_URI from the environment at runtime and (in production) retrieve credentials from a secrets store such as Azure Key Vault; provide only a .env.example with placeholders. | authentication_and_secrets | prior_knowledge_confirmed | documentdb-azure-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/azure-deployment/SKILL.md | documentdb-azure-deployment | yes |
| P02 | Create one MongoClient per process and reuse it (singleton client pattern) rather than creating a client per request; for Python async prefer PyMongo's AsyncMongoClient (newer async API) rather than Motor. | connection_handling | prior_knowledge_contradicted | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P03 | Require TLS for all connections (tls=true/ssl=true) and validate certificates in production; do not disable certificate validation. | security | prior_knowledge_confirmed | Quickstart: Use Azure DocumentDB with MongoDB driver for Python (public_doc) | https://learn.microsoft.com/azure/documentdb/quickstart-python#code-examples | Azure DocumentDB mongodb connection string retryWrites=false tls SCRAM-SHA-256 retryWrites Azure DocumentDB connection string | yes |
| P04 | Use least-privilege credentials and prefer Microsoft Entra ID / RBAC or per-application users rather than admin/root credentials in the app. | authentication_and_secrets | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P05 | Design a loan-application document to contain the application id, current state, a version or schema version, a transitions log and timestamps, and separate scheduled-action timestamps if the orchestrator queries by schedule (or store these scheduling items separately). | data_modeling | prior_knowledge_only | - (prior_knowledge) | **none** | searches: "Azure DocumentDB loan application schema", "loan application document schema state machine Azure DocumentDB", "Beanie loan application model Azure DocumentDB" | yes |
| P06 | Make state transitions atomic by filtering the update by the expected current state (or version) and applying $set and $push in a single findOneAndUpdate/updateOne so the state and transition log are updated together. | concurrency_and_transactions | prior_knowledge_confirmed | Updating data in Azure Cosmos DB for MongoDB (public_doc) | https://learn.microsoft.com/azure/cosmos-db/mongodb/tutorial-update | Azure DocumentDB findOneAndUpdate atomic update filter expected state | yes |
| P07 | Implement optimistic concurrency control by including an expected state or version in update filters (or using service-provided version/ETag checks); treat a non-match as a conflict and retry or re-read rather than relying on last-write-wins. | concurrency_and_transactions | prior_knowledge_only | - (prior_knowledge) | **none** | searches: "Azure DocumentDB optimistic concurrency version field", "Azure DocumentDB MongoDB optimistic concurrency pattern" | yes |
| P08 | Avoid unbounded growth of in-document arrays (like transitions); cap the array or move history into a separate transitions collection to stay well under the 16 MB document size limit. | data_modeling | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P09 | Create an index to efficiently find work: at minimum create a compound index on state plus a scheduling or ordering field (for example {state:1, next_action_at:1} or {state:1, updated_at:1}); make application_id unique if you query by it. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P10 | When using Beanie or another ODM, register document models and create indexes at startup (e.g., call init_beanie / create_indexes) so the app's expected indexes exist when the app runs. | provisioning_and_deployment | prior_knowledge_only | - (prior_knowledge) | **none** | searches: "Beanie init_beanie create_indexes Azure DocumentDB", "Beanie create_indexes startup best practice" | yes |
| P11 | Use TTL (expireAfterSeconds) indexes for ephemeral documents or records you want auto-pruned (create an index on a date field with expireAfterSeconds set). | data_retention | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing TTL index guidance | yes |
| P12 | For vector search, store dense float vectors and create a platform-supported vector index with explicit parameters (index type such as DiskANN/HNSW/IVF, dimensions, similarity metric) and test recall/latency on representative vectors. | vector_search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | no |
| P13 | Normalize or L2-normalize embeddings when using cosine similarity and prefer compact float32 (or fp16 where supported) to reduce storage and speed index ops. | vector_search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | no |
| P14 | Use exponential backoff with jitter for application-level retries on transient errors (network blips, 429/TooManyRequests), and keep retries idempotent and bounded to avoid cascading load spikes. | retries_and_resilience | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P15 | Monitor and tune throughput (watch for throttling / 429s): observe cluster metrics, provision appropriate compute/IO or autoscale, and alert on 429s and long-running operations. | provisioning_and_deployment | prior_knowledge_confirmed | documentdb-monitoring (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md | documentdb-monitoring | yes |
| P16 | Prefer single-document atomic updates for orchestrator state changes and use multi-document transactions only when you truly need cross-document atomicity because transactions add latency and cost. | concurrency_and_transactions | prior_knowledge_confirmed | Use Multi-document transactions in Azure Cosmos DB for MongoDB (public_doc) | https://learn.microsoft.com/azure/cosmos-db/mongodb/use-multi-document-transactions | Azure DocumentDB multi-document transactions guidance | yes |
| P17 | Avoid storing secrets, private keys, or raw LLM system prompts in the database; store references or encrypted blobs and consider field-level encryption for sensitive PII. | security | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P18 | Drive orchestration from change notifications (change streams) rather than naive polling when possible: enable change streams and subscribe to changes to reduce cost and latency. | orchestration_pattern | prior_knowledge_confirmed | Change streams in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/change-streams | Azure DocumentDB change streams support | yes |
| P19 | Keep documents small and project only required fields in queries (use projection) to reduce network transfer and cost when listing pending work or fetching histories. | queries | prior_knowledge_confirmed | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | documentdb-query-optimizer | yes |
| P20 | Cap individual document size to avoid hitting the 16 MB BSON limit; move growing history or attachments to separate collections or object storage and reference them. | data_modeling | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling model-16mb-limit | yes |
| P21 | Use explain("executionStats") to validate that queries use the intended index and test representative orchestrator queries before production. | monitoring_and_performance | prior_knowledge_confirmed | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | documentdb-query-optimizer | yes |
| P22 | Restrict network access to the cluster with firewall rules, Private Endpoint / Private Link, or IP allowlists; do not expose the database publicly without network controls. | security | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P23 | Include a schema_version (or schemaVersion) field in documents and run controlled migration scripts as deployment steps rather than on-the-fly during reads/writes. | operations | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling model-schema-versioning | yes |
| P24 | When using Python ODMs, prefer the supported async driver (PyMongo's AsyncMongoClient) and ensure startup registers models/indexes; Motor is deprecated for new async Python code and should be replaced where possible. | tooling_and_frameworks | prior_knowledge_contradicted | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection (Python async note: prefer PyMongo AsyncMongoClient over Motor) | yes |
| P25 | Consider client-side field-level encryption for highly sensitive fields (SSNs, bank account numbers) when regulatory requirements demand it; otherwise rely on TLS in transit and platform-managed or customer-managed encryption at rest. | security | prior_knowledge_confirmed | Compare Azure DocumentDB to MongoDB Atlas (security & compliance) (public_doc) | https://learn.microsoft.com/azure/documentdb/compare-mongodb-atlas#security-and-compliance | Azure DocumentDB client-side field-level encryption support | yes |

## Searches that returned nothing useful

- Beanie create_indexes Azure DocumentDB
- Azure DocumentDB guidance: Motor vs AsyncMongoClient (Microsoft Learn)
- Azure DocumentDB best practice exact loan-application document schema
- Azure DocumentDB guidance for optimistic concurrency using version field in Mongo API

## Notes

Open discovery used installed skills (documentdb-*) and Microsoft Learn pages (connection strings, change streams, updates, transactions, encryption). Practices most relevant to this sample app (connection handling, singleton client, TLS, secrets, atomic state updates, indexing, document sizing, change streams, retries, and monitoring) were found in the skills and Learn docs. A few prior beliefs (K05, K07, K10) are informed by general MongoDB/ODM experience but lacked an explicit Azure DocumentDB page prescribing the exact pattern; they are listed as prior_knowledge_only with the searches attempted.

