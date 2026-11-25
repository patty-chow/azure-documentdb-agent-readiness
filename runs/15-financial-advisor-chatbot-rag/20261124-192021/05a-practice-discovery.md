# 5a. Best practices: prior knowledge against the public record: 15-financial-advisor-chatbot-rag

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**23 practices, 19 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 1 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 2 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 17 | Memory and documentation line up. |
| Found in public sources only | 3 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

## Where public sources contradict the model

### P18: Enable diagnostic settings and alert on cluster-level saturation (CPU, memory, IOPS, storage, connection counts) and collect slow-query logs in Log Analytics to find expensive queries; monitor these host-level/IO metrics rather than relying on Cosmos DB-style RU metrics for the managed MongoDB service.

- **The model believed:** Monitor and log request charge / RU consumption per operation (or equivalent metric) and surface slow queries/expensive vector-search calls so you can tune indexes and partitioning. (knowledge of `azure_cosmos_db`)
- **The source says:** Enable diagnostic settings and alert on cluster-level saturation (CPU, memory, IOPS, storage, connection counts) and collect slow-query logs in Log Analytics to find expensive queries; monitor these host-level/IO metrics rather than relying on Cosmos DB-style RU metrics for the managed MongoDB service.
- **Source:** [documentdb-monitoring](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md)

## Known to the model, with no public source for this service

| Id | Practice | Knowledge of | Searches tried |
|---|---|---|---|
| P22 | Store vectors in a binary/typed float representation (e.g., Float32 arrays) and keep a documented dimension field so index creation and queries use the correct dimensionality. | general | Azure DocumentDB vector storage binary Float32; "DocumentDB store vectors binary Float32"; "vector storage format DocumentDB" |
| P23 | Avoid deep pagination with large skip values; prefer cursor/range-based pagination (stable sort key like createdAt or _id) to keep queries efficient. | mongodb | Searches tried: "Azure DocumentDB pagination skip vs range", "avoid large skip Azure DocumentDB", "deep pagination skip performance DocumentDB" |

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Create and reuse a single MongoClient instance as a process-wide singleton; do not create a new client per request and only close the client on graceful shutdown. | connection handling | prior_knowledge_confirmed | documentdb-driver (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md | documentdb-driver | yes |
| P02 | Read the cluster connection string from an environment variable for local/dev usage and never commit it into source control; rotate and deliver secrets via Key Vault or equivalent for production. | authentication and secrets | prior_knowledge_confirmed | .env.example / README.md (local_file) | **none** | .env.example / README.md | yes |
| P03 | In Azure-managed environments prefer Azure Key Vault + Managed Identity (and Microsoft Entra identity/RBAC) for credential access instead of using process environment variables directly. | authentication and secrets | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P04 | Always require TLS for connections to Azure DocumentDB and do not disable certificate validation in production (ensure tls=true/tls option and a correct CA bundle), addressing CA issues by fixing the cert chain rather than disabling checks. | connection handling / security | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P05 | Tune the driver's connection-pool settings (maxPoolSize, minPoolSize, maxIdleTimeMS) to match the application's concurrency profile and follow serverless vs long-running server guidance (small pools for serverless, larger pools for OLTP). | connection handling | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P06 | Implement robust transient-failure handling: use driver retry features where available, and implement application-level retries with exponential backoff + jitter for transient network errors and respect rate-limit signals (429) and Retry-After headers. | retries and throttling | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P07 | Provision cluster compute/throughput appropriate to vector-search workloads (choose a cluster tier that supports your vector index type and expected vector count, enable autoscale if available, and monitor metrics to increase capacity before throttling occurs). | provisioning | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | yes |
| P08 | Normalize embeddings when using cosine similarity and store embedding metadata (model name, version, and dimensionality) alongside vectors so you can detect model drift and reindex if models or dimensions change. | vector search / reproducibility | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | yes |
| P09 | Create a dedicated vector index (cosmosSearch) with explicit parameters (kind, dimensions, similarity, and tuned build/query parameters) that exactly match your embeddings; mismatched dimensions or similarity silently corrupt results. | vector indexing | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | yes |
| P10 | Push cheap metadata predicates into the vector search by using the `filter` parameter in `cosmosSearch` (metadata-first then vector search) rather than post-filtering the kNN results. | queries and search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | yes |
| P11 | Choose the vector index subtype by scale: prefer DiskANN for production large-scale workloads, HNSW for moderate sizes, and IVF for small collections, because each has different recall/memory/latency trade-offs. | vector indexing | found_in_public_source | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | yes |
| P12 | Do not return full vector payloads in normal query responses—project out the vector field and only fetch raw vectors for reindexing or recomputation jobs. | queries and performance | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | yes |
| P13 | Create conventional B-tree (single-field or compound) indexes on all fields used for equality filters or sorts and declare unique constraints where required to avoid collection scans. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P14 | Make index lifecycle operations idempotent: inventory existing indexes (`getIndexes` / `$indexStats`), `hideIndex` to dry-run removals, and only drop indexes after verifying no regressions. | indexing / provisioning | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P15 | Do not store unbounded conversation history in the database; enforce an upper bound via max messages, TTL indexes, or periodic summarization/compaction before persisting agent memory. | data modeling / agent memory | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | index-ttl-expiry.md (documentdb-indexing) | yes |
| P16 | Keep documents well under the BSON size limit: cap document sizes, avoid embedding large transcripts or entire portfolios, and split very large fields into side collections referenced by id. | data modeling | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P17 | Record and version document schema (e.g., add a schemaVersion field) and plan migration/reindexing paths when document shape or embedding dimension changes. | data modeling / provisioning | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P18 | Enable diagnostic settings and alert on cluster-level saturation (CPU, memory, IOPS, storage, connection counts) and collect slow-query logs in Log Analytics to find expensive queries; monitor these host-level/IO metrics rather than relying on Cosmos DB-style RU metrics for the managed MongoDB service. | monitoring | prior_knowledge_contradicted | documentdb-monitoring (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md | documentdb-monitoring | yes |
| P19 | For full-text / keyword search use DocumentDB's search indexes created with `createSearchIndexes` and query with the `$search` aggregation stage (BM25, fuzzy, phrase, custom analyzers) rather than MongoDB community `$text` indexes. | full-text search | found_in_public_source | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing (index-text-prefer-textsearch.md) | yes |
| P20 | Tune vector-index build/query parameters (e.g., maxDegree, lBuild, lSearch, k) and consider product quantization or half-precision indexing to trade memory for recall/latency depending on dataset size and budget. | vector indexing / performance | found_in_public_source | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | yes |
| P21 | Make seed scripts idempotent: upsert documents by stable id (or check before insert), and provide a guarded --wipe option for test environments; document the seed behavior. | devops / data loading | prior_knowledge_confirmed | src/seed.js / README.md (local_file) | **none** | src/seed.js (uses updateOne upsert) / README.md | yes |
| P22 | Store vectors in a binary/typed float representation (e.g., Float32 arrays) and keep a documented dimension field so index creation and queries use the correct dimensionality. | vector search / data modeling | prior_knowledge_only | - (prior_knowledge) | **none** | Azure DocumentDB vector storage binary Float32; "DocumentDB store vectors binary Float32"; "vector storage format DocumentDB" | yes |
| P23 | Avoid deep pagination with large skip values; prefer cursor/range-based pagination (stable sort key like createdAt or _id) to keep queries efficient. | queries and performance | prior_knowledge_only | - (prior_knowledge) | **none** | Searches tried: "Azure DocumentDB pagination skip vs range", "avoid large skip Azure DocumentDB", "deep pagination skip performance DocumentDB" | yes |

## Searches that returned nothing useful

- Azure DocumentDB store vectors binary Float32
- DocumentDB vector storage binary float32 format
- Azure DocumentDB pagination skip vs range performance
- Azure DocumentDB avoid large skip pagination

## Notes

I inspected the app files (src/db.js, src/agent.js, src/seed.js, README). Most public guidance is available in the installed DocumentDB skills: connection (singleton, pool sizing, TLS, serverless patterns), driver usage (singleton), vector-search (DiskANN/HNSW/IVF selection, dimensions and similarity must match, lBuild/lSearch/maxDegree tuning, normalize embeddings and store model/dims), indexing lifecycle (getIndexes, $indexStats, hideIndex), TTL semantics, and monitoring (CPU/memory/IOPS/connection alerts and slow-query logs). Two prior beliefs had no direct Azure DocumentDB source found here: storing vectors explicitly as binary Float32 arrays (K07) and explicit guidance on avoiding large skip pagination values (K17) — I recorded those as prior_knowledge_only and listed the queries I tried in how_found. One prior belief was contradicted: K16 (monitor RU/request-charge); the Azure DocumentDB guidance focuses on host/IO metrics and slow-query logs rather than Cosmos DB RU counters for this managed MongoDB service.

