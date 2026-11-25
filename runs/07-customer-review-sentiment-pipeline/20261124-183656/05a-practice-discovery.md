# 5a. Best practices: prior knowledge against the public record: 07-customer-review-sentiment-pipeline

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**25 practices, 22 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 1 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 3 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 19 | Memory and documentation line up. |
| Found in public sources only | 2 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

## Where public sources contradict the model

### P02: For new Python async code on Azure DocumentDB prefer PyMongo's AsyncMongoClient (from pymongo import AsyncMongoClient) rather than Motor; Motor is deprecated and PyMongo's async API is the supported path.

- **The model believed:** Use the async Motor driver with Beanie: create a motor.motor_asyncio.AsyncIOMotorClient(DOCUMENTDB_URI, tls=True, tlsAllowInvalidCertificates=False, maxPoolSize=100, minPoolSize=0) and pass its database to beanie.init_beanie(...). (knowledge of `mongodb`)
- **The source says:** For new Python async code on Azure DocumentDB prefer PyMongo's AsyncMongoClient (from pymongo import AsyncMongoClient) rather than Motor; Motor is deprecated and PyMongo's async API is the supported path.
- **Source:** [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md)

## Known to the model, with no public source for this service

| Id | Practice | Knowledge of | Searches tried |
|---|---|---|---|
| P12 | Limit concurrency to external APIs (OpenAI) and the database (by batching DB writes) so the pipeline is resilient to rate limits and doesn't overwhelm the DB; coordinate rate limiting and batching in your worker design. | general | searches: "Azure DocumentDB OpenAI rate limit concurrent OpenAI calls"; "DocumentDB pipeline OpenAI concurrency semaphore" |
| P20 | When using an ODM (Beanie/Pydantic), declare explicit Pydantic field types for embeddings and scores and create indexes at model/migration time (or via create_index) rather than relying on implicit typing. | general | searches: "Beanie index create_index beanie Azure DocumentDB"; loaded skills: documentdb-driver, documentdb-indexing |
| P21 | Instrument pipeline metrics (processing latency, OpenAI error rate, DB write latency) and use observability tools (Log Analytics, Azure Monitor); consider distributed tracing but the public guidance focuses on logs/metrics and alerting. | general | searches: "Azure DocumentDB monitoring OpenTelemetry metrics"; examined documentdb-monitoring |

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Read the cluster connection URI from an environment variable (e.g., DOCUMENTDB_URI) at runtime and never commit credentials; ship a .env.example or config template with placeholders instead of real secrets. | authentication and secrets | prior_knowledge_confirmed | documentdb-local-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md | documentdb-local-deployment | yes |
| P02 | For new Python async code on Azure DocumentDB prefer PyMongo's AsyncMongoClient (from pymongo import AsyncMongoClient) rather than Motor; Motor is deprecated and PyMongo's async API is the supported path. | connection handling | prior_knowledge_contradicted | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P03 | Create and use a dedicated least-privilege database user for applications (or prefer Microsoft Entra ID / managed identity + RBAC) instead of the cluster admin account, and rotate credentials or use Key Vault-managed secrets. | authentication and secrets | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P04 | Always use TLS for connections to Azure DocumentDB (tls=true) and do not disable certificate validation in production; prefer SCRAM-SHA-256 for authentication. | security | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P05 | Enable driver-level retryable reads/writes (retryReads/retryWrites) and implement application-level exponential backoff for transient network or rate-limit (429) errors; make upserts idempotent using $setOnInsert where appropriate. | retries | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P06 | Keep each document well under the 16 MB BSON limit (plan for future growth) and split very large fields (e.g., very long text or large embeddings) into a side collection keyed by the document _id if necessary. | data modeling | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P07 | Design a compound index following the ESR rule (Equality → Sort → Range) to support aggregation summaries (e.g., { product_id: 1, sentiment_label: 1 }) so group/sort operations avoid blocking in-memory sorts. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P08 | Index array fields (tags) as multikey indexes for tag queries and add a descending index on created_at to accelerate queries for recent documents. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P09 | Store embeddings as numeric arrays and create a vector index (cosmosSearch) with the correct similarity (e.g., COS for cosine); ensure index dimensions match your embedding model. | vector search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | yes |
| P10 | For production-scale vector work prefer DiskANN (or HNSW for smaller collections) and explicitly set index parameters (dimensions, similarity, maxDegree, lBuild) and tune query-time lSearch to trade recall vs latency; rebuild indexes when embedding dimensionality or model changes. | vector search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | yes |
| P11 | Use bulk/batched operations (bulkWrite, replaceOne with upsert, or provider bulk APIs) for large imports or enrichment pipelines to reduce round trips and manage RU consumption; tune batch sizes and thread counts. | provisioning and performance | prior_knowledge_confirmed | Manage a document in Azure Cosmos DB for MongoDB using JavaScript (public_doc) | https://learn.microsoft.com/azure/cosmos-db/mongodb/how-to-javascript-manage-documents#update-a-document | Azure DocumentDB MongoDB bulk write bulkWrite upsert best practices | yes |
| P12 | Limit concurrency to external APIs (OpenAI) and the database (by batching DB writes) so the pipeline is resilient to rate limits and doesn't overwhelm the DB; coordinate rate limiting and batching in your worker design. | openai integration | prior_knowledge_only | - (prior_knowledge) | **none** | searches: "Azure DocumentDB OpenAI rate limit concurrent OpenAI calls"; "DocumentDB pipeline OpenAI concurrency semaphore" | yes |
| P13 | Implement the aggregation summary with an aggregation pipeline using $group by product_id and sentiment_label (or bucketed sentiment scores) and run explain() on the aggregation to verify the query plan and index usage. | queries | prior_knowledge_confirmed | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | documentdb-query-optimizer | yes |
| P14 | Always run explain("executionStats") on expensive queries and use the cluster's slow-query logs / profiler and Azure Monitor diagnostic settings to detect missing indexes or hot queries before increasing throughput. | monitoring and tuning | prior_knowledge_confirmed | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | documentdb-query-optimizer | yes |
| P15 | Scale up compute or use autoscale during heavy bulk indexing or large imports and scale down afterwards to reduce cost; prepare capacity ahead of large write operations. | provisioning | prior_knowledge_confirmed | Optimize write performance in Azure Cosmos DB for MongoDB (public_doc) | https://learn.microsoft.com/azure/cosmos-db/mongodb/optimize-write-performance | Azure DocumentDB bulk/indexing scale up during migration | yes |
| P16 | Make reprocessing idempotent by using a stable _id (external review id) and upsert semantics; use $setOnInsert for fields that must remain only on first insert and $set for subsequent updates. | data integrity | prior_knowledge_confirmed | $setOnInsert (public_doc) | https://learn.microsoft.com/documentdb/query/operators/field-update/$setoninsert#examples | $setOnInsert Azure DocumentDB | yes |
| P17 | Enable diagnostic settings, collect slow-query logs into Log Analytics, and create alerts on CPU, memory, IOPS, storage, connection count saturation, and throttling (429) so you can react before user-visible failures. | monitoring and operations | prior_knowledge_confirmed | documentdb-monitoring (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md | documentdb-monitoring | yes |
| P18 | Prefer idempotent single-document upserts over multi-document transactions for pipelines; multi-document transactions exist but have limitations and performance costs, especially across sharded collections. | transactions and concurrency | prior_knowledge_confirmed | Use Multi-document transactions in Azure Cosmos DB for MongoDB (public_doc) | https://learn.microsoft.com/azure/cosmos-db/mongodb/use-multi-document-transactions | Use Multi-document transactions in Azure Cosmos DB for MongoDB | yes |
| P19 | Rely on the cluster's managed continuous backups and test restore procedures regularly; automatic backups are retained (35 days for active clusters) but maintain export snapshots for critical training/experimental datasets. | backups and DR | prior_knowledge_confirmed | documentdb-high-availability (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/high-availability/SKILL.md | documentdb-high-availability | yes |
| P20 | When using an ODM (Beanie/Pydantic), declare explicit Pydantic field types for embeddings and scores and create indexes at model/migration time (or via create_index) rather than relying on implicit typing. | beanie_async | prior_knowledge_only | - (prior_knowledge) | **none** | searches: "Beanie index create_index beanie Azure DocumentDB"; loaded skills: documentdb-driver, documentdb-indexing | yes |
| P21 | Instrument pipeline metrics (processing latency, OpenAI error rate, DB write latency) and use observability tools (Log Analytics, Azure Monitor); consider distributed tracing but the public guidance focuses on logs/metrics and alerting. | monitoring and observability | prior_knowledge_only | - (prior_knowledge) | **none** | searches: "Azure DocumentDB monitoring OpenTelemetry metrics"; examined documentdb-monitoring | yes |
| P22 | Shard only when a collection's size or throughput exceeds one physical shard's budget; choose a shard key based on workload (read-heavy → localize to a frequent filter; write-heavy → high-cardinality hashed key) and diagnose hot partitions before changing keys. | provisioning and scaling | prior_knowledge_confirmed | documentdb-sharding (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/sharding/SKILL.md | documentdb-sharding | no |
| P23 | Protect PII: anonymize or remove personal identifiers, and use encryption where appropriate; Azure DocumentDB supports customer-managed keys (CMK) for at-rest encryption and client-side / field-level encryption (Always Encrypted) for sensitive fields. | security and compliance | prior_knowledge_confirmed | Data encryption in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/database-encryption-at-rest | Azure DocumentDB data encryption and Always Encrypted guidance | yes |
| P24 | Prefer DocumentDB's built-in full-text search and create search indexes with createSearchIndexes and query via the $search aggregation stage (use BM25, add fuzzy/phrase options and custom analyzers as needed) rather than relying on community $text. | full-text search | found_in_public_source | documentdb-full-text-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/full-text-search/SKILL.md | documentdb-full-text-search | yes |
| P25 | Create vector indexes with matching embedding 'dimensions' and 'similarity' (mismatches cause silently incorrect results), and rebuild indexes if you change the embedding model or similarity metric. | vector search | found_in_public_source | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | yes |

## Searches that returned nothing useful

- Azure DocumentDB OpenAI concurrency semaphore
- Azure DocumentDB sample guidance about Beanie ODM field annotations
- Azure DocumentDB pipeline OpenTelemetry instrumentation guidance specific to MongoDB API

## Notes

I loaded the DocumentDB skills and Microsoft Learn docs to find public guidance for connection patterns, security, indexing, vector search, sharding, monitoring, backup, transactions, and bulk operations. Many prior beliefs (K01, K03, K04, K05, K07, K08, K09, K10, K11, K13, K14, K15, K16, K17, K18, K19, K20, K23, K24) are confirmed by DocumentDB public docs or the installed skills; K02 (Motor) is contradicted by the documentdb-connection skill which directs Python async users to PyMongo's AsyncMongoClient; K06, K12, K21, and K22 are prior-knowledge-only (I could not find an Azure DocumentDB page that prescribes the exact Beanie/Pydantic field list, application-level OpenAI concurrency pattern, or specific OpenTelemetry instrumentation). Relevant public URLs were used where available (see individual entries).

Prior beliefs the discovery step did not classify: K06. See 05a-prior-beliefs.json.

