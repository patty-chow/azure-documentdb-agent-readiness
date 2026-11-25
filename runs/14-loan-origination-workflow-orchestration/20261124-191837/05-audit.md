# 5. Best-practice audit: 14-loan-origination-workflow-orchestration

**Verdict: pass_with_findings** (5 followed, 4 not assessable, 5 violated, 3 not applicable)

The sample implements the core feature requested: Beanie models for loan applications, a LangChain-style orchestrator that advances application state, atomic state updates via a single find_one_and_update filtered on the expected state, and a transition log with timestamps. The repository contains runnable scripts, pinned dependencies, an idempotent seed, and a .env.example with placeholders. Shortcomings: no applicant-communication specialist agent, unbounded transitions array (no cap or separate history collection), no index on applicant.ssn_last4 (used by the sample runner), tests that call init_beanie and therefore require a live cluster (contrary to the gallery checklist asking for offline unit tests), missing infrastructure-as-code for the cluster, and several operational best-practice items (retry/backoff, optimistic version field) are not implemented. Some builder decisions assumed MCP/mgmt tools would run; a documentdb_create_index call was attempted but failed because management tools are opt-in in this environment. Where the run-time environment or skills supply authoritative guidance, the app sometimes followed it (singleton client, secret-from-env, atomic update). Where guidance contradicted prior MongoDB assumptions (prefer AsyncMongoClient over Motor in new guidance), the sample used Motor, which is a mismatch with the installed skills' preferred driver guidance. See detailed findings below.

## Review of the builder's decisions

| Decision | What was decided | Reason came from | Assessment | Comment |
|---|---|---|---|---|
| D001 | I approved the build with readiness 'ready_with_gaps' | operator | sound | Approval decision recorded by operator; supported by the run's readiness and build events. |
| D002 | I chose Python 3.13 as the language/runtime for the sample. | readiness_report | sound | Choosing Python 3.13 is consistent with the environment and the code (the repo is Python). Events show the runtime choice and files created accordingly. |
| D003 | I chose to read the connection string from the DOCUMENTDB_URI environment variable at runtime. | readiness_report | sound | Reading DOCUMENTDB_URI from environment is implemented (app/src/db.py) and matches readiness guidance. |
| D004 | I chose Beanie (Beanie + Motor + Pydantic) for the data model and ODM. | prompt | sound | Beanie was requested in the prompt and the sample uses Beanie models (app/src/models.py). |
| D005 | I chose to use a single find_one_and_update that filters on the expected current_state and $pushes the transition record atomically. | readiness_report | sound | The builder intended a find_one_and_update atomic update; this is implemented in app/src/orchestrator.py:62-66. |
| D006 | I chose to implement deterministic/stub agents by default and allow optional real LLM usage if OPENAI_API_KEY is set in the environment. | model_default | sound | The decision to use deterministic stub agents by default is reflected in code (app/src/agents.py defines StubLLM) and in README; reason_source is 'model_default' but the code implements the stated behavior. |
| D007 | I chose to create a collection index on current_state using the documentdb MCP server's documentdb_create_index tool (connection_profile 'default'). | readiness_report | questionable | The decision chose to use the documentdb MCP server's documentdb_create_index tool. The events show a documentdb_create_index call was attempted (events.jsonl) but it failed with 'Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true to opt in.' So the chosen verification path did not succeed in this environment. |
| D008 | I chose to pin explicit dependency versions in requirements.txt to improve reproducibility. | model_default | sound | Pinning dependencies is implemented in app/requirements.txt; events show attempts to install and subsequent version adjustments. |
| D009 | I chose to update requirements to use beanie==1.21.0 because pip reported 1.21.1 wasn't available but 1.21.0 is. | tool_result | sound | Changing beanie to 1.21.0 was taken after pip reported 1.21.1 unavailable; events show the pip failure and the requirements write. |
| D010 | I chose to update requirements to use langchain==0.0.341 because pip reported 0.0.375 wasn't available but 0.0.341 is listed. | tool_result | sound | Changing langchain to an available version was supported by the pip output in events.jsonl and requirements.txt updates. |
| D011 | I approved the build with readiness 'ready_with_gaps' | operator | sound | Duplicate approval record consistent with earlier D001; no conflicting evidence found. |
| D012 | I chose Python (use python 3.13 runtime available via 'python' in the environment). | readiness_report | sound | Repeated choice of Python in later log; consistent with repository contents. |
| D013 | I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at run time. | prompt | sound | Reiteration of reading connection string from environment; code matches this decision (app/src/db.py). |
| D014 | I chose to implement deterministic stub 'specialist agents' by default and make real LLM provider optional if OPENAI_API_KEY is set. | readiness_report | sound | Recorded choice to use stub agents by default; code implements StubLLM and conditional optional real LLM path, so this decision is supported by the repository. |
| D015 | I chose Beanie for document models and motor for raw atomic find_one_and_update operations (Beanie models will be used but atomic transitions will call the underlying motor collection). | prompt | questionable | Decision says 'Beanie + motor for raw atomic find_one_and_update operations' and the code does use Motor. However the installed connection skill recommends preferring PyMongo's AsyncMongoClient for newer async code. The choice is implemented but contradicts the skill guidance; mark as questionable because the builder knowingly chose Motor rather than the skill's recommended driver. |

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
| Known to the model, no public source, not on the checklist | 3 | Agents will act on it from memory. Decide whether it holds for this service, then document it either way. |
| On the checklist and found by open discovery | 14 | Public and discoverable. |

#### Known to the model, no public source, not on the checklist

| Topic | Description | What would help |
|---|---|---|
| Document shape | Design a loan-application document to contain id, current state, schema version, transitions, timestamps, etc. | A short 'Loan application document' example on the Azure DocumentDB docs stating recommended fields (application_id, current_state, schema_version, transitions[], created_at, updated_at) would make this public and confirm the pattern. |
| Optimistic concurrency | Implement optimistic concurrency control by including an expected state or version in update filters and retrying on mismatch. | A short guidance page in the agent kit describing the pattern (add integer version, increment on update, include version in filter, retry loop) would let agents implement it reliably. |
| Beanie model registration and indexes | When using Beanie or another ODM, register document models and create indexes at startup (e.g., call init_beanie / create_indexes). | A short manufacturer doc or agent-kit page confirming Beanie's init_beanie will create indexes on Indexed fields for Azure DocumentDB would remove ambiguity. |

#### On the checklist and found by open discovery

| Topic | Description | Sources |
|---|---|---|
| Singleton client reuse | Create one MongoClient per process and reuse it (singleton client pattern). | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| TLS enforcement | Require TLS for all connections (tls=true/ssl=true) and validate certificates in production. | [Quickstart: Use Azure DocumentDB with MongoDB driver for Python](https://learn.microsoft.com/azure/documentdb/quickstart-python#code-examples) |
| Least-privilege credentials | Use least-privilege credentials and prefer Microsoft Entra ID / RBAC or per-application users rather than admin/root credentials. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Atomic state transitions | Make state transitions atomic by filtering the update by the expected current state (or version) and applying $set and $push in a single findOneAndUpdate/updateOne. | [Updating data in Azure Cosmos DB for MongoDB](https://learn.microsoft.com/azure/cosmos-db/mongodb/tutorial-update) |
| Cap transitions | Avoid unbounded growth of in-document arrays (like transitions); cap the array or move history into a separate transitions collection. | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| Index for work discovery | Create an index to efficiently find work: at minimum create a compound index on state plus a scheduling or ordering field; make application_id unique if you query by it. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| TTL indexes | Use TTL (expireAfterSeconds) indexes for ephemeral documents or records you want auto-pruned. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Backoff and retries | Use exponential backoff with jitter for application-level retries on transient errors. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Monitoring and explain plans | Use explain("executionStats") to validate that queries use intended indexes. | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |
| Avoid storing secrets / prompts in DB | Avoid storing secrets, private keys, or raw LLM system prompts in the database. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Drive from change streams | Drive orchestration from change notifications (change streams) rather than naive polling when possible. | [Change streams in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/change-streams) |
| Project only required fields | Keep documents small and project only required fields in queries. | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |
| Prefer single-document updates | Prefer single-document atomic updates and avoid multi-document transactions unless necessary. | [Use Multi-document transactions in Azure Cosmos DB for MongoDB](https://learn.microsoft.com/azure/cosmos-db/mongodb/use-multi-document-transactions) |
| Driver choice (Motor vs AsyncMongoClient) | When using Python ODMs, prefer the supported async driver (PyMongo's AsyncMongoClient) and ensure startup registers models/indexes; Motor is deprecated for new async Python code and should be replaced where possible. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |

### How the app measures up

#### Violations

| Practice | Category | Evidence | Fix | Source |
|---|---|---|---|---|
| Avoid unbounded growth of in-document arrays (like transitions); cap the array or move history into a separate transitions collection. | data_modeling | app/src/models.py:22 defines transitions: List[Transition] = [] with no cap; app/src/orchestrator.py:62-66 pushes transitions with no slice/cap. | Change the atomic update to cap entries (example: use $push with $each and $slice) or store transitions in a separate collection. Minimal code fix: in _transition_atomic use {'$push': {'transitions': {'$each': [transition], '$slice': -100}}} to keep last 100 entries. | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| Create an index to efficiently find work: at minimum create a compound index on state plus a scheduling or ordering field; make application_id unique if you query by it. | indexing | app/src/models.py:20 declares current_state Indexed(str) (index implied). The sample runner queries by applicant.ssn_last4 (app/run_orchestrator.py:16) but there is no index on applicant.ssn_last4 declared; transitions.timestamp index not created programmatically. | Add an index on applicant.ssn_last4 (and/or create a unique application_id index). Example: in init_db or seed call coll.create_index([('applicant.ssn_last4',1)], name='idx_ssn_last4'). Also consider a compound index {current_state:1, next_action_at:1} if scheduling is added. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Use exponential backoff with jitter for application-level retries on transient errors. | retries_and_resilience | app/src/db.py creates an AsyncIOMotorClient without configuring retry/backoff strategies and orchestrator methods do not wrap DB calls with retry loops. | Add a retry wrapper with exponential backoff/jitter for transient errors (e.g., use tenacity or implement an async retry decorator) and make DB operations idempotent where retries may occur. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Keep documents small and project only required fields in queries. | queries | run_orchestrator.py:24-26 prints full document returned by coll.find_one and the orchestrator re-reads the whole document; queries fetch entire documents rather than projecting only required fields. | When listing pending work or reading only state consider projecting only necessary fields (e.g., coll.find_one({'_id': id}, projection={'current_state':1, 'applicant.name':1, 'applicant.ssn_last4':1})). | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |
| When using Python ODMs, prefer the supported async driver (PyMongo's AsyncMongoClient) and ensure startup registers models/indexes; Motor is deprecated for new async Python code and should be replaced where possible. | tooling_and_frameworks | app/src/db.py:3 instantiates AsyncIOMotorClient (Motor) rather than PyMongo's AsyncMongoClient; the documentdb-connection skill recommends preferring AsyncMongoClient. | Replace Motor with PyMongo's AsyncMongoClient usage (update get_client to instantiate AsyncMongoClient or follow the skill's example); or add a short comment explaining rationale for Motor if necessary. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |

#### Could not be assessed

| Practice | Category | What was searched and missing | Source |
|---|---|---|---|
| Use least-privilege credentials and prefer Microsoft Entra ID / RBAC or per-application users rather than admin/root credentials. | authentication_and_secrets | - | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Design a loan-application document to contain id, current state, schema version, transitions, timestamps, etc. | data_modeling | Searched for 'Beanie loan application model Azure DocumentDB' and 'loan application document schema Azure DocumentDB' (no authoritative single-page guidance found). | prior knowledge (no public address recorded) |
| Implement optimistic concurrency control by including an expected state or version in update filters and retrying on mismatch. | concurrency_and_transactions | Searches for 'Azure DocumentDB optimistic concurrency version field' returned no single canonical Microsoft page. | prior knowledge (no public address recorded) |
| When using Beanie or another ODM, register document models and create indexes at startup (e.g., call init_beanie / create_indexes). | provisioning_and_deployment | Searched for 'Beanie init_beanie create_indexes Azure DocumentDB' (no single official page returned). | prior knowledge (no public address recorded) |

#### Followed

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Create one MongoClient per process and reuse it (singleton client pattern). | connection_handling | app/src/db.py:12-22 (_client singleton and get_client()). | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Require TLS for all connections (tls=true/ssl=true) and validate certificates in production. | security | app/.env.example:2 includes tls=true and authMechanism=SCRAM-SHA-256; app/src/db.py reads DOCUMENTDB_URI from env (app/src/db.py:9). | [Quickstart: Use Azure DocumentDB with MongoDB driver for Python](https://learn.microsoft.com/azure/documentdb/quickstart-python#code-examples) |
| Make state transitions atomic by filtering the update by the expected current state (or version) and applying $set and $push in a single findOneAndUpdate/updateOne. | concurrency_and_transactions | app/src/orchestrator.py:62-66 uses find_one_and_update with {'_id': app_id, 'current_state': expected_state} and {$set: {'current_state': new_state}, $push: {'transitions': transition}}. | [Updating data in Azure Cosmos DB for MongoDB](https://learn.microsoft.com/azure/cosmos-db/mongodb/tutorial-update) |
| Avoid storing secrets, private keys, or raw LLM system prompts in the database. | security | No secrets or system prompts found in repository; the app uses environment variables for connection strings and OPENAI_API_KEY placeholder (app/.env.example). | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Prefer single-document atomic updates and avoid multi-document transactions unless necessary. | concurrency_and_transactions | app/src/orchestrator.py:62-66 uses a single-document find_one_and_update for transitions rather than a multi-document transaction. | [Use Multi-document transactions in Azure Cosmos DB for MongoDB](https://learn.microsoft.com/azure/cosmos-db/mongodb/use-multi-document-transactions) |

#### Not applicable

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Use TTL (expireAfterSeconds) indexes for ephemeral documents or records you want auto-pruned. | data_retention | Sample does not define ephemeral documents requiring TTL; no TTL index present. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Use explain("executionStats") to validate that queries use intended indexes. | monitoring_and_performance | No MCP or explain calls were executed in the sample run; the developer did not run explain to validate index usage. | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |
| Drive orchestration from change notifications (change streams) rather than naive polling when possible. | orchestration_pattern | The sample is a one-shot orchestrator executed via run_orchestrator.py and uses direct queries. Change streams are not used. | [Change streams in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/change-streams) |

### Reference requirements

11 of 19 met. The builder never saw these; this measures the starter prompt and the skills.

| Requirement | Status | Cause | Evidence | Smallest fix |
|---|---|---|---|---|
| Unit tests run without a live cluster. | not_met | prompt_silent | app/tests/test_model.py:5-10 calls await init_db([LoanApplication]) which requires DOCUMENTDB_URI and a reachable cluster, so the test needs a live service. | Change tests to not call init_db or to mock get_client; e.g., test pure-model construction using LoanApplication(...). Alternatively, provide a test fixture that mocks get_client or uses a local documentdb gateway image for CI. |
| Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. | not_met | prompt_silent | No Bicep/Terraform/ARM files present in the repo. The repo contains only app code and scripts. | Add an IaC example (Bicep or Terraform) that targets Microsoft.DocumentDB/mongoClusters (use the documentdb-azure-deployment skill's templates). |
| Specialist LangChain agents exist for underwriting, compliance checking and applicant communication, and the orchestrator delegates each step of the flow to the matching specialist agent. | partly_met | prompt_silent | app/src/agents.py defines UnderwritingAgent and ComplianceAgent (lines 34-49). Orchestrator construction uses UnderwritingAgent and ComplianceAgent (app/src/orchestrator.py:70-76). No applicant communication agent is defined or called. | Add an ApplicantCommunicationAgent stub in src/agents.py, accept it in Orchestrator.__init__, and call it where the sample should notify the applicant (e.g., after approved/rejected transitions). |
| A seed script loads sample data and creates the index, and can be run twice without duplicating data. | partly_met | prompt_silent | app/scripts/seed.py:24-30 uses coll.update_one with upsert and $setOnInsert to avoid duplication (idempotent). No explicit index creation is in scripts/seed.py; index on current_state is declared as Indexed in models.py but there is no explicit code creating transitions.timestamp index. | Add explicit idempotent index creation (programmatic) in seed.py or in init_db, e.g. create an index on 'applicant.ssn_last4' and 'transitions.timestamp' using create_index or ensure_indexes; or document that init_beanie will create model indexes and add a migration for transitions.timestamp. |
| The vector index dimensions match the embedding model's output. | not_checkable | - | Sample does not use embeddings or vector indexes; no vector index code to inspect. | none |
| The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. | not_checkable | - | No vector index usage in repository. | none |
| /search returns a clear error for an empty query and when the embedding call fails. | not_checkable | - | No /search endpoint in this sample. | none |
| Search results include the similarity score. | not_checkable | - | No search endpoint or vector search used. | none |
| A Beanie Document model in Python represents each loan application as a state-machine document in Azure DocumentDB, with a state field whose values are the workflow states (submitted, underwriting, compliance, approved/rejected). | met | - | app/src/models.py:19-23 (LoanApplication with current_state and transitions fields). | none |
| A Python LangChain orchestration pipeline loads an application's document, reads its current state and advances it step by step through submitted, underwriting and compliance to a final approved or rejected state, in that order, stopping once a final state is reached. | met | - | app/src/orchestrator.py:22-45 implements submitted→underwriting→compliance→approved/rejected flow and stops on final states. | none |
| Each specialist agent returns a result the orchestrator uses to choose the application's next state, including whether it finishes as approved or rejected. | met | - | app/src/agents.py:38-40 (UnderwritingAgent.decide) returns 'approve'/'reject'; app/src/orchestrator.py:31-36 and 39-44 uses decisions to choose next state. | none |
| Each state advance writes the new value of the state field to the application document atomically through Beanie (e.g. a single find_one_and_update with $set, or a session transaction when several documents change together). | met | - | app/src/orchestrator.py:62-66 uses coll.find_one_and_update with filter on {_id, current_state} and $set plus $push in a single call. | none |
| Every transition is logged with a timestamp taken at transition time (e.g. an entry holding the previous state, the new state and a UTC datetime, appended to a transitions list on the application document or emitted through a logger). | met | - | app/src/models.py:12-17 Transition schema (fields previous_state, new_state, agent, decision, timestamp = datetime.utcnow). app/src/orchestrator.py:54-60 constructs transition with timestamp datetime.utcnow and $pushes it to transitions. | none |
| The connection string and model credentials come from environment variables; none appear in the repository. | met | - | app/src/db.py:7-11 reads DOCUMENTDB_URI from environment; app/.env.example contains a placeholder (app/.env.example:2). No secrets in repo. | none |
| A .env.example lists every setting with placeholder values. | met | - | app/.env.example lists DOCUMENTDB_URI and OPENAI_API_KEY placeholders (app/.env.example:1-4). | none |
| One database client is created and reused across requests. | met | - | app/src/db.py:12-22 implements a module-level _client and async get_client() that instantiates AsyncIOMotorClient once. | none |
| Dependencies are pinned in requirements.txt. | met | - | app/requirements.txt pins exact versions (beanie==1.21.0, motor==3.1.1, pymongo==4.4.0, ...). | none |
| The README covers what the sample shows, prerequisites, setup, run, and clean-up. | met | - | app/README.md includes sections: What it shows, Prerequisites, Setup, Run the sample, Inspect the DB, Cleanup (README.md lines 3-29). | none |
| The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name. | met | - | app/README.md uses 'Azure DocumentDB' (README.md:3) and .env.example host uses the DocumentDB cluster host suffix. | none |

