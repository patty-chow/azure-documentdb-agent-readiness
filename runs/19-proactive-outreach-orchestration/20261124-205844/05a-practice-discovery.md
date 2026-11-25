# 5a. Best practices: prior knowledge against the public record: 19-proactive-outreach-orchestration

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**21 practices, 21 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 1 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 0 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 20 | Memory and documentation line up. |
| Found in public sources only | 0 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

## Where public sources contradict the model

### P19: Persist change-stream consumer progress (resume tokens) durably so consumers can resume exactly where they left off, but do not rely on setting client-side writeConcern: Azure DocumentDB handles replication quorum for writes and client-specified writeConcern is ignored.

- **The model believed:** Persist change-stream consumer progress (resume tokens, last processed event id/time) in a small, durable collection with a majority writeConcern so a crash or restart can resume exactly where it left off. (knowledge of `mongodb`)
- **The source says:** Persist change-stream consumer progress (resume tokens) durably so consumers can resume exactly where they left off, but do not rely on setting client-side writeConcern: Azure DocumentDB handles replication quorum for writes and client-specified writeConcern is ignored.
- **Source:** [Change streams in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/change-streams#resume-a-change-stream)

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Create a single, process-wide MongoClient and reuse it (singleton) rather than creating a new client per request or per change-stream event. | connection | prior_knowledge_confirmed | documentdb-driver (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md | load_skill documentdb-driver | yes |
| P02 | Never store production DocumentDB credentials in code or the repo; read the connection string from environment variables and use a secrets store (for example, Azure Key Vault) in deployments, keeping only a .env.example with placeholders in source control. | secrets | prior_knowledge_confirmed | documentdb-local-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md | load_skill documentdb-local-deployment | yes |
| P03 | Require TLS for all connections to Azure DocumentDB and do not disable certificate validation in production; install/point to a CA bundle in restricted runtimes instead of relaxing verification. | security | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | load_skill documentdb-security | yes |
| P04 | Tune MongoClient connection options (maxPoolSize, minPoolSize, connectTimeoutMS, socketTimeoutMS, maxIdleTimeMS) to your deployment pattern (serverless vs long-running) rather than relying on driver defaults. | connection | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | load_skill documentdb-connection | yes |
| P05 | Enable driver retryable reads/writes where supported and implement application-level retries with exponential backoff for idempotent operations while avoiding infinite retries for non-idempotent side effects. | retries | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | load_skill documentdb-connection | yes |
| P06 | Persist change-stream resume tokens (the _id from change events) to durable storage and resume streams using resumeAfter or startAtOperationTime to avoid missing or duplicating events after restarts. | change_streams | prior_knowledge_confirmed | Change streams in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/change-streams#resume-a-change-stream | Azure DocumentDB change streams resume token resumeAfter startAtOperationTime | yes |
| P07 | Handle change-stream errors explicitly: persist resume progress frequently, attempt resumes for resumable/transient errors, and provide a safe recovery plan (for non-resumable errors) such as replaying a bounded time window; be aware of limitations such as topology changes and retention windows. | change_streams | prior_knowledge_confirmed | Change streams in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/change-streams | Azure DocumentDB change streams errors resumability limitations | yes |
| P08 | Choose a shard/partition key with high cardinality and even distribution (for write-heavy workloads) or the most-frequent query filter (for read-heavy workloads); default to single-shard unless collection size or throughput exceeds one physical shard's budget. | provisioning | prior_knowledge_confirmed | documentdb-sharding (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/sharding/SKILL.md | load_skill documentdb-sharding | yes |
| P09 | Create indexes for fields used in query predicates and sort keys and verify index usage with explain(); prefer targeted indexes rather than indexing every path by default. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | load_skill documentdb-indexing | yes |
| P10 | Design compound indexes following the ESR (Equality → Sort → Range) rule so common query patterns are served by a single compound index rather than multiple single-field indexes. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | load_skill documentdb-indexing | yes |
| P11 | Use projection to return only the fields needed for a query (for example exclude large payloads or embeddings) to reduce network transfer and RU/IO consumption. | queries | prior_knowledge_confirmed | Understand request units consumption in Azure Cosmos DB (public_doc) | https://learn.microsoft.com/azure/cosmos-db/understand-request-unit-consumption#key-takeaways-and-best-practices | Azure DocumentDB projection reduce RU network projection | yes |
| P12 | Persist embeddings in a dedicated field and create a vector index with explicit parameters (dimensions, similarity, and index-type-specific tunables such as lBuild/lSearch/maxDegree or numLists) and tune both build- and search-time parameters for your accuracy/latency tradeoff. | vector_search | prior_knowledge_confirmed | Integrated vector store in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/vector-search#perform-vector-similarity-search | Azure DocumentDB vector index create DiskANN HNSW IVF cosmosSearch | no |
| P13 | Normalize embedding vectors consistently at ingest (for example L2-normalize for COSine similarity) and store the embedding model name and dimensions with each document so you can detect drift and re-embed when models change. | vector_search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | load_skill documentdb-vector-search | no |
| P14 | For temporary or retention-based logs use a TTL index on a timestamp field to automatically expire old records rather than relying on manual deletes. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | load_skill documentdb-indexing | yes |
| P15 | Make seeding and index-creation scripts idempotent: check for collection existence, use createIndexes (idempotent), or catch duplicate-key errors so running the script multiple times is safe. | provisioning | prior_knowledge_confirmed | documentdb-local-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md | load_skill documentdb-local-deployment | yes |
| P16 | Use multi-operation transactions only when you need atomicity across documents, keep transactions small and short-lived, and be prepared to retry transient transaction errors with exponential backoff. | data_modeling | prior_knowledge_confirmed | Group multiple operations in transactions in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/how-to-transactions#create-a-transaction | Azure DocumentDB transactions retry backoff | yes |
| P17 | Instrument and monitor cluster and query metrics (connections, pool usage, CPU, memory, IOPS, storage, slow query traces) and alert on leading indicators so you can scale or investigate before users are impacted. | observability | prior_knowledge_confirmed | documentdb-monitoring (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md | load_skill documentdb-monitoring | yes |
| P18 | Implement idempotency for external side effects (for example sending outreach): store and check an idempotency key such as event id or outreach_id in outreach_logs to avoid duplicate sends on replay. | data_modeling | prior_knowledge_confirmed | Recommendations for handling transient faults (public_doc) | https://learn.microsoft.com/azure/well-architected/design-guides/handle-transient-faults#implementing-retries | Azure recommendations retries idempotency guidance | yes |
| P19 | Persist change-stream consumer progress (resume tokens) durably so consumers can resume exactly where they left off, but do not rely on setting client-side writeConcern: Azure DocumentDB handles replication quorum for writes and client-specified writeConcern is ignored. | change_streams | prior_knowledge_contradicted | Change streams in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/change-streams#resume-a-change-stream | Azure DocumentDB change streams resume token writeConcern behavior | yes |
| P20 | Avoid unbounded aggregations or map-reduce in change-stream consumers; process events in bounded batches, apply backpressure, and limit concurrency to avoid exhausting cluster throughput or overwhelming the database. | performance | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | load_skill documentdb-connection | yes |
| P21 | Do not log full PII or credentials; redact or avoid persisting sensitive customer attributes in logs or persisted traces to meet security and compliance requirements. | security | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | load_skill documentdb-security | yes |

## Searches that returned nothing useful

- Azure DocumentDB vector index best practices for small demos (query returned vector docs but vector-specific how-to samples found) -- no missing guidance
- Azure DocumentDB guidance explicitly recommending client-set majority writeConcern for resume-token persistence (search found service-managed quorum behavior instead)
- Azure DocumentDB 'maxPoolSize recommended exact value' (search returns scenario-based ranges rather than a single global default)

## Notes

I inspected the app source to identify the areas it touches (connection handling, change-streams, seeding/indexing, message sending, logs) then used the installed DocumentDB skills and Microsoft Learn docs to discover public guidance. Each prior belief K01–K21 was checked against the public record: most were confirmed by DocumentDB-specific installed skills or Microsoft Learn pages; K19 (client-enforced majority writeConcern) was contradicted by Azure DocumentDB documentation which states the service handles quorum and client writeConcern may be ignored.

