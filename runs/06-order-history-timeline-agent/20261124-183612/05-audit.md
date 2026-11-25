# 5. Best-practice audit: 06-order-history-timeline-agent

**Verdict: pass_with_findings** (7 followed, 2 violated)

The sample implements the requested LangChain conversational agent with three DB-backed tools, an idempotent seeder, a singleton MongoClient, and a deterministic demo that shows conversation-context resolution (e.g., "last month"). Tests and index/explain verification were run against a live Azure DocumentDB cluster. Findings: (1) several gallery hygiene items the checklist expects are missing or only partially implemented (unpinned dependencies, no offline/mocked unit tests, no /search HTTP endpoint, no bulk/seeding batching), (2) connection tuning and retry guidance from the documentdb-connection skill was not followed (no explicit timeouts/retries), and (3) infrastructure-as-code for provisioning a cluster is absent (the run used an existing cluster). None of the findings make the sample non-functional for the demo; they are recommendations to meet gallery expectations and harden the sample for reuse and CI.

## Review of the builder's decisions

| Decision | What was decided | Reason came from | Assessment | Comment |
|---|---|---|---|---|
| D001 | I approved the build with readiness 'ready_with_gaps' | operator | sound | Operator approved the build with readiness 'ready_with_gaps'. Events show build and verification steps; the approval is an operator action and is supported by the run log. |
| D002 | I chose Python (target CPython 3.10+/3.13) with pip for dependencies. | prompt | sound | Choosing Python 3.10+ matches the prompt and the code (repo uses Python and LangChain); events and files show Python code and a virtualenv was used. |
| D003 | I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI (no secrets written to repo). | prompt | sound | Reading DOCUMENTDB_URI from the environment is implemented (src/pkgagent/db.py lines 8-12). |
| D004 | I chose to use the existing, pre-provisioned Azure DocumentDB cluster and not create new cloud resources. | prompt | sound | The build used the existing pre-provisioned cluster. Events show MCP tool calls (documentdb_count_documents, documentdb_list_indexes, documentdb_explain_operation) against sample_retail_06. |
| D005 | I chose a single-shard collection named 'orders' in the database 'sample_retail_06' (no sharding). | model_default | sound | Single-shard collection choice is reflected in code and seed (no sharding logic). Reason was model_default but the choice is consistent with the sample size and run environment. |
| D006 | I chose pymongo and will implement a singleton MongoClient (per documentdb-driver guidance). | skill | sound | Pymongo + singleton MongoClient was implemented (src/pkgagent/db.py lines 20-26). |
| D007 | I chose to create indexes using the documentdb MCP server's documentdb_create_index tool (and also include index-creation code in the seed script as idempotent fallback). | prompt | sound | The decision to create indexes in the seed script and verify via MCP is supported by create_indexes in src/pkgagent/db.py (lines 33-42) and events showing documentdb_list_indexes (events.jsonl line ~69) and explain (events.jsonl line ~84). |
| D008 | I chose OpenAI for the sample (chat + embeddings) and will read API key from OPENAI_API_KEY environment variable. Use text-embedding-3-small for embeddings (1536 dims). | model_default | questionable | The decision chose OpenAI and text-embedding-3-small (1536 dims). The repo wires OPENAI_API_KEY and OpenAI in the LangChain agent (src/pkgagent/agent.py lines 98-101) but there is no embedding usage or vector-index creation in the sample code; the embedding choice is not implemented or exercised. |
| D009 | I chose to relax the pymongo pin to a compatible range pymongo>=4.5,<5 to allow pip to find a matching wheel in the environment. | tool_result | sound | Relaxing pymongo version was a pragmatic builder choice; events show pip install issues and the decision matches the installer log (events show pip failures then successful installs). |
| D010 | I chose to relax the langchain pin to langchain>=0.0.331,<1 to avoid unavailable exact versions and allow pip to choose a compatible release. | tool_result | sound | Relaxing langchain version pin is supported by the pip install troubleshooting in events; the change is reflected in requirements and was necessary to proceed. |
| D011 | I approved the build with readiness 'ready_with_gaps' | operator | sound | Duplicate readiness approval (same as D001). |
| D012 | I chose Python 3.10+ (CPython) with a virtualenv and pip for dependency management. | prompt | sound | Duplicate of the Python choice (same rationale as D002). |
| D013 | I chose OpenAI as the default LLM and embedding provider (OPENAI_API_KEY and text-embedding-3-small). | prompt | questionable | Reiterates D008 selecting OpenAI as default LLM/embeddings; the code uses OpenAI LLM wiring but does not implement embedding calls or vector index configuration, so the decision is only partially evidenced by the repo. |
| D014 | I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime. | prompt | sound | Duplicate of D003; implementation reads DOCUMENTDB_URI from env as shown in src/pkgagent/db.py lines 8-12. |
| D015 | I chose not to provision resources and to use the existing DocumentDB cluster reachable via DOCUMENTDB_URI. | prompt | sound | Duplicate of D004; the run used the provided cluster and events show MCP interactions. The run policy disallowed provisioning. |
| D016 | I chose single-shard collection (no sharding) for the sample orders collection. | prompt | sound | Duplicate of D005; the repo implements a non-sharded single collection approach. |
| D017 | I chose to create indexes from the seed script using pymongo's create_index, and also verify indexes using the documentdb MCP server tools. | readiness_report | sound | Indexer creation via seed script and verification via MCP are present (create_indexes in code and documentdb_list_indexes/explain events). |
| D018 | I chose to run verification tests against the live cluster (the environment provides a reachable cluster). | readiness_report | sound | Running tests against the live cluster was executed (events show pytest passing in the live-run logs). The README documents tests use live cluster. |

Documentation gaps: 5 (see `doc-gaps.md`).

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
| On the checklist and found by open discovery | 8 | Public and discoverable. |

#### Known to the model, no public source, not on the checklist

| Topic | Description | What would help |
|---|---|---|
| Normalize NL time in memory | Normalize natural-language time references (like 'last month') to explicit ISO date ranges and store in conversation state. | A short public doc or a one-paragraph agent-kit rule describing the recommended normalization and timezone handling for NL time expressions would let agents confirm this pattern without relying on training memory. |

#### On the checklist and found by open discovery

| Topic | Description | Sources |
|---|---|---|
| Singleton MongoClient | Create one MongoClient per process and reuse it (singleton client). | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Env secrets | Keep database credentials out of source control; read connection strings from environment. | [Azure Cosmos DB Shell security best practices](https://learn.microsoft.com/azure/cosmos-db/shell/security#credential-management) |
| TLS enforcement | Require TLS on all connections to the cluster (tls=true) and validate server certificates in production. | [Connect to Azure DocumentDB using MongoDB Shell](https://learn.microsoft.com/azure/documentdb/how-to-connect-mongo-shell#connect-with-interactive-password-authentication) |
| Connection tuning | Tune MongoClient connection-pool and timeout parameters and initialize the client outside request handlers. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Use projection | Use projection to return only the fields you need to reduce RU and network payload. | [Request Units in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/request-units#request-unit-considerations) |
| Compound index ESR | Design compound indexes using the ESR rule for customer history queries. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Idempotent seeding | Make seeding and migration scripts idempotent (use upsert or check-and-create). | [documentdb-local-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md) |
| Pagination style | Avoid offset/skip-based pagination for large offsets; use continuation tokens / range anchors. | [Pagination - Query language in Cosmos DB (in Azure and Fabric)](https://learn.microsoft.com/cosmos-db/query/pagination) |

### How the app measures up

#### Violations

| Practice | Category | Evidence | Fix | Source |
|---|---|---|---|---|
| Tune MongoClient connection-pool and timeout parameters and initialize the client outside request handlers. | connection_handling | src/pkgagent/db.py lines 21-26 instantiate MongoClient(DOCUMENTDB_URI) with default options; no explicit maxPoolSize/serverSelectionTimeoutMS/socketTimeoutMS or env-driven tuning. | Add sensible default connection options and expose them as environment variables (e.g., MongoClient(DOCUMENTDB_URI, maxPoolSize=int(os.getenv('DB_MAX_POOL', '50')), serverSelectionTimeoutMS=int(os.getenv('DB_SERVER_SELECTION_TIMEOUT_MS','5000')), socketTimeoutMS=...)). | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Avoid offset/skip-based pagination for large offsets; use continuation tokens / range anchors. | queries | src/pkgagent/db.py find_orders_by_customer uses .skip(skip).limit(limit) (line 87-90) which relies on skip-based pagination. | Change find_orders_by_customer to support anchor-based pagination (e.g., pass last_order_date/_id and use {'order_date': {'$lt': last_order_date}} + limit) or return a driver cursor with batch_size for client-side continuation. | [Pagination - Query language in Cosmos DB (in Azure and Fabric)](https://learn.microsoft.com/cosmos-db/query/pagination) |

#### Followed

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Create one MongoClient per process and reuse it (singleton client). | connection_handling | src/pkgagent/db.py lines 20-26 (module-level _client and get_client returning a singleton). | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Keep database credentials out of source control; read connection strings from environment. | authentication_and_secrets | src/pkgagent/db.py lines 8-12 (dotenv + os.environ.get('DOCUMENTDB_URI')); .env.example exists. | [Azure Cosmos DB Shell security best practices](https://learn.microsoft.com/azure/cosmos-db/shell/security#credential-management) |
| Require TLS on all connections to the cluster (tls=true) and validate server certificates in production. | security | .env.example suggests tls in its URI (app/.env.example line 2) and get_client uses the DOCUMENTDB_URI provided by user; README warns not to commit secrets (README.md lines 39-41). | [Connect to Azure DocumentDB using MongoDB Shell](https://learn.microsoft.com/azure/documentdb/how-to-connect-mongo-shell#connect-with-interactive-password-authentication) |
| Use projection to return only the fields you need to reduce RU and network payload. | queries | get_order_status uses projection to return a small set of fields (src/pkgagent/db.py lines 93-96). | [Request Units in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/request-units#request-unit-considerations) |
| Design compound indexes using the ESR rule for customer history queries. | indexing | src/pkgagent/db.py lines 36-42 create a compound index on (customer_id ASC, order_date DESC) and order_date index for aggregations. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Make seeding and migration scripts idempotent (use upsert or check-and-create). | seeding | src/pkgagent/db.py seed_sample uses update_one with upsert=True (line 84) and create_indexes (lines 50-58) so repeated runs do not duplicate documents. | [documentdb-local-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md) |
| Normalize natural-language time references (like 'last month') to explicit ISO date ranges and store in conversation state. | data_modeling | src/pkgagent/agent.py lines 61-76 parse 'last_month' to concrete start/end datetimes and set them in the SimpleContext. | prior_knowledge (no public address recorded) |

### Reference requirements

12 of 20 met. The builder never saw these; this measures the starter prompt and the skills.

| Requirement | Status | Cause | Evidence | Smallest fix |
|---|---|---|---|---|
| /search returns a clear error for an empty query and when the embedding call fails. | not_met | prompt_silent | There is no HTTP server or /search endpoint in the repository (no web framework or route files). | Add a small FastAPI/Flask route /search that validates the query body and returns clear error JSON for empty queries and for embedding failures (e.g., 400 with message 'empty query' and 502 for embedding errors). |
| Dependencies are pinned in requirements.txt. | not_met | builder_error | requirements.txt contains open ranges (e.g., 'pymongo>=4.5.0', 'langchain>=0.0.300') rather than exact pinned versions. | Pin exact tested versions (e.g., pymongo==4.5.0, langchain==0.0.331, python-dotenv==1.0.0, openai==0.27.0, pytest==7.2.x) in requirements.txt or include a constraints file used in CI. |
| Unit tests run without a live cluster. | not_met | prompt_silent | tests/test_db.py seeds and queries the live cluster (tests call db.seed_sample and db.get_orders_collection). README explicitly says tests use the live cluster (README.md line 35-36). | Provide a lightweight mocking strategy (e.g., tests using mongomock or a local DocumentDB Gateway container) and add a test fixture that runs when an env var TEST_USE_LIVE is false. |
| Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. | not_met | prompt_silent | No Bicep/ARM/Terraform / Az CLI templates are present in the repository (no infra/ or deploy/ directory). | Add a minimal Bicep or Terraform example deploying Microsoft.DocumentDB/mongoClusters (or an AzAPI wrapper) with inexpensive defaults and comments pointing to the team's recommended resource type. |
| The README covers what the sample shows, prerequisites, setup, run, and clean-up. | partly_met | prompt_silent | README.md describes the sample, prerequisites, setup and run steps (README.md lines 3-36). It does not show an explicit clean-up/teardown script or instructions to remove seeded data or how to restore the cluster. | Add a short 'clean-up' section describing how to remove the sample data (e.g., drop sample_retail_06.orders) or provide a cleanup script (python teardown.py) and mention how tests behave against a live cluster. |
| The vector index dimensions match the embedding model's output. | not_checkable | prompt_silent | The sample does not create or use any vector/indexes (seed and DB code create only standard indexes). | If vector search is added, include a fixed mapping between the embedding model and index dimensions in the seed/index code (or derive dims at runtime from the chosen embedding model). |
| The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. | not_checkable | prompt_silent | No vector indexes are created or documented in the repo. | If vector search is included, add index-creation parameters to seed.py and document how to adjust them in README. |
| Search results include the similarity score. | not_checkable | prompt_silent | The sample does not implement vector search or an embedding-backed search endpoint. | When adding vector search, return score along with the document payload (e.g., include 'score' in search API and the demo outputs). |
| Implement the agent in Python with LangChain as a single conversational agent that takes a customer service agent's question and chooses among its tools to answer it. | met | - | src/pkgagent/agent.py lines 91-109 (build_langchain_agent uses langchain.initialize_agent) and run_agent.py lines 13-19 (scripted_demo_with_llm). | n/a |
| Provide a tool that fetches a customer's order history from Azure DocumentDB through a MongoDB driver and returns the matching order documents to the agent. | met | - | src/pkgagent/agent.py lines 41-55 (tool_fetch_order_history) calls src/pkgagent/db.py find_orders_by_customer (lines 87-90). | n/a |
| Provide a tool that runs MongoDB aggregation pipelines against the orders in Azure DocumentDB to compute spend summaries and returns the results to the agent. | met | - | src/pkgagent/agent.py lines 58-77 (tool_spend_summary) calls src/pkgagent/db.py aggregate_spend_summary (lines 99-119). | n/a |
| Provide a tool that looks up an individual order in Azure DocumentDB and returns its status to the agent. | met | - | src/pkgagent/agent.py lines 80-88 (tool_order_lookup) calls src/pkgagent/db.py get_order_status (lines 93-96). | n/a |
| Give the agent LangChain agent memory that carries conversation context (e.g. the customer under discussion and the period last asked about) from one turn to the next. | met | - | src/pkgagent/agent.py lines 107-108 (ConversationBufferMemory passed to initialize_agent) and the module-level SimpleContext (lines 8-29) used by the tools to store last_customer / last_time_range. | n/a |
| Resolve follow-up questions such as "what about last month?" from that context, turning the relative reference into the concrete filter (e.g. a date range) used in the tool call. | met | - | src/pkgagent/agent.py lines 61-76 (tool_spend_summary handles raw == 'last_month', computes start/end, calls db.aggregate_spend_summary) and run_agent.py lines 37-40 (deterministic demo uses tool_spend_summary('last_month')). | n/a |
| Reply in conversational language that summarises and reasons over the tool results for the customer service agent. | met | - | tool implementations return human-readable strings: src/pkgagent/agent.py lines 52-55 (order list lines) and lines 76-77 (JSON summary for spend). run_agent.py prints these outputs (lines 37-40). | n/a |
| The connection string and model credentials come from environment variables; none appear in the repository. | met | - | .env.example (lines 1-4) contains placeholders; src/pkgagent/db.py lines 10-12 read DOCUMENTDB_URI from environment; src/pkgagent/agent.py lines 98-100 read OPENAI_API_KEY. | n/a |
| A .env.example lists every setting with placeholder values. | met | - | app/.env.example contains DOCUMENTDB_URI and OPENAI_API_KEY placeholders (app/.env.example lines 1-4). README also documents copying .env.example (README.md lines 26-30). | n/a |
| One database client is created and reused across requests. | met | - | src/pkgagent/db.py lines 20-26 implement a module-level _client and get_client() returning a singleton MongoClient. | n/a |
| A seed script loads sample data and creates the index, and can be run twice without duplicating data. | met | - | seed.py calls db.seed_sample(size=300) (seed.py lines 8-10); src/pkgagent/db.py seed_sample uses upsert (update_one with upsert=True) and create_indexes (lines 50-76 and 33-42). | n/a |
| The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name. | met | - | README.md and code comments use 'Azure DocumentDB' (README.md lines 1-4 and other places). No references to Cosmos DB or Amazon DocumentDB appear in the sample files. | n/a |

