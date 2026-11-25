# 5a. Best practices: prior knowledge against the public record: 11-market-news-sentiment-orchestration

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**25 practices, 0 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 0 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 19 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 5 | Memory and documentation line up. |
| Found in public sources only | 1 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

> **No documentation search server answered.** In this report, "not found" means "not searchable from this machine", not "not public". Fix the server in `mcp.json` and re-run the audit.

| Source | Reachable | Detail |
|---|---|---|
| Installed agent skills | 0 | 0 have a public address |

## Known to the model, with no public source for this service

| Id | Practice | Knowledge of | Searches tried |
|---|---|---|---|
| P02 | When connecting from Node.js, ensure driver connection options (parser/topology and TLS settings) are explicitly configured according to the platform's best practices. | mongodb | Node.js MongoDB driver useUnifiedTopology azure documentdb; azure documentdb node tls enforce; azure documentdb mongodb driver connection options |
| P03 | Enable TLS/SSL and certificate validation for client connections and do not disable certificate validation in production. | azure_cosmos_db | azure documentdb tls enforce; azure documentdb mongodb tls certificate validation; mongodb driver tls azure documentdb |
| P05 | Enable driver retryable writes and implement application-level retries with exponential backoff for transient errors and throttling. | mongodb | azure documentdb retryable writes node.js; mongodb driver retryWrites azure documentdb; azure documentdb transient error handling |
| P06 | Choose an appropriate partitioning/sharding strategy (partition key) to avoid hot partitions and keep related queries efficient. | azure_cosmos_db | azure documentdb partition key best practices; azure documentdb sharding choose partition key; azure documentdb mongodb partitioning |
| P07 | Provision throughput appropriately and monitor RU/s consumption; enable autoscale where supported and alert on throttling (HTTP 429). | azure_cosmos_db | azure documentdb ru provisioning autoscale throttling 429; azure documentdb monitoring RU |
| P08 | Consider using TTL (expireAfterSeconds) on ephemeral article documents so old headlines are removed automatically instead of accumulating indefinitely. | azure_cosmos_db | azure documentdb ttl index expireAfterSeconds mongodb azure documentdb ttl on collection |
| P11 | Normalize vectors for cosine similarity and validate vector dimensionality at ingest time to avoid mismatched-dimension inserts. | general | azure documentdb vector embeddings cosine similarity normalize; azure documentdb mongodb embedding normalization best practices |
| P13 | Keep documents reasonably small and avoid shipping embeddings unless needed (use projection in queries to exclude embedding fields when not required). | mongodb | azure documentdb projection exclude embedding; mongodb projection best practices embeddings |
| P14 | Avoid cross-partition multi-document transactions by designing operations to be scoped to a single partition key whenever transactional guarantees are required. | azure_cosmos_db | azure documentdb transactions cross-partition; azure documentdb mongodb transactions restrictions |
| P15 | Handle HTTP 429/RequestRateTooLarge responses by honoring Retry-After and implementing exponential backoff with jitter; monitor and log 429 spikes. | azure_cosmos_db | azure documentdb 429 Retry-After backoff; azure documentdb throttling guidance |
| P16 | Use explain() to verify queries use indexes and avoid full-collection scans in production. | mongodb | azure documentdb explain query index use; mongodb explain() azure documentdb |
| P17 | Prefer managed identity or Azure Key Vault for long-term deployments rather than embedding primary keys or connection strings directly in environment variables when running in Azure. | azure_cosmos_db | azure documentdb managed identity key vault connection string rotation; azure key vault mongodb connection string |
| P18 | Enable driver and server metrics (connection pool, RU consumption, latency, 429s) and create alerts for throttling, high latency, or connection churn. | azure_cosmos_db | azure documentdb monitoring connection pool ru metrics; azure monitor documentdb mongodb metrics |
| P19 | Protect server endpoints that trigger scrapes or runs: require authentication/authorization, rate-limit requests, validate inputs and never expose admin DB endpoints or credentials. | general | secure express endpoint trigger job documentdb; protect webhook run endpoint authentication rate limiting |
| P20 | Create a compound index tailored to typical alert lookups (for example {ticker:1, active:1}) so watchlist queries are efficient rather than scanning the whole collection. | mongodb | azure documentdb compound index watchlist ticker active; mongodb compound index alerting |
| P22 | When doing similarity search, filter by cheap predicates (ticker or date range) before running nearest-neighbor vector search to reduce cost and RU consumption. | general | azure documentdb vector search filter before knn; vector search prefilter by metadata azure documentdb |
| P23 | Rely on server-side encryption for data at rest and in transit and consider client-side field-level encryption for sensitive fields containing PII or secrets. | azure_cosmos_db | azure documentdb encryption at rest client side field level encryption mongodb compatible |
| P24 | When ingesting at scale, use bulkWrite with reasonable batch sizes and backoff on failures rather than individual inserts to avoid RU saturation. | mongodb | mongodb bulkWrite azure documentdb best practices batching backoff; azure documentdb bulk ingest guidance |
| P25 | Prefer change streams or push-based mechanisms to trigger downstream alerting where available; if not, poll efficiently using a last-seen watermark on created_at. | mongodb | azure documentdb change streams support mongodb compatible; azure documentdb watch change stream alternatives |

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Read the DocumentDB connection string from a runtime secret (DOCUMENTDB_URI) and provide a .env.example placeholder instead of committing real credentials. | auth_and_secrets | prior_knowledge_confirmed | .env.example (local_file) | **none** | .env.example | yes |
| P02 | When connecting from Node.js, ensure driver connection options (parser/topology and TLS settings) are explicitly configured according to the platform's best practices. | connection_handling | prior_knowledge_only | - (prior_knowledge) | **none** | Node.js MongoDB driver useUnifiedTopology azure documentdb; azure documentdb node tls enforce; azure documentdb mongodb driver connection options | yes |
| P03 | Enable TLS/SSL and certificate validation for client connections and do not disable certificate validation in production. | connection_handling | prior_knowledge_only | - (prior_knowledge) | **none** | azure documentdb tls enforce; azure documentdb mongodb tls certificate validation; mongodb driver tls azure documentdb | yes |
| P04 | Reuse a single MongoClient instance across the application process instead of creating a new client per request (store it in module scope and return the same client). | connection_handling | prior_knowledge_confirmed | src/db.js (local_file) | **none** | src/db.js | yes |
| P05 | Enable driver retryable writes and implement application-level retries with exponential backoff for transient errors and throttling. | retries | prior_knowledge_only | - (prior_knowledge) | **none** | azure documentdb retryable writes node.js; mongodb driver retryWrites azure documentdb; azure documentdb transient error handling | yes |
| P06 | Choose an appropriate partitioning/sharding strategy (partition key) to avoid hot partitions and keep related queries efficient. | provisioning | prior_knowledge_only | - (prior_knowledge) | **none** | azure documentdb partition key best practices; azure documentdb sharding choose partition key; azure documentdb mongodb partitioning | no |
| P07 | Provision throughput appropriately and monitor RU/s consumption; enable autoscale where supported and alert on throttling (HTTP 429). | provisioning | prior_knowledge_only | - (prior_knowledge) | **none** | azure documentdb ru provisioning autoscale throttling 429; azure documentdb monitoring RU | no |
| P08 | Consider using TTL (expireAfterSeconds) on ephemeral article documents so old headlines are removed automatically instead of accumulating indefinitely. | data_modeling | prior_knowledge_only | - (prior_knowledge) | **none** | azure documentdb ttl index expireAfterSeconds mongodb azure documentdb ttl on collection | yes |
| P09 | Create explicit indexes for fields used in queries (text index on headline and a normal index on tickers are created by the sample seed script). | indexing | prior_knowledge_confirmed | scripts/seed.js (local_file) | **none** | scripts/seed.js | yes |
| P10 | Store vector embeddings in a dedicated fixed field (embedding) on the document when available and keep vector dimensionality consistent across documents. | vector_search | found_in_public_source | src/run.js and src/ai.js (local_file) | **none** | src/run.js; src/ai.js | yes |
| P11 | Normalize vectors for cosine similarity and validate vector dimensionality at ingest time to avoid mismatched-dimension inserts. | vector_search | prior_knowledge_only | - (prior_knowledge) | **none** | azure documentdb vector embeddings cosine similarity normalize; azure documentdb mongodb embedding normalization best practices | yes |
| P12 | Use upserts with a dedupe key (e.g., ticker or article id) to make ingestion idempotent; seed script uses updateOne with upsert:true for watchlist entries. | data_modeling | prior_knowledge_confirmed | scripts/seed.js (local_file) | **none** | scripts/seed.js | yes |
| P13 | Keep documents reasonably small and avoid shipping embeddings unless needed (use projection in queries to exclude embedding fields when not required). | data_modeling | prior_knowledge_only | - (prior_knowledge) | **none** | azure documentdb projection exclude embedding; mongodb projection best practices embeddings | yes |
| P14 | Avoid cross-partition multi-document transactions by designing operations to be scoped to a single partition key whenever transactional guarantees are required. | transactions | prior_knowledge_only | - (prior_knowledge) | **none** | azure documentdb transactions cross-partition; azure documentdb mongodb transactions restrictions | no |
| P15 | Handle HTTP 429/RequestRateTooLarge responses by honoring Retry-After and implementing exponential backoff with jitter; monitor and log 429 spikes. | retries | prior_knowledge_only | - (prior_knowledge) | **none** | azure documentdb 429 Retry-After backoff; azure documentdb throttling guidance | yes |
| P16 | Use explain() to verify queries use indexes and avoid full-collection scans in production. | queries | prior_knowledge_only | - (prior_knowledge) | **none** | azure documentdb explain query index use; mongodb explain() azure documentdb | yes |
| P17 | Prefer managed identity or Azure Key Vault for long-term deployments rather than embedding primary keys or connection strings directly in environment variables when running in Azure. | auth_and_secrets | prior_knowledge_only | - (prior_knowledge) | **none** | azure documentdb managed identity key vault connection string rotation; azure key vault mongodb connection string | no |
| P18 | Enable driver and server metrics (connection pool, RU consumption, latency, 429s) and create alerts for throttling, high latency, or connection churn. | logging_monitoring | prior_knowledge_only | - (prior_knowledge) | **none** | azure documentdb monitoring connection pool ru metrics; azure monitor documentdb mongodb metrics | yes |
| P19 | Protect server endpoints that trigger scrapes or runs: require authentication/authorization, rate-limit requests, validate inputs and never expose admin DB endpoints or credentials. | server_endpoints | prior_knowledge_only | - (prior_knowledge) | **none** | secure express endpoint trigger job documentdb; protect webhook run endpoint authentication rate limiting | yes |
| P20 | Create a compound index tailored to typical alert lookups (for example {ticker:1, active:1}) so watchlist queries are efficient rather than scanning the whole collection. | indexing | prior_knowledge_only | - (prior_knowledge) | **none** | azure documentdb compound index watchlist ticker active; mongodb compound index alerting | yes |
| P21 | Use idempotent seed and verification scripts that create-if-not-exists and are scoped to the sample_fintech_11 database (do not enumerate or modify other databases on the cluster). | scripts | prior_knowledge_confirmed | scripts/seed.js and scripts/verify.js (local_file) | **none** | scripts/seed.js; scripts/verify.js | yes |
| P22 | When doing similarity search, filter by cheap predicates (ticker or date range) before running nearest-neighbor vector search to reduce cost and RU consumption. | vector_search | prior_knowledge_only | - (prior_knowledge) | **none** | azure documentdb vector search filter before knn; vector search prefilter by metadata azure documentdb | no |
| P23 | Rely on server-side encryption for data at rest and in transit and consider client-side field-level encryption for sensitive fields containing PII or secrets. | security | prior_knowledge_only | - (prior_knowledge) | **none** | azure documentdb encryption at rest client side field level encryption mongodb compatible | no |
| P24 | When ingesting at scale, use bulkWrite with reasonable batch sizes and backoff on failures rather than individual inserts to avoid RU saturation. | provisioning | prior_knowledge_only | - (prior_knowledge) | **none** | mongodb bulkWrite azure documentdb best practices batching backoff; azure documentdb bulk ingest guidance | yes |
| P25 | Prefer change streams or push-based mechanisms to trigger downstream alerting where available; if not, poll efficiently using a last-seen watermark on created_at. | queries | prior_knowledge_only | - (prior_knowledge) | **none** | azure documentdb change streams support mongodb compatible; azure documentdb watch change stream alternatives | yes |

## Searches that returned nothing useful

- Azure DocumentDB vector index HNSW DiskANN best practices
- Azure DocumentDB (MongoDB) Node.js driver useUnifiedTopology useNewUrlParser tls options
- Azure DocumentDB enforce TLS certificate validation mongodb driver
- Azure DocumentDB RU/s autoscale guidance for MongoDB-compatible clusters
- Azure DocumentDB recommend partition key for time-series or ticker data
- Azure DocumentDB vector embedding normalization cosine similarity guidance
- Azure DocumentDB explain() usage and explain plan docs for MongoDB-compatible API
- Azure DocumentDB change streams support for MongoDB wire protocol
- Azure DocumentDB handling 429 Retry-After guidance for MongoDB-compatible clusters
- Azure DocumentDB create vector index via MongoDB driver HNSW tuning parameters

## Notes

Repository inspection (local files) provided evidence for several operational practices used by the sample app (env var for DOCUMENTDB_URI, single MongoClient reuse, seed script upserts and indexes, storing embeddings in an 'embedding' field, idempotent seed/verify scripts). No external documentation servers or installed skills were reachable in this run, so for prior beliefs where no local-file evidence exists I recorded them as prior_knowledge_only and listed the search queries that would have been tried.

Prior beliefs the discovery step did not classify: K10. See 05a-prior-beliefs.json.

