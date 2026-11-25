# Documentation and tooling gaps: 06-omnichannel-interaction-history

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Mongoose driver version compatibility

- **What was missing:** Authoritative public guidance stating the recommended exact Mongoose/mongodb-driver version (or minimal tested version) for Node.js 24 and MongoDB wire protocol 7.0/8.0 on Azure DocumentDB.
- **Where the agent looked:** Readiness searches and skill documents; readiness findings flagged the missing guidance. Searches used Learn (terms: 'Mongoose version compatibility Node 24 MongoDB wire protocol 7.0') and the documentdb skills but found no pinned recommendation.
- **Effect on this build:** The builder used a model-default choice (^7.x). This leaves ambiguity and produces a decision recorded as 'model_default' rather than grounded in a public doc.
- **Suggested fix (learn_doc):** A short guidance page 'Driver compatibility and recommended versions' that lists supported Node versions, recommended Mongoose major/minor versions, and mapping to the cluster's supported MongoDB wire-protocol versions. Include example package.json snippets and a CI check that fails if an unsupported driver version is used.

## [high] Unit test template for samples (offline)

- **What was missing:** A lightly opinionated test template and guidance for writing unit tests that run without a live Azure DocumentDB cluster (using mongodb-memory-server or mock techniques).
- **Where the agent looked:** Searches for 'DocumentDB samples tests offline mongodb-memory-server' and installed sample guidance; no ready-to-copy test template was found for DocumentDB samples.
- **Effect on this build:** The sample contains no tests. Authors are likely to omit tests unless a ready template or a required checklist item exists.
- **Suggested fix (sample_or_quickstart):** Provide an example test directory with 2–3 Jest/Mocha tests that use mongodb-memory-server or sinon to mock Mongoose, plus instructions in README and an npm test script. Include a short demonstration for verifying schema validation, pagination logic, and aggregation without a live cluster.

## [medium] IaC example for Microsoft.DocumentDB/mongoClusters

- **What was missing:** A short, copy-pasteable Bicep/ARM and Terraform example showing how to deploy an Azure DocumentDB mongoClusters resource (vCore), with reasonable defaults (region, tier, storage) and how to output the connection string.
- **Where the agent looked:** Quickstart and deployment docs were consulted; while the provider docs exist, a small sample targeting gallery authors was not discoverable as a one-file example.
- **Effect on this build:** No IaC included; authors may ship samples that assume a pre-provisioned cluster. That reduces sample completeness for users who want a one-click reproduction.
- **Suggested fix (sample_or_quickstart):** A 'deploy-mongoCluster.bicep' and Terraform HCL example that sets region, tier (M30), storage, and outputs the SRV connection string; plus a short README section describing cost trade-offs and a note: 'Use az documentdb mongocluster list-connection-strings to retrieve the URI.'

## [medium] Driver pinning / lockfile discoverability

- **What was missing:** Guidance that the gallery checks for pinned dependencies should be node-aware (check package-lock.json or npm-shrinkwrap.json) rather than expecting requirements.txt.
- **Where the agent looked:** Team checklist and sample conventions; mismatch surfaced in the readiness review where requirements.txt was expected.
- **Effect on this build:** The sample committed package-lock.json which pins versions; the checklist's Python-centric wording caused an apparent unmet requirement.
- **Suggested fix (naming_or_disambiguation):** Update the gallery 'dependencies pinned' checklist to state per-language expectations (e.g., 'Node: commit package-lock.json or npm-shrinkwrap.json; Python: requirements.txt/poetry.lock').

## [low] Search endpoint expectations

- **What was missing:** Clear gallery guidance (or a rule) that only samples implementing search must include error handling for empty queries and for embedding-call failures, and an example of error messages and logging policy for such endpoints.
- **Where the agent looked:** No single public rule or sample-template was found that ties '/search' endpoint behavior to gallery publishing requirements.
- **Effect on this build:** The starter prompt did not request a /search endpoint and the builder did not add one; the checklist nevertheless contained expectations about search behavior which caused a mismatch.
- **Suggested fix (agent_kit_rule):** An agent-kit rule: 'If your sample implements a /search endpoint, include: 1) server-side validation returning 400 for empty queries, 2) try/catch around embedding service calls returning 502 with a brief message, 3) logs with full diagnostics to protected logs, and 4) example tests mocking embedding errors.'

