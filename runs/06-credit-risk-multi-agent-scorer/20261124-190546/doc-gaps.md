# Documentation and tooling gaps: 06-credit-risk-multi-agent-scorer

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] LangChain multi-agent sample guidance

- **What was missing:** A short gallery-level example and rule that mandates how to implement 'LangChain multi-agent' samples: minimal skeletons showing agent wrappers, tool contracts (input/output JSON shapes), and how to orchestrate three agents (fetch->score->explain) with LangChain.
- **Where the agent looked:** Inspected repository and loaded documentdb-* skills; no public Microsoft Learn page provides a small canonical LangChain multi-agent sample for Azure DocumentDB.
- **Effect on this build:** The builder implemented the pipeline as plain Python functions instead of using LangChain, violating the starter prompt's explicit requirement and making the sample inconsistent with gallery conventions.
- **Suggested fix (agent_kit_rule):** Agent-kit rule: include a reference LangChain 'three-agent' skeleton in the agent-kit that shows (1) how to wrap fetch/score/explain as LangChain agents/tools, (2) the expected JSON contract between agents (applicant document shape, score_result details schema), (3) how to run sequential orchestration and record agent metadata in write-back. Include a small code snippet and tests that exercise the LangChain orchestrator in mock mode.

## [high] Test isolation / mock DocumentDB guidance

- **What was missing:** A recommended pattern and example for running tests without a live cluster: either a local gateway (docker) pattern, a mock pymongo adapter, or a documented test database/collection naming convention for isolated integration tests.
- **Where the agent looked:** Searched Learn and quickstarts; while there are local-deployment tips, there was no single authoritative pattern or sample in the agent-kit demonstrating how to structure unit vs integration tests for DocumentDB+LLM samples.
- **Effect on this build:** The tests in this repo require a live cluster. That made CI/verification dependent on the environment and increased the chance of flakiness or secret exposure in some contexts.
- **Suggested fix (sample_or_quickstart):** Add a short test-pattern doc and a sample test folder showing: unit tests that mock get_db() and the LLM, and a separate integration test profile that uses a local gateway docker-compose or a dedicated test cluster. Include a small helper to switch the DB adapter to a mock implementation inside tests.

## [high] IaC for vCore DocumentDB clusters (mongoClusters)

- **What was missing:** Clear example Bicep/Terraform snippets that create a managed MongoDB cluster using Microsoft.DocumentDB/mongoClusters (vCore) rather than the older databaseAccounts resource, plus a note on low-cost default parameters for gallery samples.
- **Where the agent looked:** The discovery found the mongoClusters ARM docs but the agent-kit lacks a snippet to copy into sample repos.
- **Effect on this build:** No IaC was added; builders might attempt to use the wrong resource type or CLI commands (databaseAccounts/cosmosdb) and fail to provision the intended vCore clusters.
- **Suggested fix (mcp_tool_or_description):** Provide a small 'iac/mongocluster.bicep' example and a README section demonstrating az documentdb mongocluster create with low-cost defaults, or explain why the sample avoids provisioning and link to authoritative IaC modules.

## [high] Guidance on recording agent metadata and audit fields

- **What was missing:** A short recommended write-back schema for samples that combine deterministic rules and LLM outputs: include fields for deterministic score, LLM score (if any), timestamp, model id/deployment, agent names, and pointer for raw LLM content.
- **Where the agent looked:** Searches located RAG and governance pages but no small copy-paste schema for gallery samples was found.
- **Effect on this build:** The sample writes creditScoreDetails and creditScoreExplanation but does not add timestamp or agent metadata; auditability is reduced.
- **Suggested fix (learn_doc):** A one-page guideline 'Write-back schema for AI-augmented samples' with a recommended JSON shape (e.g., creditScore, deterministicScore, llmScore, llm_model, llm_prompt_hash, timestamp, agent_names, llm_raw_pointer) and small code snippets for atomic $set updates.

## [medium] Pin dependencies for gallery samples

- **What was missing:** A short guidance page telling builders to pin exact package versions in requirements.txt for gallery samples and example pinned versions used in CI/verification.
- **Where the agent looked:** Searched sample repo and Microsoft Learn quickstarts; no explicit gallery guidance for pinned requirements was found by the discovery agent.
- **Effect on this build:** The repository uses open-ended version ranges (>=) which risks future breakage in CI and in user environments if transitive updates are incompatible.
- **Suggested fix (learn_doc):** A page titled 'Pinning Python dependencies for sample stability' describing why pinning is required for gallery samples, showing an example requirements.txt with pinned versions used in build verification, and instructions for periodic maintenance.

## [medium] Entra ID auth example for Python apps

- **What was missing:** A short, copy-paste Python example showing how to connect to an Azure DocumentDB managed MongoDB cluster using Microsoft Entra ID (OIDC) and azure.identity.DefaultAzureCredential with pymongo, plus the env vars and cluster settings needed.
- **Where the agent looked:** Microsoft docs on Entra ID and DocumentDB exist but a concise, language-specific example that gallery builders could paste into samples was not surfaced in the agent-kit.
- **Effect on this build:** The sample defaults to connection-string auth and does not document why Entra ID was not used; builders could miss the recommended secure option for production.
- **Suggested fix (discoverability):** Add a short 'Use Microsoft Entra ID for authentication (Python)' snippet to the documentdb-security or documentdb-driver skill: show how to obtain an OIDC token and supply it to pymongo with authMechanism=MONGODB-OIDC and the azure.identity DefaultAzureCredential flow.

