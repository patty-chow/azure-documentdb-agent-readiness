# 5. Best-practice audit: 05-appointment-scheduling-assistant

**Verdict: pass_with_findings** (8 followed, 1 violated, 1 not applicable, 2 not assessable)

The sample implements the core functionality the starter prompt asked for: a single Node.js LangChain agent with per-user in-memory memory, tools that read provider slots and create/reschedule/cancel appointments in Azure DocumentDB, an idempotent seed script that creates slots and indexes, and demo verification scripts that were run against the live cluster. Main correctness and concurrency practices (atomic conditional updates and multi-document transactions) are implemented. Findings: (1) relative-time handling ('move it an hour later') is not implemented in application code — the sample relies on the LLM to produce a tool call; (2) retry/backoff and 429 handling are not implemented; (3) there are no unit tests that run offline (the provided verification uses a live cluster); (4) some operational items (auth alternatives like Microsoft Entra ID, cleanup steps, explicit retry/tls flags, and dependency pinning semantics) are documented only partially or not at all. Several of these are due to reasonable builder choices (kept the sample small) but the product team should address the documentation gaps so agents and future builders do not assume missing behavior.

## Review of the builder's decisions

| Decision | What was decided | Reason came from | Assessment | Comment |
|---|---|---|---|---|
| D001 | I approved the build with readiness 'ready_with_gaps' | operator | sound | Approval 'ready_with_gaps' is operative and consistent with the builder_report. Evidence: builder_report/status and events show build proceeded. |
| D002 | I chose Node.js (v24) with Express for the sample app and scripts. | prompt | sound | Choice of Node.js + Express is implemented (package.json & app/src/server.js). Reason: 'prompt' — matches the starter prompt. events.jsonl shows skill loads and build events for Node usage. |
| D003 | I approved the build with readiness 'ready_with_gaps' | operator | sound | Duplicate approval entry; consistent with build logs. |
| D004 | I chose Node.js (v24) with Express for the sample app. | prompt | sound | Choice reiteration of Node.js + Express, implemented in repository (app/src/server.js). |
| D005 | I chose OpenAI (OPENAI_API_KEY) as the LLM provider for the sample. | model_default | sound | The builder selected OpenAI as the LLM provider and wired OPENAI_API_KEY into app/src/agent.js (line 7). The reason_source is 'model_default' (a default choice). The events trace does not show an external constraint preventing other providers; the code matches the decision. |
| D006 | I chose in-memory LangChain ConversationBufferMemory for agent memory. | model_default | sound | In-memory BufferMemory was chosen and is implemented (app/src/agent.js lines 9-16). Reason_source is 'model_default'; this choice is visible in code and events do not contradict it. |
| D007 | I approved the build with readiness 'ready_with_gaps' | operator | sound | Duplicate approval entry; consistent with logs. |
| D008 | I chose Node.js with Express and TypeScript-free JavaScript (Node 24) for the sample agent. | prompt | sound | Choice of JavaScript (non-TypeScript) implementation is reflected in the codebase (no TypeScript files). |
| D009 | I chose OpenAI (via OPENAI_API_KEY) as the chat model provider for the LangChain agent. | model_default | sound | Duplicate/near-duplicate of D005; implemented in code (app/src/agent.js). |
| D010 | I chose in-memory BufferMemory for conversation memory in this sample. | model_default | sound | Duplicate/near-duplicate of D006; implemented in code. |
| D011 | I chose two collections: 'slots' and 'appointments' in database 'sample_healthcare_05' with the schema described in the prompt review assumptions. | model_default | sound | Choice of two collections 'slots' and 'appointments' is implemented (seed.js lines 8-9) and matches the data model in store.js. |
| D012 | I chose a compound index { providerId: 1, start: 1, status: 1 } on the slots collection. | model_default | sound | Choice to create the compound index { providerId:1, start:1, status:1 } is implemented in seed.js (line 12). events.jsonl shows documentdb-indexing skill was loaded earlier (events contain load_skill calls). |

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
| Found publicly, not on the checklist | 2 | Add it to the checklist, or check that the public guidance is what the team intends. |
| Known to the model, no public source, not on the checklist | 2 | Agents will act on it from memory. Decide whether it holds for this service, then document it either way. |
| On the checklist and found by open discovery | 8 | Public and discoverable. |

#### Found publicly, not on the checklist

| Topic | Description | Sources |
|---|---|---|
| Observability and monitoring | Instrument and trace booking and rescheduling flows (record latency, RU cost, success/failure) and surface slow queries and RU hotspots through diagnostic settings and Log Analytics alerts. | [documentdb-monitoring](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md) |
| Audit trail: transactions used | Use transactions for multi-document operations (appts + slots). | checklist only (no public address recorded) |

#### Known to the model, no public source, not on the checklist

| Topic | Description | What would help |
|---|---|---|
| Persist minimal identifiers for memory | Persist only minimal identifiers for agent conversational memory (conversationId, lastAppointmentId) and keep full conversational context ephemeral; encrypt persisted sensitive state at rest when required. | A short guidance page in the docs that states 'If you persist agent memory for appointment flows, store only identifiers (conversationId, lastAppointmentId), avoid full PII and encrypt persisted state.' |
| Overlapping slot checks | When rescheduling slot times, check for overlapping slots for the same provider using indexed queries and enforce application-level checks to prevent overlapping bookings because DB-level partial unique constraints on time ranges are not a general replacement. | A documented pattern page showing sample queries and index recommendations for detecting overlaps and guidance that DB-level partial unique constraints do not cover arbitrary time ranges. |

#### On the checklist and found by open discovery

| Topic | Description | Sources |
|---|---|---|
| Single shared client | Read DOCUMENTDB_URI from an environment variable and create a single shared MongoClient at process startup, reusing that client across modules instead of opening a new connection per request. | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Connection tuning & TLS | Tune MongoClient pool and timeout settings (maxPoolSize, minPoolSize, maxIdleTimeMS, serverSelectionTimeoutMS, socketTimeoutMS) based on your environment (serverless vs long-running) and expected concurrency. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Require TLS | Always require TLS on connections to Azure DocumentDB and do not disable certificate validation in production. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Retry on transient errors | Implement retries with exponential backoff for transient errors and rate-limit responses (handle 429/Retry-After), and enable the driver's retryReads/retryWrites where appropriate. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Atomic slot booking | Perform slot booking with an atomic conditional update (e.g., findOneAndUpdate or updateOne with filter { _id: slotId, status: 'available' } and check the returned/modified count) to detect conflicts instead of a separate read-then-write. | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Use transactions for multi-document invariants | Use multi-document transactions (session.withTransaction) when supported by the cluster's MongoDB API version to make related updates atomic; if transactions are unavailable, use a compensated pattern and detect partial failures. | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |
| Compound index for availability queries | Create a compound index that matches common availability queries (example: { providerId: 1, start: 1, status: 1 }) and make index creation idempotent in seed scripts. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Data modelling: separate slots and appointments | Model for access patterns: keep one slot document per slot and a separate appointments collection that references slotId so you can target atomic updates on slots without large document rewrites. | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |

### How the app measures up

#### Violations

| Practice | Category | Evidence | Fix | Source |
|---|---|---|---|---|
| Implement retries with exponential backoff for transient errors and rate-limit responses (handle 429/Retry-After), and enable the driver's retryReads/retryWrites where appropriate. | retries | app/src/store.js and app/src/db.js do not implement retry/backoff or 429 handling. Transactions are used but retries on transient transaction failures are not implemented. | Add retry/backoff wrappers around DB operations and enable driver retry options (retryReads/retryWrites) and respect 429 Retry-After. Smallest fix: wrap critical operations in a retryWithBackoff helper and call it from store.js. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |

#### Could not be assessed

| Practice | Category | What was searched and missing | Source |
|---|---|---|---|
| Persist only minimal identifiers for agent conversational memory (conversationId, lastAppointmentId) and keep full conversational context ephemeral; encrypt persisted sensitive state at rest when required. | data modeling / security | azure documentdb conversation memory persistence; azure documentdb agent memory persist conversation identifiers best practice | prior_knowledge_only (no public address recorded) |
| When rescheduling slot times, check for overlapping slots for the same provider using indexed queries and enforce application-level checks to prevent overlapping bookings because DB-level partial unique constraints on time ranges are not a general replacement. | data integrity / modeling | azure documentdb enforce non-overlapping time ranges unique constraint; documentdb prevent overlapping time ranges booking constraint | prior_knowledge_only (no public address recorded) |

#### Followed

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Read DOCUMENTDB_URI from an environment variable and create a single shared MongoClient at process startup, reusing that client across modules instead of opening a new connection per request. | connection handling | app/src/db.js lines 12-24 implement a singleton MongoClient and getDb() caches the db (lines 27-31). | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Tune MongoClient pool and timeout settings (maxPoolSize, minPoolSize, maxIdleTimeMS, serverSelectionTimeoutMS, socketTimeoutMS) based on your environment (serverless vs long-running) and expected concurrency. | connection handling | app/src/db.js sets maxPoolSize:10 and serverSelectionTimeoutMS:5000 (lines 17-21) but does not set retry options (retryReads/retryWrites) or socketTimeoutMS/maxIdleTimeMS explicitly. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Always require TLS on connections to Azure DocumentDB and do not disable certificate validation in production. | authentication and secrets | The sample expects a TLS-enabled SRV-style connection string in .env.example (app/.env.example line 2 contains '?ssl=true' in the example). The driver options do not explicitly toggle tls flags (app/src/db.js lines 17-21) but the example connection string includes TLS. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Perform slot booking with an atomic conditional update (e.g., findOneAndUpdate or updateOne with filter { _id: slotId, status: 'available' } and check the returned/modified count) to detect conflicts instead of a separate read-then-write. | data integrity / concurrency | app/src/store.js createAppointmentAtomic uses findOneAndUpdate with filter { _id: slotId, status: 'available' } inside a transaction (lines 23-27) and checks slot.value (line 29). | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Use multi-document transactions (session.withTransaction) when supported by the cluster's MongoDB API version to make related updates atomic; if transactions are unavailable, use a compensated pattern and detect partial failures. | transactions | app/src/store.js uses session.withTransaction for createAppointmentAtomic, rescheduleAppointmentAtomic and cancelAppointment (store.js lines 18-36, 72-94, 49-61). | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |
| Create a compound index that matches common availability queries (example: { providerId: 1, start: 1, status: 1 }) and make index creation idempotent in seed scripts. | indexing | app/src/seed.js creates the compound index on slots (line 12) and seed upserts documents (lines 37-39) making the seed idempotent. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Model for access patterns: keep one slot document per slot and a separate appointments collection that references slotId so you can target atomic updates on slots without large document rewrites. | data modeling | app/src/seed.js creates two collections 'slots' and 'appointments' (lines 8-9) and appointments reference slotId (seed.js line 46). store.js performs targeted slot updates and appointment updates (e.g., lines 23-36, 80-92). | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| Use transactions for multi-document operations (appts + slots). | audit trail | app/src/store.js uses client.startSession() and session.withTransaction in createAppointmentAtomic, rescheduleAppointmentAtomic and cancelAppointment (store.js lines 14-36, 66-96, 43-63). | checklist only (no public address recorded) |

#### Not applicable

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Instrument and trace booking and rescheduling flows (record latency, RU cost, success/failure) and surface slow queries and RU hotspots through diagnostic settings and Log Analytics alerts. | observability / ops | No instrumentation/diagnostic code or Log Analytics guidance is present in the sample repo; the sample is small and intended for demos. | [documentdb-monitoring](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md) |

### Reference requirements

10 of 20 met. The builder never saw these; this measures the starter prompt and the skills.

| Requirement | Status | Cause | Evidence | Smallest fix |
|---|---|---|---|---|
| /search returns a clear error for an empty query and when the embedding call fails. | not_met | prompt_silent | No /search endpoint is present in the sample; only /chat is implemented (app/src/server.js). | Add a /search endpoint and validate input: return 400 on empty query, attempt embedding call with try/catch and return 503 or 500 with a clear message if embeddings fail. |
| Unit tests run without a live cluster. | not_met | prompt_silent | There are no unit tests that mock the MongoDB driver; the project's 'test' script runs demo_seed_verify.js which exercises the real cluster (app/src/demo_seed_verify.js lines 4-12, 15-33). | Add unit tests that mock mongodb (e.g., with sinon or mongodb-memory-server) and CI jobs that run them without network access; or include a lightweight LLM shim for agent tests. |
| Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. | not_met | prompt_silent | No IaC (Bicep/Terraform/ARM) files are present in the repository. | Add a Bicep/ARM template snippet that deploys Microsoft.DocumentDB/mongoClusters or an example az documentdb mongocluster command as an optional artifact (documentdb-azure-deployment skill has recommended snippets). |
| The agent has agent memory that carries the conversation context across turns, so a follow-up such as "move it an hour later" is resolved against the appointment discussed earlier without the patient restating the provider, date or time. | partly_met | builder_error | app/src/agent.js lines 9-17 (per-user BufferMemory created) and lines 95-97 (tool result saved to memory). | Implement explicit relative-time parsing/rewriting step: after the model requests a reschedule with a relative expression, look up lastAppointment in memory, compute the target ISO time, call findAvailableSlots with that target time, and then call rescheduleAppointmentAtomic. Add a helper in agent.js that converts relative phrases to a Date using the saved appointment start time. |
| When a patient gives a relative time such as "an hour later", the agent computes the target time from the remembered appointment time and uses the availability tool to find a matching slot in Azure DocumentDB before rescheduling. | partly_met | builder_error | Memory is saved (app/src/agent.js lines 11-16 and lines 95-97) so prior appointment/tool results are retained in-memory, but there is no code that parses relative-user-times and converts them into a concrete slot search before calling rescheduleAppointmentAtomic. | Add a relative-time resolution step in agent.handleMessage that: (a) reads the last appointment from the user's BufferMemory, (b) parses the relative expression (e.g., 'an hour later') to compute a target ISO datetime, (c) calls tools.findAvailableSlots(providerId, targetISO, targetISO) to find a slot, then calls tools.rescheduleAppointment with that slotId. |
| Dependencies are pinned in `requirements.txt`. | partly_met | builder_error | This is a Node.js sample: package.json lists semver ranges (e.g. "mongodb": "^5.7.0", app/package.json lines 14-20) but package-lock.json is present (app/package-lock.json) which pins versions for installs. | Either list exact dependency versions in package.json or add a note in README indicating that package-lock.json is the authoritative pinned manifest and should be committed (already present). |
| The README covers what the sample shows, prerequisites, setup, run, and clean-up. | partly_met | builder_error | README.md documents what the sample shows, prerequisites and setup (app/README.md lines 3-14, 24-42) but does not include explicit clean-up steps for the created documents or how to remove seeded data/indexes. | Add a 'clean-up' section to README with commands to remove sample documents (e.g., a small script or 'mongo' delete commands) and a note about running seed/verify on non-production clusters only. |
| The vector index dimensions match the embedding model's output. | not_checkable | prompt_silent | No vector index is created in the sample; vector search is out of scope for this sample. | If vector search is required, document the embedding model and dimensions in .env.example/README and create the index with matching 'dimensions' in the seed script. |
| The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. | not_checkable | prompt_silent | No vector indexing or parameter guidance present in repo. | If vector search is added, include parameter choices in the README and a commented section in seed.js showing how to change lBuild/lSearch/maxDegree/dimensions for larger datasets. |
| Search results include the similarity score. | not_checkable | prompt_silent | Search functionality is not present in the codebase. | When implementing semantic search, return scores from the $search aggregation stage or vector search API and include them in the endpoint response. |
| A single Node.js agent built with LangChain lets a patient book and reschedule appointments through conversation, choosing which of its tools to call for each request. | met | - | app/src/agent.js lines 19-54 (tools defined) and lines 56-99 (handleMessage) wired to src/server.js /chat endpoint (app/src/server.js lines 9-15). | n/a |
| A LangChain tool queries provider availability slots from Azure DocumentDB each time the agent needs availability, reading the current slot documents through a MongoDB-compatible Node.js driver (e.g. the `mongodb` package). | met | - | app/src/agent.js tool 'findAvailableSlots' calls store.findAvailableSlots (app/src/store.js lines 3-9) which uses the MongoDB driver via getDb (app/src/db.js lines 15-31). | n/a |
| Provider availability is modelled as slot documents in Azure DocumentDB, each carrying a status that the booking and rescheduling tools change (e.g. available to booked). | met | - | app/src/seed.js constructs slot documents with fields start, end, status and metadata (lines 22-34). app/src/store.js operates on 'slots' documents and updates status (e.g., lines 23-27, 80-84). | n/a |
| A tool books an appointment by creating an appointment document in Azure DocumentDB for the chosen slot and updating that slot's status. | met | - | app/src/store.js createAppointmentAtomic uses session.withTransaction, findOneAndUpdate on slots to set status:'booked' (lines 22-27) and inserts an appointment document (lines 33-35). | n/a |
| A tool reschedules an existing appointment by updating slot status atomically (e.g. a single conditional update that claims the new slot only while it is still available, or a session `withTransaction` when the old slot, the new slot and the appointment document change together) and pointing the appointment document at the new slot. | met | - | app/src/store.js rescheduleAppointmentAtomic uses session.withTransaction, findOneAndUpdate on the target slot with filter { _id, status:'available' } (lines 80-85), frees the old slot (line 88) and updates the appointment (line 91). | n/a |
| The connection string and model credentials come from environment variables; none appear in the repository. | met | - | app/.env.example (lines 2–5) contains placeholders; app/src/db.js reads process.env.DOCUMENTDB_URI (line 5); app/src/agent.js reads process.env.OPENAI_API_KEY and OPENAI_MODEL (line 7). No secret values are committed. | n/a |
| A `.env.example` lists every setting with placeholder values. | met | - | app/.env.example lists DOCUMENTDB_URI, DATABASE_NAME, OPENAI_API_KEY, OPENAI_MODEL and PORT (app/.env.example lines 2-6). | n/a |
| One database client is created and reused across requests. | met | - | app/src/db.js implements a singleton pattern: getClient() caches client (lines 12-24) and getDb() reuses the db (lines 27-33). | n/a |
| A seed script loads sample data and creates the index, and can be run twice without duplicating data. | met | - | app/src/seed.js creates indexes (lines 11-14) and upserts slots and an appointment using updateOne with upsert:true (lines 37-39, 44-48), then updates the slot status (line 51). | n/a |
| The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name. | met | - | README.md title and text use 'DocumentDB'/'Azure DocumentDB' (app/README.md lines 1,3). No other product names are used in code comments or README. | n/a |

