# Documentation and tooling gaps: 16-subscription-billing-engine

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] DocumentDB vs Cosmos DB naming/disambiguation

- **What was missing:** Clear, prominent guidance distinguishing 'Azure DocumentDB (managed MongoDB-compatible vCore offering)' from 'Azure Cosmos DB for MongoDB (RU-based)' and from Amazon DocumentDB. The readiness findings show agents and builders confuse resource names, CLI groups and template resource types.
- **Where the agent looked:** Learn docs and agent-kit readiness notes; several quickstarts historically show Cosmos DB 'databaseAccounts' which caused confusion with the mongoClusters resource type.
- **Effect on this build:** High risk: confusion leads to wrong IaC templates (databaseAccounts vs mongoClusters), the wrong az CLI group (az cosmosdb vs az documentdb), wrong connection strings/ports, and incorrect guidance to agents.
- **Suggested fix (naming_or_disambiguation):** A single-line prominent banner at the top of relevant quickstarts and the agent-kit README: 'Azure DocumentDB (mongoClusters) is distinct from Azure Cosmos DB for MongoDB (databaseAccounts RU) and from Amazon DocumentDB — use Microsoft.DocumentDB/mongoClusters and az documentdb mongocluster commands for DocumentDB clusters.' Include quick examples of the correct az command and a Bicep snippet showing Microsoft.DocumentDB/mongoClusters.

## [medium] Env example completeness

- **What was missing:** .env.example omitted a few runtime variables used or commonly needed for a sample (PORT, LOG_LEVEL and a note about DATABASE_NAME).
- **Where the agent looked:** Repository files (.env.example, src/db.js) and quickstart docs for Mongoose on DocumentDB.
- **Effect on this build:** Minor: the sample ran because defaults exist (PORT defaulted to 3000); however users/agents might not know which env vars are optional vs required.
- **Suggested fix (learn_doc):** Short README subsection and an updated .env.example listing: DOCUMENTDB_URI (placeholder), DATABASE_NAME (placeholder), PORT (placeholder, default 3000), LOG_LEVEL (optional), and notes indicating which are optional and where to get the connection string. Add a one-line example `DOCUMENTDB_URI="mongodb+srv://<user>:<pass>@<cluster>.global.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retryWrites=false"`.

## [medium] Which Mongoose version to pin

- **What was missing:** Authoritative guidance in the quickstarts about which Mongoose major version is recommended/pinned for DocumentDB + Node 24.
- **Where the agent looked:** learn.microsoft.com quickstarts and tutorial pages. The quickstarts recommend Mongoose 9 in several examples, but the sample used Mongoose 7.x without explicit guidance in the agent kit.
- **Effect on this build:** Medium: the builder chose Mongoose 7.x (logged D002). Using a non-tested Mongoose major can cause subtle incompatibilities or confuse agents when choosing a runtime.
- **Suggested fix (discoverability):** Add a short 'tested versions' box in the Node/Mongoose quickstarts listing a tested Mongoose version (e.g. 9.12.1) and tested MongoDB driver bundle, plus notes on which older Mongoose majors are supported. Also add a one-line recommendation in the agent-kit templates to pin the tested version in package.json.

## [medium] Idempotency operational guidance

- **What was missing:** There is no single public page that specifies idempotency-key canonicalization (length, allowed characters) or retention/cleanup guidance for billing audit records for Azure DocumentDB.
- **Where the agent looked:** Learn docs and discovered_practices search; several 'searches_with_no_useful_result' entries listed idempotency-key length and retention guidance.
- **Effect on this build:** Low: the sample uses a simple string idempotencyKey and demonstrates the technique, but agents building production systems may pick unsafe key formats or retention policies.
- **Suggested fix (learn_doc):** Add a short 'Idempotency for billing' page: recommend idempotencyKey canonical form (UUID or application-provided stable identifier), a unique index, recommended retention for audit records, and examples of how to expire/compact old audit data.

## [medium] Testing without live cluster

- **What was missing:** Guidance and an example test-suite showing how to run unit tests without a live DocumentDB cluster (example using mongodb-memory-server or Mongoose mocking).
- **Where the agent looked:** Quickstarts and agent-kit docs — no dedicated test example for DocumentDB Mongoose samples.
- **Effect on this build:** Medium: the repository contains no tests; adding example tests would make the sample suitable for CI and gallery submission.
- **Suggested fix (sample_or_quickstart):** A short 'Testing' page in the sample template that includes an example Jest/Mocha test that runs with mongodb-memory-server and demonstrates mocking transactions and idempotency behavior, plus a note describing what needs a live cluster (index verification).

## [low] Vector index createIndexes examples

- **What was missing:** Copy/paste createIndexes runCommand examples for HNSW/IVF/DiskANN with the exact cosmosSearchOptions field names and sample parameters.
- **Where the agent looked:** Vector search docs on learn.microsoft.com; readiness notes flagged that agents guess vendor-neutral syntax and can be rejected by the server.
- **Effect on this build:** Medium for vector-enabled samples; low for this sample because it doesn't use vectors. Without explicit examples agents will attempt incorrect createIndex syntax and receive errors.
- **Suggested fix (learn_doc):** A small 'indexing' snippet page showing db.runCommand({ createIndexes: '<coll>', indexes:[{ key:{'<field>':'cosmosSearch'}, name:'vec', cosmosSearchOptions:{ kind:'vector-hnsw', dimensions:1536, similarity:'COS', m:16, efConstruction:64 } }] }) for each supported kind, plus notes on dimension matching and retryWrites=false requirement.

## [low] TTL verification & testing guidance

- **What was missing:** A short documented note on TTL behavior (how expireAfterSeconds works, background thread timing, and how to test it deterministically in CI or locally).
- **Where the agent looked:** learn.microsoft.com TTL docs and sample scripts; TTL semantics (background job) are documented but a short testing cookbook for builders is missing.
- **Effect on this build:** Low: the index was created but automatic deletion was not observed during the run because TTL is time-based.
- **Suggested fix (learn_doc):** A one-paragraph note in the TTL docs: explain that expireAfterSeconds is applied relative to the indexed Date, deletion is performed by a background thread (may take minutes), and provide a testing recipe (set a near-future expiresAt and wait or simulate clock in local gateway) and how to verify deletions via listIndexes and count queries.

