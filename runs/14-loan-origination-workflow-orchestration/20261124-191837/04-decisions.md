# Decision log

| Reason came from | Decisions |
|---|---|
| readiness_report | 6 |
| prompt | 3 |
| operator | 2 |
| model_default | 2 |
| tool_result | 2 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T07:09:41+00:00

## D002 (build): I chose Python 3.13 as the language/runtime for the sample.

- **Instead of:** Node.js/TypeScript; Python 3.13
- **Because:** The environment already provides Python 3.13, and the prompt requested a Python LangChain + Beanie sample.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report: 'Python 3.13.13 (python resolves to virtualenv as described in skill_md)'.
- **When:** 2026-11-25T07:10:04+00:00

## D003 (build): I chose to read the connection string from the DOCUMENTDB_URI environment variable at runtime.

- **Instead of:** Use Microsoft Entra ID (RBAC) authentication; Read connection string from DOCUMENTDB_URI environment variable
- **Because:** Simpler for a sample app and explicitly recommended by the readiness report; avoids embedding secrets and works with the provided cluster.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report guidance: 'Read the connection string from DOCUMENTDB_URI and use the cluster host suffix...'.
- **When:** 2026-11-25T07:10:12+00:00

## D004 (build): I chose Beanie (Beanie + Motor + Pydantic) for the data model and ODM.

- **Instead of:** Use raw pymongo/motor without an ODM; Use Beanie ODM (Pydantic + Motor) as requested by prompt
- **Because:** Beanie was explicitly requested in the prompt and provides Pydantic models with async Motor integration; it fits the sample's needs.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'model each loan application as a state machine document in DocumentDB using Beanie.'
- **When:** 2026-11-25T07:10:19+00:00

## D005 (build): I chose to use a single find_one_and_update that filters on the expected current_state and $pushes the transition record atomically.

- **Instead of:** Use driver-level find_one_and_update atomic update (filter on expected current_state and $push); Use multi-document transactions and sessions
- **Because:** This approach is atomic for single-document updates, simpler to implement, and matches the DocumentDB driver's recommended pattern for single-document state transitions.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report guidance: 'For atomic state transitions use a single findOneAndUpdate / find_one_and_update that filters on the expected current state and $pushes the transition record in the same update'.
- **When:** 2026-11-25T07:10:22+00:00

## D006 (build): I chose to implement deterministic/stub agents by default and allow optional real LLM usage if OPENAI_API_KEY is set in the environment.

- **Instead of:** Require OPENAI_API_KEY and make real LLM calls; Use a deterministic stub LLM by default, and optionally use OpenAI if OPENAI_API_KEY is present
- **Because:** This keeps the sample runnable and deterministic without external API keys while preserving the LangChain integration path for users who want to enable real LLMs.
- **Reason came from:** `model_default`
- **Evidence:** readiness_report information gaps: 'LLM provider and model choice' and 'Do we require live LLM calls?'.
- **When:** 2026-11-25T07:10:25+00:00

## D007 (build): I chose to create a collection index on current_state using the documentdb MCP server's documentdb_create_index tool (connection_profile 'default').

- **Instead of:** Create indexes using Python driver at runtime; Create indexes using the documentdb MCP server create_index tool
- **Because:** Using the MCP server's create_index tool ensures the index is created on the live cluster and is visible to the agent verification tools.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report: 'the documentdb MCP server's connection profile default is connected to that same cluster. Use its tools to inspect collections, indexes and query plans and to verify what the app created.'
- **When:** 2026-11-25T07:10:28+00:00

## D008 (build): I chose to pin explicit dependency versions in requirements.txt to improve reproducibility.

- **Instead of:** Pin dependency versions loosely; Pin explicit dependency versions tested for Python 3.13
- **Because:** Pinned versions reduce CI/install breakage for the sample; exact choices are based on commonly-compatible releases.
- **Reason came from:** `model_default`
- **Evidence:** readiness_report information gap: 'Pinned dependency versions' — no authoritative versions provided, so pinning is required for the sample.
- **When:** 2026-11-25T07:10:30+00:00

## D009 (build): I chose to update requirements to use beanie==1.21.0 because pip reported 1.21.1 wasn't available but 1.21.0 is.

- **Instead of:** Keep beanie==1.21.1 (failed install); Use beanie==1.21.0 which is available
- **Because:** Install failed; switching to an available nearby release preserves compatibility while allowing installation to proceed.
- **Reason came from:** `tool_result`
- **Evidence:** pip install error: 'Could not find a version that satisfies the requirement beanie==1.21.1' and the available versions list includes 1.21.0.
- **When:** 2026-11-25T07:11:25+00:00

## D010 (build): I chose to update requirements to use langchain==0.0.341 because pip reported 0.0.375 wasn't available but 0.0.341 is listed.

- **Instead of:** Keep langchain==0.0.375 (failed); Use langchain==0.0.341 which is available in pip index
- **Because:** Select an available, reasonably recent langchain version to allow installation to proceed.
- **Reason came from:** `tool_result`
- **Evidence:** pip install error listing available langchain versions including 0.0.341.
- **When:** 2026-11-25T07:11:45+00:00

## D011 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T07:14:18+00:00

## D012 (build): I chose Python (use python 3.13 runtime available via 'python' in the environment).

- **Instead of:** Node.js/TypeScript; Python
- **Because:** Sample requested Python LangChain and Beanie; Python ecosystem is the natural choice and runtime is available.
- **Reason came from:** `readiness_report`
- **Evidence:** Assumption in prompt review: 'Assume Python 3.11...'. Readiness report: 'Python 3.13.13 (python resolves to virtualenv as described in skill_md)'.
- **When:** 2026-11-25T07:14:38+00:00

## D013 (build): I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at run time.

- **Instead of:** Read connection string from a file; Read from environment variable DOCUMENTDB_URI; Hard-code connection string in code
- **Because:** Security best practice and prompt instruction: never write secrets into files; sample must be runnable across environments.
- **Reason came from:** `prompt`
- **Evidence:** skill_md: 'Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time.'
- **When:** 2026-11-25T07:14:40+00:00

## D014 (build): I chose to implement deterministic stub 'specialist agents' by default and make real LLM provider optional if OPENAI_API_KEY is set.

- **Instead of:** Use live LLM provider (OpenAI/Azure OpenAI) for agents; Use deterministic local/dummy agents (no external API calls); Make LLM calls optional, conditional on env var
- **Because:** A deterministic stub ensures the sample is reproducible without external API keys; supporting optional OpenAI allows users with keys to demo real LLM agents.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report: 'LLM provider and model choice is an information gap. ... builder must be told whether to include real LLM calls or to stub agents.'
- **When:** 2026-11-25T07:14:46+00:00

## D015 (build): I chose Beanie for document models and motor for raw atomic find_one_and_update operations (Beanie models will be used but atomic transitions will call the underlying motor collection).

- **Instead of:** Use Beanie for models and raw motor for updates; Use only pymongo/motor without Beanie; Use ODM like odmantic
- **Because:** Beanie provides typed models and convenient async interactions; using motor for atomic find_one_and_update follows documentdb-driver guidance for atomic state transitions and avoids ORM limitations for atomic ops.
- **Reason came from:** `prompt`
- **Evidence:** Sample prompt: 'model each loan application as a state machine document in DocumentDB using Beanie.' Also documentdb-driver skill: 'Use singleton MongoClient and connection reuse.'
- **When:** 2026-11-25T07:14:52+00:00
