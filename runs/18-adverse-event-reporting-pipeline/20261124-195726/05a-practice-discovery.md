# 5a. Best practices: prior knowledge against the public record: 18-adverse-event-reporting-pipeline

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**20 practices, 19 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 0 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 1 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 16 | Memory and documentation line up. |
| Found in public sources only | 3 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

## Known to the model, with no public source for this service

| Id | Practice | Knowledge of | Searches tried |
|---|---|---|---|
| P17 | Treat LLM-driven extraction outputs as untrusted: validate, canonicalize, map to controlled vocabularies, log parse confidence, and quarantine ambiguous results rather than writing them directly to production structured fields. | general | Azure DocumentDB LLM extraction validation; Azure DocumentDB OpenAI extraction guidance; LLM output validation best practices (searches ran) |

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Create one MongoClient / driver client per process (a singleton) and reuse it across requests rather than creating a new client per request; tune maxPoolSize for expected concurrency. | connection | prior_knowledge_confirmed | documentdb-driver (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md | documentdb-driver | yes |
| P02 | Do not commit cluster connection strings or credentials to source control; read DOCUMENTDB_URI and other secrets from environment variables or a secret store (for example, Azure Key Vault) and provide only a .env.example placeholder in the repo. | secrets | prior_knowledge_confirmed | Quickstart: Use Azure DocumentDB with MongoDB driver for Python (public_doc) | https://learn.microsoft.com/azure/documentdb/quickstart-python#code-examples | Azure DocumentDB connection string environment variable best practices | yes |
| P03 | Always connect to Azure DocumentDB with TLS enabled (tls=true) and do not disable certificate validation in production. | security | found_in_public_source | Connect to Azure DocumentDB using MongoDB Shell (public_doc) | https://learn.microsoft.com/azure/documentdb/how-to-connect-mongo-shell#connect-with-interactive-password-authentication | Azure DocumentDB MongoDB connection TLS required | yes |
| P04 | Use server-side JSON Schema validation (the MongoDB $jsonSchema validator) where available and also validate/canonicalize inputs in the application; keep the original free-text report in a raw_text field and write parsed typed fields separately. | data_modeling | prior_knowledge_confirmed | $jsonSchema (public_doc) | https://learn.microsoft.com/documentdb/query/operators/evaluation-query/$jsonschema | Azure DocumentDB JSON schema validation $jsonSchema | yes |
| P05 | Create a compound index that matches the aggregation/grouping access pattern (for example { drug: 1, event: 1 }) so the GROUP/COUNT aggregation can be satisfied efficiently rather than scanning the collection. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P06 | For vector similarity search store embeddings in a dedicated top-level field and create an explicit vector index (DiskANN/HNSW/IVF) with parameters (dimensions, similarity metric, maxDegree/lBuild/lSearch) that exactly match your embedding model and query-time similarity. | vector_search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | no |
| P07 | Implement retries with exponential backoff and jitter for transient errors and throttling (HTTP 429); when a Retry-After header is present, honor it rather than retrying immediately. | retries | prior_knowledge_confirmed | Design throttling to improve resilience / Retry-After guidance (public_doc) | https://learn.microsoft.com/azure/well-architected/design-guides/throttling#[tp-5]-respect-backpressure | Azure DocumentDB 429 Retry-After backoff guidance | yes |
| P08 | Rely on the account-level configured consistency (the service maps MongoDB write/read concerns to Cosmos consistency); the default is session-consistency — prefer that rather than trying to emulate strong cross-region consistency in the app. | provisioning | prior_knowledge_confirmed | Consistency levels for Azure Cosmos DB and the API for MongoDB (public_doc) | https://learn.microsoft.com/azure/cosmos-db/mongodb/consistency-mapping | Azure DocumentDB consistency mapping MongoDB API | no |
| P09 | Prefer single-document atomic operations when possible; avoid multi-document transactions for normal workloads because they increase contention and complexity — keep transactions short and retry on conflict when needed. | data_modeling | prior_knowledge_confirmed | Use Multi-document transactions in Azure Cosmos DB for MongoDB (public_doc) | https://learn.microsoft.com/azure/cosmos-db/mongodb/use-multi-document-transactions | Azure DocumentDB transactions best practices | no |
| P10 | For large aggregation pipelines use allowDiskUse:true (where supported), and reduce intermediate sizes by filtering/projecting early (match/project/limit early) to avoid memory pressure. | queries | prior_knowledge_confirmed | aggregate command and aggregation pipeline examples and limitations (public_doc) | https://learn.microsoft.com/documentdb/query/commands/aggregation/aggregate | Azure DocumentDB aggregate allowDiskUse and aggregation best practices | yes |
| P11 | When building or reindexing large indexes, schedule index creation during low-traffic windows and prefer background/index-build-safe approaches; for large data loads, batch inserts rather than single inserts. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P12 | Avoid logging or persisting PHI/PII unnecessarily; if you store raw_text for auditing or re-parsing, protect it with least-privilege access, encryption at rest (CMK when needed), and consider field-level encryption. | security | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P13 | Use a TTL index (expireAfterSeconds on a date field) to implement automated retention/expiry of documents rather than manual delete scripts when appropriate. | data_modeling | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing index-ttl-expiry | no |
| P14 | Enable diagnostics and slow-query logging, collect query performance metrics (explain, keysExamined/docsExamined), and alert on CPU/memory/IOPS/connection saturation for production clusters. | monitoring | prior_knowledge_confirmed | documentdb-monitoring (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md | documentdb-monitoring | no |
| P15 | Use bulk/batched writes (insert_many / bulk API) for seeding and high-throughput ingestion rather than single inserts to reduce round-trips and improve throughput; respect service batch/write limits. | performance | prior_knowledge_confirmed | Document size and batch write limits in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/max-document-size | Azure DocumentDB batch write limits insert_many guidance | yes |
| P16 | Protect the DocumentDB endpoint with network controls: use Private Endpoint / VNet integration or firewall rules and avoid exposing clusters to the public internet when possible. | security | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | no |
| P17 | Treat LLM-driven extraction outputs as untrusted: validate, canonicalize, map to controlled vocabularies, log parse confidence, and quarantine ambiguous results rather than writing them directly to production structured fields. | data_modeling | prior_knowledge_only | - (prior_knowledge) | **none** | Azure DocumentDB LLM extraction validation; Azure DocumentDB OpenAI extraction guidance; LLM output validation best practices (searches ran) | yes |
| P18 | Test durability/writeConcern behavior on the Mongo API because writeConcern/readConcern options are mapped to the account's configured consistency and some Mongo writeConcern behaviors may be limited or differ under the service compatibility layer. | provisioning | prior_knowledge_confirmed | Consistency levels for Azure Cosmos DB and the API for MongoDB (public_doc) | https://learn.microsoft.com/azure/cosmos-db/mongodb/consistency-mapping | Azure DocumentDB writeConcern mapping to account consistency | no |
| P19 | Prefer PyMongo's AsyncMongoClient for async Python workloads (do not rely on Motor in new code) and initialize clients outside request/handler scope so the async client is reused across invocations. | driver | found_in_public_source | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P20 | Use explain('executionStats') and examine keysExamined/docsExamined and winningPlan to verify index usage and identify COLLSCAN or scatter-gather behavior before adding indexes. | queries | found_in_public_source | documentdb-query-optimization (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimization/SKILL.md | documentdb-query-optimization | yes |

## Searches that returned nothing useful

- Azure DocumentDB LLM extraction validation
- Azure DocumentDB guidance LLM outputs untrusted
- Azure DocumentDB best practices for validating LLM-parsed fields

## Notes

I inspected the sample app files (src/main.py, src/models.py, seed.py, README.md, .env.example) and loaded DocumentDB skills and Microsoft docs. Most prior beliefs (K01–K16, K18) are supported by Azure DocumentDB documentation or the installed DocumentDB skills; K17 (LLM output validation) is a strong application-level best practice but I found no Azure DocumentDB-specific public guidance that addresses treating LLM outputs as untrusted, so it is recorded as prior_knowledge_only. Practices most relevant to this app (connection reuse, env secrets, JSON schema validation, compound index for the aggregation, allowDiskUse/project early, bulk inserts for seeding, retries/backoff, and PyMongo async guidance) are tied to explicit docs/skills and marked relevant_to_this_app=true.

Prior beliefs the discovery step did not classify: K03. See 05a-prior-beliefs.json.

