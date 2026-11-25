# 5a. Best practices: prior knowledge against the public record: 11-preference-center-consent-store

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**22 practices, 19 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 0 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 0 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 18 | Memory and documentation line up. |
| Found in public sources only | 4 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Read the DocumentDB/MongoDB connection string from an environment variable (e.g., DOCUMENTDB_URI) and never commit secrets into code or logs; provide a .env.example with a placeholder only. | secrets | prior_knowledge_confirmed | .env.example / README.md (local_file) | **none** | .env.example | yes |
| P02 | Create a single shared MongoClient (or AsyncMongoClient) at application startup and reuse it across the process rather than creating a client per request. | connection | prior_knowledge_confirmed | documentdb-driver (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md | documentdb-driver | yes |
| P03 | Tune connection-pool parameters (maxPoolSize, minPoolSize, maxIdleTimeMS) according to the runtime (serverless vs long-running) and expected concurrency rather than using arbitrary values. | connection | found_in_public_source | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P04 | Prefer PyMongo's AsyncMongoClient for async Python applications (rather than Motor) because Motor is deprecated for new async code; avoid mixing different driver types at runtime. | runtime | found_in_public_source | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P05 | Use TLS for all connections and do not disable certificate verification in production; ensure tls=true and a valid CA bundle are available to the driver. | security | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P06 | Create a TTL index on a Date field (e.g., retention_expires_at) with expireAfterSeconds (0 for absolute expiry) and remember TTL deletions are performed by a background job and can lag (not sub-minute precise). | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P07 | Model consent as append-only history embedded in the consent document for auditability, but if history can grow unbounded split it into a separate collection to avoid large-document problems. | data_modeling | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P08 | Keep documents well under the 16 MB BSON limit: cap arrays, compress or spill large fields to child collections, and plan for steady-state growth, not just current size. | data_modeling | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P09 | Perform atomic single-document updates (e.g., findOneAndUpdate / updateOne with $push and $set or $each/$slice) to append history and update derived fields in one operation and avoid partial updates and race windows. | queries | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P10 | Use optimistic concurrency (include a version or lastUpdated in update filters) when updates cannot safely be lost to concurrent requests. | data_modeling | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P11 | Enable driver retry options (retryWrites=true, retryReads=true) and implement application-level retries with exponential backoff for transient errors while ensuring write idempotency where needed. | retries | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P12 | When you require the freshest read (e.g., current consent state), read from the primary; cross-region replicas are asynchronous and can return stale data. | queries | prior_knowledge_confirmed | documentdb-high-availability (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/high-availability/SKILL.md | documentdb-high-availability | yes |
| P13 | Multi-document transactions are supported but have limitations (e.g., supported within an unsharded collection and dependent on server-wire-protocol version); verify your cluster/server version before relying on cross-document transactions. | queries | prior_knowledge_confirmed | Microsoft Learn — Use Multi-document transactions in Azure Cosmos DB for MongoDB (public_doc) | https://learn.microsoft.com/azure/cosmos-db/mongodb/use-multi-document-transactions | Azure Cosmos DB for MongoDB transactions support | no |
| P14 | Pin and verify compatible driver and ODM versions (PyMongo/AsyncMongoClient, Motor, Beanie) to the cluster's MongoDB wire protocol to avoid runtime incompatibilities and test on the target cluster version. | runtime | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P15 | When using an ODM (e.g., Beanie), use its model validation for input validation but also consider defense-in-depth because collection-level JSON schema support may vary; check service feature support for validator/$jsonSchema on your target server version. | data_modeling | prior_knowledge_confirmed | Microsoft Learn — $jsonSchema / feature support (public_doc) | https://learn.microsoft.com/documentdb/query/operators/evaluation-query/$jsonschema | Azure Cosmos DB for MongoDB $jsonSchema feature search | yes |
| P16 | Mask or redact connection strings and secrets in logs, exceptions, and telemetry; use structured logging with sensitive-field scrubbing. | security | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P17 | Create and maintain indexes that support your API query patterns (equality → sort → range design, ESR ordering) and periodically inspect query plans with explain("executionStats") to detect and fix COLLSCANs. | operations | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P18 | For vector search create a dedicated fixed-dimension vector field and a provider-specific vector index (choose DiskANN/HNSW/IVF by scale), normalize embeddings for cosine similarity, and tune index/query parameters (lBuild, lSearch, maxDegree). | vector_search | found_in_public_source | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | no |
| P19 | Avoid mixing synchronous and asynchronous drivers in the runtime path (e.g., don't run pymongo sync client and Motor in the same event loop); if you must, keep them isolated (e.g., synchronous seeding scripts separate from async app runtime). | runtime | prior_knowledge_confirmed | scripts/seed.py (comment) and documentdb-connection (local_file) | **none** | scripts/seed.py | yes |
| P20 | Provision the cluster size / compute tier and throughput appropriate to expected write/read workload patterns (use autoscale where helpful) and monitor for 429 throttling to trigger scaling/back-off. | provisioning | prior_knowledge_confirmed | documentdb-storage (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/storage/SKILL.md | documentdb-storage | yes |
| P21 | Include actor, timestamp and reason metadata in each appended history entry so consent changes form a clear, auditable, immutable trail. | operations | prior_knowledge_confirmed | app/models.py and scripts/seed.py (local_file) | **none** | app/models.py | yes |
| P22 | On Azure DocumentDB prefer the native 'textSearch' + $search capabilities instead of community $text indexes when building full-text search experiences. | indexing | found_in_public_source | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | no |

## Searches that returned nothing useful

- Azure DocumentDB Beanie ODM best practices
- Azure DocumentDB Beanie create TTL index Beanie
- Azure DocumentDB 'consentVersion' optimistic concurrency example

## Notes

Discovery combined workspace-local evidence (app files and seed script), installed DocumentDB skills, and Microsoft Learn search results; most prior beliefs (K01–K13, K15–K20) are supported by the public guidance for Azure DocumentDB. The Microsoft Learn pages were used to confirm transactional and TTL semantics where noted.

Prior beliefs the discovery step did not classify: K07, K17. See 05a-prior-beliefs.json.

