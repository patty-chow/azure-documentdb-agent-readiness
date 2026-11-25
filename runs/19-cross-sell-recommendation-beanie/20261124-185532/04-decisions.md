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
- **When:** 2026-11-25T06:15:15+00:00

## D002 (build): I chose to use the Python runtime available on the machine (Python 3.13.13) and implement an async FastAPI service with uvicorn.

- **Instead of:** Use Python 3.11 (as in prompt assumption); Use Python available on PATH (3.13.13 per readiness report)
- **Because:** Use the locally available Python version to avoid environment mismatch and make pip installs and runtime execution straightforward.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: "Python 3.13.13 available on PATH (inventory)."
- **When:** 2026-11-25T06:15:45+00:00

## D003 (build): I chose FastAPI for an async HTTP service (uvicorn) to match the async Beanie/Motor usage.

- **Instead of:** Use Flask (sync); Use FastAPI (async)
- **Because:** FastAPI is a standard async framework that integrates well with async Mongo drivers and Beanie ODM.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: "Builder will implement a single-process async HTTP service (no multi-agent orchestration), e.g., FastAPI + uvicorn".
- **When:** 2026-11-25T06:15:47+00:00

## D004 (build): I chose Beanie ODM (beanie>=1.21.1) with motor for async MongoDB access, as the sample requests Beanie specifically.

- **Instead of:** Beanie >=1.16 with compatible motor/pymongo; Use raw motor or pymongo
- **Because:** Beanie provides document models and makes sample code concise; motor is the async driver Beanie uses.
- **Reason came from:** `prompt`
- **Evidence:** Sample prompt: "build an async Python service using Beanie ODM" and assumptions: "use a recent stable Beanie release compatible with Python 3.11".
- **When:** 2026-11-25T06:15:51+00:00
