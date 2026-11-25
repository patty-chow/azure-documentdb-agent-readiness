# 5a. Best practices: prior knowledge against the public record: 07-customer-review-sentiment-pipeline

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**28 practices, 25 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 2 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 3 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 20 | Memory and documentation line up. |
| Found in public sources only | 3 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

## Where public sources contradict the model

### P01: For Python apps prefer one process-global AsyncMongoClient (PyMongo's AsyncMongoClient) reused across the app lifecycle rather than creating a new Motor AsyncIOMotorClient per request; initialize once and close on shutdown.

- **The model believed:** Read the cluster connection string from an environment variable (DOCUMENTDB_URI) and never hard-code it; create a single AsyncIOMotorClient per process and reuse it for all Beanie/ODM operations (close it on shutdown). (knowledge of `general`)
- **The source says:** For Python apps prefer one process-global AsyncMongoClient (PyMongo's AsyncMongoClient) reused across the app lifecycle rather than creating a new Motor AsyncIOMotorClient per request; initialize once and close on shutdown.
- **Source:** [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md)

### P08: Azure DocumentDB enforces the MongoDB BSON document size limit (16 MB); keep documents well under 16 MB and spill large fields to a side collection or external blob storage.

- **The model believed:** Keep document sizes small (well below 2 MB); store large assets externally (blob storage) and keep references in the document to reduce RU cost and avoid item-size limits. (knowledge of `azure_cosmos_db`)
- **The source says:** Azure DocumentDB enforces the MongoDB BSON document size limit (16 MB); keep documents well under 16 MB and spill large fields to a side collection or external blob storage.
- **Source:** [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md)

## Known to the model, with no public source for this service

| Id | Practice | Knowledge of | Searches tried |
|---|---|---|---|
| P20 | Limit concurrency when calling external services (OpenAI) using an async semaphore or similar rate-limiter to bound simultaneous requests so you don't overwhelm external APIs or your pipeline. | general | Azure DocumentDB limit concurrency external services semaphore OpenAI best practices |
| P27 | Prefer extracting structured tags/key themes and indexing those tag fields for fast filtering/aggregation rather than relying solely on expensive free-text indexes when your queries are structured, but no authoritative Azure DocumentDB guidance explicitly mandates this trade-off. | general | Azure DocumentDB text search prefer structured tags index instead of text search |
| P28 | Test pipelines end-to-end with a mockable OpenAI implementation in CI (DevProxy / local LLM / test doubles) so CI runs do not require real API keys and real external calls. | general | Azure DocumentDB pipeline testing mock OpenAI CI |

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | For Python apps prefer one process-global AsyncMongoClient (PyMongo's AsyncMongoClient) reused across the app lifecycle rather than creating a new Motor AsyncIOMotorClient per request; initialize once and close on shutdown. | connection_handling | prior_knowledge_contradicted | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P02 | Read the cluster connection string and other secrets from environment variables or a secure secret store (Key Vault) and provide a `.env.example` placeholder for local/dev only; never commit real secrets to source control. | authentication_and_secrets | prior_knowledge_confirmed | Tutorial: Connect a Node.js web app with Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/tutorial-nodejs-web-app#test-the-mern-application-with-the-azure-documentdb-cluster | Azure DocumentDB connection string environment variable best practices | yes |
| P03 | Always connect with TLS (tls=true) and do not disable certificate verification in production; fix CA bundle/SNI issues rather than allowing invalid certificates. | connection_handling | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P04 | Tune Mongo client pool and timeout parameters for the deployment model (serverless: small pools, short maxIdleTimeMS; long-running servers: larger maxPoolSize and longer maxIdleTimeMS) and set serverSelectionTimeoutMS/socketTimeoutMS to reasonable values for your environment. | connection_handling | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P05 | Avoid logging or printing full connection strings and API keys; use Key Vault/managed identities and secret-scanning tools, and keep `.env` out of source control. | authentication_and_secrets | prior_knowledge_confirmed | Best practices for protecting secrets (public_doc) | https://learn.microsoft.com/azure/security/fundamentals/secrets-best-practices#secret-discovery-and-prevention | Azure DocumentDB connection string environment variable best practices | yes |
| P06 | Use a durable unique key (e.g., review_id or _id) and create a unique index on it so upserts are idempotent. | data_modeling | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing -> index-single-field.md | yes |
| P07 | Model sentiment as a numeric field (e.g., float) and store tags as a bounded array of strings, and be aware multikey indexes create one index entry per array element so index tags selectively and keep arrays bounded or move to a child collection. | data_modeling | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing -> index-multikey-arrays.md | yes |
| P08 | Azure DocumentDB enforces the MongoDB BSON document size limit (16 MB); keep documents well under 16 MB and spill large fields to a side collection or external blob storage. | data_modeling | prior_knowledge_contradicted | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling -> model-16mb-limit.md | yes |
| P09 | Create indexes to support aggregation/reporting: at minimum index product_id and create a compound index on (product_id, sentiment) when grouping by product and sentiment to accelerate aggregation pipelines. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing -> index-compound-esr.md | yes |
| P10 | Avoid unnecessary indexes: maintain a modest index budget (e.g., 5–15 indexes per collection), review index usage with $indexStats, and prefer partial/sparse indexes to reduce write and storage cost. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing -> index-count-budget.md | yes |
| P11 | When creating a vector index declare the field dimensions and index kind (vector-diskann, vector-hnsw or vector-ivf) and choose the similarity metric (COS/IP/L2); prefer DiskANN for large production workloads. | vector_search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search -> vector-choose-index-type.md | no |
| P12 | Normalize embeddings at ingestion when using cosine similarity and store embedding model name and dimensions with the vector to detect model drift and support re-embedding. | vector_search | found_in_public_source | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search -> vector-normalize-embeddings.md | no |
| P13 | When running vector KNN queries tune query-time parameters (k, lSearch/efSearch), combine vector retrieval with pre-filters, and project only required fields and limit returned neighbors to reduce RU/latency. | vector_search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search -> vector-knn-query.md | no |
| P14 | Implement application retries with exponential backoff for transient errors (network blips, 429 throttling, transient 5xx), and honour Retry-After headers when present. | retries | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection -> retry code sample | yes |
| P15 | Azure DocumentDB does not support driver-level retryable writes (connection strings often set retryWrites=false); do not rely on automatic retryable-write semantics—implement safe application-level retries instead. | connection_handling | found_in_public_source | documentdb-azure-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/azure-deployment/SKILL.md | documentdb-azure-deployment | yes |
| P16 | Provision throughput by choosing appropriate compute tier and storage (use autoscale or pick a tier sized for peak ingestion/aggregation); monitor RU consumption and scale or change tier proactively. | provisioning | prior_knowledge_confirmed | documentdb-azure-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/azure-deployment/SKILL.md | documentdb-azure-deployment | yes |
| P17 | Write aggregation pipelines to be RU-efficient: $match early, $project early, avoid $lookup where possible, and design $group on indexed fields; test RU cost with explain and adjust. | queries | prior_knowledge_confirmed | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | documentdb-query-optimizer | yes |
| P18 | Use pagination and batching (cursor + limit / batchSize) for reads to avoid scanning large collections in a single request; prefer cursor-based paging for large datasets. | queries | prior_knowledge_confirmed | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | documentdb-query-optimizer | yes |
| P19 | Enable diagnostic settings and slow-query logging, collect metrics (RU, latency, requestCharge), and alert on CPU/memory/IOPS/storage/connection saturation via Azure Monitor / Log Analytics. | monitoring | prior_knowledge_confirmed | documentdb-monitoring (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md | documentdb-monitoring | yes |
| P20 | Limit concurrency when calling external services (OpenAI) using an async semaphore or similar rate-limiter to bound simultaneous requests so you don't overwhelm external APIs or your pipeline. | app_behavior | prior_knowledge_only | - (prior_knowledge) | **none** | Azure DocumentDB limit concurrency external services semaphore OpenAI best practices | yes |
| P21 | Design enrichment/upsert pipelines to be idempotent: use a stable key and upsert operations so re-processing a review does not create duplicates or partial writes. | app_behavior | prior_knowledge_confirmed | update (public_doc) | https://learn.microsoft.com/documentdb/query/commands/query-and-write/update#examples | Azure DocumentDB update / upsert examples | yes |
| P22 | Use JSON schema validation ($jsonSchema) on collections where supported to enforce required fields and types, or validate in the application layer before writes. | data_modeling | prior_knowledge_confirmed | $jsonSchema (public_doc) | https://learn.microsoft.com/documentdb/query/operators/evaluation-query/$jsonschema#supported-keywords | $jsonSchema Azure DocumentDB search | yes |
| P23 | When using Beanie ODM, declare indexes in the Document Settings and call init_beanie once at application startup so indexes are created at initialization rather than per-request. | indexing | prior_knowledge_confirmed | Quickstart: Connect Beanie to Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/quickstart-python-beanie | Quickstart: Connect Beanie to Azure DocumentDB | yes |
| P24 | Prefer DocumentDB's `createSearchIndexes` + `$search` (BM25) full-text search path with search indexes and custom analyzers rather than the community `$text` approach when you need advanced full-text features; use hybrid BM25+vector approaches for combined lexical/semantic retrieval. | indexing | found_in_public_source | documentdb-full-text-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/full-text-search/SKILL.md | documentdb-full-text-search | no |
| P25 | Pick a partition (shard) key with the right tradeoff: collocate related workloads (e.g., product-level data) on the same partition key for localized queries, choose high-cardinality keys for write-heavy workloads, and avoid hot/monotonic keys. | provisioning | prior_knowledge_confirmed | documentdb-sharding (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/sharding/SKILL.md | documentdb-sharding -> sharding-shard-key-selection.md | yes |
| P26 | Enable built-in backups and retention and test restore procedures; for critical data export periodic snapshots to durable storage as part of your backup plan. | provisioning | prior_knowledge_confirmed | documentdb-azure-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/azure-deployment/SKILL.md | documentdb-azure-deployment | yes |
| P27 | Prefer extracting structured tags/key themes and indexing those tag fields for fast filtering/aggregation rather than relying solely on expensive free-text indexes when your queries are structured, but no authoritative Azure DocumentDB guidance explicitly mandates this trade-off. | indexing | prior_knowledge_only | - (prior_knowledge) | **none** | Azure DocumentDB text search prefer structured tags index instead of text search | yes |
| P28 | Test pipelines end-to-end with a mockable OpenAI implementation in CI (DevProxy / local LLM / test doubles) so CI runs do not require real API keys and real external calls. | app_behavior | prior_knowledge_only | - (prior_knowledge) | **none** | Azure DocumentDB pipeline testing mock OpenAI CI | yes |

## Searches that returned nothing useful

- Azure DocumentDB limit concurrency external services semaphore OpenAI best practices
- Azure DocumentDB text search prefer structured tags index instead of text search
- Azure DocumentDB pipeline testing mock OpenAI CI

## Notes

Discovery used the installed DocumentDB skills (connection, indexing, vector-search, deployment, sharding, monitoring, query-optimizer, full-text-search, data-modeling, security) and Microsoft Learn docs. Entries mark where a model prior belief was confirmed, contradicted (notably K01: prefer PyMongo AsyncMongoClient over Motor; K08: 16 MB document limit not 2 MB), or had no Azure-DocumentDB-backed source (prior_knowledge_only). Practices about vector/full-text search are recorded but marked not relevant_to_this_app when the sample app does not use them.

