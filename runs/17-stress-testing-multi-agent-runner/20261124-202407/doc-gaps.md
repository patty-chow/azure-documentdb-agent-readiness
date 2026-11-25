# Documentation and tooling gaps: 17-stress-testing-multi-agent-runner

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Pinned dependency guidance for samples

- **What was missing:** The sample and many skills recommend using supported driver versions, but there is no clear agent-friendly guidance page prescribing exact pinned package versions to use for a given Python target (e.g., the minimal tested set for Python 3.11).
- **Where the agent looked:** Searched installed skills (documentdb-driver, connection) and the repo; no public page prescribing exact pinned versions.
- **Effect on this build:** requirements.txt contains >= ranges rather than exact pins. This leaves sample reproducibility at risk and may cause tests or runtime to use an incompatible package version.
- **Suggested fix (discoverability):** A short 'Supported client versions' doc that lists exact tested package versions for Python (pymongo, python-dotenv, langchain, openai, pytest) per Python minor version (3.10/3.11/3.13). Include a suggested pinned requirements.txt snippet for copy/paste.

## [high] Retry patterns for aggregation and read paths

- **What was missing:** Skills mention retries for transient errors but there is no short, copyable helper in the kit that shows how to wrap aggregate() calls with a small exponential-backoff retry that handles transient network/Mongo errors.
- **Where the agent looked:** documentdb-connection and documentdb-driver skills.
- **Effect on this build:** Aggregations are called with no application retry, leaving long-running or flaky network runs more likely to fail in sample usage.
- **Suggested fix (agent_kit_rule):** Publish a snippet 'retry_aggregation' with a 3-attempt exponential-backoff wrapper using tenacity or a tiny loop that retries on network-related PyMongo exceptions and respects Retry-After-like headers where present.

## [high] Test mocking pattern examples

- **What was missing:** There is no small example in the agent kit showing a robust MagicMock pattern to emulate a database mapping (db['positions'] and db['stress_runs']) such that tests can assert insert_one was called without returning a fresh MagicMock for each __getitem__ call.
- **Where the agent looked:** sample tests and documentdb-local-deployment skill; no explicit small example found.
- **Effect on this build:** One unit test failed due to a fragile __getitem__.side_effect pattern returning a new MagicMock each access. This caused a false negative in unit testing.
- **Suggested fix (learn_doc):** A short testing helper doc showing two patterns: 1) pre-create named MagicMocks for collection names and return them from fake_db.__getitem__; 2) use mongomock for in-memory emulation. Include a short code example illustrating assert fake_db['stress_runs'].insert_one.assert_called_once().

## [medium] Driver pool and timeout defaults for sample code

- **What was missing:** The documentdb-connection and documentdb-driver skills discuss tuning but there is no small discoverable example showing the exact MongoClient args the sample should use for a CLI/long-running process versus a serverless function.
- **Where the agent looked:** documentdb-connection skill and documentdb-driver skill resources; no short 'one-line' example for sample authors.
- **Effect on this build:** The builder logged an intention to set maxPoolSize but the code ended up not setting it. Agents may omit these options unless a concrete snippet is nearby.
- **Suggested fix (agent_kit_rule):** Add a 1-page snippet 'MongoClient for samples' in the documentdb-driver skill showing the recommended MongoClient constructor for CLI/long-running apps and a variant for serverless/short-lived processes, including sensible values for maxPoolSize, serverSelectionTimeoutMS and connectTimeoutMS.

## [medium] IaC example for Microsoft.DocumentDB/mongoClusters

- **What was missing:** The sample lacks an IaC example for the vCore-managed Azure DocumentDB mongoClusters resource; authors may default to databaseAccounts or az cosmosdb commands (wrong resource).
- **Where the agent looked:** Readiness findings and skills; there are Microsoft Learn pages but no small sample file bundled with the agent kit.
- **Effect on this build:** No IaC provided in the repo; readers cannot repro the cluster as code from the sample. This increases friction for users who want to provision a cluster.
- **Suggested fix (sample_or_quickstart):** Add a minimal Bicep or ARM template (and an az CLI snippet) to the repo demonstrating Microsoft.DocumentDB/mongoClusters resource creation with parameters (tier, storage, region), and a note explaining not to run in the sample CI as desktops may lack permission.

## [medium] Vector index create-index examples for Python (DocumentDB-specific payload)

- **What was missing:** Agents often search for 'knnVector' community syntax and will try to use community examples which are rejected by DocumentDB. The vector search docs exist but no concise Python create-index snippet for DocumentDB is bundled for sample copy/paste.
- **Where the agent looked:** documentdb-vector-search skill and Microsoft Learn vector-search pages; no small Python create-index snippet in the kit.
- **Effect on this build:** This sample did not use vector features, but future sample authors may try to create vector indexes with the wrong JSON payload and fail.
- **Suggested fix (sample_or_quickstart):** Add a short Python snippet showing the exact createIndexes JSON for DocumentDB (cosmosSearchOptions with kind:'vector-hnsw' / 'vector-ivf' / 'vector-diskann') that the sample can copy to create vector indexes with given dimensions and similarity.

## [low] Public example run-document schema

- **What was missing:** There is no single, public 'stress-run audit document' schema example. The practice is sensible but only exists in prior knowledge.
- **Where the agent looked:** Searched DocumentDB docs and agent-kit resources; no authoritative run-document schema.
- **Effect on this build:** The sample created a reasonable run document with schemaVersion, but agents cannot confirm a canonical schema or find examples to copy exactly.
- **Suggested fix (learn_doc):** A short page 'Storing audit runs in DocumentDB' that gives an example JSON schema with run_id/_id, created_at, schemaVersion, scenario_parameters, agent_outputs (raw), aggregated_results, and provenance and explains migration strategy.

