# 5. Best-practice audit: 15-prescription-refill-agent

**Verdict: pass_with_findings** (4 followed, 6 violated)

The sample runs and demonstrates the required end-to-end refill flow against a reachable Azure DocumentDB cluster: it looks up prescriptions, evaluates eligibility, writes a refillRequest and persists simple agent memory so follow-ups resolve. The builder resolved the Beanie/Node mismatch by implementing the sample in Node.js with Mongoose and a small, rule-based agent; this is documented in README and recorded in decisions.jsonl. Most functional requirements from the prompt are present and were exercised against the live cluster during verification. Several gallery-quality and production best-practice items are missing or only partially implemented (atomic updates/transactions, projection to limit RU, TTL for memory, CI-friendly offline tests, a /search endpoint and search behavior). Those are not fatal for a demo but should be fixed before publishing the gallery sample.

## Review of the builder's decisions

| Decision | What was decided | Reason came from | Assessment | Comment |
|---|---|---|---|---|
| D001 | I approved the build with readiness 'ready_with_gaps' | operator | unverifiable | Decision D001 (approved build with readiness 'ready_with_gaps') appears in decisions.jsonl but there is no corresponding log_decision event in events.jsonl that records D001. The event trace contains other approval entries (D008) and many log_decision calls, but not D001; I could not verify the recorded evidence for D001 in events.jsonl. |
| D002 | I chose Node.js with Mongoose (a Node ODM) instead of Python+Beanie. | readiness_report | sound | D002 (chose Node.js with Mongoose instead of Python+Beanie) is supported by events.jsonl: a log_decision call recorded this choice and the codebase uses Mongoose (app/src/models/* and package.json). The readiness report noted the Beanie/Node mismatch and the implementation follows that decision (evidence events.jsonl entries at timestamp ~08:49:40 and source files). |
| D003 | I chose Mongoose (mongoose@7) as the ODM/driver for the Node.js sample. | model_default | sound | D003 (chose Mongoose) is recorded in events.jsonl and the code uses Mongoose (package.json and src/models). The reason_source field is 'model_default' (a choice), and the trace shows the change was performed (files created/overwritten). |
| D004 | I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime. | prompt | sound | D004 (read connection string from DOCUMENTDB_URI) is recorded in events.jsonl and implemented in app/src/db.js lines 4-8. The event trace includes a log_decision for D004 and the code reads the env var as stated. |
| D005 | I chose to use the existing DocumentDB cluster and not provision any Azure resources. | readiness_report | sound | D005 (use existing cluster and do not provision resources) is recorded in events.jsonl and matches the run policy and README. The build used the provided DOCUMENTDB_URI and did not attempt provisioning, consistent with the decision. |
| D006 | I chose a simple in-process conversation memory for this sample agent (keeps last medication mention per session). | model_default | wrong | D006 states 'I chose a simple in-process conversation memory', but the final code persists memory to a DB collection (app/src/models/AgentMemory.js and app/src/agent.js lines 68-72 use AgentMemory.findOneAndUpdate and AgentMemory.findOne). That contradicts D006; the later decision D011 documents the DB-backed memory choice and is the one actually implemented. |
| D007 | I chose to implement a small rule-based agent (with explicit tools) rather than a full LangChain dependency to keep the sample small, readable, and self-contained. | model_default | sound | D007 records the choice to implement a small rule-based agent rather than a full LangChain dependency. The repository contains a rule-based Agent (app/src/agent.js) and README documents the choice (README.md lines 12-14). events.jsonl records D007. |
| D008 | I approved the build with readiness 'ready_with_gaps' | operator | unverifiable | D008 (another approval entry) appears in decisions.jsonl but there is no explicit matching log_decision event for D008 in events.jsonl, so I could not verify the event trace for this exact decision id. |
| D009 | I chose Node.js with Mongoose ODM (JavaScript) instead of Python/Beanie. | readiness_report | sound | D009 duplicates the D002 decision (Node.js + Mongoose); events.jsonl contains a log_decision that recorded D009 and the codebase reflects the choice, so the decision is supported by the trace. |
| D010 | I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime. | prompt | sound | D010 (use env var for connection string) is logged and implemented (app/src/db.js reading DOCUMENTDB_URI). The event trace contains the corresponding log_decision entry. |
| D011 | I chose a DB-backed agent memory stored in collection 'agent_memory'. | model_default | sound | D011 (DB-backed agent memory in 'agent_memory' collection) is recorded in events.jsonl and implemented in code (app/src/models/AgentMemory.js and app/src/agent.js lines 44-72). The event trace includes the decision and file writes that create the model. |
| D012 | I chose to implement a small rule-based agent (no external LLM calls) as the default behavior; the code is structured so an LLM (OpenAI) can be plugged via env var OPENAI_API_KEY. | model_default | sound | D012 (rule-based agent default, pluggable to OpenAI) is recorded and matches the code (agent is rule-based and README documents how to plug an LLM). events.jsonl contains the log_decision for D012. |
| D013 | I chose to create the following indexes: prescriptions {patientId:1, active:1}, prescriptions {prescriptionId:1} unique, refillRequests {patientId:1, requestedAt:-1}. | readiness_report | sound | D013 (create indexes prescriptions {patientId:1, active:1}, prescriptionId unique, refillRequests {patientId:1, requestedAt:-1}) is recorded and present in app/scripts/seed.js lines 12-14; events.jsonl records the decision and seed was run successfully. |

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
| On the checklist, no public source found | 1 | Not public, or not written down. A documentation gap. |
| On the checklist, found only when searched for by name | 0 | Public but hard to find. A discoverability gap. |
| Found publicly, not on the checklist | 0 | Add it to the checklist, or check that the public guidance is what the team intends. |
| Known to the model, no public source, not on the checklist | 0 | Agents will act on it from memory. Decide whether it holds for this service, then document it either way. |
| On the checklist and found by open discovery | 9 | Public and discoverable. |

#### On the checklist, no public source found

| Topic | Searched | Description |
|---|---|---|
| Tests without live cluster | Searched the repo for test frameworks and in-memory DB usage; found only test-eligibility.js requiring a live connection. | Unit tests run without a live cluster (mocked or in-memory). |

#### On the checklist and found by open discovery

| Topic | Description | Sources |
|---|---|---|
| Singleton client reuse | Use a single process-wide MongoClient / Mongoose connection (singleton) and reuse it rather than creating a new client per request. | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| TLS and connection options | Always connect with TLS enabled (tls=true) and do not disable certificate verification in production; Azure DocumentDB requires TLS. | [Quickstart: Use Azure DocumentDB with MongoDB driver for Node.js](https://learn.microsoft.com/azure/documentdb/quickstart-nodejs#code-examples) |
| Connection pool tuning | Tune connection-pool parameters according to your environment: small pools for serverless, larger pools for long-running OLTP servers, and set sensible timeouts. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Limit projections | Limit returned fields (use projection) and keep documents small because request charge (RU) correlates with document size. | [Performance tips for Azure Cosmos DB and .NET SDK v2](https://learn.microsoft.com/azure/cosmos-db/performance-tips#throughput) |
| Seed idempotency | Make seed scripts idempotent (use upsert / create-if-not-exists) so they can be safely re-run. | repo seed script |
| Agent memory lifecycle | When designing an agent's persistent memory collection, plan for lifecycle (TTL or retention) and encryption, and avoid storing full PHI in cleartext agent memory. | [documentdb-local-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md) |
| Atomic create + decrement | When creating refillRequest docs and updating prescriptions, decrement refill counts and use single-partition transactions or application-level guarded updates to avoid lost updates. | [Group multiple operations in transactions in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/how-to-transactions) |
| Indexes for agent lookups | Use an explicit index on prescriptionId (unique) and patientId + drugName compound index to support fast lookups used by the agent. | repo scripts/seed.js |
| Use explain() during development | Use explain('executionStats') / the MCP tools to verify index usage and query plans and rework indexes accordingly. | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |

### How the app measures up

#### Violations

| Practice | Category | Evidence | Fix | Source |
|---|---|---|---|---|
| Limit returned fields (use projection) and keep documents small because request charge (RU) correlates with document size. | queries | app/src/agent.js lines 56-61 call Prescription.findOne(...) without projections, pulling all fields. | Return only needed fields (e.g., drugName, daysSupply, refillCount, lastFilledAt) in the find/query; e.g. Prescription.findOne(query, { drugName:1, daysSupply:1, refillCount:1, lastFilledAt:1 }) | [Performance tips for Azure Cosmos DB and .NET SDK v2](https://learn.microsoft.com/azure/cosmos-db/performance-tips#throughput) |
| When designing an agent's persistent memory collection, plan for lifecycle (TTL or retention) and encryption, and avoid storing full PHI in cleartext agent memory. | privacy | app/src/models/AgentMemory.js lines 3-6 define lastMedication and updatedAt but do not create a TTL index or document retention policy. | Add a TTL index on updatedAt (and document retention guidance) and avoid storing full PHI; store only a canonical drug id where possible. Example: AgentMemory.collection.createIndex({ updatedAt: 1 }, { expireAfterSeconds: 60*60*24 }) and document retention policy in README. | [documentdb-local-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md) |
| When creating refillRequest docs and updating prescriptions, decrement refill counts and use single-partition transactions or application-level guarded updates to avoid lost updates. | data_modeling | app/src/agent.js lines 84-96 create the RefillRequest (rr.save()) and then decrement prescription.refillCount and prescription.save() without a transaction or guarded single-update. | Perform an atomic guarded update or a single-partition transaction: use findOneAndUpdate with a conditional filter (e.g., { prescriptionId, refillCount: { $gt: 0 } }) and $inc on refillCount, or start a session and run both operations in a transaction with patientId as the partition key. | [Group multiple operations in transactions in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/how-to-transactions) |
| Use an explicit index on prescriptionId (unique) and patientId + drugName compound index to support fast lookups used by the agent. | indexing | app/scripts/seed.js lines 12-14 create prescription indexes ({ patientId:1, active:1 } and unique prescriptionId) but do not create a compound patientId+drugName index which would speed lookups by patient+drug. | Create an additional compound index: Prescription.collection.createIndex({ patientId:1, drugName:1 }) (or patientId:1, drugName:1, nextRefillDate:-1 if sorting by nextRefillDate is required). | repo scripts/seed.js |
| Use explain('executionStats') / the MCP tools to verify index usage and query plans and rework indexes accordingly. | operations | No calls to explain() or MCP explain_operation are present in the repository and the seed/test tools do not capture explain output; events.jsonl shows the query-optimizer skill was available but not used to run explain() against the created queries. | Add a test/CI script that runs explain('executionStats') for the agent's critical queries (prescription lookup, eligibility filters) and stores or prints the plan and key metrics. | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |
| Unit tests run without a live cluster (mocked or in-memory). | testing | scripts/test-eligibility.js (scripts/test-eligibility.js lines 1-8) connects to the live DB; no mock-based test suite is present. | Add unit tests using an in-memory MongoDB (mongodb-memory-server) or mock Mongoose models; update CI instructions and README to show how to run tests offline. | [Quickstart docs and local-dev guidance](https://learn.microsoft.com/azure/documentdb/tutorial-nodejs-mongoose#prerequisites) |

#### Followed

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Use a single process-wide MongoClient / Mongoose connection (singleton) and reuse it rather than creating a new client per request. | driver | app/src/db.js lines 23-30 implement isConnected and reuse mongoose.connection. | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Always connect with TLS enabled (tls=true) and do not disable certificate verification in production; Azure DocumentDB requires TLS. | connection | app/.env.example line 2 includes tls=true in the example URI and app/src/db.js reads DOCUMENTDB_URI (app/src/db.js line 4). | [Quickstart: Use Azure DocumentDB with MongoDB driver for Node.js](https://learn.microsoft.com/azure/documentdb/quickstart-nodejs#code-examples) |
| Tune connection-pool parameters according to your environment: small pools for serverless, larger pools for long-running OLTP servers, and set sensible timeouts. | connection | app/src/db.js lines 11-21 set maxPoolSize, minPoolSize, connectTimeoutMS, socketTimeoutMS and serverSelectionTimeoutMS. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Make seed scripts idempotent (use upsert / create-if-not-exists) so they can be safely re-run. | development | app/scripts/seed.js lines 50-52 use updateOne(..., { upsert: true }) (or insert-if-not-exists in alternate seed) to avoid duplicates. | repo seed script |

### Reference requirements

9 of 19 met. The builder never saw these; this measures the starter prompt and the skills.

| Requirement | Status | Cause | Evidence | Smallest fix |
|---|---|---|---|---|
| /search returns a clear error for an empty query and when the embedding call fails. | not_met | prompt_silent | No /search endpoint exists in app/src/index.js; only POST /chat is implemented (app/src/index.js lines 11-16). | Add an explicit /search API that validates the input and returns clear, documented error codes for empty queries and embedding failures (or document that the sample does not include embedding-based search). |
| Search results include the similarity score. | not_met | prompt_silent | No search endpoint or embedding-based search present in the codebase. | If adding embedding-based search, return similarity score in the API response and document the format in README and the API contract. |
| Unit tests run without a live cluster. | not_met | prompt_silent | scripts/test-eligibility.js connects to the real DB using connect() (scripts/test-eligibility.js lines 1-7) and is not a mocked unit test. No mock-based unit tests present. | Add unit tests using an in-memory MongoDB (mongodb-memory-server) or mock the Mongoose models so tests run offline; add test instructions to README. |
| Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. | not_met | prompt_silent | No IaC (Bicep/ARM/Terraform) files are present in the repository. The README instructs users to use an existing cluster. | If the gallery wants to include IaC, add a Bicep/ARM/Terraform snippet (Microsoft.DocumentDB/mongoClusters) and sample parameters describing tier, storage and region. Otherwise document explicitly that the sample uses an existing cluster and show how to provision one if desired. |
| A single Node.js LangChain agent, built with Beanie ODM — handles the patient's refill request conversationally and decides which of its tools to call as the conversation proceeds. | partly_met | builder_error | app/src/agent.js lines 10-18 (Agent class present) and README.md line 13 (rule-based agent), but Beanie was not used and LangChain was not integrated. | Either change the starter prompt to allow a Node.js ODM (Mongoose) or run the sample in Python with Beanie. For repository-level fix: update the README and starter prompt to request 'an agent implemented in Node.js using Mongoose (or a Node ODM)' instead of Beanie. |
| A tool looks up the patient's active prescriptions in Azure DocumentDB through Beanie ODM (e.g. by the patient's identifier and whether the prescription is active) and returns them to the agent. | partly_met | builder_error | app/src/agent.js lines 56-61 perform Prescription.findOne({ patientId, active: true, drugName: ... }). This performs the lookup, but it uses Mongoose (Node) not Beanie (Python). | If Beanie must be used, reimplement the data-access tool in Python; otherwise change the prompt to allow Node.js + Mongoose and note this substitution in the sample README (already done). |
| A tool creates a refill request document in Azure DocumentDB through Beanie ODM for the prescription being refilled. | partly_met | builder_error | app/src/agent.js lines 85-92 create a RefillRequest and call rr.save(); implemented via Mongoose, not Beanie. | Either implement the write with Beanie (Python) or accept Node+Mongoose in the prompt. For atomicity, prefer performing the create + decrement inside a transaction or using an atomic guarded update (see next requirement fix). |
| The README covers what the sample shows, prerequisites, setup, run, and clean-up. | partly_met | prompt_silent | README.md contains what the sample shows and Quickstart setup/run (README.md lines 15-25 and lines 27-34) but lacks explicit clean-up instructions. | Add a 'clean-up' section to README that shows how to remove created documents/collections or guidance to drop the sample database 'sample_healthcare_15' with a CLI command. |
| The vector index dimensions match the embedding model's output. | not_checkable | could_not_determine | The sample does not create or use any vector indexes or embeddings; no vector-index code present. | If embeddings are added, include a README section that states the embedding model and its dimensionality and create the vector index with the matching dimension. |
| The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. | not_checkable | could_not_determine | No vector indexes present in the repository; vector-index guidance absent. | If vector search will be part of the sample, add an index creation script and README notes that explain the sample's chosen index type/params and how to retune them. |
| A tool checks a prescription's refill eligibility from its days supply remaining and its refill count and returns the result to the agent. | met | - | app/src/agent.js lines 74-78 compute daysRemaining and eligible and lines 80-82 return the ineligible message. | - |
| Agent memory keeps context across turns so that a follow-up such as 'refill my blood pressure medication' resolves to the patient's prescription without the patient naming the drug again. | met | - | app/src/agent.js lines 42-47 (check AgentMemory.findOne) and 68-72 (findOneAndUpdate to persist lastMedication). Model: app/src/models/AgentMemory.js lines 3-6. | - |
| The agent completes a refill by using these tools together: it looks up the prescription, checks its eligibility, and creates the refill request document when the prescription is eligible. | met | - | app/src/agent.js lines 56-96 show the flow: lookup, eligibility check, create refillRequest, decrement refillCount. | - |
| The connection string and model credentials come from environment variables; none appear in the repository. | met | - | app/src/db.js lines 4-8 read process.env.DOCUMENTDB_URI; app/.env.example lists a placeholder DOCUMENTDB_URI (app/.env.example line 2). | - |
| A .env.example lists every setting with placeholder values. | met | - | app/.env.example lines 2-5 list DOCUMENTDB_URI, PORT and OPENAI_API_KEY placeholders. | - |
| One database client is created and reused across requests. | met | - | app/src/db.js lines 23-30 implement an isConnected guard and return mongoose.connection, so connect() reuses the same connection pool. | - |
| A seed script loads sample data and creates the index, and can be run twice without duplicating data. | met | - | app/scripts/seed.js lines 12-14 create indexes; lines 50-52 perform updateOne(..., { upsert: true }) or (in alternate seed file) use findOne/create guard — the seed is idempotent. | - |
| Dependencies are pinned in requirements.txt. | met | - | This is a Node.js project; it includes package-lock.json (app/package-lock.json) which records exact resolved dependency versions for reproducible installs. | - |
| The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name. | met | - | README.md line 1 and other places consistently use 'Azure DocumentDB'. | - |

