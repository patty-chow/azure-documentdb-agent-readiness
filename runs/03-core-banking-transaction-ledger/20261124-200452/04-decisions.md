# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 7 |
| readiness_report | 4 |
| model_default | 3 |
| operator | 2 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T09:26:18+00:00

## D002 (build): I chose Mongoose ODM (mongoose) with an Express REST surface.

- **Instead of:** Use raw MongoDB Node driver (mongodb); Use Mongoose ODM with schemas and transactions
- **Because:** Prompt explicitly requested Mongoose; Mongoose provides schema enforcement, validation, and integration with transactions which suit a readable sample app.
- **Reason came from:** `prompt`
- **Evidence:** Sample prompt: 'Using the DocumentDB skill, build a Node.js Mongoose core banking ledger'
- **When:** 2026-11-25T09:26:48+00:00

## D003 (build): I chose Mongoose 7.6.0 (pin exact version in package.json).

- **Instead of:** Pin Mongoose 6.x; Pin Mongoose 7.x (latest)
- **Because:** Mongoose 7.x is the recommended modern major line and is compatible with Node 24; pinning an exact 7.x release avoids unexpected upgrades for sample users.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'Builder will pick a recent Mongoose compatible with Node 24 (e.g., Mongoose 7.x) and the MongoDB 7.0 wire protocol.'
- **When:** 2026-11-25T09:26:51+00:00

## D004 (build): I chose to default to SCRAM credentials read from DOCUMENTDB_URI in environment variables, with README notes about Entra ID as optional.

- **Instead of:** Use SCRAM credentials from DOCUMENTDB_URI; Implement Microsoft Entra ID OIDC auth by default
- **Because:** Simpler for local development; cluster supports SCRAM and DOCUMENTDB_URI is available in environment per run environment notes.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness guidance: 'Default to SCRAM credential auth via DOCUMENTDB_URI for the sample; optionally add an enable Entra ID code path'
- **When:** 2026-11-25T09:26:54+00:00

## D005 (build): I chose to expose a small REST API (POST /transactions, GET /accounts/:id) plus an npm-run seed CLI script.

- **Instead of:** Expose CLI only; Expose REST API endpoints and CLI seed script
- **Because:** REST API demonstrates atomic posting and retrieval; seed script allows idempotent sample data loading; matches reviewer assumptions and is easy to run manually.
- **Reason came from:** `model_default`
- **Evidence:** Assumptions from prompt review recommended REST API and seed script.
- **When:** 2026-11-25T09:26:59+00:00

## D006 (build): I chose to create the unique index on transactions.transactionRef and a compound index {accountId:1, createdAt:-1}.

- **Instead of:** Create only transactionRef unique index; Also add compound index on accountId + createdAt
- **Because:** Unique index enforces idempotency; compound index supports recent-activity queries used by GET /accounts/:id.
- **Reason came from:** `model_default`
- **Evidence:** Assumptions from prompt review: 'At minimum create a unique index on transactions.transactionRef. Also create an index on transactions.accountId and transactions.createdAt'
- **When:** 2026-11-25T09:27:07+00:00

## D007 (build): I chose npm to install dependencies and run scripts.

- **Instead of:** npm; yarn
- **Because:** npm is available and standard; simpler for sample users and matches run environment.
- **Reason came from:** `readiness_report`
- **Evidence:** Environment: Node.js and npm/npx available per readiness report.
- **When:** 2026-11-25T09:28:05+00:00

## D008 (build): I chose to run the seed script against the live cluster to create sample data for verification.

- **Instead of:** Do not run seed, only create code; Run seed script against live cluster to create sample data
- **Because:** Seed data is required to demonstrate atomic transactions and to verify indexes and queries; run_policy allows non-Azure resource commands like node scripts to run against the cluster.
- **Reason came from:** `readiness_report`
- **Evidence:** Run environment: 'This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable... DOCUMENTDB_URI in environment'
- **When:** 2026-11-25T09:28:17+00:00

## D009 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T09:30:17+00:00

## D010 (build): I chose Node.js with Express and Mongoose.

- **Instead of:** Python/Flask + PyMongo; Node.js + Express + Mongoose
- **Because:** Node.js with Mongoose is the recommended quickstart for Azure DocumentDB and matches the environment (Node 24 available). It makes MongoDB transactions and Mongoose models simple for readers.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Builder will implement a single-agent, no-orchestration sample (a standalone Node.js app with local CLI and/or HTTP endpoints).'
- **When:** 2026-11-25T09:30:51+00:00

## D011 (build): I chose Mongoose 7.x (pin to 7.9.3).

- **Instead of:** Mongoose 6.x; Mongoose 7.x
- **Because:** Mongoose 7.x is stable, widely used and compatible with modern Node; no Node-24-specific authoritative version was available so I selected 7.x and will pin an explicit version in package.json.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'Builder will pick a recent Mongoose compatible with Node 24 (e.g., Mongoose 7.x)'
- **When:** 2026-11-25T09:30:54+00:00

## D012 (build): I chose SCRAM credential authentication via DOCUMENTDB_URI environment variable.

- **Instead of:** SCRAM auth via connection string env var; Microsoft Entra ID (OIDC) auth via DefaultAzureCredential
- **Because:** SCRAM is simplest for sample and the environment provides DOCUMENTDB_URI; avoid complexity of Entra ID flows for this demo.
- **Reason came from:** `prompt`
- **Evidence:** Readiness guidance: 'Default to SCRAM credential auth via DOCUMENTDB_URI for the sample; optionally add an enable Entra ID code path.'
- **When:** 2026-11-25T09:30:57+00:00

## D013 (build): I chose to use the existing cluster and not provision any Azure resources.

- **Instead of:** Provision a new cluster (Bicep/Terraform); Use existing cluster and do not provision
- **Because:** No infra changes are required and policy forbids provisioning; sample will run against provided cluster.
- **Reason came from:** `prompt`
- **Evidence:** Run environment: 'a Azure DocumentDB cluster is already provisioned and reachable ... DOCUMENTDB_URI' and run policy forbids Azure resource changes.
- **When:** 2026-11-25T09:31:00+00:00

## D014 (build): I chose REST API plus CLI scripts (seed and demo) in a single Node.js app.

- **Instead of:** REST API only; REST API + CLI seed/demo
- **Because:** This gives both programmatic and interactive ways to exercise the sample while keeping the project small and easy to run.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Builder will expose a small REST API: POST /transactions ... and a CLI script (npm run seed) to load sample data.'
- **When:** 2026-11-25T09:31:15+00:00

## D015 (build): I chose to create both a unique index on transactions.transactionRef and a compound index on { accountId:1, createdAt:-1 }.

- **Instead of:** transactionRef unique index only; transactionRef unique + accountId+createdAt compound index
- **Because:** Unique index enforces idempotency; compound index supports recent-activity queries per account efficiently.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'At minimum create a unique index on transactions.transactionRef. Also create an index on transactions.accountId and transactions.createdAt.'
- **When:** 2026-11-25T09:31:20+00:00

## D016 (build): I chose to change mongoose dependency to "^7.0.0" after npm reported no matching 7.9.3 version.

- **Instead of:** Keep mongoose@7.9.3 and retry; Change to a compatible range ^7.0.0
- **Because:** Using a caret range ^7.0.0 lets npm pick a valid 7.x release available in the registry and avoids our earlier incorrect pin; this is safer for installation in the ephemeral environment.
- **Reason came from:** `tool_result`
- **Evidence:** npm error: "No matching version found for mongoose@7.9.3."
- **When:** 2026-11-25T09:32:12+00:00

## D017 (build): I chose two collections: accounts (snapshot of balance) and transactions (immutable ledger documents).

- **Instead of:** Single collection with embedded transactions; Two collections: accounts (snapshot) + transactions (ledger)
- **Because:** This model cleanly separates immutable ledger entries from account balance snapshot, makes recent-activity queries efficient, and matches the prompt requirements for multi-document transactions.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'store every debit and credit as an immutable document in DocumentDB. Use multi-document transactions to atomically append the transaction and update the account balance snapshot.'
- **When:** 2026-11-25T09:32:43+00:00
