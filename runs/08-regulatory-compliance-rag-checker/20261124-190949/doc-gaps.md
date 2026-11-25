# Documentation and tooling gaps: 08-regulatory-compliance-rag-checker

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Copy-paste vector index creation examples

- **What was missing:** A single, copy-paste-ready createIndexes/runCommand JSON snippet for each vector index kind (vector-hnsw, vector-ivf, vector-diskann) that includes dims, similarity, and algorithm-specific params.
- **Where the agent looked:** DocumentDB vector search skill and Microsoft Learn vector-search pages during discovery; app/scripts/create_indexes.py exists but is a placeholder.
- **Effect on this build:** The MCP create-index tool was attempted and failed (management tools disabled). The builder fell back to pymongo runCommand; index listing did not show the expected index. Lack of a simple authoritative example increases the chance a builder will call the wrong API shape and fail silently or create the wrong index.
- **Suggested fix (learn_doc):** A short 'Create a vector index' page containing: (1) three copy-paste JSON examples for createIndexes/runCommand (HNSW, IVF, DiskANN) with dims parameter and recommended default params; (2) a one-liner pymongo runCommand snippet; (3) runbook notes about required privileges and how to verify with documentdb_list_indexes and explain().

## [high] Local gateway quickstart (image + port)

- **What was missing:** A prominent, brief note telling developers to use the DocumentDB Gateway Docker image (ghcr.io/documentdb/documentdb/documentdb-local) and the port 10260, and that mongo:latest on 27017 is not a substitute for feature parity.
- **Where the agent looked:** documentdb-local-deployment skill and local dev notes; README had only a brief mention of local modes.
- **Effect on this build:** The sample provides no local gateway automation; without the gateway a dev might run a plain Mongo image and miss DocumentDB-specific features (cosmosSearch) during testing.
- **Suggested fix (discoverability):** Add a short 'Local development' page with the docker run command, env flags like SKIP_INIT_DATA, and examples on connecting via DOCUMENTDB_URI with port 10260, plus how to run seed_noembed for CI.

## [high] Explain-based index verification

- **What was missing:** A small admin script and README step showing how to run explain('executionStats') for the sample retrieval queries and interpret keysExamined/docsExamined to detect COLLSCANs.
- **Where the agent looked:** documentdb-query-optimization skill; the sample only documents index shapes but not verification steps.
- **Effect on this build:** Without this, authors may ship code that appears to work on tiny datasets but will do COLLSCANs and be unusably expensive at scale.
- **Suggested fix (sample_or_quickstart):** Add scripts/explain_queries.py that runs explain('executionStats') for the sample queries and prints a short health-check; add a paragraph in README telling authors to run it pre-release.

## [high] Embedding model & dims clarity in quickstart

- **What was missing:** The starter prompt did not name an embedding model or the env var names for embeddings/LLM. While the builder chose OpenAI text-embedding-3 (1536) and documented OPENAI_EMBEDDING_MODEL/EMBEDDING_DIMENSIONS in .env.example, this guidance should be explicit in central docs.
- **Where the agent looked:** readiness notes and the repo .env.example: the repo documents a choice but the prompt lacked it.
- **Effect on this build:** If a different embedding model is used and dims are mis-sized, server-side indexes would be misconfigured and retrieval would silently return wrong neighbors.
- **Suggested fix (learn_doc):** Add a short 'Embedding model' section stating recommended default (OpenAI text-embedding-3 = 1536), the env vars to set, and how to change EMBEDDING_DIMENSIONS if you choose another model (with example dims for common models).

## [medium] Server-side hybrid retrieval examples

- **What was missing:** A small example that demonstrates BM25 + vector hybrid (RRF) implemented server-side via createSearchIndexes + $search and an aggregation pipeline or example client-side fusion with exact parameters.
- **Where the agent looked:** documentdb-full-text-search skill and Microsoft Learn hybrid-search docs; repository notes but no working sample.
- **Effect on this build:** The sample implements a lexical fallback and client-side vector scoring only; authors and readers may not see how to implement server-side hybrid retrieval recommended for production.
- **Suggested fix (sample_or_quickstart):** Add a 'hybrid-search.md' quickstart that includes: createSearchIndexes example for BM25, createIndexes example for vector index, a cosmosSearch $search aggregation that runs both and a code snippet showing Reciprocal Rank Fusion server-side or client-side, plus RU-cost considerations.

## [medium] Entra ID OIDC example

- **What was missing:** A concise example showing how to enable Microsoft Entra ID (OIDC) authentication on a cluster and a minimal Python snippet demonstrating driver callback (DefaultAzureCredential + OIDC) to obtain short-lived tokens.
- **Where the agent looked:** documentdb-security skill and Microsoft Learn RBAC docs; sample repo did not include an Entra ID example.
- **Effect on this build:** The sample uses connection strings; teams wanting to show best-practice authentication (no long-lived credentials) have no quick reference in the repo.
- **Suggested fix (learn_doc):** A short 'Auth' page: steps to enable Entra ID on a cluster, create least-privilege principals, and a Python code snippet showing how to provide an OIDC token to pymongo when auth mode is configured.

## [medium] Tests separation (unit vs integration)

- **What was missing:** Clear guidance and test markers that separate unit tests (mongomock, run in CI) from integration tests that require a live cluster, with examples for skipping integration tests by default.
- **Where the agent looked:** repo tests and README; tests include both mongomock-based test and a live-db test (test_seed_and_query.py) with no skip markers.
- **Effect on this build:** CI could fail or run against real resources unintentionally; the build had to adjust tests during verification.
- **Suggested fix (agent_kit_rule):** Add a test policy to the sample: unit tests use mongomock and live tests are marked with pytest markers (e.g., @pytest.mark.integration) and instructions in README on how to run them against a live cluster.

