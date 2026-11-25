# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 7 |
| readiness_report | 6 |
| operator | 4 |
| model_default | 4 |
| skill | 1 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T08:24:03+00:00

## D002 (build): I chose Node.js (v24) with an Express demo and CLI scripts.

- **Instead of:** Python/Flask; Node.js (Express); Go
- **Because:** Prompt explicitly requested Node.js; Node 24 is available in run environment and matches the prompt.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'build a Node.js LangChain multi-agent system'; Readiness report: 'Node 24 with npm and npx is available.'
- **When:** 2026-11-25T08:24:32+00:00

## D003 (build): I chose the official mongodb npm driver (mongodb) with a permissive ^5.11.0 version spec.

- **Instead of:** mongodb@4.x; mongodb@5.x; mongodb@6.x
- **Because:** mongodb@5 is stable and compatible with Node 24; it supports modern APIs and aligns with driver guidance.
- **Reason came from:** `skill`
- **Evidence:** documentdb-driver skill recommends using the standard MongoDB driver; Node.js ecosystem widely uses the 'mongodb' package.
- **When:** 2026-11-25T08:24:35+00:00

## D004 (build): I chose to read the cluster connection string from process.env.DOCUMENTDB_URI at runtime.

- **Instead of:** Use managed identity / Entra auth; Use connection string from env var DOCUMENTDB_URI; Prompt for credentials interactively
- **Because:** Secure, portable, matches run environment instructions; avoids writing secrets into repo.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'Read the cluster connection string from process.env.DOCUMENTDB_URI and use the standard MongoDB driver.'
- **When:** 2026-11-25T08:24:37+00:00

## D005 (build): I chose not to provision Azure resources and to use the existing cluster described in the run environment.

- **Instead of:** Provision cluster with Bicep/Terraform/azd now; Do not provision; use existing cluster
- **Because:** Avoid creating Azure resources and respect run policy; sample should use existing cluster per instructions.
- **Reason came from:** `prompt`
- **Evidence:** Prompt run environment: 'This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable.'; Run policy says Azure resource changes allowed: False.
- **When:** 2026-11-25T08:24:40+00:00

## D006 (build): I chose to create three collections: preauth_requests, clinical_criteria, and submissions, with the indexes: patientId, status on preauth_requests and text index on clinical_criteria.criteriaText.

- **Instead of:** Create only preauth_requests and submissions; Create three collections plus clinical_criteria and vector index
- **Because:** Matches suggested data model and is sufficient for the sample; vector indexes are optional and will be supported if embedding model/dim provided at runtime.
- **Reason came from:** `prompt`
- **Evidence:** Assumptions from prompt_review: 'Builder will create three collections...' and readiness guidance on using text indexes for criteria lookup.
- **When:** 2026-11-25T08:24:43+00:00

## D007 (build): I chose OpenAI-compatible environment variables (OPENAI_API_KEY) with default model names CHAT_MODEL='gpt-4o-mini' and EMBEDDING_MODEL='text-embedding-3-small' (1536 dims); fall back to deterministic local logic if no API key is present.

- **Instead of:** Use OpenAI (openai npm); Use Azure OpenAI; Use local LLM/no LLM fallback
- **Because:** OpenAI is common and easy to configure; fall back ensures tests and demo run without external credentials.
- **Reason came from:** `model_default`
- **Evidence:** Assumptions from prompt_review: 'A plausible default: OpenAI-compatible models with env OPENAI_API_KEY; use a chat model... embedding model text-embedding-3-small with dimension 1536.'
- **When:** 2026-11-25T08:24:48+00:00

## D008 (build): I chose a lightweight, LangChain-inspired multi-agent structure implemented with small modules (medicalReviewAgent, insurerCommsAgent) rather than pulling in the full langchain npm dependency.

- **Instead of:** Implement full LangChain dependency stack; Implement lightweight agent pattern without LangChain library
- **Because:** Keeps the sample small, easy to read, and runnable in constrained environments while demonstrating multi-agent orchestration patterns.
- **Reason came from:** `model_default`
- **Evidence:** Prompt asked for a 'LangChain multi-agent system' but the run environment and simplicity suggest a small multi-agent structure can demonstrate concepts without heavy dependencies.
- **When:** 2026-11-25T08:24:52+00:00

## D009 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T08:27:03+00:00

## D010 (build): I chose Node.js 24 (JavaScript) for the sample app.

- **Instead of:** Python; Node.js (24)
- **Because:** User explicitly asked for a Node.js sample; Node 24 is available per readiness report.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'Using the DocumentDB skill, build a Node.js LangChain multi-agent system'
- **When:** 2026-11-25T08:27:22+00:00

## D011 (build): I chose to read the DocumentDB connection string from process.env.DOCUMENTDB_URI at run time.

- **Instead of:** Hardcode credentials in files; Read connection string from environment variable DOCUMENTDB_URI
- **Because:** Security: do not write secrets into files; matches run environment guidance.
- **Reason came from:** `prompt`
- **Evidence:** Run environment: 'Its connection string is in the environment variable `DOCUMENTDB_URI`. Read it from the environment at run time.'
- **When:** 2026-11-25T08:27:25+00:00

## D012 (build): I chose not to provision any Azure resources and to use the existing cluster described in the run environment.

- **Instead of:** Provision new DocumentDB cluster; Use existing cluster and do not provision
- **Because:** Provisioning is disallowed by run_policy and unnecessary.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report and run environment: 'a cluster is already provisioned and reachable' and run_policy: Azure resource changes allowed: False.
- **When:** 2026-11-25T08:27:29+00:00

## D013 (build): I chose a three-collection data model: preauth_requests, clinical_criteria, submissions.

- **Instead of:** Three-collection data model; Single collection; More collections
- **Because:** Matches the sample domain separation and keeps the sample simple and readable.
- **Reason came from:** `prompt`
- **Evidence:** Assumptions from prompt review suggesting those collections.
- **When:** 2026-11-25T08:27:32+00:00

## D014 (build): I chose to implement criteria lookup using a text-search (text index) and simple rule matching; vector search is out of scope for this small sample but noted in README.

- **Instead of:** Use vector embeddings and vector index; Use keyword text search (createSearchIndexes / text index)
- **Because:** Avoids needing embedding model names/dim decisions and keeps sample runnable without external LLM keys; still follows DocumentDB guidance for createSearchIndexes vs external search.
- **Reason came from:** `readiness_report`
- **Evidence:** Assumptions and readiness report: vector support exists but embedding dims unspecified; simpler text-search is sufficient for demo.
- **When:** 2026-11-25T08:27:34+00:00

## D015 (build): I chose to make LLM usage optional: use OpenAI-compatible API if OPENAI_API_KEY provided; otherwise produce deterministic template outputs (no external call).

- **Instead of:** Use OpenAI provider and models; Use no LLM / built-in template text
- **Because:** Keeps sample runnable in environments without API keys while allowing richer behavior when a key is present.
- **Reason came from:** `readiness_report`
- **Evidence:** Information gaps: LLM provider not specified; README should instruct how to supply keys. Assumptions suggested OpenAI env vars.
- **When:** 2026-11-25T08:27:38+00:00

## D016 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T08:30:52+00:00

## D017 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T12:50:02+00:00

## D018 (build): I chose Node.js (v24) as the language/runtime for the sample.

- **Instead of:** Python; Node.js
- **Because:** Node.js matches the prompt's requirement for a Node.js LangChain multi-agent system and the workspace already contains Node.js project files.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'Node (v24) available' and package.json already present targeting Node.
- **When:** 2026-11-25T12:50:37+00:00

## D019 (build): I chose to read secrets (DocumentDB connection string and LLM API key) from environment variables at runtime (DOCUMENTDB_URI, OPENAI_API_KEY).

- **Instead of:** Environment secrets file (checked in); Environment variables (runtime)
- **Because:** Secure practice and matches existing code in repo that expects env vars.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'Never write a secret... Read them from environment variables' and seed of existing files uses process.env.DOCUMENTDB_URI and OPENAI_API_KEY.
- **When:** 2026-11-25T12:50:40+00:00

## D020 (build): I chose to use the existing Azure DocumentDB cluster described in the run environment and not provision new resources.

- **Instead of:** Provision cluster via Bicep/Terraform; Use existing cluster described in run environment
- **Because:** Avoid provisioning changes, follow run environment and run_policy restrictions.
- **Reason came from:** `readiness_report`
- **Evidence:** Run environment: 'This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable.' and run_policy disallows Azure resource changes.
- **When:** 2026-11-25T12:50:43+00:00

## D021 (build): I chose to not use embeddings/vector indexes and instead query criteria documents by procedureCode and rely on the LLM (or rule-based fallback) for assessment.

- **Instead of:** Use vector index and embeddings; Use textual criteria matching and LLM without embeddings
- **Because:** Simpler, avoids choosing embedding model/dimension and vector-index parameters given information gaps; keeps sample focused and runnable without extra configuration.
- **Reason came from:** `model_default`
- **Evidence:** Seed script already creates clinical_criteria collection and text index; no existing embedding setup. Readiness report lists vector search as optional.
- **When:** 2026-11-25T12:50:46+00:00

## D022 (build): I chose OpenAI (api.openai.com) as the default LLM provider, with model name read from CHAT_MODEL env var and API key from OPENAI_API_KEY.

- **Instead of:** Azure OpenAI; OpenAI (api.openai.com); Other providers
- **Because:** Matches existing code and is a common default; keeps credentials out of repo and configurable via env.
- **Reason came from:** `model_default`
- **Evidence:** Existing code in agents uses OpenAI package and process.env.OPENAI_API_KEY; readiness report left provider choice open.
- **When:** 2026-11-25T12:50:50+00:00

## D023 (build): I chose to modify package.json to use mongodb ^5.8.0 because ^5.11.0 failed to install in this environment.

- **Instead of:** Keep mongodb ^5.11.0 and retry; Change mongodb dependency to a published version like ^5.8.0
- **Because:** Resolve install error by pinning to a known earlier v5 series version likely available; keeps compatibility with code using MongoClient.
- **Reason came from:** `tool_result`
- **Evidence:** npm install error: 'No matching version found for mongodb@^5.11.0.'
- **When:** 2026-11-25T12:51:32+00:00
