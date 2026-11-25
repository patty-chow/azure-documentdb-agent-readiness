# Documentation and tooling gaps: 18-adverse-event-reporting-pipeline

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] LLM-driven extraction validation for DocumentDB apps

- **What was missing:** No Azure-DocumentDB-specific guidance on treating LLM outputs as untrusted: canonicalization of drug names, mapping severities to controlled vocabularies, logging parse confidence, quarantining ambiguous parses, and whether to store raw_text.
- **Where the agent looked:** Agent skill searches and docs (documentdb-* skills), and Microsoft Learn searches for 'LLM extraction validation' returned no service-specific guidance.
- **Effect on this build:** Builder validated LLM JSON via Pydantic but did not canonicalize drug names, map severity to enums, log parse confidence, or quarantine ambiguous results. This left potential risk of incorrect structured data being stored.
- **Suggested fix (learn_doc):** A short Microsoft docs page 'LLM extraction with Azure DocumentDB' that: (1) describes validation and canonicalization steps for LLM outputs, (2) shows code snippets for mapping severity to an enum and normalizing drug names, (3) demonstrates logging parse confidence and moving low-confidence parses to a quarantine collection, and (4) mentions privacy considerations for storing raw_text.

## [high] Idempotent seed script pattern

- **What was missing:** A small example pattern for idempotent seeding (unique key selection, unique index creation, upsert/bulk-upsert pattern) in the agent kit docs or quickstarts.
- **Where the agent looked:** documentdb-indexing, documentdb-local-deployment skills and README quickstarts; no dedicated seed-idempotency example found.
- **Effect on this build:** The repo's seed.py currently inserts duplicates on repeated runs. This increases sample clutter and could confuse users verifying aggregation counts.
- **Suggested fix (sample_or_quickstart):** Add a 'seed idempotency' recipe showing an idempotent seed implemented via (a) create unique index on business key(s) and (b) use update_one(..., upsert=True) in a loop or bulkWrite with upsert semantics. Include example code for Python/pymongo and a brief explanation of trade-offs.

## [high] Beanie/Async client quickstart clarification

- **What was missing:** An explicit, small code snippet showing exactly how to create and pass PyMongo's Async client into init_beanie in the context of FastAPI startup (the quickstart exists but builders may confuse MongoClient vs Async client).
- **Where the agent looked:** Beanie quickstart found in events, but the run showed the builder implemented a synchronous MongoClient and left a comment expecting Async usage.
- **Effect on this build:** The sample's startup uses pymongo.MongoClient rather than Async client; this was a code-level divergence from the documented recommended pattern and can cause confusion for users copying the sample.
- **Suggested fix (discoverability):** Add a short code snippet in the Beanie quickstart and the documentdb-driver/connection skills showing AsyncMongoClient usage in FastAPI startup and a minimal example that passes the async client to init_beanie.

## [medium] Testing strategy for DocumentDB samples (unit vs integration)

- **What was missing:** Guidance and examples showing how to structure tests so unit tests run offline (mocking/mongomock or the DocumentDB local gateway) and integration tests are gated by an env var and run only when DOCUMENTDB_URI is provided.
- **Where the agent looked:** documentdb-local-deployment skill and quickstarts; no explicit test guidance that shows offline unit-test patterns and test markers for integration tests.
- **Effect on this build:** The sample README claims pytest runs lightweight unit tests, but no tests were provided. Owners may publish samples that claim test coverage they do not have.
- **Suggested fix (agent_kit_rule):** A test-authoring rule and short sample test suite: (1) example unit test using mongomock or pytest fixtures to test extraction and Pydantic validation offline, (2) example integration test that runs only when DOCUMENTDB_URI is set, (3) CI guidance to separate these test categories.

## [medium] IaC examples for DocumentDB vCore clusters (mongoClusters)

- **What was missing:** A ready-to-copy Bicep/Terraform example using Microsoft.DocumentDB/mongoClusters and the CLI command examples to list connection strings.
- **Where the agent looked:** Microsoft Learn search found mongoClusters docs, but the sample repo had no IaC snippet.
- **Effect on this build:** Users who expect IaC in the gallery will not find a ready template and may attempt to use outdated resource types (databaseAccounts) which would fail for vCore clusters.
- **Suggested fix (mcp_tool_or_description):** Add a minimal Bicep and Terraform snippet that creates a mongoClusters resource with parameterized tier, storage, and region, plus az documentdb mongocluster list-connection-strings usage examples for consumers.

## [medium] Pinning test matrix guidance

- **What was missing:** A short guideline listing known-good package-version combinations for Beanie + PyMongo + Python versions that are tested with DocumentDB.
- **Where the agent looked:** Beanie quickstart and package docs (partial), but no consolidated pinned matrix.
- **Effect on this build:** requirements.txt pins some packages but leaves others as ranges; that reduces reproducibility of the sample runs.
- **Suggested fix (discoverability):** Add a 'supported versions matrix' doc to the agent kit or quickstart that shows exact beanie/pymongo/fastapi/uvicorn versions tested with the sample and how to update them.

