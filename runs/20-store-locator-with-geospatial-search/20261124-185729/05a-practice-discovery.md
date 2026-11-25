# 5a. Best practices: prior knowledge against the public record: 20-store-locator-with-geospatial-search

A model first listed the best practices it knew from training, with no tools. An agent then searched public sources without the team's checklist, the way an agent building this app would, and checked each prior belief against what it found.

**27 practices, 24 with a public address.**

| Outcome | Count | What it means |
|---|---|---|
| The model believed otherwise; public sources contradict it | 0 | An agent working from memory builds the wrong thing here. |
| The model knows it; no public source for this service says either way | 2 | Agents will act on it. Nothing public says whether they should. |
| The model knew it, and public sources agree | 20 | Memory and documentation line up. |
| Found in public sources only | 5 | Documented; the model did not list it beforehand. |

## Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

## Known to the model, with no public source for this service

| Id | Practice | Knowledge of | Searches tried |
|---|---|---|---|
| P17 | When using Mongoose in production, avoid enabling autoIndex; prefer controlled index builds as part of deployment (note: I could not find an Azure DocumentDB documentation page specifically about Mongoose autoIndex). | mongodb | searches: "Mongoose autoIndex Azure DocumentDB", "Mongoose autoIndex documentdb", "disable autoIndex production mongoose azure" |
| P18 | Validate and sanitize latitude/longitude input ranges (lat between -90 and 90, lon between -180 and 180) and enforce a reasonable maximum radius for geospatial queries to prevent abusive or expensive queries. | general | searches: "validate lat lon input azure documentdb", "sanitize geospatial query radius best practice" |

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Read the cluster connection string from an environment variable at runtime and do not commit cluster URIs or secrets to source control; provide a .env.example with a placeholder instead. | authentication_and_secrets | prior_knowledge_confirmed | documentdb-local-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md | documentdb-local-deployment | yes |
| P02 | Always connect to Azure DocumentDB with TLS enabled and validate server certificates in production (do not disable certificate verification in production). | security | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P03 | Use least-privilege credentials for application access (prefer Microsoft Entra ID / RBAC or per-app users with minimal roles rather than cluster admin/root credentials). | authentication_and_secrets | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P04 | Create a single MongoClient / Mongoose connection and reuse it for the process (singleton client pattern) rather than creating a new client per request. | connection_handling | prior_knowledge_confirmed | documentdb-driver (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md | documentdb-driver | yes |
| P05 | Set sensible connection and socket timeouts and configure the connection pool (maxPoolSize, minPoolSize, socketTimeoutMS, serverSelectionTimeoutMS) appropriate to your environment to avoid hanging operations or pool exhaustion. | connection_handling | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P06 | Model GeoJSON Points as objects with type:'Point' and coordinates:[longitude, latitude] and validate the type and coordinate array shape in your schema. | data_modeling | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P07 | Create a 2dsphere index on the GeoJSON location field (e.g., createIndex({ location: '2dsphere' })) before relying on geospatial queries and verify the index exists on the collection. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P08 | Create required indexes as part of deployment or controlled migration steps (index creation scripts or ops manifests) rather than relying on Mongoose autoIndex in production; use autoIndex only in development. | indexing | prior_knowledge_confirmed | documentdb-local-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md | documentdb-local-deployment | yes |
| P09 | Use an aggregation with a $geoNear stage (supplying near: { type:'Point', coordinates:[lng,lat] }, distanceField and maxDistance in meters) to both filter by radius and rank results by distance. | geo_queries | found_in_public_source | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P10 | When performing sphere-based geospatial queries, ensure GeoJSON coordinates are [lng, lat] and include spherical: true (or use the sphere-aware operator) so distances are computed on an earth-like sphere; use distanceMultiplier to convert units if needed. | geo_queries | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P11 | Project only the fields the client needs (limit returned fields such as location, distance, hours, stock) to reduce network payload and RU/I/O consumption. | query_performance | prior_knowledge_confirmed | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | documentdb-query-optimizer | yes |
| P12 | Use pagination (limit + skip or range-based cursors) for large result sets and avoid unbounded queries to prevent resource overconsumption and huge responses. | query_performance | prior_knowledge_confirmed | documentdb-full-text-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/full-text-search/SKILL.md | documentdb-full-text-search | yes |
| P13 | Implement retries with exponential backoff for transient errors and on rate-limited responses (HTTP 429), and honor Retry-After headers when provided. | retries | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P14 | Handle common driver and server errors (connection timeout, network errors, cursor timeouts, server 5xx) and return appropriate HTTP statuses from the API rather than leaking internal errors. | error_handling | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P15 | Make seed scripts idempotent: check existence or upsert documents and create indexes only if missing so the script can be safely re-run in CI/ops. | seed_data | prior_knowledge_confirmed | seed/seed.js (local_file) | **none** | seed/seed.js | yes |
| P16 | Monitor query performance and index usage (use explain('executionStats') or MCP explain_operation and ensure geospatial queries use a 2dsphere index rather than scanning the collection). | monitoring | prior_knowledge_confirmed | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | documentdb-query-optimizer | yes |
| P17 | When using Mongoose in production, avoid enabling autoIndex; prefer controlled index builds as part of deployment (note: I could not find an Azure DocumentDB documentation page specifically about Mongoose autoIndex). | mongoose | prior_knowledge_only | - (prior_knowledge) | **none** | searches: "Mongoose autoIndex Azure DocumentDB", "Mongoose autoIndex documentdb", "disable autoIndex production mongoose azure" | yes |
| P18 | Validate and sanitize latitude/longitude input ranges (lat between -90 and 90, lon between -180 and 180) and enforce a reasonable maximum radius for geospatial queries to prevent abusive or expensive queries. | security | prior_knowledge_only | - (prior_knowledge) | **none** | searches: "validate lat lon input azure documentdb", "sanitize geospatial query radius best practice" | yes |
| P19 | Do not add vector indexes to collections that do not need them; keep vector and geo workloads separated into different collections when possible to avoid unnecessary storage and compute overhead. | vector_search | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | no |
| P20 | When creating vector indexes choose the right engine (DiskANN / HNSW / IVF) and tune parameters (lBuild, lSearch, maxDegree) and normalize embeddings for cosine similarity to balance recall and latency. | vector_search | found_in_public_source | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | no |
| P21 | Provision cluster compute and storage according to workload: pick compute tier for IOPS/throughput (Premium SSD v2 gates IOPS by compute tier) and size storage for capacity, not IOPS. | provisioning | prior_knowledge_confirmed | documentdb-storage (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/storage/SKILL.md | documentdb-storage | yes |
| P22 | Avoid starting long-running or blocking index builds during peak traffic; run index builds during maintenance windows or use the provider’s recommended background/online build options. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P23 | Give indexes meaningful names and include index definitions in deployment manifests or migration scripts so operators can reconcile indexes created by the app versus ops tooling. | operational_practices | prior_knowledge_confirmed | documentdb-full-text-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/full-text-search/SKILL.md | documentdb-full-text-search | yes |
| P24 | Log aggregation pipelines and explain() output in non-sensitive debugging logs when diagnosing query performance, but avoid logging connection strings, credentials, or other secrets. | monitoring | prior_knowledge_confirmed | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | documentdb-query-optimizer | yes |
| P25 | For local development using the DocumentDB Gateway Docker image, connect on port 10260 with TLS and, if necessary for local self-signed certs, relax validation only under explicit env control (tlsAllowInvalidCertificates), but never default to relaxed TLS in code. | local_development | found_in_public_source | documentdb-local-deployment (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md | documentdb-local-deployment | yes |
| P26 | Prefer Microsoft Entra ID with RBAC and customer-managed keys (CMK) for production clusters with compliance requirements rather than only long-lived passwords or default service-managed keys. | security | found_in_public_source | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P27 | Use diagnostic settings and slow-query logs (export to Log Analytics) and alert on CPU, memory, IOPS, storage and connection saturation per cluster tier to detect resource pressure early. | monitoring | found_in_public_source | documentdb-monitoring (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md | documentdb-monitoring | yes |

## Searches that returned nothing useful

- Mongoose autoIndex Azure DocumentDB
- validate lat lon input azure documentdb
- site:microsoft.com "Mongoose autoIndex"
- azure documentdb $geoNear must be first stage

## Notes

I inspected the sample app (src/* and seed/) and loaded DocumentDB domain skills; most prior beliefs about connection handling, TLS, indexing, geoJSON, retries, seeding and monitoring are supported by the installed DocumentDB skills and resources. Two prior beliefs (K17 about Mongoose autoIndex and K18 about input validation) had no specific Azure DocumentDB documentation in the available skills; they remain prior_knowledge_only. Vector-search guidance exists in the vector-search skill and recommends keeping vector and geo workloads separate and tuning index engines, but the sample app does not use vector indexes.

Prior beliefs the discovery step did not classify: K09. See 05a-prior-beliefs.json.

