# Decision log

| Reason came from | Decisions |
|---|---|
| readiness_report | 3 |
| prompt | 2 |
| model_default | 2 |
| operator | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T14:40:55+00:00

## D002 (build): I chose Python 3.10+ as the language/runtime for the sample.

- **Instead of:** Node.js sample; C# sample; Python sample
- **Because:** Python is the common choice for LangChain and pymongo examples; the run environment has Python 3.13 available.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Target Python 3.10+ (code and CI/test suites written for Python 3.10 or 3.11).'
- **When:** 2026-11-25T14:41:08+00:00

## D003 (build): I used the PyMongo driver pinned to 'pymongo>=4.3,<5.0'.

- **Instead of:** pymongo 3.x; pymongo >=4.3,<5.0; motor (async)
- **Because:** PyMongo is the standard synchronous MongoDB driver for Python and matches the readiness guidance.
- **Reason came from:** `model_default`
- **Evidence:** Assumption: 'Use the PyMongo driver (pymongo) compatible with MongoDB 7.0; pin to a recent stable release, e.g. pymongo>=4.3,<5.0.'
- **When:** 2026-11-25T14:41:10+00:00

## D004 (build): I chose to use LangChain for agent orchestration and the OpenAI API for LLM calls.

- **Instead of:** Use LangChain library; Implement custom agent without LangChain
- **Because:** The prompt explicitly requested a LangChain agent, and the readiness guidance recommended LangChain.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report instruction: 'Use the standard MongoDB Python driver (pymongo) and LangChain for the agent orchestration; install dependencies in the venv with pip and test the end-to-end run against the live cluster using DOCUMENTDB_URI.'
- **When:** 2026-11-25T14:41:12+00:00

## D005 (build): I chose 'gpt-3.5-turbo' as the default LLM model for prioritization and talking-point generation.

- **Instead of:** gpt-4; gpt-4o-mini; gpt-3.5-turbo
- **Because:** gpt-3.5-turbo is broadly available in most environments and sufficient for demonstration; if a higher-capacity model is available the environment can override via OPENAI_MODEL env var.
- **Reason came from:** `model_default`
- **Evidence:** Assumption: 'Use an OpenAI-compatible chat model via LangChain (e.g. gpt-4o-mini or gpt-4)'; but availability may vary.
- **When:** 2026-11-25T14:41:14+00:00

## D006 (build): I chose to create only conventional (B-tree) indexes from code and not attempt provider-specific vector index creation.

- **Instead of:** Create vector indexes (provider-specific); Only create conventional B-tree indexes
- **Because:** The cluster may support specialized vector indexes but the exact syntax is provider-specific and not available locally; creating B-tree indexes is safe and satisfies sample performance needs.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness guidance: 'Treat vector-index creation as provider-specific: create conventional B-tree indexes (patient_id, last_visit_date) from code, but verify the exact vector createIndex syntax against the provider docs or the DocumentDB Agent Kit before creating vector indexes; include index creation in an idempotent seed script that logs success/failure.'
- **When:** 2026-11-25T14:41:16+00:00

## D007 (build): I chose to read DOCUMENTDB_URI from the environment and use it as-is (if it includes credentials the driver will use them).

- **Instead of:** Use SCRAM credentials from URI; Assume AAD auth
- **Because:** The run environment provides DOCUMENTDB_URI; whether it encodes credentials or requires AAD is unknown and should not be assumed programmatically.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness instruction: 'Always read the connection string from DOCUMENTDB_URI exactly and pass it to the MongoDB driver; do not construct or assume host suffix/port/options.'
- **When:** 2026-11-25T14:41:18+00:00

## D008 (build): I chose not to provision any Azure resources and to use the existing cluster described in the run environment.

- **Instead of:** Provision resources via az/ARM/Terraform; Do not provision resources and use existing cluster
- **Because:** Run policy disallows creating Azure resources and the environment already provides DOCUMENTDB_URI and the target database name.
- **Reason came from:** `prompt`
- **Evidence:** Prompt and readiness report: 'Do not provision new Azure resources; use the existing cluster per skill.md.'
- **When:** 2026-11-25T14:41:21+00:00
