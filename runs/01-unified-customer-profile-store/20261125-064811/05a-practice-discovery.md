# 5a. Best practices: prior knowledge against the public record: 01-unified-customer-profile-store

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**30 practices, 0 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 0 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 13 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 7 | Memory and documentation line up. |
| Found in public sources only | 10 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

> **No documentation search server answered.** In this report, "not found" means "not searchable from this machine", not "not public". Fix the server in `mcp.json` and re-run the audit.

| Source | Reachable | Detail |
|---|---|---|
| Installed agent skills | 0 | 0 have a public address |

## Known to the model, with no public source for this service

| Id | Practice | Knowledge of | Searches tried |
|---|---|---|---|
| P12 | Use the driver/Mongoose connection options and the provided connection string so driver-level TLS and SRV handling remain correct; avoid hardcoding conflicting flags in code. | mongodb | queries tried: "Azure DocumentDB TLS connection options"; "Azure DocumentDB mongoose connectTimeoutMS"; "Azure DocumentDB mongodb+srv tls requirements"; checked local files (src/db.js) which advise relying on URI/driver defaults but do not document explicit timeout flags for Azure DocumentDB. |
| P13 | Configure a connection pool sized to the workload rather than opening many short-lived connections per request; set maxPoolSize appropriate to app concurrency. | mongodb | queries tried: "Azure DocumentDB maxPoolSize recommend"; "Azure DocumentDB connection pool best practices"; reviewed local files (src/db.js) which do not set pool options. |
| P17 | Make updates idempotent by using upsert patterns and timestamps (createdAt/updatedAt); track event deduplication at the application layer if needed (the sample shows createdAt/updatedAt but not eventId dedupe). | general | queries tried: "Azure DocumentDB idempotent upsert eventId"; "DocumentDB deduplicate events per source"; inspected local code which uses upsert and timestamps but does not store eventId. |
| P18 | Implement retry with exponential backoff and jitter for transient network errors and throttling (429) when interacting with the DB client; limit attempts to avoid infinite retries. | azure_cosmos_db | queries tried: "Azure DocumentDB retry 429 backoff"; "Azure Cosmos MongoDB API 429 best practices"; no local code implements retry/backoff. |
| P19 | Avoid unbounded document growth by keeping profile documents small or moving high-cardinality/time-series events into a separate collection rather than storing everything in the canonical profile document. | mongodb | queries tried: "Azure DocumentDB document size limit"; "Azure DocumentDB avoid large documents arrays"; local sample keeps profile small but includes no explicit cap. |
| P20 | Create indexes that match your read/query patterns instead of indexing everything, and avoid broad wildcard indexes over large nested subdocuments to limit RU costs. | general | queries tried: "Azure DocumentDB indexing best practices RU costs"; inspected sample which creates only customerId index. |
| P22 | If you need text or vector search, create a dedicated field for embeddings and add a vector index with explicit parameters (metric, dims, algorithm_config); be mindful of dimensionality vs RU budget. | azure_documentdb | queries tried: "Azure DocumentDB vector index HNSW DiskANN guidance"; sample environment mentioned vector-capable cluster but repo contains no vector-index guidance. |
| P23 | Use partial or sparse indexes for fields that are present only for some documents (e.g., partialFilterExpression) to reduce index size and RU costs. | mongodb | queries tried: "Azure DocumentDB partial index partialFilterExpression"; local sample does not create partial/sparse indexes. |
| P24 | Log errors and basic request/validation failures at the API boundary to aid debugging and surface server-side errors. | general | queries tried: "Azure DocumentDB logging slow queries index misses"; sample logs basic errors but not slow query/index-miss capture. |
| P25 | Estimate RU consumption for common operations and reserve modest predictable throughput or use autoscale to prevent 429 throttling spikes during ingestion. | azure_cosmos_db | queries tried: "Azure DocumentDB RU/s autoscale guidance"; no RU provisioning guidance in local sample. |
| P26 | Protect cluster access by restricting network access (firewall/IP rules or VNet) and keep credentials in a secret store rather than committing them in code or CI logs. | azure_documentdb | queries tried: "Azure DocumentDB firewall VNet best practices"; local sample advises not to commit credentials but does not show Key Vault or network controls. |
| P29 | Use schema validation on the DB (e.g., MongoDB JSON Schema validator) if you need to enforce document shapes; the sample uses Mongoose validation but does not create DB-level validators. | mongodb | queries tried: "Azure DocumentDB JSON Schema validator createCollection validator"; inspected repo which uses Mongoose schema but no DB-level validator. |
| P30 | Avoid excessive indexing of large or high-cardinality nested fields and instead index only the small set of queryable fields to control RU costs. | general | queries tried: "Azure DocumentDB index costs nested fields"; sample creates only a customerId unique index. |

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Read the cluster connection string only from an environment variable (DOCUMENTDB_URI) at runtime and do not commit real credentials to the repo; provide a .env.example with a placeholder instead. | authentication/secrets | found_in_public_source | .env.example / README.md / src/db.js (local_file) | **none** | .env.example | yes |
| P02 | Connect to the cluster using the provided URI with mongoose.connect(...) and then select the intended database with connection.useDb('sample_customer_360_01') so all sample operations are scoped to the designated DB. | connection/provisioning | found_in_public_source | src/db.js (local_file) | **none** | src/db.js | yes |
| P03 | Avoid hardcoding TLS/SSL flags in code; rely on the provided connection string and current driver defaults for required TLS options. | connection/security | found_in_public_source | src/db.js (local_file) | **none** | src/db.js | yes |
| P04 | Create a unique index on customerId (CustomerSchema.index({ customerId: 1 }, { unique: true })) so identity resolution and upserts can rely on a stable unique key. | indexing/data_model | found_in_public_source | src/models/customer.js (local_file) | **none** | src/models/customer.js | yes |
| P05 | Create indexes in an idempotent, non-destructive way (call createIndexes and handle IndexKeySpecsConflict rather than dropping existing indexes), as done in the seed script. | indexing/provisioning | found_in_public_source | scripts/seed.js (local_file) | **none** | scripts/seed.js | yes |
| P06 | Perform single-document idempotent upserts using updateOne with upsert:true and $set/$setOnInsert (set updatedAt and setOnInsert createdAt) to keep writes atomic and safe for concurrent updates. | data_model/transactions | found_in_public_source | src/lib/upsert.js / README.md (local_file) | **none** | src/lib/upsert.js | yes |
| P07 | Model each source system as a nested subdocument (sources.crm, sources.ecommerce, sources.support) so source-specific attributes are stored under each source key. | data_model | found_in_public_source | src/models/customer.js / README.md (local_file) | **none** | src/models/customer.js | yes |
| P08 | Use a flexible SourceSchema (strict: false) for source subdocuments so events with different attribute shapes can be accepted without prior schema changes. | data_model/validation | found_in_public_source | src/models/customer.js (local_file) | **none** | src/models/customer.js | yes |
| P09 | Provide seed and verify scripts that operate only in the designated sample database (sample_customer_360_01) and implement idempotent behavior for safe repeated runs. | provisioning/safety | found_in_public_source | scripts/seed.js / scripts/verify.js / README.md (local_file) | **none** | scripts/seed.js | yes |
| P10 | Validate incoming event shape at the API boundary and return HTTP 400 for missing required fields to avoid invalid writes (require source, customerId, attributes). | input_validation/observability | found_in_public_source | src/routes/events.js (local_file) | **none** | src/routes/events.js | yes |
| P11 | Read the cluster connection string only from an environment variable (DOCUMENTDB_URI) at runtime; never commit keys or the full URI to the repo or logs and provide a .env.example with a placeholder instead. | authentication/secrets | prior_knowledge_confirmed | .env.example / README.md / src/db.js (local_file) | **none** | .env.example | yes |
| P12 | Use the driver/Mongoose connection options and the provided connection string so driver-level TLS and SRV handling remain correct; avoid hardcoding conflicting flags in code. | connection | prior_knowledge_only | - (prior_knowledge) | **none** | queries tried: "Azure DocumentDB TLS connection options"; "Azure DocumentDB mongoose connectTimeoutMS"; "Azure DocumentDB mongodb+srv tls requirements"; checked local files (src/db.js) which advise relying on URI/driver defaults but do not document explicit timeout flags for Azure DocumentDB. | yes |
| P13 | Configure a connection pool sized to the workload rather than opening many short-lived connections per request; set maxPoolSize appropriate to app concurrency. | connection | prior_knowledge_only | - (prior_knowledge) | **none** | queries tried: "Azure DocumentDB maxPoolSize recommend"; "Azure DocumentDB connection pool best practices"; reviewed local files (src/db.js) which do not set pool options. | yes |
| P14 | Treat the canonical customer document as the unit of atomicity and perform single-document upserts (updateOne with upsert:true and targeted $set of nested fields) rather than multi-document transactions. | data_model/transactions | prior_knowledge_confirmed | src/lib/upsert.js / README.md (local_file) | **none** | src/lib/upsert.js | yes |
| P15 | Create a unique index on customerId to support identity resolution and let upserts rely on that stable unique key. | indexing/data_model | prior_knowledge_confirmed | src/models/customer.js (local_file) | **none** | src/models/customer.js | yes |
| P16 | Model each source system as a nested subdocument and update that source key (sources.<source>) with $set so each source’s data is isolated under its key. | data_model | prior_knowledge_confirmed | README.md / src/lib/upsert.js / src/models/customer.js (local_file) | **none** | README.md; src/lib/upsert.js | yes |
| P17 | Make updates idempotent by using upsert patterns and timestamps (createdAt/updatedAt); track event deduplication at the application layer if needed (the sample shows createdAt/updatedAt but not eventId dedupe). | retries/idempotency | prior_knowledge_only | - (prior_knowledge) | **none** | queries tried: "Azure DocumentDB idempotent upsert eventId"; "DocumentDB deduplicate events per source"; inspected local code which uses upsert and timestamps but does not store eventId. | yes |
| P18 | Implement retry with exponential backoff and jitter for transient network errors and throttling (429) when interacting with the DB client; limit attempts to avoid infinite retries. | retries | prior_knowledge_only | - (prior_knowledge) | **none** | queries tried: "Azure DocumentDB retry 429 backoff"; "Azure Cosmos MongoDB API 429 best practices"; no local code implements retry/backoff. | yes |
| P19 | Avoid unbounded document growth by keeping profile documents small or moving high-cardinality/time-series events into a separate collection rather than storing everything in the canonical profile document. | data_model/provisioning | prior_knowledge_only | - (prior_knowledge) | **none** | queries tried: "Azure DocumentDB document size limit"; "Azure DocumentDB avoid large documents arrays"; local sample keeps profile small but includes no explicit cap. | yes |
| P20 | Create indexes that match your read/query patterns instead of indexing everything, and avoid broad wildcard indexes over large nested subdocuments to limit RU costs. | indexing/queries | prior_knowledge_only | - (prior_knowledge) | **none** | queries tried: "Azure DocumentDB indexing best practices RU costs"; inspected sample which creates only customerId index. | yes |
| P21 | When adding or changing indexes, perform idempotent index creation (createIndexes) and avoid changing existing index types in-place because builds may be expensive; handle conflicts gracefully in scripts. | indexing/provisioning | prior_knowledge_confirmed | scripts/seed.js (local_file) | **none** | scripts/seed.js | yes |
| P22 | If you need text or vector search, create a dedicated field for embeddings and add a vector index with explicit parameters (metric, dims, algorithm_config); be mindful of dimensionality vs RU budget. | vector_search/indexing | prior_knowledge_only | - (prior_knowledge) | **none** | queries tried: "Azure DocumentDB vector index HNSW DiskANN guidance"; sample environment mentioned vector-capable cluster but repo contains no vector-index guidance. | yes |
| P23 | Use partial or sparse indexes for fields that are present only for some documents (e.g., partialFilterExpression) to reduce index size and RU costs. | indexing | prior_knowledge_only | - (prior_knowledge) | **none** | queries tried: "Azure DocumentDB partial index partialFilterExpression"; local sample does not create partial/sparse indexes. | yes |
| P24 | Log errors and basic request/validation failures at the API boundary to aid debugging and surface server-side errors. | observability | prior_knowledge_only | - (prior_knowledge) | **none** | queries tried: "Azure DocumentDB logging slow queries index misses"; sample logs basic errors but not slow query/index-miss capture. | yes |
| P25 | Estimate RU consumption for common operations and reserve modest predictable throughput or use autoscale to prevent 429 throttling spikes during ingestion. | provisioning/throughput | prior_knowledge_only | - (prior_knowledge) | **none** | queries tried: "Azure DocumentDB RU/s autoscale guidance"; no RU provisioning guidance in local sample. | yes |
| P26 | Protect cluster access by restricting network access (firewall/IP rules or VNet) and keep credentials in a secret store rather than committing them in code or CI logs. | security | prior_knowledge_only | - (prior_knowledge) | **none** | queries tried: "Azure DocumentDB firewall VNet best practices"; local sample advises not to commit credentials but does not show Key Vault or network controls. | yes |
| P27 | Prefer single-document atomic operations and denormalized nested fields over multi-collection joins for the canonical profile to keep reads and writes cheap. | data_model/queries | prior_knowledge_confirmed | README.md / src/lib/upsert.js (local_file) | **none** | README.md; src/lib/upsert.js | yes |
| P28 | When seeding sample data and running verify scripts against a shared cluster, operate only in the designated database (sample_customer_360_01) and ensure scripts are idempotent and non-destructive. | provisioning/safety | prior_knowledge_confirmed | README.md / scripts/seed.js / scripts/verify.js (local_file) | **none** | README.md; scripts/seed.js | yes |
| P29 | Use schema validation on the DB (e.g., MongoDB JSON Schema validator) if you need to enforce document shapes; the sample uses Mongoose validation but does not create DB-level validators. | data_model/validation | prior_knowledge_only | - (prior_knowledge) | **none** | queries tried: "Azure DocumentDB JSON Schema validator createCollection validator"; inspected repo which uses Mongoose schema but no DB-level validator. | yes |
| P30 | Avoid excessive indexing of large or high-cardinality nested fields and instead index only the small set of queryable fields to control RU costs. | indexing/costs | prior_knowledge_only | - (prior_knowledge) | **none** | queries tried: "Azure DocumentDB index costs nested fields"; sample creates only a customerId unique index. | yes |

## Searches that returned nothing useful

- Azure DocumentDB TLS connection options
- Azure DocumentDB maxPoolSize recommend
- Azure DocumentDB retry 429 backoff
- Azure DocumentDB vector index HNSW guidance
- Azure DocumentDB partial index partialFilterExpression
- Azure DocumentDB RU/s autoscale guidance
- Azure DocumentDB JSON Schema validator createCollection
- Azure DocumentDB index costs nested fields

## Notes

Open discovery used only the sample repository files (local_file) because documentation search was not available in this environment; where the repository explicitly documents a practice it was marked as confirmed (prior_knowledge_confirmed), otherwise the corresponding prior belief was recorded as prior_knowledge_only with the queries that would have been used to look for official guidance.

