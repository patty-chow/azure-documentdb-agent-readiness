# 5a. Best practices: prior knowledge against the public record: 05-appointment-scheduling-assistant

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**25 practices, 23 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 0 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 2 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 23 | Memory and documentation line up. |
| Found in public sources only | 0 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

## Known to the model, with no public source for this service

| Id | Practice | Knowledge of | Searches tried |
|---|---|---|---|
| P19 | Persist only minimal identifiers for agent conversational memory (conversationId, lastAppointmentId) and keep full conversational context ephemeral; encrypt persisted sensitive state at rest when required. | general | azure documentdb conversation memory persistence; azure documentdb pii logs memory storage; documentdb encryption conversation state |
| P23 | When rescheduling slot times, check for overlapping slots for the same provider using indexed queries and enforce application-level checks to prevent overlapping bookings because DB-level partial unique constraints on time ranges are not a general replacement. | mongodb | azure documentdb overlapping time ranges unique constraint; mongodb partial unique index time ranges; documentdb enforce non-overlapping time ranges |

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Read DOCUMENTDB_URI from an environment variable and create a single shared MongoClient at process startup, reusing that client across modules instead of opening a new connection per request. | connection handling | prior_knowledge_confirmed | documentdb-driver (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md | documentdb-driver | yes |
| P02 | Tune MongoClient pool and timeout settings (maxPoolSize, minPoolSize, maxIdleTimeMS, serverSelectionTimeoutMS, socketTimeoutMS) based on your environment (serverless vs long-running) and expected concurrency. | connection handling | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P03 | Always require TLS on connections to Azure DocumentDB and do not disable certificate validation in production. | authentication and secrets | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P04 | Do not commit database credentials or connection strings to source control; load secrets from environment variables or a secrets store (e.g., Azure Key Vault) and follow least-privilege access for retrieval. | authentication and secrets | prior_knowledge_confirmed | How to choose between standard (manual) and autoscale provisioned throughput (public_doc) | https://learn.microsoft.com/azure/cosmos-db/how-to-choose-offer#understand-your-traffic-patterns | azure documentdb secrets best practices | yes |
| P05 | Prefer Microsoft Entra ID + RBAC or otherwise use a dedicated least-privilege account for application access rather than a cluster admin credential. | authentication and secrets | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P06 | Implement retries with exponential backoff for transient errors and rate-limit responses (handle 429/Retry-After), and enable the driver's retryReads/retryWrites where appropriate. | retries | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P07 | Perform slot booking with an atomic conditional update (e.g., findOneAndUpdate or updateOne with filter { _id: slotId, status: 'available' } and check the returned/modified count) to detect conflicts instead of a separate read-then-write. | data integrity / concurrency | prior_knowledge_confirmed | documentdb-driver (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md | documentdb-driver | yes |
| P08 | Use multi-document transactions (session.withTransaction) when supported by the cluster's MongoDB API version to make related updates atomic; if transactions are unavailable, use a compensated pattern and detect partial failures. | transactions | prior_knowledge_confirmed | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | documentdb-query-optimizer | yes |
| P09 | Create a compound index that matches common availability queries (example: { providerId: 1, start: 1, status: 1 }) and make index creation idempotent in seed scripts. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P10 | Enforce uniqueness at the database level by creating unique indexes for fields that must be unique (e.g., appointment reference or other application-unique keys) instead of relying only on application checks. | data modeling / indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P11 | When storing embeddings for vector search, store them as consistent-dimension numeric arrays and create a vector index with the correct dimension and similarity metric (DiskANN/HNSW/IVF) supported by the cluster. | vector search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | no |
| P12 | Provision throughput sensibly: use autoscale or an appropriately sized provisioned throughput at the collection or database level for your workload, and prefer collection-level throughput for predictable isolation. | provisioning | prior_knowledge_confirmed | Provision database, container or autoscale throughput on Azure Cosmos DB for MongoDB resources (public_doc) | https://learn.microsoft.com/azure/cosmos-db/mongodb/how-to-provision-throughput | azure documentdb autoscale throughput | yes |
| P13 | Monitor RU consumption and throttle/back off on 429 responses; use Azure Monitor / diagnostic settings to observe RU usage and autoscale behavior. | performance / retries | prior_knowledge_confirmed | How to choose between standard (manual) and autoscale provisioned throughput (public_doc) | https://learn.microsoft.com/azure/cosmos-db/how-to-choose-offer#understand-your-traffic-patterns | azure documentdb autoscale 429 retry guidance | yes |
| P14 | Avoid unbounded collection scans: always filter on indexed fields and use projection to return only necessary fields to reduce RU cost and latency. | queries | prior_knowledge_confirmed | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | documentdb-query-optimizer | yes |
| P15 | Make seed scripts idempotent: create collections and indexes only if they don't exist and use upsert/guards so running seed multiple times does not create duplicates. | provisioning / ops | prior_knowledge_confirmed | documentdb-local-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md | documentdb-local-deployment | yes |
| P16 | Use TTL indexes for ephemeral records by indexing a Date field (expireAt/createdAt) with expireAfterSeconds; remember the field must be a Date and expiry is not second-accurate. | data lifecycle | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing index-ttl-expiry.md | no |
| P17 | Prefer findOneAndUpdate (or similar find+modify) with an appropriate returnDocument option to update documents in-place atomically and return the final state for use in application state/memory. | queries / atomic updates | prior_knowledge_confirmed | documentdb-driver (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md | documentdb-driver | yes |
| P18 | Avoid storing or logging sensitive patient information in plaintext; redact or omit PII from logs and use encryption for backups and at-rest storage (CMK) where required by compliance. | security / compliance | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security security-tls-required.md + security-cmk-encryption.md | yes |
| P19 | Persist only minimal identifiers for agent conversational memory (conversationId, lastAppointmentId) and keep full conversational context ephemeral; encrypt persisted sensitive state at rest when required. | data modeling / security | prior_knowledge_only | - (prior_knowledge) | **none** | azure documentdb conversation memory persistence; azure documentdb pii logs memory storage; documentdb encryption conversation state | yes |
| P20 | For free-text search prefer the platform text/search features (DocumentDB's textSearch / $search) and scope text indexes to only the fields required to limit index size and RU cost. | indexing / search | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing index-text-prefer-textsearch.md | no |
| P21 | Model for access patterns: keep one slot document per slot and a separate appointments collection that references slotId so you can target atomic updates on slots without large document rewrites. | data modeling | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P22 | Protect the DocumentDB cluster with network restrictions (IP firewall rules or Private Endpoint / VNet) to limit access to authorized hosts only. | security / networking | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security security-private-endpoint.md | yes |
| P23 | When rescheduling slot times, check for overlapping slots for the same provider using indexed queries and enforce application-level checks to prevent overlapping bookings because DB-level partial unique constraints on time ranges are not a general replacement. | data integrity / modeling | prior_knowledge_only | - (prior_knowledge) | **none** | azure documentdb overlapping time ranges unique constraint; mongodb partial unique index time ranges; documentdb enforce non-overlapping time ranges | yes |
| P24 | Instrument and trace booking and rescheduling flows (record latency, RU cost, success/failure) and surface slow queries and RU hotspots through diagnostic settings and Log Analytics alerts. | observability / ops | prior_knowledge_confirmed | documentdb-monitoring (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md | documentdb-monitoring | yes |
| P25 | Include fields used for sorting (e.g., start) in your index prefix so queries that sort can avoid an in-memory blocking SORT; follow the ESR (Equality → Sort → Range) rule when designing compound indexes. | indexing / performance | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing index-compound-esr.md | yes |

## Searches that returned nothing useful

- azure documentdb conversation memory persistence
- azure documentdb agent memory persist conversation identifiers best practice
- azure documentdb enforce non-overlapping time ranges unique constraint
- documentdb prevent overlapping time ranges booking constraint

## Notes

Open discovery used the installed DocumentDB skills (connection, driver, indexing, vector-search, security, data-modeling, query-optimizer, monitoring, local-deployment, storage, high-availability) and Microsoft Learn docs for throughput/autoscale/provisioning. Most prior beliefs (K01–K18, K20, K21, K22, K24, K25) are confirmed by Azure DocumentDB public guidance; two prior beliefs (K19, K23) had no direct, service-specific authoritative guidance found and are recorded as prior_knowledge_only with the searches attempted.

