# 5a. Best practices: prior knowledge against the public record: 05-branch-performance-analytics

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
| P17 | Rate-limit and validate user inputs on expensive endpoints (e.g., refresh and ask); authenticate and authorize refresh operations to avoid accidental large refresh jobs or expensive LLM/vector queries from untrusted callers. | general | Azure DocumentDB rate limit API protect endpoints; DocumentDB rate limiting recommendations; DocumentDB DoS protection application rate limiting |

## All practices

| Id | Practice | Category | Basis | Source | Public address | How it was found | Applies to this app |
|---|---|---|---|---|---|---|---|
| P01 | Read the DocumentDB connection string from an environment variable or secret provider at runtime and never commit credentials or connection strings to source control. | authentication/secrets | prior_knowledge_confirmed | Quickstart: Connect Mongoose to Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/quickstart-nodejs-mongoose#prerequisites | Azure DocumentDB connection string environment variable best practices DOCUMENTDB_URI | yes |
| P02 | Create one long-lived MongoClient per process (a singleton) and reuse it across requests rather than creating a client per request. | connection handling | prior_knowledge_confirmed | documentdb-driver (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md | documentdb-driver | yes |
| P03 | Always use TLS for connections and restrict access with network controls (Private Endpoint / VNet or firewall rules) rather than relying only on username/password. | security/network | prior_knowledge_confirmed | documentdb-security (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md | documentdb-security | yes |
| P04 | Store each branch's rolled-up summary as one document targeted by branchId and maintain it with targeted updateOne(..., upsert:true); use a unique index on the branch id when branchId is the natural key. | data modeling/indexing | prior_knowledge_confirmed | update (public_doc) | https://learn.microsoft.com/documentdb/query/commands/query-and-write/update#examples | Azure DocumentDB upsert updateOne | yes |
| P05 | If you want automatic expiry of rolled-up caches, create a TTL index on a Date field (e.g., lastRefreshed) with expireAfterSeconds; TTL requires the field be a Date and cannot be a compound or multikey index. | data modeling/retention | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P06 | Create compound indexes that match the aggregation pipeline's $match shape (apply the ESR rule: Equality → Sort → Range) so aggregation can use indexes before expensive stages like $facet. | indexing | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P07 | Push restrictive $match and $project stages as early as possible in aggregation pipelines and include only fields needed by subsequent stages to reduce memory and CPU during $facet and grouping. | queries/aggregation | prior_knowledge_confirmed | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | documentdb-query-optimizer | yes |
| P08 | When running heavy aggregation pipelines, set allowDiskUse=true (or the driver equivalent) and test with explain() so operations that need disk spill are allowed and to avoid memory rejection; use paged or incremental refresh for very large datasets. | aggregation/performance | prior_knowledge_confirmed | aggregate (public_doc) | https://learn.microsoft.com/documentdb/query/commands/aggregation/aggregate | Azure DocumentDB aggregation allowDiskUse | yes |
| P09 | Use explain("executionStats") and the MCP or diagnostic tools to inspect query and aggregation plans (IXSCAN vs COLLSCAN, keysExamined/docsExamined) and fix COLLSCANs before shipping. | debugging/monitoring | prior_knowledge_confirmed | documentdb-query-optimizer (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md | documentdb-query-optimizer | yes |
| P10 | Implement retries with exponential backoff for transient network errors and rate-limiting responses, and prefer idempotent operations when retrying to avoid duplicates. | retries/resiliency | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P11 | Enable driver retryableReads/retryableWrites when supported and set sensible timeouts (connectTimeoutMS, serverSelectionTimeoutMS) so the app fails fast under misconfiguration instead of hanging. | connection handling/retries | prior_knowledge_confirmed | documentdb-connection (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md | documentdb-connection | yes |
| P12 | For a refresh job, perform an atomic per-branch upsert (updateOne with filter on branchId and upsert:true) so refreshes are safe if retried or interrupted. | data integrity | prior_knowledge_confirmed | Quickstart: Use Azure DocumentDB with MongoDB driver for Python (public_doc) | https://learn.microsoft.com/azure/documentdb/quickstart-python#code-examples | Azure DocumentDB update upsert updateOne | yes |
| P13 | Avoid multi-document transactions unless necessary: prefer single-document designs or eventual-consistency update patterns and use multi-document transactions only after evaluating latency/throughput impact. | transactions | prior_knowledge_confirmed | documentdb-data-modeling (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md | documentdb-data-modeling | yes |
| P14 | Create indexes on fields used for top-N queries or dashboard sorts (or create a compound index matching equality+sort) to avoid in-memory sorts and speed ordered list endpoints. | indexing/performance | prior_knowledge_confirmed | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |
| P15 | When using vector search, store embeddings as numeric arrays and create a DocumentDB vector index with the exact dimensions and similarity (COS/L2/IP); prefer DiskANN for production scale and tune maxDegree, lBuild and query-time lSearch for the recall/latency tradeoff. | vector search/indexing | prior_knowledge_confirmed | documentdb-vector-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md | documentdb-vector-search | yes |
| P16 | Keep third-party API keys (OpenAI, embedding providers) out of the repository and require them as runtime secrets (e.g., OPENAI_API_KEY) so the app has a clear no-op fallback in tests/CI. | authentication/secrets/third-party | prior_knowledge_confirmed | Use LlamaIndex with Azure DocumentDB (public_doc) | https://learn.microsoft.com/azure/documentdb/query-knowledge-base#llamaindex-azure-documentdb-integration | Azure DocumentDB LlamaIndex store connection string | yes |
| P17 | Rate-limit and validate user inputs on expensive endpoints (e.g., refresh and ask); authenticate and authorize refresh operations to avoid accidental large refresh jobs or expensive LLM/vector queries from untrusted callers. | security/api design | prior_knowledge_only | - (prior_knowledge) | **none** | Azure DocumentDB rate limit API protect endpoints; DocumentDB rate limiting recommendations; DocumentDB DoS protection application rate limiting | yes |
| P18 | Monitor collection- and cluster-level metrics (CPU, memory, IOPS, storage, connections), enable slow-query logging/diagnostics to Log Analytics, and add alerts for sustained saturation or throttling so you can scale or optimize indexes proactively. | monitoring/provisioning | prior_knowledge_confirmed | documentdb-monitoring (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md | documentdb-monitoring | yes |
| P19 | Prefer the DocumentDB search index + $search (createSearchIndexes + $search) and BM25 scoring for full-text search; use fuzzy/phrase settings and custom analyzers rather than the community $text operator. | full-text search | found_in_public_source | documentdb-full-text-search (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/full-text-search/SKILL.md | documentdb-full-text-search | yes |
| P20 | Enable in-region HA (availability-zone placement) for production clusters to get the 99.99% SLA and add a cross-region replica for 99.995% SLA when you need DR; understand the synchronous in-region model vs asynchronous cross-region replica RPO. | high availability/disaster recovery | found_in_public_source | documentdb-high-availability (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/high-availability/SKILL.md | documentdb-high-availability | yes |
| P21 | Keep an index budget per collection (review $indexStats) and prefer 5–15 well-chosen indexes; hide/drop unused indexes rather than accumulating overlapping single-field indexes. | indexing/maintenance | found_in_public_source | documentdb-indexing (installed_skill) | https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md | documentdb-indexing | yes |

## Searches that returned nothing useful

None.

## Notes

I inspected the app to learn which areas matter (connection/auth, aggregation/upsert, indexes, caching, simple lexical retrieval and optional vector/LLM integration) and then searched public Microsoft docs and the installed DocumentDB skills. Almost all prior beliefs (K01–K16, K18, etc.) are confirmed by Azure DocumentDB public docs or the installed skill guidance; only K17 (rate-limiting/endpoint hardening) is an application-level prior belief for which I found no Azure-DocumentDB-specific public guidance and so it is listed as prior_knowledge_only. Installed skills were used as authoritative sources for index, vector, connection, security, and monitoring guidance; Microsoft Learn pages provide confirmation for aggregation options (allowDiskUse), upsert semantics, and quickstart secret-handling guidance.

