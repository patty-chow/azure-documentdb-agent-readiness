# Documentation and tooling gaps: 15-digital-onboarding-orchestration

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Optimistic concurrency pattern for Mongo API

- **What was missing:** No authoritative Microsoft Learn page or agent-kit skill page giving a concrete optimistic-concurrency pattern (findOneAndUpdate with version or timestamp) for the Azure DocumentDB Mongo API.
- **Where the agent looked:** Microsoft Learn (transactions, optimistic concurrency queries) and agent skills (data-modeling, connection); searches: 'Azure DocumentDB optimistic concurrency version findOneAndUpdate'.
- **Effect on this build:** The builder did not implement optimistic concurrency (update predicate based on version), so concurrent updates could silently overwrite each other in a real concurrent orchestrator. For this small sample it's unlikely, but in production this would be a correctness risk.
- **Suggested fix (learn_doc):** A short Learn page titled 'Optimistic concurrency with the Mongo API in Azure DocumentDB' containing: (1) the rationale; (2) a code example using findOneAndUpdate with a version field ($inc) or timestamp check; (3) how to combine with driver sessions/transactions; (4) a brief note on conflict-handling and retries. Include a small 'pattern cookbook' snippet referencing Beanie + Motor examples.

## [high] Vector-index dimension and creation helper

- **What was missing:** The sample and prompt did not specify an embedding model or dimension. There is no small helper in samples that constructs the exact createIndexes JSON (cosmosSearch + cosmosSearchOptions) with an embedding-dimension parameter.
- **Where the agent looked:** Microsoft Learn vector-search docs (found algorithm types and createIndexes shape) and agent skills; but no sample helper shipped in the agent-kit.
- **Effect on this build:** The builder avoided creating vector indexes (prompt didn't require them), so the sample does not demonstrate vector-search usage or dims. Agents lacking a helper will guess dims and likely create incorrect vector indexes.
- **Suggested fix (mcp_tool_or_description):** Provide a small helper script or MCP tool that accepts: collection, field name, dims, algorithm (HNSW/IVF/DiskANN) and tunables and emits the correct createIndexes JSON with cosmosSearchOptions. Also add README guidance 'set embedding model and dims before creating vector index'.

## [high] Naming and provider confusion (DocumentDB vs Cosmos DB)

- **What was missing:** Clear, prominent guidance that distinguishes the vCore Azure DocumentDB (mongoClusters) product from legacy Cosmos DB databaseAccounts (RU-based) and shows which CLI/ARM resource to use (az documentdb / Microsoft.DocumentDB/mongoClusters).
- **Where the agent looked:** Readiness findings and Microsoft Learn searches showed many docs referencing databaseAccounts and cosmos examples, which led to confusion.
- **Effect on this build:** Risk that a sample author or agent will target the wrong resource type (databaseAccounts) or wrong CLI group (az cosmosdb) for provisioning; in this run the builder avoided provisioning but the confusion appears in prompts and example comments (.env.example).
- **Suggested fix (naming_or_disambiguation):** A 'Naming and CLI quicknote' near the top of product landing pages and quickstarts: explicitly state 'Use Microsoft.DocumentDB/mongoClusters and az documentdb for vCore DocumentDB clusters; databaseAccounts and az cosmosdb refer to legacy Cosmos DB control plane', with two small code snippets showing the correct Bicep/az commands.

## [medium] Beanie + DocumentDB guidance

- **What was missing:** No public Microsoft guidance documenting Beanie usage patterns with Azure DocumentDB (init_beanie startup, passing sessions into Beanie/Motor operations, and recommended versions).
- **Where the agent looked:** Searches for 'Beanie Azure DocumentDB' and 'Beanie init_beanie Motor' returned only repository examples and prior-knowledge fragments; agent-kit has no official Learn page for Beanie.
- **Effect on this build:** The builder initialized Beanie correctly, but an agent couldn't rely on a canonical public page to decide exact version constraints and session usage. This contributed to model_default decisions about Beanie version pins.
- **Suggested fix (learn_doc):** A small 'Using Beanie with Azure DocumentDB' doc: recommended Beanie versions compatible with the DocumentDB driver, init_beanie example using the cluster client, how to use sessions/transactions with Beanie (passing session objects or using Motor for transaction-sensitive operations), and a short compatibility matrix.

## [medium] Agent-driver guidance: prefer PyMongo Async client vs Motor

- **What was missing:** The agent-kit guidance contradicts prior beliefs: some examples in skills advise using PyMongo Async client for new Python async code but sample uses Motor. There is no single short note saying 'for new Python async code prefer PyMongo AsyncClient; Motor is supported for legacy code.'
- **Where the agent looked:** documentdb-connection skill and public docs; agent-kit notes exist but no compact 'which driver to pick' guidance page aimed at sample authors.
- **Effect on this build:** The builder used Motor which is acceptable, but an agent selecting a driver by default might pick the non-preferred driver or stumble on API differences (tests, init patterns).
- **Suggested fix (naming_or_disambiguation):** Add a short 'Which Python async Mongo driver to choose' note in the documentdb-connection skill and in Quickstarts: advise AsyncMongoClient (PyMongo) as preferred for new async code, list Motor compatibility caveats, and provide a short migration snippet.

## [medium] Tests and CI guidance for Beanie/Motor mocking

- **What was missing:** A brief public example showing how to mock Beanie/Motor sessions for unit tests and separate integration tests that seed the live cluster.
- **Where the agent looked:** Searched repo tests and public docs; found repo-level examples but no Learn page.
- **Effect on this build:** The sample's tests do the right thing (mocking), but an agent authoring tests might not follow the same pattern without a short reference.
- **Suggested fix (agent_kit_rule):** Agent-kit rule + short sample test showing monkeypatching get_client, faking collection methods, and separating integration tests into an 'integration/' folder that run only when an env var is set.

## [medium] Model-default decisions logged without public source

- **What was missing:** Several decisions were made from model_default (e.g., initial Beanie version pin) without an authoritative public doc to cite.
- **Where the agent looked:** decisions.jsonl shows D003 and D004 were model_default; readiness searches did not produce a single 'official' pinned-version recommendation for Beanie.
- **Effect on this build:** Caused iterative edits to pinned versions (D012) and extra iteration. Agents should prefer asking for the repository maintainer's desired driver/ODM versions or use a small guidance page.
- **Suggested fix (discoverability):** Add a 'Recommended third-party dependency versions' line to the DocumentDB quickstart or the agent-kit (a short table: beanie, motor, pymongo compatibility notes).

