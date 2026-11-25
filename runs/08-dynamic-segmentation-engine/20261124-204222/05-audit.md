# 5. Best-practice audit: 08-dynamic-segmentation-engine

**Verdict: pass_with_findings** (11 followed, 2 violated)

The sample implements the core requested behaviour: a single Python agent computes recency/frequency/category-affinity with an on-demand aggregation, applies injected segmentation rules (LLM or deterministic fallback), and writes the assigned segment back to the profile document. The repo is mostly complete (pinned dependencies, idempotent seed, README, singleton MongoClient, indexes that match the aggregation patterns). Shortcomings that matter to maintainers and the product team are: (1) the aggregation tool was not registered as a LangChain Tool object (builder implemented a LangChain-compatible flow but did not register a tool), (2) tests require a live cluster (no offline/unit mocks), (3) no explicit retry/backoff logic around transient DB errors, and (4) no infra-as-code for provisioning the mongoClusters resource. Many of the checklist practices are present and were discoverable in public docs and the installed skills; several expected gallery hygiene items that were flagged at risk turned out to be present (.env.example, pinned requirements), while others (vector-index guidance, offline tests, infra) remain gaps. See requirements, practice checks, decision reviews and doc gaps below for evidence and the smallest fixes.

## Review of the builder's decisions

| Decision | What was decided | Reason came from | Assessment | Comment |
|---|---|---|---|---|
| D001 | I approved the build with readiness 'ready_with_gaps' | operator | sound | An operator approval. Nothing in the trace contradicts the approval and it matches the builder report status 'completed'. |
| D002 | I chose to target the Python runtime already on PATH (Python 3.13) for the sample and pin package versions in requirements.txt. | readiness_report | sound | Decision to target Python 3.13 and pin packages is reflected in README (app/README.md line 14) and requirements.txt pins; events.jsonl contains a log_decision entry for this decision. |
| D003 | I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime. | readiness_report | sound | Decision to read DOCUMENTDB_URI from the environment is implemented in app/src/db.py lines 9-12. The readiness report cited in the decision justifies the choice. |
| D004 | I chose not to provision any Azure resources and to use the existing cluster referenced by DOCUMENTDB_URI. | readiness_report | sound | Decision not to provision Azure resources is consistent with the repo (no IaC files) and the run policy; the implementation uses an existing cluster via DOCUMENTDB_URI. |
| D005 | I chose to implement a LangChain-compatible agent that will use OpenAI (if OPENAI_API_KEY is provided) and fall back to a deterministic rule-based assigner when no API key is available. | model_default | sound | Decision to implement a LangChain-compatible agent with an OpenAI LLM path and deterministic fallback is implemented: lazy import of langchain/OpenAI and fallback to assign_segment_from_rules (app/src/agent.py lines 130-147). The decision's reason_source is 'model_default' but the code implements the chosen behaviour. |
| D006 | I chose to provide both a minimal CLI for one-shot demos and a small FastAPI HTTP endpoint (POST /segment) to demonstrate how the agent can be called from an API. | model_default | sound | Decision to provide both a CLI and FastAPI endpoint is implemented: app/src/cli.py and app/src/app.py exist and are wired to run_agent_assign_segment(). |
| D007 | I chose to create the collections and indexes using pymongo in the seed script (idempotent operations), and then verify them with the documentdb MCP server tools. | model_default | sound | Decision to create collections and indexes with pymongo is implemented in app/scripts/seed.py (index creation and upserts). Verification steps in the builder report and events show that the seed script ran. |
| D008 | I chose not to use vector indexes or embeddings for this sample because the segmentation logic is based on behavioural aggregates (recency, frequency, category affinity) and does not require semantic vectors. | model_default | sound | Decision not to use vectors is coherent with the repo (no vector fields or vector indexes present) and the decision rationale (keep the sample focused) matches what was implemented. |

Documentation gaps: 6 (see `doc-gaps.md`).

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
| On the checklist, found only when searched for by name | 1 | Public but hard to find. A discoverability gap. |
| Found publicly, not on the checklist | 1 | Add it to the checklist, or check that the public guidance is what the team intends. |
| Known to the model, no public source, not on the checklist | 0 | Agents will act on it from memory. Decide whether it holds for this service, then document it either way. |
| On the checklist and found by open discovery | 11 | Public and discoverable. |

#### On the checklist, found only when searched for by name

| Topic | Searched for | Sources |
|---|---|---|
| Driver version pinned | The driver version is pinned and is one the service supports.<br>**Searches:** Searched Microsoft Learn quickstart and docs for pymongo compatibility and guidance recommending drivers be pinned; quickstart docs recommend using official MongoDB drivers and indicate supported Python versions. | [Quickstart: Use Azure DocumentDB with MongoDB driver for Python](https://learn.microsoft.com/azure/documentdb/quickstart-python) |

#### Found publicly, not on the checklist

| Topic | Description | Sources |
|---|---|---|
| Audit trail: index shapes | Audit trail: the seed script creates specific compound indexes (customer_id,timestamp) and (customer_id,category) and customers unique index customer_id but there is no separate decision logging the chosen index shapes. | checklist only (no public address recorded) |

#### On the checklist and found by open discovery

| Topic | Description | Sources |
|---|---|---|
| Singleton MongoClient | Create one MongoClient per process and reuse it as a singleton rather than creating a new client per request. | documentdb-driver / driver-singleton-client<br>documentdb-driver / driver-singleton-client |
| Read URI from env | Read the cluster connection URI from an environment variable at runtime and do not commit it to source control; provide a .env.example with a placeholder. | [Use LangGraph with Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/persist-agent-state#get-started-install-dependencies) |
| TLS enforced by connection string | Always enable TLS for connections to Azure DocumentDB and do not disable certificate validation in production. | [Connect to Azure DocumentDB using role-based access control and Microsoft Entra ID (azure-resource-manager-bicep)](https://learn.microsoft.com/azure/documentdb/how-to-connect-role-based-access-control#get-cluster-credentials) |
| Index per aggregation | Design and create compound indexes that match your aggregation/query patterns (e.g., a compound index on customer_id then timestamp to accelerate per-customer recency and sort-by-timestamp queries). | documentdb-indexing / index-compound-esr<br>documentdb-indexing / index-compound-esr |
| Index category field | Index the category field (or create a compound index with customer_id when filtering by both) to make category-affinity grouping/lookup efficient. | documentdb-indexing / index-single-field<br>documentdb-indexing / index-single-field |
| Project only required fields | When computing metrics or running aggregations, project only the required fields (use $project) to reduce I/O and network transfer. | [Aggregation pipeline examples and limitations](https://learn.microsoft.com/azure/cosmos-db/mongodb/tutorial-aggregation#single-collection-pipeline-examples) |
| Atomic writeback | When writing an assigned segment back to a customer document, perform an atomic single-document update (updateOne with $set or findAndModify) rather than a read-modify-write cycle to avoid race conditions. | [Updating data in Azure Cosmos DB for MongoDB](https://learn.microsoft.com/azure/cosmos-db/mongodb/tutorial-update) |
| Optimistic concurrency | For stronger concurrency control when multiple writers may update the same profile, use optimistic concurrency (etags / _etag + If-Match) or include a version field in the update filter. | [Transactions and optimistic concurrency control](https://learn.microsoft.com/azure/cosmos-db/database-transactions-optimistic-concurrency#optimistic-concurrency-control) |
| Retries on transient errors | Handle transient errors (including 429 rate-limited responses) with retries and exponential backoff and respect server-provided retry guidance when present. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Seed idempotency & bulk writes | Use bulk writes/inserts (insertMany / bulk APIs, unordered where appropriate) when seeding or ingesting many events to improve throughput and reduce RU cost. | [Optimize write performance in Azure Cosmos DB for MongoDB](https://learn.microsoft.com/azure/cosmos-db/mongodb/optimize-write-performance#reduce-the-number-of-indexes) |
| Events in separate collection | Don't store unbounded/high-cardinality event arrays inside frequently-updated customer profile documents; keep events in a separate events collection and pre-aggregate or summarize into a small profile document to avoid hot documents and large update costs. | documentdb-data-modeling / model-embed-vs-reference<br>documentdb-data-modeling / model-embed-vs-reference |

### How the app measures up

#### Violations

| Practice | Category | Evidence | Fix | Source |
|---|---|---|---|---|
| For stronger concurrency control when multiple writers may update the same profile, use optimistic concurrency (etags / _etag + If-Match) or include a version field in the update filter. | data_integrity | app/src/agent.py writes with update_one(..., upsert=True) without a version filter or _etag handling (line 151). No optimistic-concurrency usage is present. | Add a version field or include _etag/If-Match semantics: read the current version or _etag and use find_one_and_update with a filter that includes that version (or use a conditional update filter with a 'version' value), and retry on mismatch. | [Transactions and optimistic concurrency control](https://learn.microsoft.com/azure/cosmos-db/database-transactions-optimistic-concurrency#optimistic-concurrency-control) |
| Handle transient errors (including 429 rate-limited responses) with retries and exponential backoff and respect server-provided retry guidance when present. | retries_and_error_handling | app/src/db.py and app/src/agent.py contain no retry/exponential-backoff wrappers for database operations; MongoClient is created but operations are not wrapped with retry/backoff logic. | Wrap DB calls in a small retry helper (e.g., using tenacity) or enable and document pymongo retry options; add a simple retry decorator for key DB operations (aggregation, update_one) with exponential backoff and honoring Retry-After where applicable. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |

#### Followed

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Create one MongoClient per process and reuse it as a singleton rather than creating a new client per request. | connection_handling | app/src/db.py lines 14-26 implement _client singleton with _client_lock and get_client(). | documentdb-driver / driver-singleton-client<br>documentdb-driver / driver-singleton-client |
| Read the cluster connection URI from an environment variable at runtime and do not commit it to source control; provide a .env.example with a placeholder. | connection_handling | app/src/db.py lines 9-12 read DOCUMENTDB_URI from the environment and raise if missing; app/.env.example present (app/.env.example lines 1-4). | [Use LangGraph with Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/persist-agent-state#get-started-install-dependencies) |
| Always enable TLS for connections to Azure DocumentDB and do not disable certificate validation in production. | connection_handling | app/src/db.py defers to the URI for TLS/options (comment at line 23) and the repo provides .env.example that includes ssl/tls options (app/.env.example line 2). | [Connect to Azure DocumentDB using role-based access control and Microsoft Entra ID (azure-resource-manager-bicep)](https://learn.microsoft.com/azure/documentdb/how-to-connect-role-based-access-control#get-cluster-credentials) |
| The driver version is pinned and is one the service supports. | connection_handling | app/requirements.txt pins pymongo==4.6.1 (app/requirements.txt line 1). | [Quickstart: Use Azure DocumentDB with MongoDB driver for Python](https://learn.microsoft.com/azure/documentdb/quickstart-python) |
| Design and create compound indexes that match your aggregation/query patterns (e.g., a compound index on customer_id then timestamp to accelerate per-customer recency and sort-by-timestamp queries). | indexing | app/scripts/seed.py creates events.create_index([('customer_id',1),('timestamp',-1)]) and events.create_index([('customer_id',1),('category',1)]) (lines 17-18). compute_metrics matches on customer_id and uses timestamp (app/src/agent.py lines 30-36 and 64-68). | documentdb-indexing / index-compound-esr<br>documentdb-indexing / index-compound-esr |
| Index the category field (or create a compound index with customer_id when filtering by both) to make category-affinity grouping/lookup efficient. | indexing | app/scripts/seed.py creates events.create_index([('customer_id',1),('category',1)]) (line 18). compute_metrics uses category values for affinity calculations (app/src/agent.py lines 72-81). | documentdb-indexing / index-single-field<br>documentdb-indexing / index-single-field |
| When computing metrics or running aggregations, project only the required fields (use $project) to reduce I/O and network transfer. | queries_and_aggregation | compute_metrics aggregation includes a $project stage (app/src/agent.py lines 38-44). | [Aggregation pipeline examples and limitations](https://learn.microsoft.com/azure/cosmos-db/mongodb/tutorial-aggregation#single-collection-pipeline-examples) |
| When writing an assigned segment back to a customer document, perform an atomic single-document update (updateOne with $set or findAndModify) rather than a read-modify-write cycle to avoid race conditions. | data_integrity | app/src/agent.py uses customers.update_one({"customer_id": customer_id}, {"$set": update}, upsert=True) (line 151). | [Updating data in Azure Cosmos DB for MongoDB](https://learn.microsoft.com/azure/cosmos-db/mongodb/tutorial-update) |
| Use bulk writes/inserts (insertMany / bulk APIs, unordered where appropriate) when seeding or ingesting many events to improve throughput and reduce RU cost. | provisioning_and_ingestion | app/scripts/seed.py deletes events for seeded customers (line 32) and then calls events.insert_many(evs) (line 54); create_index is idempotent (lines 17-19). | [Optimize write performance in Azure Cosmos DB for MongoDB](https://learn.microsoft.com/azure/cosmos-db/mongodb/optimize-write-performance#reduce-the-number-of-indexes) |
| Don't store unbounded/high-cardinality event arrays inside frequently-updated customer profile documents; keep events in a separate events collection and pre-aggregate or summarize into a small profile document to avoid hot documents and large update costs. | data_modeling | Seed script creates separate 'events' collection and 'customers' collection; events documents are stored separately (app/scripts/seed.py lines 11-13 and 49-55). compute_metrics aggregates events into summary metrics (app/src/agent.py). | documentdb-data-modeling / model-embed-vs-reference<br>documentdb-data-modeling / model-embed-vs-reference |
| Audit trail: the seed script creates specific compound indexes (customer_id,timestamp) and (customer_id,category) and customers unique index customer_id but there is no separate decision logging the chosen index shapes. | audit_trail | app/scripts/seed.py lines 17-19 show index creation; no recorded decision in decisions.jsonl naming the index shapes. | checklist only (no public address recorded) |

### Reference requirements

12 of 19 met. The builder never saw these; this measures the starter prompt and the skills.

| Requirement | Status | Cause | Evidence | Smallest fix |
|---|---|---|---|---|
| The agent has a DocumentDB aggregation tool, registered as a LangChain tool, that runs an aggregation pipeline through the Python MongoDB driver (e.g. PyMongo) against the event data in Azure DocumentDB for the customer the agent is working on, when the agent calls it. | not_met | builder_error | app/src/agent.py implements compute_metrics() and run_agent_assign_segment(), but there is no LangChain Tool wrapper or tool registration (no use of langchain.agents.Tool or Tool registration). | Wrap compute_metrics in a LangChain Tool (e.g., from langchain.agents import Tool) and register it with the agent executor; add a small glue function that calls compute_metrics and returns serializable JSON. |
| Unit tests run without a live cluster. | not_met | prompt_silent | app/tests/test_aggregate.py imports compute_metrics and assumes seed.py has been run; no mocks or local gateway are used (lines 4-13). | Add unit tests that mock pymongo (or use the local DocumentDB gateway in CI) or add a test fixture that spins up a local DocumentDB gateway docker image; update tests to run against an in-memory/mocked client. |
| Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. | not_met | prompt_silent | No Bicep/ARM/Terraform/az templates or IaC files are present in the repo; no Microsoft.DocumentDB/mongoClusters template is included. | Add a small Bicep/ARM template or Terraform snippet that provisions Microsoft.DocumentDB/mongoClusters with sensible default tier/storage/region and a note that the sample is intended to target an existing cluster by default. |
| The vector index dimensions match the embedding model's output. | not_checkable | - | The sample intentionally does not create vector indexes (decision D008). No vector indexes or embedding model are present in the repository to inspect. | If vectors are added, have the seed/index creation code accept a DIMENSIONS value from env and document model→dimensions mapping in the README. |
| The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. | not_checkable | - | No vector index is created in the sample (see decision D008), so no parameters exist to evaluate. | If vector indexes are added, document sensible defaults and how to tune 'numLists'/'efConstruction'/'lSearch' for larger corpora in README. |
| /search returns a clear error for an empty query and when the embedding call fails. | not_checkable | - | The sample does not expose a /search endpoint; only POST /segment exists (app/src/app.py lines 15-19). | If a /search endpoint is added, add explicit validation for empty queries and explicit error handling for embedding failures and return a 400/502 with clear message. |
| Search results include the similarity score. | not_checkable | - | No vector/search endpoints are present in the sample; similarity scores are not applicable. | If search is added, include similarity scores in the response and document the score interpretation. |
| The application is a Python LangChain agent, and one agent carries a customer through the whole flow: calling the aggregation tool, applying the segmentation rules, assigning the label and writing it back. | met | - | app/src/agent.py: lines 128-151 (compute_metrics called, label chosen and customers.update_one(...,$set...) performed). | n/a |
| The aggregation pipeline computes the behavioural metrics per customer on demand, at the time the tool is called: recency, frequency and category affinity, which the tool returns to the agent. | met | - | app/src/agent.py: pipeline building at lines 30-45 and frequency pipeline lines 64-68; compute_metrics returns recency_days, frequency_30d, category_counts and top_category (lines 83-92). | n/a |
| The segmentation rules are injected into the agent's prompt through context engineering (e.g. as a rules section assembled into the system prompt), so the rules the agent applies are present in its prompt context. | met | - | app/src/agent.py: when using the LLM path a prompt string is composed that includes the rules (lines 135-140). | n/a |
| The agent assigns a segment label to the customer from the computed metrics and the injected segmentation rules. | met | - | app/src/agent.py: assign_segment_from_rules() (lines 95-116) is used when LLM path is unavailable; when LLM path is used the prompt instructs the model to return a label and that label is used (lines 130-147). | n/a |
| The agent writes the assigned segment label back to that customer's profile document in Azure DocumentDB (e.g. an update that sets a segment field on the profile). | met | - | app/src/agent.py: customers.update_one({"customer_id": customer_id}, {"$set": update}, upsert=True) at line 151. | n/a |
| The connection string and model credentials come from environment variables; none appear in the repository. | met | - | app/src/db.py: reads DOCUMENTDB_URI from env (lines 9-12). app/src/agent.py reads OPENAI_API_KEY from env (line 11). app/.env.example contains placeholders only. | n/a |
| A `.env.example` lists every setting with placeholder values. | met | - | app/.env.example (lines 1-4) contains DOCUMENTDB_URI placeholder and OPENAI_API_KEY placeholder; README documents copying .env.example (app/README.md lines 20-24). | n/a |
| One database client is created and reused across requests. | met | - | app/src/db.py implements a process-wide singleton MongoClient with a lock (lines 14-26). | n/a |
| A seed script loads sample data and creates the index, and can be run twice without duplicating data. | met | - | app/scripts/seed.py: create_index calls (lines 15-19), upsert for customers (line 28), events.delete_many for seeded customer ids before insert (line 32) and events.insert_many (line 54). | n/a |
| Dependencies are pinned in `requirements.txt`. | met | - | app/requirements.txt pins versions (pymongo==4.6.1, fastapi==0.95.2, etc.). | n/a |
| The README covers what the sample shows, prerequisites, setup, run, and clean-up. | met | - | app/README.md contains 'What this sample shows' (lines 3-11), 'Prerequisites' (lines 12-16), 'Quickstart' setup/run steps (lines 18-44) and 'Cleaning up' (lines 45-47). | n/a |
| The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name. | met | - | app/README.md title and text use 'Azure DocumentDB (mongoClusters)' (line 1); code and comments reference DocumentDB and sample_customer_360_08. No Cosmos DB or Amazon DocumentDB names are used in the sample files. | n/a |

