# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 8 |
| prompt | 3 |
| operator | 1 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T07:59:16+00:00

## D002 (build): I chose Node.js with Express and Mongoose for the sample app.

- **Instead of:** Python/Flask; Node.js/Express with Mongoose (chosen); Go with mongo driver
- **Because:** The prompt explicitly requested Node.js and Mongoose, so this aligns directly with the user's request.
- **Reason came from:** `prompt`
- **Evidence:** Sample prompt: 'build a Node.js LangChain agent using Mongoose'
- **When:** 2026-11-25T07:59:32+00:00

## D003 (build): I chose Mongoose 7.x (e.g., ^7.3.0) as the driver version.

- **Instead of:** Mongoose 9.x; Mongoose 8.x; Mongoose 7.x (chosen)
- **Because:** Mongoose 7.x is compatible with Node 24 and matches the prompt-review assumption; it supports modern features and is widely used.
- **Reason came from:** `model_default`
- **Evidence:** assumption from prompt review: 'Use Mongoose latest 7.x compatible with Node 24'
- **When:** 2026-11-25T07:59:36+00:00

## D004 (build): I chose to use the existing, pre-provisioned DocumentDB cluster and read the connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Use Azure provisioning (Bicep/az) to create cluster; Provision new cluster (not allowed); Use existing cluster via connection string from env (chosen)
- **Because:** The environment already provides a reachable cluster and provisioning new resources is disallowed by policy; reading the connection string from env is secure and standard.
- **Reason came from:** `prompt`
- **Evidence:** Run environment: 'A vector-capable Azure DocumentDB cluster ... connection string is in the environment variable DOCUMENTDB_URI.'
- **When:** 2026-11-25T07:59:38+00:00

## D005 (build): I chose to normalize each drug pair into a single sorted key `normalizedPair` (e.g. 'aspirin|ibuprofen') and index that field for efficient pair lookups.

- **Instead of:** Store pair as separate fields and query both ways; Normalize pair into a single sorted key (chosen); Use embedded subdocuments per drug with arrays
- **Because:** A single normalized key simplifies queries for pairwise interactions and allows a single equality index lookup; it also avoids needing OR queries on drugA/drugB permutations.
- **Reason came from:** `model_default`
- **Evidence:** assumption from prompt review: 'Normalize pairs by sorting drug names so queries can search a single field.'
- **When:** 2026-11-25T07:59:49+00:00

## D006 (build): I chose to create a single-field index on `normalizedPair` and additional single-field indexes on `drugA` and `drugB`.

- **Instead of:** No indexes; Index on drugA and drugB only; Single-field index on normalizedPair plus indexes on drugA/drugB (chosen)
- **Because:** Index on normalizedPair makes pair lookups efficient; drugA/drugB indexes help other query patterns and improve seed/upsert performance.
- **Reason came from:** `model_default`
- **Evidence:** assumption from prompt review: 'Create a compound or single-field index on normalizedPair and additional indexes on drugA and drugB.'
- **When:** 2026-11-25T07:59:52+00:00

## D007 (build): I chose OpenAI as the LLM provider and will read the API key from OPENAI_API_KEY at runtime.

- **Instead of:** Use OpenAI as LLM provider (chosen); Use Anthropic or other provider
- **Because:** OpenAI is widely available and supported by LangChain; using OPENAI_API_KEY is a common convention and matches many examples.
- **Reason came from:** `model_default`
- **Evidence:** readiness_report: 'LLM provider and model selection is unspecified; builder must choose.'
- **When:** 2026-11-25T07:59:55+00:00

## D008 (build): I chose to implement an HTTP JSON API (Express) with POST /check-interactions and a CLI script that invokes the same logic for ad-hoc runs.

- **Instead of:** CLI-only app; HTTP JSON API + CLI helper (chosen); Serverless function only
- **Because:** An Express API is simple to run locally and easy to test; CLI helper is convenient for quick demonstrations without making HTTP calls.
- **Reason came from:** `model_default`
- **Evidence:** assumption from prompt review: 'Implement an HTTP JSON API (Express) ... Provide a small CLI script'
- **When:** 2026-11-25T07:59:57+00:00

## D009 (build): I chose to provide an idempotent seed script that upserts ~12 example interaction documents by normalizedPair to the `sample_healthcare_03` database.

- **Instead of:** Write ~5 seed documents; Write 10-20 seed documents with upsert by normalizedPair (chosen); No seed data
- **Because:** This gives enough realistic sample data to demonstrate pairwise queries without being large; upsert avoids duplicates on repeated runs.
- **Reason came from:** `model_default`
- **Evidence:** assumption from prompt review: 'Provide a small, idempotent seed script that loads ~10-20 example interaction documents'
- **When:** 2026-11-25T08:00:00+00:00

## D010 (build): I chose to run unit tests after installing dependencies and before seeding the live cluster to validate local logic and avoid accidental DB writes during test run.

- **Instead of:** Run unit tests (jest) before seeding; Run seed first then tests (chosen)
- **Because:** Tests exercise local heuristic LLM fallback and ensure code loads; safer to run tests before seeding the live database.
- **Reason came from:** `model_default`
- **Evidence:** Standard practice: run unit tests to check code paths before modifying external systems.
- **When:** 2026-11-25T08:01:13+00:00

## D011 (build): I chose to lazy-load the LangChain/OpenAI client inside the function and avoid requiring 'langchain' at module load time so tests without OPENAI_API_KEY can run without the LangChain package being imported.

- **Instead of:** Keep unconditional langchain import causing test failures; Lazy-load LangChain only when OPENAI_API_KEY is present (chosen)
- **Because:** Lazy-load prevents test-time require errors and is acceptable because LLM calls are optional and only happen when OPENAI_API_KEY is set.
- **Reason came from:** `tool_result`
- **Evidence:** Test failure: 'Cannot find module langchain' when running jest without OPENAI_API_KEY; the code imported langchain at module scope.
- **When:** 2026-11-25T08:01:18+00:00

## D012 (build): I chose to explicitly set the database name to 'sample_healthcare_03' in the Mongoose connection options so the sample uses the prescribed database.

- **Instead of:** Leave DB as 'test' (current); Explicitly set dbName to 'sample_healthcare_03' in mongoose connect (chosen)
- **Because:** Ensures the sample creates/uses the specified database regardless of connection string defaults, making verification consistent with the prompt.
- **Reason came from:** `prompt`
- **Evidence:** skill_md run environment: 'Use the database named sample_healthcare_03 for everything this sample creates.'
- **When:** 2026-11-25T08:02:26+00:00

## D013 (build): I chose to create the required indexes using Mongoose's model.syncIndexes() in a short script because the app uses Mongoose and this keeps index definitions with the schema.

- **Instead of:** Use documentdb MCP create_index API; Call Mongoose model.syncIndexes() from sample code (chosen)
- **Because:** Centralizing index creation in Mongoose keeps schema and indexes in the same place and is idempotent for sample runs.
- **Reason came from:** `model_default`
- **Evidence:** The schema declared indexes (drugA, drugB, normalizedPair) in src/models/interaction.js; Mongoose syncIndexes will create them in the connected DB.
- **When:** 2026-11-25T08:03:06+00:00
