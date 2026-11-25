# 5a. Best practices: prior knowledge against the public record: 11-visual-similarity-search-image-embeddings

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**24 practices, 23 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 2 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 1 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 17 | Memory and documentation line up. |
| Found in public sources only | 4 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

## Where public sources contradict the model

### P05: Store vectors as a JSON numeric array (number[]) in the document field so they can be indexed by cosmosSearch; non-number types (or unsupported encodings) may prevent a document from being indexed.

- **The model believed:** Store vector embeddings as a fixed-length float32 array with an explicit binary BSON subtype (use the provider-supported subtype, e.g., 0x09 if the server expects it), and record the embedding dimension in the document schema to validate clients (e.g., {embeddingDim:512}). (knowledge of `mongodb`)
- **The source says:** Store vectors as a JSON numeric array (number[]) in the document field so they can be indexed by cosmosSearch; non-number types (or unsupported encodings) may prevent a document from being indexed.
- **Source:** [Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-ivf-index)

### P17: Prefer storing vectors as arrays of numeric values (float32/float16) in fields and use the documented vector-field encodings/options (float types, half/quantization) rather than relying on an undocumented BSON binary packing; verify encoding support in the service docs before using a binary subtype.

- **The model believed:** When packing embeddings into BSON binary ensure byte order and type match server expectations (float32 little-endian); use a consistent serializer (e.g., numpy.astype('float32').tobytes()) and validate roundtrip reads in tests. (knowledge of `mongodb`)
- **The source says:** Prefer storing vectors as arrays of numeric values (float32/float16) in fields and use the documented vector-field encodings/options (float types, half/quantization) rather than relying on an undocumented BSON binary packing; verify encoding support in the service docs before using a binary subtype.
- **Source:** [Integrated vector store in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-ivf-index)

## Known to the model, with no public source for this service

| Id | Practice | Knowledge of | Searches tried |
|---|---|---|---|
| P10 | Do not return full embedding vectors in API responses by default; return only metadata and a score unless clients explicitly need the raw embedding. | general | embeddings API response do not return embeddings best practice |

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Do not hard-code the cluster connection string or keys in source; read the connection string from environment variables or a secrets store such as Azure Key Vault and keep only a .env.example or placeholder in repo. | secrets | prior_knowledge_confirmed | Secure your Azure Key Vault secrets (public_doc) | https://learn.microsoft.com/azure/key-vault/secrets/secure-secrets | Azure Key Vault connection string best practices | yes |
| P02 | Create a single MongoClient and reuse it for the lifetime of the process (singleton client pattern); do not instantiate a new client per request. | connection | prior_knowledge_confirmed | documentdb-driver (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md | documentdb-driver | yes |
| P03 | Always connect with TLS enabled (tls=true) and validate server certificates in production; Azure DocumentDB requires TLS. | connection | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P04 | Implement retries for transient errors (e.g., 429, 503, network timeouts) with exponential backoff and jitter; rely on the driver's retryable-reads when available and respect Retry-After when provided. | retries | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P05 | Store vectors as a JSON numeric array (number[]) in the document field so they can be indexed by cosmosSearch; non-number types (or unsupported encodings) may prevent a document from being indexed. | data_modeling | prior_knowledge_contradicted | Integrated vector store in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-ivf-index | Azure DocumentDB vector index example using IVF | yes |
| P06 | If you use cosine similarity, L2-normalize embeddings at encode time (and store model+dimension metadata with vectors) so queries use the same normalization and the index returns consistent similarity scores. | vector_search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | yes |
| P07 | Choose an index type that matches your scale (vector-ivf / vector-hnsw / vector-diskann) and configure algorithm parameters (dimensions, numLists/nProbes for IVF or m/efConstruction/efSearch for HNSW) rather than relying on defaults. | indexing | prior_knowledge_confirmed | Integrated vector store in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-ivf-index | Azure DocumentDB vector index examples (IVF/HNSW/DiskANN) | yes |
| P08 | Create vector/search indexes before bulk-loading production data and wait (or use the blocking option) for the index build to complete; track build progress with db.currentOp/listIndexes before running heavy queries. | indexing | prior_knowledge_confirmed | Indexing Best Practices in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/how-to-create-indexes#track-the-status-of-a-createindex-operation | Azure DocumentDB createIndexes and tracking index build status | yes |
| P09 | For bulk ingestion use batched writes (insert_many / bulk_write) with unordered writes (ordered=false) and tuned batch sizes (client guidance ~500–1000 per batch or use SDK bulk modes) instead of per-document inserts. | provisioning | prior_knowledge_confirmed | Tips for optimizing vector indexing & search performance (public_doc) | https://learn.microsoft.com/azure/cosmos-db/gen-ai/vector-search-performance-tips#tips-for-optimizing-insert-throughput | Azure DocumentDB vector search performance tips: bulk ingestion | yes |
| P10 | Do not return full embedding vectors in API responses by default; return only metadata and a score unless clients explicitly need the raw embedding. | operations | prior_knowledge_only | - (prior_knowledge) | **none** | embeddings API response do not return embeddings best practice | yes |
| P11 | Put the $search aggregation stage first in any aggregation pipeline that uses DocumentDB search (including cosmosSearch vector queries); the search index narrows candidate set before other stages. | queries | prior_knowledge_confirmed | Full-text search in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/full-text-search-overview#how-azure-documentdb-full-text-search-works | $search must be the first stage guidance | yes |
| P12 | When issuing a vector similarity query include a server-side top-k limit (k) and use the index scoring (searchScore) so the engine returns the top-k ordered by similarity instead of sorting client-side. | queries | prior_knowledge_confirmed | Integrated vector store in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-hnsw-index | vector search k parameter example | yes |
| P13 | Prefer the provider's native vector-search operator (cosmosSearch via $search) for kNN retrieval rather than brute-force client-side distance computations. | vector_search | prior_knowledge_confirmed | Integrated vector store in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/vector-search | Azure DocumentDB vector search overview | yes |
| P14 | Tune cluster/collection throughput (cluster tier or autoscale) to account for vector indexing and query costs; monitor resource consumption (CPU, memory, IOPS) and scale up or enable autoscale for ingestion/indexing bursts. | provisioning | prior_knowledge_confirmed | Tips for optimizing vector indexing & search performance (public_doc) | https://learn.microsoft.com/azure/cosmos-db/gen-ai/vector-search-performance-tips#tips-for-optimizing-insert-throughput | vector indexing throughput and autoscale guidance | yes |
| P15 | For local development and CI keep credentials out of logs and repository files; provide a .env.example and drive connection settings from environment variables or Key Vault references. | secrets | prior_knowledge_confirmed | documentdb-local-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md | documentdb-local-deployment | yes |
| P16 | Measure approximate-index recall by comparing index results to brute-force (small validation set) and adjust index/query parameters (nProbes, efSearch, oversampling) if recall is insufficient. | vector_search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | yes |
| P17 | Prefer storing vectors as arrays of numeric values (float32/float16) in fields and use the documented vector-field encodings/options (float types, half/quantization) rather than relying on an undocumented BSON binary packing; verify encoding support in the service docs before using a binary subtype. | data_modeling | prior_knowledge_contradicted | Integrated vector store in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-ivf-index | Azure DocumentDB vector index and 'Vectors must be a number[]' guidance | yes |
| P18 | Avoid storing large images or binary blobs inside DocumentDB documents; store image blobs in Azure Blob Storage and keep only URLs/metadata/embeddings in the database. | data_modeling | prior_knowledge_confirmed | Optimize storage cost in Azure Cosmos DB (recommend storing media in Blob Storage) (public_doc) | https://learn.microsoft.com/azure/cosmos-db/optimize-cost-storage#optimize-cost-with-rich-media-data-types | store images in blob storage best practice | yes |
| P19 | Capture server error payloads and inspect query plans (explain / currentOp); use explain/profile/diagnostic logs to troubleshoot vector-query failures and index usage. | operations | prior_knowledge_confirmed | Indexing Best Practices in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/how-to-create-indexes#track-the-status-of-a-createindex-operation | index build tracking and db.currentOp / explain references | yes |
| P20 | Protect the database at the network level (IP firewall rules, Private Endpoint/VNet) and use least-privilege credentials or Microsoft Entra authentication / RBAC instead of long-lived cluster admin keys. | security | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P21 | When creating an IVF vector index set numLists appropriately (e.g., ~documentCount/1000 for up to 1M docs; increase numLists as dataset grows) and tune nProbes/efSearch at query time to trade recall vs latency. | indexing | found_in_public_source | Integrated vector store in Azure DocumentDB (IVF guidance) (public_doc) | https://learn.microsoft.com/azure/documentdb/vector-search#example-using-an-ivf-index | Azure DocumentDB IVF numLists tuning guidance | yes |
| P22 | For HNSW tune m and efConstruction at index-build time and efSearch at query time (higher values improve recall but increase build time / memory or query latency); consider DiskANN for very large corpora. | indexing | found_in_public_source | Integrated vector store in Azure DocumentDB (HNSW / DiskANN guidance) (public_doc) | https://learn.microsoft.com/azure/documentdb/vector-search#example-using-a-diskann-index-with-filtering | Azure DocumentDB HNSW/DiskANN tuning guidance | yes |
| P23 | Project the similarity score from $search using { score: { $meta: 'searchScore' } } in a downstream $project stage to return relevance scores with documents. | queries | found_in_public_source | Integrated vector store in Azure DocumentDB (project searchScore) (public_doc) | https://learn.microsoft.com/azure/documentdb/vector-search#perform-a-vector-search-with-ivf | Azure DocumentDB $search and searchScore example | yes |
| P24 | Wait until a search/index reports status READY/queryable (via $listSearchIndexes or listIndexes/getIndexes) before running production queries that depend on it. | indexing | found_in_public_source | BM25 keyword search / listing search indexes (public_doc) | https://learn.microsoft.com/azure/documentdb/full-text-search-keyword#listing-and-inspecting-search-indexes | listSearchIndexes and status: READY guidance | yes |

## Searches that returned nothing useful

- bson subtype 0x09 Azure DocumentDB vector binary subtype 0x09
- float32 little-endian BSON subtype 0x09 Azure DocumentDB packing embedding binary
- do not return embeddings in API responses Azure DocumentDB best practice

## Notes

I inspected the sample app and the installed DocumentDB skills, and searched Microsoft documentation for Azure DocumentDB vector-search and related guidance. Most prior beliefs K01..K04, K06..K09, K11..K16, K18..K20 were confirmed by Azure DocumentDB public documentation or the installed DocumentDB skills. Two prior beliefs were contradicted by the public record for Azure DocumentDB: K05 (the public docs require numeric arrays for vectors / documented encodings rather than an undocumented BSON binary subtype) and K17 (there is no public guidance endorsing arbitrary BSON binary float32 packing; the public docs emphasize vector arrays and documented encodings). K10 (do not return embeddings in API responses) had no Azure DocumentDB public documentation explicitly addressing it, so it is recorded as prior_knowledge_only with the searches attempted.

