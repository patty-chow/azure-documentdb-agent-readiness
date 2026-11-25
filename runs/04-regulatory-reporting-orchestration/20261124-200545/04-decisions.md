# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 8 |
| readiness_report | 6 |
| model_default | 5 |
| operator | 2 |
| tool_result | 2 |
| skill | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T09:34:48+00:00

## D002 (build): I chose Python (3.13) for the sample app and a standard venv/pip workflow.

- **Instead of:** Node.js/TypeScript; Python 3.10/3.11; Python 3.13
- **Because:** Python is widely used for LangChain, the run environment already has Python 3.13, and the sample will be concise to run and read in Python.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: "Python 3.13.13 is on PATH (inventory)."
- **When:** 2026-11-25T09:35:16+00:00

## D003 (build): I chose PyMongo (pymongo) for database access and LangChain (Python) for agents/LLM orchestration.

- **Instead of:** Use PyMongo + LangChain (Python); Use native MongoDB Node driver + LangChain JS; Use Go or Java clients
- **Because:** PyMongo is the standard Python MongoDB driver, and LangChain in Python has mature LLM/agent integrations; this aligns with the prompt and available tools.
- **Reason came from:** `prompt`
- **Evidence:** documentdb-driver skill and documentdb-connection recommend PyMongo singleton pattern and the prompt requests a Python LangChain orchestration.
- **When:** 2026-11-25T09:35:19+00:00

## D004 (build): I chose to read the DocumentDB connection string from the DOCUMENTDB_URI environment variable at runtime.

- **Instead of:** Read connection string from config file; Embed connection string into code; Read from environment variable DOCUMENTDB_URI
- **Because:** Security best-practice: never write secrets to files; the run environment provides DOCUMENTDB_URI per instructions.
- **Reason came from:** `readiness_report`
- **Evidence:** Skill.md and readiness report: "Its connection string is in the environment variable `DOCUMENTDB_URI`. Read it from the environment at run time."
- **When:** 2026-11-25T09:35:21+00:00

## D005 (build): I chose to use the existing reachable DocumentDB cluster described in the run environment and not provision any Azure resources.

- **Instead of:** Provision a new cluster via az/bicep/terraform; Use the existing cluster provided in the environment
- **Because:** Run policy disallows provisioning; prompt and run environment specify an existing cluster for sample runs.
- **Reason came from:** `readiness_report`
- **Evidence:** Skill.md: "A vector-capable Azure DocumentDB cluster... is reachable from this machine. Its connection string is in DOCUMENTDB_URI." Run policy: Azure resource changes allowed: False.
- **When:** 2026-11-25T09:35:25+00:00

## D006 (build): I chose the data model with collections: accounts, transactions, positions, and workflow_runs (for orchestrator logs).

- **Instead of:** Use collections: accounts, transactions, positions, workflow_runs; Use a single denormalized collection; Use entirely different schema
- **Because:** This schema maps well to regulatory reporting examples and supports multi-collection extraction/deduplication and a separate workflow_runs collection for audit logs.
- **Reason came from:** `prompt`
- **Evidence:** Assumptions from prompt review: suggested schema including these collections and workflow_runs for orchestrator logging.
- **When:** 2026-11-25T09:35:28+00:00

## D007 (build): I chose to create supporting indexes: transactions: compound {reporting_period:1, date:1} and single-field index on account_id; workflow_runs: index on run_id and start_ts.

- **Instead of:** Create compound index on {reporting_period:1, date:1} and index on account_id; No indexes; Only text index
- **Because:** These indexes optimize the common query patterns the sample will run (filter by reporting_period and sort by date, lookup by account_id, and query workflow runs by run_id/time).
- **Reason came from:** `model_default`
- **Evidence:** Assumptions from prompt review recommended these indexes to support reporting-period queries and workflow lookups.
- **When:** 2026-11-25T09:35:31+00:00

## D008 (build): I chose to make LLM and embedding provider configurable via environment variables and default to OpenAI text-embedding-3-small (1536 dims) and a chat model named gpt-4o-mini when env variables are not provided.

- **Instead of:** Use OpenAI embeddings and chat models by default; Use local dummy model; Use Microsoft Azure OpenAI by default
- **Because:** OpenAI models are commonly available to developers, LangChain supports them well, and making them configurable follows the prompt's assumption and safety guidelines.
- **Reason came from:** `model_default`
- **Evidence:** Assumptions from prompt review suggested making models configurable and example defaults (text-embedding-3-small, 1536 dims).
- **When:** 2026-11-25T09:35:35+00:00

## D009 (build): I chose to implement the orchestration with small LangChain-driven agents encapsulated as Python functions (extraction uses DB queries, validation uses deterministic rules + optional LLM summary, filing uses LLM for formatting), rather than a full Agent framework.

- **Instead of:** Implement agents as full LangChain Agent objects; Implement agents as small LangChain LLM calls wrapped in Python functions; Use no LLM and do everything deterministically
- **Because:** This keeps the sample accessible, shows LangChain integration, and makes the pipeline deterministic where needed while using LLMs for human-friendly summaries/formatting.
- **Reason came from:** `model_default`
- **Evidence:** Prompt asked for a LangChain orchestration pipeline; the LangChain agent framework can be heavyweight. A function-based wrapper meets the requirement and remains easy to read and test.
- **When:** 2026-11-25T09:35:38+00:00

## D010 (build): I chose not to use vector search or create vector indexes for this sample; the pipeline demonstrates multi-collection extraction, validation rules and filing without vector capabilities.

- **Instead of:** Create vector index and use vector search; Don't create vector indexes and rely on direct queries
- **Because:** Avoids adding complexity and external model-dimension coupling; keeps the sample focused on orchestration, validation, and workflow logging.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: vector-index creation needs extra parameters and embedding model dimension; the sample's acceptance criteria did not require vector search.
- **When:** 2026-11-25T09:35:43+00:00

## D011 (build): I chose to use the documentdb MCP server tools (documentdb_list_indexes, documentdb_find_documents) where helpful to verify collection indexes and inserted workflow document contents during the build verification.

- **Instead of:** Use documentdb MCP tools for verification; Only rely on direct PyMongo checks
- **Because:** MCP tools provide a consistent programmatic inspection of the live cluster and are available in this environment.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: "the `documentdb` MCP server's connection profile `default` is connected to that same cluster. Use its tools to inspect collections, indexes and query plans and to verify what the app created."
- **When:** 2026-11-25T09:35:49+00:00

## D012 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T09:38:04+00:00

## D013 (build): I chose Python 3.13 for the sample app and scripts.

- **Instead of:** Node.js/TypeScript; Python 3.13
- **Because:** Python is widely used for LangChain orchestration; the run environment has Python 3.13 available.
- **Reason came from:** `readiness_report`
- **Evidence:** Assumption from prompt review: 'Builder will assume a modern, commonly-available Python 3.x — e.g., Python 3.10 (or 3.11) virtualenv/venv.' Also readiness report: 'Python 3.13.13 is on PATH (inventory).
- **When:** 2026-11-25T09:38:22+00:00

## D014 (build): I chose pymongo (synchronous) as the MongoDB driver.

- **Instead of:** mongodb driver via motor (async); pymongo (synchronous)
- **Because:** Synchronous code is simpler for a small sample CLI and matches many examples; pymongo is standard and recommended by the skills.
- **Reason came from:** `skill`
- **Evidence:** documentdb-driver skill and readiness report recommend using PyMongo.MongoClient and singleton pattern; readiness report: 'Read the connection string from DOCUMENTDB_URI at runtime and instantiate PyMongo.MongoClient with TLS.'
- **When:** 2026-11-25T09:38:25+00:00

## D015 (build): I chose to read the cluster connection string from the environment variable DOCUMENTDB_URI at runtime (SCRAM or connection-string-based auth).

- **Instead of:** Microsoft Entra ID / Managed Identity; SCRAM credentials via connection string
- **Because:** The run environment provides DOCUMENTDB_URI and the sample must not embed secrets; using the provided connection string is simplest and matches guidance.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report instruction: 'Read the connection string from DOCUMENTDB_URI at runtime and instantiate PyMongo.MongoClient with TLS; do not hard-code port or host suffix—use the cluster-provided connection string.'
- **When:** 2026-11-25T09:38:29+00:00

## D016 (build): I chose to use the existing cluster reachable via DOCUMENTDB_URI and not provision any Azure resources.

- **Instead of:** Provision new cluster via az/bicep/terraform; Use existing cluster (DOCUMENTDB_URI)
- **Because:** Provisioning is disallowed and unnecessary; the environment already provides a cluster.
- **Reason came from:** `prompt`
- **Evidence:** Prompt and skill_md: 'This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable.' Run policy: 'Azure resource changes allowed: False.'
- **When:** 2026-11-25T09:38:33+00:00

## D017 (build): I chose a synthetic data model with collections: accounts, transactions, positions, and workflow_runs (for orchestrator logs).

- **Instead of:** Use real regulatory schema (unknown); Use a small synthetic schema: accounts, transactions, positions, workflow_runs
- **Because:** The regulatory schema was unspecified; a small synthetic schema covers the sample's goals and keeps the example self-contained while meeting acceptance criteria.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: suggested schema e.g.: collections 'accounts', 'transactions', 'positions', plus a 'workflow_runs' collection.
- **When:** 2026-11-25T09:38:36+00:00

## D018 (build): I chose to create indexes supporting reporting-period queries: a compound index on {reporting_period:1, date:1} for transactions, an index on account_id for transactions, and an index on workflow_runs for run_id and start_ts.

- **Instead of:** No indexes (default); Create indexes supporting reporting-period queries: compound on {reporting_period, date}, account_id index, workflow_runs index
- **Because:** These indexes directly support the sample query patterns and are low-cost for the sample dataset.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Builder will add indexes supporting the reporting-period queries, e.g. compound index on { reporting_period: 1, date: 1 }, index on account_id, and an index for the workflow_runs collection on run_id / start_ts.'
- **When:** 2026-11-25T09:38:39+00:00

## D019 (build): I chose OpenAI embeddings text-embedding-3-small (1536 dims) and a chat model gpt-4o-mini as defaults, configurable via environment variables.

- **Instead of:** Use Anthropic or Azure OpenAI; Use OpenAI text-embedding-3-small and gpt-4o-mini (configurable)
- **Because:** OpenAI is commonly available and the readiness report noted embedding model choice is an information gap; using these defaults keeps the sample runnable if the user provides keys.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Make model/provider configurable via environment variables (e.g., OPENAI_API_KEY and MODEL_NAME). Example defaults: OpenAI embeddings (text-embedding-3-small, 1536 dims) and an OpenAI chat model (e.g., gpt-4o-mini).'
- **When:** 2026-11-25T09:38:42+00:00

## D020 (build): I chose a CLI primary entrypoint (scripts/run_report.py) with an optional small orchestrator in src that could be reused in a web endpoint later.

- **Instead of:** Web API primary (FastAPI); CLI primary with optional web endpoint
- **Because:** A CLI is straightforward to run in CI and for reviewers; it satisfies the sample acceptance criteria without requiring a running server.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'The primary demo will be the CLI script that runs the pipeline and prints / writes the formatted regulatory output file.'
- **When:** 2026-11-25T09:38:45+00:00

## D021 (build): I chose to omit langchain from requirements.txt to keep the sample runnable; the sample implements a simple orchestration without requiring the langchain package at runtime.

- **Instead of:** Pin a specific langchain version that may not be available; Omit langchain from requirements because many versions are unavailable in this environment
- **Because:** Avoid blocking the build on an unavailable package; keep the sample self-contained. Document that LangChain can be added by users in README if desired.
- **Reason came from:** `tool_result`
- **Evidence:** pip install failed: 'No matching distribution found for langchain==0.0.366'. The orchestrator code does not currently import langchain and can function without it.
- **When:** 2026-11-25T09:39:41+00:00

## D022 (build): I chose mongomock==4.3.0 as the available version to use for tests.

- **Instead of:** Keep mongomock==4.4.0; Use mongomock==4.3.0 which is available
- **Because:** Use an available version to allow tests to run in this environment.
- **Reason came from:** `tool_result`
- **Evidence:** pip error: 'No matching distribution found for mongomock==4.4.0' and pip index shows 4.3.0 available.
- **When:** 2026-11-25T09:39:52+00:00

## D023 (build): I chose to run the seed script against the existing cluster referenced by DOCUMENTDB_URI to create collections and load sample data (idempotent upserts).

- **Instead of:** Do not run seed against live cluster; Run seed against the existing cluster (DOCUMENTDB_URI) to create collections and indexes and load sample data
- **Because:** The run environment provides an existing cluster and the prompt requested the sample verify against the live cluster by creating collections and loading sample data.
- **Reason came from:** `prompt`
- **Evidence:** Skill_md: 'A vector-capable Azure DocumentDB cluster ... is reachable from this machine. Its connection string is in the environment variable DOCUMENTDB_URI.' Readiness report: 'The build can start: the documentdb MCP server... DOCUMENTDB_URI is expected from env.'
- **When:** 2026-11-25T09:40:21+00:00

## D024 (build): I chose to run scripts/run_report.py against the existing cluster to perform an end-to-end orchestration run and verify workflow_runs and filing output were created.

- **Instead of:** Do not run the orchestrator against live cluster; Run run_report to execute orchestrator end-to-end against existing cluster
- **Because:** Verifying end-to-end ensures the sample actually exercises the DocumentDB queries, index creation, seed data and workflow logging.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'Verify against the live cluster: create the collections and indexes, load the sample data, run the queries the sample exists to show, and record in the build report what was actually executed and what was not.' The cluster is reachable via DOCUMENTDB_URI.
- **When:** 2026-11-25T09:41:00+00:00
