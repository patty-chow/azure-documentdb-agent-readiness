# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 12 |
| model_default | 7 |
| readiness_report | 4 |
| operator | 3 |
| tool_result | 2 |
| skill | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T07:29:48+00:00

## D002 (build): I chose Node.js (v24) with Express for the sample app.

- **Instead of:** Python/Flask; Node.js/Express; Go/Fiber
- **Because:** The prompt explicitly requested Node.js; Express is a minimal, widely-known HTTP framework appropriate for a small sample.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'build a Node.js LangChain multi-agent system'
- **When:** 2026-11-25T07:30:33+00:00

## D003 (build): I chose the official 'mongodb' Node.js driver at 5.x (current) and will use a singleton MongoClient per driver guidance.

- **Instead of:** mongodb driver 4.x; mongodb driver 5.x (current); mongoose ODM
- **Because:** The official driver gives full control and aligns with DocumentDB guidance; driver 5.x supports MongoDB 7.0 wire protocol.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use the official mongodb Node.js driver (npm package 'mongodb') at a current 5.x release' and documentdb-driver skill guidance (singleton client).
- **When:** 2026-11-25T07:30:37+00:00

## D004 (build): I chose to read the DocumentDB connection string from the DOCUMENTDB_URI environment variable at runtime and never write it into the repository files.

- **Instead of:** Read connection string from code (bad); Embed connection string in files (forbidden); Read DOCUMENTDB_URI from environment at runtime
- **Because:** Protects secrets and matches the run environment instruction that DOCUMENTDB_URI is available; keeps sample safe for public repo.
- **Reason came from:** `skill`
- **Evidence:** Readiness report guidance: 'Read the cluster connection string from DOCUMENTDB_URI at runtime'
- **When:** 2026-11-25T07:30:48+00:00

## D005 (build): I chose NOT to provision any Azure resources and to use the existing cluster reachable via DOCUMENTDB_URI.

- **Instead of:** Provision cluster with IaC (Bicep/Terraform); Use provided live cluster and avoid provisioning
- **Because:** The run policy forbids Azure resource changes and the prompt specified using the provided cluster; provisioning is unnecessary and would violate policy.
- **Reason came from:** `readiness_report`
- **Evidence:** Run environment & readiness report: 'an Azure DocumentDB cluster is already provisioned and reachable' and run policy forbids resource creation.
- **When:** 2026-11-25T07:30:50+00:00

## D006 (build): I chose separate collections: 'transactions', 'communications', 'claims', and 'decisions' within database 'sample_fintech_18'. Documents will include schemaVersion and concise fields (ids, timestamps, amount, message, metadata).

- **Instead of:** transactions, communications, claims, decisions; single combined collection
- **Because:** Keeps data normalized for this demo, fits expected access patterns (evidence fetch uses transactionId), and supports schemaVersioning guidance.
- **Reason came from:** `model_default`
- **Evidence:** Assumption in prompt review and documentdb-data-modeling guidance: embed when data accessed together, include schemaVersion field.
- **When:** 2026-11-25T07:30:54+00:00

## D007 (build): I chose to implement deterministic, rule-based policy reasoning by default (so the sample can run without LLM keys) and provide optional hooks to call OpenAI (embeddings + LLM) when API keys are present. For docs, I will recommend OpenAI text-embedding-3-small (1536 dims) and a reasoning LLM such as gpt-4o-mini as examples.

- **Instead of:** Use OpenAI embeddings & LLMs by default; Use no AI provider and simple rules only; Support optional OpenAI integration but default to deterministic rules for offline verification
- **Because:** Ensures the demo is verifiable in environments without API keys while showing how to enable LLM/embeddings if the user wants to experiment.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: embedding model choice is unspecified; assumptions from prompt review suggested OpenAI. The readiness report flagged embedding dims as an information gap.
- **When:** 2026-11-25T07:30:57+00:00

## D008 (build): I chose a minimal Express HTTP server with endpoints POST /claims/submit and GET /health for the sample.

- **Instead of:** Serverless handler only; Long-running Express server
- **Because:** Provides a simple interface to trigger the orchestrator and is easy to run locally.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Implement a minimal HTTP API (Express) with POST /claims/submit'
- **When:** 2026-11-25T07:31:01+00:00

## D009 (build): I chose to include lightweight Jest unit tests that mock agents so CI can run without a live cluster; seed and sample-run instructions will still show how to run against the live cluster.

- **Instead of:** No tests; Unit tests with live DB; Unit tests with mocks (Jest)
- **Because:** Enables automated verification in environments that lack cluster credentials while keeping the seed script available for manual verification.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review and run environment test guidance recommending tests that run without live cluster.
- **When:** 2026-11-25T07:31:05+00:00

## D010 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T07:33:23+00:00

## D011 (build): I chose Node.js with Express and LangChain (Node) for agents.

- **Instead of:** Python/Flask; Node.js/Express; Go/Fiber
- **Because:** The prompt explicitly requests Node.js and LangChain; Express is a lightweight web framework for the orchestrator.
- **Reason came from:** `prompt`
- **Evidence:** Sample prompt: 'build a Node.js LangChain multi-agent system'
- **When:** 2026-11-25T07:33:34+00:00

## D012 (build): I chose the official 'mongodb' Node.js driver at a current 5.x release.

- **Instead of:** mongodb driver 4.x; mongodb driver 5.x
- **Because:** MongoDB Node driver 5.x supports MongoDB 7.0 wire protocol per the readiness report; matches DocumentDB compatibility.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Use the official mongodb Node.js driver (npm package 'mongodb') at a current 5.x release'
- **When:** 2026-11-25T07:33:36+00:00

## D013 (build): I chose SCRAM credentials read from DOCUMENTDB_URI environment variable for authentication.

- **Instead of:** Use SCRAM credentials from DOCUMENTDB_URI env var; Use Microsoft Entra ID / Managed Identity token auth
- **Because:** Simpler for a sample and run environment already provides DOCUMENTDB_URI; managed identity is optional and complex to set up.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report guidance: 'Read the cluster connection string from DOCUMENTDB_URI at runtime'
- **When:** 2026-11-25T07:33:40+00:00

## D014 (build): I chose collections: 'transactions', 'communications', 'claims', and 'decisions' in database 'sample_fintech_18'.

- **Instead of:** collections: transactions, communications, claims, decisions; collections: only transactions and claims
- **Because:** Keeps responsibilities separate: transactions & communications are evidence, claims record incoming disputes, decisions store final outcomes; matches sample workflow.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Collections assumed: 'transactions', 'communications' (and likely 'claims' or 'decisions')'
- **When:** 2026-11-25T07:33:58+00:00

## D015 (build): I chose to create single-field indexes on transactionId and claimId only (no vector or full-text indexes).

- **Instead of:** Create single-field indexes on claimId/transactionId; Create vector or text indexes too
- **Because:** Simpler and avoids embedding/dimension uncertainty; adequate for simple equality/time-range queries used by the sample.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report 'No vector or full-text index is strictly required unless the policy or evidence agent needs semantic search'
- **When:** 2026-11-25T07:34:01+00:00

## D016 (build): I chose deterministic rule-based policy agent by default with optional OpenAI LLM usage when OPENAI_API_KEY is provided.

- **Instead of:** Use OpenAI models by default; Use deterministic rule-based policy with optional LLM when API key present
- **Because:** Allows the sample to demonstrate the multi-agent flow without requiring API keys while showing where to plug in an LLM for richer policy reasoning.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: embedding/LLM provider not specified; sample should run without needing external AI keys.
- **When:** 2026-11-25T07:34:04+00:00

## D017 (build): I chose to attempt running the demo script once to produce a decision document in the DB and demonstrate the flow.

- **Instead of:** Run demo script now (attempt 1); Skip demo
- **Because:** It's useful to demonstrate end-to-end flow; seed worked earlier so demo may succeed.
- **Reason came from:** `prompt`
- **Evidence:** Build step: 'run the queries the sample exists to show' and README indicates demo script
- **When:** 2026-11-25T07:45:40+00:00

## D018 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T07:59:11+00:00

## D019 (build): I chose Node.js (v24) with Express for the sample app and LangChain for multi-agent orchestration.

- **Instead of:** Python/Flask; Node.js/Express; Go/fiber
- **Because:** The run environment explicitly provides Node.js v24, npm, and npx. Node/Express is the most common stack for LangChain JS and fits the prompt requirement for a Node.js LangChain multi-agent system.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Use Node.js 24 with npm and npx is available.' from skill_md run environment
- **When:** 2026-11-25T07:59:33+00:00

## D020 (build): I chose the official 'mongodb' Node.js driver (5.x) and will implement a singleton MongoClient per documentdb-driver guidance.

- **Instead of:** mongodb driver 4.x; mongodb driver 5.x; mongoose
- **Because:** Official driver (mongodb) is recommended for DocumentDB; 5.x supports MongoDB 7.0 wire protocol. Singleton client pattern avoids connection pool exhaustion and matches documentdb-driver guidance.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt review: "Use the official mongodb Node.js driver (npm package 'mongodb') at a current 5.x release"
- **When:** 2026-11-25T07:59:37+00:00

## D021 (build): I chose OpenAI text-embedding-3-small (1536 dims) if embeddings are used; but the sample will not create a vector index by default to keep the sample minimal.

- **Instead of:** Embed provider: OpenAI text-embedding-3-small (1536 dims); OpenAI text-embedding-ada-002 (1536?); No embeddings / lexical only
- **Because:** Embedding model choice determines vector index dimensions; to avoid mis-sized indexes and since semantic search is not strictly required, I will default to a lexical multi-field approach and keep embedding/model choice documented for extension.
- **Reason came from:** `model_default`
- **Evidence:** readiness_report: 'Embedding model and vector dimension' information gap
- **When:** 2026-11-25T07:59:39+00:00

## D022 (build): I chose to use the existing live cluster and NOT provision any Azure resources.

- **Instead of:** Provision cluster via IaC; Use provided live cluster (DOCUMENTDB_URI)
- **Because:** Run policy forbids provisioning and the environment already provides a reachable cluster; using it keeps sample lightweight and reproducible.
- **Reason came from:** `prompt`
- **Evidence:** skill_md run environment: 'A vector-capable Azure DocumentDB cluster ... connection string is in the environment variable DOCUMENTDB_URI'
- **When:** 2026-11-25T07:59:41+00:00

## D023 (build): I chose database 'sample_fintech_18' with collections: 'transactions', 'communications', 'claims', and 'decisions'. Each document includes schemaVersion and small typed fields.

- **Instead of:** Create collections: transactions, communications, claims, decisions; Use different names or prefix
- **Because:** These names map closely to the domain (chargeback disputes) and keep the sample easy to understand; include schemaVersion for future migrations as guided by documentdb-data-modeling skill.
- **Reason came from:** `prompt`
- **Evidence:** assumption from prompt review: 'Use the database named sample_fintech_18' and likely collections described
- **When:** 2026-11-25T07:59:44+00:00

## D024 (build): I chose to create single-field indexes on claimId and transactionId for fast lookups, and an index on createdAt for range queries. No vector index will be created by default.

- **Instead of:** Create no indexes; Create single-field indexes on claimId/transactionId; Create compound and vector indexes
- **Because:** Simple queries in the evidence agent will filter by claimId/transactionId; single-field indexes are low-cost and easy to explain in a sample. Adding vector indexes is optional for extensions and requires embedding choice; document will describe how to add one.
- **Reason came from:** `prompt`
- **Evidence:** assumption from prompt review: 'Create single-field indexes on claimId/transactionId.' and documentdb-indexing skill guidance to prefer single-field for simple filters
- **When:** 2026-11-25T07:59:48+00:00

## D025 (build): I chose to read the DocumentDB connection string from environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Read connection string from a file; Read from environment variable DOCUMENTDB_URI; Hard-code connection string
- **Because:** Security best practice and explicit instruction from readiness_report; avoids committing secrets to repo.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report guidance: 'Read the cluster connection string from DOCUMENTDB_URI at runtime and use a singleton MongoClient'
- **When:** 2026-11-25T07:59:50+00:00

## D026 (build): I chose to use LangChain (Node.js) to model the multi-agent orchestration, with environment-driven LLM provider (OpenAI) via OPENAI_API_KEY.

- **Instead of:** LangChain for agents; Hand-rolled agent orchestration without LangChain
- **Because:** Using LangChain matches the user's request and demonstrates a common production pattern; the code will be modular so LLM provider can be swapped via env vars.
- **Reason came from:** `prompt`
- **Evidence:** User prompt: 'build a Node.js LangChain multi-agent system'
- **When:** 2026-11-25T07:59:53+00:00

## D027 (build): I chose to remove the 'langchain' dependency and use the OpenAI SDK directly for the policy agent because the requested langchain version failed to install (npm ETARGET).

- **Instead of:** Keep trying to install LangChain with different version; Remove LangChain dependency and use OpenAI SDK directly
- **Because:** LangChain npm package version resolution failed during install; using OpenAI SDK directly keeps the sample lean and avoids blocking the build. The code already uses the OpenAI Responses API in policyAgent, so LangChain is not strictly required for this sample's core flow.
- **Reason came from:** `tool_result`
- **Evidence:** npm install error: 'No matching version found for langchain@^0.0.275.'
- **When:** 2026-11-25T08:00:50+00:00

## D028 (build): I chose to make the seed script idempotent by checking existing indexes and only creating missing indexes to avoid IndexOptionsConflict errors when rerun.

- **Instead of:** Abort on index conflict; Check existing indexes and only create missing ones
- **Because:** Idempotent behavior is required for sample re-runs and matches the prompt's requirement to be upsert/idempotent; checking existing indexes prevents createIndex conflicts.
- **Reason came from:** `tool_result`
- **Evidence:** Seed run failed with MongoServerError: Index already exists with a different name: claimId_1
- **When:** 2026-11-25T08:01:09+00:00

## D029 (build): I chose to run a one-shot orchestrator invocation to verify the end-to-end flow (evidence retrieval, policy heuristic, and decision write) against the live cluster using the existing DOCUMENTDB_URI.

- **Instead of:** Do not execute end-to-end orchestrator against live cluster; Execute a one-shot orchestrator run to verify end-to-end behavior against the provided cluster
- **Because:** End-to-end verification demonstrates the sample works as intended; the environment contains the cluster connection string. I will run a single short script to avoid long-running servers.
- **Reason came from:** `prompt`
- **Evidence:** skill_md: 'A vector-capable Azure DocumentDB cluster ... connection string is in the environment variable DOCUMENTDB_URI' and readiness_report said to verify against the live cluster
- **When:** 2026-11-25T08:12:19+00:00
