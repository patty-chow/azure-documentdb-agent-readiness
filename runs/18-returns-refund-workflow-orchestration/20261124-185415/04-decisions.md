# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 4 |
| model_default | 3 |
| operator | 1 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T06:14:31+00:00

## D002 (build): I chose Node.js with Express and Mongoose and LangChain JS for orchestration.

- **Instead of:** Python/Flask + PyMongo; Node.js + Express + Mongoose (LangChain JS)
- **Because:** The prompt explicitly requested Node.js and LangChain, so this directly satisfies the requirement.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'build a Node.js LangChain orchestration flow'
- **When:** 2026-11-25T06:14:49+00:00

## D003 (build): I chose Mongoose 7.x (compatible with Node 24 and MongoDB 7.0).

- **Instead of:** Mongoose 6.x; Mongoose 7.x (current)
- **Because:** Mongoose 7.x is current and matches the assumption and compatibility requirements.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Pick a current Mongoose release compatible with Node 24 and MongoDB 7.0 (e.g., Mongoose 7.x)'
- **When:** 2026-11-25T06:14:52+00:00

## D004 (build): I chose OpenAI-compatible provider via LangChain Chat model with mock fallback when OPENAI_API_KEY is not set.

- **Instead of:** OpenAI via LangChain ChatOpenAI; Anthropic via LangChain; mock-only without LangChain
- **Because:** LangChain supports OpenAI-compatible models and this choice eases mapping to common environments; adding a mock fallback avoids unexpected costs in demo runs and allows verification without calling external LLMs.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'LLM provider and model selection missing' and prompt expectation of LangChain agents.
- **When:** 2026-11-25T06:15:02+00:00

## D005 (build): I chose to use a mock LLM output for demo/test runs when OPENAI_API_KEY is not present; allow live calls if OPENAI_API_KEY is provided.

- **Instead of:** Call real LLMs in tests/demos; Use mock/stub LLM outputs for demos/tests
- **Because:** Avoids unexpected costs and flakiness in CI; still allows real LLM runs if the developer opts in by setting OPENAI_API_KEY.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'Missing: whether tests should call real LLMs'
- **When:** 2026-11-25T06:15:05+00:00

## D006 (build): I chose to read secrets from environment variables (DOCUMENTDB_URI, OPENAI_API_KEY, OPENAI_MODEL) at runtime and provide .env.example with placeholders.

- **Instead of:** Store secrets in repo; .env env vars at runtime (DOCUMENTDB_URI, OPENAI_API_KEY)
- **Because:** Follows security requirement to avoid committing secrets and matches run environment expectations.
- **Reason came from:** `prompt`
- **Evidence:** Build instructions: 'Never write a secret into a file. Read them from environment variables.' and readiness report guidance.
- **When:** 2026-11-25T06:15:08+00:00

## D007 (build): I chose not to provision any Azure resources and to use the existing cluster referenced by DOCUMENTDB_URI.

- **Instead of:** Create resources via Azure CLI/Bicep; Do not provision resources (use existing cluster)
- **Because:** Policy forbids provisioning and an existing cluster is available; keep sample limited to application code and verification against that cluster.
- **Reason came from:** `prompt`
- **Evidence:** Run policy: 'Azure resource changes allowed: False.' and run environment description that a cluster is already provisioned.
- **When:** 2026-11-25T06:15:10+00:00

## D008 (build): I chose to create a simple unique index on orders.orderId and indexes on returns.orderId and returns.createdAt.

- **Instead of:** Create vector/full-text indexes; Create simple unique index on orders.orderId and returns indexes
- **Because:** Sample doesn't require vector or full-text features; simple indexes support efficient lookups for the orchestration scenario and demonstrate index creation.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Create a simple unique index on orderId in orders and an index on returns.orderId and createdAt.'
- **When:** 2026-11-25T06:15:14+00:00

## D009 (build): I chose to replace LangChain imports with direct OpenAI package calls for live LLM paths and keep a mock fallback; this avoids ESM export issues with the installed langchain package while preserving an orchestration flow semantics.

- **Instead of:** Fix LangChain imports (investigate correct ESM import paths); Replace LangChain usage with direct OpenAI package calls and keep LangChain orchestration simulated
- **Because:** Resolving LangChain ESM export paths would take extra time and possibly require switching the project to ESM; using the OpenAI client is simpler and keeps the sample runnable. The orchestration semantics remain (policy -> refund -> comms).
- **Reason came from:** `tool_result`
- **Evidence:** Runtime error: "Package subpath './chat_models/openai' is not defined by \"exports\" in .../node_modules/langchain/package.json"
- **When:** 2026-11-25T06:16:51+00:00
