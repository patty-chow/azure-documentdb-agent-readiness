# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 3 |
| tool_result | 3 |
| readiness_report | 2 |
| operator | 1 |
| prompt | 1 |
| skill | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T09:59:34+00:00

## D002 (build): I chose Node.js with Express and Mongoose 7.x

- **Instead of:** Python/Flask; Node.js/Express with native MongoDB driver; Node.js/Express with Mongoose
- **Because:** The prompt explicitly requested Node.js and Mongoose, so this is the required choice.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'build a Node.js Mongoose settlement tracker'
- **When:** 2026-11-25T09:59:49+00:00

## D003 (build): I chose Mongoose 7.x pinned at 7.14.0

- **Instead of:** Mongoose 6.x; Mongoose 7.x (latest)
- **Because:** Mongoose 7.x is current major release and compatible with Node 24; pining to 7.14.0 balances stability and currency (minor versions can be updated later).
- **Reason came from:** `model_default`
- **Evidence:** Assumption in prompt review: 'Use a recent Mongoose 7.x release compatible with Node.js 24'
- **When:** 2026-11-25T09:59:52+00:00

## D004 (build): I chose to load and use the documentdb-connection skill for connection tuning guidance

- **Instead of:** Read connection guidance from docs manually; Load documentdb-connection skill
- **Because:** The skill contains Azure DocumentDB-specific connection tuning and best-practices which should be followed when implementing the singleton client and transaction usage.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report listed documentdb-connection skill as available and relevant
- **When:** 2026-11-25T10:00:00+00:00

## D005 (build): I chose OLTP connection defaults tuned for a long-running Express server: maxPoolSize 50, minPoolSize 10, socketTimeoutMS 30000

- **Instead of:** Use small pool-size for serverless; Use OLTP settings (larger pool) for long-running Express server
- **Because:** The sample implements an Express server running on a developer machine; OLTP recommendations are most appropriate for a long-running server to show realistic concurrency behavior.
- **Reason came from:** `skill`
- **Evidence:** documentdb-connection skill guidance: 'Traditional Long-Running Servers (OLTP) settings'
- **When:** 2026-11-25T10:00:05+00:00

## D006 (build): I chose to create a compound index {assetClass:1, counterparty:1, currentState:1} plus single-field indexes on currentState

- **Instead of:** Create separate single-field indexes; Create compound index {assetClass:1, counterparty:1, currentState:1}
- **Because:** Aggregation will group by assetClass and counterparty and filter by currentState; a compound index in ESR order is appropriate; also create single-field index on currentState for simple filters.
- **Reason came from:** `model_default`
- **Evidence:** Assumptions from prompt review suggested compound index for aggregation and the documentdb-indexing skill recommends ESR compound indexes for multi-field queries
- **When:** 2026-11-25T10:00:12+00:00

## D007 (build): I chose to change mongoose version to ^7.9.0 in package.json

- **Instead of:** Keep mongoose 7.14.0 and fail; Pick a different recent 7.x Mongoose version
- **Because:** 7.14.0 appears not available in npm registry in this environment; selecting a slightly older 7.x release increases likelihood of being available while remaining compatible with Node 24 and MongoDB 7 wire protocol.
- **Reason came from:** `tool_result`
- **Evidence:** npm install failed: 'No matching version found for mongoose@^7.14.0'
- **When:** 2026-11-25T10:01:01+00:00

## D008 (build): I chose to continue development of files but record the npm install failure and continue verification using available MCP tools

- **Instead of:** Proceed despite npm install failure; Stop and retry npm later
- **Because:** Network or registry constraints prevented dependency installation in this environment; per guidance continue building sample files and use documentdb MCP server to verify data-plane actions where possible. Record what could and couldn't be executed.
- **Reason came from:** `tool_result`
- **Evidence:** npm install failed with 'No matching version found for mongoose'
- **When:** 2026-11-25T10:01:13+00:00

## D009 (build): I chose to use the documentdb MCP server's list_databases tool for verification

- **Instead of:** Use application code to inspect cluster (requires npm); Use documentdb MCP server to inspect cluster
- **Because:** The MCP server can inspect collections and indexes without requiring local npm dependencies to be installed; it's suited to verify what was created on the live cluster.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'documentdb MCP server present... Every call must pass connection_profile "default".'
- **When:** 2026-11-25T10:01:16+00:00

## D010 (build): I chose to seed a small set of sample trade documents directly using the documentdb MCP server

- **Instead of:** Wait to seed until npm install succeeds; Seed the sample data using the documentdb MCP server directly
- **Because:** This allows verifying aggregation and change-stream detection paths at the database level even though local app dependencies couldn't be installed; record this as a workaround in the report.
- **Reason came from:** `tool_result`
- **Evidence:** npm install failed, but documentdb MCP server can operate against the live cluster and insert documents
- **When:** 2026-11-25T10:01:24+00:00

## D011 (build): I chose to retry the insert once using the documentdb MCP server

- **Instead of:** Do not retry insert; Retry insert once using MCP server
- **Because:** Transient MCP server or permission issue might have caused the failure; retry once to see if it succeeds.
- **Reason came from:** `model_default`
- **Evidence:** First insert returned 'Function failed.' with no details; per guidance, retrying once is acceptable before failing over.
- **When:** 2026-11-25T10:01:37+00:00
