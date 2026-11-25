# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 3 |
| operator | 1 |
| readiness_report | 1 |
| docs | 1 |
| skill | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T09:05:46+00:00

## D002 (build): I chose Python 3.13 (the system python available) for runtime.

- **Instead of:** Python 3.11; Python 3.10
- **Because:** Use the available system Python to run and verify the sample in this environment without requiring users to install a different minor version.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'Python 3.13.13 available on PATH.'
- **When:** 2026-11-25T09:06:11+00:00

## D003 (build): I chose FastAPI for the app surface with POST /reports and GET /reports/top-events.

- **Instead of:** Flask; Click/CLI; no HTTP surface
- **Because:** FastAPI is lightweight, async-friendly (Beanie uses async), and familiar to Python developers; it maps well to the POST/GET endpoints requested.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Provide a minimal FastAPI HTTP API...'; FastAPI is common for small async Python APIs.
- **When:** 2026-11-25T09:06:14+00:00

## D004 (build): I chose Beanie 2 with PyMongo AsyncMongoClient.

- **Instead of:** Beanie 1 with Motor; Beanie 2 with AsyncMongoClient
- **Because:** Beanie 2 is the recommended version in the official quickstart and works with Azure DocumentDB's async PyMongo client.
- **Reason came from:** `docs`
- **Evidence:** Quickstart: Connect Beanie to Azure DocumentDB notes: 'This quickstart was tested with Beanie 2.2.0 and PyMongo 4.19.0.'
- **When:** 2026-11-25T09:06:35+00:00

## D005 (build): I chose OpenAI (openai-python) as the LLM provider and to read API key from OPENAI_API_KEY.

- **Instead of:** No LLM / rule-based extraction; Anthropic; Local LLM
- **Because:** OpenAI is widely available and has a simple JSON-output prompt pattern; the app will degrade to a direct-insert fallback when the API key is absent.
- **Reason came from:** `model_default`
- **Evidence:** No provider specified in prompt; common samples use OpenAI; readiness_report flagged missing LLM provider choice.
- **When:** 2026-11-25T09:06:39+00:00

## D006 (build): I chose to create a compound index on {drug:1, event:1} programmatically at app startup using the driver's create_index.

- **Instead of:** Create index via Beanie declared indexes at init; Create index programmatically with create_index; Use documentdb MCP createIndexes command
- **Because:** Creating the compound index improves aggregation speed for grouping by drug and event; programmatic creation at startup is simple for a sample app and visible to users.
- **Reason came from:** `skill`
- **Evidence:** documentdb-indexing skill recommends compound ES R patterns and a compound index for query pattern equality on drug and event.
- **When:** 2026-11-25T09:06:43+00:00

## D007 (build): I chose to store raw_text and created_at in addition to extracted structured fields (drug, event, severity, onset_date).

- **Instead of:** Store only structured fields; Also keep raw_text and created_at
- **Because:** Preserving raw_text and timestamp aids debugging and re-extraction without losing source content.
- **Reason came from:** `model_default`
- **Evidence:** Prompt requires storing extracted structured fields; keeping raw_text is useful for audits and later reprocessing; common sample patterns include raw input and timestamp.
- **When:** 2026-11-25T09:06:46+00:00
