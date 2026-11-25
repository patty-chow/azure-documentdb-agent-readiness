# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 6 |
| readiness_report | 2 |
| operator | 1 |
| skill | 1 |
| model_default | 1 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T06:45:25+00:00

## D002 (build): I chose Python (system python 3.13) for the sample runtime and scripts.

- **Instead of:** Node.js/TypeScript; Python
- **Because:** Python is requested in the sample prompt and is the simplest option for LangChain, pymongo and quick scripting on the build machine.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt review: "Use Python 3.10 (or 3.11) virtual environment; pip available as in skill.md."
- **When:** 2026-11-25T06:45:48+00:00

## D003 (build): I chose the Python pymongo driver (pymongo >= 4.4).

- **Instead of:** pymongo 3.x; pymongo >=4.3
- **Because:** Official DocumentDB guidance uses the MongoDB drivers; recent pymongo 4.x is current and supports MongoDB 7.0 wire protocol used by the cluster.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt review: "Use the Python pymongo driver (pymongo >= 4.3, e.g., 4.4)"
- **When:** 2026-11-25T06:45:53+00:00

## D004 (build): I chose a process-wide MongoClient singleton (one client per Python process).

- **Instead of:** create a MongoClient per operation; use a process-wide MongoClient singleton
- **Because:** Best practice for MongoDB drivers and the documentdb-driver skill recommends a singleton to reuse connection pools and avoid exhaustion.
- **Reason came from:** `skill`
- **Evidence:** documentdb-driver skill guidance: "singleton `MongoClient`"
- **When:** 2026-11-25T06:45:55+00:00

## D005 (build): I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Read connection info from config file; .env or environment variable DOCUMENTDB_URI
- **Because:** The run environment and readiness report explicitly require using DOCUMENTDB_URI and forbids writing secrets to files.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report instruction: "Read the cluster connection string from DOCUMENTDB_URI at runtime."
- **When:** 2026-11-25T06:45:58+00:00

## D006 (build): I chose OpenAI (gpt-3.5-turbo) as the LLM provider with a mock fallback for CI/verification.

- **Instead of:** Azure OpenAI; OpenAI (OPENAI_API_KEY); No LLM and only deterministic rules
- **Because:** OpenAI is commonly available and works with LangChain; however the environment has no LLM credentials, so the sample supports a mock mode to allow verification without secrets.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt review: "Use LangChain with an OpenAI provider: model `gpt-3.5-turbo` ... read from OPENAI_API_KEY."
- **When:** 2026-11-25T06:46:01+00:00

## D007 (build): I chose not to provision resources and to use the existing cluster (no infra changes).

- **Instead of:** Provision new DocumentDB cluster; Use the existing pre-provisioned cluster
- **Because:** The run policy forbids creating Azure resources in this run; the environment already provides a reachable cluster to use for the sample.
- **Reason came from:** `prompt`
- **Evidence:** Run policy and readiness_report: "Azure resource changes allowed: False."
- **When:** 2026-11-25T06:46:06+00:00

## D008 (build): I chose an embedded data model: a single `applicants` collection with embedded `transactions` and `pastLoans` arrays.

- **Instead of:** Separate collections for transactions and pastLoans; Embed transactions and pastLoans inside the applicant document
- **Because:** Embedding keeps the sample simple and readable in one document and is appropriate for small, read-heavy sample workloads.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt review: "Embed transaction entries rather than separate collections for this sample."
- **When:** 2026-11-25T06:46:14+00:00

## D009 (build): I chose not to add any additional indexes beyond the default `_id` index for the minimal sample.

- **Instead of:** Create additional indexes (compound/multikey); Rely on default _id index only
- **Because:** The pipeline queries by applicant id and writes a single document; additional indexes would add write cost and are unnecessary for this small sample.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt review: "Use a simple equality query on `_id` (which has the default index). No additional indexes required for the minimal sample."
- **When:** 2026-11-25T06:46:17+00:00

## D010 (build): I chose not to use vector/embeddings in this sample.

- **Instead of:** Use vector/embedding-based retrieval; Do not use vector indexes
- **Because:** Removing vector search keeps the sample focused, avoids choosing an embedding model and configuring vector indexes, and simplifies verification.
- **Reason came from:** `model_default`
- **Evidence:** Prompt and readiness_report: vector search is optional and an information gap; the sample focuses on a rule+LLM scoring pipeline.
- **When:** 2026-11-25T06:46:20+00:00

## D011 (build): I chose to add a mock-LLM mode so the end-to-end pipeline can be verified without real LLM credentials.

- **Instead of:** Require real LLM credentials for verification; Support a mock LLM mode for offline verification
- **Because:** This ensures tests and sample runs can be executed in the build environment despite missing LLM credentials, while still supporting real LLM usage if the developer supplies keys.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report: "An LLM credential/provider is not in the inventory and is required... End-to-end pipeline that calls an LLM will fail; the scoring and explainer agents cannot call an LLM without credentials."
- **When:** 2026-11-25T06:46:24+00:00

## D012 (build): I chose to modify the test to insert the project root onto sys.path at test import time so pytest can find the package when run by the command runner.

- **Instead of:** Set PYTHONPATH when running pytest (not allowed by run_command); Modify tests to adjust sys.path at runtime
- **Because:** The command runner disallows prefixing environment variables; modifying the test to adjust sys.path is a small, practical change that lets tests run in this environment without changing CI commands.
- **Reason came from:** `tool_result`
- **Evidence:** The run_command refused env-prefixed commands: "REFUSED: 'pythonpath=.' is not on the allowed command list"
- **When:** 2026-11-25T06:47:47+00:00
