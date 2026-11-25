# 5a. Best practices: prior knowledge against the public record: 08-personalized-email-campaign-builder

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**32 practices, 30 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 1 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 2 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 22 | Memory and documentation line up. |
| Found in public sources only | 7 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

## Where public sources contradict the model

### P18: Azure DocumentDB uses compute tiers and per-shard IOPS/throughput characteristics rather than Cosmos DB-style RU accounting; monitor CPU/memory/IOPS and scale the compute/storage tier and alerts accordingly.

- **The model believed:** Monitor request units / consumed throughput and configure autoscale or increase provisioned throughput for the sample_retail_08 database/collections to accommodate vector search and LLM-generation bursts; add alerts on RU consumption. (knowledge of `azure_cosmos_db`)
- **The source says:** Azure DocumentDB uses compute tiers and per-shard IOPS/throughput characteristics rather than Cosmos DB-style RU accounting; monitor CPU/memory/IOPS and scale the compute/storage tier and alerts accordingly.
- **Source:** [documentdb-storage](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/storage/SKILL.md)

## Known to the model, with no public source for this service

| Id | Practice | Knowledge of | Searches tried |
|---|---|---|---|
| P23 | Design writeConcern and readPreference intentionally for cross-replica durability or latency needs, but verify Azure DocumentDB's default mapping and supported features first. | mongodb | Azure DocumentDB writeConcern readPreference; Azure DocumentDB writeConcern support |
| P27 | Avoid sending raw PII to LLMs or retaining it in logs; redact or minimize PII in prompts and encrypt or limit sensitive fields at rest. | general | azure documentdb pii lLM redaction; documentdb privacy logging pii |

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | In serverless environments initialize the MongoClient outside the function handler so the single client and its pool are reused across warm invocations and use small pools (e.g., maxPoolSize 3–5, minPoolSize 0). | connection | found_in_public_source | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P02 | Prefer Microsoft Entra ID (OIDC) authentication with a token-callback (DefaultAzureCredential / managed identity) instead of long-lived DB passwords when possible, using the driver's OIDC callback interface to supply tokens. | authentication_and_secrets | found_in_public_source | Build a Node.js console app with Azure DocumentDB (how-to-build-nodejs-console-app) (public_doc) | https://learn.microsoft.com/azure/documentdb/how-to-build-nodejs-console-app#configure-your-console-application | how to connect azure documentdb with microsoft Entra DefaultAzureCredential | yes |
| P03 | For local development use the DocumentDB Gateway image (Mongo protocol on port 10260) and allow TLS relaxation (tlsAllowInvalidCertificates) only driven by environment variables and never defaulted in production code. | local_development | found_in_public_source | documentdb-local-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md | documentdb-local-deployment | yes |
| P04 | Prefer the provider's textSearch / $search full-text capability instead of the community `$text` index for production lexical search needs on Azure DocumentDB. | indexing | found_in_public_source | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | no |
| P05 | Limit the number of indexes per collection (keep a modest budget, e.g., 5–15 indexes) and regularly review index usage (`$indexStats`) to drop unused indexes that add write cost. | indexing | found_in_public_source | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P06 | Percent-encode reserved characters in usernames/passwords before inserting them into the connection URI and do not commit credentials in source control. | connection | found_in_public_source | Tutorial: Connect a Node.js web app with Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/tutorial-nodejs-web-app#test-the-mern-application-with-the-azure-documentdb-cluster | Azure DocumentDB quickstart Node.js connection string encode password | yes |
| P07 | Enable diagnostic settings and slow-query logs and create alerts on CPU, memory, IOPS, storage, and connection saturation appropriate to your cluster tier for production monitoring. | monitoring | found_in_public_source | documentdb-monitoring (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md | documentdb-monitoring | yes |
| P08 | Reuse a single MongoClient for the life of a Node.js process; do not create a new client per request. | connection | prior_knowledge_confirmed | documentdb-driver (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md | documentdb-driver | yes |
| P09 | Always connect with TLS (tls=true) and do not disable certificate validation in production. | security | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P10 | Do not commit credentials into source control; use environment variables and prefer secrets stores (Key Vault) or managed identities for production secrets management. | authentication_and_secrets | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P11 | Use least-privilege database identities (per-app users or Microsoft Entra RBAC) rather than admin/root credentials for application access. | authentication_and_secrets | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P12 | Avoid building query strings by concatenation; use driver filter objects or parameterized queries so the driver can safely and efficiently apply indexes. | queries | prior_knowledge_confirmed | Quickstart: Use Azure DocumentDB with MongoDB driver for Node.js (public_doc) | https://learn.microsoft.com/azure/documentdb/quickstart-nodejs#code-examples | Azure DocumentDB MongoDB driver examples (quickstart) | yes |
| P13 | Create single-field indexes on fields frequently used in filters or sorts (e.g., segmentId, customerId, createdAt) before using the dataset. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P14 | For vector search define a dedicated embedding field and create the provider-specified vector index (choose DiskANN / HNSW / IVF based on scale), and tune build/search parameters to match recall/latency goals. | vector_search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | no |
| P15 | Normalize embeddings and record the embedding model and dimensionality alongside the vectors; reject or pad vectors of the wrong dimension on write. | data_model | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | no |
| P16 | Use partial or sparse indexes for optional large fields (like embeddings) so only documents with those fields are indexed to avoid index bloat. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | no |
| P17 | Implement retry logic for transient errors and 429 rate-limits with exponential backoff and honor Retry-After when provided. | retries | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P18 | Azure DocumentDB uses compute tiers and per-shard IOPS/throughput characteristics rather than Cosmos DB-style RU accounting; monitor CPU/memory/IOPS and scale the compute/storage tier and alerts accordingly. | provisioning | prior_knowledge_contradicted | documentdb-storage (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/storage/SKILL.md | documentdb-storage | yes |
| P19 | Keep documents well under the 16 MB BSON document limit and store large binary attachments in Blob storage referenced from documents. | data_model | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P20 | Avoid large skip offsets for pagination; prefer keyset (range-based) pagination using a stable sort key (e.g., createdAt + _id bookmark) for efficient paging. | queries | prior_knowledge_confirmed | Pagination guidance and $skip considerations (public_doc) | https://learn.microsoft.com/documentdb/query/operators/aggregation/$skip | Azure DocumentDB pagination skip performance | yes |
| P21 | Create required indexes before seeding or significant reads, and verify indexes at deployment time (listIndexes/listIndexes check) in your provisioning/seed scripts. | operations | prior_knowledge_confirmed | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | documentdb-query-optimizer | yes |
| P22 | Use TTL indexes for ephemeral documents (createIndex with expireAfterSeconds) to automatically expire old campaign drafts or staging documents. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P23 | Design writeConcern and readPreference intentionally for cross-replica durability or latency needs, but verify Azure DocumentDB's default mapping and supported features first. | consistency_and_durability | prior_knowledge_only | - (prior_knowledge) | **none** | Azure DocumentDB writeConcern readPreference; Azure DocumentDB writeConcern support | yes |
| P24 | Make writes idempotent or use upsert (e.g., replaceOne / updateOne with upsert: true) so retries do not create duplicates. | writes | prior_knowledge_confirmed | documentdb-driver (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md | documentdb-driver | yes |
| P25 | Restrict network access to clusters with firewall rules, Private Link (private endpoints) or VNet integration and avoid exposing production cluster endpoints publicly. | security | prior_knowledge_confirmed | Quickstart: Use Azure DocumentDB with MongoDB driver for Node.js (public_doc) | https://learn.microsoft.com/azure/documentdb/quickstart-nodejs#create-an-azure-documentdb-cluster | Azure DocumentDB quickstart networking/firewall guidance | yes |
| P26 | Enable slow-query logging and use explain('executionStats') / indexStats to detect COLLSCANs and add appropriate indexes to avoid collection scans. | performance | prior_knowledge_confirmed | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | documentdb-query-optimizer | yes |
| P27 | Avoid sending raw PII to LLMs or retaining it in logs; redact or minimize PII in prompts and encrypt or limit sensitive fields at rest. | privacy | prior_knowledge_only | - (prior_knowledge) | **none** | azure documentdb pii lLM redaction; documentdb privacy logging pii | yes |
| P28 | Pre-create vector indexes and wait for their build/ready state before running similarity queries to avoid missing or inconsistent recall results. | vector_search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | no |
| P29 | Use projection to fetch only needed fields (partial projection) when building prompts or assembling context to reduce bandwidth, I/O and cost. | queries | prior_knowledge_confirmed | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | documentdb-query-optimizer | yes |
| P30 | Implement application-level retries for transient faults but avoid retrying non-idempotent multi-document transactions unless you can guarantee idempotency or use a deduplication token. | retries | prior_knowledge_confirmed | Reliability in Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/reliability/reliability-documentdb#resilience-to-transient-faults | resilience to transient faults azure documentdb retries guidance | yes |
| P31 | Include provisioning and verification scripts that create collections, desired indexes, and perform a short sample query (listCollections/listIndexes) as part of deployment. | provisioning | prior_knowledge_confirmed | documentdb-local-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md | documentdb-local-deployment | yes |
| P32 | Never log or persist raw connection strings or SAS tokens; use Key Vault references or managed identities and rotate credentials regularly. | authentication_and_secrets | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |

## Searches that returned nothing useful

- Azure DocumentDB writeConcern readPreference
- Azure DocumentDB writeConcern support
- azure documentdb pii lLM redaction
- documentdb privacy logging pii

## Notes

I inspected the app (src/client.js, src/seed.js, src/generate.js). The code follows many recommended patterns (MongoClient singleton, TLS in example URI, env-based secrets, index creation in seed, upserts for segments, projection could be added for prompt fields). The installed domain skills (documentdb-*) provided concrete, actionable best practices for connection pooling, security, indexing, vector search, monitoring, local development and query optimization; Microsoft Learn quickstarts complemented these with connection-string and auth examples. The only clear contradiction was K11 (RUs): Azure DocumentDB uses compute/IOPS/tiers rather than a Cosmos-style RU accounting, so the RU-focused prior belief does not map to this product.

