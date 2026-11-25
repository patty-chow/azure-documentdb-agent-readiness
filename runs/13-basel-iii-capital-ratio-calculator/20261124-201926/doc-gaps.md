# Documentation and tooling gaps: 13-basel-iii-capital-ratio-calculator

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] LLM & PII guidance for DocumentDB samples

- **What was missing:** No service-specific guidance on whether and when to send per-position balances or PII to external LLMs. The discovered practice P17 is prior_knowledge_only (no public DocumentDB page was found).
- **Where the agent looked:** Searches for 'Azure DocumentDB LLM PII guidance' and 'Azure DocumentDB privacy LLM' returned no service-specific guidance; general privacy docs exist elsewhere.
- **Effect on this build:** The builder conservatively sends only aggregates to the LLM, but an agent might send raw documents unless guidance is explicit; this could cause privacy leakage depending on developer choices.
- **Suggested fix (learn_doc):** A short guidance page titled 'Using LLMs with Azure DocumentDB: privacy and PII best practices' that states: (1) do not send raw per-customer balance-level data to external LLMs; (2) prefer sending de-identified aggregates for commentary; (3) include example payloads that are acceptable and unacceptable; (4) example code showing how to reduce documents to aggregates before calling an LLM. Put this page under DocumentDB security/operational guidance.

## [high] Driver version and OIDC compatibility

- **What was missing:** Clear, discoverable guidance about which PyMongo driver versions are required for newer authentication modes (e.g., OIDC/MONGODB-OIDC). The repo pinned pymongo==4.4.0 but Microsoft docs show newer tested versions (>=4.7+ recommended for OIDC).
- **Where the agent looked:** Microsoft Learn quickstarts and vector-search docs (quickstart-python, quickstart-python-vector-search) and skill docs.
- **Effect on this build:** The sample pins pymongo==4.4.0 which may lack support for some auth modes or features; users enabling Entra ID-based auth or OIDC may encounter failures.
- **Suggested fix (discoverability):** A short note on the DocumentDB quickstart page and sample README that lists 'Tested PyMongo versions' and states min version for features (e.g., 'For MONGODB-OIDC/Entra integration ensure pymongo >= 4.7; we recommend pinning to 4.19.0 used in Microsoft quickstarts').

## [high] Tests run offline guidance

- **What was missing:** A guideline (and sample helper) showing how to write unit tests for DocumentDB-based samples that run without a live cluster, e.g., monkeypatching get_positions_collection or providing a fake collection client.
- **Where the agent looked:** Repository tests and installed skills; no sample-specific guidance found in the repo.
- **Effect on this build:** Current tests require a DOCUMENTDB_URI or refer to a non-existent class, preventing local CI verification without a live cluster.
- **Suggested fix (agent_kit_rule):** An agent-kit rule and short README snippet: 'Unit tests must run offline by mocking pymongo.Collection or the sample's DB-adapter function. Provide an example pytest fixture that replaces get_positions_collection() with a fake collection implementing aggregate().' Include a minimal example test that does this.

## [high] DocumentDB guidance for Decimal128 and aggregation currency handling

- **What was missing:** A short, discoverable example on the DocumentDB docs or agent-kit showing storing regulatory/monetary amounts as Decimal128 and showing $toDecimal usage in aggregation pipelines.
- **Where the agent looked:** Microsoft Learn $toDecimal page and documentdb skills; guidance exists but an explicit short example for 'Basel III' style sums would help agents.
- **Effect on this build:** Builder stored numeric values as floats; adopting Decimal128 would make the sample safer for regulatory sums and avoid rounding differences.
- **Suggested fix (discoverability):** Add a small 'Handling money and regulatory numerics' example page or snippet showing: 'Use bson.decimal128.Decimal128 for storage; example seed_data write; example aggregation using $toDecimal or ensuring Decimal128 propagation.'

## [medium] README: exact CLI and ARM resource types (mongoClusters)

- **What was missing:** The sample README does not explicitly state the exact Azure resource type name and the authoritative az CLI group for vCore DocumentDB clusters (Microsoft.DocumentDB/mongoClusters and az documentdb mongocluster).
- **Where the agent looked:** Readiness findings and Microsoft Learn quickstarts (az documentdb mongocluster docs).
- **Effect on this build:** Risk of authors copying older Cosmos DB examples (databaseAccounts/az cosmosdb) which target a different service. This causes deploy or user confusion when trying to create clusters.
- **Suggested fix (naming_or_disambiguation):** Add a short 'Naming and provisioning' paragraph to the README with: (1) exact ARM/Bicep resource type: Microsoft.DocumentDB/mongoClusters; (2) example az CLI command group 'az documentdb mongocluster create' and one-liner; (3) note that az cosmosdb examples may target a different service. Include links to the Microsoft Learn pages.

## [medium] .env.example correctness

- **What was missing:** A valid, syntactically-correct .env.example that the README references. The current .env.example contains a malformed line (missing closing quote) which can confuse users copying it.
- **Where the agent looked:** app/.env.example and README.
- **Effect on this build:** Minor friction: copy/paste may produce a malformed .env and cause immediate run errors for newcomers.
- **Suggested fix (learn_doc):** Replace .env.example with syntactically-correct placeholders and a short comment for each var. Example: DOCUMENTDB_URI="mongodb+srv://<user>:<pass>@<cluster>/?tls=true". Include a one-line note about retrieving the connection string from 'az documentdb mongocluster list-connection-strings'.

