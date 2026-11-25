# Documentation and tooling gaps: 12-abandoned-cart-recovery-orchestration

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] LangChain JS version guidance for samples

- **What was missing:** There is no authoritative, agent-findable guidance in the agent-kit docs about which LangChain JS version to pin for Node 24 or an example LangChain-based orchestrator for this sample pattern.
- **Where the agent looked:** Loaded skills documentdb-driver, documentdb-connection, and multiple learn.microsoft docs; repository search and events show attempts to plan for LangChain but no doc specifying a version or an example.
- **Effect on this build:** Builder avoided installing LangChain (D011) and implemented a non-LangChain orchestration; the sample therefore partly fails the explicit 'LangChain' requirement in the starter prompt.
- **Suggested fix (agent_kit_rule):** Add an agent-kit rule + short quickstart 'LangChain for DocumentDB samples' documenting the tested LangChain JS version(s) for Node 24, a minimal example Chain/Agent wiring to the OpenAI SDK, and a one-line recipe to switch the sample from the lightweight orchestration to the LangChain-based implementation.

## [high] Embedding model dimension & vector-index guidance

- **What was missing:** No small, discoverable recommendation with example embedding dimensions (e.g., 1536) and how to keep vector index 'dimensions' in sync with the chosen model in sample README or kit docs.
- **Where the agent looked:** documentdb-vector-search skill, search; the sample did not create vector indexes and the skill did not provide a single concise sample mapping model→dims for use in samples.
- **Effect on this build:** Builder opted not to use vector indexes. If a future sample or an agent attempts to add vectors, it may choose mismatched dimensions and fail.
- **Suggested fix (learn_doc):** A page 'Embeddings & vector-index dimensions' that lists common embedding models, their dims (OpenAI/text-embedding-3-small: 1536, etc.), example createSearchIndexes calls with dimensions, and a checklist to validate dims at write-time.

## [high] How to author unit tests without a live DocumentDB

- **What was missing:** No sample test pattern showing either (a) running the DocumentDB gateway locally, or (b) monkeypatching getDb / using an in-memory mock so CI unit tests run offline.
- **Where the agent looked:** documentdb-local-deployment skill and repo; skill describes local gateway but there is no concise 'tests' quickstart.
- **Effect on this build:** The sample contains no offline-capable tests (test-runner prints a placeholder). This reduces gallery quality and makes it hard for agents to generate tests.
- **Suggested fix (sample_or_quickstart):** Add a 'tests/README' + example test that uses either the DocumentDB gateway docker image (start via docker-compose) or a small mock of getDb (e.g., dependency-inject getDb and provide an in-memory stub); include a CI matrix example that runs the tests without network access.

## [high] Should you store LLM/API keys in the database?

- **What was missing:** Searches returned no clear best-practice guidance about whether to keep LLM API keys in the database versus environment or key vault specifically for Azure DocumentDB samples.
- **Where the agent looked:** Agent-kit skills and public Learn docs (searches listed in practice discovery 'searches_with_no_useful_result').
- **Effect on this build:** No guidance led the builder to use env vars (OK) but agents may decide to persist keys in DB in other samples unless told explicitly not to.
- **Suggested fix (learn_doc):** Short security note on storing secrets: 'Do not store API keys in documents. Use environment variables, Azure Key Vault, or secret stores; show minimal sample for retrieving secrets in Node.'

## [high] Naming / provisioning disambiguation: mongoClusters vs databaseAccounts

- **What was missing:** Agents and older docs confuse Microsoft.DocumentDB/mongoClusters and the legacy databaseAccounts resource used by Cosmos DB. The readiness report found multiple confusions (Q01–Q03) and searches demonstrate the risk.
- **Where the agent looked:** Multiple Learn docs and documentdb-azure-deployment skill; agent-kit search showed conflicting 'cold answers'.
- **Effect on this build:** If a builder attempted to supply IaC from generic Cosmos examples, they would produce incorrect resources. The sample avoided provisioning (run policy), but the risk remains for other samples.
- **Suggested fix (naming_or_disambiguation):** Add a short 'Deployment naming' section in the agent-kit and sample README: explicit examples showing Microsoft.DocumentDB/mongoClusters (Bicep/Terraform), and a warning not to use Microsoft.DocumentDB/databaseAccounts / az cosmosdb for vCore clusters.

## [medium] Default LLM provider & env var conventions

- **What was missing:** No central guidance that samples should name LLM env vars (e.g., OPENAI_API_KEY, OPENAI_MODEL) and prefer 'provider-agnostic' wiring or document fallbacks. The builder assumed OPENAI_* and used it by model-default.
- **Where the agent looked:** Skill docs and prompt review; no single agent-kit doc prescribing default env var names and fallback behavior for samples.
- **Effect on this build:** Decision D005 used model_default assumptions about LLM wiring; lacking explicit guidance led to a builder choice that was later modified (D011) and left an implementation that may differ across repos.
- **Suggested fix (discoverability):** A short 'LLM provider conventions' page: recommended env var names (OPENAI_API_KEY, OPENAI_MODEL), how to add alternative providers, and recommended non-secret placeholders for .env.example; include a sample wrapper that selects provider by env var.

## [medium] Graceful shutdown examples for Node.js clients (SIGINT/SIGTERM)

- **What was missing:** Searches failed to return a concise Node.js example for graceful MongoClient shutdown (SIGINT/SIGTERM) that is tailored to DocumentDB driver patterns.
- **Where the agent looked:** documentdb-driver and public Learn docs; 'searches_with_no_useful_result' includes 'graceful shutdown Node.js SIGINT SIGTERM examples'.
- **Effect on this build:** The sample's db.js does not show a graceful client.close() on process exit; this can lead to unflushed metrics or abrupt connections in tests.
- **Suggested fix (learn_doc):** A short snippet in the driver best-practices page that shows hooking process.on('SIGINT'|'SIGTERM') and awaiting client.close() before exit, with a small caveat about CI runs.

