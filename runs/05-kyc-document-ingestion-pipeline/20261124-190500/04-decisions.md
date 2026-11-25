# Decision log

| Reason came from | Decisions |
|---|---|
| readiness_report | 3 |
| model_default | 2 |
| tool_result | 2 |
| operator | 1 |
| prompt | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T06:40:09+00:00

## D002 (build): I chose Python 3.13 as the runtime for the sample.

- **Instead of:** Python 3.11; Python 3.13
- **Because:** The run environment reports Python 3.13 is available and pip installs work; using the available runtime avoids compatibility issues in this environment.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report: "Python 3.13.13 on PATH (virtualenv/pip install works)."
- **When:** 2026-11-25T06:40:25+00:00

## D003 (build): I chose to read all secrets (DOCUMENTDB_URI, OPENAI_API_KEY) from environment variables at runtime.

- **Instead of:** Read secrets from code/config files; Read secrets from environment variables
- **Because:** Security best practice and explicit prompt instruction to avoid writing secrets into files.
- **Reason came from:** `prompt`
- **Evidence:** prompt: "Never write a secret, password, key or full connection string into a file. Read them from environment variables, and ship a .env.example with placeholder values."
- **When:** 2026-11-25T06:40:34+00:00

## D004 (build): I chose gpt-4o-mini as the OpenAI model for structured extraction in this sample.

- **Instead of:** gpt-4o-mini; gpt-4.1; gpt-3.5-turbo
- **Because:** gpt-4o-mini balances capability and cost for extraction tasks and is commonly available; the sample focuses on JSON-extraction prompts rather than long conversational context.
- **Reason came from:** `model_default`
- **Evidence:** assumptions_from_prompt_review: "Builder will pick a text model appropriate for extraction (e.g., gpt-4o-mini or gpt-4.1 if available)."
- **When:** 2026-11-25T06:40:44+00:00

## D005 (build): I chose to upsert records by government_id (stable unique identifier) and create a unique index on government_id.

- **Instead of:** Upsert by customer_id; Upsert by government_id
- **Because:** KYC documents often include government-issued ID numbers as stable identifiers; using government_id makes sample idempotent and realistic for deduplication.
- **Reason came from:** `model_default`
- **Evidence:** assumptions_from_prompt_review: "Builder will at minimum create a unique index on the stable key (government_id or customer_id)."
- **When:** 2026-11-25T06:40:46+00:00

## D006 (build): I chose to use the existing DocumentDB cluster and not provision any new Azure resources.

- **Instead of:** Provision a new DocumentDB cluster; Use the existing cluster and do not provision new resources
- **Because:** Run policy forbids Azure resource changes and an existing cluster is available; provisioning is unnecessary for this sample.
- **Reason came from:** `readiness_report`
- **Evidence:** run environment: "A DocumentDB cluster is already provisioned and reachable... The connection string is in the environment variable DOCUMENTDB_URI."
- **When:** 2026-11-25T06:41:26+00:00

## D007 (build): I chose motor==3.5.3 to match available PyPI releases compatible with Beanie in this environment.

- **Instead of:** motor==4.1.0; motor==3.5.3
- **Because:** Use a Motor version available on PyPI that is compatible with Beanie; avoids installation failure.
- **Reason came from:** `tool_result`
- **Evidence:** pip error: "No matching distribution found for motor==4.1.0" and PyPI lists motor 3.5.3 as available.
- **When:** 2026-11-25T06:41:38+00:00

## D008 (build): I chose openai==1.0.0 to match an older stable client API surface compatible with synchronous ChatCompletion.create used in the sample's thread-executor call.

- **Instead of:** openai==0.29.0; openai==1.0.0
- **Because:** Selecting a widely-available OpenAI client version that supports ChatCompletion.create avoids install failures while keeping the sample simple; the code runs the sync call in a thread for async compatibility.
- **Reason came from:** `tool_result`
- **Evidence:** pip error: "No matching distribution found for openai==0.29.0" and PyPI lists 1.0.0 as available.
- **When:** 2026-11-25T06:41:51+00:00

## D009 (build): I chose to create and verify the unique index on government_id using the documentdb MCP server (create_index and list_indexes) for reliable programmatic verification.

- **Instead of:** Create collection/index via app code (Beanie); Create index via documentdb MCP server
- **Because:** MCP server provides programmatic access without requiring the app to run and matches the verification requirement in the prompt.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report: "The documentdb MCP server's connection profile `default` is connected to that same cluster. Use its tools to inspect collections, indexes and query plans and to verify what the app created."
- **When:** 2026-11-25T06:42:10+00:00
