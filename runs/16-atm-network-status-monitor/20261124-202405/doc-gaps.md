# Documentation and tooling gaps: 16-atm-network-status-monitor

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] readPreference/readConcern mapping

- **What was missing:** Explicit public guidance mapping MongoDB readPreference/readConcern options to recommended settings for Azure DocumentDB clusters.
- **Where the agent looked:** Searches for 'Azure DocumentDB readPreference readConcern' and discovered_practices (the earlier discovery noted no authoritative mapping page). I also used Microsoft Learn quickstarts and compatibility pages.
- **Effect on this build:** Agents and builders may not know which readConcern/readPreference to choose for correctness vs latency. The sample did not set explicit read preferences and left defaults unspecified.
- **Suggested fix (learn_doc):** A short Learn page titled 'Recommended readPreference and readConcern for Azure DocumentDB (MongoDB-compatible)'. Sections: (1) recommended defaults for status/summary workloads; (2) guidance when to use primary/majority; (3) examples of mongoose.connect options and example code; (4) note about latency tradeoffs and compatibility matrix. Include examples for single-shard and multi-shard clusters.

## [high] Seed script idempotency for heartbeats

- **What was missing:** Guidance and a template for making seed scripts idempotent (avoid inserting duplicate sample records on repeated runs).
- **Where the agent looked:** Inspected seed.js and documentdb-local-deployment skill resources. No dedicated seed-idempotency template was present.
- **Effect on this build:** The seed claims idempotency in README but inserts duplicate heartbeat documents when run multiple times; this could confuse users and tests that assume a stable dataset.
- **Suggested fix (sample_or_quickstart):** A short sample-seed pattern page showing idempotent seeding approaches: use deterministic _id or a seedId, upsert semantics for sample documents, or explicit 'seedVersion' fields to detect already-applied seed runs. Include a small seed helper library for agent kit sample templates.

## [high] Pinning dependencies and reproducible installs

- **What was missing:** Agent guidance / rule that samples must commit lockfiles or pin exact dependency versions to avoid registry mismatch failures in CI.
- **Where the agent looked:** Inspected package.json and build events (npm install failures). No specific agent-kit rule enforced pinned dependencies for Node samples.
- **Effect on this build:** npm install failed twice in this run due to an unavailable dev dependency version; build could not run seed/start/tests. This blocks verification in CI-like environments.
- **Suggested fix (agent_kit_rule):** Agent-kit rule: 'Node samples must check in package-lock.json or pin exact package versions in package.json for sample releases; CI should run npm ci against committed lockfile.' Provide a short doc explaining when to use ^ ranges vs exact versions for samples.

## [high] Change-stream resume tokens and multishard note

- **What was missing:** Prominent README guidance about storing resume tokens and enabling multishard change-stream feature if needed.
- **Where the agent looked:** README and code (no mention), Microsoft Learn change-streams docs were found but not surfaced in the sample README.
- **Effect on this build:** Sample uses change streams but does not persist resume tokens nor document the multishard caveat; this could cause event loss on restarts or confusion on multishard clusters.
- **Suggested fix (learn_doc):** Add a README section 'Change streams and resiliency' summarizing: (1) how to persist resume tokens (store change._id after processing), (2) example code snippet, (3) the multishard feature flag requirement and how to enable it in the portal/CLI, (4) retention considerations.

## [medium] .env.example completeness

- **What was missing:** .env.example did not list all env vars the sample reads (e.g., SEED_ATMS, PORT).
- **Where the agent looked:** Inspected app/ files (seed.js, index.js) and .env.example in the repo.
- **Effect on this build:** Builders copying .env.example may miss configuring seed size or the port and will not see all configurable options documented in a template.
- **Suggested fix (agent_kit_rule):** Agent-kit rule: 'Every sample must include a .env.example listing every environment variable read by the application code with placeholders and short descriptions.' Example content for this sample: DOCUMENTDB_URI, DATABASE_NAME, AVAILABILITY_THRESHOLD, SEED_ATMS, PORT, optional local gateway URI. Include a small script or rule that fails CI if a variable is used in code but missing in .env.example.

## [medium] IaC snippet for Microsoft.DocumentDB/mongoClusters

- **What was missing:** A minimal Bicep/Terraform example that shows how to declare the vCore mongoClusters resource (Microsoft.DocumentDB/mongoClusters) for builders who want to supply IaC.
- **Where the agent looked:** Microsoft Learn templates for mongoClusters were found in readiness work but the sample repo contains no IaC.
- **Effect on this build:** Builders who expect a sample to include optional provisioning code must create it themselves; missing IaC increases manual steps to reproduce the environment.
- **Suggested fix (sample_or_quickstart):** A short Bicep file snippet and a one-file Terraform/AzAPI example that creates a small M10/M30 mongoCluster with parameters for tier, storage, and firewall. Include comments that emphasize correct resource type (Microsoft.DocumentDB/mongoClusters) and warn not to use legacy databaseAccounts resource for vCore clusters.

## [low] Decision guidance discoverability (atm_status pattern)

- **What was missing:** The builder used a model_default rationale to keep per-ATM state; data-modeling guidance would cover this but must be discoverable to agents at decision time.
- **Where the agent looked:** documentdb-data-modeling skill exists but was loaded after the decision in this run.
- **Effect on this build:** A decision made from model_default carries risk if the agent did not find the explicit data-modeling guidance before choosing. The code implemented the pattern, but agents should find authoritative guidance earlier.
- **Suggested fix (discoverability):** Make 'per-entity current-state' guidance more prominent in the agent-kit index and include a short checklist item 'Use per-entity state collection with unique id' in sample templates so agents will find it before making decisions.

