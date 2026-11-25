# Documentation and tooling gaps: 11-preference-center-consent-store

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Beanie + Azure DocumentDB examples

- **What was missing:** Concise public examples showing how to create indexes (including TTL) and perform atomic findOneAndUpdate operations using Beanie against Azure DocumentDB; examples for optimistic concurrency patterns that show how to use a consentVersion field in the update filter.
- **Where the agent looked:** Local repo files (.env.example, README, scripts), installed DocumentDB skills search for 'Beanie' returned no direct example; the discovered searches returned no useful result for 'Azure DocumentDB Beanie ODM best practices' (discovery log).
- **Effect on this build:** The builder implemented Beanie models and input validation, but did not adopt atomic $push/$set updates or optimistic-concurrency patterns with version filters (led to partly_met findings for atomic updates and optimistic concurrency). Tests and examples for Beanie usage against DocumentDB are absent, leaving an agent or new builder unsure of idiomatic code patterns.
- **Suggested fix (learn_doc):** A short 'Beanie on Azure DocumentDB' page that includes: 1) example async init_beanie sequence for azure DocumentDB, 2) TTL index creation examples in Beanie and a note about create_index fallback, 3) atomic append-and-update example using find_one_and_update/$push/$set with upsert and returnDocument, 4) optimistic concurrency example using consentVersion in the filter with a retry/conflict handling snippet, 5) note on Beanie index creation/Indexed usage. Put this under the DocumentDB agent-kit docs and reference it from the documentdb-driver and documentdb-data-modeling skills.

## [high] Driver compatibility matrix (Motor / PyMongo / Beanie)

- **What was missing:** An authoritative, small compatibility table listing tested Motor / PyMongo / Beanie versions for Python 3.11+ / 3.13 that are known to work together without ImportError (the run encountered an ImportError caused by a Motor / PyMongo mismatch).
- **Where the agent looked:** DocumentDB skills and Microsoft docs (skill resources were loaded), but there was no single pinned matrix for the sample's stack (searches in discovery returned no single authoritative table).
- **Effect on this build:** The builder had to change the seed script to synchronous pymongo to work around an environment ImportError, and the async app start was not exercised in this run. This reduces confidence that uvicorn app startup will work for users following the README.
- **Suggested fix (discoverability):** Add a short compatibility matrix page to the agent kit docs (or a 'tested-versions.md' in the sample template) listing a small set of tested tuples (Beanie version X, Motor version Y, PyMongo version Z) with a short note on how to reproduce and test the async startup locally. Include a one-line reproduction test command to validate compatibility (e.g., start the app in a disposable virtualenv and confirm init_beanie completes).

## [high] Tests without live cluster — testing guidance

- **What was missing:** Clear guidance and an example on how to write sample tests that do not require the real DocumentDB cluster (patterns: patch init_db in startup, use a local DocumentDB gateway container with TLS, or inject a mock client).
- **Where the agent looked:** Repository files and agent-kit skills; discovery searches returned no useful 'Beanie + local testing' example.
- **Effect on this build:** The included test imports app.main at module scope and therefore triggers startup which requires DOCUMENTDB_URI; as a result tests could not be executed without a live cluster. This prevents CI-style checks and confuses new builders.
- **Suggested fix (agent_kit_rule):** An agent-kit rule and short README section: 1) recommend starting the app lazily in samples (only connect to DB when first request or explicitly when env var RUN_WITH_DB=true), or 2) show how to patch startup/init_beanie in tests (example pytest fixture that monkeypatches init_db to a no-op and provides a fake in-memory client). Provide a concrete test fixture snippet and an example test that runs without a remote cluster.

## [high] Naming and product disambiguation

- **What was missing:** Clear, prominent documentation that explains the product name 'Azure DocumentDB (vCore Mongo offering)', how it differs from 'Azure Cosmos DB for MongoDB (RU)', and that it is not Amazon DocumentDB. The readiness findings show confusion across many docs/agents.
- **Where the agent looked:** Readiness findings and discovered searches; agent-kit and Microsoft Learn contain relevant pages but a concise naming note is not consistently prominent.
- **Effect on this build:** Potential to mis-provision or use the wrong resource type (e.g., databaseAccounts vs mongoClusters) if a builder follows older or ambiguous docs. This is a high-risk area for IaC and sample provisioning.
- **Suggested fix (naming_or_disambiguation):** A short 'Naming note' at the top of the DocumentDB quickstart and sample README clarifying the lineage and difference between Azure DocumentDB (vCore), Azure Cosmos DB for MongoDB (RU), and Amazon DocumentDB, and pointing to the correct Bicep/Terraform resource type (Microsoft.DocumentDB/mongoClusters).

## [medium] Default retention policy guidance

- **What was missing:** A recommended sample default retention period (and rationale) so builders choose consistent values rather than model-defaults. The builder chose 365 days (model_default) but no public guidance defines a sample default.
- **Where the agent looked:** Discovery did not find prescriptive 'consent retention default' guidance; the choice was model_default in decisions (D004/D013).
- **Effect on this build:** The sample uses 365 days and documents it in README, but because this was a model-default choice there is variability between samples. Agents will make arbitrary choices when a default is missing.
- **Suggested fix (learn_doc):** Add a short 'Consent retention' sentence in guidance that recommends a sample default for demos (e.g., 365 days) and explains how to change it via CONSENT_RETENTION_DAYS; include policy caveats and mention legal/regulatory guidance as out-of-scope.

## [medium] Beanie + TTL index example

- **What was missing:** An explicit example showing how to declare TTL indexes in Beanie model Settings or how to create them from Python if Beanie does not express expireAfterSeconds directly.
- **Where the agent looked:** Discovery for 'Azure DocumentDB Beanie create TTL index Beanie' returned no targeted example.
- **Effect on this build:** The builder created the index via client.create_index in both main and seed; a Beanie-specific example would let agent builders do this idiomatically within models or startup code.
- **Suggested fix (learn_doc):** A minimal code snippet showing either: a) how to create TTL index via Beanie startup (call the underlying collection.create_index with expireAfterSeconds=0) or b) how to include TTL semantics in a Beanie Settings block if supported. Put this as a short subsection in the 'Beanie on Azure DocumentDB' doc.

