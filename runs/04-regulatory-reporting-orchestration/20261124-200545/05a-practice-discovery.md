# 5a. Best practices: prior knowledge against the public record: 04-regulatory-reporting-orchestration

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**24 practices, 19 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 0 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 4 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 14 | Memory and documentation line up. |
| Found in public sources only | 6 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

## Known to the model, with no public source for this service

| Id | Practice | Knowledge of | Searches tried |
|---|---|---|---|
| P21 | Record each orchestration step's status and timestamps in a workflow-run document to support resumability and idempotent retries. | general | Azure DocumentDB workflow resumable steps best practices; documentdb orchestration logging best practices; azure documentdb workflow-run logging |
| P22 | Use multi-document transactions only when required for atomicity across documents/collections, keep transactions small and short-lived, and validate transaction behavior against the live cluster. | mongodb | azure documentdb transactions guidance; documentdb multi-document transaction best practices; mongodb transactions azure documentdb |
| P23 | Do not write secrets or raw PII into workflow logs or plain documents; redact or encrypt sensitive fields and restrict access via RBAC and network controls. | general | azure documentdb logs redact PII; documentdb logging PII sensitive data best practices; azure monitor PII redaction guidance |
| P24 | Run integration tests against a real DocumentDB instance (or the documented local Gateway) for behaviors mongomock cannot emulate (indexing, explain plans, vector indexes, transactions). | mongodb | documentdb local deployment integration tests; mongomock limitations vector index explain; azure documentdb integration testing guidance |

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Create one MongoClient per process (singleton) and reuse it across the application rather than creating a new client per request. | connection handling | prior_knowledge_confirmed | documentdb-driver (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md | documentdb-driver | yes |
| P02 | Read the cluster connection string from the environment at runtime (e.g., DOCUMENTDB_URI) and avoid committing connection secrets to source control; drive local config via a .env file or secret store instead. | authentication and secrets | prior_knowledge_confirmed | documentdb-local-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md | documentdb-local-deployment | yes |
| P03 | Always connect with TLS enabled and do not disable certificate validation in production (ensure tls=true in connection string and validate certs). | security | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P04 | Set reasonable connection timeouts (serverSelectionTimeoutMS, connectTimeoutMS, socketTimeoutMS) to fail fast and avoid hung requests, tuned to the application's latency expectations. | connection handling | found_in_public_source | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P05 | Configure the MongoClient connection pool (maxPoolSize, minPoolSize, maxIdleTimeMS) according to the deployment model (serverless vs long-running servers vs OLAP) rather than relying on defaults. | connection handling | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P06 | Enable driver retryable reads/writes and implement application-level retries with exponential backoff for transient errors, ensuring retries are safe or guarded by idempotency/dedup keys. | retries | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P07 | Use least-privilege credentials: prefer Microsoft Entra ID (managed identity) + RBAC for apps, or create dedicated DB users with only required roles and rotate secrets via Key Vault. | authentication and secrets | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P08 | Make seed scripts idempotent (use upsert or check for existing documents/indexes) so repeated runs do not duplicate data or fail unexpectedly. | provisioning | prior_knowledge_confirmed | documentdb-local-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md | documentdb-local-deployment | yes |
| P09 | Create indexes that match query filters and sort order (test with explain('executionStats') to confirm the winning plan uses IXSCAN and avoids COLLSCAN) and use projections to return only needed fields. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P10 | Design compound indexes following the ESR rule (Equality → Sort → Range) and order equality fields by selectivity. | indexing | found_in_public_source | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P11 | Use TTL indexes (expireAfterSeconds on a date field) for ephemeral workflow/log documents so old workflow runs are automatically purged. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P12 | For vector search, store embeddings as arrays, normalize them for cosine similarity at ingestion, and store embedding metadata (model name and dimensions) alongside the vector. | vector search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | no |
| P13 | Ensure vector-index creation and vector field usage are validated at write time (dimensions match, model recorded) and treat index creation as an idempotent, explicit operation with correct parameters (kind, dimensions, similarity, tuning knobs). | vector search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | no |
| P14 | Log orchestration/workflow-run state (start/end timestamps, per-step status, messages) as documents so long-running multi-step processes can be tracked and resumed safely. | orchestration and logging | found_in_public_source | src/orchestrator.py (local_file) | **none** | src/orchestrator.py | yes |
| P15 | Enable diagnostic settings and slow-query logging (route to Log Analytics) and use explain()/operation logs to identify slow queries and drive index changes and alerts on saturation metrics. | queries & monitoring | prior_knowledge_confirmed | documentdb-monitoring (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md | documentdb-monitoring | yes |
| P16 | Enable in-region high availability (HA) on production clusters to obtain the 99.99% SLA and automatic zone-level failover; add cross-region replicas for DR and higher SLAs when needed. | high availability | found_in_public_source | documentdb-high-availability (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/high-availability/SKILL.md | documentdb-high-availability | yes |
| P17 | Only shard a collection once it exceeds a single physical shard's capacity, and pick the shard key by workload (read-heavy → localize frequent query filter; write-heavy → high-cardinality, evenly-distributed field). | sharding | found_in_public_source | documentdb-sharding (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/sharding/SKILL.md | documentdb-sharding | yes |
| P18 | Keep documents well under the 16 MB BSON limit and split very large fields or arrays into side collections or bucketed documents to avoid oversized-document and update inefficiencies. | data modeling | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P19 | Include a schemaVersion or document_version field on documents and plan migration scripts or lazy-migration paths so consumers can detect and handle older document shapes. | data modeling | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P20 | For regulated workloads, enable customer-managed keys (CMK) at cluster creation to control encryption-at-rest keys and plan key rotation and recovery runbooks. | security | found_in_public_source | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P21 | Record each orchestration step's status and timestamps in a workflow-run document to support resumability and idempotent retries. | orchestration and logging | prior_knowledge_only | - (prior_knowledge) | **none** | Azure DocumentDB workflow resumable steps best practices; documentdb orchestration logging best practices; azure documentdb workflow-run logging | yes |
| P22 | Use multi-document transactions only when required for atomicity across documents/collections, keep transactions small and short-lived, and validate transaction behavior against the live cluster. | transactions | prior_knowledge_only | - (prior_knowledge) | **none** | azure documentdb transactions guidance; documentdb multi-document transaction best practices; mongodb transactions azure documentdb | yes |
| P23 | Do not write secrets or raw PII into workflow logs or plain documents; redact or encrypt sensitive fields and restrict access via RBAC and network controls. | security | prior_knowledge_only | - (prior_knowledge) | **none** | azure documentdb logs redact PII; documentdb logging PII sensitive data best practices; azure monitor PII redaction guidance | yes |
| P24 | Run integration tests against a real DocumentDB instance (or the documented local Gateway) for behaviors mongomock cannot emulate (indexing, explain plans, vector indexes, transactions). | testing | prior_knowledge_only | - (prior_knowledge) | **none** | documentdb local deployment integration tests; mongomock limitations vector index explain; azure documentdb integration testing guidance | yes |

## Searches that returned nothing useful

- Azure DocumentDB workflow resumable steps best practices
- azure documentdb multi-document transactions guidance
- azure documentdb logs redact PII best practices
- mongomock limitations vector indexes explain azure documentdb

## Notes

Discovery prioritized practices that are directly relevant to the sample app (connection, auth, seeding, indexing, monitoring, data modeling, orchestration logging). Vector-search guidance exists in the installed vector-search skill (included) but the sample code does not exercise vector indexes so those entries are marked not relevant_to_this_app. Four prior beliefs (K11, K13, K17, K18) had no explicit Azure-DocumentDB documentation found in the installed skills or local repo that directly stated them, so they are reported as prior_knowledge_only with the searches attempted listed above.

