# Documentation and tooling gaps: 01-unified-customer-profile-store

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Distinct deployment resource guidance (mongoClusters vs databaseAccounts)

- **What was missing:** Clear, prominent documentation that distinguishes the vCore-managed Azure DocumentDB cluster resource (Microsoft.DocumentDB/mongoClusters) from older Cosmos DB databaseAccounts, including the correct ARM/Bicep/Terraform resource types and CLI groups (az documentdb vs az cosmosdb).
- **Where the agent looked:** Microsoft Learn pages for DocumentDB (overview, templates), az CLI docs, and readiness findings (service_confusions).
- **Effect on this build:** Risk of choosing the wrong IaC resource type or CLI commands; the builder did not include IaC and the readiness findings flagged this confusion. If a builder tried to add IaC with the wrong resource type they would deploy Cosmos DB RU accounts instead of vCore Mongo clusters.
- **Suggested fix (naming_or_disambiguation):** A short 'Which resource to use' page or a top-note on the mongoClusters and databaseAccounts docs that: 1) defines when to use Microsoft.DocumentDB/mongoClusters vs Microsoft.DocumentDB/databaseAccounts; 2) shows exact Bicep/ARM snippet for creating a mongoClusters resource; 3) shows the az CLI group (az documentdb mongocluster) and example commands; 4) references Terraform/AVM modules for mongoClusters. Add a quick-check script that warns if templates use databaseAccounts when a sample declares it's for vCore DocumentDB.

## [high] Azure CLI and Bicep examples for vCore clusters

- **What was missing:** Copy-paste ready examples and a short guide showing az documentdb mongocluster commands and the Bicep ARM snippet for Microsoft.DocumentDB/mongoClusters (including tier parameter examples like M30).
- **Where the agent looked:** az CLI docs, DocumentDB quickstarts, readiness findings (Q02, Q03).
- **Effect on this build:** Without an authoritative quick example a sample author may include the wrong CLI commands or resource types in a README or IaC sample, causing user errors and wrong resource creation.
- **Suggested fix (learn_doc):** A small page 'Provision a vCore DocumentDB cluster' containing: az documentdb mongocluster create examples (with --tier M30), a Bicep snippet for Microsoft.DocumentDB/mongoClusters, and a Terraform AVM module example; include notes on required permissions and minimal cost defaults.

## [high] Default retry/backoff guidance and a small retry helper

- **What was missing:** A short recommended defaults snippet for retries/backoff for DocumentDB Mongo drivers (honor 429 Retry-After and use bounded exponential backoff with jitter) and a small example helper authors can copy into samples.
- **Where the agent looked:** Design throttling docs and connection guidance; no single snippet of defaults for Node/Mongoose was provided to copy into samples.
- **Effect on this build:** The sample does not implement retry/backoff; missing guidance makes builders less likely to handle throttling correctly, potentially causing transient failures or retry storms in produced samples.
- **Suggested fix (agent_kit_rule):** An agent-kit rule and a one-file 'retry.js' helper that implements bounded exponential backoff with jitter and respects Retry-After; quickstart shows how to call the helper from an upsert path (example in Node).

## [medium] Canonical Mongoose/driver version guidance for Node 24 samples

- **What was missing:** A single recommended Mongoose version (and compatible mongodb driver) for Node 24 in the quickstart so sample authors can pin confidently.
- **Where the agent looked:** Quickstart and readiness findings; no single top-line recommendation discovered.
- **Effect on this build:** The builder picked Mongoose 7.x; authors may choose differing major versions. Lack of explicit recommendation risks inconsistent dependency choices across samples and occasional install failures.
- **Suggested fix (discoverability):** Add a one-line 'Recommended client stack' box to the Mongoose quickstart with 'Mongoose 7.x (tested with Node 24) and driver X.Y', plus an example package.json snippet showing exact pinned versions and how to update them.

## [medium] Seed script idempotency and index creation best practice

- **What was missing:** A short sample-pattern that shows idempotent seed scripts which create indexes via a migration step (or idempotent syncIndexes) and that recommend whether index creation should be done via a migration tool vs syncIndexes at startup.
- **Where the agent looked:** Quickstarts and local-deployment docs; examples exist but a single recommended pattern for samples was not prominent.
- **Effect on this build:** The sample uses syncIndexes() in seed/startup which is workable, but authors may be uncertain whether index creation belongs in seed/startup or in a separate migration step.
- **Suggested fix (discoverability):** A short 'seed and migration' cookbook page showing 1) safe syncIndexes usage for small samples, 2) migration scripts for production index deployment, and 3) a sample idempotent seed that uses upserts and syncIndexes().

## [medium] Dependency pinning guidance for Node samples

- **What was missing:** A guideline page that explains lockfile expectations for Node.js samples (include package-lock.json or pin exact versions) and a short CI snippet showing how to assert lockfile presence.
- **Where the agent looked:** Quickstart pages and sample guidelines; no single authoritative statement for sample repo expectations was found.
- **Effect on this build:** The sample currently relies on package.json caret ranges and missing lockfile; the run environment encountered an npm registry version resolution problem. Pinning/lockfile would improve reproducibility for gallery consumers.
- **Suggested fix (discoverability):** A short sample-repo checklist for Node: include package-lock.json (committed), pin direct dependencies to exact versions where reproducibility is important, and include a note for maintainers about updating devDependencies.

## [medium] Guidance for enabling and using MCP write tools in CI

- **What was missing:** Documentation explaining that MCP write tools are disabled by default and how to opt in (ENABLE_WRITE_TOOLS=true) and recommended security considerations when allowing automated write operations.
- **Where the agent looked:** MCP skill docs and events; the MCP call failed with a 'Write tools are disabled by default' error but no public doc was surfaced explaining the default or opt-in.
- **Effect on this build:** The builder attempted to fallback to MCP writes when npm install failed but the MCP write tools were disabled and the attempt failed; having this guidance would have shortened debugging and given a clearer fallback plan.
- **Suggested fix (mcp_tool_or_description):** Add a short MCP README note that explains write tools are opt-in, how to enable them for a trusted CI run (ENABLE_WRITE_TOOLS=true), and the security implications and audit trace recommendations.

## [low] Clarify vector-index create payload and param examples

- **What was missing:** A single, copy-paste index creation example for each DocumentDB vector 'kind' (vector-ivf, vector-hnsw, vector-diskann) including dims, metric, and the key payload the client should send.
- **Where the agent looked:** Vector-search docs; the docs are present but builders may confuse community MongoDB 7+ 'vector' syntax with DocumentDB-specific create-index payloads.
- **Effect on this build:** Not directly affecting this sample (no vectors used) but important for future samples adding vector search; missing clear examples risks authors using incompatible index payloads.
- **Suggested fix (learn_doc):** On the vector-search landing page add one-line JS examples for each 'kind' showing the exact createIndexes payload and minimal recommended defaults (dims, similarity, algorithm params) and a short note mapping popular embedding dims (e.g., 1536) to index choices.

