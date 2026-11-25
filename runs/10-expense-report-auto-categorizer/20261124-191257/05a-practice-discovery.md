# 5a. Best practices: prior knowledge against the public record: 10-expense-report-auto-categorizer

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**24 practices, 23 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 0 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 1 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 17 | Memory and documentation line up. |
| Found in public sources only | 6 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

## Known to the model, with no public source for this service

| Id | Practice | Knowledge of | Searches tried |
|---|---|---|---|
| P20 | Persist agent/session memory or ephemeral classification decisions with explicit versioning and, if ephemeral, a TTL; include deterministic-fallback flags to allow replayable deterministic tests. | general | documentdb-vector-search; documentdb-data-modeling; searches: "azure documentdb store agent memory ttl", "documentdb ephemeral session memory ttl", "azure documentdb deterministic fallback flag LLM" |

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Read the DocumentDB MongoDB-compatible connection string from an environment variable (e.g., DOCUMENTDB_URI) at runtime and do not check it into source control or logs. | authentication_and_secrets | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P02 | Create one MongoClient/driver client and reuse it (process-wide singleton) rather than creating a new client per request; cache it across warm serverless invocations. | connection | prior_knowledge_confirmed | documentdb-driver (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md | documentdb-driver | yes |
| P03 | Always connect with TLS enabled and do not disable certificate validation in production (ensure CA bundles or proper TLS configuration instead). | security | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P04 | Use least-privilege credentials for applications (create per-app users or use Microsoft Entra ID / managed identity + RBAC) instead of using admin/root accounts. | security | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P05 | Include a schema or classifier version (and model identifier/dimensions where vectors are used) alongside vectors and indexable metadata so you can interpret and rebuild results later. | data_modeling | found_in_public_source | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | yes |
| P06 | Embed small, bounded arrays (one-to-few) inside the parent document when children are always read together; avoid embedding unbounded arrays that could approach BSON size limits. | data_modeling | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P07 | Model frequently-updated or unbounded children (e.g., line items that are queried/updated individually or can grow large) as a separate collection with a reference and index on the parent id. | data_modeling | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P08 | Design compound indexes that match the app’s common query shapes following the ESR rule (Equality → Sort → Range) so queries and sorts can be served by an index without blocking in-memory sorts. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P09 | Ensure fields used in sort operations are included in an index (or index prefix) to avoid blocking in-memory sorts and high memory use. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P10 | Use partial or sparse indexes for optional or rarely-populated fields (e.g., policy_violation:true) to reduce index size and write cost when appropriate. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P11 | Plan index changes safely: inventory existing indexes, detect redundancy, hide an index to test, build/drop during low-traffic windows and monitor impact rather than doing blind index changes in production. | provisioning | found_in_public_source | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P12 | For vector search, create a matching vector index (DiskANN/HNSW/IVF) with the correct dimensionality and similarity and tune build/search params (e.g., lBuild, lSearch, maxDegree) for your recall/latency tradeoff. | vector_search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | no |
| P13 | Normalize/store the embedding dimensionality and persist model identifiers with vectors, and index metadata fields (company_id, report_id) so ANN queries can pre-filter by metadata before nearest-neighbour search. | vector_search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | no |
| P14 | Implement idempotent processing using an atomic state change (e.g., findOneAndUpdate with a processing_status filter) or use optimistic concurrency (ETag/_etag) to prevent double-processing in retries. | retries | prior_knowledge_confirmed | Transactions and optimistic concurrency control (public_doc) | https://learn.microsoft.com/azure/cosmos-db/database-transactions-optimistic-concurrency#optimistic-concurrency-control | Azure Cosmos DB optimistic concurrency findOneAndUpdate | yes |
| P15 | Use retries with exponential backoff for transient network or rate-limit errors, catch driver-specific retryable exceptions, and bound total retry time to avoid long blocking operations. | retries | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P16 | Avoid long-running, large multi-document transactions for classifier pipelines; prefer single-document atomic updates or small transactions scoped to the partition key. | queries | prior_knowledge_confirmed | Transactions and optimistic concurrency control (public_doc) | https://learn.microsoft.com/azure/cosmos-db/database-transactions-optimistic-concurrency#optimistic-concurrency-control | Azure Cosmos DB transactions optimistic concurrency | yes |
| P17 | Log slow or high-latency queries, capture timestamps and correlation ids, and use explain("executionStats") and provider tooling (MCP/diagnostic logs) to inspect query plans and index usage. | observability | prior_knowledge_confirmed | documentdb-query-optimization (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimization/SKILL.md | documentdb-query-optimization | yes |
| P18 | Never persist API keys or plaintext credentials (LLM keys or DB admin passwords) in the database; keep secrets in a secret store (Key Vault) or use managed identities. | authentication_and_secrets | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P19 | Make seed and demo scripts idempotent (create-if-not-exists / upsert semantics) and target the intended database name so repeated runs are safe. | provisioning | prior_knowledge_confirmed | documentdb-local-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md | documentdb-local-deployment | yes |
| P20 | Persist agent/session memory or ephemeral classification decisions with explicit versioning and, if ephemeral, a TTL; include deterministic-fallback flags to allow replayable deterministic tests. | data_modeling | prior_knowledge_only | - (prior_knowledge) | **none** | documentdb-vector-search; documentdb-data-modeling; searches: "azure documentdb store agent memory ttl", "documentdb ephemeral session memory ttl", "azure documentdb deterministic fallback flag LLM" | yes |
| P21 | Use the $search aggregation stage with the cosmosSearch operator for kNN vector queries, tune k and lSearch (keep lSearch ≥ k), and push equality/range/geospatial pre-filters into the operator's filter field rather than post-filtering. | vector_search | found_in_public_source | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | no |
| P22 | Prefer provider-supported full-text/search (DocumentDB's textSearch/$search) features over community $text where available for better integration and scoring. | indexing | found_in_public_source | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | no |
| P23 | Be aware of driver and API feature differences across supported MongoDB wire versions; check the provider's feature-support matrix for operations like retryable writes, findAndModify, sessions and transaction support before relying on them. | provisioning | found_in_public_source | Supported features and syntax in Azure Cosmos DB for MongoDB 7.0 server version (public_doc) | https://learn.microsoft.com/azure/cosmos-db/mongodb/feature-support-70#operators | Azure Cosmos DB MongoDB feature support search | yes |
| P24 | Tune connection pool parameters to your deployment type: small pools for serverless warm-invocations (maxPoolSize 3–5), larger pools for long-running OLTP servers, and short maxIdleTime for serverless to avoid idle connections. | connection | found_in_public_source | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |

## Searches that returned nothing useful

- azure documentdb LLM provenance
- azure documentdb store classifier_version deterministic_fallback_flag
- azure documentdb persist agent memory TTL
- Azure DocumentDB guidance "deterministic_fallback_flag"

## Notes

I inspected the sample app (it reads DOCUMENTDB_URI, uses Motor AsyncIOMotorClient via Beanie, embeds items in Report documents, creates simple indexes via a separate module, seeds idempotently, and includes vector-related skills in the environment). Most prior beliefs (K01–K04, K06–K10, K11, K12–K15, K16–K19) are supported by installed skills or Microsoft docs (feature/transactions pages); two beliefs about explicit LLM-provenance fields (K05) and storing agent-memory with TTL and deterministic flags (K20) had no Azure DocumentDB public guidance I could find, so they are marked prior_knowledge_only. Where Microsoft Learn pages returned coverage (transactions, feature-support, update semantics) I cited the page URL; for many operational best practices the installed skills contained the documented guidance and are referenced as installed_skill sources.

Prior beliefs the discovery step did not classify: K05, K11. See 05a-prior-beliefs.json.

