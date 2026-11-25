# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 6 |
| model_default | 3 |
| operator | 2 |
| skill | 2 |
| readiness_report | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T06:31:59+00:00

## D002 (build): I chose Node.js with Express and Mongoose (JavaScript) for the sample app.

- **Instead of:** Python/Flask; Node.js/Express with Mongoose; Go with mgo
- **Because:** The prompt explicitly requested Node.js and Mongoose; it is the natural choice for compatibility and the available environment (Node.js v24).
- **Reason came from:** `prompt`
- **Evidence:** Sample prompt: 'build a Node.js Mongoose portfolio service'
- **When:** 2026-11-25T06:32:17+00:00

## D003 (build): I chose Mongoose 7.x (latest 7.x release) for the sample, e.g., mongoose@7.6.0.

- **Instead of:** Mongoose 6.x; Mongoose 7.x
- **Because:** Mongoose 7.x is current, supported on Node 24, and compatible with MongoDB 7.x; it pairs with the modern Node.js driver and simplifies schema definitions for the sample.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'cluster is MongoDB 7.0 wire protocol' and skills recommend using a Mongoose version compatible with MongoDB 7.0.
- **When:** 2026-11-25T06:32:29+00:00

## D004 (build): I chose to read the connection string from process.env.DOCUMENTDB_URI at runtime.

- **Instead of:** Read connection string from a config file; Read from environment variable DOCUMENTDB_URI
- **Because:** Avoid storing secrets in code; follow run environment guidance and readiness report.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report instruction: 'Read the connection string from process.env.DOCUMENTDB_URI at runtime and use the SRV-style connection string provided by the cluster (do not hardcode host suffixes/ports).'
- **When:** 2026-11-25T06:32:32+00:00

## D005 (build): I chose to create indexes: {userId:1}, {userId:1, symbol:1} (compound), {symbol:1}, and {sector:1}.

- **Instead of:** Create many indexes including unique constraints; Create a small set of single-field and compound indexes (userId, userId+symbol, sector)
- **Because:** These indexes support the aggregation and query patterns the sample exposes while keeping index count small and useful.
- **Reason came from:** `prompt`
- **Evidence:** Assumptions from prompt review suggested indexes on userId, symbol, compound {userId, symbol}, and sector for grouping. documentdb-indexing recommends compound indexes for equality+sort patterns.
- **When:** 2026-11-25T06:32:34+00:00

## D006 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T06:35:01+00:00

## D007 (build): I chose Node.js (v24) with Express and Mongoose (7.x) for the sample app.

- **Instead of:** Python/Flask; Node.js/Express with Mongoose; Go with Mongo driver
- **Because:** The prompt explicitly requests Node.js and Mongoose; Node 24 is available in the environment. Mongoose 7.x is a modern, compatible choice for MongoDB 7.0 wire protocol.
- **Reason came from:** `prompt`
- **Evidence:** User prompt: 'build a Node.js Mongoose portfolio service' and readiness_report: 'Node.js v24 is present' and assumptions: 'Mongoose 7.x with the mongodb driver 5.x'.
- **When:** 2026-11-25T06:35:27+00:00

## D008 (build): I chose to read the DocumentDB connection string from process.env.DOCUMENTDB_URI at runtime.

- **Instead of:** Read URI from env (DOCUMENTDB_URI); Read from a local config file; Prompt user for connection string at runtime
- **Because:** Avoid storing secrets in files; environment variable is standard and required by the runner instructions.
- **Reason came from:** `prompt`
- **Evidence:** readiness_report instruction: 'Read the connection string from process.env.DOCUMENTDB_URI at runtime' and skill documentdb-connection: 'Ensure tls=true in connection string'.
- **When:** 2026-11-25T06:35:41+00:00

## D009 (build): I chose NOT to provision Azure resources in the sample and to include no provisioning commands to create clusters.

- **Instead of:** Include infra provisioning in sample and run az to create cluster; Do not provision and only include IaC as files
- **Because:** The environment forbids creating Azure resources; the cluster is already provided and documented in DOCUMENTDB_URI.
- **Reason came from:** `prompt`
- **Evidence:** run_policy: 'Azure resource changes allowed: False' and readiness_report guidance to not provision in this run.
- **When:** 2026-11-25T06:35:44+00:00

## D010 (build): I chose not to implement sharding in this sample (single-shard collections).

- **Instead of:** Shard collection with shard key userId or symbol; Do not shard — single-shard collection
- **Because:** Sample dataset is small and the environment's cluster is pre-provisioned; sharding is an advanced production technique outside scope of this teaching sample.
- **Reason came from:** `model_default`
- **Evidence:** Assumptions: small sample app; readiness_report: 'check sharding before production' and no need in sample.
- **When:** 2026-11-25T06:35:46+00:00

## D011 (build): I chose a conservative sample policy: single HTTP POST attempt to the webhook and log failures (no durable retry queue).

- **Instead of:** Single attempt then log failures; Retry webhook delivery with exponential backoff and persist attempts; Push webhook to durable queue for retries
- **Because:** Keeps the sample simple and focused on change streams and aggregation; production apps should implement durable retries—this is noted in README.
- **Reason came from:** `model_default`
- **Evidence:** readiness_report noted webhook retry policy unspecified; no skill prescribes it.
- **When:** 2026-11-25T06:35:48+00:00

## D012 (build): I chose to define indexes in the Mongoose schemas (schema.index) and run ensureIndexes on connection; also verify via the documentdb MCP server.

- **Instead of:** Create indexes via Mongoose schema.index and rely on model.ensureIndexes; Create indexes using documentdb MCP tool; Create indexes via a dedicated script using MongoDB driver
- **Because:** Keeping index definitions with the schema simplifies sample maintenance and ensures they are created when the app runs; verification will use the MCP tool.
- **Reason came from:** `skill`
- **Evidence:** documentdb-indexing skill: 'Only _id is created automatically; every other index must be created explicitly.'
- **When:** 2026-11-25T06:35:55+00:00

## D013 (build): I chose to force the database name to 'sample_fintech_03' via mongoose.connect option dbName to ensure sample uses the required database.

- **Instead of:** Leave connection to use default database from URI; Force dbName to 'sample_fintech_03' in mongoose.connect options
- **Because:** The environment's DOCUMENTDB_URI may not include the desired database; forcing dbName ensures consistent placement of sample data for verification.
- **Reason came from:** `prompt`
- **Evidence:** skill_md: 'Use the database named sample_fintech_03 for everything this sample creates.'
- **When:** 2026-11-25T06:37:39+00:00

## D014 (build): I chose to add and run a small script (scripts/create_indexes.js) that explicitly calls createIndexes() on the models to ensure indexes are created for verification.

- **Instead of:** Rely on Mongoose autoIndex at model creation; Explicitly call createIndexes in a small script to ensure indexes exist
- **Because:** Explicitly creating indexes ensures the sample's intended indexes are present for query performance and for verification via the MCP tools.
- **Reason came from:** `skill`
- **Evidence:** documentdb-indexing: 'every other index must be created explicitly' and current inspection showed only _id and userId index existed.
- **When:** 2026-11-25T06:38:11+00:00
