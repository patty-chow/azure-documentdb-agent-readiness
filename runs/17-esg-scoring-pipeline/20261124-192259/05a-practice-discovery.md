# 5a. Best practices: prior knowledge against the public record: 17-esg-scoring-pipeline

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**20 practices, 19 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 1 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 1 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 18 | Memory and documentation line up. |
| Found in public sources only | 0 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

## Where public sources contradict the model

### P05: Store rationale text and the embedding as a numeric array field on the same document; ensure the embedding is stored as a number[] and also persist embedding model name and dimension metadata alongside the vector.

- **The model believed:** Store the LLM rationale text and a separate embedding vector field (e.g., rationale_embedding: [float]) in the same document; keep vector field name and embedding dimension consistent across documents and persist type as float32 arrays (or BSON arrays of floats). (knowledge of `general`)
- **The source says:** Store rationale text and the embedding as a numeric array field on the same document; ensure the embedding is stored as a number[] and also persist embedding model name and dimension metadata alongside the vector.
- **Source:** [Vector normalize embeddings guidance (Azure DocumentDB)](https://learn.microsoft.com/azure/documentdb/vector-search#vector-normalize-embeddings)

## Known to the model, with no public source for this service

| Id | Practice | Knowledge of | Searches tried |
|---|---|---|---|
| P10 | Use bulk writes (for example PyMongo bulk_write) to improve throughput when updating many documents, and handle BulkWriteError and examine upserted_ids for idempotency verification. | mongodb | Searches tried: 'Azure DocumentDB bulk_write pymongo bulk_write', 'Azure DocumentDB bulk writes best practices', 'Azure DocumentDB bulk_write guidance'; no Azure DocumentDB public page recommending bulk_write was found |

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Read the MongoDB-compatible connection URI from an environment variable and create one process-wide MongoClient (singleton) with TLS enabled and appropriately bounded pool size and timeouts for your runtime. | connection | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P02 | Keep secrets out of the repository: place the DocumentDB connection URI and any LLM/embedding API keys in environment variables or a secrets store (for example, use managed identities/Entra or Key Vault) and provide only a .env.example with placeholders. | authentication_and_secrets | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P03 | Make seed operations idempotent by upserting via a deterministic key (for example name or company_id) using update/upsert or $setOnInsert so repeated runs don't create duplicates. | seeding | prior_knowledge_confirmed | Quickstart: Use Azure DocumentDB with MongoDB driver for Python (public_doc) | https://learn.microsoft.com/azure/documentdb/quickstart-python#code-examples | Azure DocumentDB quickstart python upsert | yes |
| P04 | For read-heavy ranking and sorting workloads, store E, S, G pillar scores as small integers and denormalize by persisting a precomputed composite (aggregate) score on each document to support fast sorting/aggregation. | data_modeling | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P05 | Store rationale text and the embedding as a numeric array field on the same document; ensure the embedding is stored as a number[] and also persist embedding model name and dimension metadata alongside the vector. | data_modeling | prior_knowledge_contradicted | Vector normalize embeddings guidance (Azure DocumentDB) (public_doc) | https://learn.microsoft.com/azure/documentdb/vector-search#vector-normalize-embeddings | Azure DocumentDB vector embedding storage and metadata | yes |
| P06 | Create indexes that match your query patterns: add a unique index on an identifier (e.g., name/company_id), an index on schemaVersion, and create a descending index on any precomputed composite score or a compound index matching common filter+sort shapes to avoid blocking sorts. | indexing | prior_knowledge_confirmed | Manage indexing in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/how-to-create-indexes#for-multiple-indexes-created-on-historical-data,-issue-nonblocking-createindex-commands-for-each-field | Azure DocumentDB indexing best practices compound index ESR | yes |
| P07 | When using server-side vector search, create a cosmosSearch vector index on the embedding field with the chosen kind (vector-diskann/vector-hnsw/vector-ivf), the exact embedding dimension, and the similarity metric you will use at query time. | vector_search | prior_knowledge_confirmed | Integrated vector store in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-hnsw-index | Azure DocumentDB vector index createIndexes cosmosSearch | yes |
| P08 | If you use cosine similarity for vector search, L2-normalize embeddings at ingestion and store the embedding model name and dimensions so queries and indexes use a consistent metric and shape. | vector_search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | yes |
| P09 | Tune vector-index creation parameters (for example DiskANN lBuild/lSearch/maxDegree, HNSW m/efConstruction, IVF numLists) to balance recall and build/query cost and expect index builds to be resource-intensive; choose DiskANN for large corpora, HNSW for mid-size, and IVF for small demos. | vector_search | prior_knowledge_confirmed | Integrated vector store in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/vector-search#perform-vector-similarity-search | Azure DocumentDB vector index tuning DiskANN HNSW IVF | yes |
| P10 | Use bulk writes (for example PyMongo bulk_write) to improve throughput when updating many documents, and handle BulkWriteError and examine upserted_ids for idempotency verification. | seeding | prior_knowledge_only | - (prior_knowledge) | **none** | Searches tried: 'Azure DocumentDB bulk_write pymongo bulk_write', 'Azure DocumentDB bulk writes best practices', 'Azure DocumentDB bulk_write guidance'; no Azure DocumentDB public page recommending bulk_write was found | yes |
| P11 | Implement retries with exponential backoff for transient network and throttling errors (honor Retry-After when provided and handle 429/TooManyRequests), and make operations idempotent where possible. | retries | prior_knowledge_confirmed | Troubleshoot TooManyRequestsReceived (429) / Azure guidance (public_doc) | https://learn.microsoft.com/azure/cosmos-db/troubleshoot-request-rate-too-large#rate-limiting-on-metadata-requests | Azure DocumentDB 429 TooManyRequests handling | yes |
| P12 | Provision adequate cluster throughput (or enable autoscale) for your expected embedding upserts and vector-index builds and monitor normalized RU consumption and throttling (429) to scale up when needed. | provisioning | prior_knowledge_confirmed | Autoscale for Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/autoscale | Azure DocumentDB autoscale and throughput guidance | yes |
| P13 | Avoid very large documents and stay well under the service's per-document BSON size limit (plan for growth and split very large blobs into side collections), keeping vectors+text+metadata sized appropriately. | data_modeling | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling model-16mb-limit | yes |
| P14 | Update embedding vectors and computed scores in a single document-level update (single update/upsert) to preserve atomicity and avoid inconsistent states between score and embedding. | queries | prior_knowledge_confirmed | findAndModify / single-document atomic operations guidance (public_doc) | https://learn.microsoft.com/documentdb/query/commands/query-and-write/findandmodify | Azure DocumentDB single-document atomic update findAndModify | yes |
| P15 | Store a schemaVersion and processing metadata (for example last_updated timestamp or processing_status) on each document so pipelines can resume, perform lazy migrations, and avoid reprocessing already-scored documents. | data_modeling | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling model-schema-versioning | yes |
| P16 | In aggregation pipelines, $match early to pre-filter documents before $addFields/$project, and design indexes (for example via compound ESR rule) so $sort can be covered by an index to avoid in-memory sorts; paginate using range queries rather than unbounded $skip where possible. | queries | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing index-compound-esr | yes |
| P17 | Restrict network access to the cluster via firewall rules or Private Endpoint and prefer Microsoft Entra ID / RBAC or per-application least-privilege users rather than embedding account-level admin credentials in app code. | security | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security security-entra-rbac | yes |
| P18 | Enable diagnostic settings and slow-query logs, export metrics to Log Analytics/Azure Monitor, and alert on CPU/memory/IOPS/storage/connection saturation and normalized RU consumption to detect 429 throttling and index-build impact. | monitoring | prior_knowledge_confirmed | documentdb-monitoring (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md | documentdb-monitoring monitoring-slow-query-log | yes |
| P19 | When using the integrated vector store, prefer storing embeddings as arrays on the same document as the source text (one vector path per document) so the server-side vector index (cosmosSearch) can index and filter by metadata in the same document. | data_modeling | prior_knowledge_confirmed | Use LangChain on Azure with Azure DocumentDB (integration notes) (public_doc) | https://learn.microsoft.com/azure/documentdb/build-rag-applications#langchain-azure-documentdb-integration | Azure DocumentDB LangChain integration and vector store guidance | yes |
| P20 | For development and tests, run DocumentDB locally (Gateway Docker) or use a test database and small synthetic datasets, drive connection config via env vars, and make seed/teardown scripts idempotent to avoid polluting production throughput and data. | testing | prior_knowledge_confirmed | documentdb-local-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md | documentdb-local-deployment local-env-driven-config | yes |

## Searches that returned nothing useful

- Azure DocumentDB bulk_write pymongo bulk_write
- Azure DocumentDB best practices bulk writes 'bulkWrite' 'bulk_write' 'BulkWriteError'

## Notes

I scanned the repository to see what the sample uses (singleton MongoClient, environment-configured DOCUMENTDB_URI, upsert seeding, bulk_write in processing, storing rationale_embedding, aggregation precompute) and then consulted installed DocumentDB skills and official Microsoft docs (vector-search, indexing, quickstarts, autoscale, monitoring, and 429 troubleshooting). Where the public Azure DocumentDB documentation explicitly matched a prior belief I marked it confirmed; where the docs said something different I marked the belief contradicted (K05); where no Azure DocumentDB public guidance was found (bulk write details) I marked prior_knowledge_only and listed the queries tried.

