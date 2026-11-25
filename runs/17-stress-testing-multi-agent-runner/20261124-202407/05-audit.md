# 5. Best-practice audit: 17-stress-testing-multi-agent-runner

**Verdict: pass_with_findings** (12 followed, 2 violated, 1 not assessable, 1 not applicable)

The sample implements the requested Python LangChain multi-agent stress test: three agent roles, aggregation-based impact calculations against Azure DocumentDB, run persistence as audit documents, idempotent seeding, a CLI runner, and a small test suite. Key best-practice guidance from the DocumentDB skills (singleton client, env-based URI, index creation, upsert-style seeds) was discovered and followed. Remaining findings are mostly hygiene and discoverability gaps (unpinned dependencies, one failing unit test due to a fragile mock, some minor mismatches between seed scripts and code, and missing explicit driver pool/timeout tuning and retry logic). None of the uncovered issues makes the sample insecure or non-functional for the demonstrated run against the live cluster; they do affect sample robustness and gallery-readiness.

## Review of the builder's decisions

| Decision | What was decided | Reason came from | Assessment | Comment |
|---|---|---|---|---|
| D001 | I approved the build with readiness 'ready_with_gaps' | operator | sound | Decision to approve build with readiness 'ready_with_gaps' is recorded and consistent with the build actions and the builder_report. |
| D002 | I chose Python 3.11 for the sample runtime. | prompt | questionable | D002 states 'I chose Python 3.11'. That is a reasonable choice, but events/logs show the actual run environment used Python 3.13 artifacts (pip wheels referenced cp313). The choice is defensible but not strictly reflected in the runtime observed; duplicate D009 also records a 3.11 choice. |
| D003 | I chose the synchronous PyMongo driver (pymongo) and to use a singleton MongoClient. | skill | sound | Decision to use synchronous PyMongo and a singleton client is consistent with the documentdb-driver skill and is implemented in src/db.py. |
| D004 | I chose to read DOCUMENTDB_URI from the environment and instantiate a singleton MongoClient with conservative pool settings suitable for a CLI/long-running sample (maxPoolSize=20, minPoolSize=0). | skill | questionable | D004 recorded the intention to set conservative pool settings (maxPoolSize=20). The skill was loaded, but the final src/db.py in the repo does not set maxPoolSize or explicit timeouts (it calls MongoClient(_DOCUMENTDB_URI, retryWrites=True)). The decision is therefore not fully implemented in code. |
| D005 | I chose to create single-field indexes on account_id, instrument, and timestamp (descending) and a partial index on risk_factors.rateSensitivity because the sample's aggregation filters will commonly filter by instrument or account and group by timestamp windows. | skill | sound | Indexing decision D005 is implemented: scripts/seed.py creates indexes matching the decision (idx_account, idx_instrument, idx_timestamp, idx_rate_sens). |
| D006 | I chose to use the live DocumentDB cluster reachable via DOCUMENTDB_URI for seeding and verification. | readiness_report | sound | Decision to use the live DocumentDB cluster (DOCUMENTDB_URI) for seeding and verification is recorded and matches the run (run_seed.py executed successfully against the live cluster). |
| D007 | I chose to create a small runner script `run_seed.py` that adjusts sys.path and imports the seed script, because the shell-style PYTHONPATH prefix was refused by the runner. | tool_result | sound | Decision to add run_seed.py because PYTHONPATH=... was refused is supported by events showing the PYTHONPATH invocation was refused and run_seed.py was created and used. |
| D008 | I approved the build with readiness 'ready_with_gaps' | operator | sound | Duplicate readiness approval entry; consistent with D001. |
| D009 | I chose Python 3.11 for the sample runtime. | model_default | questionable | Duplicate record of choosing Python 3.11 recorded with reason_source 'model_default'. See D002 comments: the environment logs suggest cp313 (Python 3.13) packages were used, so this decision is defensible but not fully aligned with the runtime artifacts. |
| D010 | I chose the synchronous PyMongo MongoClient (blocking) for simplicity. | prompt | sound | Decision to use synchronous PyMongo (again) is reflected in code (sync PyMongo usage) and tests; this is implemented. |
| D011 | I chose to read the DocumentDB connection string from the DOCUMENTDB_URI environment variable at runtime. | prompt | sound | Decision to read DOCUMENTDB_URI from environment is implemented in src/db.py and recorded in events; evidence present. |
| D012 | I chose OpenAI (public) as the LLM provider using text-embedding-3-small (1536 dims) for embeddings and gpt-4o-mini for chat when available, but the sample will run without an API key (LLM steps become optional). | prompt | questionable | D012 records a choice of OpenAI and embedding model dimensions (text-embedding-3-small / 1536 dims). The repository makes the LLM path optional and does not create vector indexes or embeddings; the stated embedding-model decision is not exercised in code. The decision is reasonable but not realized by the sample. |
| D013 | I chose a simple CLI entrypoint (run_stress_test.py) as the app surface. | prompt | sound | Decision to expose a CLI entrypoint (run_stress_test.py) is reflected in the repo and README and was used for verification. |

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
| Known to the model, no public source, not on the checklist | 2 | Agents will act on it from memory. Decide whether it holds for this service, then document it either way. |
| On the checklist and found by open discovery | 14 | Public and discoverable. |

#### Known to the model, no public source, not on the checklist

| Topic | Description | What would help |
|---|---|---|
| Audit document shape | Treat a recommended audit document shape (immutable, run_id, created_at, schema_version, scenario_parameters, agent_outputs, aggregated_results, provenance) as an application-level convention. | A short public example run-document schema on the DocumentDB sample-page would let agents confirm this exact shape. |
| Tests/Unit testing guidance | For unit tests prefer lightweight mocks or run integration tests against an isolated live test database. | An example in the sample README showing how to run tests offline (mongomock or mock patterns) would help agents author similar samples. |

#### On the checklist and found by open discovery

| Topic | Description | Sources |
|---|---|---|
| Connection client reuse | Create one MongoClient per process and reuse it (module/global singleton) rather than creating a new client per request. | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Connection tuning | Tune connection-pool and driver timeouts to your deployment pattern; set serverSelectionTimeoutMS/connectTimeoutMS/socketTimeoutMS appropriately. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Read URI from env | Read the cluster connection string only from environment variables (e.g., DOCUMENTDB_URI) and never hard-code or write it to logs or files. | [documentdb-local-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md) |
| TLS enforcement | Always use TLS for connections and do not disable certificate validation in production. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Retry semantics | Implement retry semantics for transient errors and throttling: use exponential backoff with jitter and honor 429 / Retry-After responses. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Index queries | Create indexes that match the fields used in filters and early $match stages; prefer a well-ordered compound index rather than many single-field indexes. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Aggregation pipeline patterns | When running aggregation pipelines, push $match and $project stages early and use allowDiskUse for large groups/sorts; verify plan with explain() to avoid COLLSCANs. | [aggregate](https://learn.microsoft.com/documentdb/query/commands/aggregation/aggregate) |
| Seed idempotency | Make seed scripts idempotent by using upsert/replaceOne. | [MongoDB Query Language (MQL) compatibility in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/compatibility-query-language#database-commands) |
| Schema versioning | Include a schemaVersion field in persisted documents and perform lazy per-document migration. | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| Document size | Keep documents well under the 16 MB BSON document limit. | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| Instrumentation and explain() usage | Use explain('executionStats') or the MCP explain_operation tool to verify index usage for aggregation pipelines when tuning. | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |
| Seed indexes | Create useful indexes as part of seed/index scripts so sample data and queries run efficiently and idempotently. | src/seed.py |
| Compatibility checks | If a driver or command isn't supported on Azure DocumentDB (check compatibility), adapt code to supported alternatives rather than assuming server parity (e.g., use replaceOne upsert loops). | [MongoDB Query Language (MQL) compatibility in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/compatibility-query-language#database-commands) |
| Monitoring guidance | Monitor cluster metrics and enable diagnostic settings and slow-query logs. | [documentdb-monitoring](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md) |

### How the app measures up

#### Violations

| Practice | Category | Evidence | Fix | Source |
|---|---|---|---|---|
| Tune connection-pool and driver timeouts to your deployment pattern; set serverSelectionTimeoutMS/connectTimeoutMS/socketTimeoutMS appropriately. | connection | src/db.py:15-16 creates MongoClient(_DOCUMENTDB_URI, retryWrites=True) without explicit maxPoolSize, serverSelectionTimeoutMS, or connectTimeoutMS. | Set sensible pool/timeouts on MongoClient (e.g. MongoClient(uri, maxPoolSize=20, serverSelectionTimeoutMS=5000, connectTimeoutMS=10000, retryWrites=True)). | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Implement retry semantics for transient errors and throttling: use exponential backoff with jitter and honor 429 / Retry-After responses. | retries | Aggregation calls in src/agents.py:87-89 and src/main.py:54-55 call collection.aggregate(...) with no retry wrapper. MongoClient is created with retryWrites=True but no application-level retries for aggregations. | Wrap aggregation calls in a small retry helper (exponential backoff + jitter) or use tenacity; handle transient network errors explicitly. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |

#### Could not be assessed

| Practice | Category | What was searched and missing | Source |
|---|---|---|---|
| Use explain('executionStats') or the MCP explain_operation tool to verify index usage for aggregation pipelines when tuning. | queries | - | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |

#### Followed

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Create one MongoClient per process and reuse it (module/global singleton) rather than creating a new client per request. | connection | src/db.py:15-20 (module-level _client and get_client/get_db exposing singleton). | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Read the cluster connection string only from environment variables (e.g., DOCUMENTDB_URI) and never hard-code or write it to logs or files. | connection | src/db.py:8-13 reads DOCUMENTDB_URI from environment and raises if missing; .env.example uses placeholders. | [documentdb-local-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md) |
| Always use TLS for connections and do not disable certificate validation in production. | security | .env.example suggests a TLS-enabled SRV URI with tls=true (app/.env.example: lines 2-4). The client relies on the connection string TLS settings rather than forcing tls flags in code (src/db.py:16). | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Create indexes that match the fields used in filters and early $match stages; prefer a well-ordered compound index rather than many single-field indexes. | indexing | scripts/seed.py: create_indexes creates indexes on account_id, instrument, timestamp and risk_factors.rateSensitivity (scripts/seed.py: lines that create indexes). These support the sample's aggregation patterns. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| When running aggregation pipelines, push $match and $project stages early and use allowDiskUse for large groups/sorts; verify plan with explain() to avoid COLLSCANs. | queries | Main aggregation pipelines in src/main.py and src/agents.py put projection before grouping (src/main.py:12-41, src/agents.py:45-81). No large sorts are used in the sample; explain() was used by the builder interactively via MCP but not invoked in code. | [aggregate](https://learn.microsoft.com/documentdb/query/commands/aggregation/aggregate) |
| Make seed scripts idempotent by using upsert/replaceOne. | bulk_ops | scripts/seed.py: load_seed_data uses pos.replace_one({'_id': d['_id']}, d, upsert=True) (scripts/seed.py load_seed_data). | [MongoDB Query Language (MQL) compatibility in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/compatibility-query-language#database-commands) |
| Include a schemaVersion field in persisted documents and perform lazy per-document migration. | schema | src/run_stress_test.py:59 sets 'schemaVersion': 1 when persisting run_doc. src/main.py:69 sets 'schemaVersion': 1 in run_doc as well. | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| Keep documents well under the 16 MB BSON document limit. | data_modeling | data/positions_seed.json contains small position documents and run documents are compact (app/data/positions_seed.json, src/run_stress_test.py run_doc). | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| Create useful indexes as part of seed/index scripts so sample data and queries run efficiently and idempotently. | seed | scripts/seed.py create_indexes() creates indexes for positions (scripts/seed.py: pos.create_index calls). | src/seed.py |
| If a driver or command isn't supported on Azure DocumentDB (check compatibility), adapt code to supported alternatives rather than assuming server parity (e.g., use replaceOne upsert loops). | compatibility | scripts/seed.py uses replace_one upserts rather than bulkWrite, avoiding bulkWrite compatibility issues (scripts/seed.py: load_seed_data uses replace_one with upsert=True). | [MongoDB Query Language (MQL) compatibility in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/compatibility-query-language#database-commands) |
| Treat a recommended audit document shape (immutable, run_id, created_at, schema_version, scenario_parameters, agent_outputs, aggregated_results, provenance) as an application-level convention. | data_modeling | src/run_stress_test.py:53-60 constructs run_doc with _id, scenario, impact_summary, narrative, generated_at, schemaVersion (src/run_stress_test.py:53-60). | prior_knowledge (no public address recorded) |
| For unit tests prefer lightweight mocks or run integration tests against an isolated live test database. | testing | tests/test_agents.py uses deterministic ScenarioAgent and ReportingAgent; tests/test_orchestrator.py uses mocks to avoid a live DB but has a fragile MagicMock side_effect (tests/test_orchestrator.py:17-19). | prior_knowledge (no public address recorded) |

#### Not applicable

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Monitor cluster metrics and enable diagnostic settings and slow-query logs. | monitoring | The sample is a small CLI demonstration; it does not attempt to set diagnostic settings or monitoring. The builder did inspect the cluster via MCP during verification (builder_report). | [documentdb-monitoring](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md) |

### Reference requirements

10 of 18 met. The builder never saw these; this measures the starter prompt and the skills.

| Requirement | Status | Cause | Evidence | Smallest fix |
|---|---|---|---|---|
| /search returns a clear error for an empty query and when the embedding call fails. | not_met | prompt_silent | The sample does not implement a /search endpoint or a search flow using embeddings. | Add a small search API or CLI routine that validates input and returns clear errors on empty query or embedding failures. |
| Search results include the similarity score. | not_met | prompt_silent | No search implementation or vector-search results exist in the repo. | If adding search, include similarity scores in result documents and in the returned report structure. |
| Dependencies are pinned in requirements.txt. | not_met | prompt_silent | app/requirements.txt contains version ranges using >= rather than exact pins (pymongo>=4.5.0, langchain>=0.0.350, etc.). | Pin exact versions in requirements.txt (e.g. pymongo==4.20.1, langchain==1.5.2, python-dotenv==1.2.4, openai==3.59.0, pytest==7.4.0). |
| Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. | not_met | prompt_silent | No IaC files (Bicep/ARM/Terraform) are present in the repository; readiness findings flagged this as likely missing and events show no write_file creating IaC. | Add a small Bicep/ARM or Terraform sample that uses Microsoft.DocumentDB/mongoClusters (or az documentdb mongocluster CLI snippet) with tier/storage/region parameters. |
| The scenario agent uses the LLM to generate macroeconomic shock parameters for a stress scenario and returns them in a structured form that the impact agent can consume. | partly_met | prompt_silent | src/agents.py:6-27 (ScenarioAgent.generate returns a structured dict); src/run_stress_test.py:48-50 (build_llm_client returns None if no OPENAI_API_KEY, making LLM path optional). | Document that the LLM path is optional and add an integration test exercising the OpenAI path when OPENAI_API_KEY is present. |
| Unit tests run without a live cluster. | partly_met | builder_error | Tests are present (tests/test_agents.py and tests/test_orchestrator.py). Running pytest produced 3 passed, 1 failed (test_run_persists_run) due to a fragile MagicMock side_effect pattern (tests/test_orchestrator.py:17-19 uses __getitem__.side_effect that returns a new MagicMock for stress_runs). | Change the test's fake_db.__getitem__.side_effect to return a stable MagicMock for 'stress_runs' (pre-create fake_stress_runs = MagicMock() and return it), or use mongomock to simulate the DB. |
| The vector index dimensions match the embedding model's output. | not_checkable | prompt_silent | The sample does not create or use vector indexes; vector features are not exercised (builder_report: 'Vector index creation and vector-search pipeline: not used or created by this sample'). | If adding vector search, add env vars EMBEDDING_MODEL/EMBEDDING_DIMS and create-index code that uses EMBEDDING_DIMS. |
| The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. | not_checkable | prompt_silent | No vector index created or referenced in code or README. | If vector search is added, include guidance in README and env placeholders for index parameters. |
| The system is written in Python with LangChain and is organised as a multi-agent runner: an orchestrator coordinates three distinct agent roles (a scenario agent, an impact agent and a reporting agent) and runs them as one stress test, handing each agent's output to the next. | met | - | src/run_stress_test.py:41-50 (ScenarioAgent instantiation, ImpactAgent compute call, ReportingAgent synthesis) and src/agents.py class definitions (ScenarioAgent, ImpactAgent, ReportingAgent). | n/a |
| The impact agent computes P&L impacts by running aggregation pipelines in Azure DocumentDB over the stored position data. | met | - | src/agents.py:37-95 (ImpactAgent.compute builds and runs aggregation pipeline); src/run_stress_test.py:45-46 (ImpactAgent created and compute called). | n/a |
| The reporting agent synthesises scenario parameters and impact results into a structured stress test report and the orchestrator returns that report as the result of the run. | met | - | src/agents.py:111-124 (ReportingAgent.synthesize), src/run_stress_test.py:50-63 (report created, persisted, and printed). | n/a |
| Every scenario run is stored as a document in Azure DocumentDB for audit. | met | - | src/run_stress_test.py:53-61 (run_doc constructed with schemaVersion and inserted via persist_run -> coll.insert_one); verification in builder_report: 'documentdb_find_documents ... returned the inserted run document'. | n/a |
| The connection string and model credentials come from environment variables; none appear in the repository. | met | - | .env.example: lines 4-7 (DOCUMENTDB_URI and OPENAI_API_KEY placeholders); src/db.py:8-13 reads DOCUMENTDB_URI from environment and errors if missing. | n/a |
| A .env.example lists every setting with placeholder values. | met | - | app/.env.example lists DOCUMENTDB_URI, OPENAI_API_KEY and DB_NAME (app/.env.example: lines 4-10). Code uses DB_NAME/DB_NAME equivalent and OPENAI_API_KEY where applicable. | n/a |
| One database client is created and reused across requests. | met | - | src/db.py:15-20 defines a module-level MongoClient singleton and get_client/get_db helpers (lines 15-23). | n/a |
| A seed script loads sample data and creates the index, and can be run twice without duplicating data. | met | - | scripts/seed.py: ensure_collections, create_indexes, and load_seed_data perform replace_one upserts (scripts/seed.py: load_seed_data uses replace_one ... upsert=True). The run used run_seed.py which imports scripts/seed.py and completed successfully (events: run_seed.py executed with exit code 0). | n/a |
| The README covers what the sample shows, prerequisites, setup, run, and clean-up. | met | - | app/README.md includes 'What this sample shows', 'Prerequisites', 'Quickstart' and 'Cleaning up' sections (README.md lines 1-34). | n/a |
| The sample uses the name 'Azure DocumentDB' throughout, and no former or neighbouring product name. | met | - | app/README.md and code comments use 'Azure DocumentDB' and do not reference CosmosDB or Amazon DocumentDB. | n/a |

