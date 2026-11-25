# 5a. Best practices: prior knowledge against the public record: 07-mortgage-application-multi-agent

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**22 practices, 19 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 2 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 2 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 18 | Memory and documentation line up. |
| Found in public sources only | 0 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

## Where public sources contradict the model

### P05: Provision capacity by choosing the appropriate cluster compute tier (M10, M30, etc.) and storage sizing and monitor CPU/IOPS/storage/connection metrics (throughput is driven by compute/storage tier rather than Cosmos-style RU tokens); optimize queries to reduce IO and index usage.

- **The model believed:** Provision and monitor throughput (RUs) for the database/collections and design queries to minimize RU cost: use projections to fetch only needed fields and avoid returning large documents unnecessarily. (knowledge of `azure_cosmos_db`)
- **The source says:** Provision capacity by choosing the appropriate cluster compute tier (M10, M30, etc.) and storage sizing and monitor CPU/IOPS/storage/connection metrics (throughput is driven by compute/storage tier rather than Cosmos-style RU tokens); optimize queries to reduce IO and index usage.
- **Source:** [documentdb-azure-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/azure-deployment/SKILL.md)

### P20: Azure DocumentDB supports multi-document transactions and the API exposes startSession()/withTransaction() that can run across multiple logical and physical shards (be aware of transaction timeouts and limits).

- **The model believed:** Avoid long-running multi-document transactions across different partitions; prefer idempotent single-document updates or orchestrated workflows with compensation logic if multi-collection atomicity is required. (knowledge of `azure_cosmos_db`)
- **The source says:** Azure DocumentDB supports multi-document transactions and the API exposes startSession()/withTransaction() that can run across multiple logical and physical shards (be aware of transaction timeouts and limits).
- **Source:** [Group multiple operations in transactions in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/how-to-transactions)

## Known to the model, with no public source for this service

| Id | Practice | Knowledge of | Searches tried |
|---|---|---|---|
| P14 | Perform input validation and sanitize free-text prior to passing it to an LLM and avoid storing unnecessary PII; for data-at-rest encryption of sensitive fields prefer customer-managed keys (CMK) where compliance requires it. | general | "Azure DocumentDB LLM PII sanitization"; "Azure DocumentDB guidance PII storage and encryption" |
| P19 | Mock the database and external LLMs in unit tests and keep live-cluster integration tests gated or explicit (unit tests should be hermetic). | general | searches: "Azure DocumentDB testing guidance mock mongodb unit tests"; "Azure DocumentDB LLM mocking guidance" |

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Read the DocumentDB connection string from environment variables (e.g., DOCUMENTDB_URI) and keep a .env.example placeholder rather than committing secrets into the repo. | authentication_and_secrets | prior_knowledge_confirmed | Quickstart: Connect Mongoose to Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/quickstart-nodejs-mongoose#create-the-project | "Azure DocumentDB .env connection string example" | yes |
| P02 | Create and reuse a single MongoClient instance (process-wide singleton) rather than creating a new client per request; initialize it once and reuse across handlers (cache on module/global scope). | connection_handling | prior_knowledge_confirmed | documentdb-driver (driver-singleton-client) (installed_skill) | **none** | load_skill documentdb-driver | yes |
| P03 | Always use TLS for connections to Azure DocumentDB (connection strings include tls=true) and do not disable certificate validation in production. | network_security | prior_knowledge_confirmed | Connect to Azure DocumentDB using MongoDB Shell (public_doc) | https://learn.microsoft.com/azure/documentdb/how-to-connect-mongo-shell#connect-with-interactive-password-authentication | "Azure DocumentDB tls=true connection string" | yes |
| P04 | Handle transient errors with bounded exponential-backoff retries and specifically detect and back off / retry on throttling (429) or transient network errors rather than unlimited retries. | retries | prior_knowledge_confirmed | Reliability in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/reliability/reliability-documentdb#resilience-to-transient-faults | "Azure DocumentDB transient fault handling 429 exponential backoff" | yes |
| P05 | Provision capacity by choosing the appropriate cluster compute tier (M10, M30, etc.) and storage sizing and monitor CPU/IOPS/storage/connection metrics (throughput is driven by compute/storage tier rather than Cosmos-style RU tokens); optimize queries to reduce IO and index usage. | provisioning_and_performance | prior_knowledge_contradicted | documentdb-azure-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/azure-deployment/SKILL.md | load_skill documentdb-azure-deployment | yes |
| P06 | Choose an appropriate shard key (partition key) based on query and write patterns—pick a key that localizes the most-common reads or that evenly distributes writes to avoid hot partitions. | data_modeling_and_partitioning | prior_knowledge_confirmed | documentdb-sharding (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/sharding/SKILL.md | load_skill documentdb-sharding | yes |
| P07 | Create indexes on frequently filtered or sorted fields used by the pipeline (e.g., applicationId, status, createdAt, credit_score) so lookups and sorts are covered by indexes. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | load_skill documentdb-indexing | yes |
| P08 | Avoid unindexed queries and full-collection scans in production; use explain('executionStats') to verify queries use indexes and to examine keysExamined/docsExamined/execTime metrics. | queries_and_explain | prior_knowledge_confirmed | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | load_skill documentdb-query-optimizer | yes |
| P09 | For vector similarity search use a dedicated vector index (cosmosSearch) and choose the implementation (DiskANN / HNSW / IVF) appropriate to scale and recall requirements; create the index with correct dimensions and similarity metric (COS/L2/IP). | vector_search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | load_skill documentdb-vector-search | no |
| P10 | When performing ANN/vector queries, tune candidate sizes and index/query parameters and fetch only required document fields (projections) and apply post-filters to reduce IO, memory use, and latency. | vector_search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | load_skill documentdb-vector-search | no |
| P11 | Make pipeline output idempotent—use upsert (e.g., updateOne with upsert: true) keyed by applicationId or decisionId so retries don't create duplicate documents. | data_integrity | prior_knowledge_confirmed | Build a Node.js console app with Azure DocumentDB (perform common operations / upsert example) (public_doc) | https://learn.microsoft.com/azure/documentdb/how-to-build-nodejs-console-app#perform-common-operations | "Azure DocumentDB upsert updateOne upsert example" | yes |
| P12 | Observe the maximum BSON document size (16 MB) and avoid embedding very large blobs—store large binary or long text in external storage (e.g., Azure Blob Storage) and keep references in DocumentDB. | data_modeling | prior_knowledge_confirmed | Document size and batch write limits in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/max-document-size | "Azure DocumentDB max document size 16 MB" | yes |
| P13 | Use TTL (time-to-live) indexes for ephemeral or cache-like collections (create an index with expireAfterSeconds) to automatically expire old documents. | lifecycle_management | prior_knowledge_confirmed | MongoDB Query Language (MQL) compatibility in Azure DocumentDB (index types / TTL) (public_doc) | https://learn.microsoft.com/azure/documentdb/compatibility-query-language#index-types | "Azure DocumentDB TTL index expireAfterSeconds" | no |
| P14 | Perform input validation and sanitize free-text prior to passing it to an LLM and avoid storing unnecessary PII; for data-at-rest encryption of sensitive fields prefer customer-managed keys (CMK) where compliance requires it. | security_and_compliance | prior_knowledge_only | - (prior_knowledge) | **none** | "Azure DocumentDB LLM PII sanitization"; "Azure DocumentDB guidance PII storage and encryption" | yes |
| P15 | Use least-privilege credentials: prefer Microsoft Entra ID / RBAC or create DB users with only necessary privileges rather than a full admin key; rotate secrets and prefer Key Vault references for deployment-time secrets. | authentication_and_secrets | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | load_skill documentdb-security | yes |
| P16 | Design queries and indexes to avoid cross-partition sorts and aggregations; when heavy aggregation is required, pre-aggregate or target a single partition where possible. | queries_and_aggregation | prior_knowledge_confirmed | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | load_skill documentdb-query-optimizer | yes |
| P17 | Close the MongoClient cleanly on application shutdown and only close when the process is exiting, ensuring background tasks are drained to avoid leaked connections or partial writes. | connection_handling | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | load_skill documentdb-connection | yes |
| P18 | Instrument and monitor cluster metrics (CPU, memory, IOPS, storage), query/slow-query logs, connection pool metrics and throttling (429) via Azure Monitor / Log Analytics and alert on high throttling or resource saturation. | monitoring | prior_knowledge_confirmed | documentdb-monitoring (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md | load_skill documentdb-monitoring | yes |
| P19 | Mock the database and external LLMs in unit tests and keep live-cluster integration tests gated or explicit (unit tests should be hermetic). | testing | prior_knowledge_only | - (prior_knowledge) | **none** | searches: "Azure DocumentDB testing guidance mock mongodb unit tests"; "Azure DocumentDB LLM mocking guidance" | yes |
| P20 | Azure DocumentDB supports multi-document transactions and the API exposes startSession()/withTransaction() that can run across multiple logical and physical shards (be aware of transaction timeouts and limits). | transactions_and_consistency | prior_knowledge_contradicted | Group multiple operations in transactions in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/how-to-transactions | "Azure DocumentDB transactions across shards" | no |
| P21 | Use projections to limit returned fields (exclude large vectors or unneeded subdocuments) and prefer range-based or cursor-based pagination over deep skip-based offsets. | queries_and_performance | prior_knowledge_confirmed | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | load_skill documentdb-query-optimizer | yes |
| P22 | When storing embeddings, persist retrieval metadata (source document id, chunk id, text snippet, model name, and vector dimension) as separate indexed fields alongside the vector to allow efficient retrieval after a vector match. | vector_search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | load_skill documentdb-vector-search | no |

## Searches that returned nothing useful

- Azure DocumentDB guidance for sanitizing PII before passing to an LLM
- Azure DocumentDB guidance on storing LLM-generated rationales / provenance fields as a recommended pattern

## Notes

I inspected the sample app (seed, db, pipeline, agents) and used official Microsoft docs (learn.microsoft.com) via searches plus the installed DocumentDB skills. Many general MongoDB best practices are explicitly present in the DocumentDB public docs and the installed skills (singleton MongoClient, TLS, retry handling, index design, explain(), vector index choices, TTL, 16MB doc size, upsert examples, monitoring/alerts, compute-tier provisioning). A few app-level concerns tied to LLM usage (sanitization of free text before LLM, explicit guidance on storing decision rationales) are not present in Azure DocumentDB documentation and are recorded as prior_knowledge_only entries (K14, K19). K05 (RU-based provisioning) and K20 (avoid cross-partition transactions) were contradicted for Azure DocumentDB: the public record indicates capacity is chosen by compute/storage tier rather than Cosmos-style RUs, and DocumentDB supports multi-document transactions across shards via the transactions API.

