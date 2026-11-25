# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 7 |
| prompt | 6 |
| operator | 3 |
| readiness_report | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T09:23:28+00:00

## D002 (build): I chose Python with FastAPI + Beanie ODM

- **Instead of:** Use Node/TypeScript; Use Python (FastAPI + Beanie)
- **Because:** The user requested an async Python service and the prompt review recommended FastAPI and Beanie; Python fits the async, Motor driver, and Beanie ODM usage.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt review: 'Use a current CPython 3.11 (or 3.10) runtime' and 'Implement an HTTP API using FastAPI'
- **When:** 2026-11-25T09:23:47+00:00

## D003 (build): I chose to use permissive version constraints (e.g., beanie>=1.0, motor>=3.0, pymongo>=4.0) in requirements.txt

- **Instead of:** Pin exact Beanie/Motor/pymongo versions; Use open version ranges (>=) so pip installs compatible latest)
- **Because:** No authoritative pinned versions available; allowing pip to install recent compatible releases reduces risk of install-time mismatch while keeping sample maintainable. I'll log this as model_default where needed.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'Missing exact package/version pins for Beanie + Motor + pymongo'
- **When:** 2026-11-25T09:23:58+00:00

## D004 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T09:25:46+00:00

## D005 (build): I chose Python with FastAPI and Beanie (async Motor)

- **Instead of:** Node/TypeScript; Python FastAPI + Beanie/Motor; Go + Mongo driver
- **Because:** The prompt explicitly asks for async Python and Beanie; FastAPI is a common async web framework suitable for this sample.
- **Reason came from:** `prompt`
- **Evidence:** User: 'build an async Python SWIFT message ingestion service using Beanie ODM'
- **When:** 2026-11-25T09:26:10+00:00

## D006 (build): I chose to pin specific recent package versions in requirements.txt (Beanie, Motor, PyMongo, FastAPI, Uvicorn, python-dotenv)

- **Instead of:** Use latest unpinned package versions; Pin known-compatible versions
- **Because:** Pinning reduces surprises during pip install and helps reproducibility; versions chosen are recent and likely compatible. If compatibility issues arise, they will be reported in verification.
- **Reason came from:** `model_default`
- **Evidence:** readiness_report: 'Exact package/version pins for Beanie + Motor + pymongo compatible with Mongo wire 7.0' is an information gap
- **When:** 2026-11-25T09:26:13+00:00

## D007 (build): I chose to read the connection URI from the environment variable DOCUMENTDB_URI at runtime and provide a .env.example with placeholders

- **Instead of:** Read credentials from a config file; Embed connection string in code; Read DOCUMENTDB_URI from environment variables
- **Because:** This matches the run environment instructions and avoids committing secrets to source control.
- **Reason came from:** `prompt`
- **Evidence:** skill_md: 'Its connection string is in the environment variable `DOCUMENTDB_URI`. Read it from the environment at run time. Never write its value into a file'
- **When:** 2026-11-25T09:26:29+00:00

## D008 (build): I chose a single collection 'swift_messages' with a required 'message_type' field and polymorphic parsing

- **Instead of:** Use separate collections for MT103 and MT202; Use a single polymorphic collection 'swift_messages' with message_type field
- **Because:** Single collection simplifies aggregation across message types and matches the assumption in the prompt review; fewer collections keeps the sample compact.
- **Reason came from:** `prompt`
- **Evidence:** assumptions_from_prompt_review: 'Implement two Beanie Document models or a single polymorphic model in one collection named 'swift_messages' ...'
- **When:** 2026-11-25T09:26:32+00:00

## D009 (build): I chose to create explicit indexes programmatically at app startup using the connected Motor/PyMongo client

- **Instead of:** Let Beanie create indexes implicitly via model Settings; Manually create explicit indexes with Motor/pymongo
- **Because:** Explicitly creating indexes makes the sample behaviour clear and ensures the compound and unique indexes are created with intended options; it's easy to verify via MCP tools.
- **Reason came from:** `model_default`
- **Evidence:** documentdb-indexing skill guidance suggests picking index shapes deliberately; Beanie's automatic index creation is not as explicit
- **When:** 2026-11-25T09:26:35+00:00

## D010 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T09:32:06+00:00

## D011 (build): I chose Python 3 (CPython 3.13) with FastAPI for an async web sample.

- **Instead of:** Node.js/TypeScript with Express; Python with FastAPI; Go with Gin
- **Because:** Python is requested in the sample prompt and Beanie (Python ODM) is specified; FastAPI provides an async HTTP surface suitable for ingest and aggregation endpoints.
- **Reason came from:** `model_default`
- **Evidence:** Assumption: 'Use a current CPython 3.11 (or 3.10) runtime' and readiness_report: 'Python 3.13.13'
- **When:** 2026-11-25T09:32:38+00:00

## D012 (build): I chose to use Beanie ODM for models and Motor (async) as the underlying client for bulk writes, while initializing Beanie for model validation.

- **Instead of:** Use Motor (async) for driver; Use PyMongo AsyncMongoClient (pymongo async); Use synchronous PyMongo
- **Because:** Beanie provides ODM features requested; Motor is commonly used with Beanie and supports async bulk insert via insert_many; documentdb-connection notes PyMongo Async available but Motor is acceptable per prompt assumptions and installed skills.
- **Reason came from:** `model_default`
- **Evidence:** Assumption: 'Use Beanie (1.x) with Motor (async PyMongo driver) 3.x and pymongo 4.x' from the prompt review.
- **When:** 2026-11-25T09:32:41+00:00

## D013 (build): I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Read connection string from config file; Read connection string from environment variable DOCUMENTDB_URI; Hardcode connection string in file
- **Because:** Security best-practice and requirement from the prompt not to write secrets into files.
- **Reason came from:** `prompt`
- **Evidence:** skill_md: 'Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time.'
- **When:** 2026-11-25T09:32:44+00:00

## D014 (build): I chose a single collection named 'swift_messages' with a required 'message_type' field to store both MT103 and MT202 messages.

- **Instead of:** Create separate collections for MT103 and MT202; Use a single collection 'swift_messages' with message_type field (MT103/MT202)
- **Because:** Simpler sample and allows aggregation across message types; keeps schema compact and demonstrates polymorphic storage in one collection per sample requirements.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Implement two Beanie Document models or a single polymorphic model in one collection named "swift_messages" with a required "message_type" field'
- **When:** 2026-11-25T09:32:51+00:00

## D015 (build): I chose to include an idempotent create_indexes.py script that creates a unique index on message_id and a compound index on (message_type, value_date) and that the seed script will call it. Index creation uses Motor driver.

- **Instead of:** Create indexes via driver code at startup; Create indexes via a separate index script; Do not create indexes (leave to user)
- **Because:** Indexing improves aggregation performance; an idempotent script is safe to run repeatedly and aligns with sample reproducibility.
- **Reason came from:** `model_default`
- **Evidence:** Assumption: 'Create indexes on fields used in aggregation and lookups: e.g., compound index on (message_type, value_date) and an index on amount/value fields.'
- **When:** 2026-11-25T09:32:54+00:00

## D016 (build): I chose to implement a simple regex-based parser that extracts common SWIFT tags (:20:, :32A:, :50K:, :59:, etc.) and to document the simplified assumptions and that this is not a complete SWIFT parser.

- **Instead of:** Implement full SWIFT parser using external library; Implement a small regex-based parser for key tags and document the assumptions
- **Because:** A full SWIFT parser is out of scope for the sample; a lightweight parser demonstrates ingestion/parsing and keeps sample simple and self-contained.
- **Reason came from:** `model_default`
- **Evidence:** readiness_report information_gaps: 'No canonical SWIFT MT103/MT202 samples', and assumption that builder must provide example messages and mapping.
- **When:** 2026-11-25T09:32:57+00:00

## D017 (build): I chose Motor insert_many for bulk writes after Beanie validation.

- **Instead of:** Beanie insert per-document; Motor insert_many bulk
- **Because:** Motor insert_many offers better throughput for batches; Beanie will be used to validate/construct documents before bulk insert.
- **Reason came from:** `model_default`
- **Evidence:** Need for bulk throughput and driver best-practice to use driver bulk APIs.
- **When:** 2026-11-25T09:33:07+00:00
