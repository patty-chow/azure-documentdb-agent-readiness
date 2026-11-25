# Documentation and tooling gaps: 20-identity-resolution-multi-agent

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Embedding model <-> index dimension mapping

- **What was missing:** A runtime check or authoritative README text that explicitly ties the chosen embedding model to the vector-index 'dimensions' value and fails fast if they differ.
- **Where the agent looked:** README, seed_data.py, documentdb-vector-search skill resources (events show vector-create-diskann-index.md and vector-choose-index-type.md were loaded).
- **Effect on this build:** The sample hardcodes DIM=1536 and defaults the embedding model to text-embedding-3-small; this works for the default but would silently produce wrong index behavior if a user changed the embedding model to one with different dimensionality without also updating DIM. The sample created an index with dimensions=1536 (verified), so mismatch risk remains for users.
- **Suggested fix (learn_doc):** A short README section 'Embedding model and index dimensions' with: 1) recommended default model (text-embedding-3-small) and its dimension (1536); 2) a code snippet showing how to assert embedding dimensionality at startup (call embedding once and assert len(vector)==DIM); 3) instructions to change DIM if using a different model.

## [high] Connection option recommendations (TLS, pool sizing, timeouts)

- **What was missing:** Explicit example and testable helper showing recommended client options (e.g., tls=true when needed, serverSelectionTimeoutMS, maxPoolSize) and how to provide them via env or config.
- **Where the agent looked:** src/db.py (no options set), documentdb-connection and documentdb-driver skills in events.
- **Effect on this build:** Client is created without explicit options; while it works in many environments it may be non-optimal or insecure if DOCUMENTDB_URI lacks expected TLS flags or if pool sizes cause resource pressure at scale.
- **Suggested fix (agent_kit_rule):** Add a small 'connection helper' in src/db.py that accepts and documents env settings like DB_MAX_POOL_SIZE, DB_SERVER_SELECTION_TIMEOUT_MS, and enforces tls=True unless explicitly disabled; include a one-line unit test verifying options are passed to AsyncIOMotorClient.

## [high] Retry/backoff for transient faults

- **What was missing:** A small retry helper or policy and guidance to retry only idempotent operations or use merge-status recording for non-idempotent workflows.
- **Where the agent looked:** app code (no retry logic), documentdb retry/backoff guidance loaded in events (P14, P36).
- **Effect on this build:** No client-side retry/backoff is implemented; transient errors could cause partial merges or failures during seeding/merging in flaky networks.
- **Suggested fix (agent_kit_rule):** Ship a retry utility with exponential backoff and jitter and a recommendation to use it only for idempotent ops; show sample usage for seeding and for read operations, and a pattern for making merge/upsert idempotent.

## [high] Beanie initialization compatibility note

- **What was missing:** Guidance on Beanie/Motor compatibility quirks and a recommended version matrix or a 'if init_beanie fails' recipe.
- **Where the agent looked:** events show init_beanie printed 'MotorDatabase object is not callable' during verification; src/db.py catches and falls back (lines 26-31).
- **Effect on this build:** During verification Beanie init produced a warning/error; the sample falls back to motor writes but lacks a documented troubleshooting step to fix Beanie init issues.
- **Suggested fix (learn_doc):** Add a short troubleshooting subsection describing the error and recommended fixes: correct beanie/motor version matrix, how to pass the MotorDatabase instance to init_beanie, and a one-line example to run if init_beanie fails.

## [medium] Index tuning and algorithm guidance

- **What was missing:** User-facing guidance in README showing when to pick HNSW vs DiskANN vs IVF and how to tune algorithm-specific parameters for larger datasets and cluster tiers.
- **Where the agent looked:** README; vector-search skill resources were consulted in events but the README does not contain the guidance.
- **Effect on this build:** The sample picks reasonable defaults for a small dataset (HNSW) but does not tell a user how to scale or when to change algorithm and parameters. That can lead to poor production choices if copied without reading product docs.
- **Suggested fix (discoverability):** Add an 'Index tuning' subsection: describe HNSW recommended for small/medium dev sets, DiskANN for production M30+ large corpora, explain parameters (lBuild, maxDegree, efSearch), and link to the product vector-search doc with example createIndexes payloads and recommended cluster tiers.

## [medium] Pinned dependency guidance

- **What was missing:** A pinned requirements.txt or guidance about reproducible pins (lockfile / constraints) so samples are reproducible over time.
- **Where the agent looked:** app/requirements.txt (uses >=), package install logs in events.
- **Effect on this build:** The build used floating minimum specifiers; this may cause different environments to install different versions in future runs, making CI and reproductions brittle.
- **Suggested fix (learn_doc):** Replace requirements.txt with pinned versions (requirements.lock) or add a section to README recommending exact pins and providing commands to freeze versions (pip freeze > constraints.txt) and how to use a constraints file in CI.

## [medium] IaC for provisioning (mongoClusters)

- **What was missing:** An example Bicep/Terraform snippet that demonstrates creating the correct Azure DocumentDB resource (Microsoft.DocumentDB/mongoClusters) and notes about cluster tier selection (M30 for vector workloads).
- **Where the agent looked:** Repo (no IaC); readiness findings and CLI docs in events note the correct resource type.
- **Effect on this build:** No IaC included; the sample relies on the run environment's existing cluster. Users copying the sample may try to provision the wrong resource type (databaseAccounts) without clear guidance.
- **Suggested fix (mcp_tool_or_description):** Add an optional 'provisioning' folder with a small Bicep or Terraform example using Microsoft.DocumentDB/mongoClusters and default parameters (tier=M30, low-cost region), plus an 'If you cannot provision, run against a provided cluster' note.

## [medium] README: clean-up and run matrix

- **What was missing:** Explicit clean-up instructions and a description of which tests run offline vs require live cluster resources (and how to run integration tests).
- **Where the agent looked:** app/README.md (no clean-up); tests directory (unit tests present).
- **Effect on this build:** Users may not know how to remove created data or which tests require the live cluster. The builder ran seeding and orchestrator against a live cluster based on environment, but README doesn't document clean-up.
- **Suggested fix (learn_doc):** Add README 'Clean-up' section with commands to drop the sample collections or a small script to delete seed data; add 'Testing' section clarifying unit tests are offline and integration tests require DOCUMENTDB_URI and how to run them.

