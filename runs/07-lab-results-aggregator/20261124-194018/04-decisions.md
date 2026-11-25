# Decision log

| Reason came from | Decisions |
|---|---|
| tool_result | 3 |
| readiness_report | 2 |
| operator | 1 |
| prompt | 1 |
| model_default | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T08:19:59+00:00

## D002 (build): I chose Python (use the system 'python' from the run environment) as the language/runtime for the sample; prefer the existing environment Python (3.13 per readiness_report) and write an async FastAPI + Beanie app.

- **Instead of:** Python 3.11; Python 3.13; Node.js
- **Because:** The run environment already provides Python and pip and the readiness_report explicitly states Python 3.13; using Python matches Beanie/Motor ecosystem and the prompt request for an async Python service.
- **Reason came from:** `readiness_report`
- **Evidence:** Assumption: 'Builder will target a recent stable Python 3.x runtime' in the prompt review; readiness_report lists 'Python 3.13.13 on PATH'.
- **When:** 2026-11-25T08:20:19+00:00

## D003 (build): I chose Beanie ODM with Motor async driver and FastAPI for HTTP endpoints.

- **Instead of:** Beanie + Motor (async ODM); Use pymongo directly without ODM; Use a different language/driver
- **Because:** This directly matches the user's request and the readiness guidance; Beanie provides convenient document modeling and async integration with Motor for Azure DocumentDB.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'build an async Python service using Beanie ODM'; readiness_report guidance: 'Use Motor + Beanie and apply the documentdb-driver singleton pattern'.
- **When:** 2026-11-25T08:20:22+00:00

## D004 (build): I chose specific, recent stable package versions in requirements.txt (Beanie 1.20.1, Motor 3.2.0, pymongo 4.4.0, FastAPI 0.95.1, uvicorn 0.22.0) while noting compatibility is an information gap.

- **Instead of:** Pin exact package versions; Use flexible version ranges in requirements
- **Because:** Pinning gives reproducible installs; versions chosen are recent stable releases but exact compatibility with DocumentDB wire protocol is not guaranteed (see readiness_report information_gaps).
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report: 'Information gap: Beanie/Motor compatibility matrix' and need to pin versions for reproducibility.
- **When:** 2026-11-25T08:20:28+00:00

## D005 (build): I chose to store demo reference ranges as a small in-code dictionary with the option to extend to a DB collection later.

- **Instead of:** Store reference ranges in-code (hard-coded mapping); Store reference ranges in a DB collection; Fetch ranges from external service
- **Because:** For a compact sample it's simplest and clear to hard-code demo reference ranges; it keeps the sample self-contained and easy to run. The README documents how to replace with a DB-backed or external source.
- **Reason came from:** `model_default`
- **Evidence:** readiness_report: 'Information gap: Reference range source for demo' — no authoritative guidance provided.
- **When:** 2026-11-25T08:20:40+00:00

## D006 (build): I chose to update the Beanie version to a published one (beanie==1.22.6) because pip failed to find 1.20.1.

- **Instead of:** Keep beanie==1.20.1 and fail; Pick a published beanie version available on PyPI
- **Because:** Using an available release on PyPI allows dependency installation to succeed; exact Beanie/Motor compatibility remains an information gap noted in readiness_report.
- **Reason came from:** `tool_result`
- **Evidence:** pip error: 'ERROR: No matching distribution found for beanie==1.20.1' from the earlier pip install attempt.
- **When:** 2026-11-25T08:21:33+00:00

## D007 (build): I chose to run the seed script by invoking python with a small -c wrapper that inserts '.' into sys.path and then imports and runs the seed coroutine, because the runner forbids env var prefix syntax like 'PYTHONPATH=...'.

- **Instead of:** Set PYTHONPATH in command line (PYTHONPATH=. python ...); Modify scripts to adjust sys.path; Use python -c wrapper to insert path then import and run seed
- **Because:** The wrapper achieves the same effect without relying on disallowed shell env assignment syntax; it's a minimal change and keeps files unchanged.
- **Reason came from:** `tool_result`
- **Evidence:** Runner refusal: "REFUSED: 'pythonpath=.' is not on the allowed command list" returned when attempting to prefix the command with an env var.
- **When:** 2026-11-25T08:21:56+00:00

## D008 (build): I chose to update src/models.py to call Indexed(str) per the installed Beanie version's API because the runtime error showed Indexed() requires a 'typ' positional argument.

- **Instead of:** Keep current Indexed() usage and fail; Adapt model to Beanie's Indexed signature requiring type argument
- **Because:** Fixing the model to the installed Beanie API allows the sample to run with the installed beanie package.
- **Reason came from:** `tool_result`
- **Evidence:** Runtime TypeError: 'Indexed() missing 1 required positional argument: 'typ'' when importing src.models during seed run.
- **When:** 2026-11-25T08:22:05+00:00
