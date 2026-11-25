# 5. Best-practice audit: 15-digital-onboarding-orchestration

**Verdict: pass_with_findings** (6 violated, 9 followed, 3 not assessable, 4 not applicable)

The sample implements the requested orchestrator: a Beanie Document model, a sequential orchestrator that delegates to three agents, atomic updates inside driver transactions, idempotent seed, index scripts, CLI and FastAPI surfaces, and unit tests that run without a live cluster. Major functional requirements from the starter prompt are met. Findings include: (1) the orchestrator uses Motor/MotorClient calls rather than loading the document through Beanie model methods (the code intentionally mixes Beanie model definitions with Motor updates); (2) the code uses Motor (AsyncIOMotorClient) rather than the newer PyMongo AsyncMongoClient recommended by the DocumentDB connection guidance; (3) history is embedded but not capped (no $slice), risking unbounded growth; (4) no retry/backoff logic for transient errors; (5) vector / embedding guidance and infra-as-code were not supplied (prompt did not ask), so these checklist items are missing and flagged as documentation gaps; (6) a small README/CLI mismatch and a minor info-leak risk in logging the full connection string. I verified the seed, index creation (via Motor fallback), index listing via MCP tools, and tests (1 unit test passed). See requirement_results for line-by-line status, practice checks for discoverability and follow/violate status, decision_reviews for recorded choices, and doc_gaps with recommended deliverables for the product team.

## Review of the builder's decisions

| Decision | What was decided | Reason came from | Assessment | Comment |
|---|---|---|---|---|
| D001 | I approved the build with readiness 'ready_with_gaps' | operator | sound | Operator decision to approve 'ready_with_gaps' is recorded in decisions.jsonl and is consistent with the run. events.jsonl includes the corresponding log entries. |
| D002 | I chose Python 3.13 (system python) for the sample runtime and virtualenv. | readiness_report | sound | Choice of Python 3.13 is consistent with the run environment and subsequent build steps; evidence in events.jsonl and used by pip/pytest runs. |
| D003 | I chose Beanie 1.21.x (stable 1.x series) for ODM. | model_default | questionable | Initially choosing Beanie 1.21.x was defensible, but a later tool result (pip) led the builder to use beanie==1.25.0. The decision relied on model_default rather than a single authoritative source and was later revised (see D012). |
| D004 | I chose to pin specific package versions in requirements.txt (Beanie==1.21.0, motor==3.1.1, pymongo==4.5.0, langchain==0.0.236, openai==1.0.0, python-dotenv==1.0.0, pytest==7.4.0, pytest-asyncio==0.22.0). | model_default | questionable | Pinning dependencies is good practice. The exact pinned versions were based on model_default assumptions and were later adjusted after tool feedback (pip install output). The events show subsequent changes to pinned versions (D012, D013). |
| D005 | I approved the build with readiness 'ready_with_gaps' | operator | sound | Duplicate operator approval similar to D001; recorded in decisions.jsonl and consistent with events. |
| D006 | I chose Python 3 (async) with Motor + Beanie ODM and FastAPI for the sample. | prompt | sound | Choosing Python async + Motor + Beanie + FastAPI matches the code produced and the prompt. Evidence in repository and events.jsonl. |
| D007 | I chose beanie==1.24.1 and motor==3.1.1 pinned in requirements.txt. | model_default | wrong | Decision to pin beanie==1.24.1 was later shown to be invalid: pip could not find 1.24.1 and the builder updated the version (events.jsonl shows pip failure and later D012 switching to 1.25.0). The events show the tool feedback and the subsequent correction. |
| D008 | I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime. | prompt | sound | Decision to read DOCUMENTDB_URI from environment is implemented (app/src/sample_orchestrator/db.py reads os.environ['DOCUMENTDB_URI']). Note: some attempts to log this decision failed due to an invalid reason_source value in a log_decision call (events.jsonl lines ~14-18 show validation exceptions for log_decision with reason_source='skill_md'). |
| D009 | I chose Motor's find_one_and_update with client.start_session() and start_transaction() for atomic state transitions while using Beanie for model definitions. | skill | sound | Decision to use Motor's find_one_and_update inside a driver session/transaction is implemented in orchestrator.py and is consistent with the intent to combine Beanie definitions and explicit transactional Motor updates (events.jsonl shows the write_file for orchestrator and the transaction usage). |
| D010 | I chose an embedded compact history array on the onboarding document to record transitions (agent, from_state, to_state, ts) rather than a separate audit collection. | skill | sound | Decision to embed a compact history array is implemented (models.py and orchestrator.py append history inline). The choice is explicit and documented; the auditor notes the history is not capped and suggests limiting growth. |
| D011 | I chose to create a single-field index on 'state' (for quick queries by processing state) and a compound index on ('applicant_id', 'state') to support lookups by applicant and to follow the ESR ordering (equality then sort/range). | skill | sound | Decision to create indexes on 'state' and a compound index on applicant_id+state is implemented; create_indexes.py and events.jsonl show indexes created and verified by documentdb_list_indexes. |
| D012 | I chose to use beanie==1.25.0 after pip reported 1.24.1 is not available. | tool_result | sound | Tool-driven correction to beanie==1.25.0 is recorded and matches the content of app/requirements.txt and the pip installation logs in events.jsonl; the decision is supported by the pip failure that triggered it. |
| D013 | I chose fastapi==0.98.0 after pip reported 0.98.1 is not available. | tool_result | sound | FastAPI version adjustment to 0.98.0 after tool feedback is recorded and consistent with the final requirements and pip install output. |

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
| Known to the model, no public source, not on the checklist | 3 | Agents will act on it from memory. Decide whether it holds for this service, then document it either way. |
| On the checklist and found by open discovery | 19 | Public and discoverable. |

#### Known to the model, no public source, not on the checklist

| Topic | Description | What would help |
|---|---|---|
| Optimistic concurrency | Use optimistic concurrency (version or lastUpdated checked in update predicate) | A short Microsoft Learn page or note in the agent-kit documenting an optimistic-concurrency pattern for the Mongo API (example using findOneAndUpdate with version or timestamp). |
| Beanie startup init | When using Beanie with an async driver, initialize Beanie once at startup with your Motor/Async client and document models and reuse the client | A short Azure doc explaining Beanie + Motor init pattern and session handling would let an agent rely on public guidance instead of prior knowledge. |
| Mock DB for CI | In CI, mock the DB and driver sessions for unit tests and run integration tests that seed and mutate a live cluster only when permitted | A short Microsoft Learn note recommending mocking Motor/Beanie for unit tests and reserving live cluster integration tests for gated CI runs would help agents. |

#### On the checklist and found by open discovery

| Topic | Description | Sources |
|---|---|---|
| Singleton client | Create a single AsyncMongoClient at application startup and reuse it across the process instead of creating a client per request; Motor is deprecated for new Python async code in favor of PyMongo's AsyncMongoClient. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Connection config | Configure the MongoDB async client with TLS and sensible connection-pool and timeout settings (maxPoolSize, minPoolSize, maxIdleTimeMS, connectTimeoutMS, socketTimeoutMS) | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Secret handling | Read the cluster connection string from a secure source at runtime (environment variable such as DOCUMENTDB_URI...), do not commit credentials to the repository or logs and provide a .env.example placeholder for local dev. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Transaction usage | Group multi-operation updates inside a driver session transaction and keep transactions short | [Transactions](https://learn.microsoft.com/azure/documentdb/how-to-transactions#create-a-transaction) |
| Embed vs history | Model a state machine document with an embedded, bounded history only when the history is bounded; otherwise use a separate history collection | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| Work-queue indexes | Create a unique index on application identifier and add a compound index for orchestrator lookup patterns | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Partial/sparse indexes | Use partial or sparse indexes for fields present only on active items to reduce RU cost | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Transient fault retries | Handle transient faults with exponential backoff and limited retries | [Reliability in Azure DocumentDB](https://learn.microsoft.com/azure/reliability/reliability-documentdb#resilience-to-transient-faults) |
| Small transactions | Keep transactions and updates small; avoid updating large blobs inside a transaction | [documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md) |
| Projection to avoid vectors | Use projection to avoid transferring vectors or other large fields unless required | [documentdb-query-optimization](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimization/SKILL.md) |
| Atomic audit history | Record audited state transitions and make the append part of the same atomic update/transaction | [Group multiple operations in transactions in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/how-to-transactions#create-a-transaction) |
| Create indexes before bulk load | Create indexes (including vector indexes) before bulk-loading or running large backfills | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Limit embedded history writes | Limit the size of embedded history writes with $push + $slice or cap the history length | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| Monitor RU/throughput | Monitor RU/throughput and slow queries; use explain() to diagnose slow queries and alert on RU throttling | [documentdb-monitoring](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md) |
| Transaction retry | When using transactions, implement recommended retry-on-transient-failure logic | [Transactions](https://learn.microsoft.com/azure/documentdb/how-to-transactions#create-a-transaction) |
| Document size | Keep per-document size well under the 16 MB limit by avoiding large inline blobs or very high-dimension vectors | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| Verify indexes with explain | Use explain('executionStats') to verify index usage and avoid COLLSCAN | [documentdb-query-optimization](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimization/SKILL.md) |
| HA & DR guidance | Enable in-region high availability (HA) on production clusters | [documentdb-high-availability](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/high-availability/SKILL.md) |
| Production hardening | Harden production clusters with network isolation, Entra ID + RBAC and CMK | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |

### How the app measures up

#### Violations

| Practice | Category | Evidence | Fix | Source |
|---|---|---|---|---|
| Create a single AsyncMongoClient at application startup and reuse it across the process instead of creating a client per request; Motor is deprecated for new Python async code in favor of PyMongo's AsyncMongoClient. | connection | app/src/sample_orchestrator/db.py:7-16 (uses Motor AsyncIOMotorClient and a singleton _client), not AsyncMongoClient from PyMongo. | Use the recommended PyMongo AsyncMongoClient (or update requirements and code) or state in README why Motor is intentionally used; change get_client to construct PyMongo's Async client and update requirements.txt accordingly. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Configure the MongoDB async client with TLS and sensible connection-pool and timeout settings (maxPoolSize, minPoolSize, maxIdleTimeMS, connectTimeoutMS, socketTimeoutMS) | connection | app/src/sample_orchestrator/db.py:12-17 (client = AsyncIOMotorClient(uri) with no explicit pool/timeout settings). | Pass recommended options when creating the client (e.g., AsyncIOMotorClient(uri, maxPoolSize=50, maxIdleTimeMS=120000, tls=True, serverSelectionTimeoutMS=2000)) and document the rationale in README. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Model a state machine document with an embedded, bounded history only when the history is bounded; otherwise use a separate history collection | data_modeling | app/src/sample_orchestrator/models.py:14-19 (history: List[Transition] = Field(default_factory=list)) and app/src/sample_orchestrator/orchestrator.py:44-46 (pushes full transition into history) but no cap is applied. | Limit embedded history with $push + $slice (e.g., use {'$push': {'history': {'$each':[transition], '$position':0, '$slice':100}}}) or move transitions to a separate history collection. Update create/update paths accordingly. | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| Handle transient faults with exponential backoff and limited retries | retries | Orchestrator and seed scripts perform direct driver calls without retry/backoff wrappers; no retry logic around transactions or index creation (see app/src/sample_orchestrator/orchestrator.py and app/scripts/seed.py). | Wrap critical operations (transactions, write operations) with retry logic and exponential backoff (or use driver-level retry settings) and make transaction bodies idempotent. | [Reliability in Azure DocumentDB](https://learn.microsoft.com/azure/reliability/reliability-documentdb#resilience-to-transient-faults) |
| Limit the size of embedded history writes with $push + $slice or cap the history length | data_modeling | orchestrator uses '$push': {'history': transition} with no $slice or cap (app/src/sample_orchestrator/orchestrator.py:44-46). | Use $push with $each/$slice to cap history length in the same transaction (update query change). | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| When using transactions, implement recommended retry-on-transient-failure logic | transactions | Orchestrator transaction block does not implement retry-on-transient-error; no retry wrapper around the transaction body (app/src/sample_orchestrator/orchestrator.py:41-50). | Wrap transaction logic inside a retry loop per guidance (retry the withTransaction callback on transient errors) and ensure transaction body is idempotent. | [Transactions](https://learn.microsoft.com/azure/documentdb/how-to-transactions#create-a-transaction) |

#### Could not be assessed

| Practice | Category | What was searched and missing | Source |
|---|---|---|---|
| Use optimistic concurrency (version or lastUpdated checked in update predicate) | data_modeling | Searched 'Azure DocumentDB optimistic concurrency version findOneAndUpdate' (no authoritative Azure DocumentDB doc found that prescribes a specific pattern for the Mongo API). | None recorded |
| Use partial or sparse indexes for fields present only on active items to reduce RU cost | indexing | - | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Use explain('executionStats') to verify index usage and avoid COLLSCAN | queries | - | [documentdb-query-optimization](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimization/SKILL.md) |

#### Followed

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Read the cluster connection string from a secure source at runtime (environment variable such as DOCUMENTDB_URI...), do not commit credentials to the repository or logs and provide a .env.example placeholder for local dev. | authentication | app/.env.example:1-5 (placeholder); app/src/sample_orchestrator/db.py:12-16 (reads DOCUMENTDB_URI from env). | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Group multi-operation updates inside a driver session transaction and keep transactions short | transactions | app/src/sample_orchestrator/orchestrator.py:41-50 (start_session + start_transaction + find_one_and_update with session). | [Transactions](https://learn.microsoft.com/azure/documentdb/how-to-transactions#create-a-transaction) |
| Create a unique index on application identifier and add a compound index for orchestrator lookup patterns | indexing | app/scripts/create_indexes.py:14-16 and later scripts/create_indexes.py (created applicant_id unique and status/state index); events.jsonl shows indexes created and listed (documentdb_list_indexes results). | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Keep transactions and updates small; avoid updating large blobs inside a transaction | transactions | Orchestrator updates only small fields (state, history entry) inside transactions (app/src/sample_orchestrator/orchestrator.py:44-46). | [documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md) |
| When using Beanie with an async driver, initialize Beanie once at startup with your Motor/Async client and document models and reuse the client | connection | app/src/sample_orchestrator/db.py:20-23 calls await init_beanie(database=client[db_name], document_models=[OnboardingApplication]) at startup. | None recorded |
| Record audited state transitions and make the append part of the same atomic update/transaction | logging | app/src/sample_orchestrator/orchestrator.py:42-50 (transaction) app/src/sample_orchestrator/orchestrator.py:44-46 ($set state and $push history executed in same transaction). | [Group multiple operations in transactions in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/how-to-transactions#create-a-transaction) |
| Create indexes (including vector indexes) before bulk-loading or running large backfills | indexing | scripts/create_indexes.py exists and was used to create indexes before/around seed operations (events.jsonl shows scripts/create_indexes.py executed and indexes observed). | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| In CI, mock the DB and driver sessions for unit tests and run integration tests that seed and mutate a live cluster only when permitted | testing | app/tests/test_orchestrator.py uses monkeypatch/fakes and does not require a live cluster; pytest passed (events.jsonl). | None recorded |
| Keep per-document size well under the 16 MB limit by avoiding large inline blobs or very high-dimension vectors | data_modeling | Model fields are small (strings, small history entries); no large inline blobs or vectors present in model (app/src/sample_orchestrator/models.py). | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |

#### Not applicable

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Use projection to avoid transferring vectors or other large fields unless required | queries | The sample does not store or transfer vector fields in queries. | [documentdb-query-optimization](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimization/SKILL.md) |
| Monitor RU/throughput and slow queries; use explain() to diagnose slow queries and alert on RU throttling | provisioning | Sample is a small example and does not include monitoring/diagnostic setup. | [documentdb-monitoring](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md) |
| Enable in-region high availability (HA) on production clusters | high_availability | Sample targets an existing cluster for demonstration; production HA is out-of-scope for this sample. | [documentdb-high-availability](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/high-availability/SKILL.md) |
| Harden production clusters with network isolation, Entra ID + RBAC and CMK | security | Sample is a dev/example project and does not attempt to provision or configure production network/security features. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |

### Reference requirements

12 of 19 met. The builder never saw these; this measures the starter prompt and the skills.

| Requirement | Status | Cause | Evidence | Smallest fix |
|---|---|---|---|---|
| The vector index dimensions match the embedding model's output | not_met | prompt_silent | The sample does not create any vector index (app/scripts/create_indexes.py creates simple single-field indexes; vector indexes not implemented). | Add an explicit instruction to the starter prompt or a README section: 'If you include vector search, specify the embedding model (provider and model) and its output dimension; pass embeddings_dim to the index-creation helper so index dims match model output.' |
| The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one | not_met | prompt_silent | No vector index created, and README has no guidance about vector index sizing or parameters. | Add a README section explaining index type and tunables and a parameterized index creation helper in scripts/create_indexes.py to accept data-size-guided parameters. |
| Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type | not_met | prompt_silent | Repository contains no Bicep/ARM/Terraform file for Microsoft.DocumentDB/mongoClusters (no infra files present). | Add a minimal IaC example (Bicep or Terraform/AzAPI) that declares a Microsoft.DocumentDB/mongoClusters resource with reasonable default tier/storage (commented) so authors can provision the correct vCore DocumentDB resource. |
| A Python LangChain orchestration pipeline acts as the orchestrator: it loads an onboarding application document through Beanie and drives that application through the journey | partly_met | builder_error | app/src/sample_orchestrator/orchestrator.py:24-26 (loads app via coll.find_one using Motor) and app/src/sample_orchestrator/db.py:20-23 (init_beanie is called at startup) | Change the orchestrator to load the document via Beanie (e.g. await OnboardingApplication.find_one({'applicant_id': application_id}) or use OnboardingApplication.get_by_id/ appropriate Beanie API) and pass driver sessions into Beanie/Motor calls for transactional updates. |
| The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name | partly_met | builder_error | app/README.md uses 'DocumentDB' and references DocumentDB. However, app/.env.example line 2 example connection string uses a cosmos-style host ("clustername.mongo.cosmos.azure.com") in the comment; events/logs also include a real cluster URI referencing 'mongocluster.cosmos.azure.com' displayed in runtime logs. | Replace host examples with neutral placeholders in .env.example and avoid printing full connection strings in logs; prefer 'mongodb+srv://<USER>:<REDACTED>@<CLUSTER_URI>/?...' or simply '<YOUR_DOCUMENTDB_URI_HERE>' so the repository doesn't hint at neighbouring product examples. |
| /search returns a clear error for an empty query and when the embedding call fails | not_checkable | prompt_silent | No /search endpoint is implemented in this sample. | If you add a /search endpoint, include explicit checks for empty query and wrap embedding calls with try/except to return clear 4xx/5xx errors. |
| Search results include the similarity score | not_checkable | prompt_silent | No search endpoint or embedding-based queries implemented in this sample. | If search is implemented, return similarity score alongside document metadata. |
| A Python Beanie ODM `Document` model represents an onboarding application as a state machine stored in Azure DocumentDB | met | - | app/src/sample_orchestrator/models.py:14-20 (OnboardingApplication with state, history, schemaVersion) | none |
| Three separate agents exist for the roles of ID verification, risk assessment and account opening, and the orchestrator delegates each step to the matching agent | met | - | app/src/sample_orchestrator/agents.py:8-14,17-23,26-32 (three agent functions); app/src/sample_orchestrator/orchestrator.py:11-15 (AGENTS list) and orchestration loop uses them (line 30-33). | none |
| The orchestrator invokes the agents in sequence, ID verification first, then risk assessment, then account opening, with each agent's run completing before the next one starts | met | - | app/src/sample_orchestrator/orchestrator.py:30-33 (for loop over AGENTS) and line 32 (await agent_fn(app_doc)). | none |
| After each agent step, the orchestrator updates the application document's state in Azure DocumentDB atomically | met | - | app/src/sample_orchestrator/orchestrator.py:41-50 (async with await client.start_session(); start_transaction(); coll.find_one_and_update(..., session=session)). | none |
| Each state transition is logged (previous state, the new state and the agent that ran) | met | - | app/src/sample_orchestrator/orchestrator.py:52-53 (print with from_state, new_state and agent_name) and history append in the same transaction (line 46). | none |
| The connection string and model credentials come from environment variables; none appear in the repository | met | - | app/.env.example:1-5 (DOCUMENTDB_URI placeholder); app/src/sample_orchestrator/db.py:10-16 (reads DOCUMENTDB_URI from environment). No secret is committed in repo files. | none |
| A `.env.example` lists every setting with placeholder values | met | - | app/.env.example:1-7 (DOCUMENTDB_URI and DOCUMENTDB_DB and OPENAI_API_KEY placeholders). | none |
| One database client is created and reused across requests | met | - | app/src/sample_orchestrator/db.py:7-17 (_client singleton and get_client() that returns AsyncIOMotorClient instance). | none |
| A seed script loads sample data and creates the index, and can be run twice without duplicating data | met | - | app/scripts/seed.py:21-22 uses coll.replace_one(..., upsert=True) for idempotent upsert; scripts/create_indexes.py and scripts/create_indexes.py uses create_index which is idempotent (and was used successfully). | none |
| Dependencies are pinned in `requirements.txt` | met | - | app/requirements.txt:1-10 (explicit pinned versions, e.g. beanie==1.25.0, motor==3.1.1). | none |
| Unit tests run without a live cluster | met | - | app/tests/test_orchestrator.py uses monkeypatch/fakes; pytest run recorded a passing test (events.jsonl run_command shows '1 passed'). | none |
| The README covers what the sample shows, prerequisites, setup, run, and clean-up | met | - | app/README.md:1-27 (What it shows, Prerequisites, Quickstart) and lines 29-37 (Tests, Security, Cleanup). | none |

