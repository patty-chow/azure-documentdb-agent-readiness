# 5a. Best practices: prior knowledge against the public record: 19-cross-sell-recommendation-beanie

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**25 practices, 13 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 1 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 0 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 20 | Memory and documentation line up. |
| Found in public sources only | 4 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

## Where public sources contradict the model

### P04: For new Python async code on Azure DocumentDB, prefer PyMongo's AsyncMongoClient (pymongo AsyncMongoClient) rather than Motor because Motor is deprecated for new Python async usage.

- **The model believed:** Use Motor (async pymongo driver) under Beanie for async access rather than creating blocking pymongo clients or synchronous DB calls in async code. (knowledge of `mongodb`)
- **The source says:** For new Python async code on Azure DocumentDB, prefer PyMongo's AsyncMongoClient (pymongo AsyncMongoClient) rather than Motor because Motor is deprecated for new Python async usage.
- **Source:** [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md)

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Always require TLS on the wire and do not disable certificate validation in production when connecting to an Azure DocumentDB Mongo endpoint. | security | prior_knowledge_confirmed | documentdb-security/security-tls-required (installed_skill) | **none** | documentdb-security | yes |
| P02 | Read the cluster connection string from environment variables in development and use Key Vault (or another secret store) for production secrets; never commit credentials to source control or logs. | authentication/secrets | prior_knowledge_confirmed | documentdb-azure-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/azure-deployment/SKILL.md | documentdb-azure-deployment | yes |
| P03 | Create a single MongoClient (singleton) per process and reuse it for the application lifetime rather than creating a client per request. | connection handling | prior_knowledge_confirmed | documentdb-driver/driver-singleton-client (installed_skill) | **none** | documentdb-driver | yes |
| P04 | For new Python async code on Azure DocumentDB, prefer PyMongo's AsyncMongoClient (pymongo AsyncMongoClient) rather than Motor because Motor is deprecated for new Python async usage. | library/runtime | prior_knowledge_contradicted | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P05 | Tune connection-pool and timeout settings for the expected concurrency pattern (maxPoolSize/minPoolSize, socketTimeoutMS, connectTimeoutMS, serverSelectionTimeoutMS) instead of accepting driver defaults. | connection handling | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P06 | In serverless environments initialize the database client outside the handler (module/global scope) and use small pools (e.g., maxPoolSize 3–5, minPoolSize 0) so warm invocations reuse connections and cold starts don't create many idle connections. | connection handling | found_in_public_source | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P07 | Azure DocumentDB's connection string commonly includes retryWrites=false because the service does not support retryable writes; verify driver defaults and set retryWrites accordingly. | connection handling | found_in_public_source | documentdb-azure-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/azure-deployment/SKILL.md | documentdb-azure-deployment | yes |
| P08 | When using cosine similarity, L2-normalize (unit-length) embeddings at ingest and store the embedding model name, dimensions and version alongside each vector so you can detect drift and rebuild indexes if the model changes. | vector_search | prior_knowledge_confirmed | documentdb-vector-search/vector-normalize-embeddings (installed_skill) | **none** | documentdb-vector-search | yes |
| P09 | Enforce and validate the embedding dimension and numeric type at write time and ensure index `dimensions` matches the model output exactly; rebuild the index if embedding model or dimension changes. | data validation | prior_knowledge_confirmed | documentdb-vector-search/vector-create-diskann-index (installed_skill) | **none** | documentdb-vector-search | yes |
| P10 | Choose the vector index type by scale: prefer vector-diskann for production large-scale workloads (M30+), HNSW for up to ~50k vectors, and IVF for very small sets; pick similarity (COS/L2/IP) to match your normalization strategy. | vector_search | prior_knowledge_confirmed | documentdb-vector-search/vector-choose-index-type (installed_skill) | **none** | documentdb-vector-search | yes |
| P11 | Tune vector index build/query parameters (e.g., DiskANN maxDegree and lBuild at index time; lSearch and k at query time) to trade recall vs latency and test with realistic queries. | vector_search | prior_knowledge_confirmed | documentdb-vector-search/vector-create-diskann-index (installed_skill) | **none** | documentdb-vector-search | yes |
| P12 | Run kNN with the $search aggregation stage using cosmosSearch, pass filters inside the cosmosSearch operator (not as a post-filter), and project the search score for reranking. | vector_search/queries | prior_knowledge_confirmed | documentdb-vector-search/vector-knn-query (installed_skill) | **none** | documentdb-vector-search | yes |
| P13 | Aggregate order history into co-purchase counts server-side using MongoDB aggregation pipelines (unwind, group/self-join) rather than loading all orders into the application. | queries | prior_knowledge_confirmed | documentdb-query-optimization/query-explain-plan (installed_skill) | **none** | documentdb-query-optimization | yes |
| P14 | Use atomic update operators such as $inc together with upsert (upsert: true) to increment co-purchase counts atomically and avoid race conditions. | data integrity | prior_knowledge_confirmed | Field update - operators (public_doc) | https://learn.microsoft.com/documentdb/query/operators/field-update/$inc | Azure docs search: "$inc Azure DocumentDB" | yes |
| P15 | Implement exponential backoff and retry logic for transient network/driver errors and handle rate-limited responses (429) with capped backoff; use driver retryReads where supported. | retries | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P16 | Set reasonable server-side query time limits (maxTimeMS) and enforce request cancellation/timeouts at the API layer to avoid runaway queries and resource exhaustion. | queries | prior_knowledge_confirmed | Azure DocumentDB service limits and quotas reference (public_doc) | https://learn.microsoft.com/azure/documentdb/limitations | Azure docs search: "Azure DocumentDB maxTimeMS query limit" | yes |
| P17 | Do not store sensitive PII in embeddings or unencrypted metadata; encrypt or redact sensitive fields at the application level before storing in DocumentDB and keep sensitive mappings in a separate secure store. | security/privacy | prior_knowledge_confirmed | Security Frame: Sensitive Data \| Mitigations (public_doc) | https://learn.microsoft.com/azure/security/develop/threat-modeling-tool-sensitive-data#ensure-that-sensitive-data-relevant-to-web-api-is-not-stored-in-browser's-storage | Azure docs search: "sensitive data encrypt DocumentDB" | yes |
| P18 | Create conventional indexes (B-tree) to support non-vector filters and sorting (for example on co_purchase_count or frequently filtered product fields) so hybrid queries remain efficient. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P19 | Build indexes in background when possible and avoid creating large unique/index builds during peak traffic; create unique indexes on empty collections or schedule blocking builds during maintenance windows because unique builds block writes. | provisioning/maintenance | prior_knowledge_confirmed | Background indexing (public_doc) | https://learn.microsoft.com/azure/documentdb/background-indexing | Azure docs search: "background index build Azure DocumentDB" | yes |
| P20 | Enable diagnostic settings and slow-query logs, send them to Log Analytics and alert on CPU/memory/IOPS/connection saturation so you can monitor index usage and identify slow queries via explain()/slow logs. | monitoring | prior_knowledge_confirmed | documentdb-monitoring/monitoring-slow-query-log (installed_skill) | **none** | documentdb-monitoring | yes |
| P21 | Use least-privilege access: prefer Microsoft Entra ID + RBAC and create per-application roles/users scoped to the application database instead of using cluster-admin credentials in apps. | authentication/secrets | prior_knowledge_confirmed | documentdb-security/security-entra-rbac (installed_skill) | **none** | documentdb-security | yes |
| P22 | Create a unique index on a canonical unordered-pair key (e.g., pair_key) to enable atomic upserts or deduplication when incrementing co-purchase counters. | indexing | prior_knowledge_confirmed | Manage indexing in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/indexing | Azure docs search: "unique index Azure DocumentDB createIndex" | yes |
| P23 | Size cluster compute and storage for ANN/vector workloads (DiskANN/HNSW memory needs); prefer M30+ for production DiskANN and plan to scale up if vector search is memory or IO bound. | provisioning | prior_knowledge_confirmed | documentdb-vector-search/vector-choose-index-type (installed_skill) | **none** | documentdb-vector-search | yes |
| P24 | Batch embedding requests to the embedding service (respecting model token and per-request limits) to improve throughput and avoid hitting per-request and TPM limits. | external_api | found_in_public_source | Generate embeddings with Azure OpenAI - Best practices (public_doc) | https://learn.microsoft.com/azure/foundry/openai/how-to/embeddings#best-practices | Azure docs search: "batch embeddings Azure OpenAI" | yes |
| P25 | Prefer storing embeddings as numeric arrays (dense float) and consider product quantization or half-precision (fp16) to reduce memory footprint when supported by the index engine. | vector_search | found_in_public_source | documentdb-vector-search/vector-product-quantization (installed_skill) | **none** | documentdb-vector-search | yes |

## Searches that returned nothing useful

- canonical unordered pair key Azure DocumentDB guidance
- product_pairs collection schema Azure DocumentDB best practice 'product_pairs' 'canonical_pair_key' fields embedding co_purchase_count
- cache embeddings Azure DocumentDB 'cache embeddings' guidance
- API design 'do not return embeddings' Azure DocumentDB guidance
- workspace root contained no app files to inspect

## Notes

Discovery used the installed DocumentDB skills plus Microsoft Learn / Azure docs. The workspace contained no local app files to read. Prior beliefs K07, K08, K12 and K25 had no explicit Azure DocumentDB documentation confirming their exact wording; they are reported as prior_knowledge_only below.

Prior beliefs the discovery step did not classify: K07, K08, K12, K25. See 05a-prior-beliefs.json.

