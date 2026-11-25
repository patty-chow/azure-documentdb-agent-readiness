# 5a. Best practices: prior knowledge against the public record: 16-atm-network-status-monitor

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**21 practices, 20 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 0 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 1 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 17 | Memory and documentation line up. |
| Found in public sources only | 3 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

## Known to the model, with no public source for this service

| Id | Practice | Knowledge of | Searches tried |
|---|---|---|---|
| P14 | Prefer explicit, documented guidance for readPreference/readConcern only when the service documents their mapping for the MongoDB driver; do not assume MongoDB defaults map identically without checking Azure DocumentDB compatibility docs. | mongodb | searches: "Azure DocumentDB readPreference readConcern"; "readPreference Azure DocumentDB"; "readConcern Azure DocumentDB" |

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Read the cluster connection string from an environment variable at runtime and never commit credentials to source control; provide an example .env with placeholders only. | auth | prior_knowledge_confirmed | Quickstart: Use Azure DocumentDB with MongoDB driver for Node.js (public_doc) | https://learn.microsoft.com/azure/documentdb/quickstart-nodejs#code-examples | Azure DocumentDB MongoDB connection string SCRAM TLS mongodb+srv "cosmos" "DocumentDB" | yes |
| P02 | Require TLS on all MongoDB connections to Azure DocumentDB and do not disable certificate verification in production. | security | prior_knowledge_confirmed | Quickstart: Use Azure DocumentDB with MongoDB driver for Node.js (public_doc) | https://learn.microsoft.com/azure/documentdb/quickstart-nodejs#code-examples | Azure DocumentDB MongoDB connection string SCRAM TLS mongodb+srv "cosmos" "DocumentDB" | yes |
| P03 | Create and reuse a single MongoClient/Mongoose connection (singleton) and tune pool options for your deployment scenario rather than creating new clients per request. | connection | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P04 | Persist change-stream resume tokens durably (e.g., in a small collection or durable store) so streams can be resumed after restarts or transient errors. | change_streams | prior_knowledge_confirmed | Change streams in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/change-streams#resume-a-change-stream | Azure DocumentDB change streams resume token | yes |
| P05 | Keep heartbeat documents small and split or store large attachments outside the database (for example, Azure Blob Storage) to avoid reaching the 16 MB BSON document limit and to reduce RU spikes. | data_modeling | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P06 | Create indexes that match read/query patterns—use a compound index following the ESR rule (Equality → Sort → Range) such as { atmId: 1, timestamp: -1 } for latest-heartbeat queries and a single-field index on status for fast aggregations. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P07 | Maintain a single network summary document per scope and update it with atomic single-document operations (upsert / $inc / $set) rather than recomputing the whole summary on every change to reduce RU cost and race windows. | data_modeling | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P08 | Avoid multi-document or cross-partition transactions for high-throughput heartbeat ingestion; prefer single-document atomic updates or idempotent upserts and only use transactions when necessary and within documented limits. | transactions | prior_knowledge_confirmed | Use Mongoose with Azure DocumentDB: Build a Node.js inventory API (public_doc) | https://learn.microsoft.com/azure/documentdb/tutorial-nodejs-mongoose#mongoose-on-azure-documentdb | Use Mongoose with Azure DocumentDB tutorial and Azure DocumentDB limitations | yes |
| P09 | Use a TTL index on a Date field to expire old heartbeat documents (or run a controlled background prune job) and understand TTL semantics (date field required, ~60s sweeper granularity, single-field only). | provisioning | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P10 | Monitor request-unit (RU) consumption and index usage and provision sufficient throughput or enable autoscale to handle ingestion spikes from many frequent heartbeats. | provisioning | prior_knowledge_confirmed | Autoscale for Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/autoscale | Azure DocumentDB RU/s autoscale monitor | yes |
| P11 | Implement exponential backoff with jitter for client retries on transient network/429/5xx errors and leverage driver-level retry settings where supported, limiting attempts to avoid thundering retries. | retries | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P12 | When using change streams, apply a server-side aggregation pipeline ($match) to filter events you don't need so you reduce event volume and associated costs. | change_streams | prior_knowledge_confirmed | Change streams in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/change-streams | Azure DocumentDB change streams | yes |
| P13 | Persist alert state (active alerts, lastTriggeredAt) in the database and make alert writes idempotent or deduplicated (use uniqueness constraints or transactional patterns) to avoid duplicate notifications from flapping events. | alerting | prior_knowledge_confirmed | Idempotent Consumer pattern (public_doc) | https://learn.microsoft.com/azure/architecture/patterns/idempotent-consumer#solution | Azure idempotent consumer pattern idempotent writes upsert dedupe | yes |
| P14 | Prefer explicit, documented guidance for readPreference/readConcern only when the service documents their mapping for the MongoDB driver; do not assume MongoDB defaults map identically without checking Azure DocumentDB compatibility docs. | query | prior_knowledge_only | - (prior_knowledge) | **none** | searches: "Azure DocumentDB readPreference readConcern"; "readPreference Azure DocumentDB"; "readConcern Azure DocumentDB" | yes |
| P15 | Model per-ATM current state in a dedicated collection with a unique index on atmId for cheap lookups and fast updates rather than scanning heartbeat history. | data_modeling | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P16 | When using Mongoose, declare strict schemas, explicit indexes, and avoid heavy middleware on the hot insert path; rely on lightweight validation and explicit indexes for performance-sensitive workloads. | development | prior_knowledge_confirmed | Use Mongoose with Azure DocumentDB: Build a Node.js inventory API (public_doc) | https://learn.microsoft.com/azure/documentdb/tutorial-nodejs-mongoose#mongoose-on-azure-documentdb | Use Mongoose with Azure DocumentDB tutorial | yes |
| P17 | For vector-capable clusters, create vector indexes with the appropriate algorithm (DiskANN/HNSW/IVF) and parameters for your dataset, and validate latency and RU-cost with representative vectors before production rollout. | vector_search | prior_knowledge_confirmed | Integrated vector store in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/vector-search#perform-vector-similarity-search | Azure DocumentDB vector search DiskANN HNSW IVF cosmosSearch | no |
| P18 | Do not log the full DOCUMENTDB_URI or any credentials; redact connection strings and only log non-sensitive diagnostics, error codes and connection status. | security | prior_knowledge_confirmed | Quickstart: Use Azure DocumentDB with MongoDB driver for Node.js (public_doc) | https://learn.microsoft.com/azure/documentdb/quickstart-nodejs#code-examples | Azure DocumentDB Quickstart examples and guidance 'Don't include any personal, sensitive, or confidential information in resource names' | yes |
| P19 | Prefer Microsoft Entra ID (OIDC) and role-based access control for authentication instead of long-lived DB passwords; use managed identities when possible. | auth | found_in_public_source | Connect to Azure DocumentDB using role-based access control and Microsoft Entra ID (azure-portal) (public_doc) | https://learn.microsoft.com/azure/documentdb/how-to-connect-role-based-access-control#connect-using-microsoft-entra-id-in-mongodb-compass-or-mongodb-shell | Azure DocumentDB role-based access control Microsoft Entra ID | no |
| P20 | Restrict network access with Private Endpoints / Private Link or firewall rules and avoid exposing clusters to the public internet where possible. | security | found_in_public_source | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P21 | Be aware of change stream limitations: multishard clusters affect resumability and ordering, and some multishard features require enabling a portal feature flag; design your change-stream usage accordingly. | change_streams | found_in_public_source | Change streams in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/change-streams#limitations | Azure DocumentDB change streams limitations | yes |

## Searches that returned nothing useful

- Azure DocumentDB readPreference readConcern
- Azure DocumentDB readConcern mapping
- Azure DocumentDB readPreference majority primary readConcern

## Notes

I inspected the sample app files (db.js, index.js, models, seed etc.) and used Microsoft Learn pages plus installed DocumentDB skills to collect public guidance. Practices P01–P18 correspond to the prior beliefs K01–K18 and are marked confirmed except K14 which had no Azure DocumentDB page explicitly describing readPreference/readConcern mapping for this service (I recorded the searches tried). Additional public practices found: prefer Entra ID/RBAC (P19), network isolation with Private Endpoint/firewall (P20), and change-stream limitations for multishard clusters (P21).

