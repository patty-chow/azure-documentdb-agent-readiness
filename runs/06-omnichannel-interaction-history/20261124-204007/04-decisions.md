# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 6 |
| operator | 1 |
| model_default | 1 |
| skill | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T11:27:37+00:00

## D002 (build): I chose Node.js with Express and Mongoose (MongoDB ODM) for a small REST service.

- **Instead of:** Python/Flask; Node.js + Express + Mongoose; Go + mgo
- **Because:** The prompt explicitly requests Node.js and Mongoose; Express is the common framework for small REST APIs.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'build a Node.js Mongoose service'
- **When:** 2026-11-25T11:27:54+00:00

## D003 (build): I chose Mongoose ^7 (latest 7.x) as the dependency constraint.

- **Instead of:** Pin an exact Mongoose version (e.g., 6.x); Use latest 7.x (Mongoose ^7)
- **Because:** Mongoose 7.x supports modern Node.js and MongoDB server versions; readiness report flagged missing exact recommended version, so choose 7.x which is current and compatible.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report assumption: 'Use current stable Mongoose v7.x (compatible with MongoDB 7.0 wire protocol)'.
- **When:** 2026-11-25T11:27:58+00:00

## D004 (build): I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Read connection string from a local config file; Read connection string from environment variable DOCUMENTDB_URI
- **Because:** Security and the prompt's instruction to never write secrets to files; environment variables are standard for samples.
- **Reason came from:** `prompt`
- **Evidence:** Skill run environment: 'connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time.'
- **When:** 2026-11-25T11:28:01+00:00

## D005 (build): I chose not to provision resources and to use the existing cluster reachable via DOCUMENTDB_URI.

- **Instead of:** Provision a new cluster via az / Bicep / Terraform; Use existing pre-provisioned cluster (DOCUMENTDB_URI) and do not provision resources
- **Because:** Avoid provisioning per policy and follow the instruction to use the provided cluster for verification.
- **Reason came from:** `prompt`
- **Evidence:** Run environment: 'an Azure DocumentDB cluster is already provisioned and reachable. Connection string is in DOCUMENTDB_URI.' Also run policy forbids Azure resource changes.
- **When:** 2026-11-25T11:28:03+00:00

## D006 (build): I chose cursor-based pagination using (timestamp, _id) encoded as a base64 cursor.

- **Instead of:** Offset-based pagination (skip/limit); Cursor-based pagination (timestamp + _id)
- **Because:** Cursor-based pagination is stable and correct for time-ordered histories; it avoids skip performance and consistency issues.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'prefer cursor (timestamp) for correctness.'
- **When:** 2026-11-25T11:28:07+00:00

## D007 (build): I chose to create exactly the two required compound indexes: (customerId, timestamp) and (channel, timestamp).

- **Instead of:** Create compound indexes on (customerId, timestamp) and (channel, timestamp) only; Also create other supporting indexes (e.g., text, vector)
- **Because:** Keep sample focused and avoid unnecessary write-costs; these two indexes satisfy the query patterns the sample demonstrates.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'Create compound indexes on (customerId, timestamp) and (channel, timestamp) to support efficient history queries.'
- **When:** 2026-11-25T11:28:10+00:00

## D008 (build): I chose to require DOCUMENTDB_URI from environment and provide a .env.example with a placeholder; no secrets will be written to files.

- **Instead of:** Use .env file for local secrets and provide .env.example; Embed the connection string in code or config files
- **Because:** Security best practice and explicit instruction in prompt.
- **Reason came from:** `prompt`
- **Evidence:** Prompt guidance: 'Never write a secret... Read them from environment variables, and ship a .env.example with placeholder values.'
- **When:** 2026-11-25T11:28:13+00:00

## D009 (build): I chose tuned connection options suitable for a long-running OLTP service: maxPoolSize=50, minPoolSize=10, connectTimeoutMS=10000, socketTimeoutMS=30000, serverSelectionTimeoutMS=5000.

- **Instead of:** Use default Mongo client options; Tune connection pool for long-running OLTP (maxPoolSize 50, minPoolSize 10, connectTimeoutMS 10000, socketTimeoutMS 30000)
- **Because:** The sample is a long-running local Express service intended to represent an OLTP use case; these settings provide reasonable defaults while following the skill's guidance to state assumptions.
- **Reason came from:** `skill`
- **Evidence:** documentdb-connection skill guidance lists recommended parameters for Traditional Long-Running Servers (OLTP).
- **When:** 2026-11-25T11:28:25+00:00
