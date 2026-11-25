# Documentation and tooling gaps: 04-medical-imaging-metadata-store

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Demo pseudo-embeddings guidance

- **What was missing:** Authoritative public guidance recommending or discouraging deterministic pseudo-embeddings for demos (when OpenAI keys are not available).
- **Where the agent looked:** learn.microsoft.com (vector-search pages), documentdb-agent-kit skills, general web searches for 'pseudo-embeddings demo deterministic'.
- **Effect on this build:** Builder implemented deterministic pseudo-embeddings for demo mode (seed.py, compute_vector.py). No authoritative doc exists to tell agents whether this is acceptable or how to do it safely; agents may either (a) omit embeddings entirely or (b) embed deterministically in a way that confuses users. This increases the chance of inconsistent demo behavior across samples.
- **Suggested fix (learn_doc):** A short Learn page or a subsection in the vector-search quickstart titled 'Demo-mode deterministic embeddings' describing: when demo embeddings are acceptable, a canonical deterministic algorithm (hash-based RNG seeded by text), an environment flag (e.g., USE_DEMO_EMBEDDINGS=true), cautions about production usage, and example code. Include a one-paragraph warning about PHI and a pointer to secrets management guidance.

## [high] Client timeout/pool tuning and retry patterns

- **What was missing:** A concise recommendation in the driver best-practices docs and a small code snippet demonstrating how to set MongoClient options (serverSelectionTimeoutMS, socketTimeoutMS, maxPoolSize) and how to add retries/backoff for transient network and OpenAI errors.
- **Where the agent looked:** documentdb-connection skill, Microsoft Learn quickstarts, code in repo.
- **Effect on this build:** The sample creates a singleton MongoClient but does not set timeouts or retry/backoff. This can cause flaky behavior or pool exhaustion under load or on slow networks; agents following the sample could ship code with no timeouts or retries.
- **Suggested fix (agent_kit_rule):** Add an agent-kit rule and a short code snippet to documentdb-driver/connection skills showing recommended default options and a tiny retry wrapper for embedding/DB calls (e.g., use tenacity with a 3-5 retry max and exponential backoff). Include sample environment variables for pool sizes and timeouts.

## [high] No local/offline unit tests guidance

- **What was missing:** A sample test harness pattern for Azure DocumentDB samples that demonstrates how to run unit tests without a live cluster (using mongomock or dependency-injected clients) and how to mock OpenAI embeddings.
- **Where the agent looked:** repo and skills; no pre-existing sample in agent-kit.
- **Effect on this build:** This sample lacks unit tests; CI and maintainers cannot run quick checks offline. Agents will ship samples with no offline tests unless the pattern is documented and discoverable.
- **Suggested fix (sample_or_quickstart):** A 'Testing DocumentDB samples' page with a minimal pytest example that injects a mocked collection or uses mongomock, plus an example of monkeypatching the OpenAI Embeddings client to return deterministic vectors.

## [high] IaC examples for vCore DocumentDB (mongoClusters) discoverability

- **What was missing:** Clear, discoverable IaC snippets (Bicep/Terraform/az CLI) that use Microsoft.DocumentDB/mongoClusters rather than older databaseAccounts examples, with an example low-cost default config.
- **Where the agent looked:** learn.microsoft.com templates and sample repo; quickstarts sometimes reference older databaseAccounts shapes.
- **Effect on this build:** No IaC included; authors may misuse older resource types and create the wrong resource (RU/Cosmos DB vs vCore DocumentDB), causing confusion and broken instructions.
- **Suggested fix (naming_or_disambiguation):** Add a short 'Provision a vCore DocumentDB cluster' quickstart using Bicep and Terraform showing Microsoft.DocumentDB/mongoClusters with parameters for tier, region, and cost-saving defaults. Add a prominent note contrasting 'mongoClusters' with 'databaseAccounts' and az documentdb vs az cosmosdb CLI groups.

## [medium] Index-parameter tuning guidance discoverability

- **What was missing:** Readable, near-sample guidance that explains why numLists/lBuild/lSearch were chosen and how to change them for larger corpora.
- **Where the agent looked:** README.md, documentdb-vector-search skill resources and Microsoft Learn vector-search pages.
- **Effect on this build:** The builder picked reasonable defaults (numLists=100, lBuild=50) via skill guidance, but README lacks instruction for users to change them for larger data. Users may copy the sample defaults into bigger datasets and suffer poor recall or performance.
- **Suggested fix (discoverability):** Add a short subsection in the sample README titled 'Index parameters and scaling' that: (1) lists parameter defaults used by sample and why; (2) gives recommended ranges/algorithm choices by corpus size (IVF <10k, HNSW 10k-50k, DiskANN>50k); (3) shows how to override via env vars and how to re-create the index safely.

## [medium] Idempotent seeding pattern guidance

- **What was missing:** A canonical seed-script pattern that is safe to run multiple times (upsert or idempotent markers) with a code example in the sample patterns gallery.
- **Where the agent looked:** seed.py, documentdb-data-modeling skill, README.
- **Effect on this build:** The seed script inserts duplicate documents if run multiple times; this makes iterative development noisy and complicates verification scripts that expect predictable counts.
- **Suggested fix (sample_or_quickstart):** Provide a sample-seed template that uses deterministic IDs or replace_one(..., upsert=True) and documents the approach in seed README section. Include a CLI flag --idempotent that toggles upsert mode.

## [medium] Deterministic 'tested driver versions' and dependency pinning guidance discoverability

- **What was missing:** A clear, discoverable guidance page that tells sample authors to pin tested driver versions and where to capture the tested driver versions in README (and to record the 'tested with' matrix).
- **Where the agent looked:** Quickstarts on learn.microsoft.com and repo requirements.txt; some quickstarts mention tested driver versions but the practice is not prominent in the agent-kit rules.
- **Effect on this build:** requirements.txt partially pins pymongo but leaves other dependencies unpinned; this reduces reproducibility of local builds and CI tests.
- **Suggested fix (discoverability):** Add a short doc in the agent-kit describing a 'tested dependencies' section authors should add to README and recommend pin formats (requirements.txt or constraints.txt). Suggest typical pins for fastapi, openai and numpy and provide a CI snippet to regenerate pins.

