# 5a. Best practices: prior knowledge against the public record: 13-basel-iii-capital-ratio-calculator

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**20 practices, 19 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 0 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 1 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 16 | Memory and documentation line up. |
| Found in public sources only | 3 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

## Known to the model, with no public source for this service

| Id | Practice | Knowledge of | Searches tried |
|---|---|---|---|
| P17 | Avoid sending raw PII or sensitive balance-level data to external LLM services; minimize exposure by sending de-identified aggregates or running LLMs in an approved, private environment. | general | searches: "Azure DocumentDB LLM PII guidance", "Azure DocumentDB privacy LLM" |

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Read the MongoDB-style connection string from an environment variable (e.g., DOCUMENTDB_URI) and do not hard-code, log, or commit it; publish a .env.example with placeholders instead. | connection & secrets | prior_knowledge_confirmed | Quickstart: Use Azure DocumentDB with MongoDB driver for Python (public_doc) | https://learn.microsoft.com/azure/documentdb/quickstart-python#code-examples | Azure DocumentDB MongoDB connection string example tls=true (learn.microsoft.com) / Quickstart: Use Azure DocumentDB with MongoDB driver for Python | yes |
| P02 | Always require TLS on the wire (e.g., tls=true or equivalent driver option) and validate server certificates when connecting to an Azure DocumentDB cluster. | connection & security | prior_knowledge_confirmed | Quickstart: Use Azure DocumentDB with MongoDB driver for Python (public_doc) | https://learn.microsoft.com/azure/documentdb/quickstart-python#code-examples | Azure DocumentDB MongoDB TLS SCRAM-SHA-256 connection string mongodb+srv tls=true | yes |
| P03 | Store connection strings and other secrets in a managed secret store (e.g., Azure Key Vault) or inject them as environment-only values rather than embedding them in code or repository files. | secrets | prior_knowledge_confirmed | Secure your Azure Key Vault secrets (public_doc) | https://learn.microsoft.com/azure/key-vault/secrets/secure-secrets | Azure Key Vault store connection strings best practices | yes |
| P04 | Create a single MongoClient per process (singleton) and reuse it rather than creating a new client per request; configure pool parameters only after understanding app concurrency patterns. | driver & connection | found_in_public_source | documentdb-driver (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md | documentdb-driver | yes |
| P05 | Tune connection-pool and timeout settings to match your runtime (serverless vs long-running servers vs OLAP) and initialize the client outside the request/handler scope to enable reuse (serverless: small maxPoolSize, short maxIdleTimeMS). | connection | found_in_public_source | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P06 | Implement retries with exponential backoff for transient network or rate-limit errors and make aggregation/write operations idempotent or detect duplicates to avoid double-counting. | retries | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P07 | Perform numeric aggregations server-side using the aggregation pipeline (db.collection.aggregate with $group and accumulators) rather than fetching documents and summing client-side to reduce network and I/O cost. | queries & performance | prior_knowledge_confirmed | Aggregation - commands (public_doc) | https://learn.microsoft.com/documentdb/query/commands/aggregation/ | Azure DocumentDB aggregation pipeline guidance (learn.microsoft.com) / aggregate command docs | yes |
| P08 | Order aggregation pipeline stages to filter early: place $match first, then $project to keep only required numeric fields, then $group to minimize documents and memory use; verify plan/index usage with explain("executionStats"). | queries & performance | prior_knowledge_confirmed | documentdb-query-optimization (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimization/SKILL.md | documentdb-query-optimization | yes |
| P09 | Use explain("executionStats") and server-side profiling / slow-query logs to confirm index usage and detect COLLSCANs; tune indexes or pipeline ordering when keysExamined/docsExamined indicate inefficiency. | observability & performance | prior_knowledge_confirmed | documentdb-query-optimization (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimization/SKILL.md | documentdb-query-optimization | yes |
| P10 | Store monetary and regulatory numeric values using Decimal128 (or other fixed-point/decimal types) and use aggregation operators like $toDecimal / $convert when needed to avoid floating-point rounding errors. | data_modeling | prior_knowledge_confirmed | $toDecimal (public_doc) | https://learn.microsoft.com/documentdb/query/operators/aggregation/$todecimal#examples | Azure DocumentDB $toDecimal / $convert aggregation operator docs | yes |
| P11 | Create indexes that support the aggregation pipeline (equality fields first, then sort/range) — prefer one well-shaped compound index over many single-field indexes and keep a modest per-collection index budget. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P12 | Prefer DocumentDB's search path: create search indexes with createSearchIndexes and query with $search (textSearch / BM25) rather than relying on the community $text index. | full-text search & indexing | found_in_public_source | documentdb-full-text-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/full-text-search/SKILL.md | documentdb-full-text-search | no |
| P13 | When using vector search, store vectors in a dedicated numeric array field, normalize embeddings for cosine similarity, and create a provider-specific cosmosSearch vector index (DiskANN/HNSW/IVF) with tuned parameters (dimensions, lBuild/lSearch, maxDegree, efConstruction/efSearch). | vector_search & indexing | prior_knowledge_confirmed | Integrated vector store in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/vector-search#perform-vector-similarity-search | Azure DocumentDB vector search DiskANN HNSW IVF guidance (learn.microsoft.com) / integrated vector store | no |
| P14 | Limit vector index dimensionality and cardinality and use product quantization or half-precision (fp16) when appropriate to reduce memory and build cost and keep index performance predictable. | vector_search | prior_knowledge_confirmed | Integrated vector store in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/vector-search#perform-vector-similarity-search | Azure DocumentDB vector search guidance (learn.microsoft.com) / integrated vector store | no |
| P15 | Shard only when a collection's storage or throughput exceeds a single physical shard's budget; choose a shard key that matches the most common read filter for read-heavy workloads or the highest-cardinality evenly-distributed field for write-heavy workloads to avoid hot partitions. | provisioning & scalability | prior_knowledge_confirmed | documentdb-sharding (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/sharding/SKILL.md | documentdb-sharding | no |
| P16 | Seed sample data idempotently (use upserts or bulk_write upserts) and, for ephemeral test data, consider TTL indexes so repeated runs do not accumulate test artifacts. | data loading & testing | prior_knowledge_confirmed | documentdb-local-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md | documentdb-local-deployment | yes |
| P17 | Avoid sending raw PII or sensitive balance-level data to external LLM services; minimize exposure by sending de-identified aggregates or running LLMs in an approved, private environment. | LLM & privacy | prior_knowledge_only | - (prior_knowledge) | **none** | searches: "Azure DocumentDB LLM PII guidance", "Azure DocumentDB privacy LLM" | yes |
| P18 | Enable diagnostic settings and collect slow-query logs and cluster metrics (CPU, memory, IOPS, storage, connection saturation) into Log Analytics; create alerts for throttling, slow queries, and resource saturation. | monitoring | prior_knowledge_confirmed | documentdb-monitoring (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md | documentdb-monitoring | yes |
| P19 | Prefer least-privilege credentials (Azure Entra ID / RBAC or per-app users) rather than a single full-access account key; rotate and revoke credentials used for test runs. | security | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P20 | Compute numerators and denominators together on the server (single aggregation pipeline or transaction where supported) to avoid inconsistent snapshots across multiple client queries; when multi-document transactions aren't available (sharded collections) prefer single-pipeline aggregations. | correctness & queries | prior_knowledge_confirmed | Aggregation - commands (public_doc) | https://learn.microsoft.com/documentdb/query/commands/aggregation/ | Azure DocumentDB aggregation / transaction docs; search: "Azure DocumentDB aggregate atomic snapshot" | yes |

## Searches that returned nothing useful

- Azure DocumentDB readConcern writeConcern guidance (tried to find explicit guidance for DocumentDB mapping of readConcern/writeConcern)
- Azure DocumentDB guidance explicitly forbidding sending PII to external LLMs (searched for service-specific LLM/PII guidance)

## Notes

Discovery combined official Microsoft docs (learn.microsoft.com) and the installed DocumentDB skills. I loaded domain skills (documentdb-connection, documentdb-driver, documentdb-indexing, documentdb-query-optimization, documentdb-vector-search, documentdb-security, documentdb-sharding, documentdb-monitoring, documentdb-local-deployment, documentdb-data-modeling, documentdb-full-text-search) and used Microsoft Learn search results for connection, aggregation, Decimal128, and vector-search pages. Each prior belief (K01..K20) was checked: most were confirmed by public DocumentDB docs or the installed skills; K09 (explicit guidance on setting readConcern/writeConcern for Azure DocumentDB) and K16 (service-specific guidance about sending PII to external LLMs) had no Azure DocumentDB page directly supporting or contradicting the belief and are marked prior_knowledge_only.

Prior beliefs the discovery step did not classify: K04, K06, K09. See 05a-prior-beliefs.json.

