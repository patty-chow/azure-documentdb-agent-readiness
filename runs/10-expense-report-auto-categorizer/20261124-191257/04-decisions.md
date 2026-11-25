# Decision log

| Reason came from | Decisions |
|---|---|
| tool_result | 6 |
| model_default | 5 |
| prompt | 4 |
| readiness_report | 3 |
| operator | 2 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T06:54:58+00:00

## D002 (build): I chose Python 3.11 as the target runtime for the sample (developed to be compatible with 3.10–3.11).

- **Instead of:** Python 3.10; Python 3.11; Python 3.13
- **Because:** Most samples target 3.11 and it balances modern features with wide package compatibility.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Assume modern CPython 3.10 or 3.11 (most samples target 3.11)'.
- **When:** 2026-11-25T06:55:19+00:00

## D003 (build): I chose async Motor + Beanie ODM (Beanie + Motor + PyMongo stack).

- **Instead of:** Use synchronous PyMongo with ODM like MongoEngine; Use async Motor + Beanie ODM
- **Because:** Beanie provides Pydantic-based ODM with async support and works naturally with LangChain async flows; follows prompt guidance.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use Beanie (latest compatible release) with Motor (async) and a current PyMongo-compatible driver'.
- **When:** 2026-11-25T06:55:22+00:00

## D004 (build): I chose not to create vector indexes in this sample and instead provide a simple rule-based fallback for categorization when LLM keys are not provided.

- **Instead of:** Create vector index and require an embedding model/dimension; Do not create vector indexes; use rule-based/fallback LLM if embedding model not configured
- **Because:** The embedding model and dimension were unspecified; avoiding vector indexes avoids creating indexes with wrong dimensions and keeps the sample runnable without an API key. I will still support OpenAI if keys are present.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'The sample must choose an LLM provider and embedding model (typical choice: OpenAI...)' and 'Create vector indexes only after you choose the embedding model and confirm its output dimension'.
- **When:** 2026-11-25T06:55:27+00:00

## D005 (build): I chose to make OPENAI_API_KEY optional and implement a deterministic rule-based fallback categorizer if an API key is not present.

- **Instead of:** Require OPENAI_API_KEY; Allow optional OPENAI_API_KEY and fallback to deterministic rule-based classifier
- **Because:** This keeps the sample runnable in environments without LLM credentials while still supporting LLM-driven behavior when keys are provided.
- **Reason came from:** `model_default`
- **Evidence:** Run environment: 'API keys will be read from environment variables (e.g., OPENAI_API_KEY)' but readiness report noted missing LLM choice and potential absence of keys.
- **When:** 2026-11-25T06:55:29+00:00

## D006 (build): I chose to create only conventional B-tree indexes (status, submitter.email) and not create any vector or textSearch indexes in this sample.

- **Instead of:** Create vector index using a chosen embedding model (needs model dim); Skip vector index creation
- **Because:** Avoids configuring vector index dimensions and keeps sample runnable without an embedding model; still provides useful indexes for the main query pattern (find submitted reports).
- **Reason came from:** `readiness_report`
- **Evidence:** documentdb-indexing guidance and readiness report's note about choosing embedding model before creating vector indexes.
- **When:** 2026-11-25T06:55:46+00:00

## D007 (build): I chose to keep agent memory in-process (LangChain ConversationBufferMemory) but also persist categorization decisions per submitter in a 'decisions' collection for cross-session consistency.

- **Instead of:** Persist agent memory in the DB via Beanie; Keep agent memory ephemeral in-process (LangChain ConversationBufferMemory)
- **Because:** This provides immediate session memory for the agent and durable storage of decisions for reuse across sessions without needing a complex memory-DB integration.
- **Reason came from:** `model_default`
- **Evidence:** Assumption and readiness_report: 'use agent memory to apply consistent categorisation decisions across multiple reports in a session' and lack of canonical pattern for persisting memory in Beanie.
- **When:** 2026-11-25T06:55:49+00:00

## D008 (build): I chose to pin Pydantic to v1.10.12 to match Beanie's expectations (Beanie 1.19.1 requires pydantic v1).

- **Instead of:** Change to a Beanie version that supports Pydantic v2; Downgrade Pydantic to v1 to match Beanie
- **Because:** Pinning Pydantic to v1 is the minimal change to make Beanie work in this environment without choosing an untested Beanie version.
- **Reason came from:** `tool_result`
- **Evidence:** ImportError during runtime: 'cannot import name ModelField from pydantic.fields' indicates Beanie expects Pydantic v1 API.
- **When:** 2026-11-25T06:57:07+00:00

## D009 (build): I chose to update Indexed annotations to include the type argument (e.g., Indexed(str, unique=True)) to conform to Beanie's expected signature under pydantic v1.

- **Instead of:** Keep current Indexed(...) usage (Beanie v1 expects type); Change Indexed annotations to include type argument
- **Because:** Fixing the annotation is straightforward and aligns with Beanie's API.
- **Reason came from:** `tool_result`
- **Evidence:** TypeError: Indexed() missing 1 required positional argument: 'typ' from runtime error.
- **When:** 2026-11-25T06:57:18+00:00

## D010 (build): I chose to replace the deprecated Collection inner class with the Settings inner class per Beanie's error message and documentation.

- **Instead of:** Keep old Collection inner class in Beanie models; Use Settings inner class (Beanie requires Settings)
- **Because:** Beanie v1 expects Settings; updating models resolves initialization error.
- **Reason came from:** `tool_result`
- **Evidence:** Deprecation error: 'Collection inner class is not supported more. Please use Settings instead.'
- **When:** 2026-11-25T06:57:28+00:00

## D011 (build): I chose to use dict-based filters (Report.find_one({'report_id': value})) in seed to avoid expression conversion issues with Beanie field wrappers in this environment.

- **Instead of:** Keep using Report.find_one(Report.report_id == value); Use dict-based filter Report.find_one({'report_id': value})
- **Because:** Dict filters are straightforward and reliable across Beanie versions and avoid expression compatibility issues.
- **Reason came from:** `tool_result`
- **Evidence:** Runtime error: AttributeError: 'bool' object has no attribute 'items' during Report.find_one(Report.report_id == ...) suggests expression conversion failed.
- **When:** 2026-11-25T06:57:44+00:00

## D012 (build): I chose to avoid LangChain imports at module import time and to call the OpenAI SDK directly (lazy import) when OPENAI_API_KEY is present, to prevent dependency conflicts with Pydantic versions and to keep runtime simple.

- **Instead of:** Keep LangChain import and try to reconcile pydantic versions; Avoid LangChain and call OpenAI SDK directly when key provided (lazy import)
- **Because:** Direct use of the OpenAI SDK is lighter-weight and avoids pulling in langchain/langsmith requiring pydantic v2; also keeps behavior when OPENAI_API_KEY is absent (fallback) intact.
- **Reason came from:** `tool_result`
- **Evidence:** Runtime import error from langchain/langsmith traced to Pydantic forwardref evaluation and version mismatch after downgrading to pydantic v1.
- **When:** 2026-11-25T06:58:09+00:00

## D013 (build): I chose to implement a small in-process ConversationBufferMemory substitute to avoid importing LangChain (which requires pydantic v2) and to keep the sample runnable.

- **Instead of:** Keep LangChain memory (requires Pydantic v2); Implement a small in-process memory class
- **Because:** A tiny custom memory fulfills the sample's need for session memory without pulling heavy incompatible dependencies.
- **Reason came from:** `tool_result`
- **Evidence:** Import-time errors caused by langchain/langsmith requiring Pydantic v2 after we pinned pydantic to v1 for Beanie compatibility.
- **When:** 2026-11-25T06:58:23+00:00

## D014 (build): I chose to create B-tree indexes on {status:1} and {submitter.email:1} to support querying submitted reports and listing by submitter.

- **Instead of:** Create no indexes; Create B-tree indexes on status and submitter.email
- **Because:** These indexes are low-cost and directly support the app's query patterns (find submitted reports, queries by submitter).
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Create an index on report status ... and on submitter/date' from prompt review and documentdb-indexing guidance recommends single-field indexes for equality queries.
- **When:** 2026-11-25T06:58:45+00:00

## D015 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T07:00:35+00:00

## D016 (build): I chose Python 3.11 with Beanie (ODM), Motor (async Mongo driver) and LangChain for the agent.

- **Instead of:** Use Node.js/TypeScript; Use Python 3.11 with Beanie/Motor and LangChain
- **Because:** The sample prompt requested a Python LangChain agent using Beanie ODM; Python with Beanie and Motor is the natural fit and aligns with the prompt's assumptions.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt review: 'Assume modern CPython 3.10 or 3.11 (most samples target 3.11)'; and 'Use Beanie (latest compatible release) with Motor (async)'.
- **When:** 2026-11-25T07:00:57+00:00

## D017 (build): I chose to use constrained version ranges in requirements (e.g., beanie>=1.19,<2, motor>=3.1,<4, pymongo>=4.3,<5, langchain>=0.0.200,<1) rather than pinning exact micro versions.

- **Instead of:** Use exact pinned library versions; Use broad but constrained version ranges
- **Because:** Avoids failing installs due to too-strict pins while still constraining to compatible generations; exact pins couldn't be confidently chosen from available docs.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'Beanie + Motor + PyMongo version compatibility with MongoDB 7.0 wire protocol' was ambiguous and not authoritative.
- **When:** 2026-11-25T07:01:04+00:00

## D018 (build): I chose Motor (motor.motor_asyncio.AsyncIOMotorClient) as the Mongo driver to use with Beanie in this sample.

- **Instead of:** Use PyMongo AsyncMongoClient (per documentdb-connection skill guidance); Use Motor (as assumed in prompt review and compatible with Beanie)
- **Because:** Beanie integrates directly with Motor; while the documentdb-connection skill recommends PyMongo's AsyncMongoClient for new projects, changing to AsyncMongoClient would require verifying Beanie compatibility. To keep the sample implementable and simple, Motor is used.
- **Reason came from:** `model_default`
- **Evidence:** Prompt-review assumption: 'Use Beanie (latest compatible release) with Motor (async)'; Beanie historically integrates with Motor.
- **When:** 2026-11-25T07:01:25+00:00

## D019 (build): I chose to implement agent memory as an in-session in-memory mapping (merchant -> category) and to include a deterministic rule-based fallback when OPENAI_API_KEY is not provided (so the demo can run without external AI).

- **Instead of:** Call the LLM for categorisation unconditionally; Use session memory and a non-AI fallback when API key is missing
- **Because:** This keeps the sample runnable in the developer environment without exposing secrets while still demonstrating how to wire LangChain in when API key is available. It also meets the prompt requirement of consistent decisions across a session.
- **Reason came from:** `model_default`
- **Evidence:** Assumption: 'Agent memory to apply consistent categorisation decisions across multiple reports in a session' and readiness_report 'LangChain integration pattern for agent memory with Beanie' missing.
- **When:** 2026-11-25T07:01:28+00:00

## D020 (build): I chose not to create vector indexes or use embeddings in this sample to avoid needing to pick and pin an embedding model and dimension (which was not specified), and because this sample focuses on LLM-based categorisation, not vector similarity search.

- **Instead of:** Create vector indexes now and pick embedding model/dimensions; Do not create vector indexes and avoid embeddings in this sample
- **Because:** Avoids making unsupported assumptions about embedding model/dimensions and keeps the sample focused and runnable against the provided cluster without additional index creation.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'LLM and embeddings model choice & embedding dimension' gap; vector index creation requires embedding dimension to be known.
- **When:** 2026-11-25T07:01:31+00:00
