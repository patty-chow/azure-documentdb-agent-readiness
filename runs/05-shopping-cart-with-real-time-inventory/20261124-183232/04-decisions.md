# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 2 |
| operator | 1 |
| prompt | 1 |
| skill | 1 |
| readiness_report | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T05:16:55+00:00

## D002 (build): I chose Node.js with Express and Mongoose (Mongoose 7.x) for the sample app.

- **Instead of:** Python/Flask; Node.js/Express + Mongoose; Go + MongoDB driver
- **Because:** The prompt explicitly requests Node.js and Mongoose; Express is the common minimal HTTP framework to expose the API.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'build a Node.js cart service using Mongoose'
- **When:** 2026-11-25T05:17:26+00:00

## D003 (build): I chose to read the connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Read credentials from a file; Read DOCUMENTDB_URI from environment variable; Use Managed Identity / OIDC
- **Because:** Safe practice: do not write secrets into repo; README and .env.example will document env usage.
- **Reason came from:** `skill`
- **Evidence:** Skill run environment: 'connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time.'
- **When:** 2026-11-25T05:17:29+00:00

## D004 (build): I chose to use the existing cluster and not provision any Azure resources.

- **Instead of:** Provision cluster via Bicep/Terraform/az (create new); Use existing cluster (no provisioning)
- **Because:** Run policy disallows resource changes; the sample should target the existing cluster.
- **Reason came from:** `readiness_report`
- **Evidence:** Run environment: 'a cluster is already provisioned and reachable' and run policy forbids Azure writes.
- **When:** 2026-11-25T05:17:33+00:00

## D005 (build): I chose to use Mongoose optimisticConcurrency (versionKey __v) and explicit retry loop for transaction conflicts.

- **Instead of:** Use Mongoose automatic __v versionKey optimisticConcurrency; Implement manual version field and conditional updates; Use MongoDB transactions without versioning
- **Because:** Using Mongoose built-in optimisticConcurrency keeps code concise and matches prompt requirement; add retry loop to surface clear errors when stock exhausted.
- **Reason came from:** `model_default`
- **Evidence:** Prompt: 'Handle optimistic locking with a version field'; Mongoose supports optimisticConcurrency using versionKey.
- **When:** 2026-11-25T05:17:36+00:00

## D006 (build): I chose to create minimal, practical indexes: index on Inventory.sku and Cart.userId.

- **Instead of:** Create many indexes including compound and vector; Create minimal indexes: productId on inventory, userId on cart; Omit index creation (rely on _id)
- **Because:** Keep sample small while demonstrating index creation; SKU and userId cover common lookup patterns used in sample.
- **Reason came from:** `model_default`
- **Evidence:** Assumption in prompt review: minimal indexes needed for demonstrated queries. documentdb-indexing skill: create single-field indexes for query patterns.
- **When:** 2026-11-25T05:17:39+00:00
