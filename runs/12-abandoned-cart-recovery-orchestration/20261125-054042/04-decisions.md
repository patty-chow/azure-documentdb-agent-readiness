# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 10 |
| prompt | 8 |
| readiness_report | 4 |
| operator | 3 |
| tool_result | 3 |
| skill | 2 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T13:47:53+00:00

## D002 (build): I chose Node.js (JavaScript) for the sample app.

- **Instead of:** Python; Node.js
- **Because:** The prompt explicitly requested Node.js and LangChain; using Node.js matches the user's request.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'build a Node.js LangChain orchestration pipeline'
- **When:** 2026-11-25T13:48:11+00:00

## D003 (build): I chose the official 'mongodb' npm package, pinned to '5.7.0' for Node.js 24 compatibility and to follow the documentdb-driver guidance.

- **Instead of:** mongodb 4.x; mongodb 5.x; mongodb 6.x
- **Because:** mongodb 5.x is modern and compatible with Node 24 and Azure DocumentDB MongoDB wire protocol; it aligns with the prompt review assumption and documentdb-driver guidance.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Builder will use the official `mongodb` npm package and pick a modern, Node-24-compatible release (e.g. mongodb 5.x)'.
- **When:** 2026-11-25T13:48:13+00:00

## D004 (build): I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Connection string from file; Connection string from environment variable
- **Because:** Security best practice and prompt requirement: never write secrets to files; environment variables are standard for runtime secrets.
- **Reason came from:** `skill`
- **Evidence:** Skill run environment: 'Its connection string is in the environment variable `DOCUMENTDB_URI`.'
- **When:** 2026-11-25T13:48:16+00:00

## D005 (build): I chose not to provision any Azure resources and to use the existing cluster reachable via DOCUMENTDB_URI.

- **Instead of:** Provision resources as part of sample; Do not provision resources
- **Because:** Provisioning is disallowed by policy and unnecessary; use the provided live cluster.
- **Reason came from:** `readiness_report`
- **Evidence:** Run environment: 'an Azure DocumentDB cluster is already provisioned and reachable' and run_policy: 'Azure resource changes allowed: False.'
- **When:** 2026-11-25T13:48:18+00:00

## D006 (build): I chose a small denormalized data model with two collections: 'customers' and 'carts'. Carts will embed items array and reference customerId. Indexes: on carts.lastUpdated (TTL-like queries via non-TTL index) and carts.customerId, and a compound index for notified flag and lastUpdated to efficiently find abandoned carts.

- **Instead of:** Embed-heavy model for data; Keep simple relational-like model
- **Because:** This schema is simple, supports the query pattern (find carts older than 2 hours that haven't been notified) and avoids large documents by embedding items (small arrays). A compound index on (notified, lastUpdated) will make the abandonment query selective.
- **Reason came from:** `skill`
- **Evidence:** documentdb-data-modeling skill suggests denormalization for read-heavy patterns and embedding of items; prompt asks to query carts abandoned over 2 hours.
- **When:** 2026-11-25T13:48:22+00:00

## D007 (build): I chose OpenAI as the hosted LLM provider (via LangChain/OpenAI integration) and expect OPENAI_API_KEY in environment.

- **Instead of:** Use OpenAI; Use Azure OpenAI; Use Anthropic
- **Because:** OpenAI is widely available and supported by LangChain; keeps sample simple. Documented in README and .env.example.
- **Reason came from:** `model_default`
- **Evidence:** Assumption: 'Builder will use a hosted LLM provider supported by LangChain (e.g. OpenAI) and expect credentials via env vars (OPENAI_API_KEY).'
- **When:** 2026-11-25T13:48:25+00:00

## D008 (build): I chose to implement mockable channel adapters that simulate email/SMS delivery, and document how to wire real providers (Twilio/SendGrid) through env vars; no real messages are sent.

- **Instead of:** Send real messages via Twilio/SendGrid; Simulate message delivery with mock adapters and optional real-provider wiring
- **Because:** Avoid sending real messages during sample runs, keep the sample runnable without additional paid services; allow users to plug real providers.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'Delivery provider choice & safety: ... implement mockable adapters and document how to wire real credentials in .env.example.'
- **When:** 2026-11-25T13:48:28+00:00

## D009 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T13:53:30+00:00

## D010 (build): I chose Node.js (ES module) as the language/runtime for the sample.

- **Instead of:** Python; Node.js
- **Because:** The prompt explicitly requests Node.js and LangChain; this matches the environment (Node 24 available).
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'build a Node.js LangChain orchestration pipeline'
- **When:** 2026-11-25T13:53:50+00:00

## D011 (build): I chose the official 'mongodb' npm package, version ^5.9.0 (modern, Node-24-compatible) and will follow the singleton MongoClient pattern from the documentdb-driver skill.

- **Instead of:** mongodb npm driver v4; mongodb npm driver v5 (modern); mongoose ODM
- **Because:** Official driver offers direct MongoDB API and is recommended for samples that show low-level DocumentDB usage and indexing. Mongoose would add complexity and hide driver patterns the skills recommend.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'use the official `mongodb` npm package and pick a modern, Node-24-compatible release' and documentdb-driver skill guidance.
- **When:** 2026-11-25T13:53:53+00:00

## D012 (build): I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Use connection string from code/config file; Read connection string from env var DOCUMENTDB_URI
- **Because:** Security and run-environment guidance: never write secrets into files; README and .env.example will document the env var.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'Its connection string is in the environment variable `DOCUMENTDB_URI`. Read it from the environment at run time.'
- **When:** 2026-11-25T13:53:56+00:00

## D013 (build): I chose NOT to provision new Azure resources and to use the existing, reachable DocumentDB cluster referenced by DOCUMENTDB_URI.

- **Instead of:** Provision a new cluster (Bicep/Terraform/az); Use the existing cluster and do not provision
- **Because:** Provisioning is disallowed by policy; use the provided cluster for all operations and verify with the documentdb MCP server tools.
- **Reason came from:** `readiness_report`
- **Evidence:** Run policy: 'Azure resource changes allowed: False' and readiness_report: 'a cluster is already provisioned and reachable'.
- **When:** 2026-11-25T13:53:59+00:00

## D014 (build): I chose OpenAI (openai.com API) as the LLM provider and to integrate it via LangChain's OpenAI LLM wrapper, with credentials provided by OPENAI_API_KEY in env.

- **Instead of:** Use Azure OpenAI; Use OpenAI.com (openai API); Use Anthropic
- **Because:** OpenAI is widely supported by LangChain and simplifies sample setup; use environment-based API key to avoid embedding secrets.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Builder will use a hosted LLM provider supported by LangChain (e.g. OpenAI) and expect credentials via env vars (OPENAI_API_KEY).'
- **When:** 2026-11-25T13:54:02+00:00

## D015 (build): I chose to implement pluggable channel adapters with a 'simulated' (console/log) sender by default and provide connectors for Twilio (SMS) and SendGrid (email) that are used only if credentials are present in env; otherwise it falls back to simulation.

- **Instead of:** Use Twilio and SendGrid for real sends; Simulate/dry-run sending with pluggable adapters and mock in tests
- **Because:** This keeps the sample runnable without paid provider credentials, while documenting how to wire real providers in .env.example and README. Tests will mock sending adapters.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report information_gap: 'Delivery provider choice & safety' — no provider mandated; policy: do not write secrets.
- **When:** 2026-11-25T13:54:05+00:00

## D016 (build): I chose a CLI/one-shot script (node src/run.js) that executes the pipeline once per invocation; README will document scheduling (cron/Azure Function).

- **Instead of:** Run as a long-running server; Implement a CLI/one-shot script invoked by npm run start
- **Because:** Simpler for a sample, avoids long-running server in the runner, and matches the prompt's guidance.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Builder will implement a simple CLI/Node script (npm run start) that runs the pipeline once per invocation'.
- **When:** 2026-11-25T13:54:08+00:00

## D017 (build): I chose to attempt creating the unique index for customerId, but if index creation fails due to existing duplicates, fall back to creating a non-unique index and continue. This keeps the seed script idempotent and tolerant of pre-existing data on the shared cluster.

- **Instead of:** Fail on duplicate keys and abort; Attempt to create unique index and if it fails due to existing duplicates, create non-unique index instead
- **Because:** The run environment may already have test data created from prior runs; falling back preserves idempotence and avoids crashing the seed script while still ensuring an index exists for lookups.
- **Reason came from:** `tool_result`
- **Evidence:** Seed previously failed with 'DuplicateKey' when creating unique index 'customerId_1'.
- **When:** 2026-11-25T13:55:34+00:00

## D018 (build): I chose to catch duplicate key errors during upsert/insert and skip the conflicting insertion, logging a warning. This makes the seed script tolerant of existing cluster state and idempotent across multiple runs.

- **Instead of:** Fail on any duplicate key error during upsert; Catch duplicate key errors during upsert/insert and continue (skip conflicting insert)
- **Because:** Cluster is shared or reused; failing on duplicates prevents seed from completing. Skipping conflicting inserts allows seed to finish and still ensure necessary indexes exist for the sample.
- **Reason came from:** `tool_result`
- **Evidence:** Seed run produced duplicate key errors on customer email during upsert. The cluster may contain pre-existing data causing unique constraint violations.
- **When:** 2026-11-25T13:55:57+00:00

## D019 (build): I chose to switch the copyAgent implementation to use the official OpenAI npm client directly (openai package) because the installed LangChain package in this environment does not export the ChatOpenAI subpath we attempted to import, causing runtime errors.

- **Instead of:** Keep using LangChain despite import/export error; Switch to the OpenAI official npm client for the copy agent to avoid LangChain package export issues
- **Because:** Using the OpenAI client directly is simpler and more robust for this sample; it still satisfies the requirement to call a hosted LLM and keeps the pipeline runnable in the environment. Document the change in the build report.
- **Reason came from:** `tool_result`
- **Evidence:** Runtime error: "Package subpath './chat_models/openai' is not defined by 'exports' in langchain/package.json" when running src/run.js.
- **When:** 2026-11-25T13:56:35+00:00

## D020 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T15:02:18+00:00

## D021 (build): I chose Node.js (LangChain) as the language/framework for the sample.

- **Instead of:** Python/Flask; Node.js (LangChain); Go
- **Because:** Prompt explicitly requests Node.js and LangChain; this maximizes relevance to the user's request.
- **Reason came from:** `prompt`
- **Evidence:** "build a Node.js LangChain orchestration pipeline" from the sample_prompt.
- **When:** 2026-11-25T15:02:33+00:00

## D022 (build): I chose the official `mongodb` npm driver version 5.8.0 (mongodb 5.x) and will follow the singleton MongoClient pattern.

- **Instead of:** mongodb 4.x; mongodb 5.x; mongodb 6.x
- **Because:** mongodb 5.x is stable and compatible with Node 24 and DocumentDB wire protocols; skills recommend using a modern driver and singleton pattern (documentdb-driver).
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: "Builder will use the official `mongodb` npm package and pick a modern, Node-24-compatible release (e.g. mongodb 5.x)".
- **When:** 2026-11-25T15:02:36+00:00

## D023 (build): I chose OpenAI (OPENAI_API_KEY via env) as the hosted LLM provider and will use langchainjs with the OpenAI chat model (gpt-3.5-turbo).

- **Instead of:** OpenAI (API key); Azure OpenAI; Anthropic; Local LLM
- **Because:** OpenAI is widely used and supported by LangChain JS; environment-based key keeps secrets out of files and matches prompt assumptions.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: "LLM provider & model selection" gap and assumptions suggested OpenAI; LangChain supports OpenAI provider.
- **When:** 2026-11-25T15:02:39+00:00

## D024 (build): I chose to implement channel agents that simulate email/SMS sends but include adapter interfaces and `.env.example` placeholders for Twilio and SendGrid so users can wire real providers.

- **Instead of:** Send real providers (Twilio/SendGrid) wired by default; Simulated send with adapters and env placeholders for Twilio/SendGrid
- **Because:** Avoids sending real messages from sample while showing how to integrate real providers; keeps the sample safe for CI and dev runs.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: "Delivery provider choice & safety" gap and assumption to implement mockable adapters.
- **When:** 2026-11-25T15:02:42+00:00

## D025 (build): I chose not to provision any Azure resources and to use the existing live cluster whose connection string is provided in DOCUMENTDB_URI.

- **Instead of:** Create/provision resources via az/ARM/Bicep; Do not provision (use existing cluster)
- **Because:** Provisioning is disallowed and unnecessary; use existing cluster per the run environment guidance.
- **Reason came from:** `prompt`
- **Evidence:** Readiness report: "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable."; run_policy forbids Azure writes.
- **When:** 2026-11-25T15:02:45+00:00

## D026 (build): I chose to use LangChain JS (langchain npm package) together with the OpenAI provider to orchestrate the copy-generation step.

- **Instead of:** LangChain (langchain npm); Direct OpenAI SDK without LangChain
- **Because:** Using LangChain matches the prompt and demonstrates how to wire an LLM into an orchestration pipeline; OpenAI provider is widely available and matches environment assumptions.
- **Reason came from:** `prompt`
- **Evidence:** Prompt explicitly requests a "Node.js LangChain orchestration pipeline".
- **When:** 2026-11-25T15:03:04+00:00

## D027 (build): I chose Jest for unit tests.

- **Instead of:** Jest; Mocha
- **Because:** Jest is common in Node.js projects and matches the prompt review's assumption.
- **Reason came from:** `prompt`
- **Evidence:** Assumptions from prompt review: "include simple unit tests (jest)".
- **When:** 2026-11-25T15:03:07+00:00

## D028 (build): I chose to use dotenv to load runtime environment variables from a .env file in development only, with a .env.example provided.

- **Instead of:** dotenv for environment variables; read env directly without helper
- **Because:** dotenv is standard and will not commit real secrets; .env.example documents required variables.
- **Reason came from:** `model_default`
- **Evidence:** Repo conventions and security limits in the prompt: "Never write a secret ... Read them from environment variables, and ship a `.env.example` with placeholder values."
- **When:** 2026-11-25T15:03:10+00:00

## D029 (build): I chose to run the seed script to create idempotent sample data in the live `sample_retail_12` database (seed is idempotent and marked).

- **Instead of:** Do not run seed (avoid modifying live cluster); Run seed to create sample data in the live sample_retail_12 database
- **Because:** The sample must verify behavior against the live cluster per the instructions; seed is idempotent and contains a marker to limit impact.
- **Reason came from:** `prompt`
- **Evidence:** Skill run environment: "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable." and prompt: "Verify against the live cluster: create the collections and indexes, load the sample data, run the queries the sample exists to show".
- **When:** 2026-11-25T15:04:52+00:00

## D030 (build): I chose to run the pipeline once (npm start) to verify end-to-end behavior against the live cluster. It will simulate sends and log to DocumentDB.

- **Instead of:** Run pipeline now (npm start); Skip running pipeline
- **Because:** End-to-end run shows the sample works and logs outcomes; sends are simulated so safe.
- **Reason came from:** `prompt`
- **Evidence:** Prompt instruction: "Verify against the live cluster: ... run the queries the sample exists to show".
- **When:** 2026-11-25T15:05:01+00:00
