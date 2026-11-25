# 5. Best-practice audit: 03-portfolio-tracker-with-live-alerts

**Verdict: pass_with_findings** (11 followed, 5 violated, 7 not applicable, 3 not assessable)

The sample implements the requested Node.js + Mongoose portfolio service, change-stream watcher, webhook firing and aggregation endpoint and was exercised against the live cluster in this run. Core functional requirements are met and unit tests passed. Findings focus on operational hardening and a few checklist / best-practice gaps an author or the product team should address before publishing: resume-token durability, change-stream handler offload, aggregation allowDiskUse, more explicit retry/backoff and webhook idempotency guidance, and a small README improvement. Several practices the product team expects are discoverable (public docs or packaged skills) and were followed; a handful are only prior-knowledge beliefs or not implemented and should be documented or added to the agent kit so future agents and builders reliably do the right thing.

## Review of the builder's decisions

| Decision | What was decided | Reason came from | Assessment | Comment |
|---|---|---|---|---|
| D001 | I approved the build with readiness 'ready_with_gaps' | operator | sound | Operator-approved 'ready_with_gaps' is consistent with the build logs; approval is an operator action and evidence exists in the run. |
| D002 | I chose Node.js with Express and Mongoose (JavaScript) for the sample app. | prompt | sound | Choice of Node.js + Mongoose follows the prompt; events show the decision and the code implements that stack. |
| D003 | I chose Mongoose 7.x (latest 7.x release) for the sample, e.g., mongoose@7.6.0. | model_default | unverifiable | Mongoose 7.x was chosen with reason_source 'model_default'. The run loaded driver skills but no explicit documentation source proving a specific 7.x minor is required for the cluster—this is a model-default choice and should be documented (driver compatibility guidance). |
| D004 | I chose to read the connection string from process.env.DOCUMENTDB_URI at runtime. | readiness_report | sound | Reading DOCUMENTDB_URI from the environment was implemented (app/src/db.js); the decision matches the run environment guidance. |
| D005 | I chose to create indexes: {userId:1}, {userId:1, symbol:1} (compound), {symbol:1}, and {sector:1}. | prompt | sound | Index selection was recorded and implemented; create_indexes.js produced the intended indexes (events show indexes created). |
| D006 | I approved the build with readiness 'ready_with_gaps' | operator | sound | Duplicate approval entry; same rationale as D001. |
| D007 | I chose Node.js (v24) with Express and Mongoose (7.x) for the sample app. | prompt | sound | Duplicate/confirming decision to use Node.js v24 and Mongoose 7.x; matched by the runtime and package.json. |
| D008 | I chose to read the DocumentDB connection string from process.env.DOCUMENTDB_URI at runtime. | prompt | sound | Duplicate of the environment-reading decision; code reads DOCUMENTDB_URI at runtime. |
| D009 | I chose NOT to provision Azure resources in the sample and to include no provisioning commands to create clusters. | prompt | sound | Decision not to provision Azure resources is consistent with run policy. events.jsonl shows the run policy constraint and the decision to not create resources. |
| D010 | I chose not to implement sharding in this sample (single-shard collections). | model_default | sound | Decision not to shard for the sample is reasonable (small dataset, teaching sample). The code implements single-shard assumptions. |
| D011 | I chose a conservative sample policy: single HTTP POST attempt to the webhook and log failures (no durable retry queue). | model_default | questionable | Choosing a single POST (simple retry) is defensible for a sample, but the product's best practice (durable delivery/queue) differs; decision logged as 'model_default'—documenting the chosen minimal policy in README (which was done) is appropriate. |
| D012 | I chose to define indexes in the Mongoose schemas (schema.index) and run ensureIndexes on connection; also verify via the documentdb MCP server. | skill | sound | Indexes defined in Mongoose schemas were created and verified; the decision matches the code and index verification steps in events. |
| D013 | I chose to force the database name to 'sample_fintech_03' via mongoose.connect option dbName to ensure sample uses the required database. | prompt | sound | Forcing dbName to 'sample_fintech_03' was implemented in src/db.js; events show connect() used dbName and seed/index scripts operated on that database. |
| D014 | I chose to add and run a small script (scripts/create_indexes.js) that explicitly calls createIndexes() on the models to ensure indexes are created for verification. | skill | sound | Adding scripts/create_indexes.js and running it was recorded and verified; events show indexes created. |

Documentation gaps: 10 (see `doc-gaps.md`).

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
| Known to the model, no public source, not on the checklist | 4 | Agents will act on it from memory. Decide whether it holds for this service, then document it either way. |
| On the checklist and found by open discovery | 20 | Public and discoverable. |

#### Found publicly, not on the checklist

| Topic | Description | Sources |
|---|---|---|
| Audit trail: HTTP library choices | Audit: the code uses both axios and node-fetch for HTTP; the choice was not logged as a design decision. | code files (no public address recorded) |
| Audit trail: changeStream config | Audit: change stream uses fullDocument:updateLookup but the decision to use this option was not logged. | code files (no public address recorded) |

#### Known to the model, no public source, not on the checklist

| Topic | Description | What would help |
|---|---|---|
| Webhook idempotency | Make webhook delivery idempotent (include an event id or deduplication key and have the receiver deduplicate), or persist short-lived delivery records so retries don't cause duplicate effects. | A public guidance page stating: 'Include change _id and ruleId in webhook payload and persist delivery attempts to a webhook_deliveries collection for deduplication and observability.' |
| Mongoose .lean() | When using Mongoose in read-heavy code paths, prefer projection + .lean() to avoid constructing Mongoose documents when you only need plain objects for evaluation/aggregation. | A sentence in the Mongoose/Driver skill: 'For read-heavy evaluation paths (alerts) use .find(...).lean() to avoid Mongoose document construction overhead.' |
| Testing aggregation | Write unit tests for aggregation logic with realistic sample documents and include short integration tests that run aggregations against the live sample_fintech_03 database to validate correctness and index usage. | - |
| Precompute thresholds / cache lookups | Keep alert evaluation fast by precomputing thresholds and caching static lookups (instrument metadata like sector) with an in-memory TTL cache. | A short page in agent-kit: 'For alert watchers, cache alert rules/metadata in memory and refresh on change to keep evaluation O(1) per rule.' |

#### On the checklist and found by open discovery

| Topic | Description | Sources |
|---|---|---|
| Connection string env var | Load the cluster connection string from an environment variable (do not hard-code or commit it), avoid printing the full URI to logs, and use an example file (.env.example) or a secret store for developer onboarding. | [Quickstart: Connect Mongoose to Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/quickstart-nodejs-mongoose#create-the-project) |
| Connection tuning | Tune MongoDB driver connection options to your deployment: set sensible maxPoolSize/minPoolSize, serverSelectionTimeoutMS and socketTimeoutMS according to serverless vs long-running server patterns. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Client reuse | Use a single MongoClient / Mongoose connection (singleton) for the process and reuse it across requests. | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| TLS enforcement | Always require TLS when connecting to Azure DocumentDB; do not disable certificate verification in production. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Change stream fullDocument | When using change streams and you need the post-update document, open the stream with fullDocument: 'updateLookup' so handlers receive the current document on update events. | [Change streams in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/change-streams) |
| Resume tokens | Persist change-stream resume tokens durably and resume the stream with resumeAfter/startAtOperationTime to continue from the last processed event. | [Change streams in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/change-streams#resume-a-change-stream) |
| Short handlers | Keep change-stream handlers short and offload webhook delivery or expensive evaluation to background workers/queues. | [Change streams in Azure DocumentDB; Best practices for background jobs](https://learn.microsoft.com/azure/documentdb/change-streams) |
| Alert-rule indexing | Design alert-rule queries so they can be satisfied by indexes (e.g., lookup by userId + active + symbol); create appropriate compound indexes rather than scanning all rules. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Compound index ESR | Follow the ESR rule (Equality → Sort → Range) when creating compound indexes for queries and aggregation match stages. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Aggregation indexes | Create indexes to support aggregation match and group stages used by portfolio P&L and sector allocation (e.g., indexes on accountId, symbol, sector or a compound {accountId:1, symbol:1}). | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| allowDiskUse | When running potentially large aggregations, enable allowDiskUse: true and minimize projection/result shape to reduce data transferred over the wire. | [aggregate](https://learn.microsoft.com/documentdb/query/commands/aggregation/aggregate) |
| Retries and backoff | Implement retries with exponential backoff for transient connection/server-selection errors and rate-limited responses and cap retries with a dead-lettering approach for permanent failures. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Idempotent seeds | Make seed scripts idempotent by using upserts keyed on stable natural keys so seeds can be rerun safely. | scripts/seed.js<br>scripts/seed.js |
| Embedding vector model | Model and store embeddings as a fixed-length numeric array and record the embedding dimensionality and model metadata. | [documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md) |
| Vector index creation | Create a dedicated vector index (cosmosSearch) with explicit options that match your embedding model and scale. | [documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md) |
| Monitoring & slow queries | Enable diagnostic settings and capture slow-query logs to Log Analytics and alert on CPU/memory/connection saturation. | [documentdb-monitoring](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md) |
| Capacity sizing | Pick cluster throughput to cover peak workloads from change-stream consumers and heavy aggregations. | [documentdb-high-availability](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/high-availability/SKILL.md) |
| Backups | Rely on the platform's automatic backups and retention policy as part of DR planning. | [documentdb-high-availability](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/high-availability/SKILL.md) |
| Network isolation & Entra ID | Prefer Private Endpoint / firewall rules and Microsoft Entra ID + RBAC for auth and use CMK for encryption-at-rest when required. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Parallelizing change streams | When using change streams at scale, use the GetChangeStreamTokens command to obtain per-physical-shard resume tokens and run a watcher per token to parallelize load. | [Use MongoDB extension commands to manage data stored in Azure Cosmos DB for MongoDB](https://learn.microsoft.com/azure/cosmos-db/mongodb/custom-commands#parallelizing-change-streams) |

### How the app measures up

#### Violations

| Practice | Category | Evidence | Fix | Source |
|---|---|---|---|---|
| Persist change-stream resume tokens durably and resume the stream with resumeAfter/startAtOperationTime to continue from the last processed event. | change_streams | No code persists resume tokens. change stream is opened without resumeAfter/startAtOperationTime (app/src/worker/watch.js and app/src/alert_watcher.js show watch() calls but no token persistence). | Persist the last processed change._id (resume token) to a durable collection on every processed event and call Model.watch(..., { resumeAfter: token }) on restart; implement exponential backoff and safe resume failure handling. | [Change streams in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/change-streams#resume-a-change-stream) |
| Keep change-stream handlers short and offload webhook delivery or expensive evaluation to background workers/queues. | change_streams | app/src/worker/watch.js and app/src/alert_watcher.js perform synchronous HTTP requests (await axios.post or await sendWebhook) inside the change stream handler rather than enqueuing work. | Offload webhook delivery to a background worker or message queue; in the short term, perform non-blocking enqueue (e.g., write delivery requests to a 'deliveries' collection and process them with a separate worker) so the watch loop returns quickly. | [Change streams in Azure DocumentDB; Best practices for background jobs](https://learn.microsoft.com/azure/documentdb/change-streams) |
| Follow the ESR rule (Equality → Sort → Range) when creating compound indexes for queries and aggregation match stages. | indexing | Alert-rule queries use userId + active + symbol semantics; existing indexes include userId and userId+active but not a full { userId:1, active:1, symbol:1 } compound index to cover the common predicate, so some queries may still require extra work. (app/src/models/alertrule.js shows defined indexes.) | Add a compound index on { userId: 1, active: 1, symbol: 1 } to avoid scans when matching rules by userId, active and symbol. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| When running potentially large aggregations, enable allowDiskUse: true and minimize projection/result shape to reduce data transferred over the wire. | aggregation | Aggregations in app/src/app.js and scripts/aggregate_test.js call Position.aggregate(...) but do not pass the option { allowDiskUse: true } for large workloads. | Pass { allowDiskUse: true } to aggregate when running larger datasets or document this option in README and conditionally enable it when result size may exceed memory. | [aggregate](https://learn.microsoft.com/documentdb/query/commands/aggregation/aggregate) |
| Implement retries with exponential backoff for transient connection/server-selection errors and rate-limited responses and cap retries with a dead-lettering approach for permanent failures. | retries | The sample implements a single short retry for webhook delivery (app/src/worker/watch.js sendWebhook has one retry) but lacks a general exponential-backoff retry strategy for driver transient errors or 429 handling and does not record failed deliveries to a dead-letter store. | Add exponential-backoff retry helper for transient DB and webhook errors and persist failed webhooks to a 'dead-letter' collection after retry exhaustion. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |

#### Could not be assessed

| Practice | Category | What was searched and missing | Source |
|---|---|---|---|
| Make webhook delivery idempotent (include an event id or deduplication key and have the receiver deduplicate), or persist short-lived delivery records so retries don't cause duplicate effects. | webhooks | Azure DocumentDB webhook idempotent delivery (search returned no explicit guidance) | prior_knowledge (no public address recorded) |
| When using Mongoose in read-heavy code paths, prefer projection + .lean() to avoid constructing Mongoose documents when you only need plain objects for evaluation/aggregation. | mongoose | Mongoose .lean Azure DocumentDB guidance (search returned no direct doc) | prior_knowledge (no public address recorded) |
| Keep alert evaluation fast by precomputing thresholds and caching static lookups (instrument metadata like sector) with an in-memory TTL cache. | data_modeling | alert evaluation performance best practices (general search returned no Azure DocumentDB specific guidance) | prior_knowledge (no public address recorded) |

#### Followed

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Load the cluster connection string from an environment variable (do not hard-code or commit it), avoid printing the full URI to logs, and use an example file (.env.example) or a secret store for developer onboarding. | security | app/src/db.js lines 8-9 (const uri = process.env.DOCUMENTDB_URI), app/.env.example present. | [Quickstart: Connect Mongoose to Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/quickstart-nodejs-mongoose#create-the-project) |
| Tune MongoDB driver connection options to your deployment: set sensible maxPoolSize/minPoolSize, serverSelectionTimeoutMS and socketTimeoutMS according to serverless vs long-running server patterns. | connection | app/src/db.js lines ~12-18 sets maxPoolSize:50, minPoolSize:10, serverSelectionTimeoutMS:5000, socketTimeoutMS:30000. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Use a single MongoClient / Mongoose connection (singleton) for the process and reuse it across requests. | driver | app/src/db.js implements isConnected guard and returns the shared mongoose connection. | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Always require TLS when connecting to Azure DocumentDB; do not disable certificate verification in production. | security | app/src/db.js sets tls: true in mongoose options and README warns 'TLS is required'. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| When using change streams and you need the post-update document, open the stream with fullDocument: 'updateLookup' so handlers receive the current document on update events. | change_streams | app/src/worker/watch.js line 38 and app/src/alert_watcher.js line 54 pass { fullDocument: 'updateLookup' } to Model.watch(). | [Change streams in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/change-streams) |
| Design alert-rule queries so they can be satisfied by indexes (e.g., lookup by userId + active + symbol); create appropriate compound indexes rather than scanning all rules. | indexing | app/src/models/alertrule.js includes indexes on userId and compound userId+active (AlertRuleSchema.index({ userId: 1, active: 1 })). | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Create indexes to support aggregation match and group stages used by portfolio P&L and sector allocation (e.g., indexes on accountId, symbol, sector or a compound {accountId:1, symbol:1}). | indexing | app/src/models/position.js defines indexes: userId, symbol, sector and compound userId+symbol; documentdb_list_indexes shows these indexes were created (events entries). | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Make seed scripts idempotent by using upserts keyed on stable natural keys so seeds can be rerun safely. | seeding | app/scripts/seed.js uses Position.updateOne(..., { upsert: true }) and AlertRule.updateOne(..., { upsert: true }). | scripts/seed.js<br>scripts/seed.js |
| Write unit tests for aggregation logic with realistic sample documents and include short integration tests that run aggregations against the live sample_fintech_03 database to validate correctness and index usage. | testing | tests/aggregation.test.js unit test exists and passed (npm test); scripts/aggregate_test.js runs aggregation against the live DB (events show the aggregation output). | prior_knowledge (no public address recorded) |
| Audit: the code uses both axios and node-fetch for HTTP; the choice was not logged as a design decision. | audit trail | app/src/worker/watch.js imports node-fetch; app/src/alert_watcher.js imports axios. No explicit decision logged choosing libraries. | code files (no public address recorded) |
| Audit: change stream uses fullDocument:updateLookup but the decision to use this option was not logged. | audit trail | app/src/worker/watch.js line 38 and app/src/alert_watcher.js line 54 use fullDocument:'updateLookup' but no decision entry mentions this specific option. | code files (no public address recorded) |

#### Not applicable

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Model and store embeddings as a fixed-length numeric array and record the embedding dimensionality and model metadata. | vector_search | The sample does not use embeddings or vector indexes. | [documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md) |
| Create a dedicated vector index (cosmosSearch) with explicit options that match your embedding model and scale. | vector_search | No vector indexes created in the sample. | [documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md) |
| Enable diagnostic settings and capture slow-query logs to Log Analytics and alert on CPU/memory/connection saturation. | monitoring | Cluster-level monitoring is outside this sample's code; no cluster settings modified by the sample. | [documentdb-monitoring](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md) |
| Pick cluster throughput to cover peak workloads from change-stream consumers and heavy aggregations. | provisioning | Cluster provisioning is outside sample code and was not modified in this run. | [documentdb-high-availability](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/high-availability/SKILL.md) |
| Rely on the platform's automatic backups and retention policy as part of DR planning. | backups | Backups are a cluster-level setting; sample does not alter backup policy. | [documentdb-high-availability](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/high-availability/SKILL.md) |
| Prefer Private Endpoint / firewall rules and Microsoft Entra ID + RBAC for auth and use CMK for encryption-at-rest when required. | security | Configuration of network isolation or Entra-auth is a cluster/admin concern outside the sample code. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| When using change streams at scale, use the GetChangeStreamTokens command to obtain per-physical-shard resume tokens and run a watcher per token to parallelize load. | change_streams | The sample runs a single watcher and the environment/seed is single-shard; multishard token parallelization is not implemented. | [Use MongoDB extension commands to manage data stored in Azure Cosmos DB for MongoDB](https://learn.microsoft.com/azure/cosmos-db/mongodb/custom-commands#parallelizing-change-streams) |

### Reference requirements

12 of 19 met. The builder never saw these; this measures the starter prompt and the skills.

| Requirement | Status | Cause | Evidence | Smallest fix |
|---|---|---|---|---|
| Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. | not_met | tool_unavailable | No IaC (Bicep/Terraform) files present in repo. The builder deliberately did not provision resources (decision D009) because run policy forbids creating Azure resources. | Add minimal IaC artifacts (Bicep or Terraform templates targeting Microsoft.DocumentDB/mongoClusters) to the repo so the sample includes optional provisioning; the build pipeline can skip applying them in restricted runs. |
| Dependencies are pinned in requirements.txt. | partly_met | prompt_silent | This is a Node.js sample: package-lock.json is present (ensures reproducible installs). package.json contains caret (^) ranges rather than exact pinned versions. | Commit package-lock.json (already present) and/or replace ranges with exact versions in package.json (or add a note in README to use npm ci to ensure lockfile reproducibility). |
| The README covers what the sample shows, prerequisites, setup, run and clean-up. | partly_met | prompt_silent | README.md documents what the sample shows, prerequisites, setup and run steps, but does not include explicit clean-up / teardown instructions for the sample database or indexes. | Add a 'Clean up' section to README with commands to drop the sample collections or database (or instructions to run a provided cleanup script). |
| The vector index dimensions match the embedding model's output. | not_checkable | - | The sample does not create or use vector embeddings or vector indexes. | - |
| The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. | not_checkable | - | No vector index is created in this sample. | - |
| /search returns a clear error for an empty query and when the embedding call fails. | not_checkable | - | This sample does not implement a /search endpoint. | - |
| Search results include the similarity score. | not_checkable | - | No search functionality in this sample. | - |
| A Node.js portfolio service built with Mongoose that defines models for positions and for alert rules and persists documents of both kinds in Azure DocumentDB. | met | - | app/src/index.js lines 11-12 (mongoose.model registrations); app/src/models/position.js and app/src/models/alertrule.js define schemas and indexes. | - |
| A change stream opened through Mongoose on the positions collection (e.g. Model.watch()) that stays open while the service runs and receives the collection's change events. | met | - | app/src/worker/watch.js line 38 (Position.watch(..., { fullDocument: 'updateLookup' })); app/src/index.js lines 57-59 starts the worker. | - |
| Incoming change events are inspected to detect price updates on positions, and each detected price update triggers alert evaluation for the affected position. | met | - | app/src/worker/watch.js lines 39-46 and app/src/alert_watcher.js lines 10-16 inspect change.fullDocument, compute pnl and trigger evaluation. | - |
| On a detected price update, each alert rule document is evaluated against the position's new price to decide whether the rule's threshold is breached. | met | - | app/src/alert_watcher.js lines 22-28 (metric selection) and lines 4-7 (evalComparison). | - |
| When an alert rule's threshold is breached, the service fires a webhook (an HTTP request to a webhook endpoint) carrying the alert. | met | - | app/src/alert_watcher.js lines 31-36 (axios.post) and app/src/worker/watch.js lines 50-53 (sendWebhook result logged). | - |
| An aggregation pipeline run through Mongoose on the positions data that computes portfolio P&L and sector allocation. | met | - | app/src/app.js lines 16-27 and app/src/index.js lines 18-36 show the aggregation pipeline; scripts/aggregate_test.js exercised the pipeline (events show it returned summary JSON). | - |
| The connection string and model credentials come from environment variables; none appear in the repository. | met | - | app/src/db.js lines 8-9 read process.env.DOCUMENTDB_URI; app/.env.example contains only a placeholder for DOCUMENTDB_URI. | - |
| A .env.example lists every setting with placeholder values. | met | - | app/.env.example contains DOCUMENTDB_URI placeholder; README documents usage (copy .env.example to .env). | - |
| One database client is created and reused across requests. | met | - | app/src/db.js implements a singleton pattern (isConnected) and reuses mongoose across the process. | - |
| A seed script loads sample data and creates the index, and can be run twice without duplicating data. | met | - | app/scripts/seed.js uses updateOne(..., { upsert: true }) for positions and alert rules; app/scripts/create_indexes.js calls createIndexes(); events show seed and index creation ran successfully. | - |
| Unit tests run without a live cluster. | met | - | tests/aggregation.test.js exercises a pure function and npm test passed (events: 'PASS tests/aggregation.test.js'). | - |
| The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name. | met | - | README.md and docs use the name 'Azure DocumentDB' consistently (README lines 1, 3 and other references). | - |

