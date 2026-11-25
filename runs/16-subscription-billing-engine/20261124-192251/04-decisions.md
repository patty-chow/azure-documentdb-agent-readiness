# Decision log

| Reason came from | Decisions |
|---|---|
| readiness_report | 4 |
| operator | 1 |
| prompt | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T07:22:05+00:00

## D002 (build): I chose Node.js with Mongoose 7.x (pin to 7.7.0)

- **Instead of:** Node.js + Mongoose 7.x; Node.js + Mongoose 9.x; TypeScript with Mongoose
- **Because:** Mongoose 7.x is widely compatible with MongoDB 7 wire protocol and matches the prompt review assumption; it keeps the sample simpler than introducing TypeScript or a newer major release with fewer tested docs in readiness report.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Builder will use a modern Mongoose 7.x compatible with Node 24"
- **When:** 2026-11-25T07:22:22+00:00

## D003 (build): I chose to read the connection string from environment variable DOCUMENTDB_URI at runtime

- **Instead of:** Read connection string from a config file; Read connection string from environment variable DOCUMENTDB_URI; Use Azure Entra authentication
- **Because:** It matches the readiness guidance, keeps secrets out of source, and is easiest for users to run the sample against an existing cluster.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report instruction: "Read DOCUMENTDB_URI at runtime from an environment variable in the sample (process.env.DOCUMENTDB_URI)"
- **When:** 2026-11-25T07:22:34+00:00

## D004 (build): I chose not to provision resources; the sample uses the existing cluster and includes no provisioning actions

- **Instead of:** Provision a cluster as part of the sample (Bicep/Terraform); Do not provision — use existing cluster and provide IaC as files only
- **Because:** Provisioning is disallowed by policy and the run environment already provides a reachable cluster; writing provisioning code would be unverified and possibly refused.
- **Reason came from:** `readiness_report`
- **Evidence:** Run policy: "Azure resource changes allowed: False." and readiness report guidance that cluster is provided
- **When:** 2026-11-25T07:22:37+00:00

## D005 (build): I chose to create a unique index on chargeEvents.idempotencyKey (unique:true) and also index customerId

- **Instead of:** Unique index on chargeEvents.idempotencyKey; Partial unique index where idempotencyKey exists; No unique index, check in application logic
- **Because:** A unique DB index is the most reliable way to prevent double-billing under concurrency; application-level checks alone are race-prone.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report instruction: "Enforce idempotency by creating a unique index on the idempotencyKey"
- **When:** 2026-11-25T07:22:39+00:00

## D006 (build): I chose to create a TTL index on entitlement.expiresAt with expireAfterSeconds: 0

- **Instead of:** TTL on entitlement.trialExpiresAt; TTL on entitlement.expiresAt with expireAfterSeconds:0
- **Because:** Using an expiresAt canonical field and expireAfterSeconds:0 matches recommendations and allows immediate expiry when the UTC timestamp passes.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report example: "db.entitlements.createIndex({ trialExpiresAt: 1 }, { expireAfterSeconds: 0 })"
- **When:** 2026-11-25T07:22:48+00:00
