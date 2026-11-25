# 5a. Best practices: prior knowledge against the public record: 01-anti-money-laundering-pattern-detector

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**30 practices, 0 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 1 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 9 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 9 | Memory and documentation line up. |
| Found in public sources only | 11 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

> **No documentation search server answered.** In this report, "not found" means "not searchable from this machine", not "not public". Fix the server in `mcp.json` and re-run the audit.

| Source | Reachable | Detail |
|---|---|---|
| Installed agent skills | 0 | 0 have a public address |

## Where public sources contradict the model

### P03: Create single-field indexes on transactions for fields used in traversal and filtering (from_account, to_account, timestamp) and a unique index on accounts.account_id before running queries.

- **The model believed:** Create indexes that support the detector's most common patterns: indexes on transaction_id, from_account, to_account, timestamp (often compound, e.g., {from_account:1, timestamp:-1} and {to_account:1, timestamp:-1}) to make chain-following and time-window queries efficient. (knowledge of `mongodb`)
- **The source says:** Create single-field indexes on transactions for fields used in traversal and filtering (from_account, to_account, timestamp) and a unique index on accounts.account_id before running queries.
- **Source:** src/seed_data.py

## Known to the model, with no public source for this service

| Id | Practice | Knowledge of | Searches tried |
|---|---|---|---|
| K02 | Store and rotate long‑lived secrets (connection strings, DB keys, OPENAI_API_KEY) in a secure secret store (Azure Key Vault) and grant the application least‑privilege access (managed identity) rather than embedding secrets in code or config files. | azure_cosmos_db | search queries attempted: "Azure DocumentDB Key Vault managed identity", "DocumentDB connection string Azure Key Vault", "azure documentdb managed identity" |
| K04 | Configure the MongoDB/PyMongo connection pool (maxPoolSize, minPoolSize) and sensible serverSelectionTimeoutMS/heartbeatFrequencyMS to avoid frequent reconnects and to control concurrent connections for the managed cluster. | mongodb | search queries attempted: "Azure DocumentDB PyMongo maxPoolSize", "DocumentDB connection pool settings", "Azure DocumentDB pymongo connection pool" |
| K06 | Provision throughput thoughtfully: use autoscale or database/collection-level throughput to match workload, and avoid running large analytics against a shared, low-throughput OLTP provisioned database without throttling or dedicated capacity. | azure_cosmos_db | search queries attempted: "Azure DocumentDB throughput autoscale RU/s provisioning", "Azure DocumentDB autoscale" |
| K11 | When storing vector embeddings for similarity search, keep a consistent embedding dimension, normalize vectors if using cosine similarity, and store them in a dedicated field with a matching vector index configured. | general | search queries attempted: "Azure DocumentDB vector index HNSW DiskANN best practices", "DocumentDB vector embeddings dimension normalize" |
| K12 | Tune vector index parameters (e.g., efConstruction, efSearch, nprobe or equivalent) according to dataset size and latency/retrieval quality needs, and validate recall with a held-out test set rather than default settings. | general | search queries attempted: "Azure DocumentDB HNSW efConstruction efSearch tuning", "DocumentDB DiskANN tuning parameters" |
| K15 | Protect PII: enable encryption at rest (platform default), and consider client-side field-level encryption for extremely sensitive fields (account numbers, SSNs) so data remains encrypted in the DB and logs. | mongodb | search queries attempted: "Azure DocumentDB field level encryption client side", "DocumentDB client side field encryption" |
| K16 | Use firewall rules and private endpoints (VNet) to restrict cluster access to known hosts or application subnets rather than opening the DB to the public internet. | azure_cosmos_db | search queries attempted: "Azure DocumentDB private endpoint vnet firewall", "DocumentDB network access control" |
| K17 | Instrument and monitor query performance and resource metrics (RU/s consumption, operation latency, index usage, slow queries) and configure alerts to catch spikes caused by heavy aggregations or full-collection scans. | azure_cosmos_db | search queries attempted: "Azure DocumentDB monitor RU/s alerts slow queries", "DocumentDB monitoring indexes slow queries" |
| K20 | Implement observability and resumability for detectors: log processed chains, store processed checkpoints and flagged-chain artifacts in a durable collection with unique IDs to allow retries and auditability. | general | search queries attempted: "DocumentDB detector resumable checkpoints logging best practices", "Azure DocumentDB auditability logging" |

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Read the DocumentDB connection string from the DOCUMENTDB_URI environment variable at runtime and provide a .env.example placeholder rather than committing credentials. | authentication | prior_knowledge_confirmed | .env.example / src/db.py / README.md (local_file) | **none** | .env.example | yes |
| P02 | Seed sample data idempotently using replace_one(..., upsert=True) for each seeded document and mark seeding completion with a dedicated metadata document to avoid duplicate seeds on re-run. | testing | prior_knowledge_confirmed | src/seed_data.py (local_file) | **none** | src/seed_data.py | yes |
| P03 | Create single-field indexes on transactions for fields used in traversal and filtering (from_account, to_account, timestamp) and a unique index on accounts.account_id before running queries. | indexing | prior_knowledge_contradicted | src/seed_data.py (local_file) | **none** | src/seed_data.py | yes |
| P04 | Detect whether the server supports $graphLookup by issuing a minimal aggregation with explain and, if unsupported, fall back to a client-side traversal implementation. | queries | found_in_public_source | src/db.py (local_file) | **none** | src/db.py | yes |
| P05 | When using $graphLookup in aggregation pipelines, set maxDepth to limit recursion and bound server-side graph traversal work. | queries | prior_knowledge_confirmed | src/detector.py (local_file) | **none** | src/detector.py | yes |
| P06 | Implement a bounded client-side BFS traversal fallback that tracks visited transaction IDs and limits hops to avoid unbounded in-memory expansion and cycles. | performance | prior_knowledge_confirmed | src/detector.py (local_file) | **none** | src/detector.py | yes |
| P07 | Use projection (e.g., $project) in aggregation pipelines to return only the necessary fields (for example, project only the assembled 'chain') to reduce network and memory use. | performance | prior_knowledge_confirmed | src/detector.py (local_file) | **none** | src/detector.py | yes |
| P08 | Use aggregate explain (or explain-mode aggregation) to validate whether certain aggregation operators are accepted by the server without scanning or requiring actual data. | queries | found_in_public_source | src/db.py (local_file) | **none** | src/db.py | yes |
| P09 | Create the indexes the application needs before inserting the sample data (ensure indexes are created in the seed script prior to data writes). | indexing | found_in_public_source | src/seed_data.py (local_file) | **none** | src/seed_data.py | yes |
| P10 | Read optional external API keys (e.g., OPENAI_API_KEY) from the environment and only invoke external services when the key is present to keep optional dependencies conditional. | authentication | found_in_public_source | src/detector.py / README.md (local_file) | **none** | src/detector.py | yes |
| P11 | Fail fast with a clear error if the required DOCUMENTDB_URI environment variable is not set so the operator can supply configuration before runtime. | connection | found_in_public_source | src/db.py (local_file) | **none** | src/db.py | yes |
| P12 | Place $match early in aggregation pipelines (before expensive stages) and use projection; validate heavy pipelines with explain to avoid long-running scans. | queries | prior_knowledge_confirmed | src/detector.py / src/db.py (local_file) | **none** | src/detector.py | yes |
| P13 | Design transaction documents with explicit fields used by detectors (from_account, to_account, timestamp, amount, and a consistent _id) to support deterministic queries and joins. | data_modeling | prior_knowledge_confirmed | src/seed_data.py (local_file) | **none** | src/seed_data.py | yes |
| P14 | Use timestamp sorting and explicit time-window queries (ranges) when checking for rapid pass-through behavior (e.g., find outgoing transaction with timestamp within N minutes of incoming one). | queries | found_in_public_source | src/detector.py (local_file) | **none** | src/detector.py | yes |
| P15 | Use replace_one(..., upsert=True) for idempotent writes when seeding or when a retried operation should not create duplicates. | retries | prior_knowledge_confirmed | src/seed_data.py (local_file) | **none** | src/seed_data.py | yes |
| P16 | Include an example connection string showing SSL/TLS options (e.g., ssl=true) in .env.example to indicate TLS should be used in production connections. | connection | prior_knowledge_confirmed | .env.example (local_file) | **none** | .env.example | yes |
| P17 | If an aggregation operator may be unavailable on the server, use explain rather than running the pipeline to validate operator acceptance without executing heavy work. | queries | found_in_public_source | src/db.py (local_file) | **none** | src/db.py | yes |
| P18 | Keep optional external integrations conditional (check for API key presence at runtime) and fall back to local deterministic templates if the external LLM is not available. | architecture | found_in_public_source | src/detector.py (local_file) | **none** | src/detector.py | yes |
| P19 | Use a unique index on accounts.account_id to enforce uniqueness for account lookup and to support deterministic traversal starting points. | indexing | found_in_public_source | src/seed_data.py (local_file) | **none** | src/seed_data.py | yes |
| P20 | When validating operator availability or running feature-detection queries, prefer commands that do not require cluster writes and avoid scanning large collections in detection code. | operations | found_in_public_source | src/db.py (local_file) | **none** | src/db.py | yes |
| P21 | If a prior belief cannot be corroborated for Azure DocumentDB in public sources reachable here, record it as prior-knowledge-only so code authors know it came from memory not from an accessible DocumentDB source. | method | found_in_public_source | README.md (local_file) | **none** | README.md | no |
| K02 | Store and rotate long‑lived secrets (connection strings, DB keys, OPENAI_API_KEY) in a secure secret store (Azure Key Vault) and grant the application least‑privilege access (managed identity) rather than embedding secrets in code or config files. | authentication | prior_knowledge_only | - (prior_knowledge) | **none** | search queries attempted: "Azure DocumentDB Key Vault managed identity", "DocumentDB connection string Azure Key Vault", "azure documentdb managed identity" | yes |
| K04 | Configure the MongoDB/PyMongo connection pool (maxPoolSize, minPoolSize) and sensible serverSelectionTimeoutMS/heartbeatFrequencyMS to avoid frequent reconnects and to control concurrent connections for the managed cluster. | connection | prior_knowledge_only | - (prior_knowledge) | **none** | search queries attempted: "Azure DocumentDB PyMongo maxPoolSize", "DocumentDB connection pool settings", "Azure DocumentDB pymongo connection pool" | yes |
| K06 | Provision throughput thoughtfully: use autoscale or database/collection-level throughput to match workload, and avoid running large analytics against a shared, low-throughput OLTP provisioned database without throttling or dedicated capacity. | provisioning | prior_knowledge_only | - (prior_knowledge) | **none** | search queries attempted: "Azure DocumentDB throughput autoscale RU/s provisioning", "Azure DocumentDB autoscale" | yes |
| K11 | When storing vector embeddings for similarity search, keep a consistent embedding dimension, normalize vectors if using cosine similarity, and store them in a dedicated field with a matching vector index configured. | vector_search | prior_knowledge_only | - (prior_knowledge) | **none** | search queries attempted: "Azure DocumentDB vector index HNSW DiskANN best practices", "DocumentDB vector embeddings dimension normalize" | no |
| K12 | Tune vector index parameters (e.g., efConstruction, efSearch, nprobe or equivalent) according to dataset size and latency/retrieval quality needs, and validate recall with a held-out test set rather than default settings. | vector_search | prior_knowledge_only | - (prior_knowledge) | **none** | search queries attempted: "Azure DocumentDB HNSW efConstruction efSearch tuning", "DocumentDB DiskANN tuning parameters" | no |
| K15 | Protect PII: enable encryption at rest (platform default), and consider client-side field-level encryption for extremely sensitive fields (account numbers, SSNs) so data remains encrypted in the DB and logs. | security | prior_knowledge_only | - (prior_knowledge) | **none** | search queries attempted: "Azure DocumentDB field level encryption client side", "DocumentDB client side field encryption" | yes |
| K16 | Use firewall rules and private endpoints (VNet) to restrict cluster access to known hosts or application subnets rather than opening the DB to the public internet. | security | prior_knowledge_only | - (prior_knowledge) | **none** | search queries attempted: "Azure DocumentDB private endpoint vnet firewall", "DocumentDB network access control" | yes |
| K17 | Instrument and monitor query performance and resource metrics (RU/s consumption, operation latency, index usage, slow queries) and configure alerts to catch spikes caused by heavy aggregations or full-collection scans. | monitoring | prior_knowledge_only | - (prior_knowledge) | **none** | search queries attempted: "Azure DocumentDB monitor RU/s alerts slow queries", "DocumentDB monitoring indexes slow queries" | yes |
| K20 | Implement observability and resumability for detectors: log processed chains, store processed checkpoints and flagged-chain artifacts in a durable collection with unique IDs to allow retries and auditability. | monitoring | prior_knowledge_only | - (prior_knowledge) | **none** | search queries attempted: "DocumentDB detector resumable checkpoints logging best practices", "Azure DocumentDB auditability logging" | yes |

## Searches that returned nothing useful

- Azure DocumentDB Key Vault managed identity
- DocumentDB connection pool pymongo maxPoolSize
- Azure DocumentDB throughput autoscale RU/s provisioning
- Azure DocumentDB vector index HNSW DiskANN best practices
- DocumentDB DiskANN tuning parameters
- Azure DocumentDB client side field encryption
- Azure DocumentDB private endpoint vnet firewall
- Azure DocumentDB monitor RU/s alerts slow queries
- DocumentDB detector resumable checkpoints logging

## Notes

Open discovery was limited to the local sample code, README and .env.example because no external documentation or installed skills were reachable in this run. Practices were extracted from src/*.py and the README; where a prior belief matched the local files it was marked confirmed or contradicted, otherwise it is recorded as prior_knowledge_only with the queries an agent would try listed in how_found/searches_with_no_useful_result.

Prior beliefs the discovery step did not classify: K19. See 05a-prior-beliefs.json.

