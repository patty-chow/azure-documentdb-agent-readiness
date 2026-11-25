# 5. Best-practice audit: 19-cross-sell-recommendation-beanie

**Verdict: fail** (25 not assessable, 1 violated)

The builder produced a complete design and plans but created no repository files or runnable code in this workspace. Because the sample files, scripts and runnable endpoints are missing, every reference requirement that needs code or artifacts is unfulfilled. The discovery phase correctly found many DocumentDB best-practices and skills (vector-index creation, client reuse, TLS, embedding normalization, atomic $inc upserts, batching embeddings, etc.). One logged build decision (D004: Beanie + motor) contradicts skill guidance that recommends PyMongo's AsyncMongoClient for new async Beanie code; that decision is marked wrong below. Key documentation and agent-discoverability gaps (schema canonicalization for unordered pairs, explicit affinity formula, an idempotent seed script, and a comprehensive .env.example) remain and would likely lead an agent or developer to make inconsistent choices if left unaddressed.

## Review of the builder's decisions

| Decision | What was decided | Reason came from | Assessment | Comment |
|---|---|---|---|---|
| D001 | I approved the build with readiness 'ready_with_gaps' | operator | sound | Approving the build lifecycle as 'ready_with_gaps' is an operator decision. The events trace shows readiness searches and discovery of gaps; the decision is consistent with the readiness report. |
| D002 | I chose to use the Python runtime available on the machine (Python 3.13.13) and implement an async FastAPI service with uvicorn. | readiness_report | sound | Choosing Python 3.13.13 and FastAPI is consistent with the readiness report showing Python 3.13 available on PATH. events.jsonl includes the readiness discovery that Python 3.13 is present (used as evidence). |
| D003 | I chose FastAPI for an async HTTP service (uvicorn) to match the async Beanie/Motor usage. | prompt | sound | Choosing FastAPI for an async service is reasonable and supported by the prompt. The events trace contains a log_decision for this choice. |
| D004 | I chose Beanie ODM (beanie>=1.21.1) with motor for async MongoDB access, as the sample requests Beanie specifically. | prompt | wrong | D004 chose 'Beanie ODM with motor' for async MongoDB access. The loaded skills and quickstart docs (seen in events.jsonl and the Beanie quickstart discovered above) recommend using PyMongo's AsyncMongoClient with Beanie 2.x rather than Motor for new async code. The events show the documentdb-connection and documentdb-driver skills were loaded, thus the guidance was available; the decision contradicts that guidance. |

Documentation gaps: 8 (see `doc-gaps.md`).

## Appendix

### Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

### Public availability of best practices

| Outcome | Count | What it means |
|---|---|---|
| On the checklist, no public source found | 0 | Not public, or not written down. A documentation gap. |
| On the checklist, found only when searched for by name | 3 | Public but hard to find. A discoverability gap. |
| Found publicly, not on the checklist | 2 | Add it to the checklist, or check that the public guidance is what the team intends. |
| Known to the model, no public source, not on the checklist | 0 | Agents will act on it from memory. Decide whether it holds for this service, then document it either way. |
| On the checklist and found by open discovery | 21 | Public and discoverable. |

#### On the checklist, found only when searched for by name

| Topic | Searched for | Sources |
|---|---|---|
| Driver version pinning | Pin the driver version to one the service supports.<br>**Searches:** Searched the Beanie quickstart; it states tested Beanie 2.2.0 and PyMongo 4.19.0. | [Quickstart: Connect Beanie to Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/quickstart-python-beanie#prerequisites) |
| .env.example provided | Provide a .env.example listing required settings.<br>**Searches:** Searched quickstart and tutorial pages for .env examples; found illustrative .env in docs. | [Quickstart: Connect Beanie to Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/quickstart-python-beanie) |
| Engine & compatibility | Verify MongoDB wire protocol and operator compatibility for the chosen driver and server version.<br>**Searches:** Searched Azure DocumentDB compatibility docs; found wire protocol and operator coverage info. | [MongoDB Query Language (MQL) compatibility in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/compatibility-query-language) |

#### Found publicly, not on the checklist

| Topic | Description | Sources |
|---|---|---|
| Audit trail: embedding model choice not logged | Choices made but not logged: chosen OpenAI embedding model (text-embedding-3-small) appears in builder_report but is not recorded as a decision. | build report (no public address recorded) |
| Audit trail: affinity scoring formula not logged | Affinity scoring formula was selected in the plan but not logged as a decision. | build report (no public address recorded) |

#### On the checklist and found by open discovery

| Topic | Description | Sources |
|---|---|---|
| Singleton client reuse | Create a single MongoClient (singleton) per process and reuse it for the application lifetime rather than creating a client per request. | documentdb-driver/driver-singleton-client<br>documentdb-driver/driver-singleton-client |
| TLS enforcement | Require TLS on the wire and do not disable certificate validation in production when connecting to Azure DocumentDB. | documentdb-security/security-tls-required<br>documentdb-security/security-tls-required |
| Connection pool tuning | Tune connection-pool and timeout settings for the expected concurrency pattern. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Retryable writes / retryWrites flag | Azure DocumentDB's connection string commonly includes retryWrites=false because the service does not support retryable writes; verify driver defaults and set retryWrites accordingly. | [documentdb-azure-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/azure-deployment/SKILL.md) |
| Secrets management | Read the cluster connection string from environment variables and never commit credentials to source control; use Key Vault for production. | [documentdb-azure-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/azure-deployment/SKILL.md) |
| Aggregation server-side | Aggregate order history into co-purchase counts server-side using aggregation pipelines (unwind, group/self-join). | documentdb-query-optimization/query-explain-plan<br>documentdb-query-optimization/query-explain-plan |
| Atomic increments & upserts | Use $inc with upsert:true to increment co-purchase counts atomically and avoid race conditions. | [Field update - operators](https://learn.microsoft.com/documentdb/query/operators/field-update/$inc) |
| Batch embeddings | Batch embedding requests to the embedding service to improve throughput and avoid rate limits. | [Generate embeddings with Azure OpenAI - Best practices](https://learn.microsoft.com/azure/foundry/openai/how-to/embeddings#best-practices) |
| Vector normalization & metadata | L2-normalize embeddings for cosine similarity and store the embedding model name and dimensions alongside each vector. | documentdb-vector-search/vector-normalize-embeddings<br>documentdb-vector-search/vector-normalize-embeddings |
| Enforce embedding dimension | Enforce and validate the embedding dimension and numeric type at write time and ensure index 'dimensions' matches the model output exactly. | documentdb-vector-search/vector-create-diskann-index<br>documentdb-vector-search/vector-create-diskann-index |
| Choose vector index by scale | Choose vector index type by dataset scale: vector-diskann for large, HNSW for up to ~50k, IVF for small sets. | documentdb-vector-search/vector-choose-index-type<br>documentdb-vector-search/vector-choose-index-type |
| kNN search via $search | Run kNN with the $search aggregation stage using cosmosSearch and project the search score for reranking. | documentdb-vector-search/vector-knn-query<br>documentdb-vector-search/vector-knn-query |
| Index conventional fields | Create conventional indexes (B-tree) to support non-vector filters and sorting (e.g., on co_purchase_count). | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Tuning vector index params | Tune vector index build/query parameters (lBuild, lSearch, maxDegree, etc.) for recall vs latency. | documentdb-vector-search/vector-create-diskann-index<br>documentdb-vector-search/vector-create-diskann-index |
| Monitoring and diagnostics | Enable diagnostic settings and slow-query logs and alert on resource saturation. | documentdb-monitoring/monitoring-slow-query-log<br>documentdb-monitoring/monitoring-slow-query-log |
| Least-privilege access | Use least-privilege access: prefer Microsoft Entra ID + RBAC and per-application roles instead of cluster-admin credentials. | documentdb-security/security-entra-rbac<br>documentdb-security/security-entra-rbac |
| Unique canonical pair index | Create a unique index on a canonical unordered-pair key to enable atomic upserts / deduplication. | [Manage indexing in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/indexing) |
| Index build background | Build indexes in background when possible and avoid creating large unique/index builds during peak traffic. | [Background indexing](https://learn.microsoft.com/azure/documentdb/background-indexing) |
| Retry & backoff | Implement exponential backoff and retry logic for transient network/driver errors and handle 429 by capped backoff. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Batch load best practice | Bulk loads are batched. | [Generate embeddings with Azure OpenAI - Best practices](https://learn.microsoft.com/azure/foundry/openai/how-to/embeddings#best-practices) |
| Prefer AsyncMongoClient (Beanie) | For new Python async code on Azure DocumentDB, prefer PyMongo's AsyncMongoClient rather than Motor. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |

### How the app measures up

#### Violations

| Practice | Category | Evidence | Fix | Source |
|---|---|---|---|---|
| For new Python async code on Azure DocumentDB, prefer PyMongo's AsyncMongoClient rather than Motor. | library/runtime | Decision D004 selected Beanie with motor; events.jsonl shows the documentdb-connection and documentdb-driver skills were loaded. | Use PyMongo's AsyncMongoClient (Beanie 2.x guidance) instead of Motor for new async Beanie code. Update the decision log and implementation to use AsyncMongoClient. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |

#### Could not be assessed

| Practice | Category | What was searched and missing | Source |
|---|---|---|---|
| Create a single MongoClient (singleton) per process and reuse it for the application lifetime rather than creating a client per request. | connection handling | - | documentdb-driver/driver-singleton-client<br>documentdb-driver/driver-singleton-client |
| Require TLS on the wire and do not disable certificate validation in production when connecting to Azure DocumentDB. | security | - | documentdb-security/security-tls-required<br>documentdb-security/security-tls-required |
| Tune connection-pool and timeout settings for the expected concurrency pattern. | connection handling | - | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Azure DocumentDB's connection string commonly includes retryWrites=false because the service does not support retryable writes; verify driver defaults and set retryWrites accordingly. | connection handling | - | [documentdb-azure-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/azure-deployment/SKILL.md) |
| Pin the driver version to one the service supports. | connection | Searched the Beanie quickstart; it states tested Beanie 2.2.0 and PyMongo 4.19.0. | [Quickstart: Connect Beanie to Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/quickstart-python-beanie#prerequisites) |
| Read the cluster connection string from environment variables and never commit credentials to source control; use Key Vault for production. | authentication/secrets | - | [documentdb-azure-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/azure-deployment/SKILL.md) |
| Provide a .env.example listing required settings. | authentication/secrets | Searched quickstart and tutorial pages for .env examples; found illustrative .env in docs. | [Quickstart: Connect Beanie to Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/quickstart-python-beanie) |
| Aggregate order history into co-purchase counts server-side using aggregation pipelines (unwind, group/self-join). | queries | - | documentdb-query-optimization/query-explain-plan<br>documentdb-query-optimization/query-explain-plan |
| Use $inc with upsert:true to increment co-purchase counts atomically and avoid race conditions. | data integrity | - | [Field update - operators](https://learn.microsoft.com/documentdb/query/operators/field-update/$inc) |
| Batch embedding requests to the embedding service to improve throughput and avoid rate limits. | external_api | - | [Generate embeddings with Azure OpenAI - Best practices](https://learn.microsoft.com/azure/foundry/openai/how-to/embeddings#best-practices) |
| L2-normalize embeddings for cosine similarity and store the embedding model name and dimensions alongside each vector. | vector_search | - | documentdb-vector-search/vector-normalize-embeddings<br>documentdb-vector-search/vector-normalize-embeddings |
| Enforce and validate the embedding dimension and numeric type at write time and ensure index 'dimensions' matches the model output exactly. | data validation | - | documentdb-vector-search/vector-create-diskann-index<br>documentdb-vector-search/vector-create-diskann-index |
| Choose vector index type by dataset scale: vector-diskann for large, HNSW for up to ~50k, IVF for small sets. | vector_search | - | documentdb-vector-search/vector-choose-index-type<br>documentdb-vector-search/vector-choose-index-type |
| Run kNN with the $search aggregation stage using cosmosSearch and project the search score for reranking. | vector_search/queries | - | documentdb-vector-search/vector-knn-query<br>documentdb-vector-search/vector-knn-query |
| Create conventional indexes (B-tree) to support non-vector filters and sorting (e.g., on co_purchase_count). | indexing | - | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Tune vector index build/query parameters (lBuild, lSearch, maxDegree, etc.) for recall vs latency. | vector_search | - | documentdb-vector-search/vector-create-diskann-index<br>documentdb-vector-search/vector-create-diskann-index |
| Enable diagnostic settings and slow-query logs and alert on resource saturation. | monitoring | - | documentdb-monitoring/monitoring-slow-query-log<br>documentdb-monitoring/monitoring-slow-query-log |
| Use least-privilege access: prefer Microsoft Entra ID + RBAC and per-application roles instead of cluster-admin credentials. | authentication/secrets | - | documentdb-security/security-entra-rbac<br>documentdb-security/security-entra-rbac |
| Create a unique index on a canonical unordered-pair key to enable atomic upserts / deduplication. | indexing | - | [Manage indexing in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/indexing) |
| Build indexes in background when possible and avoid creating large unique/index builds during peak traffic. | provisioning/maintenance | - | [Background indexing](https://learn.microsoft.com/azure/documentdb/background-indexing) |
| Implement exponential backoff and retry logic for transient network/driver errors and handle 429 by capped backoff. | retries | - | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Bulk loads are batched. | reliability | - | [Generate embeddings with Azure OpenAI - Best practices](https://learn.microsoft.com/azure/foundry/openai/how-to/embeddings#best-practices) |
| Verify MongoDB wire protocol and operator compatibility for the chosen driver and server version. | compatibility | Searched Azure DocumentDB compatibility docs; found wire protocol and operator coverage info. | [MongoDB Query Language (MQL) compatibility in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/compatibility-query-language) |
| Choices made but not logged: chosen OpenAI embedding model (text-embedding-3-small) appears in builder_report but is not recorded as a decision. | audit trail | - | build report (no public address recorded) |
| Affinity scoring formula was selected in the plan but not logged as a decision. | audit trail | - | build report (no public address recorded) |

### Reference requirements

0 of 20 met. The builder never saw these; this measures the starter prompt and the skills.

| Requirement | Status | Cause | Evidence | Smallest fix |
|---|---|---|---|---|
| Aggregation step via Beanie to derive unordered co-purchase pairs, persist one document per pair via Beanie. | not_met | tool_unavailable | No application files or Beanie model files were written into the workspace; builder_report states plan only and seed/aggregation steps were not executed. | Create src/models.py and scripts/seed.py implementing the Beanie aggregation + upsert; add a unit test that runs aggregation against an in-memory fixture. |
| Each stored product pair is embedded with OpenAI embeddings and saved on the pair document. | not_met | tool_unavailable | No code that calls OpenAI embeddings or writes vectors to DocumentDB exists in the workspace; builder_report describes plan only. | Add async embedding code in scripts/seed.py and a wrapper service module that batches OpenAI requests and upserts vectors to ProductPair documents. |
| Create a cosmosSearch vector index (ivf/hnsw/diskann) in code on the embedding field with correct dimensions and similarity metric. | not_met | tool_unavailable | No index-creation script or code in the workspace; builder_report includes instructions but did not run them or write files. | Add scripts/create_indexes.py to call db.command({'createIndexes': ...}) with cosmosSearchOptions; derive dimensions from OPENAI_EMBEDDING_MODEL env var. |
| Expose /cross-sell HTTP endpoint that accepts a basket of product IDs. | not_met | tool_unavailable | No FastAPI app files or endpoint definitions are present; builder_report only contains a runbook and plan. | Add src/main.py implementing FastAPI app with POST /cross-sell and request/response pydantic models. |
| Handle /cross-sell by embedding the basket and running a $search/cosmosSearch aggregation against the vector index. | not_met | tool_unavailable | No request handler or $search usage in repository; plan described but no artifacts created. | Implement an async handler that batches basket embedding, then executes an aggregation with a cosmosSearch operator using the query vector. |
| Endpoint returns exactly top 5 candidates ordered by affinity; excludes basket items; affinity derived from co-purchase data and similarity. | not_met | tool_unavailable | No endpoint or response tests available; builder_report documents a heuristic but not code. | Implement ranking code that merges DB cosine-similarity score and normalized co_purchase_count into an affinity score and returns top 5 excluding basket IDs. |
| Entire service is async end to end (async/await for request handling, Beanie calls, index creation, and OpenAI calls). | not_met | tool_unavailable | No code present; builder_report states async design but nothing was implemented. | When writing code, use AsyncPyMongo/AsyncMongoClient + async Beanie init, async OpenAI calls (httpx or Azure OpenAI async client), and annotate async/await throughout. |
| Connection string and model credentials come from environment variables; none are in the repo. | not_met | tool_unavailable | No config files or .env.example exist in the workspace; builder_report planned .env.example but not written. | Add .env.example listing DOCUMENTDB_URI, OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL, DATABASE_NAME, and optional tuning params. |
| Provide a .env.example listing every setting with placeholders. | not_met | tool_unavailable | No .env.example file in workspace; builder_report refers to one in the plan only. | Add .env.example with placeholders for all required settings and short comments. |
| Vector index dimensions match the embedding model output. | not_met | tool_unavailable | No index creation code or index metadata present to verify dimension alignment; builder_report assumed text-embedding-3-small (1536) but didn't create index. | Pass embedding model name and dimensions from env var into index-creation script and validate vector length at write time. |
| Vector index parameters chosen for data size and README describes how to change them for larger data. | not_met | tool_unavailable | No README or index parameter choices exist in the repository; builder_report mentions guidance but not enacted. | Add README section on index choice (ivf/hnsw/diskann), default params for demo size, and instructions to tune lBuild/lSearch/numLists for production. |
| One database client is created and reused across requests. | not_met | tool_unavailable | No application code to inspect; builder_report indicates intent but no implementation exists. | Implement a single AsyncMongoClient/AsyncMongoClient wrapper initialized at startup and closed on shutdown; document in README. |
| Seed script loads sample data and creates the index, and is idempotent (can be run twice without duplicating data). | not_met | tool_unavailable | No seed.py or scripts/seed.py present; builder_report planned an idempotent seed but it was not written or executed. | Add scripts/seed.py that upserts Orders and ProductPairs (canonical pair key + upsert) and checks/creates indexes only if absent. |
| /search returns clear errors for empty query and when embedding call fails. | not_met | tool_unavailable | No API code or tests to verify error handling in place. | Add request validation in the endpoint (400 for empty basket) and catch embedding errors returning 502/503 with helpful messages; add tests that stub the embedding client. |
| Search results include the similarity score. | not_met | tool_unavailable | No endpoint or response payload implemented; builder_report planned to include affinity and component scores but no code exists. | Return the search score from the cosmosSearch result in the response along with computed affinity and co_purchase_count. |
| Dependencies pinned in requirements.txt. | not_met | tool_unavailable | No requirements.txt in repository; builder_report suggests pinned versions but did not add file. | Add requirements.txt pinning beanie, pymongo/AsyncMongoClient, fastapi, uvicorn, httpx, numpy, python-dotenv, test dependencies with exact versions. |
| Unit tests run without a live cluster. | not_met | tool_unavailable | No tests in workspace; builder_report planned tests but did not produce them. | Add unit tests that mock the database and embedding calls (pytest + respx/httpx mocking) so they run offline. |
| Infrastructure for cluster provided as IaC using Azure DocumentDB resource type. | not_met | tool_unavailable | No Bicep/Terraform/ARM templates are present in the workspace; builder_report referenced IaC but did not create files. | Provide a Bicep or Terraform snippet that uses Microsoft.DocumentDB/mongoClusters or equivalent AzAPI resource example in infra/ folder. |
| README covers what the sample shows, prerequisites, setup, run, and clean-up. | not_met | tool_unavailable | No README file exists in the workspace; builder_report contains run instructions but they are not committed as a file. | Add README.md with sections: Overview, Prereqs, Setup, Seeding, Running, Examples, Cleanup and Troubleshooting. |
| Sample uses the name 'Azure DocumentDB' throughout and not a neighbouring product name. | not_met | tool_unavailable | No README or source files exist to validate naming usage; builder_report uses the correct name in narrative but no files to inspect. | When adding README and docs, ensure the product name 'Azure DocumentDB' is used consistently and add a 'Naming' paragraph clarifying differences from Cosmos DB and Amazon DocumentDB. |

