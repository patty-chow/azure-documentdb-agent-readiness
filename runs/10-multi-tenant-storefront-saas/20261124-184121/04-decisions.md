# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 2 |
| model_default | 2 |
| readiness_report | 2 |
| operator | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T05:39:51+00:00

## D002 (build): I chose Node.js with Mongoose and a minimal Express surface for the sample.

- **Instead of:** Python/Flask; Node.js with Mongoose and Express; Go with Mongo driver
- **Because:** The prompt explicitly requested a Node.js Mongoose app; Express provides a familiar minimal API surface for samples.
- **Reason came from:** `prompt`
- **Evidence:** "build a Node.js Mongoose app" from the sample prompt.
- **When:** 2026-11-25T05:40:09+00:00

## D003 (build): I chose Mongoose 7.x (specifically ^7.4.0) as the driver version to depend on in package.json.

- **Instead of:** Mongoose 9.x (newer); Mongoose 7.x (legacy)
- **Because:** Mongoose 7.x is compatible with Node 24 and was the prompt-review assumption; it avoids potential breaking changes of major newer versions while staying modern.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from the prompt review: "Use a modern stable Mongoose (e.g., Mongoose 7.x) compatible with Node 24".
- **When:** 2026-11-25T05:40:12+00:00

## D004 (build): I chose to read the connection string from process.env.DOCUMENTDB_URI at runtime.

- **Instead of:** Read DB connection string from a file; Read DB connection string from environment variable DOCUMENTDB_URI
- **Because:** Security and run-policy: never write secrets to files. The guidance explicitly instructs to use DOCUMENTDB_URI.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness guidance: "Read the cluster connection string from process.env.DOCUMENTDB_URI and pass it unchanged to mongoose.connect();"
- **When:** 2026-11-25T05:40:15+00:00

## D005 (build): I chose not to provision any Azure resources and to use the existing cluster referenced by DOCUMENTDB_URI.

- **Instead of:** Create resources on Azure (provision cluster); Do not provision; use existing cluster in DOCUMENTDB_URI
- **Because:** Run policy forbids Azure writes; sample guidance expects use of the provided cluster.
- **Reason came from:** `prompt`
- **Evidence:** Run policy: "Azure resource changes allowed: False." Also the skill_md states an existing cluster is reachable and its connection string is in DOCUMENTDB_URI.
- **When:** 2026-11-25T05:40:17+00:00

## D006 (build): I chose not to set a shard key in this sample and only implement tenantId as a required field with compound indexes (tenantId, sku) and (tenantId, createdAt).

- **Instead of:** Use tenantId only as index; Also set tenantId as shard key
- **Because:** Sharding would require cluster-level operations and provisioning; for a sample demonstrating repository-layer tenant isolation it's sufficient to enforce tenantId and create compound indexes as requested.
- **Reason came from:** `model_default`
- **Evidence:** Prompt required tenantId field and compound indexes. No provisioning allowed to implement sharding, and readiness report left shard key unspecified.
- **When:** 2026-11-25T05:40:20+00:00

## D007 (build): I chose to enforce tenant isolation primarily in a repository layer and also include a small Mongoose plugin that throws if tenantId is omitted from queries/mutations.

- **Instead of:** Enforce tenant isolation with only Mongoose pre middleware; Enforce tenant isolation in a repository layer and also add a Mongoose safety plugin
- **Because:** A repository layer is explicit and clear for sample readers; adding a plugin provides a defense-in-depth guard against accidental cross-tenant queries during development and tests.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness guidance: "Enforce tenant isolation centrally: require tenantId on every repository method and inject tenantId into query filters (or enforce via Mongoose pre middleware) so no repository call can return or mutate documents for a different tenant."
- **When:** 2026-11-25T05:40:33+00:00
