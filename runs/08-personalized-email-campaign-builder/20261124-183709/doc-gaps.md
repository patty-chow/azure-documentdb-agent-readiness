# Documentation and tooling gaps: 08-personalized-email-campaign-builder

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] LlamaIndex integration guidance

- **What was missing:** The starter prompt explicitly asked for a LlamaIndex agent that registers a fetch tool, but no installed skill or public quickstart detailing 'how to wire LlamaIndex to Azure DocumentDB' was found. The builder defaulted to not using LlamaIndex.
- **Where the agent looked:** Loaded installed skills (documentdb-*), searched Microsoft Learn for LlamaIndex + DocumentDB examples; no authoritative guide was discovered.
- **Effect on this build:** The builder implemented a lightweight agent instead of a LlamaIndex-based agent, causing the build to diverge from the prompt's explicit requirement (the missing item is the primary functional difference).
- **Suggested fix (agent_kit_rule):** Add an agent-kit rule and short sample that shows how to integrate LlamaIndex Node.js with Azure DocumentDB: (1) install LlamaIndex, (2) implement a tool adapter named `fetch_segment` that calls the DocumentDB driver, (3) register the tool with the LlamaIndex agent, and (4) an end-to-end example that seeds segments and runs the LlamaIndex agent to generate a campaign.

## [high] Embedding model ↔ vector-index dimensionality mapping

- **What was missing:** Public guidance that maps specific embedding model outputs (e.g., OpenAI embeddings dims = 1536) to the vector-index 'dimensions' parameter for DocumentDB was not found in the skill set or Learn quickstarts.
- **Where the agent looked:** documentdb-vector-search skill, Microsoft Learn vector search pages, quickstart vector docs.
- **Effect on this build:** The builder avoided using vector indexes and embeddings to keep the sample simple; without a published mapping agents cannot safely create vector indexes with the correct 'dimensions' setting.
- **Suggested fix (learn_doc):** A short Learn page or a section in the vector-search quickstart titled 'Embedding models and DocumentDB index dimensions' that lists common embedding models and their dimensionality (e.g., model X -> 1536) and an example createIndexes JSON block with 'dimensions' set accordingly.

## [high] LLM PII handling guidance for prompts

- **What was missing:** No public guidance was found that specifically tells agent authors which customer fields are acceptable to send to an LLM when building prompts from DocumentDB data, or sample redaction helpers for Node.js.
- **Where the agent looked:** Searches for 'azure documentdb pii lLM redaction' and installed skills.
- **Effect on this build:** The sample injects purchase_history into the prompt; absent guidance, an agent may inadvertently send PII to the LLM. The auditor cannot say whether the seeded data contains PII in this sample, so the risk remains.
- **Suggested fix (learn_doc):** A short 'PII & LLM' guideline for the agent kit and sample README: what fields to redact, sample redaction function (mask email/phone), and a statement recommending encrypting sensitive fields at rest.

## [high] Tests without live cluster (mock patterns)

- **What was missing:** Example test harness or pattern that shows how to write unit tests for samples without requiring a live DocumentDB cluster (e.g., using mongodb-memory-server or mocking the MongoClient).
- **Where the agent looked:** Installed skills and sample repo. No sample tests or test patterns were found.
- **Effect on this build:** The sample contains no tests and the package.json test is a noop; this increases friction for gallery acceptance and automated CI validation.
- **Suggested fix (sample_or_quickstart):** Add a short 'Testing' README subsection and an example test file using a mocked MongoClient or mongodb-memory-server showing unit tests for seed/generate functions that pass without a live cluster.

## [medium] WriteConcern / readPreference mapping for Azure DocumentDB

- **What was missing:** Public guidance that states how Azure DocumentDB maps MongoDB writeConcern and readPreference semantics to the managed product and a recommended default for application code.
- **Where the agent looked:** Searches for 'Azure DocumentDB writeConcern readPreference' returned no authoritative mapping.
- **Effect on this build:** The sample does not set explicit writeConcern/readPreference. An agent cannot confidently change defaults without knowing service behaviour—this could lead to surprising durability or latency mismatches in production.
- **Suggested fix (learn_doc):** A short page 'Consistency and durability: writeConcern/readPreference' describing supported values, defaults, and sample Node.js driver options to set them safely for typical app needs.

## [medium] Driver versions and supported combinations

- **What was missing:** A concise, discoverable list of recommended/pinned Node.js driver versions that are tested and supported against Azure DocumentDB clusters (e.g., supported mongodb Node driver versions).
- **Where the agent looked:** Installed skills and Microsoft Learn quickstarts; no single 'supported driver versions' box found.
- **Effect on this build:** The sample used mongodb ^5.7.0 and package-lock.json to pin transiently. Agents may not know which driver minor versions are supported; this can cause runtime incompatibilities when new driver versions change behaviour.
- **Suggested fix (discoverability):** Add a short 'Supported drivers' section to the quickstart listing tested driver versions per runtime and a recommendation to pin using a lockfile (or add a package.json example with exact versions).

## [medium] IaC using Microsoft.DocumentDB/mongoClusters

- **What was missing:** A short IaC snippet for Bicep/ARM/Terraform that shows the correct resource type (Microsoft.DocumentDB/mongoClusters) to provision an Azure DocumentDB cluster and minimal safe defaults.
- **Where the agent looked:** Learn samples and installed skills; documentation exists but a small ready-to-copy snippet in the sample template was missing.
- **Effect on this build:** The sample used an existing cluster (per prompt) so no provisioning was performed; new users may attempt az cosmosdb or azurerm_cosmosdb_account and target the wrong resource type.
- **Suggested fix (discoverability):** Add a short 'Optional IaC' file (Bicep) in the sample that demonstrates creating a minimal mongoClusters resource and document the az documentdb mongocluster CLI commands. Link to the Learn template.

## [medium] Model-default decisions recorded without source

- **What was missing:** Some build decisions (D003) were made by model default choices instead of following the prompt (LlamaIndex) and there was no skill or public source that would resolve the choice for an agent.
- **Where the agent looked:** decisions.jsonl and the loaded skills; LlamaIndex integration guidance was missing.
- **Effect on this build:** The builder diverted from the explicit prompt requirement (no LlamaIndex).
- **Suggested fix (agent_kit_rule):** Add a rule to the agent-kit "If the starter prompt requires a particular library (e.g., LlamaIndex) install and use it, or explicitly record and justify why it was not possible (and prefer to raise a build halt)."

## [low] .env.example completeness

- **What was missing:** .env.example omitted USE_OPENAI (the runtime toggle used by the code).
- **Where the agent looked:** app/.env.example and src/generate.js
- **Effect on this build:** Operators may be confused why OpenAI is not called by default; small usability gap for developers following README steps.
- **Suggested fix (agent_kit_rule):** Update .env.example to include USE_OPENAI=0 and optionally DOCUMENTDB_MAX_POOL_SIZE, ENABLE_WRITE_TOOLS, and any other runtime toggles used by the sample.

