# Decision log

| Reason came from | Decisions |
|---|---|
| readiness_report | 3 |
| prompt | 3 |
| operator | 1 |
| skill | 1 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T09:19:19+00:00

## D002 (build): I chose Python 3.13 (the system Python available) for the sample runtime.

- **Instead of:** Python 3.10; Python 3.13
- **Because:** Use the actual available Python to avoid compatibility issues and because it is supported.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: "Python 3.13.13" available on the run environment.
- **When:** 2026-11-25T09:19:38+00:00

## D003 (build): I chose PyMongo (pymongo) v4.x as the MongoDB driver.

- **Instead of:** pymongo 3.x; pymongo 4.x
- **Because:** PyMongo 4.x is current major version with modern features and matches driver guidance for Azure DocumentDB.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Use PyMongo (mongodb-driver for Python) v4.x" and general driver best practices in documentdb-driver skill.
- **When:** 2026-11-25T09:19:46+00:00

## D004 (build): I chose the SRV connection string from DOCUMENTDB_URI env var.

- **Instead of:** Microsoft Entra ID; SRV env var
- **Because:** Env var provided; avoids storing secrets.
- **Reason came from:** `skill`
- **Evidence:** Run environment note: connection string is in DOCUMENTDB_URI.
- **When:** 2026-11-25T09:19:59+00:00

## D005 (build): I chose separate `accounts` and `transactions` collections in database `sample_banking_01` with transactions containing fields `_id`, `from_account`, `to_account`, `amount`, `timestamp`, and optional `linked_tx_ids`.

- **Instead of:** Single collection for both accounts and transactions; Separate `accounts` and `transactions` collections
- **Because:** Separating accounts and transactions follows common modeling for transaction systems and simplifies graph queries and indexing.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt review: "Builder will create a database `sample_banking_01` with collections such as `transactions` and `accounts`..."
- **When:** 2026-11-25T09:20:03+00:00

## D006 (build): I chose OpenAI text-embedding-3-small (1536 dimensions) as the embedding model, but make LLM/embedding calls optional (fallback stub) if API key is not provided.

- **Instead of:** Use OpenAI text-embedding-3-small (1536 dims); Use local embedding model or none
- **Because:** Choosing a common hosted embedding reduces friction; making it optional keeps tests runnable without keys.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report notes embedding-model gap and suggests choosing a model and aligning index dims.
- **When:** 2026-11-25T09:20:06+00:00

## D007 (build): I chose to implement both a CLI entrypoint (`python -m aml_agent analyze`) and a small FastAPI HTTP endpoint `/analyze`.

- **Instead of:** CLI only; CLI + FastAPI HTTP endpoint
- **Because:** Provides both programmatic and interactive ways to run the analysis for reviewers.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Builder will provide a simple CLI entrypoint ... and a small Flask/FastAPI HTTP endpoint `/analyze`".
- **When:** 2026-11-25T09:20:08+00:00

## D008 (build): I chose to create the initial single-field and compound indexes using the documentdb MCP server `documentdb_create_index` tool for verification and to follow guidance from documentdb-indexing skill.

- **Instead of:** Create only PyMongo indexes in seed.py; Use MCP server documentdb_create_index tool to create recommended indexes
- **Because:** Using MCP server tools allows programmatic verification of index creation and matches the instruction to use installed skills for verification.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report and skills recommend using documentdb createIndexes and verifying with MCP tools.
- **When:** 2026-11-25T09:20:11+00:00

## D009 (build): I attempted to use the documentdb MCP server but it failed, so I used PyMongo create_index in seed.py as a fallback.

- **Instead of:** Use documentdb MCP server to create indexes; Use PyMongo create_index in seed.py
- **Because:** MCP tool failed in this environment; PyMongo can create the indexes directly when seeding data and is idempotent.
- **Reason came from:** `tool_result`
- **Evidence:** Attempt to call documentdb_create_index returned: 'Error: Function failed.'
- **When:** 2026-11-25T09:21:32+00:00
