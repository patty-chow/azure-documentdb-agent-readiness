# 5a. Best practices: prior knowledge against the public record: 04-earnings-call-rag-assistant

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**28 practices, 25 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 1 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 2 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 21 | Memory and documentation line up. |
| Found in public sources only | 4 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

## Where public sources contradict the model

### P24: Azure DocumentDB storage uses premium SSD options and IOPS/bandwidth is gated by compute tier (not RU model); size compute for throughput requirements rather than sizing disk for IOPS.

- **The model believed:** For performance and cost reasons, batch inserts of document+embedding (e.g., 100–1000 docs per bulk insert) rather than inserting one document at a time during ingestion, and monitor RU/throughput or equivalent credits during bulk loads. (knowledge of `azure_cosmos_db`)
- **The source says:** Azure DocumentDB storage uses premium SSD options and IOPS/bandwidth is gated by compute tier (not RU model); size compute for throughput requirements rather than sizing disk for IOPS.
- **Source:** [documentdb-storage](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/storage/SKILL.md)

## Known to the model, with no public source for this service

| Id | Practice | Knowledge of | Searches tried |
|---|---|---|---|
| P25 | Sanitize and normalize text before embedding (strip control characters, normalize whitespace, preserve timestamps) to ensure reproducible chunking and better nearest-neighbor accuracy. | general | azure documentdb chunk sanitize normalize embeddings; documentdb vector search normalize embeddings (checked) but not full sanitization guidance for DocumentDB |
| P26 | Use context-engineering rules to assemble retrieved passages to fit the LLM token budget: rank by vector score, concatenate until budget minus answer buffer is reached, and favor distinct timestamps to improve coverage. | general | azure documentdb rag context engineering LLM window; searched for 'Azure DocumentDB RAG context window assemble passages' (no targeted guidance found) |

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Read the DocumentDB/MongoDB connection string from an environment variable at runtime and fail early if it is missing; do not embed credentials in source files. | authentication_and_secrets | prior_knowledge_confirmed | Quickstart: Use Azure DocumentDB with MongoDB driver for Python (public_doc) | https://learn.microsoft.com/azure/documentdb/quickstart-python#code-examples | azure documentdb quickstart python connection string | yes |
| P02 | Create a single MongoClient (process-wide singleton) and reuse it across the app instead of opening a new client per request; configure and tune connection-pool parameters to suit serverless vs long-running workloads. | connection_handling | prior_knowledge_confirmed | documentdb-driver (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md | documentdb-driver | yes |
| P03 | Require TLS for all connections (connection strings include tls=true) and restrict network access with firewall rules or Private Endpoints so only authorized app runtimes can reach the cluster. | security | prior_knowledge_confirmed | Quickstart: Use Azure DocumentDB with MongoDB driver for Python (public_doc) | https://learn.microsoft.com/azure/documentdb/quickstart-python#code-examples | azure documentdb quickstart python connection string tls=true | yes |
| P04 | Avoid committing raw credentials to source; provide a .env.example with a placeholder connection string and instruct users to set the real value via environment variables or a secrets manager. | authentication_and_secrets | prior_knowledge_confirmed | documentdb-local-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md | documentdb-local-deployment | yes |
| P05 | Give application credentials least privilege: create a database-scoped user for the sample app instead of using an admin key or cluster-wide credentials. | security | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P06 | Record the embedding vector, embedding model name and the vector dimensionality alongside the text so index creation and later queries can verify compatibility. | data_modeling | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | yes |
| P07 | When provisioning a vector index, set the index type and dimensions to match your embedding model (choose diskANN for large production sets, HNSW for smaller sets, IVF for tiny sets) and set similarity (e.g., COS for cosine) in the index definition. | indexing | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | yes |
| P08 | Also create conventional single-field or compound indexes on frequently filtered fields (e.g., transcript_id, source, chunk_id, start_time) so filter-by-transcript and time-range queries are efficient. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P09 | Store embeddings in a documented field together with metadata and the embedding dimensions and model name (the DB may accept arrays or specialized formats such as quantized/fp16; document what you use so index creation matches the stored shape). | data_modeling | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | yes |
| P10 | Run nearest-neighbor queries using the cluster's vector search API (cosmosSearch / $search) with a topK parameter and tune search parameters (lSearch / k / score thresholds); combine with projections to return only needed fields to reduce bandwidth. | vector_search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | yes |
| P11 | Apply metadata-based pre-filtering (for example by transcript/source or date range or partition key) as part of or before vector search to reduce fan-out and improve precision and RU/IO costs. | vector_search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | yes |
| P12 | When returning results, project only the needed fields and limit/paginate results (limit topK to a reasonable number like 10–50) so post-processing and LLM context assembly stays within memory and token budgets. | queries | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | yes |
| P13 | Make ingestion idempotent: deduplicate documents using a deterministic key (e.g., transcript + chunk id checksum) or upsert semantics so re-running ingestion doesn't create duplicates. | provisioning_and_ingest | prior_knowledge_confirmed | Quickstart: Use Azure DocumentDB with MongoDB driver for Python (public_doc) | https://learn.microsoft.com/azure/documentdb/quickstart-python#code-examples | azure documentdb quickstart upsert insertMany upsert guidance | yes |
| P14 | Implement exponential backoff and retries for transient network errors and throttling (429), and make writes idempotent (upsert) so retries don't create duplicates. | retries | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P15 | Normalize embeddings (e.g., unit-length) when using cosine similarity and store the embedding model name and dimensions with each document so queries and index parameters can be validated. | vector_search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | yes |
| P16 | Store text chunks and their embedding together in the same document (text, timestamps, source, embedding, embedding_model, embedding_dims, inserted_at) to avoid extra lookups during retrieval and to enable direct citation. | data_modeling | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P17 | Record provenance metadata per chunk (source filename, chunk id, start/end timestamps, ingestion time, embedding model) so answers can cite exact transcripts and timestamps. | data_modeling | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P18 | Monitor index and query performance (enable diagnostic settings and slow-query logs, alert on CPU/memory/IOPS/storage/connection saturation) and use the MCP inspection tools to validate created indexes and query plans. | monitoring | prior_knowledge_confirmed | documentdb-monitoring (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md | documentdb-monitoring | yes |
| P19 | Tune vector-index build/search parameters appropriate to the chosen engine (e.g., lBuild/lSearch/maxDegree for DiskANN, HNSW/IVF parameters or product-quantization settings) to trade off recall vs latency and memory. | indexing | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | yes |
| P20 | Enable provider-managed backups and understand the service's automatic backup retention (point-in-time recovery); treat heavy ingest/index operations with care and ensure you have a restore plan. | provisioning_and_safety | prior_knowledge_confirmed | Reliability in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/reliability/reliability-documentdb#backup-and-restore | azure documentdb backup restore reliability | yes |
| P21 | When running ingestion, batch inserts (use bulk/insertMany or provider bulk APIs) to improve throughput and failure handling rather than issuing single-document writes one at a time. | provisioning_and_ingest | found_in_public_source | insert (DocumentDB / MongoDB commands) (public_doc) | https://learn.microsoft.com/documentdb/query/commands/query-and-write/insert | azure documentdb insertMany bulk insert guidance | yes |
| P22 | Use application-side cosine calculation only as a fallback; prefer built-in vector search APIs for scale and performance when a vector index is available on the cluster. | vector_search | found_in_public_source | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | yes |
| P23 | Use the DocumentDB MCP server tools (or provider management UI) to inspect index definitions, validate document counts, and verify what the ingestion created as part of automation verification. | verification_and_testing | prior_knowledge_confirmed | documentdb-mcp-setup (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/mcp-setup/SKILL.md | documentdb-mcp-setup | yes |
| P24 | Azure DocumentDB storage uses premium SSD options and IOPS/bandwidth is gated by compute tier (not RU model); size compute for throughput requirements rather than sizing disk for IOPS. | storage | prior_knowledge_contradicted | documentdb-storage (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/storage/SKILL.md | documentdb-storage | yes |
| P25 | Sanitize and normalize text before embedding (strip control characters, normalize whitespace, preserve timestamps) to ensure reproducible chunking and better nearest-neighbor accuracy. | ingest_processing | prior_knowledge_only | - (prior_knowledge) | **none** | azure documentdb chunk sanitize normalize embeddings; documentdb vector search normalize embeddings (checked) but not full sanitization guidance for DocumentDB | yes |
| P26 | Use context-engineering rules to assemble retrieved passages to fit the LLM token budget: rank by vector score, concatenate until budget minus answer buffer is reached, and favor distinct timestamps to improve coverage. | context_engineering | prior_knowledge_only | - (prior_knowledge) | **none** | azure documentdb rag context engineering LLM window; searched for 'Azure DocumentDB RAG context window assemble passages' (no targeted guidance found) | yes |
| P27 | Chunk transcripts into stable, reproducible units and record deterministic chunk IDs (e.g., hash(source,start,end)) so ingestion is idempotent and chunks can be referenced in citations. | context_engineering | found_in_public_source | sample app ingest code (local_file) | **none** | inspected src/ingest.py in workspace | yes |
| P28 | When developing locally against a local DocumentDB gateway, connect on the gateway port with TLS and allow invalid certs only via environment-driven flags—never default tlsAllowInvalidCertificates=true in code. | local_development | found_in_public_source | documentdb-local-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md | documentdb-local-deployment | yes |

## Searches that returned nothing useful

- Azure DocumentDB recommended chunk size tokens overlap RAG
- Azure DocumentDB guidance: context engineering for LLM retrieval assembly
- Azure DocumentDB guidance: specific token sizes per chunk for embeddings
- Azure DocumentDB 'tlsAllowInvalidCertificates' recommended defaults in code

## Notes

I used installed skills (documentdb-*) as authoritative public guidance where available and Microsoft Learn quickstarts/docs for connection, backup and insert behavior. Several ingest/context-engineering items (chunk size, token overlap, passage assembly heuristics, text sanitization) are general RAG best practices and not documented specifically for Azure DocumentDB; those remain prior_knowledge_only. The workspace app implements many of the confirmed practices (env var, singleton client, storing embedding+metadata, unique chunk_id index, insert_many bulk insert).

Prior beliefs the discovery step did not classify: K04, K06. See 05a-prior-beliefs.json.

