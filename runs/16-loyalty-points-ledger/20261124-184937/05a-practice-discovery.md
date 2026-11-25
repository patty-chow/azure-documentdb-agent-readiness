# 5a. Best practices: prior knowledge against the public record: 16-loyalty-points-ledger

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**22 practices, 17 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 2 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 2 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 14 | Memory and documentation line up. |
| Found in public sources only | 4 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

## Where public sources contradict the model

### P04: Azure DocumentDB supports multi-document ACID transactions (use startSession()/withTransaction and pass the session to each operation) and transactions may span collections and shards; use the driver's transaction APIs to commit or retry.

- **The model believed:** For multi-document transactions, always start the transaction on a session from the same client/connection and ensure the involved collections are in the same database and appropriate partition/shard so the transaction is supported; keep transactions short and touch as few documents as possible. (knowledge of `mongodb`)
- **The source says:** Azure DocumentDB supports multi-document ACID transactions (use startSession()/withTransaction and pass the session to each operation) and transactions may span collections and shards; use the driver's transaction APIs to commit or retry.
- **Source:** [Group multiple operations in transactions in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/how-to-transactions#create-a-transaction)

### P16: Provision cluster compute and storage separately: pick Premium SSD v2 for new clusters, size storage for capacity and choose the compute tier to meet IOPS/bandwidth (IOPS are gated by compute tier, not disk size).

- **The model believed:** Provision throughput appropriately (RU/s or autoscale) for the collections that will receive writes (events and balances), and monitor consumed RU to avoid throttling. Use separate collections for write-heavy and read-heavy workloads if necessary. (knowledge of `azure_cosmos_db`)
- **The source says:** Provision cluster compute and storage separately: pick Premium SSD v2 for new clusters, size storage for capacity and choose the compute tier to meet IOPS/bandwidth (IOPS are gated by compute tier, not disk size).
- **Source:** [documentdb-storage](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/storage/SKILL.md)

## Known to the model, with no public source for this service

| Id | Practice | Knowledge of | Searches tried |
|---|---|---|---|
| P21 | Do not assume driver writeConcern settings (w, j) will be honored identically across services; if strong durability guarantees are required, verify the service's behavior and documentation for write concern mapping before relying on w:'majority' or j:true. | mongodb | search: Azure DocumentDB write concern w majority j; search: Azure DocumentDB durability writeConcern; search: 'writeConcern' site:learn.microsoft.com azure documentdb |
| P22 | Some Mongoose-specific client optimizations (e.g., using .lean() for read-heavy queries and projecting only required fields) are general MongoDB best practices but are not explicitly documented in Azure DocumentDB guidance; treat them as application-level optimizations to apply when using Mongoose. | mongodb | search: Mongoose .lean() Azure DocumentDB; search: 'lean()' site:learn.microsoft.com 'DocumentDB' 'Mongoose' |

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Read the DocumentDB connection string only from an environment variable or secret store (DOCUMENTDB_URI); never hard-code credentials or commit them, and provide a .env.example placeholder for developers. | authentication_and_secrets | prior_knowledge_confirmed | .env.example / README.md (local_file) | **none** | .env.example | yes |
| P02 | Create a single, process-level MongoClient / Mongoose connection and reuse it across the app (singleton pattern); configure the connection pool (e.g., maxPoolSize) according to workload rather than opening a new connection per request. | connection_handling | prior_knowledge_confirmed | documentdb-driver (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md | documentdb-driver | yes |
| P03 | Require TLS and lock down network access: always connect with TLS (tls=true), avoid disabling certificate validation in production, and restrict access using firewall rules or Private Endpoints (prefer VNet/private endpoint and least-privilege identities). | security | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P04 | Azure DocumentDB supports multi-document ACID transactions (use startSession()/withTransaction and pass the session to each operation) and transactions may span collections and shards; use the driver's transaction APIs to commit or retry. | transactions | prior_knowledge_contradicted | Group multiple operations in transactions in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/how-to-transactions#create-a-transaction | Azure DocumentDB transactions startSession withTransaction | yes |
| P05 | When using transactions, run them with the driver's withTransaction helper (or equivalent), avoid non-idempotent external side effects inside the transaction callback, and keep transaction scope small so retries and auto-retries are safe. | transactions | found_in_public_source | Group multiple operations in transactions in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/how-to-transactions#create-a-transaction | Azure DocumentDB transactions startSession withTransaction | yes |
| P06 | Pick the shard/partition key to collocate related data: for read-heavy workloads choose the most common query filter (to localize reads); for write-heavy workloads choose a high-cardinality evenly distributed key to avoid hot partitions. | provisioning_and_partitioning | prior_knowledge_confirmed | documentdb-sharding (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/sharding/SKILL.md | documentdb-sharding | yes |
| P07 | Create a compound index on (accountId, timestamp) (accountId ascending, timestamp descending if queries return most-recent-first) to support efficient /history queries that page by time. | indexing | prior_knowledge_confirmed | documentdb-indexing (index-compound-esr) (installed_skill) | **none** | documentdb-indexing | yes |
| P08 | Create a unique index on balances.accountId (one balance document per account) and update that document atomically inside the same transaction that inserts the event, rather than rebuilding balances from events on every read. | indexing | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P09 | Make index creation idempotent in startup/seed scripts (call createIndexes and tolerate already-exists), and avoid blocking the application on long foreground index builds when possible. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P10 | Use explain('executionStats') / the profiler and index-stats to verify /history and aggregation queries use the intended indexes; iterate on index shape when explain shows a COLLSCAN or blocking SORT. | monitoring_and_debugging | prior_knowledge_confirmed | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | documentdb-query-optimizer | yes |
| P11 | Use idempotency/deduplication keys and enforce them with a uniqueness constraint (or transactional marker) so retries and duplicate deliveries are safe; record the deduplication key and the business write in the same transaction when possible. | data_modeling | prior_knowledge_confirmed | Idempotent Consumer pattern (Azure Architecture Center) (public_doc) | https://learn.microsoft.com/azure/architecture/patterns/idempotent-consumer | Azure DocumentDB idempotency unique index retry duplicate prevention | yes |
| P12 | Denormalize and precompute read-heavy aggregates (e.g., maintain a small balances document with lifetime totals) to avoid running full-collection aggregation scans per request, or ensure aggregations are selective and backed by indexes. | queries_and_aggregations | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P13 | Avoid unbounded arrays and large binary/blobs inside documents; keep documents well under the 16 MB BSON limit and split large fields into side collections or blob storage if needed. | data_modeling | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P14 | Enable retryable reads/writes and implement bounded application retry logic with exponential backoff; design writes to be idempotent so retries are safe and consider driver retry settings (retryReads/retryWrites) as part of the strategy. | retries_and_error_handling | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P15 | When using vector search, define fixed vector dimensionality, choose the right index type for scale (DiskANN for large sets, HNSW/IVF for smaller), tune build/search params, and normalize embeddings for cosine similarity before storing. | vector_search | found_in_public_source | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | no |
| P16 | Provision cluster compute and storage separately: pick Premium SSD v2 for new clusters, size storage for capacity and choose the compute tier to meet IOPS/bandwidth (IOPS are gated by compute tier, not disk size). | provisioning | prior_knowledge_contradicted | documentdb-storage (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/storage/SKILL.md | documentdb-storage | yes |
| P17 | Use the Azure guidance for idempotent operations and transactional outbox/inbox patterns when writing seed/verification scripts so they are safe to rerun (use upserts, existence checks, or create-if-missing inside a transaction or idempotent workflow). | operations_and_deployment | prior_knowledge_confirmed | Idempotent Consumer pattern (Azure Architecture Center) (public_doc) | https://learn.microsoft.com/azure/architecture/patterns/idempotent-consumer | idempotency seed scripts Azure guidance | yes |
| P18 | Use monitoring and diagnostics: enable diagnostic settings and slow-query logs, ingest them into Log Analytics, and alert on CPU/memory/IOPS/storage/connection saturation for the cluster tier. | monitoring_and_debugging | found_in_public_source | documentdb-monitoring (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md | documentdb-monitoring | yes |
| P19 | Prefer the service text/vector search features (textSearch / $search) over community $text indexes for production text search workloads on Azure DocumentDB. | indexing | found_in_public_source | documentdb-indexing (index-text-prefer-textsearch) (installed_skill) | **none** | documentdb-indexing | no |
| P20 | Keep transactions small and short-lived (touch as few documents as possible), and be prepared to retry or abort and retry transactions that hit conflicts or time limits. | transactions | prior_knowledge_confirmed | Group multiple operations in transactions in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/how-to-transactions#create-a-transaction | Azure DocumentDB transactions startSession withTransaction | yes |
| P21 | Do not assume driver writeConcern settings (w, j) will be honored identically across services; if strong durability guarantees are required, verify the service's behavior and documentation for write concern mapping before relying on w:'majority' or j:true. | durability_and_consistency | prior_knowledge_only | - (prior_knowledge) | **none** | search: Azure DocumentDB write concern w majority j; search: Azure DocumentDB durability writeConcern; search: 'writeConcern' site:learn.microsoft.com azure documentdb | yes |
| P22 | Some Mongoose-specific client optimizations (e.g., using .lean() for read-heavy queries and projecting only required fields) are general MongoDB best practices but are not explicitly documented in Azure DocumentDB guidance; treat them as application-level optimizations to apply when using Mongoose. | mongoose_practices | prior_knowledge_only | - (prior_knowledge) | **none** | search: Mongoose .lean() Azure DocumentDB; search: 'lean()' site:learn.microsoft.com 'DocumentDB' 'Mongoose' | yes |

## Searches that returned nothing useful

- Azure DocumentDB write concern w:'majority' j:true
- Mongoose .lean() guidance in Azure DocumentDB docs

## Notes

I discovered public guidance across the installed DocumentDB skills (connection, driver, indexing, data-modeling, sharding, security, storage, monitoring, vector-search) and Microsoft Learn docs. Practices implemented in the sample (env var for DOCUMENTDB_URI, singleton connection, transactions, append-only events + balances, createIndexes usage, .lean() usage in code) align with many public recommendations. Two prior beliefs lacked an explicit Azure DocumentDB documentation confirmation in the public sources searched: write-concern (w/j) specifics and a Mongoose .lean() recommendation — these remain 'prior_knowledge_only'. K03 (transactions must be limited to same DB/partition) and K14 (provision RU/s autoscale) were contradicted by Azure DocumentDB public guidance (Azure DocumentDB supports multi-document ACID transactions across collections/shards and uses compute tiers + Premium SSD v2 rather than RU/sec autoscale).

Prior beliefs the discovery step did not classify: K04, K20. See 05a-prior-beliefs.json.

