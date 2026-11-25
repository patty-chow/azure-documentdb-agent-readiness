# Documentation and tooling gaps: 08-dynamic-segmentation-engine

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Tests run offline (mocking guidance)

- **What was missing:** Explicit examples and a small test fixture that let unit tests run without a live cluster (e.g., using a local DocumentDB gateway docker image example or a pymongo/mongomock mocking pattern).
- **Where the agent looked:** Repository tests and Microsoft Learn quickstarts; searched the repo for test fixtures and the installed documentdb-local-deployment skill docs.
- **Effect on this build:** The provided tests (tests/test_aggregate.py) require a seeded live cluster. This meant CI or consumers who lack a live cluster cannot run tests offline; it also raises the bar for contributors.
- **Suggested fix (learn_doc):** A short README subsection 'Running tests' plus a test-helper module. Content: 1) A one-paragraph explanation of two options: (a) run tests against a running local DocumentDB gateway docker image (docker run example, default port 10260 and env vars), with sample docker-compose; (b) run pure unit tests by setting TEST_MONGO_MOCK=true and using a provided test fixture that swaps out src.db.get_db for a mongomock-backed client. Include a small example test that uses the fixture.

## [high] Infrastructure-as-code for mongoClusters

- **What was missing:** An example Bicep/ARM or Terraform snippet that provisions Microsoft.DocumentDB/mongoClusters with sensible default tier, storage and region.
- **Where the agent looked:** Repository (no IaC files), documentdb-azure-deployment skill docs and Microsoft Learn templates for mongoClusters.
- **Effect on this build:** The sample currently requires an existing cluster; users may copy the repo and not have an owned cluster. Lack of IaC reduces reproducibility and forces manual portal steps.
- **Suggested fix (mcp_tool_or_description):** Provide a minimal Bicep file named deploy/mongoCluster.bicep that provisions Microsoft.DocumentDB/mongoClusters with parameters (tier, region, storage) and outputs connection strings; a README subsection explains running az extension install documentdb and az deployment group create --template-file. Also include Terraform/azapi example in a second file for users who prefer Terraform.

## [high] Retry/backoff examples for common DB ops

- **What was missing:** A small example showing how to wrap aggregation and update operations with retries + exponential backoff and how to honor server-supplied retry guidance.
- **Where the agent looked:** documentdb-connection skill and repo code (no retry wrappers present).
- **Effect on this build:** The sample runs against a live cluster but lacks robustness instructions; intermittent 429s or transient network blips could cause the sample or CI to fail until retried.
- **Suggested fix (agent_kit_rule):** A short code snippet (new module src/retry.py) that supplies a retry decorator using tenacity, plus examples showing wrapping compute_metrics and update_one calls and how to read Retry-After from responses. Include a note in README recommending enabling retries in production workloads.

## [medium] Auth options and Entra ID guidance

- **What was missing:** A short note in the README explaining available auth modes (connection-string SCRAM vs Microsoft Entra ID) and why the sample uses a connection string by default, and how to change to Entra ID (if the cluster is configured for MONGODB-OIDC).
- **Where the agent looked:** Repository README (no discussion of Entra ID), documentdb-security skill and Microsoft docs about Entra ID auth.
- **Effect on this build:** Users who expect to use Microsoft Entra ID may be uncertain whether the sample supports it and how to enable it; they might try to embed credentials incorrectly.
- **Suggested fix (learn_doc):** Add a 'Authentication' subsection in README: list supported methods, show a short example of how to exchange an Entra token and how to configure the driver for MONGODB-OIDC, and mention that the sample demonstrates connection-string usage for simplicity and how to adapt code to call the token-exchange helper.

## [medium] LangChain tool registration example

- **What was missing:** A small example showing how to wrap an aggregation function as a LangChain Tool and register it in an AgentExecutor.
- **Where the agent looked:** Repo (agent implements compute_metrics but no langchain Tool wrapper), LangChain docs (general) and 'Use LangChain on Azure with Azure DocumentDB' page.
- **Effect on this build:** The sample demonstrates LangChain-compatible behavior and lazy LLM import, but does not present the recommended pattern for exposing the aggregation pipeline as a callable LangChain tool. This may confuse sample users expecting a Tool-registered example.
- **Suggested fix (sample_or_quickstart):** Add a short code snippet in the README or src/agent.py that creates from langchain.agents import Tool and Tool(func=compute_metrics, name='documentdb_aggregate', description='Compute recency/frequency/affinity') and shows how to pass it into an agent.

## [medium] Runtime compatibility guidance (LangChain/pydantic)

- **What was missing:** A short note describing the potential LangChain/Pydantic compatibility issue observed on Python 3.13 and suggested mitigations (pin langchain/pydantic to working versions or use Python 3.11).
- **Where the agent looked:** Builder open_issues and runtime inventory; no such note in README.
- **Effect on this build:** The builder encountered an import-time pydantic compatibility error with langchain on Python 3.13 and implemented a lazy-import fallback. Users who try the LLM path on 3.13 may run into the same issue and not know why the sample falls back to deterministic rules.
- **Suggested fix (discoverability):** Add a short 'Runtime and LLM notes' subsection in README explaining: recommended Python minors (3.11/3.12) if using LLM path, or exact pinned langchain/pydantic versions that are known to work. Include a sample requirements-llm.txt showing the compatible pin set.

