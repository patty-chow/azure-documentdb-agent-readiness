# 5a. Best practices: prior knowledge against the public record: 12-abandoned-cart-recovery-orchestration

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**22 practices, 22 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 1 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 0 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 14 | Memory and documentation line up. |
| Found in public sources only | 7 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

## Where public sources contradict the model

### P21: Do not assume Cosmos DB throughput concepts (RU/s autoscale) map directly to Azure DocumentDB; instead, size compute tier for IOPS/throughput because IOPS are gated by compute (Premium SSD v2) rather than disk size.

- **The model believed:** Provision adequate throughput for queries and bulk writes (use autoscale where available) and monitor RU/s (or equivalent) consumption; tune indices and batching to control cost. (knowledge of `azure_cosmos_db`)
- **The source says:** Do not assume Cosmos DB throughput concepts (RU/s autoscale) map directly to Azure DocumentDB; instead, size compute tier for IOPS/throughput because IOPS are gated by compute (Premium SSD v2) rather than disk size.
- **Source:** [documentdb-storage](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/storage/SKILL.md)

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Create one shared MongoClient per process (singleton) and reuse it across modules; do not create a new client per request. | connection | prior_knowledge_confirmed | documentdb-driver (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md | documentdb-driver | yes |
| P02 | Read the cluster connection URI and all credentials from environment variables or a secrets store and never commit credentials into source or logs. | secrets | prior_knowledge_confirmed | documentdb-local-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md | documentdb-local-deployment | yes |
| P03 | Always use TLS for connections to Azure DocumentDB and do not disable certificate validation in production. | security | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P04 | Tune connection-pool and timeout settings to your environment: choose maxPoolSize/minPoolSize/connectTimeoutMS/socketTimeoutMS according to serverless vs long-running server scenarios and expected concurrency. | connection | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P05 | Use retries for transient errors with exponential backoff and classify errors so non-idempotent operations are not retried blindly; combine driver automatic retryable reads with application-level backoff where appropriate. | retries | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P06 | Design compound indexes using the ESR rule (Equality → Sort → Range) so abandonment queries (filters + sort) are index-supported and avoid blocking in-memory sorts. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P07 | Use projections and covered queries to return only fields needed for orchestration to reduce network and memory usage; design covering indexes when appropriate. | queries | prior_knowledge_confirmed | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | documentdb-query-optimizer | yes |
| P08 | Keep a small index budget per collection (review with $indexStats) and avoid creating many unused indexes; drop or hide unused indexes after verification. | indexing | found_in_public_source | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P09 | Prefer the DocumentDB full-text search (`createSearchIndexes` + $search) and its textSearch indexes for lexical search rather than the community `$text` operator. | indexing | found_in_public_source | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | no |
| P10 | Enable diagnostic settings and slow-query logging, route logs to Log Analytics, and use explain("executionStats") to identify COLLSCANs and high docsExamined to guide index changes. | operations | prior_knowledge_confirmed | documentdb-monitoring (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md | documentdb-monitoring | yes |
| P11 | For vector search, choose the index type by scale: prefer DiskANN for large production corpora, HNSW for mid-scale, and IVF only for small datasets; declare dimensions and similarity and tune lBuild/lSearch parameters. | vector search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | no |
| P12 | Normalize embeddings at ingestion when using cosine similarity, store embedding model metadata and dims with the document, and validate dimensionality on writes. | vector search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | no |
| P13 | Use HA (availability-zone enabled) for production clusters to get automatic in-region failover and the 99.99% SLA; add cross-region replica clusters when you need cross-region DR and a 99.995% SLA. | high availability | found_in_public_source | documentdb-high-availability (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/high-availability/SKILL.md | documentdb-high-availability | no |
| P14 | Premium SSD v2 decouples IOPS/bandwidth from disk size — size compute for throughput (IOPS) and storage for capacity; IOPS caps are gated by compute tier rather than disk size. | storage | found_in_public_source | documentdb-storage (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/storage/SKILL.md | documentdb-storage | no |
| P15 | Do not index high-cardinality free-text fields by default; review index cardinality and prefer specialized text search or external search for heavy full-text workloads. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P16 | When performing vector similarity queries, limit topK and tune approximate search parameters (lSearch/ef) to control latency and resource usage, and combine vector search with pre-filters. | vector search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | no |
| P17 | Prefer least-privilege application users and Microsoft Entra ID / RBAC rather than embedding cluster-admin credentials in apps. | security | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P18 | Make seed scripts idempotent — use upserts or existence checks rather than dropping collections so scripts are safe to run repeatedly. | seeding | prior_knowledge_confirmed | documentdb-local-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md | documentdb-local-deployment | yes |
| P19 | Use explain("executionStats") (or MCP explain_operation) and index stats to diagnose query performance and verify index effectiveness before and after changes. | operations | found_in_public_source | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | documentdb-query-optimizer | yes |
| P20 | Avoid creating a separate MongoClient per request in serverless functions: initialize the client outside the handler so it is reused across warm invocations and keep maxPoolSize small (3–5) for serverless instances. | connection | found_in_public_source | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | no |
| P21 | Do not assume Cosmos DB throughput concepts (RU/s autoscale) map directly to Azure DocumentDB; instead, size compute tier for IOPS/throughput because IOPS are gated by compute (Premium SSD v2) rather than disk size. | provisioning | prior_knowledge_contradicted | documentdb-storage (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/storage/SKILL.md | documentdb-storage | no |
| P22 | Do not index a low-cardinality boolean alone expecting good selectivity; combine it in a compound index with a more-selective field so the index is useful for filtering. | indexing | found_in_public_source | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |

## Searches that returned nothing useful

- Azure DocumentDB idempotent logging best practices
- Azure DocumentDB bulkWrite best practices batching RU consumption
- Azure DocumentDB guidance: should I store LLM/API keys in the database
- Azure DocumentDB multi-document transactions support guidance
- Azure DocumentDB collection validator schema enforcement docs (search for "validator")
- Azure DocumentDB graceful shutdown Node.js SIGINT SIGTERM examples
- Azure DocumentDB retryWrites=false recommendation (search for explicit guidance)

## Notes

I used the installed DocumentDB skills (documentdb-connection, documentdb-driver, documentdb-indexing, documentdb-query-optimizer, documentdb-vector-search, documentdb-security, documentdb-local-deployment, documentdb-monitoring, documentdb-storage, documentdb-high-availability) as the public sources of guidance; those skills represent the product documentation and were loaded as part of open discovery. Where the repository itself shows a practice (e.g., idempotent seed upserts in src/seed.js and .env.example), that evidence is in the workspace but not treated as an external public documentation page. Prior beliefs that are not present in Azure DocumentDB public guidance have been marked prior_knowledge_only and listed in searches_with_no_useful_result (these are the searches I tried before concluding the public record did not support them).

Prior beliefs the discovery step did not classify: K06, K09, K12, K16, K17, K19, K20, K21, K22, K25. See 05a-prior-beliefs.json.

