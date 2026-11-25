# Decision log

| Reason came from | Decisions |
|---|---|
| readiness_report | 6 |
| prompt | 2 |
| operator | 1 |
| model_default | 1 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T10:16:53+00:00

## D002 (build): I chose Node.js with Express and Mongoose (mongoose ^7.x) for the sample.

- **Instead of:** Python/Flask; Node.js/Express with Mongoose; Go with mongo-driver
- **Because:** Node.js + Mongoose is idiomatic for MongoDB-based apps, matches the prompt's request for a Node.js Mongoose service, and Node 24 is available in the run environment.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Builder will pick a recent Mongoose release compatible with Node 24 (e.g. mongoose ^7.x)'.
- **When:** 2026-11-25T10:17:11+00:00

## D003 (build): I chose to read the connection string from the environment variable DOCUMENTDB_URI at runtime and use SCRAM-SHA-256 as provided by the connection string.

- **Instead of:** Use Entra/AAD token-based auth (authMode=entra); Use connection string from DOCUMENTDB_URI env var
- **Because:** The run environment already provides a reachable cluster and connection string via DOCUMENTDB_URI; no need to implement token-based Entra auth in this small sample and the readiness report flagged missing Entra examples.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'Consume the connection string from DOCUMENTDB_URI as-is and use the recommended options: tls=true..., authMechanism=SCRAM-SHA-256, and set retryWrites=false.'
- **When:** 2026-11-25T10:17:15+00:00

## D004 (build): I chose not to provision any Azure resources and to use the existing cluster referenced by DOCUMENTDB_URI.

- **Instead of:** Provision a new Azure DocumentDB cluster via IaC; Do not provision and use the existing cluster provided via DOCUMENTDB_URI
- **Because:** Provisioning is unnecessary and disallowed; using the existing cluster keeps the sample small and avoids cost.
- **Reason came from:** `readiness_report`
- **Evidence:** Run environment: 'This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable.' and run policy: 'Azure resource changes allowed: False.'
- **When:** 2026-11-25T10:17:17+00:00

## D005 (build): I chose to store an immutable per-stage document in a single collection named 'audit_events' with fields paymentReference, stage, stageTimestamp, details.

- **Instead of:** Per-stage documents in single collection (embed events); Single document per payment with array of stages (embed stages)
- **Because:** Storing one document per stage aligns with the audit-trail, simplifies immutability enforcement, and matches the prompt's explicit requirement.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'writes an immutable document to DocumentDB at every stage of a cross-border payment lifecycle' and readiness report: 'Use the database named sample_banking_12 for everything this sample creates.'
- **When:** 2026-11-25T10:17:19+00:00

## D006 (build): I chose to define the compound index { paymentReference: 1, stageTimestamp: 1 } in the Mongoose schema and also create it via the documentdb MCP server and verify with explain().

- **Instead of:** Create only Mongoose indexes; Create index via Mongoose and also create/verify via documentdb MCP server
- **Because:** Creating via both ensures the sample will work even if schema-based auto-indexing is disabled, and the MCP server verification meets the guidance requirement.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report guidance: 'Create the compound index { paymentReference: 1, stageTimestamp: 1 } before running the timeline aggregation and verify it with the documentdb MCP server's explain operation.'
- **When:** 2026-11-25T10:17:23+00:00

## D007 (build): I chose to create the compound index via the documentdb MCP server (documentdb_create_index) and then run an explain to verify index usage.

- **Instead of:** Create index only with Mongoose autoIndex; Create index explicitly via documentdb MCP server and verify explain
- **Because:** Using the MCP server to create and verify the index satisfies the guidance and provides an authoritative explain() check.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report guidance: 'Create the compound index { paymentReference: 1, stageTimestamp: 1 } before running the timeline aggregation and verify it with the documentdb MCP server's explain operation.'
- **When:** 2026-11-25T10:18:19+00:00

## D008 (build): I chose to retry documentdb_create_index without passing connection_profile (omit it) on the second attempt.

- **Instead of:** Retry documentdb_create_index with connection_profile 'default' again; Retry without connection_profile set
- **Because:** A second attempt with a slightly different parameter set may succeed; per instructions stop after second attempt if it still fails.
- **Reason came from:** `model_default`
- **Evidence:** Previous attempt with connection_profile:'default' returned a generic Error; MCP server tools sometimes accept no explicit profile when 'default' is configured.
- **When:** 2026-11-25T10:18:25+00:00

## D009 (build): I chose to proceed using the index defined in the Mongoose schema and continue verification by running the aggregation; I will record that MCP create_index and explain verification could not be run due to the documentdb MCP tool failure.

- **Instead of:** Abort and require MCP tool functioning; Proceed using Mongoose schema index only and record MCP create_index as not_verified
- **Because:** The build must continue; Mongoose will ensure the index exists client-side (autoIndex) and the sample can still be demonstrated; the MCP server failure is recorded for reviewers to investigate.
- **Reason came from:** `tool_result`
- **Evidence:** Two attempts to call documentdb_create_index failed with generic errors.
- **When:** 2026-11-25T10:18:32+00:00

## D010 (build): I chose to run an automated immutability check script that attempts updateOne and findOneAndUpdate and verifies they are rejected by the application-layer guards.

- **Instead of:** Skip immutability verification; Run an automated immutability check against the live cluster
- **Because:** This verifies the key security guarantee of the sample: documents are immutable at the application layer.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report guidance: 'Test that updateOne / findOneAndUpdate / replaceOne are rejected in unit/integration tests.'
- **When:** 2026-11-25T10:18:53+00:00

## D011 (build): I chose to attempt documentdb_explain_operation via the documentdb MCP server to verify the aggregation uses the compound index.

- **Instead of:** Skip MCP explain verification; Attempt to run documentdb_explain_operation via MCP server to verify index usage
- **Because:** If the MCP server works for explain it gives authoritative index usage info; worth trying once.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'verify it with the documentdb MCP server's explain operation.'
- **When:** 2026-11-25T10:19:10+00:00
