# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 2 |
| skill | 2 |
| readiness_report | 2 |
| operator | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T07:08:26+00:00

## D002 (build): I chose Python with FastAPI targeting modern CPython (3.11/3.10)

- **Instead of:** Node.js/TypeScript; Python (Flask); Python (FastAPI)
- **Because:** Prompt review assumptions and run environment indicated Python and FastAPI; FastAPI provides a small, testable HTTP surface and fits single-file examples
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Target modern CPython 3.11 (or 3.10)'; App surface: 'small FastAPI-based HTTP service'
- **When:** 2026-11-25T07:08:42+00:00

## D003 (build): I chose to read the cluster connection string from the environment variable DOCUMENTDB_URI at runtime

- **Instead of:** Read connection string from code/config file; Read from environment variable DOCUMENTDB_URI; Prompt user for connection string at runtime
- **Because:** Security and run-policy constraints prohibit writing secrets to files; environment variable is standard and documented in readiness report
- **Reason came from:** `skill`
- **Evidence:** Readiness report: 'Read the cluster's connection string from DOCUMENTDB_URI at runtime'
- **When:** 2026-11-25T07:08:45+00:00

## D004 (build): I chose not to provision any Azure resources and use the existing, reachable cluster

- **Instead of:** Provision cluster via az/ARM/Bicep; Provision nothing; use existing cluster
- **Because:** Provisioning is disallowed and unnecessary; use provided cluster for verification
- **Reason came from:** `prompt`
- **Evidence:** Run policy: 'Azure resource changes allowed: False' and skill_md: 'a cluster is already provisioned and reachable'
- **When:** 2026-11-25T07:08:47+00:00

## D005 (build): I chose to compute max drawdown client-side in Python after retrieving the ordered P&L time series from the server

- **Instead of:** Compute drawdown purely server-side with aggregation pipeline; Compute drawdown client-side after retrieving ordered P&L series
- **Because:** No canonical tested server-side pipeline exists in docs; safer and clearer to compute drawdown deterministically in client code and still run optimized server-side aggregations for counts/averages
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'One information gap: a fully worked ... server-side aggregation example for max drawdown is not present'
- **When:** 2026-11-25T07:08:51+00:00

## D006 (build): I chose to use a singleton MongoClient (module-level) reused across the FastAPI app

- **Instead of:** Create one MongoClient per request; Create a singleton MongoClient reused across the app
- **Because:** Avoid pool exhaustion and connection overhead; aligns with driver best practices
- **Reason came from:** `skill`
- **Evidence:** documentdb-driver skill guidance: 'singleton MongoClient' best practice (skill in available_skills)
- **When:** 2026-11-25T07:08:54+00:00

## D007 (build): I chose to create a compound index {strategy_id: 1, timestamp: -1} on the journal collection

- **Instead of:** Compound index {strategy_id:1, timestamp:1}; Separate indexes on strategy_id and timestamp; No index
- **Because:** Optimizes time-ordered per-strategy queries and recent-first reads; align with readiness guidance
- **Reason came from:** `readiness_report`
- **Evidence:** Assumption from prompt review: 'create a compound index on {strategy_id:1, timestamp:1}'; readiness_report guidance: 'choose compound indexes such as {strategy_id:1, timestamp:-1} for time-ordered per-strategy aggregation'
- **When:** 2026-11-25T07:09:02+00:00
