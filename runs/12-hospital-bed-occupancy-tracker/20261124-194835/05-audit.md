# 5. Best-practice audit: 12-hospital-bed-occupancy-tracker

**Verdict: pass_with_findings** (10 followed, 2 violated, 1 not applicable, 1 not assessable)

The sample implements the core functionality: a Node.js (Mongoose) service that stores bed documents, opens a change stream, maintains per-ward summary documents, seeds data idempotently, and creates a TTL index that targets cleaning-state documents. The build ran against a live cluster and the demo/change-stream exercises updated ward summaries as expected. Key gaps: the change-stream handler does not detect previous→new status transitions (it recomputes counts for the ward on every change), so it does not 'act only on events where the status changed' as required; the handler does not persist resume tokens or checkpoints; there is no retry/backoff handling for transient errors; and the seed script performs many per-bed upserts rather than a batched bulkWrite. Documentation and IaC expectations in the gallery checklist (tests that run without a live cluster, explicit IaC for mongoClusters) are not provided. The TTL index and cleaningExpiresAt semantics are implemented, and the build observed expected TTL-index metadata, but TTL deletions are background-driven and were not observed in a short live test (not a failure of the sample, but a behavioral note).

## Review of the builder's decisions

| Decision | What was decided | Reason came from | Assessment | Comment |
|---|---|---|---|---|
| D001 | I approved the build with readiness 'ready_with_gaps' | operator | unverifiable | D001 records an operator approval ('ready_with_gaps') with no evidence or tool trace beyond the decision entry. The events log contains the decision entry but no external artifact to verify the operator's stated readiness criteria. |
| D002 | I chose Node.js with Mongoose 7.x | prompt | sound | D002: The decision to use Node.js with Mongoose 7.x is recorded and matches package.json which declares mongoose ^7.6.0. events.jsonl contains the log_decision entry (Recorded as D002). |
| D003 | I chose to set tls=true, authMechanism=SCRAM-SHA-256, and retryWrites=false in the MongoDB connection options (passed via connection string or mongoose options) | readiness_report | questionable | D003: The decision text records using tls=true, SCRAM-SHA-256 and retryWrites=false. The events log shows D003 recorded. The code relies on the connection string to carry TLS/auth options (app/src/db.js:14-21) and .env.example includes a tls=true example. This is acceptable, but the decision implies client options would be set explicitly; the code doesn't enforce them, so the decision is somewhat optimistic about how options are supplied. |
| D004 | I chose not to provision any Azure resources and to use the existing cluster referenced by DOCUMENTDB_URI | readiness_report | sound | D004: Decision to not provision Azure resources is consistent with the run environment and events; the builder used an existing DOCUMENTDB_URI and did not execute IaC provisioning (events show no az resource create or IaC writes). |
| D005 | I chose to maintain a separate ward summary collection with documents like { wardId, counts: { occupied, available, cleaning }, capacity } updated atomically via $inc upsert | prompt | wrong | D005 states the summary will be updated atomically via $inc upsert. The events show D005 was recorded, but the implementation in app/src/changeWatcher.js recomputes counts and uses updateOne with $set of the counts (app/src/changeWatcher.js:45-50) rather than applying a delta via $inc based on the observed transition. The decision content and the code therefore diverge. |
| D006 | I chose to use a TTL index on a Date field cleaningExpiresAt with expireAfterSeconds set to 0 (so documents expire at that instant) and set that field when entering 'cleaning' | readiness_report | sound | D006: Decision to use TTL index on cleaningExpiresAt with expireAfterSeconds:0 and set that field when entering cleaning is implemented: seed.js creates the index and server.js/demo/seed set/clear cleaningExpiresAt accordingly. events.jsonl shows the index metadata via documentdb_list_indexes. |
| D007 | I chose to perform a live TTL test by setting a small TTL on a bed (5s) and polling to observe whether the document is removed, to validate TTL semantics on the target cluster. | readiness_report | sound | D007: The decision to perform a live TTL test was executed — events.jsonl contains the run of src/ttl_check.js and output showing TTL deletion was not observed within 30s. The decision and evidence align. |

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
| On the checklist and found by open discovery | 13 | Public and discoverable. |

#### Known to the model, no public source, not on the checklist

| Topic | Description | What would help |
|---|---|---|
| Change-stream idempotency | Design change-stream consumers to be idempotent (dedupe or use idempotency keys) because event replays or redelivery are possible and can otherwise cause double-counting. | A public guidance page documenting recommended idempotency/dedupe patterns for DocumentDB change-stream consumers (control-collection + processed-event id checkpoint example). |

#### On the checklist and found by open discovery

| Topic | Description | Sources |
|---|---|---|
| Connection client reuse | Create a single MongoClient (or single Mongoose connection) and reuse it for the process lifetime instead of creating a client per request. | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Connection pool tuning | Tune connection-pool parameters for your environment: use small pools for serverless, larger pools for long-running OLTP, set minPoolSize, maxIdleTimeMS and serverSelectionTimeoutMS appropriately. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| TLS enforcement | Always require TLS on the wire (tls=true) and do not disable certificate validation in production; configure TLS options only via environment/secret-driven config for local detours. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Change-stream resume tokens | Persist change-stream resume tokens durably and resume change streams using resumeAfter / startAtOperationTime so a watcher can continue from the last-processed event after restart. | [Change streams in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/change-streams#resume-a-change-stream) |
| fullDocument updateLookup | When you need the post-update document in change-stream events use fullDocument: 'updateLookup' so update events include the current document state. | [$changeStream (aggregation stage)](https://learn.microsoft.com/documentdb/query/operators/aggregation/$changestream) |
| Pre-images for before-change | Enable pre-images (changeStreamPreAndPostImages) on a collection if you need fullDocumentBeforeChange, but be aware this increases storage and write amplification. | [Change streams in Azure DocumentDB (pre-images)](https://learn.microsoft.com/azure/documentdb/change-streams#pre-images-in-change-streams) |
| TTL index on Date field | Use a TTL index on a Date field (createIndex({ expiresAt: 1 }, { expireAfterSeconds: 0 })) to expire at a specific timestamp, and ensure the field is a Date (not a number); know TTL deletions are background-driven and can be delayed. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| TTL background timing | Do not rely on TTL for strict, immediate deletion semantics; if you need deterministic deletion timing implement an explicit scheduled job or background worker. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Compound index ESR | Design compound indexes using ESR and create a compound index like { wardId: 1, status: 1 } to support queries listing beds by ward and status. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Denormalize ward summary | Denormalize read-heavy data and precompute small per-ward summary documents (one document per ward) to avoid expensive $lookup and permit efficient atomic updates. | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| Atomic single-document updates | Use findAndModify / findOneAndUpdate (atomic single-document modification) for counters and other atomic updates to a single document (supports upsert and $inc semantics). | [findAndModify](https://learn.microsoft.com/documentdb/query/commands/query-and-write/findandmodify) |
| .env.example for developers | For secrets and developer workflows include a .env.example with a placeholder DOCUMENTDB_URI and instruct developers not to commit real credentials; in CI use environment secrets or Key Vault. | [documentdb-local-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md) |
| Use MCP/mongosh to validate indexes | Use the DocumentDB MCP or mongosh explain/index/list commands to validate index usage and get collection/index statistics before making index changes. | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |

### How the app measures up

#### Violations

| Practice | Category | Evidence | Fix | Source |
|---|---|---|---|---|
| Tune connection-pool parameters for your environment: use small pools for serverless, larger pools for long-running OLTP, set minPoolSize, maxIdleTimeMS and serverSelectionTimeoutMS appropriately. | connection handling | app/src/db.js:14-21 (only serverSelectionTimeoutMS set; no explicit pool size/minIdle/maxIdle configuration) | Set pool options (e.g., maxPoolSize, minPoolSize, maxIdleTimeMS) in mongoose.connect options or document expected production values in README (e.g., maxPoolSize:50 for OLTP). | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Persist change-stream resume tokens durably and resume change streams using resumeAfter / startAtOperationTime so a watcher can continue from the last-processed event after restart. | change streams & operations | app/src/changeWatcher.js shows Bed.watch(...) usage but no durable storage or persistence of resume tokens; there is no control collection or checkpoint logic. | Persist the change._id (resume token) or last processed clusterTime into a small control collection after each processed event; on restart, open the stream with resumeAfter: savedToken. | [Change streams in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/change-streams#resume-a-change-stream) |

#### Could not be assessed

| Practice | Category | What was searched and missing | Source |
|---|---|---|---|
| Design change-stream consumers to be idempotent (dedupe or use idempotency keys) because event replays or redelivery are possible and can otherwise cause double-counting. | change streams & idempotency | Searched: 'Azure DocumentDB change stream duplicate', 'Azure DocumentDB change stream idempotent' | prior_knowledge (no public address recorded) |

#### Followed

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Create a single MongoClient (or single Mongoose connection) and reuse it for the process lifetime instead of creating a client per request. | connection handling | app/src/db.js:8-16 (singleton connection variable and connect() that returns existing connection) | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Always require TLS on the wire (tls=true) and do not disable certificate validation in production; configure TLS options only via environment/secret-driven config for local detours. | security & networking | app/.env.example:3 (connection string example includes tls=true); app/src/db.js:19-21 (comment notes TLS/auth options are usually encoded in the connection string) | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| When you need the post-update document in change-stream events use fullDocument: 'updateLookup' so update events include the current document state. | change streams | app/src/changeWatcher.js:12 (Bed.watch(pipeline, { fullDocument: 'updateLookup' })) | [$changeStream (aggregation stage)](https://learn.microsoft.com/documentdb/query/operators/aggregation/$changestream) |
| Use a TTL index on a Date field (createIndex({ expiresAt: 1 }, { expireAfterSeconds: 0 })) to expire at a specific timestamp, and ensure the field is a Date (not a number); know TTL deletions are background-driven and can be delayed. | ttl & lifecycle | app/src/seed.js:12-16 (createIndex({ cleaningExpiresAt:1 }, { expireAfterSeconds:0 })), app/src/models/bed.js:9-10 (cleaningExpiresAt is Date) | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Do not rely on TTL for strict, immediate deletion semantics; if you need deterministic deletion timing implement an explicit scheduled job or background worker. | ttl & lifecycle | app/src/ttl_check.js demonstrates a short TTL test and README/seed note documents that TTL deletions are background-driven; run logs show TTL deletion not observed in 30s | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Design compound indexes using ESR and create a compound index like { wardId: 1, status: 1 } to support queries listing beds by ward and status. | indexes & queries | app/src/models/bed.js:15 (BedSchema.index({ wardId: 1, status: 1 })), app/src/seed.js:16 (also creates the compound index) | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Denormalize read-heavy data and precompute small per-ward summary documents (one document per ward) to avoid expensive $lookup and permit efficient atomic updates. | data modeling & atomicity | app/src/models/wardSummary.js:4-12 (WardSummary schema), app/src/seed.js:30-32 (creates summary docs), app/src/changeWatcher.js:45-50 (updates summary) | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| Use findAndModify / findOneAndUpdate (atomic single-document modification) for counters and other atomic updates to a single document (supports upsert and $inc semantics). | data modeling & atomicity | app/src/changeWatcher.js:50 uses WardSummary.updateOne(..., { upsert: true }) which performs a single-document atomic update (the sample uses $set of counts rather than $inc delta) | [findAndModify](https://learn.microsoft.com/documentdb/query/commands/query-and-write/findandmodify) |
| For secrets and developer workflows include a .env.example with a placeholder DOCUMENTDB_URI and instruct developers not to commit real credentials; in CI use environment secrets or Key Vault. | developer ergonomics & security | app/.env.example:1-10 (placeholder DOCUMENTDB_URI and CLEANING_TTL_SECONDS explained) and README.md:14-16 (copy .env.example to .env) | [documentdb-local-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md) |
| Use the DocumentDB MCP or mongosh explain/index/list commands to validate index usage and get collection/index statistics before making index changes. | operations & tooling | events.jsonl: documentdb_list_indexes result (index list for beds) and documentdb_list_databases show collections; the builder used MCP tooling during verification (documentdb_list_indexes call recorded). | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |

#### Not applicable

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Enable pre-images (changeStreamPreAndPostImages) on a collection if you need fullDocumentBeforeChange, but be aware this increases storage and write amplification. | change streams & auditing | app/src/changeWatcher.js does not attempt to use fullDocumentBeforeChange; the sample uses fullDocument: 'updateLookup' and recompute logic instead | [Change streams in Azure DocumentDB (pre-images)](https://learn.microsoft.com/azure/documentdb/change-streams#pre-images-in-change-streams) |

### Reference requirements

10 of 16 met. The builder never saw these; this measures the starter prompt and the skills.

| Requirement | Status | Cause | Evidence | Smallest fix |
|---|---|---|---|---|
| From change stream events detect status transitions and act only on events where the status changed (e.g., compare previous status with new one). | not_met | builder_error | app/src/changeWatcher.js:37-50 (handler recomputes entire ward counts from the Bed collection for every event rather than comparing old/new status or inspecting pre-image) | Change the change-stream handler to detect transitions. Either enable and use pre-images/fullDocumentBeforeChange or persist the last-known status (or pre-image) and compare to fullDocument.status; then only perform the atomic summary update when status differs. |
| Unit tests run without a live cluster. | not_met | prompt_silent | No tests or test harness present in repository (no test files found during discovery). | Add a small unit test suite that uses an in-memory Mongo replacement or mocks Mongoose (e.g., mongodb-memory-server or sinon to stub model methods) that runs without a live cluster. |
| Infrastructure for the cluster is provided as code using the Azure DocumentDB resource type. | not_met | prompt_silent | No IaC files found (no Bicep/Terraform templates) in repository; builder intentionally used existing cluster per decision D004. | Add a minimal Bicep template (or Terraform) showing Microsoft.DocumentDB/mongoClusters example (documentdb-azure-deployment skill has canonical templates). |
| A live occupancy summary document is maintained per ward and updated from the change stream handler on every detected transition. | partly_met | builder_error | app/src/changeWatcher.js:45-51 (handler recomputes counts and updates WardSummary.updateOne with $set), app/src/models/wardSummary.js:4-12 (schema) | Change handler to compute the delta from the transition and apply a targeted atomic update (see next). If you prefer full recompute, still make it conditional on observed status change to reduce work. |
| Dependencies are pinned in a dependency lock so installs are reproducible. | partly_met | prompt_silent | app/package.json:18-22 (dependencies with ^ ranges), app/package-lock.json present in repo (package-lock.json at project root) | Either pin exact versions in package.json (remove ^) or rely on package-lock.json and document that CI uses package-lock for deterministic installs. |
| README covers what the sample shows, prerequisites, setup, run, and clean-up. | partly_met | prompt_silent | app/README.md includes what the sample shows, prerequisites and quickstart (seed/demo/server) but lacks an explicit clean-up section for sample-created data/indexes. | Add a 'Clean-up' section to README describing how to remove seeded documents/indexes or how to drop the sample database/collections (e.g., mongosh commands or MCP commands). |
| A Node.js service uses Mongoose to store bed status documents; each bed doc belongs to a ward and status is one of occupied, available or cleaning. | met | - | app/src/models/bed.js:4-11 (bed schema with wardId, status enum ['occupied','available','cleaning']) | none |
| The service opens a change stream on the bed status collection and keeps consuming its events while running. | met | - | app/src/changeWatcher.js:8-14 (pipeline) and 12 (Bed.watch(..., { fullDocument: 'updateLookup' })) and 58-64 (watcher kept alive until timeout) | none |
| Each summary update is a single atomic update operation (e.g., one updateOne with $inc adjusting the affected counts). | met | - | app/src/changeWatcher.js:50 (await WardSummary.updateOne({ wardId }, { $set: { counts } }, { upsert: true })) — single updateOne call, which is atomic for a single document | none |
| A TTL index is created in code on a Date field of the bed documents, with expireAfterSeconds (or the indexed Date value) derived from a configurable cleaning timeout. | met | - | app/src/seed.js:12-16 (createIndex({ cleaningExpiresAt: 1 }, { expireAfterSeconds: 0 })), app/src/seed.js:34-41 (cleaningExpiresAt set using DEFAULT_TTL derived from CLEANING_TTL_SECONDS) | none |
| Cleaning-state documents, and only those, are expired by the TTL index once the timeout has passed (e.g., set/clear the Date when entering/leaving cleaning or use a partial filter). | met | - | app/src/server.js:25-31 (sets cleaningExpiresAt when status==='cleaning' and clears it otherwise), app/src/seed.js:38-41 (seed sets cleaningExpiresAt only for cleaning), app/src/models/bed.js:9-10 (cleaningExpiresAt field) | none |
| Connection string and model credentials come from environment variables; none appear in repo. | met | - | app/.env.example:3-4 (DOCUMENTDB_URI placeholder), app/src/db.js:2 (reads process.env.DOCUMENTDB_URI) | none |
| A .env.example lists every setting with placeholder values. | met | - | app/.env.example:4-10 (DOCUMENTDB_URI, CLEANING_TTL_SECONDS, DB_NAME placeholders) | none |
| One database client is created and reused across requests. | met | - | app/src/db.js:8-16 (singleton connection variable and connect() that returns existing connection) | none |
| A seed script loads sample data and creates the index, and can be run twice without duplicating data. | met | - | app/src/seed.js:12-16 (index creation) and 34-41 (updateOne upsert per bed) and 30-32 (WardSummary upsert with $setOnInsert) | none |
| The sample uses the name 'Azure DocumentDB' throughout, and no former or neighbouring product name. | met | - | app/README.md:1 and other files refer to 'Azure DocumentDB' (no Cosmos DB or Amazon DocumentDB names present) | none |

