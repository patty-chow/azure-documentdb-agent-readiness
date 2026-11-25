# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 6 |
| prompt | 4 |
| readiness_report | 3 |
| operator | 2 |
| skill | 2 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T12:22:47+00:00

## D002 (build): I chose Node.js (v24) with LangChain JS for orchestration.

- **Instead of:** Python/Flask; Node.js (LangChain)
- **Because:** The prompt explicitly requires Node.js + LangChain.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'build a Node.js LangChain orchestration pipeline'
- **When:** 2026-11-25T12:23:07+00:00

## D003 (build): I chose the official mongodb npm driver (latest stable compatible with Node.js 24, e.g., mongodb 5.x/6.x) and will instantiate a singleton MongoClient.

- **Instead of:** mongodb driver 4.x; mongodb driver 5.x/6.x (latest compatible)
- **Because:** Official driver is recommended by DocumentDB skills and Node.js ecosystem for MongoDB-compatible clusters.
- **Reason came from:** `model_default`
- **Evidence:** Assumption in prompt review: 'Use the official MongoDB Node.js driver (mongodb npm package) latest stable compatible with Node.js 24'
- **When:** 2026-11-25T12:23:10+00:00

## D004 (build): I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Environment variable connection string (URI); Managed Identity / AAD OIDC flow
- **Because:** Simplest safe approach for a sample; avoids embedding secrets and keeps code environment-driven. AAD OIDC is more complex and needs tenant setup; sample will mention it in README.
- **Reason came from:** `prompt`
- **Evidence:** Skill run environment note: 'Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time.'
- **When:** 2026-11-25T12:23:14+00:00

## D005 (build): I chose to provide an idempotent Node.js seed script that uses the mongodb driver (reads DOCUMENTDB_URI) and also provide a script using documentdb MCP server as a backup for verification.

- **Instead of:** Seed using Node.js script with MongoDB driver; Seed using MCP server documentdb_insert_documents
- **Because:** Node.js seed script is part of the sample app and runnable by developers; MCP backup allows verification via the provided MCP server tools if the driver cannot connect from the runner.
- **Reason came from:** `model_default`
- **Evidence:** Assumption: 'Provide a small idempotent seed script' and readiness note recommending MCP server for inspection.
- **When:** 2026-11-25T12:23:22+00:00

## D006 (build): I chose no sharding for sample collections (single-shard) and simple indexes suitable for small sample data.

- **Instead of:** Shard collection; Single-shard (no sharding)
- **Because:** Sharding and resharding add complexity and require cluster-level changes; for a sample with tens of docs single-shard is simpler and aligns with learning goals.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'No sharding (single-shard) for the sample cluster'
- **When:** 2026-11-25T12:23:27+00:00

## D007 (build): I chose text-embedding-3-small with 1536 dimensions for embeddings in the sample and for configuring the vector index dimensions.

- **Instead of:** OpenAI text-embedding-3-small (1536 dims); Other embedding model
- **Because:** Need a concrete embedding dimension for the vector-index schema; text-embedding-3-small is commonly used and 1536 dims is a reasonable sample dimension. This is not DocumentDB-specific and is therefore a model_default choice.
- **Reason came from:** `model_default`
- **Evidence:** Assumption in prompt review: 'text-embedding-3-small with 1536 dims' and common OpenAI embedding dims.
- **When:** 2026-11-25T12:23:35+00:00

## D008 (build): I chose a mock 'send' agent by default that logs actions to outreach_logs and supports a configurable 'DISABLE_EXTERNAL_SENDS' env var to prevent real sends; real provider hooks are left as documented stubs.

- **Instead of:** Send real providers (SMTP/Twilio); Mock send provider (safe default)
- **Because:** Safety and compliance — sample should never send real messages by default.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'avoid sending real marketing messages in uncontrolled ways — use a mock or a clearly documented sandbox option for send agent by default.'
- **When:** 2026-11-25T12:23:38+00:00

## D009 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T12:25:38+00:00

## D010 (build): I chose Node.js (JavaScript) with CommonJS modules for the sample app.

- **Instead of:** Use Python; Use Node.js (JavaScript)
- **Because:** Prompt explicitly requested Node.js; CommonJS keeps examples simple and compatible with Node 24 runtime and many npm packages.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'build a Node.js LangChain orchestration pipeline'
- **When:** 2026-11-25T12:25:57+00:00

## D011 (build): I chose the official mongodb npm package (latest stable compatible with Node.js 24).

- **Instead of:** mongodb driver v5/6 (latest)
- **Because:** Official driver is recommended; will instantiate a singleton MongoClient.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review recommending the official MongoDB Node.js driver.
- **When:** 2026-11-25T12:26:07+00:00

## D012 (build): I chose to read the cluster connection string from the DOCUMENTDB_URI environment variable at runtime and use it for MongoClient connections.

- **Instead of:** Use AAD OIDC auth with MONGODB-OIDC; Use connection string from env (username/password or SRV)
- **Because:** This avoids embedding secrets in repo and matches the provided environment expectations.
- **Reason came from:** `skill`
- **Evidence:** Skill run environment: 'Its connection string is in the environment variable DOCUMENTDB_URI.'
- **When:** 2026-11-25T12:26:12+00:00

## D013 (build): I chose to create a singleton MongoClient with moderate pool settings suitable for a long-running Node.js service: maxPoolSize=20, minPoolSize=5, retryWrites=true.

- **Instead of:** Default MongoClient options; Configure pool for long-running server (maxPoolSize=20, minPoolSize=5)
- **Because:** Sample app is a long-running orchestration process; moderate pool sizing avoids connection thrashing while remaining safe for a dev cluster.
- **Reason came from:** `skill`
- **Evidence:** documentdb-connection skill guidance: use singleton client and tune pool sizes for long-running servers.
- **When:** 2026-11-25T12:26:18+00:00

## D014 (build): I chose a denormalized document model with three collections: customers, events, and outreach_logs.

- **Instead of:** Normalized relational-style collections; Denormalized document model with customers, events, outreach_logs
- **Because:** Denormalization is appropriate for read-heavy orchestration flows; keeps sample simple to query and seed.
- **Reason came from:** `model_default`
- **Evidence:** Assumptions from prompt review recommended these collections: 'customers', 'events', and 'outreach_logs'.
- **When:** 2026-11-25T12:26:24+00:00

## D015 (build): I chose OpenAI (public OpenAI API) for the LLM provider and text-embedding-3-small (1536 dims) for embeddings; model name is configurable via MODEL_NAME and EMBEDDING_MODEL env vars.

- **Instead of:** OpenAI (openai.com); Azure OpenAI; Anthropic
- **Because:** OpenAI is widely accessible and supported by LangChain examples; picking text-embedding-3-small (1536 dims) provides a concrete embedding dimensionality for the sample.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'LLM provider and embedding model selection missing; choose a provider and model so vector index dims match'
- **When:** 2026-11-25T12:26:34+00:00

## D016 (build): I chose a mock/sandbox send agent that does not send real messages: it logs to console and writes the outreach_logs document marked 'mocked' or 'sent' depending on SANDBOX_SEND env var.

- **Instead of:** Attempt real integration (SMTP/Twilio); Use mock/sandbox send agent that logs and records in DB
- **Because:** Avoid sending real messages in a sample; provides a clear path to replace with real provider via env vars and documented instructions.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'safe defaults - sample should avoid sending real marketing messages'
- **When:** 2026-11-25T12:26:37+00:00

## D017 (build): I chose to implement a CLI listener (long-running) and a minimal Express REST API exposing GET /logs for recent outreach logs.

- **Instead of:** Only CLI long-running listener; CLI listener + minimal REST API for logs
- **Because:** Provides both a way to run the orchestrator and to inspect results programmatically.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review recommended a CLI listener and a small REST API.
- **When:** 2026-11-25T12:26:43+00:00
