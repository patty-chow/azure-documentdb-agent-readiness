# Decision log

| Reason came from | Decisions |
|---|---|
| readiness_report | 2 |
| model_default | 2 |
| operator | 1 |
| prompt | 1 |
| tool_unavailable | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T14:43:13+00:00

## D002 (build): I chose Python 3.13 (use 'python'/'pip' from the venv)

- **Instead of:** Node.js/TypeScript; Python 3.13
- **Because:** Python is commonly used for LangChain and data processing; the run environment already has Python and pip available.
- **Reason came from:** `readiness_report`
- **Evidence:** Assumption: 'Use Python 3.10 or 3.11 (latest stable 3.x available)'; readiness report: 'Python 3.13.13 on PATH'
- **When:** 2026-11-25T14:43:24+00:00

## D003 (build): I chose PyMongo (pymongo==4.4) as the MongoDB driver

- **Instead of:** pymongo; motor (async); official Mongo C driver bindings
- **Because:** Synchronous PyMongo is simple to use for a small sample and matches recommended patterns for aggregation and $graphLookup.
- **Reason came from:** `model_default`
- **Evidence:** Assumption: 'Use PyMongo (pymongo>=4.0, e.g. pymongo==4.4) and call collection.aggregate(...)'
- **When:** 2026-11-25T14:43:27+00:00

## D004 (build): I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime

- **Instead of:** Use connection string with username/password written into files; Read DOCUMENTDB_URI from environment variable at runtime
- **Because:** Avoids committing secrets and follows run-environment guidance.
- **Reason came from:** `prompt`
- **Evidence:** Run environment: 'Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time. Never write its value into a file'
- **When:** 2026-11-25T14:43:29+00:00

## D005 (build): I chose to attempt $graphLookup and fall back to iterative lookups if unsupported

- **Instead of:** Use $graphLookup in aggregation pipelines; Implement iterative BFS in client code
- **Because:** $graphLookup is more efficient and concise; fallback increases compatibility with clusters that may not support it.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness guidance: 'implement a runtime check that verifies $graphLookup support and falls back to iterative lookups if unsupported.'
- **When:** 2026-11-25T14:43:30+00:00

## D006 (build): I chose to provide optional OpenAI summarization (if OPENAI_API_KEY present) and a local template fallback

- **Instead of:** Include OpenAI summarization and LangChain integration; Provide optional OpenAI summarization controlled by env var and implement a simple local narrative fallback
- **Because:** Avoids requiring a key to run sample while showing how to integrate with LLMs; keeps secrets out of repo.
- **Reason came from:** `model_default`
- **Evidence:** Assumption: 'Use OpenAI for embeddings and chat... read OpenAI API key from environment'
- **When:** 2026-11-25T14:43:35+00:00

## D007 (build): I chose to skip running pytest because pytest is not installed on PATH in this environment

- **Instead of:** Install pytest into the environment and run tests; Skip running pytest because pytest is not installed
- **Because:** Installing pytest is feasible but the run-policy and readiness guidance allow lightweight verification via direct script runs; we already executed the seed and detector scripts directly which exercise the main functionality.
- **Reason came from:** `tool_unavailable`
- **Evidence:** Command runner output: "NOT INSTALLED: 'pytest' was not found on PATH."
- **When:** 2026-11-25T14:45:13+00:00
