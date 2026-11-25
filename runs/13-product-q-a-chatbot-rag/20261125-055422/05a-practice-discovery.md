# 5a. Best practices: prior knowledge against the public record: 13-product-q-a-chatbot-rag

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**19 practices, 17 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 1 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 0 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 14 | Memory and documentation line up. |
| Found in public sources only | 4 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

## Where public sources contradict the model

### P09: Prefer DocumentDB's search index and $search aggregation (createSearchIndexes) for full-text features (BM25, fuzzy, phrase, custom analyzers) rather than relying on community MongoDB text indexes and $text.

- **The model believed:** Create a scalar/index on commonly filtered fields such as product_id and any category/tags used for filtering, and create a text index for fallback keyword matching on chunk text (e.g., db.product_chunks.createIndex({text: 'text'})). (knowledge of `mongodb`)
- **The source says:** Prefer DocumentDB's search index and $search aggregation (createSearchIndexes) for full-text features (BM25, fuzzy, phrase, custom analyzers) rather than relying on community MongoDB text indexes and $text.
- **Source:** [Full-text search in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/full-text-search-overview#how-azure-documentdb-full-text-search-works)

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Create one long-lived MongoClient per process (singleton) and reuse it rather than opening a new client per request. | connection | prior_knowledge_confirmed | Quickstart: Use Azure DocumentDB with MongoDB driver for Python (public_doc) | https://learn.microsoft.com/azure/documentdb/quickstart-python#code-examples | Azure DocumentDB MongoDB driver quickstart connection examples | yes |
| P02 | Keep the DocumentDB connection string and credentials out of source control; read DOCUMENTDB_URI from environment (or an uncommitted config) and never log secrets. | secrets | prior_knowledge_confirmed | Quickstart: Use Azure DocumentDB with MongoDB driver for Python (public_doc) | https://learn.microsoft.com/azure/documentdb/quickstart-python#code-examples | Azure DocumentDB connection string quickstart; search: "Azure DocumentDB connection string quickstart .env" | yes |
| P03 | For production, store DB credentials or secrets in a managed secret store such as Azure Key Vault rather than embedding primary keys in code or sample fixtures. | secrets | prior_knowledge_confirmed | Migrate from Amazon DocumentDB to Azure DocumentDB (with MongoDB compatibility) (public_doc) | https://learn.microsoft.com/azure/documentdb/migrate-amazon-documentdb#update-your-application | Azure DocumentDB migration guidance; search: "store connection string Azure Key Vault DocumentDB" | yes |
| P04 | Always use TLS for client connections and restrict network access with firewall rules or Private Endpoints/Private Link; prefer private connectivity for production clusters. | security | prior_knowledge_confirmed | Azure DocumentDB FAQ (Connectivity & Security) (public_doc) | https://learn.microsoft.com/azure/documentdb/faq#how-do-clients-connect-to-an-azure-documentdb-cluster | Azure DocumentDB security/connectivity FAQ; search: "Azure DocumentDB TLS Private Link firewall" | yes |
| P05 | When building a RAG pipeline, store each chunk with document identifiers, chunk id, chunk text, embedding (if present), and metadata (title/source) so you can filter, attribute and retrieve without re-reading original documents. | data_modeling | prior_knowledge_confirmed | Retrieval-augmented generation (RAG) with Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/rag | search: "Azure DocumentDB RAG chunk metadata" | yes |
| P06 | When running a vector kNN ($search with cosmosSearch), push structured predicates into the search (filter/pre_filter) so filtering happens inside the ANN search rather than post-filtering client-side. | queries | prior_knowledge_confirmed | documentdb-vector-search (vector-knn-query.md) (installed_skill) | **none** | documentdb-vector-search | yes |
| P07 | Store vectors as dense numeric arrays (number[]) so they are indexable by DocumentDB; include the embedding model name and the vector dimension as metadata so queries can validate compatibility. | vector_search | prior_knowledge_confirmed | Integrated vector store in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/vector-search#perform-vector-similarity-search | Azure DocumentDB vector search docs; search: "vectors must be number[] Azure DocumentDB" | yes |
| P08 | When creating vector indexes, pick the algorithm and parameters to match scale (vector-ivf for small demos, vector-hnsw for medium datasets, vector-diskann for large production), set the similarity metric that matches your query-time scoring, and tune index parameters (numLists / m / efConstruction / lSearch / maxDegree) to balance recall and latency. | vector_search | prior_knowledge_confirmed | Integrated vector store in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/vector-search#perform-vector-similarity-search | search: "Azure DocumentDB vector index DiskANN HNSW IVF tuning" | yes |
| P09 | Prefer DocumentDB's search index and $search aggregation (createSearchIndexes) for full-text features (BM25, fuzzy, phrase, custom analyzers) rather than relying on community MongoDB text indexes and $text. | indexing | prior_knowledge_contradicted | Full-text search in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/full-text-search-overview#how-azure-documentdb-full-text-search-works | search: "Azure DocumentDB full-text search createSearchIndexes vs text index" | yes |
| P10 | Use explain()/query plan output and the DocumentDB tooling (Index Advisor / MCP list_indexes / explain) to verify index definitions, confirm index usage, and detect COLLSCANs or index-misses. | indexing | prior_knowledge_confirmed | Azure DocumentDB MCP Toolkit / How to read explain output (public_doc) | https://learn.microsoft.com/azure/documentdb/mcp-toolkit#tool-catalog | search: "MCP Toolkit list_indexes explain_operation DocumentDB" | yes |
| P11 | Implement retries for transient faults with exponential backoff and jitter, and make write operations idempotent (upserts or client-generated idempotency tokens) if they will be retried. | retries | prior_knowledge_confirmed | Reliability in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/reliability/reliability-documentdb#resilience-to-transient-faults | search: "Azure DocumentDB transient faults retry exponential backoff" | yes |
| P12 | Monitor index and query performance: enable diagnostic settings/slow-query logs, use explain() and Index Advisor recommendations, and alert on CPU/memory/IOPS/connection saturation for your cluster tier. | monitoring | prior_knowledge_confirmed | Manage indexing in Azure DocumentDB / Index Advisor (public_doc) | https://learn.microsoft.com/azure/documentdb/index-advisor#open-a-query-for-analysis | search: "Index Advisor Azure DocumentDB explain query plan" | yes |
| P13 | Use SDK bulk/ingestion features when ingesting large numbers of documents (AllowBulkExecution / bulk mode where available) or parallel async clients; be aware there are batch/write limits and tune concurrency to avoid throttling. | provisioning | found_in_public_source | Tips for optimizing vector indexing & search performance / bulk execution (public_doc) | https://learn.microsoft.com/azure/cosmos-db/gen-ai/vector-search-performance-tips#tips-for-optimizing-insert-throughput | search: "Azure DocumentDB bulk ingestion AllowBulkExecution bulk mode" | yes |
| P14 | Document size must not exceed 16 MB; design chunking and chunk-size to keep documents well under that limit. | data_modeling | found_in_public_source | Document size and batch write limits in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/max-document-size | search: "Azure DocumentDB max document size 16 MB" | yes |
| P15 | In RAG prompt engineering, retrieve a tuned top-N set of chunks, deduplicate/threshold them, and truncate or summarize the assembled context to fit the LLM token budget before calling the model. | queries | prior_knowledge_confirmed | RAG prompt engineering (Azure architecture guidance) (public_doc) | https://learn.microsoft.com/azure/architecture/ai-ml/guide/rag/rag-prompt-engineering#manage-context-window-and-token-limits | search: "RAG prompt engineering manage context window Azure" | yes |
| P16 | Record provenance metadata (source id, chunk index, source URL/timestamp) with each chunk so answers can cite sources and support traceability for RAG outputs. | data_modeling | prior_knowledge_confirmed | Build RAG applications with Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/build-rag-applications | search: "RAG store provenance metadata Azure DocumentDB" | yes |
| P17 | Prefer Microsoft Entra ID and RBAC for authentication and least-privilege per-application users rather than long-lived primary/master keys; use key rotation and restrict permissions to required DB/collections. | security | prior_knowledge_confirmed | Security — Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/how-to-connect-role-based-access-control | search: "Azure DocumentDB Microsoft Entra ID RBAC least privilege" | yes |
| P18 | Normalize embeddings for cosine similarity (e.g., L2-normalize) and record the embedding model and dimensions with each vector so query-time checks can avoid dimension mismatches. | vector_search | found_in_public_source | documentdb-vector-search (vector-normalize-embeddings.md) (installed_skill) | **none** | documentdb-vector-search | yes |
| P19 | Prefer creating indexes after large bulk ingestion to reduce write-time overhead; plan index lifecycle (hide -> drop) and keep a modest number of indexes per collection. | indexing | found_in_public_source | Indexing Best Practices in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/how-to-create-indexes#queryable-fields-should-always-have-indexes-created | search: "Azure DocumentDB indexing best practices create indexes after data load" | yes |

## Searches that returned nothing useful

- Azure DocumentDB embedding dtype float32 preferred 'float32' 'float16' 'float64'
- Azure DocumentDB recommended insert_many batch size 500 1000 'insert_many batch size' 'best batch size' DocumentDB
- Azure DocumentDB guidance chunk token size 500-1000 tokens 'chunk size tokens' 'RAG chunk size recommendation' site:learn.microsoft.com
- Azure DocumentDB explicit 'fallback to text search when vector index missing' guidance 'vector index not present' 'fallback' site:learn.microsoft.com

## Notes

I searched official Microsoft docs and inspected installed DocumentDB skills. Practices that matched the prior-belief list are marked as confirmed or contradicted; beliefs with no Azure DocumentDB documentation evidence (or where docs do not confirm numeric choices like batch sizes, dtype, or exact chunk-token counts) are reported as prior_knowledge_only entries (those appear under searches_with_no_useful_result and as separate prior_knowledge_only items in the practices list). For skills used as sources I set source_kind to installed_skill and listed the skill name in how_found.

Prior beliefs the discovery step did not classify: K05, K07, K12, K13, K16. See 05a-prior-beliefs.json.

