# 5a. Best practices: prior knowledge against the public record: 09-clinical-notes-de-identification

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**23 practices, 20 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 2 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 2 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 16 | Memory and documentation line up. |
| Found in public sources only | 3 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

## Where public sources contradict the model

### P07: Size cluster capacity by picking the appropriate compute tier and storage type (IOPS/bandwidth are gated by compute tier for Premium SSD v2) and use autoscale or larger tiers for heavy batch workloads rather than thinking in Cosmos DB RU/s.

- **The model believed:** Provision collection throughput (RU/s) or autoscale appropriately for the de-identification pipeline's read/write pattern; benchmark and raise RUs or enable autoscale to avoid frequent throttling during batch runs. (knowledge of `azure_cosmos_db`)
- **The source says:** Size cluster capacity by picking the appropriate compute tier and storage type (IOPS/bandwidth are gated by compute tier for Premium SSD v2) and use autoscale or larger tiers for heavy batch workloads rather than thinking in Cosmos DB RU/s.
- **Source:** [documentdb-storage](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/storage/SKILL.md)

### P17: Enable diagnostic settings and slow-query logging and alert on CPU, memory, IOPS, storage, and connection saturation (and frequent 429s); use Log Analytics for slow-query analysis rather than relying on RU metrics.

- **The model believed:** Monitor query RU charge and latency (via driver command monitoring or Azure Monitor/Diagnostic settings); add alerts for sustained high RU consumption or frequent 429s and capture slow query patterns to optimize indexes/queries. (knowledge of `azure_cosmos_db`)
- **The source says:** Enable diagnostic settings and slow-query logging and alert on CPU, memory, IOPS, storage, and connection saturation (and frequent 429s); use Log Analytics for slow-query analysis rather than relying on RU metrics.
- **Source:** [documentdb-monitoring](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md)

## Known to the model, with no public source for this service

| Id | Practice | Knowledge of | Searches tried |
|---|---|---|---|
| P15 | Before sending clinical text to an external LLM, verify compliance and minimize PHI exposure; there is no authoritative Azure DocumentDB public guidance that endorses sending PHI to external LLMs for de-identification. | general | Azure DocumentDB documentation + installed skills searched for LLM or OpenAI PHI guidance; no authoritative guidance found |
| P19 | When a workflow spans multiple documents or partitions, plan for at-least-once semantics and use idempotency keys or compensating actions because cross-partition transactions are supported but can be expensive. | general | searched installed skills for 'idempotent', 'multi-document transactions' and 'compensating actions' in Azure DocumentDB guidance; found discussion that cross-shard transactions are supported but not explicit application-level guidance |

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Keep DocumentDB connection strings and DB credentials in environment variables or a managed secret store and never commit them to the repository or test fixtures. | secrets | prior_knowledge_confirmed | documentdb-local-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md | documentdb-local-deployment | yes |
| P02 | Prefer Microsoft Entra ID (managed identities) and RBAC for authentication so apps use short-lived credentials rather than long-lived DB passwords; if SCRAM is used, create per-app least-privilege users and rotate secrets. | secrets | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P03 | Always require TLS for client connections and do not disable certificate validation in production; configure CA bundles correctly for development instead of turning off verification. | security | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P04 | Create a single shared MongoClient/Async client at process startup and reuse it across requests rather than creating a new client per request or operation. | connection | prior_knowledge_confirmed | documentdb-driver (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md | documentdb-driver | yes |
| P05 | Tune driver connection-pool and timeout settings (maxPoolSize/minPoolSize/connectTimeoutMS/socketTimeoutMS) to match the workload, using small pools for serverless and larger pools for long-running servers. | connection | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P06 | Implement retry and exponential backoff (with jitter) for transient errors and rate-limited responses, detect 429s and retryable error codes, and respect any Retry-After guidance from the service. | retries | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P07 | Size cluster capacity by picking the appropriate compute tier and storage type (IOPS/bandwidth are gated by compute tier for Premium SSD v2) and use autoscale or larger tiers for heavy batch workloads rather than thinking in Cosmos DB RU/s. | provisioning | prior_knowledge_contradicted | documentdb-storage (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/storage/SKILL.md | documentdb-storage | yes |
| P08 | Choose shard/partition keys to obtain even distribution: for read-heavy workloads pick the most-used query filter; for write-heavy workloads pick a high-cardinality, evenly distributed field and avoid monotonic keys. | data_modeling | prior_knowledge_confirmed | documentdb-sharding (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/sharding/SKILL.md | documentdb-sharding | yes |
| P09 | Create explicit indexes on fields your application queries frequently (for example sourceId and created_at) and use compound indexes when queries filter or sort on multiple fields. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P10 | Keep small indexed fields for status/processed checks (for example deid_status + sourceId) so efficient lookups support idempotent batch processing. | data_modeling | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P11 | Enforce schema and model validation at the application or DB layer (use Pydantic/Beanie model validation or MongoDB schema validation) and include a schemaVersion field to support migrations. | data_modeling | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P12 | Make the de-identification pipeline idempotent by ensuring exactly one DeidNote per RawNote, using a unique index on DeidNote.sourceId or an upsert/check pattern to avoid duplicates. | application_pattern | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P13 | Avoid storing very large clinical blobs directly in documents; split large fields into a side collection or store attachments in Azure Blob Storage and reference them to stay well under the 16 MB BSON limit. | data_modeling | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P14 | Do not log PHI or connection strings: redact or hash identifiers in application logs and use synthetic data for CI and local testing. | security | prior_knowledge_confirmed | README.md (local_file) | **none** | README.md | yes |
| P15 | Before sending clinical text to an external LLM, verify compliance and minimize PHI exposure; there is no authoritative Azure DocumentDB public guidance that endorses sending PHI to external LLMs for de-identification. | security | prior_knowledge_only | - (prior_knowledge) | **none** | Azure DocumentDB documentation + installed skills searched for LLM or OpenAI PHI guidance; no authoritative guidance found | yes |
| P16 | When using vector search, store fixed-length float arrays, set the index dimension equal to the vector length, choose similarity (COS/IP/L2), and pick DiskANN/HNSW/IVF with tuned build/search parameters and normalized embeddings for cosine similarity. | vector_search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | no |
| P17 | Enable diagnostic settings and slow-query logging and alert on CPU, memory, IOPS, storage, and connection saturation (and frequent 429s); use Log Analytics for slow-query analysis rather than relying on RU metrics. | observability | prior_knowledge_contradicted | documentdb-monitoring (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md | documentdb-monitoring | yes |
| P18 | Create and change indexes in a controlled manner (during deployment or maintenance windows), use explicit create_indexes scripts, and prefer sparse/partial/TTL options to limit index write cost. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P19 | When a workflow spans multiple documents or partitions, plan for at-least-once semantics and use idempotency keys or compensating actions because cross-partition transactions are supported but can be expensive. | application_pattern | prior_knowledge_only | - (prior_knowledge) | **none** | searched installed skills for 'idempotent', 'multi-document transactions' and 'compensating actions' in Azure DocumentDB guidance; found discussion that cross-shard transactions are supported but not explicit application-level guidance | yes |
| P20 | Run automated tests against a dedicated test database or a local DocumentDB gateway/emulator, keep seed scripts idempotent, and avoid running tests that modify production collections. | testing | prior_knowledge_confirmed | documentdb-local-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md | documentdb-local-deployment | yes |
| P21 | On Azure DocumentDB prefer the `textSearch` index and the `$search` aggregation stage for lexical full-text search rather than relying on the community `$text` index. | indexing | found_in_public_source | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | no |
| P22 | Prefer Premium SSD v2 for new clusters because it decouples IOPS/bandwidth from disk size and requires sizing compute for throughput while sizing storage for capacity. | storage | found_in_public_source | documentdb-storage (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/storage/SKILL.md | documentdb-storage | no |
| P23 | For local development, use the DocumentDB Gateway Docker image (Mongo protocol on port 10260) and drive TLS relaxation and connection URIs from environment variables rather than hard-coding relaxed TLS in code. | local_development | found_in_public_source | documentdb-local-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md | documentdb-local-deployment | yes |

## Searches that returned nothing useful

- Azure DocumentDB OpenAI PHI guidance
- Azure DocumentDB send PHI to external LLM guidance
- Azure DocumentDB idempotent pipeline best practices
- Azure DocumentDB monitor RU charge
- Azure DocumentDB 'RU/s' guidance for Mongo API

## Notes

I inspected the sample app files (src/models.py, src/db.py, create_indexes.py, seed.py, deid_pipeline.py, README.md) and loaded installed DocumentDB skills to capture publicly available guidance. Prior beliefs K01–K20 were compared to the public guidance: most mapped cleanly and were confirmed; beliefs that referenced Cosmos DB-specific concepts (RU/s) or external-LLM PHI guidance were either contradicted or had no authoritative Azure DocumentDB documentation and are marked accordingly.

