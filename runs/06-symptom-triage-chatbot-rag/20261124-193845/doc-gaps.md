# Documentation and tooling gaps: 06-symptom-triage-chatbot-rag

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Dependency pinning

- **What was missing:** Explicit pinned versions in requirements.txt (the repo uses unpinned dependencies).
- **Where the agent looked:** Repository files (app/requirements.txt) and the build logs/events (events.jsonl show pip install used cached wheels but no pinned file).
- **Effect on this build:** Lack of pinned dependencies increases reproducibility risk (tests/install may install different versions in CI) and can cause subtle behavioral differences across environments.
- **Suggested fix (learn_doc):** Add pinned requirements.txt (requirements.txt) with explicit versions. Example: fastapi==0.95.0, uvicorn==0.23.0, pymongo==4.20.1, python-dotenv==1.2.4, openai==0.29.0, langchain==0.1.0, pydantic==1.10.11, pytest==7.4.0, requests==2.31.0. Also add a short note in README explaining how to rebuild the virtualenv.

## [high] Offline/CI test strategy

- **What was missing:** A test strategy and CI-friendly fixtures that run tests without a live production cluster (mocking get_client or using the DocumentDB local gateway).
- **Where the agent looked:** Repository tests, README and documentdb-local-deployment skill resources (events.jsonl show that skill was loaded but no test fixtures were added).
- **Effect on this build:** Tests in this repo run against a reachable cluster in the run environment; they are not portable to CI environments that should not use production secrets, so CI would either need a test cluster or the tests would fail/misuse credentials.
- **Suggested fix (sample_or_quickstart):** Provide one of: (A) a pytest fixture that monkeypatches app.db.get_client() to return a local in-memory or mongomock client for unit tests; (B) a small script & docker-compose to run the DocumentDB local gateway for integration tests and instructions to point DOCUMENTDB_URI at localhost:10260 for CI; include example CI steps that use the fixture/matcher.

## [medium] Index tuning & README guidance

- **What was missing:** README lacks guidance on how to tune DiskANN/HNSW/IVF parameters (maxDegree, lBuild, lSearch, numLists) for larger datasets.
- **Where the agent looked:** Repository README and seed.py. The documentdb-vector-search skill and its 'vector-create-diskann-index.md' resource provide tuning heuristics (events.jsonl shows the skill resource was read).
- **Effect on this build:** The sample used moderate defaults appropriate for ~20 docs, but users may copy these defaults into production without tuning, potentially causing poor recall or excessive resource use.
- **Suggested fix (discoverability):** Add an 'Index tuning' subsection in README summarizing: why dimensions must match embedding model; recommended defaults for small demos (DiskANN: maxDegree=32, lBuild=50, lSearch=50), how to increase lSearch for recall, and links to the vector-search docs for large-corpus production tuning.

## [medium] Embedding error handling

- **What was missing:** Explicit server-side handling and user-facing error messages when external embedding provider calls fail.
- **Where the agent looked:** app/app.py and app/utils.py (no try/except around get_embedding in app), and standard LangChain/OpenAI docs. The run logs show real OpenAI calls were not executed in this run and fallback was used.
- **Effect on this build:** If OPENAI_API_KEY is set in a user's environment and the embedding call fails (network/quotas), the current endpoint would raise a server-side exception and return a generic 500 without a clear indication that the embedding provider failed.
- **Suggested fix (agent_kit_rule):** Add try/except around get_embedding() in the /triage handler; on failure return HTTP 502 with 'Embedding provider failed' and include a short remediation sentence. Add a unit test asserting the 502 response when the embedding call raises.

## [medium] Model-default decision: synthetic corpus

- **What was missing:** The decision to use synthetic guideline text was recorded with reason_source 'model_default'.
- **Where the agent looked:** decisions.jsonl (D008) and README; the sample does include synthetic data but the choice originated from a model_default decision entry.
- **Effect on this build:** While using synthetic data is safe, a model_default origin means the agent's default led the choice. Making this guidance explicit in a developer-facing doc prevents ambiguity about when to use synthetic vs licensed clinical content and what approvals are required.
- **Suggested fix (naming_or_disambiguation):** Add a short section in README or a contributor guide: 'Why synthetic data?': explain licensing/PHI reasons, when to swap in real guidelines, and the governance/clinical-review checklist required before using real clinical content.

## [low] Infrastructure as code snippet

- **What was missing:** An example Bicep/Terraform snippet that demonstrates creating an Azure DocumentDB (mongoClusters) cluster using the Microsoft.DocumentDB/mongoClusters resource type.
- **Where the agent looked:** Repository root (no IaC files) and readiness notes that provisioning was intentionally omitted (run environment told builder not to create clusters).
- **Effect on this build:** Users who want to reproduce the end-to-end sample must already have a cluster; providing IaC lowers friction and prevents users from choosing the wrong (databaseAccounts / RU) resource type.
- **Suggested fix (sample_or_quickstart):** Add a minimal 'infra/' directory with a Bicep and/or Terraform AzAPI example showing Microsoft.DocumentDB/mongoClusters with parameters (tier=M30 default, storage minimal, region variable). Document the difference between mongoClusters and databaseAccounts.

