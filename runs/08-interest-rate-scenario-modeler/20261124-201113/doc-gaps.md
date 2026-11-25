# Documentation and tooling gaps: 08-interest-rate-scenario-modeler

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Computed-field indexing guidance (maturity buckets)

- **What was missing:** Clear documentation advising when to precompute bucket keys (e.g., maturity_bucket) at write time vs computing them in aggregation ($addFields), including performance trade-offs and indexability of computed fields.
- **Where the agent looked:** Searched installed skills (documentdb-data-modeling) and Microsoft Learn; discovered practice P07 exists but public guidance around indexing computed fields and examples of precompute vs $addFields for bucketing is minimal.
- **Effect on this build:** Builder computed maturity_years at query time ($addFields) which risks full-collection scans on larger datasets and prompted a runtime index creation in the aggregation path rather than in seed/migrations.
- **Suggested fix (learn_doc):** A short Learn/agent-kit page titled 'Precompute vs computed fields for bucket/group queries' describing: (1) why precomputing bucket keys (maturity_bucket) helps index usage, (2) an example seed script that writes maturity_bucket, (3) an aggregation example that groups on maturity_bucket, (4) an explain() compare showing effect on index usage. Include a migration snippet to backfill the bucket for existing data.

## [high] Idempotent index lifecycle guidance

- **What was missing:** A concise doc or code snippet showing idempotent index creation in seed/migration scripts and how to audit existing indexes before creating them programmatically.
- **Where the agent looked:** Searches for exact 'create index idempotent check existing index programmatic exact match' returned no useful single authoritative example; skill guidance on indexing exists but a short pattern snippet for seeds is missing.
- **Effect on this build:** Index creation was implemented in the aggregation code path (aggregation_tool._ensure_index) rather than seed/migrations; the MCP tool attempt also failed, causing the builder to fall back to programmatic create_index at runtime.
- **Suggested fix (agent_kit_rule):** Agent-kit rule and sample 'seed-and-index' script showing: check existing indexes (listIndexes), create missing indexes idempotently, name indexes explicitly, and include a CI dev-check that runs explain() to detect missing index coverage.

## [high] Naming and CLI confusion: mongoClusters vs databaseAccounts / az documentdb vs az cosmosdb

- **What was missing:** Clear prominent guidance that the vCore Mongo product uses Microsoft.DocumentDB/mongoClusters and the az documentdb mongocluster CLI group, and that this is distinct from the Cosmos DB (RU) databaseAccounts resource. Developers commonly misapply older Cosmos examples.
- **Where the agent looked:** Readiness findings and CLI/Bicep docs; searches found mixed historical materials that confuse authors.
- **Effect on this build:** If the builder had attempted to include IaC or az CLI snippets, they might target the wrong resource type. The sample avoided provisioning because of run policy but the README and agent-kit should guard future authors from picking the wrong CLI/resource.
- **Suggested fix (naming_or_disambiguation):** Add a 'Product map and CLI note' card in the agent-kit README summarizing: (a) Microsoft.DocumentDB/mongoClusters is vCore Azure DocumentDB, (b) do not use Microsoft.DocumentDB/databaseAccounts for vCore clusters, (c) CLI commands: az documentdb mongocluster for vCore clusters, with a copyable minimal az/Bicep example.

## [high] Driver authentication examples including Microsoft Entra ID (OIDC)

- **What was missing:** Concrete code examples showing both SCRAM-based connection-string usage and Microsoft Entra ID (MONGODB-OIDC) connection examples (including token acquisition or managed-identity flow) for PyMongo.
- **Where the agent looked:** Installed skills and Microsoft docs include Entra ID pages but a short sample snippet for the sample repo was not included.
- **Effect on this build:** The sample uses DOCUMENTDB_URI; clusters that require Entra OIDC would fail with only a plain connection-string example. The README does not show Entra/OIDC examples.
- **Suggested fix (learn_doc):** A small README subsection titled 'Authentication options' with two copyable code snippets: (1) SCRAM connection via DOCUMENTDB_URI; (2) OIDC example using pymongo with authMechanism=MONGODB-OIDC and a short Python snippet showing how to obtain and supply the token or use managed identity.

## [medium] LLM provider & model selection guidance for samples

- **What was missing:** Product-level guidance advising which LLM providers/models to default to in samples and a short rationale (cost/availability/pin).
- **Where the agent looked:** Agent kit readiness notes and installed skills; no authoritative product guidance on a default model for LangChain-based gallery samples.
- **Effect on this build:** Builder defaulted to OpenAI/gpt-4 (decision D004). This is acceptable but leaves reproducibility and billing assumptions unspecified; the LLM call was not executed in CI because the API key was omitted.
- **Suggested fix (discoverability):** A top-level agent-kit page 'Choosing an LLM for samples' that recommends a default (eg OpenAI with example model and fallback notes for Azure OpenAI), documents env variables to set (OPENAI_API_KEY, OPENAI_MODEL), and shows pinned versions and cost considerations for gallery builds.

## [medium] Local development gateway quickstart

- **What was missing:** A concise local-dev snippet showing the DocumentDB gateway Docker image and connection string (port 10260) and TLS guidance for local runs.
- **Where the agent looked:** Readiness notes and documentdb-local-deployment skill; developer searches found references but a one-paragraph snippet in agent-kit is missing.
- **Effect on this build:** Builder used the live cluster for verification; authors without live clusters may prefer to run against a documented local gateway image but the README lacks that quickstart.
- **Suggested fix (discoverability):** A one-paragraph 'Local dev' section in the sample README and the documentdb-local-deployment skill with a Docker run snippet (ghcr.io/documentdb/documentdb/documentdb-local), connection examples (mongodb://localhost:10260/?tls=true&tlsAllowInvalidCertificates=true), and seed invocation instructions.

