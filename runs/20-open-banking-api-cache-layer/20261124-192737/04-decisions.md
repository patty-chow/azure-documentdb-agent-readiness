# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 3 |
| readiness_report | 2 |
| model_default | 2 |
| operator | 1 |
| skill | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T07:43:09+00:00

## D002 (build): I chose Node.js with Express and Mongoose (Node 24, Mongoose ^7) as the implementation platform.

- **Instead of:** Python/Flask; Node.js/Express; Go/Fiber
- **Because:** The prompt asked explicitly for a Node.js Mongoose caching layer and an Express-compatible middleware is the most immediate demo surface for Node developers.
- **Reason came from:** `prompt`
- **Evidence:** <assumptions_from_prompt_review> suggested 'Builder will implement as a single-process Node.js library/middleware' and 'Use Mongoose ^7'.
- **When:** 2026-11-25T07:43:40+00:00

## D003 (build): I chose Mongoose ^7.5.0 as the dependency to use (pinned as ^7.5.0 in package.json).

- **Instead of:** Mongoose ^9; Mongoose ^7; MongoDB native driver only
- **Because:** Mongoose ^7 is compatible with Node 24 and provides schema/index convenience for TTL index creation; pinning to ^7.5.0 gives reproducibility while staying current in 7.x line.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use Mongoose ^7' and readiness_report guidance to 'follow Mongoose quickstart connection example'.
- **When:** 2026-11-25T07:43:42+00:00

## D004 (build): I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime and not write any secrets to files.

- **Instead of:** Embed credentials in files; Read DOCUMENTDB_URI from environment; Use Azure Key Vault
- **Because:** Security best practice and explicit instruction in the run environment description; keeps sample safe for cloning.
- **Reason came from:** `skill`
- **Evidence:** Readiness report: 'Read the cluster connection string from DOCUMENTDB_URI and connect with Mongoose' and 'Never write a secret... Read them from environment variables'.
- **When:** 2026-11-25T07:43:45+00:00

## D005 (build): I chose not to provision any Azure resources and to use the existing cluster referenced by DOCUMENTDB_URI.

- **Instead of:** Provision cluster with Bicep/Terraform/azd; Do not provision; use existing cluster
- **Because:** Provisioning is disallowed and unnecessary; the environment already contains a reachable cluster for verification.
- **Reason came from:** `prompt`
- **Evidence:** Run policy: 'Azure resource changes allowed: False' and the skill run environment: 'a cluster is already provisioned and reachable; DOCUMENTDB_URI provided'.
- **When:** 2026-11-25T07:43:48+00:00

## D006 (build): I chose a per-document expiresAt field with a TTL index created via schema.index({ expiresAt: 1 }, { expireAfterSeconds: 0 }).

- **Instead of:** expiresAt TTL index (per-document expiry); createdAt + expireAfterSeconds static TTL
- **Because:** Per-document expiry lets the code set different TTLs per cached response and matches the sample requirement to implement TTL semantics.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report guidance: 'For Mongoose use CacheSchema.index({ expiresAt: 1 }, { expireAfterSeconds: 0 }) if you want per-document expiry.'
- **When:** 2026-11-25T07:43:51+00:00

## D007 (build): I chose to implement both an Express-compatible middleware and an exported wrapper function that can be used around an HTTP client (axios).

- **Instead of:** Middleware only; HTTP-client wrapper only; Both middleware and wrapper
- **Because:** Providing both surfaces makes the sample broadly useful: middleware for routing scenarios and wrapper for programmatic outbound calls; both are useful for open banking caching patterns.
- **Reason came from:** `model_default`
- **Evidence:** Assumptions: 'Implement as an Express-compatible middleware plus an exported wrapper function' from prompt review.
- **When:** 2026-11-25T07:43:54+00:00

## D008 (build): I chose demo-friendly defaults: TTL = 5 seconds and stale-while-revalidate window = 10 seconds for the included demo; the library supports configurable TTLs for production use.

- **Instead of:** TTL = 60s, staleWindow = 300s; TTL = 5s (demo), staleWindow = 10s (demo); No defaults; require user to set
- **Because:** Short TTLs let the one-shot demo show fresh, stale, and background refresh behavior without long waits; production usage should set longer values and is configurable.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'Default TTL and stale window values: builder must choose sensible defaults' and the requirement to demonstrate stale-while-revalidate behavior in a short-running demo.
- **When:** 2026-11-25T07:43:57+00:00

## D009 (build): I chose to verify the sample against the live cluster reachable via DOCUMENTDB_URI during build and not to include mongodb-memory-server tests.

- **Instead of:** Include unit tests with mongodb-memory-server; Rely on live cluster for verification; Use Docker local gateway
- **Because:** Using the live cluster matches the run environment and the MCP server is available for inspection; adding mongodb-memory-server would increase dependencies and complexity for this sample.
- **Reason came from:** `readiness_report`
- **Evidence:** Run environment: 'a DocumentDB cluster is already provisioned and reachable' and readiness_report: 'test against the live cluster'. Also run_policy forbids provisioning new resources but allows networked access.
- **When:** 2026-11-25T07:44:01+00:00
