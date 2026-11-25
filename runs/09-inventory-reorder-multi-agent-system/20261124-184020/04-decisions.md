# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 2 |
| operator | 1 |
| readiness_report | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T05:35:54+00:00

## D002 (build): I chose Python 3.11 (via the `python` on PATH) for the sample app.

- **Instead of:** Node.js/TypeScript; Python 3.10/3.11
- **Because:** Python is the requested language in the sample prompt and the run environment provides python/pip; Python 3.11 is a recent and compatible choice for LangChain and PyMongo.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt review: 'Use a recent Python 3.10 or 3.11 interpreter'.
- **When:** 2026-11-25T05:36:13+00:00

## D003 (build): I chose PyMongo pinned to 'pymongo>=4.3,<5.0'.

- **Instead of:** pymongo 3.x; pymongo>=4.3,<5.0
- **Because:** PyMongo 4.x is the modern driver compatible with MongoDB 7.0 wire protocol and Azure DocumentDB recommendations; pinning avoids breaking API changes in 5.x.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt review: 'Use PyMongo (the standard MongoDB driver for Python) with a modern pinned version (e.g., pymongo>=4.3,<5.0)'.
- **When:** 2026-11-25T05:36:15+00:00

## D004 (build): I chose to read the connection string from the DOCUMENTDB_URI environment variable at runtime.

- **Instead of:** Use connection string from file; Use DOCUMENTDB_URI environment variable
- **Because:** Security policy forbids committing secrets to files; prompt explicitly required reading DOCUMENTDB_URI from env.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time.'
- **When:** 2026-11-25T05:36:18+00:00
