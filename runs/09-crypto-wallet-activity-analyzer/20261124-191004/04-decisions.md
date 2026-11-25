# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 3 |
| readiness_report | 3 |
| model_default | 2 |
| operator | 1 |
| tool_unavailable | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T06:52:07+00:00

## D002 (build): I chose Python 3.x (use python from PATH) as the language/runtime for the sample.

- **Instead of:** Node.js (JavaScript); Python 3.13
- **Because:** The run environment already provides Python on PATH and the sample is requested as a Python LangChain agent.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Builder will target a modern Python 3.x' and run environment: 'python resolves to a virtual environment created for this run'.
- **When:** 2026-11-25T06:52:27+00:00

## D003 (build): I chose the official PyMongo driver (pymongo) pinned to a recent 4.x release.

- **Instead of:** Use PyMongo >=4.3,<5.0; Use motor (async) or older driver
- **Because:** PyMongo is the standard synchronous driver and aligns with the documentdb-driver skill guidance about a singleton MongoClient pattern and simplicity for a sample app.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Use the official PyMongo driver (pymongo) compatible with MongoDB 7.0, e.g. pymongo >=4.3,<5.0'.
- **When:** 2026-11-25T06:52:31+00:00

## D004 (build): I chose to support OpenAI (via OPENAI_API_KEY) for LangChain summarization if available, and fall back to a local rule-based summarizer when no API key is present.

- **Instead of:** Use Azure OpenAI (if available); Use OpenAI via OPENAI_API_KEY; Don't require LLM / use rule-based summarizer
- **Because:** This allows the sample to demonstrate LangChain integration when credentials are present while remaining runnable offline without leaking secrets or requiring cloud LLM access.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'LLM choice and credentials are undefined' and 'no LLM provider credentials were visible'.
- **When:** 2026-11-25T06:52:35+00:00

## D005 (build): I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Read connection string from a config file; Read connection string from environment variable DOCUMENTDB_URI
- **Because:** The prompt explicitly requires using DOCUMENTDB_URI and forbids writing secrets to files.
- **Reason came from:** `prompt`
- **Evidence:** Prompt run environment: 'Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time.'
- **When:** 2026-11-25T06:52:37+00:00

## D006 (build): I chose not to provision any Azure resources in the sample; the app will use the existing live cluster pointed to by DOCUMENTDB_URI.

- **Instead of:** Provision resources in sample; Do not provision resources; use existing cluster
- **Because:** Provisioning is disallowed and unnecessary for the sample; using the existing cluster keeps the sample safe and compliant with policy.
- **Reason came from:** `prompt`
- **Evidence:** Run policy: 'Azure resource changes allowed: False' and prompt: 'a cluster is already provisioned and reachable'.
- **When:** 2026-11-25T06:52:41+00:00

## D007 (build): I chose a single-shard collection (no explicit shard key) and a simple transactions schema with fields {wallet_address, timestamp, amount, currency, tx_id}.

- **Instead of:** Shard collection and pick shard key; Don't shard (single-shard)
- **Because:** The sample is small, for demos, and the readiness report suggests single-shard is acceptable. It simplifies the seed and aggregation pipeline.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'No shard key by default (single-shard), and daily grouping uses the timestamp field.'
- **When:** 2026-11-25T06:52:46+00:00

## D008 (build): I chose to create a small runner script (scripts/run_seed.py) that adds 'src' to sys.path and invokes the package module, because the command-runner refused env-prefix commands.

- **Instead of:** Prefix command with PYTHONPATH=src (refused by run_command); Create a small runner script that sets sys.path before importing the package
- **Because:** The execution environment refuses setting environment variable prefixes in the command; adding a wrapper script is a portable workaround that keeps commands allowed and reproducible.
- **Reason came from:** `tool_unavailable`
- **Evidence:** Error from run_command: "REFUSED: 'pythonpath=src' is not on the allowed command list"
- **When:** 2026-11-25T06:54:01+00:00

## D009 (build): I chose to call the documentdb MCP server's documentdb_explain_operation to verify the aggregation pipeline and index usage after seeding, per readiness guidance.

- **Instead of:** Rely only on client-side pymongo aggregation behavior; Also call the documentdb MCP server's documentdb_explain_operation to verify index usage
- **Because:** Using the MCP explain tool gives authoritative executionStats for index usage and avoids manual inspection.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report guidance: 'Create a compound index on { wallet: 1, timestamp: 1 } before running the aggregation, and verify the pipeline with documentdb_explain_operation to ensure the index is used.'
- **When:** 2026-11-25T06:54:19+00:00

## D010 (build): I chose to call documentdb_list_indexes to verify the compound index exists on the collection.

- **Instead of:** Trust the client-side create_index call; Use MCP documentdb_list_indexes to verify index creation
- **Because:** Programmatic verification using MCP is authoritative and reproducible for the build report.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report recommendation: 'Create a compound index on { wallet: 1, timestamp: 1 } before running the aggregation, and verify the pipeline with documentdb_explain_operation to ensure the index is used.'
- **When:** 2026-11-25T06:54:50+00:00
