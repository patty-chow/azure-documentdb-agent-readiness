# 5a. Best practices: prior knowledge against the public record: 16-subscription-billing-engine

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**16 practices, 16 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 0 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 0 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 13 | Memory and documentation line up. |
| Found in public sources only | 3 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Read the DocumentDB/MongoDB connection string from an environment variable (e.g. MONGODB_URI or DOCUMENTDB_URI) and do not commit secrets to source control. | authentication | prior_knowledge_confirmed | Quickstart: Connect Mongoose to Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/quickstart-nodejs-mongoose#create-the-project | Azure DocumentDB connection string environment variable | yes |
| P02 | Require TLS for client connections (include tls=true in the URI) and use SCRAM-SHA-256 authentication for Azure DocumentDB connections. | authentication | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P03 | Create a single shared MongoClient / Mongoose connection (singleton) and reuse it across the process rather than creating a new connection per request. | connection handling | prior_knowledge_confirmed | documentdb-driver (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md | documentdb-driver | yes |
| P04 | Tune connection-pool and timeout settings for your deployment (serverless vs long-running) — e.g., small pools and low minPoolSize for serverless, larger maxPoolSize and longer maxIdleTime for OLTP servers; set serverSelectionTimeoutMS/connectTimeoutMS appropriately. | connection handling | found_in_public_source | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P05 | When using multi-document transactions, start a session, pass the session into every read and write that belongs to the transaction, and commit or abort explicitly (or use withTransaction when available). | transactions | prior_knowledge_confirmed | Group multiple operations in transactions in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/how-to-transactions#create-a-transaction | Azure DocumentDB transactions startSession | yes |
| P06 | Use a TTL index (expireAfterSeconds) on an expiration Date field (e.g., expiresAt) for ephemeral entitlement/trial documents so the database automatically removes expired documents. | ttl | prior_knowledge_confirmed | MongoDB Query Language (MQL) compatibility in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/compatibility-query-language#index-types | Azure DocumentDB TTL index expireAfterSeconds TTL indexes expiresAt | yes |
| P07 | Persist an idempotency marker using a unique index (for example on idempotencyKey) so duplicate attempts produce a duplicate-key error that the application can detect and handle instead of double-processing. | idempotency | prior_knowledge_confirmed | Reliability in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/reliability/reliability-documentdb#resilience-to-transient-faults | Azure DocumentDB idempotency unique index | yes |
| P08 | Create indexes to match your query patterns (equality → sort → range ordering) and verify index usage with explain('executionStats') to avoid collection scans. | indexing | prior_knowledge_confirmed | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | documentdb-query-optimizer | yes |
| P09 | Keep transactional scope minimal — only touch the documents that must be updated atomically to reduce conflicts and latency. | transactions | prior_knowledge_confirmed | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | documentdb-query-optimizer | yes |
| P10 | Azure DocumentDB documents are limited to 16 MB and transactions have a maximum lifetime (transaction timeout documented in service limits); design transactions and document sizes accordingly. | performance | found_in_public_source | Azure DocumentDB service limits and quotas reference (public_doc) | https://learn.microsoft.com/azure/documentdb/limitations | Azure DocumentDB transaction lifetime 30 seconds document size 16 MB | yes |
| P11 | When using Mongoose transactions, explicitly pass the session returned by startSession() into Model.create(), updateOne(), findOneAndUpdate(), etc., so those operations participate in the transaction. | Mongoose | prior_knowledge_confirmed | Use Mongoose with Azure DocumentDB: Build a Node.js inventory API (public_doc) | https://learn.microsoft.com/azure/documentdb/tutorial-nodejs-mongoose#mongoose-on-azure-documentdb | Use Mongoose with Azure DocumentDB transactions pass session | yes |
| P12 | Implement bounded retries with exponential backoff for transient errors and ensure retries are safe (idempotent) or protected by the idempotency key rather than blindly reissuing non-idempotent writes. | retries | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P13 | Disable automatic index creation in Mongoose in production (autoIndex: false) and create your indexes as part of a deployment/migration step rather than at runtime. | provisioning | prior_knowledge_confirmed | Use Mongoose with Azure DocumentDB: Build a Node.js inventory API (public_doc) | https://learn.microsoft.com/azure/documentdb/tutorial-nodejs-mongoose#create-the-project | Azure DocumentDB manage index creation deployment createIndexes vs autoIndex | yes |
| P14 | For vector search, set retryWrites=false in the connection and create the appropriate vector index (HNSW/IVF/DiskANN) with correct metric and dimension settings before storing embeddings. | vector search | found_in_public_source | Quickstart: Vector index with Python in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/quickstart-python-select-algorithm#create-the-algorithm-comparison-code | Azure DocumentDB vector index retryWrites=false vector index type HNSW DiskANN IVF | no |
| P15 | Enable diagnostic settings and collect slow-query logs and metrics (CPU, memory, IOPS, connections) into Log Analytics and alert on saturation or elevated retry/failed-transaction rates. | monitoring | prior_knowledge_confirmed | documentdb-monitoring (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md | documentdb-monitoring | yes |
| P16 | Use least-privilege credentials for the app: create a database user limited to the application database and grant only the minimal roles/permissions required rather than using an admin/root account; consider Microsoft Entra ID and role-based access control for production. | security | prior_knowledge_confirmed | Migrate from Amazon DocumentDB to Azure DocumentDB (with MongoDB compatibility) (public_doc) | https://learn.microsoft.com/azure/documentdb/migrate-amazon-documentdb#update-your-application | Azure DocumentDB migration create database user minimum permissions | yes |

## Searches that returned nothing useful

- Azure DocumentDB writeConcern majority recommendation
- Azure DocumentDB readConcern repeatable read recommendation for financial operations
- Azure DocumentDB validate idempotency key length 'idempotencyKey' guidance
- Azure DocumentDB recommended retention TTL for billing/audit history guidance

## Notes

Discovery combined official Azure DocumentDB docs (learn.microsoft.com) and the installed DocumentDB skills. Practices most relevant to the sample app (connection handling, transactions, idempotency, TTL, index creation, Mongoose session usage, retries and monitoring) appear in service docs or the installed skills. A few application-level best practices (idempotency key canonicalization, exact writeConcern/readConcern choices for financial workloads, and retention policy decisions for audit records) did not have a single Azure DocumentDB doc prescribing the exact wording in the prior beliefs; those are recorded below as prior_knowledge_only entries where appropriate.

Prior beliefs the discovery step did not classify: K10, K11, K13, K16, K17, K18, K19. See 05a-prior-beliefs.json.

