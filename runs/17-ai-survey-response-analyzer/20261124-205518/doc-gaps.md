# Documentation and tooling gaps: 17-ai-survey-response-analyzer

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Index creation & management tools discoverability

- **What was missing:** Concrete, copy-paste index JSON and a guarded script to create native vector indexes (vector-diskann/HNSW/IVF) and instructions on the ENABLE_MANAGEMENT_TOOLS opt-in for the MCP server were not present in the repository. README mentions an index but lacks the exact index JSON and CLI/API snippet to create it.
- **Where the agent looked:** Repository (README, seeds/), events.jsonl, documentdb-vector-search skill, Microsoft Learn vector-search docs.
- **Effect on this build:** The builder attempted to create the index via the MCP create_index tool but it failed (management tools disabled). Because the repo lacked explicit index JSON or a guarded script, the build could not recover automatically and required operator manual steps.
- **Suggested fix (mcp_tool_or_description):** Add a file index/create_vector_index.json with the exact createIndexes payload (e.g., vector-diskann on 'embedding' with dimensions placeholder, similarity 'COS', and candidate tuning parameters) and a short script create_index.py that calls the MCP create_index API only when ENABLE_MANAGEMENT_TOOLS=true. README should include the exact portal/CLI steps for manual creation as well.

## [high] Embedding model / dimension guidance

- **What was missing:** A short, prominent sentence explaining the mapping of default embedding model (text-embedding-3-small) to EMBEDDING_DIMENSIONS and how to change both consistently, plus recommended dims for common providers.
- **Where the agent looked:** Repository README, enrich/enrich.py, documentdb-vector-search skill and Microsoft Learn embedding docs.
- **Effect on this build:** The code enforces EMBEDDING_DIMS but operators need to know which embedding model outputs which dims and how to change the vector index to match; lack of this guidance risks dimension mismatches if users swap models.
- **Suggested fix (discoverability):** README subsection 'Embedding model and dimensions' that states the default model and dims (text-embedding-3-small -> 1536), shows how to set OPENAI_MODEL_EMBEDDING and EMBEDDING_DIMENSIONS, and gives a short table of common providers/models and their dims.

## [medium] Aggregation via Beanie (discoverability for authors)

- **What was missing:** The checklist expects aggregation examples executed through Beanie; the repository contains aggregation pipelines but they are executed via pymongo rather than via the Beanie/Motor binding.
- **Where the agent looked:** Repository (aggregates/show_aggregates.py), Beanie docs, documentdb-beanie readiness notes.
- **Effect on this build:** Readers may not see how to run aggregations with the Beanie-initialized client; the sample demonstrates the pipelines but not the Beanie execution path, reducing consistency with the rest of the sample.
- **Suggested fix (learn_doc):** Add a short section to README and an alternate aggregates/show_aggregates_beanie.py demonstrating how to call the same pipelines through the Beanie-initialized database (init_beanie -> SurveyResponse.get_motor_collection().aggregate(...)) and explain reasons to use the Beanie/Motor binding.

## [medium] Tests runnable without cloud

- **What was missing:** Unit tests and a test harness that run without a live cluster (mocks or Gateway docker config) are absent.
- **Where the agent looked:** Repository (no tests directory), documentdb-local-deployment skill for Gateway guidance.
- **Effect on this build:** No fast offline tests for CI or contributors; verifying behavior requires a live cluster or adding mocks which increases friction.
- **Suggested fix (sample_or_quickstart):** Add tests/test_enrich.py that patches SurveyResponse and Motor client (use pytest + pytest-asyncio), plus an optional docker-compose snippet or test fixture that starts the DocumentDB Gateway image for integration tests. Include instructions in README on how to run tests locally without Azure credentials.

## [medium] Beanie + async driver compatibility matrix

- **What was missing:** Clear, short guidance on which Beanie versions are compatible with Motor vs PyMongo AsyncMongoClient and recommended pinned versions.
- **Where the agent looked:** documentdb-connection and documentdb-driver skills, Beanie docs, repository requirements.txt.
- **Effect on this build:** The builder chose Beanie+Motor and pinned versions; future authors may pick incompatible combos (Beanie + PyMongo Async) causing runtime errors.
- **Suggested fix (agent_kit_rule):** Agent-kit rule or a one-page compatibility table that lists tested Beanie releases and the underlying async client (Motor or PyMongo Async) with exact pinned versions and a short snippet for init_beanie for each supported stack.

## [low] Decision to modify sys.path in scripts (packaging guidance)

- **What was missing:** The repository uses a sys.path insertion to make 'src' importable for direct script runs. The sample README does not explain this convenience choice or recommend the proper packaging alternative.
- **Where the agent looked:** app/enrich/enrich.py lines 7-10, events.jsonl D015 and D015's model_default reason.
- **Effect on this build:** Works for local runs but is not idiomatic for published packages and may confuse readers about correct packaging/installation.
- **Suggested fix (learn_doc):** Add a short README note: 'The scripts modify PYTHONPATH for convenience when run directly. For production or proper packaging, install the package (pip install -e .) or use canonical entrypoints; see packaging notes.'

