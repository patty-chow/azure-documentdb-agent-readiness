# 5. Best-practice audit: 09-inventory-reorder-multi-agent-system

**Verdict: fail** (7 violated, 7 not assessable)

The run produced no application files (the app/ folder is empty) and no seeds, indexes or tests were created or executed. The builder recorded a small set of architectural decisions in decisions.jsonl (Python 3.11, PyMongo pin, read DOCUMENTDB_URI from env) but could not write code, create .env.example, add requirements.txt, implement the LangChain agents, or run verification because workspace actions were not performed in this response. Documentation search tools were available and were used; the discovered best practices (P01..P21) are present in the supplied skills and Microsoft Learn results. Because the sample code is missing, nearly every reference requirement is unmet or partly met and many best-practice checks are violated or not assessable. Small, specific fixes are listed for each unmet item to make the next build successful.

## Review of the builder's decisions

| Decision | What was decided | Reason came from | Assessment | Comment |
|---|---|---|---|---|
| D001 | I approved the build with readiness 'ready_with_gaps' | operator | sound | D001 (approved the build with readiness 'ready_with_gaps') is an operator decision. The events trace records the decision in decisions.jsonl and there's no conflicting evidence; classification: sound. |
| D002 | I chose Python 3.11 (via the `python` on PATH) for the sample app. | prompt | sound | D002 (choose Python 3.11) cites the prompt and run-environment; events.jsonl shows the decision was logged and Python was the requested language — the reason and evidence align. Sound. |
| D003 | I chose PyMongo pinned to 'pymongo>=4.3,<5.0'. | prompt | sound | D003 (pin PyMongo to 'pymongo>=4.3,<5.0') is a reasonable compatibility choice and is recorded in decisions.jsonl. The events trace records the log_decision call. No documentation contradiction found; sound. |
| D004 | I chose to read the connection string from the DOCUMENTDB_URI environment variable at runtime. | readiness_report | sound | D004 (read DOCUMENTDB_URI from env) corresponds to the run-environment guidance and the events trace contains the logged decision; sound. Note: the builder recorded intent but did not create code to implement it during this run. |

Documentation gaps: 7 (see `doc-gaps.md`).

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
| On the checklist, found only when searched for by name | 0 | Public but hard to find. A discoverability gap. |
| Found publicly, not on the checklist | 0 | Add it to the checklist, or check that the public guidance is what the team intends. |
| Known to the model, no public source, not on the checklist | 1 | Agents will act on it from memory. Decide whether it holds for this service, then document it either way. |
| On the checklist and found by open discovery | 13 | Public and discoverable. |

#### Known to the model, no public source, not on the checklist

| Topic | Description | What would help |
|---|---|---|
| Consistency controls | Prefer explicit DB-level consistency controls (readConcern/writeConcern) when strong ordering is required and verify the service-level mapping for Azure DocumentDB. | An explicit Microsoft Learn page mapping MongoDB readConcern/writeConcern to Azure DocumentDB behavior (or a short guidance snippet in the documentdb-connection skill). |

#### On the checklist and found by open discovery

| Topic | Description | Sources |
|---|---|---|
| Singleton MongoClient | Create and reuse a single MongoClient (singleton) per process and do not create a new client per request; cache/connect once and share the client across handlers. | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Secrets from environment | Keep the DocumentDB connection string and credentials out of source control: read them from environment variables or retrieve from Azure Key Vault at runtime instead of committing secrets to files. | [documentdb-azure-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/azure-deployment/SKILL.md) |
| TLS enforcement | Always use TLS for connections to Azure DocumentDB and do not disable certificate validation in production. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Least-privilege credentials | Use least-privilege credentials and prefer Microsoft Entra ID / RBAC and per-application users instead of using admin/root credentials in the app. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Idempotent purchase orders | Enforce idempotency for purchase orders with a unique index and use upsert/conditional writes to avoid duplicate orders from concurrent agents. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| TTL for agent-memory | Use TTL indexes for ephemeral agent-memory documents and ensure the field is Date typed. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Indexing for query patterns | Index every field used as a filter or sort key in production queries and design compound indexes using ESR to avoid COLLSCAN. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Vector embeddings & index dims | Store fixed-length numeric embeddings in a dedicated field and create a vector index whose dimensions and similarity match the model. | [documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md) |
| Vector index engine & tuning | When building a vector index, pick the engine (DiskANN/HNSW/IVF) appropriate to scale and tune parameters and query-time settings. | [documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md) |
| Projection | Limit projection to only the fields the agent needs to reduce network transfer and serialization costs. | [find (projections)](https://learn.microsoft.com/documentdb/query/commands/query-and-write/find#projections) |
| Server-side aggregation for velocity | Compute rollups and sales-velocity metrics server-side with aggregation pipelines and create indexes that support match->sort->group. | [documentdb-query-optimization](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimization/SKILL.md) |
| Retries & idempotency | Implement retries with exponential backoff for transient errors and use idempotent operations so retries do not create duplicates. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Retryable multi-document writes | Azure DocumentDB does not support retryable multi-document writes; drivers should not assume retryable-writes semantics (connection strings include retryWrites=false). | [documentdb-azure-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/azure-deployment/SKILL.md) |

### How the app measures up

#### Violations

| Practice | Category | Evidence | Fix | Source |
|---|---|---|---|---|
| Create and reuse a single MongoClient (singleton) per process and do not create a new client per request; cache/connect once and share the client across handlers. | connection | No client module or any code to create/reuse MongoClient found (app/ empty). | Add db/client.py with get_client() that memoizes a single pymongo.MongoClient (respecting env DOCUMENTDB_URI). | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Enforce idempotency for purchase orders with a unique index and use upsert/conditional writes to avoid duplicate orders from concurrent agents. | data_model | No purchase_orders collection or unique index creation was found. | Create a unique compound index (e.g., product_id + order_period or order_reference) and perform upsert/findOneAndUpdate with a unique filter to ensure idempotency. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Use TTL indexes for ephemeral agent-memory documents and ensure the field is Date typed. | data_model | No agent memory collection or TTL index creation found. | Create an agent_memory collection with a Date last_updated field and a TTL index (expireAfterSeconds) and ensure code writes Date objects not strings. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Index every field used as a filter or sort key in production queries and design compound indexes using ESR to avoid COLLSCAN. | indexing | No index creation scripts or create_index calls for product_id, supplier_id, last_sale_date were found. | Create single-field and compound indexes that support forecast and supplier queries (product_id, supplier_id, last_sale_date) and document index rationale in README. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Store fixed-length numeric embeddings in a dedicated field and create a vector index whose dimensions and similarity match the model. | vector_search | No embeddings field or vector index createIndexes/runCommand present to inspect. | Store embeddings under embedding (float array) and create a cosmosSearch vector index with 'dimensions' equal to chosen embedding model output; include seed/index script that sets this. | [documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md) |
| Limit projection to only the fields the agent needs to reduce network transfer and serialization costs. | queries | No query code to show use of projection; all queries absent. | When querying, use projection to fetch only required fields (e.g., {'product_id':1,'velocity':1}). | [find (projections)](https://learn.microsoft.com/documentdb/query/commands/query-and-write/find#projections) |
| Compute rollups and sales-velocity metrics server-side with aggregation pipelines and create indexes that support match->sort->group. | queries | No aggregation pipelines or explain() checks present. | Implement server-side aggregation pipelines for sales velocity and create supporting indexes; include explain("executionStats") in a verification script. | [documentdb-query-optimization](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimization/SKILL.md) |

#### Could not be assessed

| Practice | Category | What was searched and missing | Source |
|---|---|---|---|
| Keep the DocumentDB connection string and credentials out of source control: read them from environment variables or retrieve from Azure Key Vault at runtime instead of committing secrets to files. | authentication and secrets | - | [documentdb-azure-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/azure-deployment/SKILL.md) |
| Always use TLS for connections to Azure DocumentDB and do not disable certificate validation in production. | security | - | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Use least-privilege credentials and prefer Microsoft Entra ID / RBAC and per-application users instead of using admin/root credentials in the app. | authentication and secrets | - | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| When building a vector index, pick the engine (DiskANN/HNSW/IVF) appropriate to scale and tune parameters and query-time settings. | vector_search | - | [documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md) |
| Implement retries with exponential backoff for transient errors and use idempotent operations so retries do not create duplicates. | retries | - | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Prefer explicit DB-level consistency controls (readConcern/writeConcern) when strong ordering is required and verify the service-level mapping for Azure DocumentDB. | consistency | Azure DocumentDB readConcern writeConcern causal consistency readConcern majority MongoDB compatibility | None recorded |
| Azure DocumentDB does not support retryable multi-document writes; drivers should not assume retryable-writes semantics (connection strings include retryWrites=false). | connection | - | [documentdb-azure-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/azure-deployment/SKILL.md) |

### Reference requirements

0 of 19 met. The builder never saw these; this measures the starter prompt and the skills.

| Requirement | Status | Cause | Evidence | Smallest fix |
|---|---|---|---|---|
| A Python LangChain multi-agent system with three agent roles: a forecast agent, a supplier agent and an orchestrator agent. | not_met | tool_unavailable | app/ is empty; no Python files, no LangChain agents defined. | Create agent modules (e.g., agents/forecast.py, agents/supplier.py, agents/orchestrator.py) implementing the three roles and an entrypoint run.py that wires the LangChain agents together. |
| The forecast agent reads sales velocity documents from Azure DocumentDB with the Python MongoDB driver (e.g. PyMongo) and predicts a reorder quantity from them. | not_met | tool_unavailable | No code found that imports pymongo or queries a sales_velocity collection. | Add a forecast agent that uses a shared pymongo MongoClient to read sales_velocity (use aggregation for velocity) and returns a numeric reorder quantity; include a deterministic fallback if LLM credentials are missing. |
| The supplier agent reads lead time documents from Azure DocumentDB and selects the best supplier based on lead time (e.g. the shortest). | not_met | tool_unavailable | No code found that queries a suppliers or lead_times collection. | Add a supplier agent that queries the suppliers/lead_times collection via the shared client and returns the supplier_id having the shortest expected lead_time. |
| The orchestrator agent coordinates the forecast agent and the supplier agent and reconciles their results into a reorder decision. | not_met | tool_unavailable | No orchestrator implementation or orchestration script present. | Implement an orchestrator (orchestrator.py) that calls the forecast and supplier agents (concurrently or sequentially as documented), reconciles results, and produces purchase-order payloads. |
| The orchestrator writes purchase order documents to Azure DocumentDB for the reorders it decides on. | not_met | tool_unavailable | No code writing to a purchase_orders collection was found. | Implement a write path in the orchestrator that upserts a purchase_orders document using a compound id or unique index to enforce idempotency. |
| Shared agent memory is used by the orchestrator to detect an order already placed for the same item and skip it, and a newly written purchase order is recorded in that memory. | not_met | tool_unavailable | No agent-memory implementation, memory collection, or TTL index was created in the repository. | Implement shared memory backed by a collection (e.g., agent_memory) with a TTL index; orchestrator should check memory (and DB unique constraint) before creating an order and record the placed order into memory after successful write. |
| A `.env.example` lists every setting with placeholder values. | not_met | tool_unavailable | No .env.example file present in the repository (app/ empty). | Add `.env.example` listing DOCUMENTDB_URI, optional LLM keys (OPENAI_API_KEY or AZURE_OPENAI_KEY), MODEL_NAME, EMBEDDING_MODEL, and any other runtime flags with placeholder values and comments. |
| The vector index dimensions match the embedding model's output. | not_met | tool_unavailable | No index-creation code or index definition present to inspect. | When creating the vector index, set dimensions equal to the chosen embedding model (e.g., 1536). Document the embedding model and index dimensions in README and in the index creation script (seed.py). |
| The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. | not_met | tool_unavailable | No index parameter choices or README guidance present. | Provide a seed/index script that creates a vector index with parameters tuned for the sample (small dataset), and document how to increase lBuild/lSearch/numLists for larger datasets in README. |
| One database client is created and reused across requests. | not_met | tool_unavailable | No db client module or client reuse pattern present. | Add a single client factory (e.g., db/client.py with get_client() that memoizes a MongoClient) and import it from all modules; reference documentdb-driver guidance in code comments. |
| A seed script loads sample data and creates the index, and can be run twice without duplicating data. | not_met | tool_unavailable | No seed.py or data fixtures present. | Add seed.py that upserts sample sales_velocity, suppliers and product documents, and idempotently creates normal and vector indexes (use createIndexes/runCommand with upsert-safe semantics). |
| /search returns a clear error for an empty query and when the embedding call fails. | not_met | tool_unavailable | No web server or /search endpoint present to inspect. | Implement a /search handler that validates query input, returns 400 for empty queries, and catches embedding errors to return a 502/500 with a clear message; add unit tests for those cases. |
| Search results include the similarity score. | not_met | tool_unavailable | No search implementation to show results or similarity scores. | Return nearest-neighbor results with the score returned by the DB (or compute cosine similarity) and include it in the JSON response. |
| Dependencies are pinned in `requirements.txt`. | not_met | tool_unavailable | No requirements.txt present in the repository. | Add requirements.txt with pinned versions, e.g., pymongo>=4.3,<5.0, langchain==0.xx (choose a stable LangChain version), python-dotenv==x.y.z, pytest==x.y.z, mongomock==x.y.z. |
| Unit tests run without a live cluster. | not_met | tool_unavailable | No tests or test configuration found. | Add pytest tests that mock the DB with mongomock or patch pymongo.MongoClient to use an in-memory/fake client so tests run offline. |
| Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. | not_met | tool_unavailable | No Bicep/Terraform/ARM templates found in the repo. | Add Bicep or Terraform (AzAPI) templates that target Microsoft.DocumentDB/mongoClusters with parameterized tier/region and clean-up instructions; mark them optional in README when a cluster already exists. |
| The README covers what the sample shows, prerequisites, setup, run, and clean-up. | not_met | tool_unavailable | No README.md found in repository. | Add README.md with sections: Overview, What it demonstrates, Prerequisites (DOCUMENTDB_URI, Python), Setup (.env.example, pip install), Run (seed.py, run.py), Verification (how to inspect DB), and Clean-up (how to remove created documents). |
| The connection string and model credentials come from environment variables; none appear in the repository. | partly_met | tool_unavailable | The builder logged decision D004 to read DOCUMENTDB_URI from environment, and the README/how-to-run in the builder report says variables are read at runtime, but there is no code or .env.example in the repo to inspect. | Add code that reads os.environ['DOCUMENTDB_URI'] and optional model env vars, and add a .env.example containing placeholders for every required setting. |
| The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name. | not_checkable | tool_unavailable | No documentation or code where the product name would appear. | Ensure documentation and code use 'Azure DocumentDB' consistently; grep/CI check can enforce the product-name rule. |

