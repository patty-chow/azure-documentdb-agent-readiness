# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 9 |
| prompt | 6 |
| readiness_report | 6 |
| operator | 4 |
| skill | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T11:35:40+00:00

## D002 (build): I chose Node.js (v24) for the sample app and LangChain agent implementation.

- **Instead of:** Python; Node.js; Go
- **Because:** The user explicitly asked for a Node.js LangChain agent and Node.js 24 is available in the environment.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'build a Node.js LangChain agent' and readiness_report: 'Node.js, npx available (v24.21.0)'
- **When:** 2026-11-25T11:36:01+00:00

## D003 (build): I chose the official mongodb npm driver mongodb@6.x.

- **Instead of:** mongodb@4.x; mongodb@5.x; mongodb@6.x
- **Because:** Modern stable release compatible with Node.js 24 and aligns with assumptions and skills guidance to use the mongodb driver and MongoClient singleton.
- **Reason came from:** `model_default`
- **Evidence:** assumptions_from_prompt_review: 'assume mongodb@6.x' and readiness_report suggesting mongodb npm driver latest (compatible with Node 24).
- **When:** 2026-11-25T11:36:04+00:00

## D004 (build): I chose to use SCRAM/native credentials provided indirectly via DOCUMENTDB_URI environment variable at runtime.

- **Instead of:** Use Microsoft Entra ID (OIDC) auth; Use SCRAM/native credentials from the URI
- **Because:** Entra-ID requires cluster configuration and extra setup; sample should run against existing cluster using DOCUMENTDB_URI and not store secrets in repo.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report: 'If you want to support Microsoft Entra ID authentication, enable it on the cluster... otherwise use native SCRAM credentials from the connection string.'
- **When:** 2026-11-25T11:36:08+00:00

## D005 (build): I chose OpenAI text-embedding-3-small (1536 dimensions) for embeddings and to document OPENAI_API_KEY as the env var.

- **Instead of:** OpenAI text-embedding-3-small (1536 dims); OpenAI ada-002 (unrecommended); Azure OpenAI with unknown model
- **Because:** Common, well-supported embedding model with 1536 dims that matches LangChain/OpenAI support; easy for users to supply OPENAI_API_KEY.
- **Reason came from:** `model_default`
- **Evidence:** assumptions_from_prompt_review: 'plausible default: OpenAI embeddings (text-embedding-3-small, 1536 dims)'; readiness_report noted embedding model choice missing.
- **When:** 2026-11-25T11:36:11+00:00

## D006 (build): I chose a default of using OpenAI chat model gpt-4o-mini (or falling back to a deterministic local heuristic when OPENAI_API_KEY is not set).

- **Instead of:** gpt-4; gpt-4o-mini; gpt-4o-mini or gpt-4 depending on availability
- **Because:** gpt-4o-mini is a capable, lower-cost chat model for reasoning; sample must run in environments without API keys so fallback deterministic scoring is provided for verification.
- **Reason came from:** `model_default`
- **Evidence:** assumptions_from_prompt_review suggested 'gpt-4o-mini or gpt-4' and readiness_report said LLM choice missing.
- **When:** 2026-11-25T11:36:16+00:00

## D007 (build): I chose to create only standard (non-vector) indexes in the seed script for robust verification here, and include commented/example code and README notes for creating a vector index (cosmosSearch) matching 1536 dims for users with vector-capable clusters.

- **Instead of:** Create vector indexes now (complex); Create only standard indexes and leave vector index as optional example
- **Because:** Vector index creation can fail or require cluster-specific permissions/commands; to ensure the seed runs against the existing cluster reliably, create conventional indexes and document vector-index steps for users to run manually if desired.
- **Reason came from:** `model_default`
- **Evidence:** readiness_report: 'Vector indexes use special createIndexes + cosmosSearchOptions' and 'vector index creation may be more complex and cluster-dependent.'
- **When:** 2026-11-25T11:36:20+00:00

## D008 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T11:39:29+00:00

## D009 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T11:43:02+00:00

## D010 (build): I chose Node.js with Express for the sample app and CLI entrypoints.

- **Instead of:** Python/Flask; Node.js/Express (JavaScript); Go net/http
- **Because:** The prompt explicitly asks for a Node.js LangChain agent; Express is a minimal familiar HTTP framework for the sample.
- **Reason came from:** `prompt`
- **Evidence:** The sample prompt requested 'build a Node.js LangChain agent' and the run environment lists Node.js 24 and npm available.
- **When:** 2026-11-25T11:43:23+00:00

## D011 (build): I chose the official mongodb npm driver, version ^6.10.0 (mongodb@6.x as declared in package.json).

- **Instead of:** mongodb@5.x; mongodb@6.x; mongoose ODM
- **Because:** Official driver is recommended in DocumentDB driver skill and is compatible with Node 24; sample already lists mongodb@6.10.0.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'use official mongodb npm driver... mongodb@6.x'. package.json already contains "mongodb": "^6.10.0".
- **When:** 2026-11-25T11:43:26+00:00

## D012 (build): I chose to use SCRAM via the provided DOCUMENTDB_URI environment variable and not enable Entra-ID flows in the sample.

- **Instead of:** SCRAM (connection string); Microsoft Entra ID (OIDC)
- **Because:** Simpler for a sample and matches the run environment note that DOCUMENTDB_URI is provided; avoids additional setup for Entra ID.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report guidance: 'read DOCUMENTDB_URI from the environment' and 'use native SCRAM credentials from the connection string' when not enabling Entra-ID.
- **When:** 2026-11-25T11:43:29+00:00

## D013 (build): I chose to use the already-provisioned live Azure DocumentDB cluster reachable via DOCUMENTDB_URI and not provision new resources.

- **Instead of:** Provision new cluster with Bicep/az; Use existing live cluster (DOCUMENTDB_URI)
- **Because:** Run policy forbids provisioning and the environment already provides a cluster; use that for verification and seeding.
- **Reason came from:** `prompt`
- **Evidence:** Run environment states: 'A vector-capable Azure DocumentDB cluster is reachable and its connection string is in DOCUMENTDB_URI.' Run policy forbids Azure resource changes.
- **When:** 2026-11-25T11:43:32+00:00

## D014 (build): I chose the data model: database 'sample_customer_360_09' with collections 'leads', 'activities', 'companies', 'engagement_signals'.

- **Instead of:** Multiple collection names; leads/activities/companies/engagement_signals
- **Because:** These collections map to the prompt's requirements (lead document, activity history, firmographics, engagement signals) and are simple for a demo.
- **Reason came from:** `model_default`
- **Evidence:** Assumptions from prompt review recommended these collections and the readme/samples in folder reflect this.
- **When:** 2026-11-25T11:43:35+00:00

## D015 (build): I chose OpenAI text-embedding-3-small with 1536 dimensions for embeddings and to store embeddings in engagement_signals when used.

- **Instead of:** OpenAI text-embedding-3-small (1536 dim); OpenAI ada-002 (1536?); Azure embedding model
- **Because:** Common, modern embedding model with 1536 dims; consistent with earlier assumption and small sample size.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report lists text-embedding-3-small (1536 dims) as a plausible default and the sample will use OpenAI for embeddings.
- **When:** 2026-11-25T11:43:37+00:00

## D016 (build): I chose to use OpenAI chat model gpt-4o-mini (configurable via OPENAI_MODEL env var) for scoring reasoning calls.

- **Instead of:** OpenAI gpt-4; gpt-4o-mini; local LLM
- **Because:** Balances capability and cost for a sample; make model configurable through env var so users can swap to gpt-4 if desired.
- **Reason came from:** `model_default`
- **Evidence:** The prompt requested an LLM to reason; readiness report left model unspecified. gpt-4o-mini is cost-effective and suited for reasoning tasks.
- **When:** 2026-11-25T11:43:40+00:00

## D017 (build): I chose to create standard scalar indexes (activities: {leadId:1, timestamp:-1}, engagement_signals: {leadId:1}) and include a skeleton vector index spec in seed that uses 'cosmosSearch' with kind 'vector-hnsw' and dimensions 1536 (for embeddings).

- **Instead of:** No vector/index creation; Create scalar indexes only; Create vector index with 1536 dims HNSW/DiskANN
- **Because:** Matches embedding dims and provides example createIndexes command for users; HNSW is appropriate for small sample dataset.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report and documentdb-vector-search skill instruct to create vector indexes with createIndexes and cosmosSearchOptions; sample should show index creation but not heavy tuning.
- **When:** 2026-11-25T11:43:43+00:00

## D018 (build): I chose to provide an Express HTTP API with POST /score-lead and a CLI script entrypoint (npm run score) that calls the same scoring logic.

- **Instead of:** No HTTP API; Express POST /score-lead and CLI script
- **Because:** Provides both programmatic and CLI access for demos and CI/testing.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review suggested Express API and CLI; package.json already includes scripts 'start' and 'score'.
- **When:** 2026-11-25T11:43:46+00:00

## D019 (build): I chose singleton MongoClient pattern (single shared client) for the sample database connections.

- **Instead of:** Instantiate MongoClient per request; Singleton MongoClient reused across app lifecycle
- **Because:** Avoid connection-pool exhaustion and follow best practices for Node.js and DocumentDB drivers.
- **Reason came from:** `readiness_report`
- **Evidence:** documentdb-driver skill guidance: 'singleton MongoClient' and readiness_report instruction to use it.
- **When:** 2026-11-25T11:43:51+00:00

## D020 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T13:19:22+00:00

## D021 (build): I chose Node.js 24 with Express and LangChain for the agent implementation.

- **Instead of:** Python/Flask; Node.js/Express (LangChain); Go with Gin
- **Because:** The prompt explicitly requests a Node.js LangChain agent; Node.js 24 is available in the run environment per the readiness report.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'build a Node.js LangChain agent'
- **When:** 2026-11-25T13:19:56+00:00

## D022 (build): I chose the official mongodb npm driver mongodb@6.x (declared ^6.0.0 in package.json).

- **Instead of:** mongodb@5.x; mongodb@6.x; mongodb@4.x
- **Because:** mongodb@6.x is the modern stable driver compatible with Node.js 24 and aligns with the documentdb-driver and documentdb-connection skills.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use the official mongodb npm driver and pick a modern stable release compatible with Node.js 24 (assume mongodb@6.x).'
- **When:** 2026-11-25T13:19:58+00:00

## D023 (build): I chose to read the connection string from environment variable DOCUMENTDB_URI and use the native SCRAM credentials provided there.

- **Instead of:** Use connection string from env (SCRAM); Use Microsoft Entra ID (OIDC) role-based auth
- **Because:** The run environment already contains DOCUMENTDB_URI and enabling Entra ID requires cluster changes; using the connection string is simplest and safe for the sample.
- **Reason came from:** `skill`
- **Evidence:** Skill guidance: 'Use mongodb npm driver (MongoClient) reading DOCUMENTDB_URI from environment; set tls=true and retryWrites=false'
- **When:** 2026-11-25T13:20:02+00:00

## D024 (build): I chose not to provision any Azure resources and use the existing cluster referenced by DOCUMENTDB_URI.

- **Instead of:** Provision a cluster in this run; Do not provision cluster; use existing cluster
- **Because:** Provisioning is disallowed by policy and not needed; the sample should use the existing live cluster.
- **Reason came from:** `readiness_report`
- **Evidence:** Run policy: 'Azure resource changes allowed: False' and readiness report stating a cluster is already reachable.
- **When:** 2026-11-25T13:20:05+00:00

## D025 (build): I chose to avoid vector embeddings and vector indexes in this sample and instead reason directly over retrieved signals with an LLM.

- **Instead of:** Use vector search + embeddings; Avoid vector indexes and use LLM reasoning only
- **Because:** Simpler, avoids needing an embedding provider and creating vector indexes; keeps sample focused on agent tooling and DocumentDB data access.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'Embedding model & dimensions' missing and creates complexity; prompt didn't mandate vector search.
- **When:** 2026-11-25T13:20:09+00:00

## D026 (build): I chose to provide both a small Express HTTP API (POST /score-lead) and a CLI script (npm run score) for convenience.

- **Instead of:** HTTP API only; HTTP API + CLI
- **Because:** Provides both programmatic access and a way to run the agent locally in CI or ad-hoc without running the server.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Builder will provide a small HTTP API (Express) with POST /score-lead and CLI script'
- **When:** 2026-11-25T13:20:12+00:00
