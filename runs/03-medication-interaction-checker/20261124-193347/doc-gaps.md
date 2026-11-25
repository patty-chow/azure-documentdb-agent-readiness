# Documentation and tooling gaps: 03-medication-interaction-checker

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Vector index & embedding guidance for samples

- **What was missing:** Public, sample-level guidance that shows the minimal createIndexes JSON payload (cosmosSearchOptions) and the matching schema field for an embedding vector, with an explicit note about which embedding dimensions to use for popular models (e.g., OpenAI embedding dims) and a small example script.
- **Where the agent looked:** Azure DocumentDB vector-search docs and quickstarts (discovered practices P10/P11), repo README.
- **Effect on this build:** The builder did not create an embedding field or vector index; semantic search and vector-based caching were not implemented. This left the sample using only document lookup + LLM fallback, and the sample cannot demonstrate vector retrieval or server-side RRF hybrid search.
- **Suggested fix (learn_doc):** A short page 'Vector index quickstart for samples' including: 1) minimal schema snippet showing an 'embedding: [Number]' field; 2) createIndexes JSON example with cosmosSearchOptions for HNSW/IVF/DiskANN and the 'dimension' property; 3) recommended dimension examples (e.g., 1536 for certain OpenAI models), default params for small sample (m/efConstruction), and how to change them for larger datasets; 4) a sample create-index script and note to set EMBEDDING_DIM in .env.example.

## [high] Retry and 429 handling guidance for agents using DocumentDB

- **What was missing:** A short agent-kit rule or sample snippet that demonstrates a small retry-with-exponential-backoff wrapper (with jitter), how to detect DocumentDB throttling errors, and how to respect Retry-After semantics in both driver and REST responses.
- **Where the agent looked:** Azure reliability and 429 troubleshooting docs (discovered practice P12/P13), repo code.
- **Effect on this build:** No retry or throttling handling was added to DB or LLM calls; transient errors could cause the sample to surface confusing failures in higher-latency or throttled environments.
- **Suggested fix (agent_kit_rule):** An agent-kit rule 'db-retries' containing a Node.js small helper function (retryWithBackoff) and an example of wrapping Interaction.find/updateOne and LLM calls; detection code for common transient errors and a policy to limit retries and surface human-friendly messages.

## [high] Explicit guidance about logging & PHI in agent examples

- **What was missing:** A sentence in the sample README and an agent-kit rule addressing that samples dealing with medication lists must avoid logging PHI, with examples of what to redact and how to implement redaction utilities.
- **Where the agent looked:** Quickstart security notes (P20), repo code.
- **Effect on this build:** The sample logs errors and fallback messages without redaction; in a clinical integration this could leak sensitive data if the app were adapted carelessly.
- **Suggested fix (learn_doc):** A README subsection 'PHI, logging and telemetry' with a small code snippet (redact function) and an agent-kit rule that enforces 'do not log medication lists or raw prompts' for healthcare samples.

## [medium] Explain()/index-check script and instructions

- **What was missing:** A small sample script and README guidance that runs explain('executionStats') for the pairwise lookup query and shows how to interpret results and MCP tooling output.
- **Where the agent looked:** Indexing docs and MCP toolkit (discovered practice P17/P24), repo.
- **Effect on this build:** The builder created indexes but did not include a 'how to verify' script; reviewers had to use MCP manually. This increases friction for contributors verifying that their queries are indexed efficiently.
- **Suggested fix (sample_or_quickstart):** Add scripts/explain_pair.js which connects to DB, runs Interaction.find({ normalizedPair: { $in: [...] } }).explain('executionStats'), and prints index usage and key metrics. Add a README subsection showing how to run it and interpret the results.

## [medium] Guidance on choosing authentication method in samples

- **What was missing:** A short README paragraph or agent-kit rule explaining when to use a connection string vs Microsoft Entra ID (OIDC/managed identity) in samples and a template for both approaches.
- **Where the agent looked:** Connect to Azure DocumentDB using Entra ID docs (discovered P04) and sample repo README.
- **Effect on this build:** The sample uses a connection string but doesn't explain why Entra ID was not chosen; readers may be uncertain whether the sample is production-ready regarding auth.
- **Suggested fix (discoverability):** Add a README section 'Authentication choices' that: 1) explains connection-string (SCRAM) usage for local/quickstart scenarios; 2) shows steps to enable Microsoft Entra ID and link to how-to docs; 3) provides a short example or link to an Entra-ID-based connection snippet.

## [medium] Infrastructure-as-code example for mongoClusters

- **What was missing:** A minimal Bicep/Terraform example that creates an Azure DocumentDB vCore cluster using Microsoft.DocumentDB/mongoClusters with parameters and low-cost defaults.
- **Where the agent looked:** ARM/Bicep and mongoClusters docs (readiness findings showed resource naming confusion), repo.
- **Effect on this build:** No IaC was provided; maintainers or users who want to reproduce the cluster must author their own IaC and risk using the wrong resource type (databaseAccounts vs mongoClusters).
- **Suggested fix (mcp_tool_or_description):** Add infra/mongoCluster.bicep (or terraform) demonstrating Microsoft.DocumentDB/mongoClusters creation with tier/storage/region parameters, and a note in README pointing to 'az documentdb mongocluster' CLI examples.

