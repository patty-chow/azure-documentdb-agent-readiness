# Documentation and tooling gaps: 10-wealth-management-rag-portal

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Embedding model / dimension default

- **What was missing:** A canonical gallery-recommended default embedding model and associated dimension for samples. The prompt and skill.md did not prescribe an embedding model, leaving the builder to choose (text-embedding-3-small / 1536 in this run).
- **Where the agent looked:** Readiness findings and the documentdb-vector-search skill; no single agent-facing sample recommendation was available in the repo docs.
- **Effect on this build:** Builder chose a reasonable default (1536) and matched index dimensions, but different defaults across authors would cause mismatch bugs in many samples.
- **Suggested fix (agent_kit_rule):** Agent-kit rule: 'Unless the user specifies an embedding model, use OPENAI text-embedding-3-small (1536 dims) and set EMBEDDING_DIMS accordingly.' Add a one-line example to the sample starter prompt template and .env.example.

## [high] PII-handling rule for RM/portfolio samples

- **What was missing:** An agent-kit rule or short sample page specifying that relationship-management samples must either redact PII or explain explicitly in the README and provide a flag to enable/disable sending raw portfolio data to third-party LLMs.
- **Where the agent looked:** The AI security guidance pages were found but not a Gallery-specific rule for RM patterns.
- **Effect on this build:** The sample currently sends full portfolio JSON to the LLM prompt; this would be a data-leak risk in a real deployment and should be reduced or guarded by explicit consent/config flags.
- **Suggested fix (agent_kit_rule):** An agent-kit rule: 'For any sample that includes client data, include either (a) a redaction/preprocessing step before LLM calls and a note in the README, or (b) an explicit warning and env flag (SEND_RAW_PORTFOLIO=true) so the developer knowingly opts into sending PII.' Provide a small redact function example and a test.

## [high] Retry guidance (small retry wrapper)

- **What was missing:** A short recommended retry wrapper example (exponential backoff + jitter) for DocumentDB client operations and for embedding/LLM calls.
- **Where the agent looked:** Reliability guidance pages were present but a minimal 'drop-in' code snippet for samples was not obvious in the agent-kit sample templates.
- **Effect on this build:** No retries are present in the sample; transient failures would surface as 500s and degrade developer experience.
- **Suggested fix (sample_or_quickstart):** Add a small Python helper (utils/retries.py) with a tenacity-based decorator and a short README example showing wrapping db.search_similar and the OpenAI embedding call.

## [medium] Driver version recommendations

- **What was missing:** A short public page that states the recommended Python driver versions for Azure DocumentDB (e.g., tested PyMongo version ranges) and whether exact pinning (==) or ranged pinning (>=,<) is preferable for gallery samples.
- **Where the agent looked:** Searched Microsoft docs and quickstarts via learn_microsoft_docs_search for 'pymongo tested version' and 'pymongo compatibility'. Quickstarts mention tested versions in examples but there is no single short guidance page for sample authors stating 'pin dependencies like X.Y.Z or X.Y' for DocumentDB samples.
- **Effect on this build:** The builder picked a reasonable pymongo pin (>=4.3,<5) by convention. A canonical recommendation would make the choice less reliant on model defaults and reduce variability across samples.
- **Suggested fix (discoverability):** Add a short 'driver-compatibility' page in the DocumentDB agent-kit that lists tested driver package versions for Python (pymongo), Node (mongodb), Java, and notes whether gallery samples should pin exact versions or ranges. Include example requirements.txt snippets.

## [medium] Idempotent index creation example (driver fallback)

- **What was missing:** A short copy-pasteable example of the db.command({createIndexes:..., cosmosSearchOptions: ...}) payload and a note about drivers that block vendor extensions. The vector-search skill contains guidance but a tiny snippet in the agent-kit README would help.
- **Where the agent looked:** documentdb-vector-search skill resources and the Integrated vector store docs; the agent-kit has detailed guidance but not a one-liner in the sample template.
- **Effect on this build:** The builder implemented the fallback (and created scripts/create_vector_index.py), but authors unfamiliar with cosmosSearchOptions may produce non-working createIndex calls.
- **Suggested fix (sample_or_quickstart):** Add a 10-line snippet in the vector-search quickstart and agent-kit README showing db.command({createIndexes: 'col', indexes:[{key:{embedding:'cosmosSearch'}, cosmosSearchOptions:{kind:'vector-hnsw',dimensions:1536,similarity:'COS',...}}]}) and note the common driver errors and the MCP tool fallback.

## [medium] Infrastructure example for mongoClusters

- **What was missing:** A tiny Bicep or Terraform example that creates Microsoft.DocumentDB/mongoClusters with parameters for tier (Mxx), region and storage and a note about default low-cost choices.
- **Where the agent looked:** documentdb-azure-deployment skill and MS Learn templates; no gallery-ready 1-file IaC example was in the sample repository.
- **Effect on this build:** The sample had to rely on a pre-provisioned cluster. Authors may ship samples without a consistent way to recreate the dev cluster if they lack IaC snippets.
- **Suggested fix (mcp_tool_or_description):** Add infra/ folder with a minimal Bicep file (main.bicep) that declares resource 'Microsoft.DocumentDB/mongoClusters@{stable}', parameters 'tier','region','storage', and default low-cost values, plus a README note about the run policy and when to use it.

