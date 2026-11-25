# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 3 |
| skill | 3 |
| operator | 2 |
| prompt | 2 |
| tool_result | 2 |
| readiness_report | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T10:28:16+00:00

## D002 (build): I chose Python 3.13 (system python) for the sample runtime and virtualenv.

- **Instead of:** Python 3.11; Python 3.13
- **Because:** The run environment has Python 3.13 available; using the system Python avoids installing another runtimes.
- **Reason came from:** `readiness_report`
- **Evidence:** Assumption: 'Use a modern supported Python (e.g. Python 3.11)'; readiness report: 'Python 3.13.13 on PATH'
- **When:** 2026-11-25T10:28:31+00:00

## D003 (build): I chose Beanie 1.21.x (stable 1.x series) for ODM.

- **Instead of:** Beanie 1.x; Beanie 2.x
- **Because:** Use a stable 1.x series compatible with Motor and existing docs; avoids major API changes in Beanie 2 if not necessary.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'Quickstart: Connect Beanie to Azure DocumentDB' and ambiguity about version; Beanie 1.x is widely used with Motor.
- **When:** 2026-11-25T10:28:34+00:00

## D004 (build): I chose to pin specific package versions in requirements.txt (Beanie==1.21.0, motor==3.1.1, pymongo==4.5.0, langchain==0.0.236, openai==1.0.0, python-dotenv==1.0.0, pytest==7.4.0, pytest-asyncio==0.22.0).

- **Instead of:** Pin recent versions; Leave versions unpinned
- **Because:** Pinned versions improve reproducibility for the sample and tests; pick reasonably recent stable releases.
- **Reason came from:** `model_default`
- **Evidence:** Assumptions_from_prompt_review: 'requirements.txt pinned; include .env.example'
- **When:** 2026-11-25T10:28:45+00:00

## D005 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T10:34:29+00:00

## D006 (build): I chose Python 3 (async) with Motor + Beanie ODM and FastAPI for the sample.

- **Instead of:** Node.js/TypeScript; Python (async, Beanie ODM); Go
- **Because:** The sample and installed skills target Python + Beanie and the readiness_report explicitly instructs using Motor + Beanie for transactions; Python is also the user's requested language.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt review: 'Use a modern supported Python (e.g. Python 3.11) in a virtualenv' and readiness guidance: 'Use Motor + Beanie for the Python ODM'
- **When:** 2026-11-25T10:34:55+00:00

## D007 (build): I chose beanie==1.24.1 and motor==3.1.1 pinned in requirements.txt.

- **Instead of:** beanie==1.x (new API); beanie==0.24.x (older)
- **Because:** Beanie 1.x is the modern stable line; I picked 1.24.1 as a recent 1.x release compatible with Motor 3.x and Python 3.13. This keeps the sample current while avoiding API mismatch.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'Ambiguity: Exact Beanie version expectations' and general compatibility with Motor
- **When:** 2026-11-25T10:34:58+00:00

## D008 (build): I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Use cluster-level secrets in files; Read connection string from environment variable DOCUMENTDB_URI
- **Because:** Security policy forbids writing secrets to files; readiness instructions explicitly require reading DOCUMENTDB_URI from env.
- **Reason came from:** `prompt`
- **Evidence:** skill_md: 'Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time.'
- **When:** 2026-11-25T10:35:01+00:00

## D009 (build): I chose Motor's find_one_and_update with client.start_session() and start_transaction() for atomic state transitions while using Beanie for model definitions.

- **Instead of:** Use Beanie document save for transaction; Use Motor find_one_and_update with session transaction
- **Because:** Beanie provides models but Motor provides explicit session-aware atomic updates; combining them follows best practice and ensures transactions work as intended.
- **Reason came from:** `skill`
- **Evidence:** Readiness guidance: Use Motor + Beanie and implement transaction semantics via client.start_session() and start_transaction()/withTransaction when performing atomic state transitions.
- **When:** 2026-11-25T10:35:16+00:00

## D010 (build): I chose an embedded compact history array on the onboarding document to record transitions (agent, from_state, to_state, ts) rather than a separate audit collection.

- **Instead of:** Embed full audit trail across application; Store only current state and a compact history array (embed)
- **Because:** History is accessed together with the application document and is small per application, so embedding keeps reads simple and consistent with DocumentDB patterns.
- **Reason came from:** `skill`
- **Evidence:** documentdb-data-modeling guidance: 'Embed data accessed together; add a schemaVersion field and history for lazy migration' and the 'embed vs reference' rule.
- **When:** 2026-11-25T10:35:20+00:00

## D011 (build): I chose to create a single-field index on 'state' (for quick queries by processing state) and a compound index on ('applicant_id', 'state') to support lookups by applicant and to follow the ESR ordering (equality then sort/range).

- **Instead of:** No indexes or only default _id; Index on 'state' and 'applicant_name' plus an index on 'created_at'
- **Because:** Queries in the sample will filter by state and occasionally by applicant_id + state; these indexes improve these patterns and keep index count small.
- **Reason came from:** `skill`
- **Evidence:** documentdb-indexing: 'single-field for simple filters' and 'compound ESR: Equality -> Sort -> Range' and keep index budget modest.
- **When:** 2026-11-25T10:35:24+00:00

## D012 (build): I chose to use beanie==1.25.0 after pip reported 1.24.1 is not available.

- **Instead of:** keep beanie==1.24.1; use beanie==1.25.0; use beanie==1.24.0
- **Because:** 1.25.0 is a published, recent 1.x release visible in PyPI and compatible with Motor; switching resolves the install failure.
- **Reason came from:** `tool_result`
- **Evidence:** pip install error: 'Could not find a version that satisfies the requirement beanie==1.24.1'
- **When:** 2026-11-25T10:36:19+00:00

## D013 (build): I chose fastapi==0.98.0 after pip reported 0.98.1 is not available.

- **Instead of:** keep fastapi==0.98.1; use fastapi==0.98.0
- **Because:** 0.98.0 is available and compatible for this sample; switching resolves the install failure.
- **Reason came from:** `tool_result`
- **Evidence:** pip install error: 'No matching distribution found for fastapi==0.98.1'
- **When:** 2026-11-25T10:36:28+00:00
