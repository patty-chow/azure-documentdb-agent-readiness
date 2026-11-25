# Documentation and tooling gaps: 12-hospital-bed-occupancy-tracker

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Unit tests without live cluster

- **What was missing:** Guidance and example tests showing how to unit-test DocumentDB/Mongoose code without a live cluster (preferred patterns: mongodb-memory-server, fakered/mocks, or MCP gateway-based tests).
- **Where the agent looked:** documentdb-local-deployment skill, overall agent skills for DocumentDB, repository files (no tests found).
- **Effect on this build:** No unit tests were added; the sample contains runtime verification steps that require a live cluster. This reduces confidence for CI and reviewers and increases the manual verification burden.
- **Suggested fix (sample_or_quickstart):** A short page 'Testing DocumentDB samples offline' that includes: 1) an example using mongodb-memory-server with Mongoose and instructions to wire it into the sample's connect() during tests; 2) a small Jest test that stubs change stream events and asserts WardSummary updates; 3) an alternative using the DocumentDB Gateway Docker image and instructions and npm scripts to run integration tests. Include code snippets and a sample package.json test script.

## [high] Provide a minimal Bicep example for mongoClusters

- **What was missing:** A tiny IaC quickstart (Bicep or Terraform) showing how to provision a Microsoft.DocumentDB/mongoClusters resource with minimal, cost-conscious defaults (tier, region, storage).
- **Where the agent looked:** documentdb-azure-deployment skill and Microsoft Learn templates; the sample repo contained no IaC files.
- **Effect on this build:** The gallery sample has no IaC attachment; authors and users may target the wrong resource type (databaseAccounts) if they follow older Cosmos DB instructions. This increases the chance of provisioning the wrong service or producing an unprovisioned expectation gap.
- **Suggested fix (learn_doc):** A tiny 'iac/mongoCluster.bicep' example (parameters: location, sku/tier, serverVersion) plus short README text showing az deployment group create with the template, and a note: 'Use Microsoft.DocumentDB/mongoClusters — do not use databaseAccounts for vCore DocumentDB'.

## [high] Idempotent consumer pattern for DocumentDB change streams

- **What was missing:** A DocumentDB-specific example of idempotent change-stream consumption (dedupe/inbox pattern, uniqueness constraints, or per-event checkpointing) demonstrating how to avoid double-counting when events are replayed or reordered in multi-shard deployments.
- **Where the agent looked:** Azure architecture patterns (Idempotent Consumer) and change-stream docs; there is conceptual guidance but no short DocumentDB-oriented sample.
- **Effect on this build:** The sample's recompute approach is idempotent by accident; other apps might implement naive $inc deltas and would be at risk of double-counting without idempotency guidance.
- **Suggested fix (learn_doc):** A 'Change-stream consumer patterns' page showing 1) full-recompute approach (pros/cons), 2) delta-$inc with pre-images or stored previous-state approach, and 3) dedupe/inbox table pattern, each with small code snippets using Mongoose/native driver.

## [medium] Resume token persistence guidance

- **What was missing:** A concrete example that shows persisting resume tokens (change._id) into a small control collection and using resumeAfter when reopening the stream, including sample code for Mongoose/native driver.
- **Where the agent looked:** Change-stream docs in Microsoft Learn and documentdb skills; public docs describe resume tokens but lack a short 'store and resume' code example for Mongoose-based watchers.
- **Effect on this build:** The sample's change-stream watcher does not persist resume tokens; if the watcher restarts it may reprocess events and the sample lacks a durable checkpoint example for authors to copy.
- **Suggested fix (agent_kit_rule):** An agent-kit rule and a short code snippet: 1) after processing an event, write { watcherId, lastResumeToken, lastProcessedTs } to a control collection; 2) on startup, query control collection and pass resumeAfter: token to collection.watch(); include failure/retry semantics and expected schema for the control document.

## [medium] Clarify monitoring/metrics guidance (RUs vs vCore)

- **What was missing:** A short naming/disambiguation note explaining that Azure DocumentDB (vCore/mongoClusters) is billed by compute tier (M-sizes) and not by Cosmos DB RUs, and list the recommended metrics to monitor for DocumentDB clusters (CPU, memory, IOPS, connections) plus pointers to slow-query logging and explain-based analysis.
- **Where the agent looked:** documentdb-monitoring skill and Microsoft Learn; agent readiness found confusion in cold answers.
- **Effect on this build:** Risk that authors will monitor or reason about RUs (a Cosmos DB concept) and misinterpret cluster health or plan scaling incorrectly.
- **Suggested fix (naming_or_disambiguation):** A one-paragraph callout on the main quickstart: 'Azure DocumentDB (mongoClusters) uses vCore compute tiers (Mxx) and is not RU-based — monitor CPU/memory/IOPS and enable diagnostic settings + slow-query logs. See sample monitoring checklist.'

