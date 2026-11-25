# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 5 |
| operator | 1 |
| model_default | 1 |
| readiness_report | 1 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T12:11:54+00:00

## D002 (build): I chose Python 3 (FastAPI) for a single-process service using a venv and FastAPI for HTTP endpoints.

- **Instead of:** Node.js/TypeScript; Python (FastAPI); Go
- **Because:** Python is the environment-provided runtime, widely used for samples, and FastAPI is lightweight and suitable for the small HTTP surface the sample needs.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Default to Python 3.10... use 'python' and 'pip' as environment-provided executables' and prompt review 'Assume a single-process Python service...'
- **When:** 2026-11-25T12:12:21+00:00

## D003 (build): I chose to target the existing DocumentDB cluster and not provision any resources.

- **Instead of:** Use existing cluster (no infra); Provision new cluster with Bicep/Terraform
- **Because:** The run policy forbids creating Azure resources; the environment already has a reachable cluster with DOCUMENTDB_URI.
- **Reason came from:** `prompt`
- **Evidence:** run_policy: 'Azure resource changes allowed: False.'
- **When:** 2026-11-25T12:12:42+00:00

## D004 (build): I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Read connection string from config file; Read connection string from env var DOCUMENTDB_URI
- **Because:** Avoids committing secrets and matches the provided run environment guidance.
- **Reason came from:** `prompt`
- **Evidence:** skill_md: 'Its connection string is in the environment variable `DOCUMENTDB_URI`. Read it from the environment at run time.'
- **When:** 2026-11-25T12:12:45+00:00

## D005 (build): I chose to store attribution output in a separate collection 'attribution_results' with a version field per customer.

- **Instead of:** Embed results in customers collection; Store a separate collection 'attribution_results' versioned per customer
- **Because:** Keeps event and result data separate, allows versioning and auditing, and is easier for marketers to query results.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Store the attribution output as a versioned document per customer.'
- **When:** 2026-11-25T12:12:49+00:00

## D006 (build): I chose a small synthetic seed dataset: ~20 customers with ~500 events total.

- **Instead of:** small (20 customers, few hundred events); large (thousands)
- **Because:** Sufficient to demonstrate attribution models without creating heavy load on the live cluster; idempotent seed script will upsert events.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'small synthetic seed dataset (e.g., a few hundred to a few thousand events across ~20 customers)'
- **When:** 2026-11-25T12:12:52+00:00

## D007 (build): I chose LangChain with OpenAI provider (OPENAI_API_KEY) for the marketer-facing natural language tool.

- **Instead of:** LangChain with OpenAI provider; LangChain with local LLM; No LangChain, custom prompt to OpenAI
- **Because:** OpenAI provider is widely used and available in the environment; LangChain integration with OpenAI is straightforward for this sample.
- **Reason came from:** `model_default`
- **Evidence:** Assumption: 'Assume use of OpenAI-compatible models' and common LangChain patterns.
- **When:** 2026-11-25T12:12:55+00:00

## D008 (build): I chose to pin dependencies in requirements.txt to specific, recent stable versions.

- **Instead of:** Pinned dependency versions; Unpinned latest
- **Because:** Pinned deps provide reproducible installs for sample users.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report: 'Python runtime pin and dependency pins: sample repo should pick a target Python version and pinned requirements.txt.'
- **When:** 2026-11-25T12:13:05+00:00

## D009 (build): I chose to loosen the mongomock pin to >=4.2.0.post1 because pip reported the exact 4.2.0 wheel is unavailable in this environment.

- **Instead of:** Keep mongomock==4.2.0 and fail install; Adjust mongomock spec to available version
- **Because:** Allow installation to proceed with a compatible mongomock release available from PyPI.
- **Reason came from:** `tool_result`
- **Evidence:** pip install error: 'No matching distribution found for mongomock==4.2.0'
- **When:** 2026-11-25T12:14:10+00:00
