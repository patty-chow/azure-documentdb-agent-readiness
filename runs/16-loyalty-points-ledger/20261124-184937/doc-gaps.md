# Documentation and tooling gaps: 16-loyalty-points-ledger

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Node.js Mongoose + Microsoft Entra ID example

- **What was missing:** A concise, copy-paste Node.js (Mongoose) example that shows how to obtain an OIDC token (via azure-identity/DefaultAzureCredential or similar) and connect to an Azure DocumentDB cluster using authMechanism=MONGODB-OIDC was not found in the public quickstarts the agent searched.
- **Where the agent looked:** Microsoft Learn Azure DocumentDB quickstarts, documentdb security/readme, and the agent-kit skill resources (documentdb-security), plus general web search recorded in readiness findings.
- **Effect on this build:** Builder chose SCRAM-based credentials for the sample rather than demonstrating Entra ID; README documents that Entra ID was not shown. Without a short example, agents and builders are likely to omit OIDC in quickstarts or attempt broken/partial implementations.
- **Suggested fix (learn_doc):** A small page or appendix titled 'Connect with Microsoft Entra ID (MONGODB-OIDC) — Node.js + Mongoose' that includes: 1) brief prerequisites (cluster auth-allowed-modes must include MicrosoftEntraID), 2) sample code showing DefaultAzureCredential/ManagedIdentityCredential to get an access token for scope (resource) and how to pass it to mongoose.connect with authMechanism=MONGODB-OIDC (or driver-specific token callback), 3) a note about required driver versions, 4) a one-line az CLI command to enable Entra ID on a cluster, and 5) a short troubleshooting checklist. Include copy-ready code with minimal dependencies (azure-identity, mongoose) and show both SRV and non-SRV forms.

## [high] Write-concern semantics for ledger use

- **What was missing:** Clear guidance on how MongoDB writeConcern settings (w, j) map to Azure DocumentDB durability guarantees for ledger/financial workloads was not present in the public sources the agent found (this remained a prior-knowledge-only item).
- **Where the agent looked:** Searches for 'Azure DocumentDB write concern w majority j true' and related queries; agent-kit resources and Microsoft Learn compatibility pages were checked but no definitive mapping page was found.
- **Effect on this build:** The sample does not set an explicit writeConcern. For ledger scenarios, teams may need authoritative guidance about recommended writeConcern settings and their effects on durability and performance on DocumentDB vCore clusters.
- **Suggested fix (learn_doc):** A short guidance note on the 'Transactions and Durability' page: 1) explain how DocumentDB maps common driver writeConcern options to service durability, 2) give recommended settings for ledger-style workloads (what to set, and tradeoffs), 3) show an example in Node.js/Mongoose of setting writeConcern on operations or on the connection, and 4) include an MCP command or explain() snippet to verify write durability behavior.

## [high] CLI / IaC naming and resource-type clarity (mongoclusters vs databaseAccounts)

- **What was missing:** Discoverability confusion between the older Cosmos DB 'databaseAccounts' resource and the vCore DocumentDB 'Microsoft.DocumentDB/mongoClusters' resource; agents may use incorrect az CLI groups or ARM types by habit.
- **Where the agent looked:** Microsoft Learn CLI and ARM docs; readiness_findings Q01-Q03 show search results and confusion evidence.
- **Effect on this build:** The builder did not attempt to provision resources in this run, but shipping example IaC or CLI snippets that use the wrong resource type would mislead builders and break deployments.
- **Suggested fix (naming_or_disambiguation):** A short 'Infra quick note' page or README section clarifying: 'For vCore Azure DocumentDB clusters, use Microsoft.DocumentDB/mongoClusters (Bicep/ARM) and az documentdb mongocluster commands. Do not use Microsoft.DocumentDB/databaseAccounts or az cosmosdb commands for vCore clusters.' Include one minimal Bicep snippet and one az documentdb mongocluster list-connection-strings example.

## [medium] Mongoose .lean() guidance discoverability

- **What was missing:** The practical Mongoose optimization pattern to use .lean() for read-heavy endpoints is not present in the Azure DocumentDB quickstart pages the agent searched; it exists in general Mongoose guidance but not surfaced in DocumentDB-specific docs.
- **Where the agent looked:** Search for 'Mongoose .lean() Azure DocumentDB' and Mongoose guidance pages; agent-kit skill resources did not include a short explicit mention targeted at DocumentDB quickstarts.
- **Effect on this build:** This did not break the sample (the builder used .lean()), but agents that rely only on DocumentDB quickstarts may not apply the optimization by default.
- **Suggested fix (discoverability):** Add a short note in the 'Quickstart: Connect Mongoose to Azure DocumentDB' page: a two-sentence recommendation to use .lean() for endpoints that return plain JSON and project only required fields, with an inline code example for Event.find(...).lean().

## [medium] No authoritative node test pattern for offline unit tests

- **What was missing:** While there is a local gateway skill, there is no short DocumentDB-specific example in the quickstarts showing a minimal test harness using mongodb-memory-server or the DocumentDB local gateway for Node.js Mongoose tests.
- **Where the agent looked:** DocumentDB local deployment skill and quickstarts; no direct test harness examples were found in the sample quickstarts consulted.
- **Effect on this build:** The sample lacks unit tests runnable without a live cluster. Having a short, documented test pattern would make it straightforward to add tests that run in CI without external resources.
- **Suggested fix (sample_or_quickstart):** A 'Testing' section in the Node.js quickstart showing two options: (1) use mongodb-memory-server with example test code (Jest/Mocha) to run ledger unit tests offline, and (2) optionally show how to start the DocumentDB gateway Docker image for integration tests (port 10260) with the exact connection string and TLS dev settings.

