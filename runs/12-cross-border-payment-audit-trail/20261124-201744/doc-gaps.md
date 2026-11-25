# Documentation and tooling gaps: 12-cross-border-payment-audit-trail

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] MCP management-tool availability and fallback

- **What was missing:** Clear documentation about MCP management tool opt-in (ENABLE_MANAGEMENT_TOOLS) and recommended driver-based fallback when MCP is not available. The MCP tool returned 'Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true to opt in.' but the sample had no documented fallback.
- **Where the agent looked:** documentdb-mcp-setup skill docs and events.jsonl show the tool error; search for MCP opt-in docs returned the skill pages but no prominent quickstart note about default opt-out and fallbacks.
- **Effect on this build:** The builder attempted MCP create_index twice and both failed, leaving index creation unverified on the server. This forced reliance on Mongoose-declared indexes and left explain() showing COLLSCAN for the sample.
- **Suggested fix (discoverability):** Add a short note to the MCP setup and index-creation quickstart: (a) MCP management operations are opt-in by environment variable ENABLE_MANAGEMENT_TOOLS; (b) if MCP is not available, the sample should call collection.createIndexes(...) via the official driver as a fallback; include a copy-paste snippet for that fallback.

## [high] Node.js Entra (Azure AD) auth snippet for Mongo driver

- **What was missing:** A ready-to-copy example showing how to obtain a Microsoft Entra (Azure AD) access token in Node.js and use it with the Mongo driver / Mongoose for clusters configured to use Entra authentication.
- **Where the agent looked:** Searched documentdb-security skill and public Learn docs; no clear Node.js copy-paste example was found.
- **Effect on this build:** Builder defaulted to using DOCUMENTDB_URI (SCRAM credentials) rather than implementing an Entra flow; adding a snippet would make it easy to add Entra auth in future samples and would reduce authors reinventing the steps.
- **Suggested fix (agent_kit_rule):** Add a small 'Node.js + Entra Auth' snippet to documentdb-security and documentdb-connection skills: show how to request an access token (MSAL), how to format it for use with the Mongo driver or the cluster authMode, and an example for mongoose.connect that uses the token. Include notes about when clusters must be configured for Entra auth.

## [high] Unit testing guidance for samples (local Gateway / in-memory DB)

- **What was missing:** A recommended pattern and example for authoring unit tests that do not require a live DocumentDB cluster: either a local Gateway docker-compose example for CI or an in-memory MongoDB approach documented for Node.js samples.
- **Where the agent looked:** documentdb-local-deployment skill and general README — local gateway docs exist but no concise test recipe for Node.js test suites was found.
- **Effect on this build:** The sample's test/verification scripts run against the live cluster. Without a small, documented offline test pattern, authors will ship tests that require credentials or a reachable cluster.
- **Suggested fix (learn_doc):** A short 'Testing' page: two recommended approaches: (1) use the DocumentDB local Gateway Docker image and a docker-compose snippet with ports and TLS options aimed at CI; (2) provide an example using mongodb-memory-server with caveats (feature differences). Include example package.json test scripts and a sample jest/mocha test that runs offline.

## [high] Index creation fallback example

- **What was missing:** A concise code snippet demonstrating a driver-based createIndexes fallback for samples when MCP index creation is not available.
- **Where the agent looked:** documentdb-indexing and documentdb-mcp-setup skill docs; index-creation via MCP is documented but a clear 'if MCP fails, call this' snippet was not obvious in the quickstarts.
- **Effect on this build:** The lack of a clear fallback led the builder to rely on Mongoose schema-index declaration only; explain() showed COLLSCAN and index usage was not guaranteed.
- **Suggested fix (mcp_tool_or_description):** Add a single-file snippet to the indexing quickstart showing: (a) how to call AuditEvent.collection.createIndexes([...]) safely and idempotently from seed/startup; (b) how to wait for completion and run explain(); (c) how to surface helpful error messages.

## [medium] Mongoose strict-mode & DocumentDB guidance

- **What was missing:** No Azure-DocumentDB-specific public guidance on Mongoose's strict mode and how schema strictness interacts with DocumentDB (examples showing explicit strict:true usage and common pitfalls).
- **Where the agent looked:** Searched installed skills (documentdb-data-modeling, documentdb-driver) and public Learn queries for 'Azure DocumentDB Mongoose schema validation strict mode' (no service-specific guidance found).
- **Effect on this build:** The sample uses Mongoose required fields and enum but does not explicitly set strict mode. An agent could not confirm whether explicit strict-mode settings are recommended for Azure DocumentDB, so the agent left default behavior implicit.
- **Suggested fix (learn_doc):** A short page in the Node.js/Mongoose quickstart: explain Mongoose strict:true, show a minimal schema example with strict enabled, show how immutable fields (createdAt) and enums interact with DocumentDB, and recommend what tests to run. Include a one-line example to add to schema options.

## [medium] Agent guidance for retries on writes

- **What was missing:** A short exemplar retry wrapper with exponential backoff + jitter and error classification for transient vs permanent errors in the DocumentDB context.
- **Where the agent looked:** documentdb-connection skill; it explains retries conceptually but lacks a small copy-paste Node.js snippet for writes.
- **Effect on this build:** No retry logic was implemented in the sample; authors need a short, battle-tested snippet to avoid implementing fragile ad-hoc retries.
- **Suggested fix (sample_or_quickstart):** Add a small Node.js helper module 'retry-writes.js' demonstrating exponential backoff + jitter, classification of retryable errors, and an example usage around an insert/upsert call.

