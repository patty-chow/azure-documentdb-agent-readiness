# 5a. Best practices: prior knowledge against the public record: 12-clv-prediction-pipeline

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**23 practices, 21 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 1 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 2 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 19 | Memory and documentation line up. |
| Found in public sources only | 1 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

## Where public sources contradict the model

### P22: Azure DocumentDB supports multi-document ACID transactions across collections and shards (the platform documents multi-document transactions as supported).

- **The model believed:** Avoid multi-document transactions spanning partitions for CLV writes; prefer single-partition updates or design for per-customer partitioning—if multi-document transactions are needed, validate whether the MongoDB API on this cluster supports them before relying on them. (knowledge of `mongodb`)
- **The source says:** Azure DocumentDB supports multi-document ACID transactions across collections and shards (the platform documents multi-document transactions as supported).
- **Source:** [Azure DocumentDB at a glance](https://learn.microsoft.com/azure/documentdb/at-a-glance#mongodb-compatibility)

## Known to the model, with no public source for this service

| Id | Practice | Knowledge of | Searches tried |
|---|---|---|---|
| P15 | Record LLM outputs and the LLM rationale in structured fields and an append-only audit or history subdocument rather than overwriting a single source-of-truth field so you can trace changes. | general | Azure DocumentDB record LLM outputs rationale append-only; DocumentDB audit LLM (no useful public guidance found) |
| P16 | Sanitize and validate any values produced by an LLM before writing them to the database (type checking, allowed enums, ranges) to avoid corrupting customer documents. | general | Azure DocumentDB sanitize LLM outputs validate before write; DocumentDB write validation guidance (no explicit service doc found) |

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Read the DocumentDB connection string and other secrets from environment variables (or a runtime-loaded .env) and never commit secrets into source control or logs. | secrets | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P02 | Create a single long-lived MongoClient per process (singleton) and reuse it for all requests; do not open a new client per request, and close it only on orderly shutdown. | connection | prior_knowledge_confirmed | documentdb-driver (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md | documentdb-driver | yes |
| P03 | Always use TLS for connections to Azure DocumentDB and do not disable certificate validation in production. | security | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P04 | Set sensible socket and server-selection timeouts (e.g., serverSelectionTimeoutMS and socketTimeoutMS) and tune them for your environment so client calls fail fast on unreachable clusters. | connection | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P05 | Implement automatic retries for transient errors (network blips, timeouts, and 429/RequestRateTooLarge) with exponential backoff and only retry idempotent operations. | retries | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P06 | Use batched/bulk write operations for large-scale updates; Azure DocumentDB supports batch write operations (note: a batch is a single request and there are documented limits such as maximum writes per batch). | performance | prior_knowledge_confirmed | Document size and batch write limits in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/max-document-size | Azure DocumentDB bulkWrite pymongo bulkWrite Azure DocumentDB bulk operations | yes |
| P07 | When updating fields on a customer document, use partial updates like $set (and upsert when appropriate) rather than replacing the entire document to avoid accidental data loss. | data_modeling | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P08 | Design your shard/partition key so related customer data and most writes for a single customer map to the same logical partition (e.g., customer_id) to keep updates atomic and efficient. | provisioning | prior_knowledge_confirmed | documentdb-sharding (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/sharding/SKILL.md | documentdb-sharding | yes |
| P09 | Create a compound index following the ESR rule (Equality → Sort → Range) for fields used together in aggregations (for example customer_id + order_date) to accelerate grouping and chronological queries. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P10 | For arrays you query or aggregate over (line items, product_ids), create appropriate multikey indexes and avoid unbounded arrays that would make indexes explode. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P11 | Only project (return) the fields required for the computation in aggregation pipelines to reduce RU consumption and network transfer. | queries | prior_knowledge_confirmed | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | documentdb-query-optimizer | yes |
| P12 | Keep aggregation pipelines concise and place $match stages early (preferably filtering on the partition/shard key) to reduce scanned records and RU costs. | queries | prior_knowledge_confirmed | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | documentdb-query-optimizer | yes |
| P13 | When using the service's vector-search features, explicitly set and validate index parameters (dimensions, similarity metric, algorithm choice such as DiskANN/HNSW/IVF) and store the model and dimensionality with the vectors. | vector_search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | no |
| P14 | Avoid storing very large documents (stay well under the 16 MB BSON limit); split very large blobs into object storage or side collections and reference them instead. | data_modeling | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P15 | Record LLM outputs and the LLM rationale in structured fields and an append-only audit or history subdocument rather than overwriting a single source-of-truth field so you can trace changes. | data_modeling | prior_knowledge_only | - (prior_knowledge) | **none** | Azure DocumentDB record LLM outputs rationale append-only; DocumentDB audit LLM (no useful public guidance found) | yes |
| P16 | Sanitize and validate any values produced by an LLM before writing them to the database (type checking, allowed enums, ranges) to avoid corrupting customer documents. | security | prior_knowledge_only | - (prior_knowledge) | **none** | Azure DocumentDB sanitize LLM outputs validate before write; DocumentDB write validation guidance (no explicit service doc found) | yes |
| P17 | Use explain("executionStats") / server-side explain plans and index-usage statistics to verify aggregations use the intended indexes and to measure RU consumption of sample aggregation workloads. | monitoring | prior_knowledge_confirmed | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | documentdb-query-optimizer | yes |
| P18 | Provision sufficient compute/throughput for heavy aggregation jobs and index builds and schedule heavy batch/index work during off-peak windows to avoid throttling. | provisioning | prior_knowledge_confirmed | documentdb-storage (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/storage/SKILL.md | documentdb-storage | yes |
| P19 | Create or build indexes during low-traffic windows (or follow a safe lifecycle: hide → verify → drop) because index creation can consume large amounts of RU and impact latency. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P20 | Enable and configure automatic backups (and point-in-time restore where offered) so you can recover from accidental writes or faulty aggregation runs. | backup | prior_knowledge_confirmed | documentdb-high-availability (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/high-availability/SKILL.md | documentdb-high-availability | yes |
| P21 | Enable diagnostic settings and application-level monitoring (Azure Monitor / Log Analytics) to track RU usage, slow queries, and throttling (HTTP 429) and alert on CPU/memory/IOPS/connection saturation. | monitoring | prior_knowledge_confirmed | documentdb-monitoring (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md | documentdb-monitoring | yes |
| P22 | Azure DocumentDB supports multi-document ACID transactions across collections and shards (the platform documents multi-document transactions as supported). | transactions | prior_knowledge_contradicted | Azure DocumentDB at a glance (public_doc) | https://learn.microsoft.com/azure/documentdb/at-a-glance#mongodb-compatibility | Azure DocumentDB multi-document transactions MongoDB transactions support cross-shard transactions DocumentDB MongoDB API | yes |
| P23 | In local development, drive TLS relaxation (e.g., tlsAllowInvalidCertificates) from env vars and keep such relaxation out of production code; never default tlsAllowInvalidCertificates=true in application code. | local_development | found_in_public_source | documentdb-local-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md | documentdb-local-deployment | yes |

## Searches that returned nothing useful

- Azure DocumentDB record LLM outputs rationale append-only
- Azure DocumentDB sanitize LLM outputs validate before write

## Notes

I loaded domain-specific skills (connection, driver, indexing, query-optimizer, vector-search, security, monitoring, sharding, data-modeling, storage, HA, local-deployment) and used Microsoft Learn searches for batch-write limits and compatibility; prior beliefs K01–K22 have been matched to the public record above (K15 and K16 had no explicit Azure DocumentDB guidance and are recorded as prior_knowledge_only).

