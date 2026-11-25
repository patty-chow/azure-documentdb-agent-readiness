# 5a. Best practices: prior knowledge against the public record: 14-telehealth-session-summarizer

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**24 practices, 22 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 2 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 0 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 18 | Memory and documentation line up. |
| Found in public sources only | 4 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

## Where public sources contradict the model

### P12: Do not rely on client-specified MongoDB writeConcern to change durability on Azure DocumentDB: the service maps write durability to the account consistency and ignores client writeConcern parameters.

- **The model believed:** Use appropriate writeConcern for the use case: for clinical summaries prefer acknowledged writes (w=majority or w=1 with journaling) rather than unacknowledged, and allow the app to surface write failures to operators. (knowledge of `general`)
- **The source says:** Do not rely on client-specified MongoDB writeConcern to change durability on Azure DocumentDB: the service maps write durability to the account consistency and ignores client writeConcern parameters.
- **Source:** [Azure Docs — Supported features and syntax (MongoDB) / Write Concern](https://learn.microsoft.com/azure/cosmos-db/mongodb/feature-support-36#time-to-live-ttl)

### P14: Azure Cosmos DB for MongoDB accounts do not provide MongoDB collection-level JSON Schema enforcement in the same way some MongoDB distributions do, so JSON-Schema-based validators are not generally supported for data governance on this API.

- **The model believed:** Add schema validation (JSON Schema) on the summaries collection to enforce required fields and datatypes (patientId as string/UUID, createdAt as date, summary fields as strings) to catch bad writes early. (knowledge of `mongodb`)
- **The source says:** Azure Cosmos DB for MongoDB accounts do not provide MongoDB collection-level JSON Schema enforcement in the same way some MongoDB distributions do, so JSON-Schema-based validators are not generally supported for data governance on this API.
- **Source:** [Azure Docs — Compare Azure Cosmos DB for MongoDB to MongoDB Atlas](https://learn.microsoft.com/azure/cosmos-db/mongodb/compare-mongodb-atlas#data-features-and-capabilities)

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Read the Azure DocumentDB/MongoDB connection string from an environment variable at runtime and never commit or log the URI or credentials. | authentication_and_secrets | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P02 | Create one process-wide MongoClient and reuse it (singleton) rather than creating a client per request; tune maxPoolSize to match expected concurrency. | connection_handling | prior_knowledge_confirmed | documentdb-driver (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md | documentdb-driver | yes |
| P03 | Require TLS on all connections to the cluster and do not disable certificate verification in production. | connection_handling | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P04 | Do not store secrets in source control; provide a .env.example with placeholders and load real secrets from environment variables or a secret store at runtime. | authentication_and_secrets | prior_knowledge_confirmed | README.md / .env.example (local_file) | **none** | .env.example / README.md | yes |
| P05 | Create a single-field index on patientId (and make index creation idempotent as part of seeding/migrations) to support lookups rather than relying on collection scans. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P06 | When common lookups include patientId plus a sort or timestamp, create a compound index following the ESR rule (Equality → Sort → Range), e.g., { patientId: 1, createdAt: -1 }. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P07 | Keep individual documents well under the 16 MB BSON limit; split or chunk large transcripts into separate documents or a child collection to avoid failed writes and poor performance. | data_modeling | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P08 | Model a structured clinical summary as a compact typed document (patientId, chief_complaint, assessment, plan, follow_up, createdAt, schemaVersion, sourceTranscriptId) stored in its own collection rather than embedding large transcripts. | data_modeling | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P09 | If storing LLM embeddings, store them as numeric arrays in a dedicated embeddings field and create a matching vector index (cosmosSearch) with the correct dimensions and similarity type at index-creation time. | vector_search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | no |
| P10 | When creating a vector index specify index metadata (dimensions, similarity like COS/L2/IP, index kind DiskANN/HNSW/IVF) and validate embedding length at write time; rebuild the index if you change embedding model or dimensions. | vector_search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | no |
| P11 | Implement application-level retries with exponential backoff for transient errors, and optionally enable driver retryable-writes only if the account capability for retryable writes is enabled on the cluster. | retries | prior_knowledge_confirmed | Azure Docs — Supported features and syntax (MongoDB) / Retryable writes (public_doc) | https://learn.microsoft.com/azure/cosmos-db/mongodb/feature-support-50#retryable-writes | cosmos db mongodb retryable writes | yes |
| P12 | Do not rely on client-specified MongoDB writeConcern to change durability on Azure DocumentDB: the service maps write durability to the account consistency and ignores client writeConcern parameters. | provisioning_and_safety | prior_knowledge_contradicted | Azure Docs — Supported features and syntax (MongoDB) / Write Concern (public_doc) | https://learn.microsoft.com/azure/cosmos-db/mongodb/feature-support-36#time-to-live-ttl | cosmos db mongodb write concern client ignored | yes |
| P13 | Limit returned fields with projection (select only required fields) to reduce bandwidth and memory, and avoid returning raw transcript text in list endpoints. | queries | prior_knowledge_confirmed | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | documentdb-query-optimizer | yes |
| P14 | Azure Cosmos DB for MongoDB accounts do not provide MongoDB collection-level JSON Schema enforcement in the same way some MongoDB distributions do, so JSON-Schema-based validators are not generally supported for data governance on this API. | data_modeling | prior_knowledge_contradicted | Azure Docs — Compare Azure Cosmos DB for MongoDB to MongoDB Atlas (public_doc) | https://learn.microsoft.com/azure/cosmos-db/mongodb/compare-mongodb-atlas#data-features-and-capabilities | cosmos db mongodb json schema validation supported | yes |
| P15 | Avoid expensive unindexed queries in production; capture and inspect query plans with explain("executionStats") and use index changes as part of deployable migration scripts. | indexing | prior_knowledge_confirmed | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | documentdb-query-optimizer | yes |
| P16 | Use TTL indexes for ephemeral data (session logs, caches) by creating an index with expireAfterSeconds on a date field rather than running ad-hoc deletion scripts. | provisioning_and_safety | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | no |
| P17 | Enable diagnostic settings and slow-query / operation logs and send them to Log Analytics (or Event Hub/Storage) so you can detect slow queries and alert on CPU, memory, IOPS, storage, and connection saturation. | monitoring | prior_knowledge_confirmed | documentdb-monitoring (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md | documentdb-monitoring | yes |
| P18 | Treat patient-identifying data as sensitive: enforce network isolation (Private Endpoint / firewall), use Microsoft Entra ID + RBAC for operational access, and use customer-managed keys (CMK) for encryption-at-rest when required. | security | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P19 | Make seed scripts idempotent (upserts / create-if-not-exists) and keep seed/index scripts versioned and in source control for dev/prod parity. | testing_and_deployment | prior_knowledge_confirmed | documentdb-local-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md | documentdb-local-deployment | yes |
| P20 | In tests and CI avoid using production secrets or customer data; run tests against a dedicated test database (e.g., sample_healthcare_14) and clean up or isolate test artifacts. | testing_and_deployment | prior_knowledge_confirmed | README.md / documentdb-local-deployment (local_file) | **none** | README.md and documentdb-local-deployment | yes |
| P21 | Tune connection-pool and timeout parameters to the app context (serverless vs long-running server); initialize clients outside handlers for serverless so connections survive warm invocations. | connection_handling | found_in_public_source | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P22 | Normalize embeddings to unit length when using cosine similarity and store embedding model name and dimension metadata alongside vectors for drift detection and safe reindexing. | vector_search | found_in_public_source | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | no |
| P23 | Choose vector index kind by scale: prefer vector-diskann for production large-scale, vector-hnsw for medium (up to ~50k), and vector-ivf for very small datasets, and tune maxDegree, lBuild and lSearch accordingly. | vector_search | found_in_public_source | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | no |
| P24 | Prefer Azure DocumentDB's textSearch / $search capabilities for full-text search functionality rather than MongoDB's community $text index. | indexing | found_in_public_source | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | no |

## Searches that returned nothing useful

None.

## Notes

I inspected the app files (src/, scripts/) and used the installed DocumentDB skills plus Microsoft Learn queries. All 20 prior beliefs were matched to the public record: most are confirmed; K12 and K14 are contradicted by Azure Cosmos DB for MongoDB docs (writeConcern is ignored / mapped to account consistency; JSON-Schema collection-level enforcement is not supported). Vector-search guidance exists but the sample app does not create a vector index by default (README notes this).

