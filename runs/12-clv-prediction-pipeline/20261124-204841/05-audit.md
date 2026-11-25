# 5. Best-practice audit: 12-clv-prediction-pipeline

**Verdict: pass_with_findings** (8 followed, 3 not assessable, 5 violated, 6 not applicable)

The sample implements the requested CLV pipeline in Python, seeds idempotent sample data, creates an index, computes the required metrics with a DocumentDB aggregation pipeline, prompts an LLM to classify CLV, and writes results back to the customer document. Tests and index/listing/seed verification were run against the live cluster where possible. Find‑and‑fix items: the LangChain agent does not expose the DocumentDB aggregation as a LangChain Tool (the agent calls the aggregation function directly), connection tuning / retries / bulk-write patterns are not implemented, dependencies are not strictly pinned, tests require a live cluster (no offline unit tests), and infrastructure-as-code is not supplied. Several documentation gaps (LLM output audit/sanitization, MCP management-tool opt-in discoverability, guidance on choosing a default LLM) are noted for the Product team.

## Review of the builder's decisions

| Decision | What was decided | Reason came from | Assessment | Comment |
|---|---|---|---|---|
| D001 | I approved the build with readiness 'ready_with_gaps' | operator | sound | An operator-approved readiness decision. Events show readiness tooling and skills were loaded; nothing in the trace contradicts an operator acceptance of 'ready_with_gaps'. |
| D002 | I chose Python 3.13 with a virtualenv and standard Python packaging (requirements.txt). | readiness_report | sound | The code and README are Python-based and the run used Python 3.13; events show the decision was logged and environment supports Python 3.13. |
| D003 | I chose PyMongo (pymongo>=4.4). | prompt | sound | The repo pins pymongo in requirements.txt as pymongo>=4.4.0 and code uses PyMongo; the decision is consistent with the implementation. |
| D004 | I chose to read the connection string from the DOCUMENTDB_URI environment variable and use it directly in pymongo.MongoClient. | readiness_report | sound | Events and code show DOCUMENTDB_URI is read from the environment (app/src/db.py line 13) and passed to MongoClient, matching the decision and its evidence. |
| D005 | I chose OpenAI gpt-3.5-turbo as the default LLM for the LangChain Chat model. | model_default | questionable | The builder logged choosing OpenAI gpt-3.5-turbo (app/src/agent.py line 25). The decision's reason_source is 'model_default' (the builder's default); this is defensible but a product-level guidance page on recommended LLM providers/models would remove guesswork. Also events show OPENAI_API_KEY was unset so the LLM call was not executed in this run. |
| D006 | I chose to create a multikey index on 'purchases.date' to accelerate aggregations that unwind purchases by date and compute tenure/recency. | model_default | sound | Events record creation of purchases_date_idx (src/create_indexes.py line 7) and documentdb_list_indexes confirmed the index; the choice and execution are supported by traces. |
| D007 | I chose to create the index using pymongo from a local script because documentdb_create_index MCP tool failed. | tool_result | sound | Events show documentdb_create_index MCP tool returned a ToolExecutionException (management tools disabled) and the builder then created the index via pymongo; the log_decision and subsequent commands are present in events.jsonl. |

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
| On the checklist, found only when searched for by name | 0 | Public but hard to find. A discoverability gap. |
| Found publicly, not on the checklist | 0 | Add it to the checklist, or check that the public guidance is what the team intends. |
| Known to the model, no public source, not on the checklist | 2 | Agents will act on it from memory. Decide whether it holds for this service, then document it either way. |
| On the checklist and found by open discovery | 20 | Public and discoverable. |

#### Known to the model, no public source, not on the checklist

| Topic | Description | What would help |
|---|---|---|
| Record LLM outputs | Record LLM outputs and the LLM rationale in structured fields and an append-only audit or history subdocument rather than overwriting a single source-of-truth field. | A documented example page showing an audit subdocument schema and update snippet for writing LLM outputs with $push. |
| Sanitize LLM outputs | Sanitize and validate any values produced by an LLM before writing them to the database (type checking, allowed enums, ranges). | A short policy page specifying allowed enums and example validation code to run before DB writes. |

#### On the checklist and found by open discovery

| Topic | Description | Sources |
|---|---|---|
| Connection client reuse | Create a single long-lived MongoClient per process (singleton) and reuse it for all requests; do not open a new client per request, and close it only on orderly shutdown. | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Secrets from env | Read the DocumentDB connection string and other secrets from environment variables (or a runtime-loaded .env) and never commit secrets into source control or logs. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| TLS enforcement | Always use TLS for connections to Azure DocumentDB and do not disable certificate validation in production. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Connection timeouts | Set sensible socket and server-selection timeouts and tune them for your environment so client calls fail fast on unreachable clusters. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Retries for transient errors | Implement automatic retries for transient errors with exponential backoff and only retry idempotent operations. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Bulk writes for updates | Use batched/bulk write operations for large-scale updates. | [Document size and batch write limits in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/max-document-size) |
| Partial updates | When updating fields on a customer document, use partial updates like $set (and upsert when appropriate) rather than replacing the entire document. | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| Shard key design | Design your shard/partition key so related customer data and most writes for a single customer map to the same logical partition (e.g., customer_id). | [documentdb-sharding](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/sharding/SKILL.md) |
| Compound index ESR | Create a compound index following the ESR rule for fields used together in aggregations (e.g., customer_id + order_date). | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Multikey indexes for arrays | For arrays you query or aggregate over (line items, product_ids), create appropriate multikey indexes and avoid unbounded arrays. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Projection of fields | Only project (return) the fields required for the computation in aggregation pipelines to reduce RU consumption and network transfer. | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |
| Early $match in pipelines | Keep aggregation pipelines concise and place $match stages early (preferably filtering on the partition/shard key) to reduce scanned records and RU costs. | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |
| Avoid very large documents | Avoid storing very large documents (stay well under the 16 MB BSON limit); split very large blobs into object storage or side collections and reference them instead. | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| Explain plans | Use explain("executionStats") / server-side explain plans to verify aggregations use intended indexes and to measure RU consumption. | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |
| Provision compute for heavy jobs | Provision sufficient compute/throughput for heavy aggregation jobs and index builds and schedule heavy batch/index work during off-peak windows. | [documentdb-storage](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/storage/SKILL.md) |
| Index build windows | Create or build indexes during low-traffic windows (or follow a safe lifecycle: hide → verify → drop). | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Automatic backups | Enable and configure automatic backups (and point-in-time restore where offered) so you can recover from accidental writes or faulty aggregation runs. | [documentdb-high-availability](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/high-availability/SKILL.md) |
| Observability | Enable diagnostic settings and application-level monitoring (Azure Monitor / Log Analytics) to track RU usage, slow queries, and throttling and alert on saturation. | [documentdb-monitoring](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md) |
| Transactions support | Azure DocumentDB supports multi-document ACID transactions across collections and shards (the platform documents multi-document transactions as supported). | [Azure DocumentDB at a glance](https://learn.microsoft.com/azure/documentdb/at-a-glance#mongodb-compatibility) |
| Local TLS relaxation | In local development, drive TLS relaxation (e.g., tlsAllowInvalidCertificates) from env vars and keep such relaxation out of production code. | [documentdb-local-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md) |

### How the app measures up

#### Violations

| Practice | Category | Evidence | Fix | Source |
|---|---|---|---|---|
| Set sensible socket and server-selection timeouts and tune them for your environment so client calls fail fast on unreachable clusters. | connection | app/src/db.py constructs MongoClient(uri) without serverSelectionTimeoutMS/socketTimeoutMS options (line 17). | Pass sensible defaults in get_client(), e.g. MongoClient(uri, serverSelectionTimeoutMS=5000, socketTimeoutMS=30000), and allow overriding via environment variables. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Implement automatic retries for transient errors with exponential backoff and only retry idempotent operations. | retries | No retry wrapper or exponential backoff logic found around DB calls (app/src/clv_tool.py and app/src/db.py show direct PyMongo usage). | Add retry logic (e.g., tenacity or a small wrapper) for transient operations and restrict retries to idempotent actions; document default retry policy in the README. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Use batched/bulk write operations for large-scale updates. | performance | update_customer_clv uses update_one (app/src/clv_tool.py line 46-47). No bulkWrite implementation for applying CLV for many customers is present. | Provide a bulk write helper that builds a list of UpdateOne ops and calls collection.bulk_write(ops) for batch persistence. | [Document size and batch write limits in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/max-document-size) |
| Record LLM outputs and the LLM rationale in structured fields and an append-only audit or history subdocument rather than overwriting a single source-of-truth field. | data_modeling | The sample writes clv_score, clv_tier, clv_rationale as top-level fields via $set (app/src/clv_tool.py line 46-47) and does not maintain an append-only audit/history subdocument. | Change update_customer_clv to $push an audit entry into a clv_history array (timestamp, score, tier, rationale, model) and keep latest fields if desired. | prior_knowledge (no public address recorded) |
| Sanitize and validate any values produced by an LLM before writing them to the database (type checking, allowed enums, ranges). | security | app/src/agent.py accepts LLM JSON and directly casts to float/string then writes to DB; there is no explicit validation of allowed tiers or score ranges before update (agent.py lines 76-81, clv_tool.update_customer_clv line 46-47). | Add validation: ensure clv_tier in {low,medium,high,VIP}, clv_score within 0..1000, sanitize rationale length and escape or truncate dangerous content before $push/$set. | prior_knowledge (no public address recorded) |

#### Could not be assessed

| Practice | Category | What was searched and missing | Source |
|---|---|---|---|
| Always use TLS for connections to Azure DocumentDB and do not disable certificate validation in production. | security | - | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Azure DocumentDB supports multi-document ACID transactions across collections and shards (the platform documents multi-document transactions as supported). | transactions | - | [Azure DocumentDB at a glance](https://learn.microsoft.com/azure/documentdb/at-a-glance#mongodb-compatibility) |
| In local development, drive TLS relaxation (e.g., tlsAllowInvalidCertificates) from env vars and keep such relaxation out of production code. | local_development | - | [documentdb-local-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md) |

#### Followed

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Create a single long-lived MongoClient per process (singleton) and reuse it for all requests; do not open a new client per request, and close it only on orderly shutdown. | connection | app/src/db.py lines 7-18 implement module-level _client and get_client() that creates MongoClient once. | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Read the DocumentDB connection string and other secrets from environment variables (or a runtime-loaded .env) and never commit secrets into source control or logs. | secrets | app/src/db.py reads DOCUMENTDB_URI from os.environ (line 13); app/.env.example contains placeholders (file contents). | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| When updating fields on a customer document, use partial updates like $set (and upsert when appropriate) rather than replacing the entire document. | data_modeling | update_customer_clv uses coll.update_one with $set to write clv_score, clv_tier, clv_rationale (app/src/clv_tool.py line 46-47). | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| Create a compound index following the ESR rule for fields used together in aggregations (e.g., customer_id + order_date). | indexing | An index on purchases.date was created (app/src/create_indexes.py line 7). The pipeline also benefits from the _id index when matching by _id (default). Index presence confirmed by MCP list (events: documentdb_list_indexes result). | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| For arrays you query or aggregate over (line items, product_ids), create appropriate multikey indexes and avoid unbounded arrays. | indexing | create_indexes.py creates an index on purchases.date (app/src/create_indexes.py line 7) which is an array field (multikey index). | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Only project (return) the fields required for the computation in aggregation pipelines to reduce RU consumption and network transfer. | queries | The aggregation pipeline groups and returns only computed aggregate values (app/src/clv_tool.py lines 9-20). | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |
| Keep aggregation pipelines concise and place $match stages early (preferably filtering on the partition/shard key) to reduce scanned records and RU costs. | queries | Pipeline begins with {$match: {_id: customer_id}} (app/src/clv_tool.py line 10), thus filtering early. | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |
| Avoid storing very large documents (stay well under the 16 MB BSON limit); split very large blobs into object storage or side collections and reference them instead. | data_modeling | Sample documents in seed.py embed a small purchases array (app/src/seed.py lines 6-33), not large blobs. | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |

#### Not applicable

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Design your shard/partition key so related customer data and most writes for a single customer map to the same logical partition (e.g., customer_id). | provisioning | This sample uses a single sample database/collection and does not create or document a sharded cluster or shard key. | [documentdb-sharding](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/sharding/SKILL.md) |
| Use explain("executionStats") / server-side explain plans to verify aggregations use intended indexes and to measure RU consumption. | monitoring | No explain() usage was added to the sample; the run used MCP list_indexes and observed RU warnings but no explain calls in code. | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |
| Provision sufficient compute/throughput for heavy aggregation jobs and index builds and schedule heavy batch/index work during off-peak windows. | provisioning | Sample uses an existing cluster and does not perform heavy index builds beyond a small test index; no provisioning code present. | [documentdb-storage](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/storage/SKILL.md) |
| Create or build indexes during low-traffic windows (or follow a safe lifecycle: hide → verify → drop). | indexing | Index creation was performed interactively in this run via a one-off pymongo command; sample does not include scheduled index lifecycle guidance. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Enable and configure automatic backups (and point-in-time restore where offered) so you can recover from accidental writes or faulty aggregation runs. | backup | Backup configuration is a cluster-level setting outside the sample; sample README does not instruct on backup configuration. | [documentdb-high-availability](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/high-availability/SKILL.md) |
| Enable diagnostic settings and application-level monitoring (Azure Monitor / Log Analytics) to track RU usage, slow queries, and throttling and alert on saturation. | monitoring | The sample includes no observability configuration or examples. | [documentdb-monitoring](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md) |

### Reference requirements

9 of 18 met. The builder never saw these; this measures the starter prompt and the skills.

| Requirement | Status | Cause | Evidence | Smallest fix |
|---|---|---|---|---|
| /search returns a clear error for an empty query and when the embedding call fails. | not_met | prompt_silent | No /search endpoint or search code exists in the repository. | If a search endpoint is intended, add a /search handler that validates input and returns clear error messages on empty query or embedding failures. |
| Dependencies are pinned in requirements.txt. | not_met | prompt_silent | app/requirements.txt uses >= ranges (e.g., pymongo>=4.4.0, langchain>=0.0.300) rather than exact pinned versions (file contents). | Pin exact versions (==) in requirements.txt or provide a constraints file (requirements-lock.txt) created by pip-compile or pip freeze for reproducible builds. |
| Unit tests run without a live cluster. | not_met | prompt_silent | app/tests/test_clv.py seeds and uses the real customers collection via get_customers_collection(); tests ran against the live cluster in this run (events show pytest executed against real DB). | Add unit tests that mock pymongo (e.g., mongomock or monkeypatch get_customers_collection) so CI can run without a live cluster, and keep integration tests separate. |
| Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. | not_met | prompt_silent | No IaC (Bicep/Terraform/ARM) files present in the repo. The run instructions and skill_md explicitly used an existing cluster instead. | Add a Bicep or Terraform example that uses Microsoft.DocumentDB/mongoClusters (sample parameters: tier, storage, region) or link to the deployment skill’s template. |
| Implement the sample in Python with a LangChain agent that acts as the single agent of the pipeline, with the DocumentDB aggregation tool registered as a LangChain tool the agent can invoke during a run. | partly_met | builder_error | app/src/agent.py calls compute_customer_metrics() directly and does not register a LangChain Tool object (no Tool(...) or initialize_agent tool registration observed). | Wrap compute_customer_metrics in a langchain.agents.Tool and register it when initializing the agent (few-line change in src/agent.py). |
| A seed script loads sample data and creates the index, and can be run twice without duplicating data. | partly_met | prompt_silent | app/src/seed.py is idempotent (uses update_one with upsert on lines 45-46) and can be run twice. Index creation is provided as a separate script (app/src/create_indexes.py) and was executed manually via an inline python command; seed.py does not create the index. | Add idempotent index creation to seed() (call create_index with name) or document that seed and index-creation are separate. Prefer adding index creation to seed for single-step setup. |
| The vector index dimensions match the embedding model's output. | not_checkable | could_not_determine | The sample does not use vector indexes or embeddings (no embedding code or vector-index creation). | If vectors are added, record the embedding model and dimensions in code and .env.example and validate at index creation time. |
| The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. | not_checkable | could_not_determine | No vector index creation or parameters in repository. | Not applicable unless vectors are used; otherwise add guidance when adding vector search features. |
| Search results include the similarity score. | not_checkable | could_not_determine | No search functionality implemented in this sample. | If adding search, include score in result projection and document it in README. |
| The DocumentDB aggregation tool runs an aggregation pipeline in Azure DocumentDB through a MongoDB driver and returns, per customer, historical purchase frequency, average order value and tenure. | met | - | app/src/clv_tool.py lines 9-20 create and run an aggregation pipeline; compute_customer_metrics returns purchase_count, avg_order_value and tenure_days (lines 6-42). | - |
| The agent includes the purchase frequency, average order value and tenure returned by the aggregation tool in the prompt it sends to the LLM. | met | - | app/src/agent.py lines 23-28 build the human prompt with `metrics` and `baseline_score` and pass it to the LLM call. | - |
| The prompt engineering instructs the LLM to estimate a CLV tier chosen from low, medium, high and VIP, to produce a CLV score, and to generate a rationale for the estimate. | met | - | app/src/agent.py PROMPT_INSTR (lines 11-20) instructs the model to return clv_score, clv_tier in [low, medium, high, VIP] and a rationale. | - |
| The agent writes the CLV score and tier back to that customer's profile document in Azure DocumentDB by updating the existing document. | met | - | app/src/clv_tool.py update_customer_clv uses coll.update_one with $set (line 46-47). compute_and_classify (app/src/agent.py lines 80-81) calls update_customer_clv to persist results. | - |
| The connection string and model credentials come from environment variables; none appear in the repository. | met | - | app/src/db.py reads DOCUMENTDB_URI from environment (line 13). app/src/agent.py reads OPENAI_API_KEY from environment (line 8). app/.env.example contains only placeholders (app/.env.example lines 2-3). | - |
| A .env.example lists every setting with placeholder values. | met | - | app/.env.example contains DOCUMENTDB_URI and OPENAI_API_KEY placeholders (file contents). | - |
| One database client is created and reused across requests. | met | - | app/src/db.py implements a module-level _client singleton and get_client() that creates MongoClient only once (lines 7-18). | - |
| The README covers what the sample shows, prerequisites, setup, run, and clean-up. | met | - | app/README.md includes the sample purpose, prerequisites, how to run, seed/cleanup notes (file contents). | - |
| The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name. | met | - | README.md and code refer to 'Azure DocumentDB' sample and do not reference Amazon DocumentDB or Cosmos DB in documentation files. | - |

