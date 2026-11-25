# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 10 |
| readiness_report | 7 |
| operator | 2 |
| skill | 1 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T09:40:42+00:00

## D002 (build): I chose Node.js with Express and Mongoose (mongoose@7) for the sample app.

- **Instead of:** Python/Flask; Go/gin; Node.js/Express
- **Because:** Node.js is specified by the prompt; Express + Mongoose is a familiar stack for MongoDB-style samples and matches developer expectations.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt review: 'Implement as a normal single-process Node.js sample' and readiness report: 'Node.js 24, npx, npm available.'
- **When:** 2026-11-25T09:41:08+00:00

## D003 (build): I chose Mongoose (mongoose@7) as the MongoDB ODM/driver layer.

- **Instead of:** mongodb native driver; Mongoose ODM
- **Because:** Mongoose simplifies schema definitions, indexing, and versioned document modeling for a small sample app.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Use a current Mongoose 7.x release compatible with Node 24 (e.g., "mongoose@7").'
- **When:** 2026-11-25T09:41:12+00:00

## D004 (build): I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Store DocumentDB credentials in code; Read DOCUMENTDB_URI from environment variables
- **Because:** Keeps secrets out of source and follows the prompt's explicit instruction.
- **Reason came from:** `prompt`
- **Evidence:** Skill_md: 'Its connection string is in the environment variable `DOCUMENTDB_URI`. Read it from the environment at run time.'
- **When:** 2026-11-25T09:41:14+00:00

## D005 (build): I chose OpenAI (api.openai.com) as the default LLM provider with model 'gpt-4o-mini' configurable via env.

- **Instead of:** Use Azure OpenAI; Use OpenAI.com API; Use local LLM
- **Because:** OpenAI is commonly available and easy to configure; making provider and model configurable avoids locking users in and allows offline testing with a fallback classifier.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'LLM provider/model must be chosen and exposed in .env.example; suggested models include gpt-4o-mini.'
- **When:** 2026-11-25T09:41:19+00:00

## D006 (build): I chose a single collection 'collateral_assets' where each valuation update is a new document version (same assetId, incrementing version, createdAt timestamp).

- **Instead of:** Separate collections for assets and valuations; Single collection with versioned documents
- **Because:** This matches the prompt's versioned-document requirement and simplifies fetching the latest version via aggregation.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt review: 'Create one collection (e.g. `collateral_assets`) ... updates insert a new document with same assetId and higher version.'
- **When:** 2026-11-25T09:41:23+00:00

## D007 (build): I chose compound index on assetId+version and a single-field index on createdAt.

- **Instead of:** Compound index on assetId+version and createdAt index; No additional indexes
- **Because:** Compound supports fast latest-version queries; createdAt supports time filters.
- **Reason came from:** `skill`
- **Evidence:** documentdb-indexing skill guidance recommending compound ESR indexes and the prompt review suggestion to use {assetId:1,version:-1}.
- **When:** 2026-11-25T09:41:35+00:00

## D008 (build): I chose coverage ratio = sum(latest collateral valuations for eligible assets) / sum(latest liabilities for those assets).

- **Instead of:** Compute coverage as sum(latest valuations) / sum(liabilities); Compute coverage as asset-level ratio averaged
- **Because:** This formula is straightforward, commonly used in collateralisation contexts, and allows the sample to demonstrate aggregation over latest versions; eligibility is determined by LLM-assigned eligibilityTier (exclude 'ineligible').
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report flagged 'Coverage ratio formula' as an information gap and asked builder to choose and document.
- **When:** 2026-11-25T09:41:38+00:00

## D009 (build): I chose to make embeddings optional and not create a vector index in the sample; embedding dimension configurable in .env.example if users want to enable it.

- **Instead of:** Create a vector index and store embeddings; Do not create vector index and make embeddings optional
- **Because:** Vector indexes require matching embedding dimensions and cluster support; keeping this optional keeps sample small and safe while still documenting how to enable it.
- **Reason came from:** `readiness_report`
- **Evidence:** Information gap in readiness report about embedding dimension and vector usage; vector search skill advises making dims configurable.
- **When:** 2026-11-25T09:41:41+00:00

## D010 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T09:44:16+00:00

## D011 (build): I chose Node.js with Express and Mongoose (mongoose@7)

- **Instead of:** Python/Flask; Node.js/Express with Mongoose; Java/Spring
- **Because:** Prompt explicitly requested a Node.js Mongoose service and Node 24 is available in the run environment; Mongoose 7.x is compatible and common.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use a current Mongoose 7.x release compatible with Node 24' and sample asks for 'build a Node.js Mongoose collateral management service'
- **When:** 2026-11-25T09:44:33+00:00

## D012 (build): I chose OpenAI API (OPENAI_API_KEY) as default provider with MODEL_NAME configurable (e.g., gpt-4o-mini or gpt-4o-mini-classification). The sample allows DISABLE_LLM=true to skip classification in environments without keys.

- **Instead of:** Use Azure OpenAI; Use OpenAI (api.openai.com); Use no LLM and hard-code tags
- **Because:** OpenAI is widely available, the openai npm package is easy to use for a simple classification call, and making it configurable keeps sample flexible.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Call an LLM via a provider configured in env vars (e.g., OPENAI_API_KEY). Default to a lightweight classification model (e.g., an OpenAI classification-capable model...)'
- **When:** 2026-11-25T09:44:36+00:00

## D013 (build): I chose to read the DocumentDB connection string from the DOCUMENTDB_URI environment variable at runtime and never write it into repository files.

- **Instead of:** Read DB credentials from a config file; Hard-code the connection string; Read DOCUMENTDB_URI from environment variables
- **Because:** This follows the run environment guidance and security best-practice to avoid committing secrets.
- **Reason came from:** `prompt`
- **Evidence:** Skill_md: 'Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time. Never write its value into any file...'
- **When:** 2026-11-25T09:44:38+00:00

## D014 (build): I chose not to provision any Azure resources and to use the pre-provisioned cluster referenced by DOCUMENTDB_URI.

- **Instead of:** Provision resources inside sample (Bicep/az); Do not provision resources (use existing cluster)
- **Because:** Policy forbids creating resources; the cluster already exists and should be used for verification.
- **Reason came from:** `readiness_report`
- **Evidence:** Run policy: 'Azure resource changes allowed: False.' and skill_md: 'a cluster is already provisioned and reachable'
- **When:** 2026-11-25T09:44:42+00:00

## D015 (build): I chose one collection 'collateral_assets' in database 'sample_banking_06' where each version is a new document sharing assetId and having a version integer and createdAt timestamp.

- **Instead of:** Single collection with embedded versions; Separate collection per version; One collection with each version as new document (version field)
- **Because:** This matches the prompt requirement and keeps schema simple for sample; it enables efficient time-travel queries via aggregation to pick latest version.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Each collateral asset and valuation update as a versioned document in DocumentDB (using a version field and createdAt timestamp). Create one collection (e.g. collateral_assets) ... Updates insert a new document with same assetId and higher version.'
- **When:** 2026-11-25T09:44:45+00:00

## D016 (build): I chose the coverage formula: coverage_ratio = sum(latest valuations of assets (optionally only eligible ones)) / totalLiabilities where totalLiabilities is provided by the client as a query parameter. The endpoint will return both numerator and denominator.

- **Instead of:** Compute coverage as sum(latest valuations) / totalLiabilities provided by client; Compute coverage as per-asset liability fields; Compute coverage using external liability collection
- **Because:** Simple, transparent, and easy for a sample to demonstrate aggregation logic; keeps liabilities external so sample stays focused on collateral management.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report: 'Coverage ratio formula missing; builder must choose and document.'
- **When:** 2026-11-25T09:44:52+00:00

## D017 (build): I chose to make embeddings optional and configurable; the schema includes an optional embedding field, but the sample will not generate embeddings by default. If provided, embeddings dimension and vector-index instructions are in README and .env.example.

- **Instead of:** Create a vector index and store embeddings; Do not include vector embeddings in sample; Make embeddings optional and configurable
- **Because:** Vector search is out of scope for core collateral/coverage demo; keep optional to avoid embedding model dependency and to comply with minimal sample complexity.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report: 'If you include vector search... make embedding dimension configurable'
- **When:** 2026-11-25T09:44:56+00:00

## D018 (build): I chose mongodb-memory-server for unit tests (offline in-memory MongoDB) to allow tests to run without network dependencies; tests set DISABLE_LLM=true to avoid external LLM calls.

- **Instead of:** Use mongodb-memory-server for tests; Mock Mongoose with sinon; Use live cluster for tests
- **Because:** mongodb-memory-server provides a realistic MongoDB server for integration-style tests without requiring the live cluster and keeps CI-friendly behavior.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Include basic unit tests using mocking for the DB and LLM so tests can run offline (e.g., jest with mongodb-memory-server or sinon stubs).','readiness_report' guidance
- **When:** 2026-11-25T09:46:53+00:00

## D019 (build): I chose to replace tests to use jest mocks of the Mongoose model instead of mongodb-memory-server after mongodb-memory-server failed to start (spawn Unknown system error -86).

- **Instead of:** Retry mongodb-memory-server with debug; Replace tests to mock Mongoose model methods
- **Because:** Spawning mongod is failing in this environment; mocking Mongoose gives deterministic offline tests and avoids native binary requirements.
- **Reason came from:** `tool_result`
- **Evidence:** npm test run showed: 'Error: spawn Unknown system error -86' when starting MongoMemoryServer; readiness instructions: 'If a tool keeps failing, stop retrying after the second attempt, log it, and take another route.'
- **When:** 2026-11-25T09:47:33+00:00

## D020 (build): I chose to run the seed script against the live cluster using DOCUMENTDB_URI from the environment to create collections and sample documents for verification.

- **Instead of:** Don't run seed (skip live verification); Run seed against live cluster using DOCUMENTDB_URI from environment
- **Because:** The run environment provides a pre-provisioned cluster and the sample should create the collection and sample docs for demonstration; running seed verifies the app behavior end-to-end.
- **Reason came from:** `readiness_report`
- **Evidence:** skill_md: 'A vector-capable Azure DocumentDB cluster is reachable... connection string is in env DOCUMENTDB_URI' and readiness_report 'Verify against the live cluster: create the collections and indexes, load the sample data...'.
- **When:** 2026-11-25T10:07:42+00:00

## D021 (build): I chose to explicitly set the database name to 'sample_banking_06' when connecting (configurable via DB_NAME env var) to comply with the prompt requirement to use that database.

- **Instead of:** Keep using default DB derived from URI; Explicitly set database name to 'sample_banking_06' via mongoose dbName option
- **Because:** Ensures sample writes target the required database regardless of DOCUMENTDB_URI default database in the connection string.
- **Reason came from:** `prompt`
- **Evidence:** Skill_md: 'Use the database named sample_banking_06 for everything this sample creates.'
- **When:** 2026-11-25T10:08:11+00:00
