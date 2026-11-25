# 5. Best-practice audit: 10-expense-report-auto-categorizer

**Verdict: pass_with_findings** (10 followed, 2 not assessable, 3 not applicable, 3 violated)

The sample implements the requested Python LangChain + Beanie agent: it reads submitted reports, applies an LLM (when OPENAI_API_KEY is present) or a deterministic fallback, applies session memory across a run, flags policy violations, and writes enriched reports back to Azure DocumentDB. The repo includes an idempotent seeder, index-creation script, .env.example, and a README. Key operational best-practice gaps remain (atomic idempotent processing, vector/index guidance left intentionally out, connection-pool tuning, tests that run offline, and an IaC example). See requirement_results and checks for line-level evidence and the smallest-fix recommendations to make the sample gallery-ready.

Notes about environment: the build used the provided live cluster and MCP tools according to the build report. The sample was executed in deterministic demo mode (no LLM key), and the AI path was not exercised in this run because OPENAI_API_KEY was not provided.

## Review of the builder's decisions

| Decision | What was decided | Reason came from | Assessment | Comment |
|---|---|---|---|---|
| D001 | I approved the build with readiness 'ready_with_gaps' | operator | sound | Operator approval is an operator-level choice and the decisions.jsonl entry records it. The events log shows the build proceeded after approval. |
| D002 | I chose Python 3.11 as the target runtime for the sample (developed to be compatible with 3.10–3.11). | prompt | sound | Choosing Python 3.11 is a reasonable target; README documents Python 3.10+ and the code runs in the environment. No contradiction found in the repo. |
| D003 | I chose async Motor + Beanie ODM (Beanie + Motor + PyMongo stack). | prompt | sound | The code uses Motor + Beanie (app/src/db.py lines 2-19), matching the decision. |
| D004 | I chose not to create vector indexes in this sample and instead provide a simple rule-based fallback for categorization when LLM keys are not provided. | readiness_report | sound | The repo intentionally omits vector indexes and documents that choice in README (app/README.md line 38); this matches the decision to avoid creating vector indexes without selecting embedding model/dimension. |
| D005 | I chose to make OPENAI_API_KEY optional and implement a deterministic rule-based fallback categorizer if an API key is not present. | model_default | sound | OPENAI_API_KEY is optional and the sample implements a deterministic fallback (--no-ai). Code checks env and CLI flags (app/main.py lines 16-20; app/src/processor.py lines 27/57). |
| D006 | I chose to create only conventional B-tree indexes (status, submitter.email) and not create any vector or textSearch indexes in this sample. | readiness_report | sound | Only B-tree indexes were created via app/src/indexes.py lines 10-12; this matches the stated decision. |
| D007 | I chose to keep agent memory in-process (LangChain ConversationBufferMemory) but also persist categorization decisions per submitter in a 'decisions' collection for cross-session consistency. | model_default | questionable | The decision states both in-process memory and persisted per-submitters in a 'decisions' collection. The implementation includes an in-process SessionMemory (app/src/processor.py lines 9-18) but does not persist decisions to a DB collection. The trace (events.jsonl) shows skills were loaded but no DB collection named 'decisions' exists in the code; the persistence part of the decision was not implemented. |
| D008 | I chose to pin Pydantic to v1.10.12 to match Beanie's expectations (Beanie 1.19.1 requires pydantic v1). | tool_result | questionable | D008 describes pinning Pydantic to v1.10.12 due to Beanie expectations. The repo constraints pydantic to v1 (app/requirements.txt line 4 pydantic>=1.10,<2) rather than the exact micro-version claimed; the intent is followed but the exact pin in the decision is not reflected as a strict == pin. |
| D009 | I chose to update Indexed annotations to include the type argument (e.g., Indexed(str, unique=True)) to conform to Beanie's expected signature under pydantic v1. | tool_result | questionable | D009 describes changing Indexed annotations to include type arguments; the models in app/src/models.py do not use Indexed heavily and no explicit Indexed(type, ...) edits are visible. The decision was defensive, but the code does not show the exact change (it isn't necessary here). |
| D010 | I chose to replace the deprecated Collection inner class with the Settings inner class per Beanie's error message and documentation. | tool_result | sound | Beanie Settings inner class is present in app/src/models.py lines 25-28; the code reflects the described change. |
| D011 | I chose to use dict-based filters (Report.find_one({'report_id': value})) in seed to avoid expression conversion issues with Beanie field wrappers in this environment. | tool_result | wrong | D011 states the seed uses dict-based filters to avoid expression conversion issues. The actual seed uses expression filters (app/src/seed.py line 40 uses Report.find_one(Report.report_id == r['report_id'])). The decision said they would use dict filters but the code remained an expression; the decision's implementation did not match the code. |
| D012 | I chose to avoid LangChain imports at module import time and to call the OpenAI SDK directly (lazy import) when OPENAI_API_KEY is present, to prevent dependency conflicts with Pydantic versions and to keep runtime simple. | tool_result | questionable | D012 says to avoid LangChain imports at module import time and call the OpenAI SDK directly. The code performs a lazy import of LangChain inside classify_item (app/src/processor.py lines 29-34) and uses ChatOpenAI (LangChain) there; it does not replace LangChain with direct OpenAI SDK calls. The lazy-import aspect is implemented, but the stated plan to call the OpenAI SDK directly was not fully implemented. |
| D013 | I chose to implement a small in-process ConversationBufferMemory substitute to avoid importing LangChain (which requires pydantic v2) and to keep the sample runnable. | tool_result | sound | D013's custom in-process memory substitute is implemented as SessionMemory in app/src/processor.py lines 9-18. |
| D014 | I chose to create B-tree indexes on {status:1} and {submitter.email:1} to support querying submitted reports and listing by submitter. | prompt | sound | D014's B-tree indexes on status and submitter/created_at were created by app/src/indexes.py lines 10-12 and are present in the build verification. |
| D015 | I approved the build with readiness 'ready_with_gaps' | operator | sound | A second approval record similar to D001; recorded as an operator decision and consistent with the run logs. |
| D016 | I chose Python 3.11 with Beanie (ODM), Motor (async Mongo driver) and LangChain for the agent. | prompt | sound | Duplicate of the Python/Beanie/Motor/LangChain choice; code aligns with this decision. |
| D017 | I chose to use constrained version ranges in requirements (e.g., beanie>=1.19,<2, motor>=3.1,<4, pymongo>=4.3,<5, langchain>=0.0.200,<1) rather than pinning exact micro versions. | model_default | sound | D017 chose constrained version ranges; app/requirements.txt shows constrained ranges rather than exact pins, matching the decision. |
| D018 | I chose Motor (motor.motor_asyncio.AsyncIOMotorClient) as the Mongo driver to use with Beanie in this sample. | model_default | sound | D018 chose Motor as the driver; app/src/db.py imports AsyncIOMotorClient and uses it (line 2 and 15), consistent with the decision. |
| D019 | I chose to implement agent memory as an in-session in-memory mapping (merchant -> category) and to include a deterministic rule-based fallback when OPENAI_API_KEY is not provided (so the demo can run without external AI). | model_default | sound | D019 describes session in-memory mapping and a deterministic fallback. The code provides SessionMemory (app/src/processor.py) and the CLI allows --no-ai/detects OPENAI_API_KEY (app/main.py lines 23-26), matching the decision. |
| D020 | I chose not to create vector indexes or use embeddings in this sample to avoid needing to pick and pin an embedding model and dimension (which was not specified), and because this sample focuses on LLM-based categorisation, not vector similarity search. | readiness_report | sound | D020 restates the choice not to create vector indexes; the README documents that choice (app/README.md line 38) and no vector indexes are created in code. |

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
| Known to the model, no public source, not on the checklist | 1 | Agents will act on it from memory. Decide whether it holds for this service, then document it either way. |
| On the checklist and found by open discovery | 17 | Public and discoverable. |

#### Known to the model, no public source, not on the checklist

| Topic | Description | What would help |
|---|---|---|
| Agent memory persistence | Persist agent/session memory or ephemeral classification decisions with versioning and, if ephemeral, a TTL; include deterministic-fallback flags. | A documentation page stating recommended patterns for persisting ephemeral agent memory (schema, TTL policy, version fields, and the deterministic fallback flag) so agents can implement durable or ephemeral memory safely. |

#### On the checklist and found by open discovery

| Topic | Description | Sources |
|---|---|---|
| Connection string from env | Read the DocumentDB MongoDB-compatible connection string from an environment variable (e.g., DOCUMENTDB_URI) at runtime and do not check it into source control or logs. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Client reuse | Create one MongoClient/driver client and reuse it (process-wide singleton). | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| TLS enforcement | Always connect with TLS enabled and do not disable certificate validation in production. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Least-privilege credentials | Use least-privilege credentials for applications (per-app users or Microsoft Entra ID + RBAC). | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Schema/versioning | Include a schema or classifier version (and model identifier/dimensions where vectors are used). | [documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md) |
| Embed small arrays | Embed small, bounded arrays inside the parent document when children are always read together. | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| Separate collection for unbounded children | Model frequently-updated or unbounded children as a separate collection with a reference and index on the parent id. | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| Compound indexes ESR | Design compound indexes matching common query shapes following ESR (Equality → Sort → Range). | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Sort fields in indexes | Ensure fields used in sort operations are included in an index to avoid in-memory sorts. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Partial index for rare fields | Use partial or sparse indexes for optional or rarely-populated fields (e.g., policy_violation:true). | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Index change planning | Plan index changes safely: inventory, test, hide, build/drop in low-traffic windows. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Idempotent processing | Implement idempotent processing using an atomic state change (e.g., findOneAndUpdate with a processing_status filter) to prevent double-processing. | [Transactions and optimistic concurrency control](https://learn.microsoft.com/azure/cosmos-db/database-transactions-optimistic-concurrency#optimistic-concurrency-control) |
| Avoid large multi-doc transactions | Avoid long-running, large multi-document transactions for classifier pipelines; prefer single-document atomic updates. | [Transactions and optimistic concurrency control](https://learn.microsoft.com/azure/cosmos-db/database-transactions-optimistic-concurrency#optimistic-concurrency-control) |
| Observability: slow queries | Log slow/high-latency queries, include timestamps and correlation ids, and use explain('executionStats') and MCP tools to inspect plans. | [documentdb-query-optimization](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimization/SKILL.md) |
| Secrets not persisted | Never persist API keys or plaintext credentials (LLM keys or DB admin passwords) in the database. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Idempotent seed scripts | Make seed and demo scripts idempotent (create-if-not-exists / upsert semantics). | [documentdb-local-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md) |
| Connection pool tuning | Tune connection pool parameters to your deployment type (small pools for serverless, larger for OLTP). | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |

### How the app measures up

#### Violations

| Practice | Category | Evidence | Fix | Source |
|---|---|---|---|---|
| Implement idempotent processing using an atomic state change (e.g., findOneAndUpdate with a processing_status filter) to prevent double-processing. | retries | app/src/processor.py lines 88-106: the code iterates Report.find(...) and later saves the modified report (report.save()), not using an atomic findOneAndUpdate or an optimistic concurrency check to claim processing work. | Change processing to atomically claim/lock a report (e.g., findOneAndUpdate filter status=='submitted' set status='processing' and only then process), or use optimistic concurrency/etag checks to avoid double-processing. | [Transactions and optimistic concurrency control](https://learn.microsoft.com/azure/cosmos-db/database-transactions-optimistic-concurrency#optimistic-concurrency-control) |
| Log slow/high-latency queries, include timestamps and correlation ids, and use explain('executionStats') and MCP tools to inspect plans. | observability | The sample uses print() for progress (app/src/processor.py lines 92-104) but does not log timestamps, correlation ids, nor call explain() to capture query plans. | Add structured logging, capture processing timestamps and correlation ids, and call explain('executionStats') on slow queries; expose a flag to emit explain() output during profiling runs. | [documentdb-query-optimization](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimization/SKILL.md) |
| Tune connection pool parameters to your deployment type (small pools for serverless, larger for OLTP). | connection | app/src/db.py line 15 constructs AsyncIOMotorClient(uri) without explicit pool tuning parameters (no maxPoolSize/minPoolSize or maxIdleTimeMS). | Set pool parameters on AsyncIOMotorClient (e.g., maxPoolSize for OLTP or small pool for serverless) and document different recommended values in README. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |

#### Could not be assessed

| Practice | Category | What was searched and missing | Source |
|---|---|---|---|
| Use least-privilege credentials for applications (per-app users or Microsoft Entra ID + RBAC). | security | - | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Persist agent/session memory or ephemeral classification decisions with versioning and, if ephemeral, a TTL; include deterministic-fallback flags. | data_modeling | searched for 'azure documentdb store agent memory TTL', 'documentdb persist agent memory TTL', 'deterministic_fallback_flag LLM' (no useful public result) | prior_knowledge (no public address recorded) |

#### Followed

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Read the DocumentDB MongoDB-compatible connection string from an environment variable (e.g., DOCUMENTDB_URI) at runtime and do not check it into source control or logs. | authentication_and_secrets | app/src/db.py line 10 reads DOCUMENTDB_URI; app/.env.example line 2 shows a placeholder SRV URI. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Create one MongoClient/driver client and reuse it (process-wide singleton). | connection | app/src/db.py lines 13-16 create and reuse a module-level AsyncIOMotorClient singleton (_client). | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Always connect with TLS enabled and do not disable certificate validation in production. | security | app/.env.example line 2 includes tls=true in the example URI; the client uses that URI (app/src/db.py line 15). | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Include a schema or classifier version (and model identifier/dimensions where vectors are used). | data_modeling | app/src/models.py line 21 defines schema_version on the Report document. No vector/model fields exist because vectors were not created. | [documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md) |
| Embed small, bounded arrays inside the parent document when children are always read together. | data_modeling | app/src/models.py line 20 stores items: List[Item] on the Report document (embedded array). | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| Design compound indexes matching common query shapes following ESR (Equality → Sort → Range). | indexing | app/src/indexes.py lines 10-12 create an index on status and a compound index on (submitter, created_at) which match the app's observed query shapes (find submitted reports and lists by submitter/date). | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Ensure fields used in sort operations are included in an index to avoid in-memory sorts. | indexing | The compound index includes created_at (app/src/indexes.py line 12) which would support sorting by created_at when listing reports by submitter/date. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Avoid long-running, large multi-document transactions for classifier pipelines; prefer single-document atomic updates. | queries | The sample updates each report document individually (app/src/processor.py lines 101-104) rather than running bulk multi-document transactions. | [Transactions and optimistic concurrency control](https://learn.microsoft.com/azure/cosmos-db/database-transactions-optimistic-concurrency#optimistic-concurrency-control) |
| Never persist API keys or plaintext credentials (LLM keys or DB admin passwords) in the database. | authentication_and_secrets | The code reads OPENAI_API_KEY from the environment (app/src/processor.py lines 27/57) and there is no code that writes secrets into DB documents. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Make seed and demo scripts idempotent (create-if-not-exists / upsert semantics). | provisioning | app/src/seed.py lines 39-60 perform a find_one by report_id and update existing documents, otherwise insert, so repeated runs are safe. | [documentdb-local-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md) |

#### Not applicable

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Model frequently-updated or unbounded children as a separate collection with a reference and index on the parent id. | data_modeling | The sample embeds items and the provided seed uses small arrays (3 reports, 2 items each); no evidence of unbounded arrays or frequent single-item updates. | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| Use partial or sparse indexes for optional or rarely-populated fields (e.g., policy_violation:true). | indexing | The sample does not create a partial index for policy_violation and the sample's query patterns do not require it. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Plan index changes safely: inventory, test, hide, build/drop in low-traffic windows. | provisioning | This sample is a small demo and contains no index migration tooling; the practice is operational guidance rather than a code-level behavior in this sample. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |

### Reference requirements

13 of 20 met. The builder never saw these; this measures the starter prompt and the skills.

| Requirement | Status | Cause | Evidence | Smallest fix |
|---|---|---|---|---|
| The vector index dimensions match the embedding model's output. | not_met | prompt_silent | No vector indexes were created (app/README.md line 38 states 'No vector indexes or embeddings were created'); app/src/indexes.py creates only B-tree indexes. | Ask the builder (in the starter prompt) to pick an embedding model and expose EMBEDDING_MODEL and EMBEDDING_DIM env settings, or add a skill rule that must provision vector indexes only when EMBEDDING_DIM is defined. |
| The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. | not_met | prompt_silent | app/README.md explicitly says vector indexes were not created (line 38); indexes.py only creates B-tree indexes (lines 10-12). | Add to the starter prompt or sample README a short 'Vectors & Indexes' section that documents EMBEDDING_MODEL, EMBEDDING_DIM and recommended index parameters and how to adjust them for larger datasets. |
| /search returns a clear error for an empty query and when the embedding call fails. | not_met | prompt_silent | No HTTP server or /search endpoint is implemented in the sample (no FastAPI/Flask app present). | If a search API is desired, add a small web handler (e.g., FastAPI) with a /search route that returns 400 for empty queries and returns a clear error payload when embedding or vector-query calls fail. |
| Search results include the similarity score. | not_met | prompt_silent | No search or embedding-based query code is implemented; app/src/indexes.py only creates B-tree indexes and processors do not call vector search. | Add similarity score in the search result model and return it from the vector-query path; require the embedding model/dim setting before enabling this feature. |
| Unit tests run without a live cluster. | not_met | prompt_silent | No unit test files are present; no test harness or mocked-driver fixtures were included in the repo. | Add unit tests that mock Motor/Beanie (e.g., use asynctest/pytest-asyncio with monkeypatch on AsyncIOMotorClient or use a local DocumentDB Gateway in CI), and document how to run them without a live cluster. |
| Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. | not_met | prompt_silent | No IaC files (Bicep/Terraform/ARM) are present in the repository; the run used an existing cluster per the run environment. | Add a minimal Bicep or Terraform example that uses Microsoft.DocumentDB/mongoClusters (or link to the AVM module) with parameters for tier/storage and a short snippet in README showing how to customize. |
| Dependencies are pinned in requirements.txt. | partly_met | prompt_silent | app/requirements.txt pins major/minor ranges (beanie>=1.19,<2, motor>=3.1,<4, pydantic>=1.10,<2, etc.) instead of exact micro-version pins (no ==micro.patch pins). | Pin exact micro versions (==) in requirements.txt, or include a constraints file with exact tested versions and a short README note about tested pins. |
| Implement the agent in Python with LangChain as a single agent that, for each submitted expense report, reads the report, categorises its line items, flags policy violations and writes the enriched report back. | met | - | app/src/processor.py lines 85-106 (process_submitted_reports iterates Report.find, classifies items and saves updated report); app/src/processor.py lines 27-56 (conditional LangChain call and JSON parsing). | - |
| Define Beanie ODM Document models for expense reports and use Beanie to read the submitted expense reports from Azure DocumentDB. | met | - | app/src/models.py lines 16-26 (Report Document model); app/src/db.py lines 18-19 (await init_beanie(...)); app/src/processor.py lines 88-90 (Report.find usage). | - |
| Each line item in a report receives a category from the LLM (e.g. OpenAI through LangChain) through an engineered prompt that supplies the company policy and the line item's details. | met | - | app/src/processor.py lines 36-44 (SystemMessage contains policy prompt and HumanMessage contains item fields); lines 46-56 parse the LLM response JSON. | - |
| Flag policy violations: each line item that breaks the company policy is marked as a violation in the agent's output for the report. | met | - | app/src/processor.py lines 50-54 (parse policy_violation and violation_reason from LLM response); app/src/processor.py lines 65-82 (fallback classifier sets policy_violation and reason). | - |
| Write the enriched report back to Azure DocumentDB through Beanie, with the category and violation flag for each line item attached to the report document. | met | - | app/src/processor.py lines 95-104 (update report.items[...] and await report.save()). | - |
| Provide an agent memory component that lives for a session spanning multiple reports and records the categorisation decisions the agent makes. | met | - | app/src/processor.py lines 9-18 (SessionMemory class) and line 86 (memory = SessionMemory()) used across the processing loop. | - |
| When categorising a line item, the agent consults the session memory and applies an earlier decision to a matching item, so the same kind of expense receives the same category across the reports processed in that session. | met | - | app/src/processor.py lines 21-26 (classify_item consults memory.get and returns stored category) and line 61 (memory.set after classification). | - |
| The connection string and model credentials come from environment variables; none appear in the repository. | met | - | app/src/db.py line 10 reads DOCUMENTDB_URI from environment; app/src/processor.py lines 27 and 57 check OPENAI_API_KEY; app/.env.example lists placeholders (line 2, line 4). No secrets are checked in. | - |
| A .env.example lists every setting with placeholder values. | met | - | app/.env.example lines 2-8 include DOCUMENTDB_URI, OPENAI_API_KEY, USE_AI, DOCUMENTDB_DB placeholders. | - |
| One database client is created and reused across requests. | met | - | app/src/db.py lines 6 and 13-16 implement a module-level singleton _client and reuse it in init_db/get_client. | - |
| A seed script loads sample data and creates the index, and can be run twice without duplicating data. | met | - | app/src/seed.py lines 35-60 perform idempotent upsert by report_id (find_one and update/insert). app/src/indexes.py lines 10-12 create indexes (create_index is idempotent). | - |
| The README covers what the sample shows, prerequisites, setup, run, and clean-up. | met | - | app/README.md includes sections 'What this sample shows', 'Prerequisites', 'Quick start' (setup/run), and 'Cleanup' (lines 1-41). | - |
| The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name. | met | - | app/README.md title and body use 'Azure DocumentDB' (line 1). app/.env.example uses a mongocluster host (mongocluster.cosmos.azure.com) which is appropriate for the service. | - |

