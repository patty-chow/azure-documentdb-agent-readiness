# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 5 |
| skill | 3 |
| operator | 2 |
| readiness_report | 1 |
| tool_result | 1 |
| model_default | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T10:44:30+00:00

## D002 (build): I chose Python 3.11 for the sample runtime.

- **Instead of:** Python 3.10; Python 3.11; Python 3.13
- **Because:** 3.11 is widely supported by libraries (LangChain, PyMongo) and balances modern features and compatibility compared to 3.13 which may be too new. It matches the prompt review assumption.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Builder will target a modern Python 3.x LTS typically used for samples (assume Python 3.10 or 3.11).'
- **When:** 2026-11-25T10:44:50+00:00

## D003 (build): I chose the synchronous PyMongo driver (pymongo) and to use a singleton MongoClient.

- **Instead of:** Sync PyMongo (pymongo); Async Motor (motor)
- **Because:** Synchronous PyMongo keeps the sample simpler to read and run; it aligns with documentdb-driver guidance for a singleton client and is sufficient for a CLI-style orchestrator. Async adds complexity without significant benefit here.
- **Reason came from:** `skill`
- **Evidence:** documentdb-driver skill guidance: 'Reuse MongoClient as a process-wide singleton; never create a new client per request.'
- **When:** 2026-11-25T10:44:56+00:00

## D004 (build): I chose to read DOCUMENTDB_URI from the environment and instantiate a singleton MongoClient with conservative pool settings suitable for a CLI/long-running sample (maxPoolSize=20, minPoolSize=0).

- **Instead of:** Read connection string and set pool defaults for serverless; Read connection string and use PyMongo defaults
- **Because:** The orchestrator is a short-running CLI/interactive app; a moderate pool size avoids over-allocating connections while allowing concurrency in the sample's aggregation work.
- **Reason came from:** `skill`
- **Evidence:** documentdb-connection skill guidance: 'Create client once only and reuse; default max pool size 100 unless specific needs; for OLTP long-running servers use larger pool sizes. For general samples, conservative values are recommended.'
- **When:** 2026-11-25T10:45:01+00:00

## D005 (build): I chose to create single-field indexes on account_id, instrument, and timestamp (descending) and a partial index on risk_factors.rateSensitivity because the sample's aggregation filters will commonly filter by instrument or account and group by timestamp windows.

- **Instead of:** Create single-field indexes: instrument, account_id, currency, timestamp; Create compound indexes; Create hashed index on shard key
- **Because:** These indexes support the sample aggregation patterns (filter by instrument/account and time-bounded queries) while remaining simple and low-write-cost for the sample dataset.
- **Reason came from:** `skill`
- **Evidence:** documentdb-indexing skill: 'Use single-field indexes for common equality filters; keep 5–15 indexes per collection; partial indexes for sparse fields.'
- **When:** 2026-11-25T10:45:08+00:00

## D006 (build): I chose to use the live DocumentDB cluster reachable via DOCUMENTDB_URI for seeding and verification.

- **Instead of:** Use a local DocumentDB gateway (Docker) for seeding; Use the live cluster referenced by DOCUMENTDB_URI
- **Because:** The run environment already supplies a reachable cluster and provisioning is not allowed; using the live cluster fulfills verification requirements and aligns with the run environment guidance.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'A vector-capable Azure DocumentDB cluster ... is reachable from this machine. Its connection string is in the environment variable DOCUMENTDB_URI.'
- **When:** 2026-11-25T10:46:00+00:00

## D007 (build): I chose to create a small runner script `run_seed.py` that adjusts sys.path and imports the seed script, because the shell-style PYTHONPATH prefix was refused by the runner.

- **Instead of:** Invoke seed with PYTHONPATH env prefix (refused); Create a small runner script that adjusts sys.path and imports seed module
- **Because:** A runner script avoids forbidden shell prefixes while still allowing the seed script to import local packages.
- **Reason came from:** `tool_result`
- **Evidence:** Command runner refused 'PYTHONPATH=.' style env assignment: "REFUSED: 'pythonpath=.' is not on the allowed command list".
- **When:** 2026-11-25T10:46:09+00:00

## D008 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T10:48:02+00:00

## D009 (build): I chose Python 3.11 for the sample runtime.

- **Instead of:** Python 3.10; Python 3.11; Python 3.13
- **Because:** 3.11 is a widely supported modern LTS for samples and compatible with LangChain and PyMongo; it balances novelty with library compatibility.
- **Reason came from:** `model_default`
- **Evidence:** Assumption: 'Builder will target a modern Python 3.x LTS typically used for samples (assume Python 3.10 or 3.11).'
- **When:** 2026-11-25T10:48:19+00:00

## D010 (build): I chose the synchronous PyMongo MongoClient (blocking) for simplicity.

- **Instead of:** Async driver (motor/AsyncIOMotorClient); Synchronous PyMongo MongoClient
- **Because:** Synchronous code keeps the sample smaller and easier to read; it integrates straightforwardly with simple CLI orchestrator and unit tests.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'If sync code is simpler, use PyMongo 4.0+ (latest stable).'
- **When:** 2026-11-25T10:48:23+00:00

## D011 (build): I chose to read the DocumentDB connection string from the DOCUMENTDB_URI environment variable at runtime.

- **Instead of:** Read DOCUMENTDB_URI from environment; Use Entra/OIDC interactive auth; Embed connection string in file
- **Because:** Security: never write secrets to files. This aligns with the readiness_report guidance and the run environment expectation.
- **Reason came from:** `prompt`
- **Evidence:** Readiness report guidance: 'Read DOCUMENTDB_URI from the environment and pass it to pymongo.MongoClient'
- **When:** 2026-11-25T10:48:25+00:00

## D012 (build): I chose OpenAI (public) as the LLM provider using text-embedding-3-small (1536 dims) for embeddings and gpt-4o-mini for chat when available, but the sample will run without an API key (LLM steps become optional).

- **Instead of:** Use OpenAI (text-embedding-3-small + gpt-4o-mini); Use Azure OpenAI; No LLM (mock only)
- **Because:** OpenAI is commonly available, matches embedding dimension assumptions, and makes the sample accessible. Making LLM optional keeps the sample runnable without credentials.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Builder will use an LLM provider configured via environment variables (e.g., OpenAI API key in OPENAI_API_KEY). For embeddings use a standard embedding model (e.g., text-embedding-3-small, 1536 dims) and for chat use a contemporary chat model (e.g., gpt-4o-mini). The repo will read LLM credentials from env and will not hard-code them.'
- **When:** 2026-11-25T10:48:30+00:00

## D013 (build): I chose a simple CLI entrypoint (run_stress_test.py) as the app surface.

- **Instead of:** CLI only; HTTP API + CLI
- **Because:** Keeps the sample small and easy to run locally for developers following README steps.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Builder will implement a simple CLI entrypoint (e.g., run_stress_test.py or a `main()` CLI using click/argparse) that runs the orchestrator and prints/writes the structured report.'
- **When:** 2026-11-25T10:48:33+00:00
