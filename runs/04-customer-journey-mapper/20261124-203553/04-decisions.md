# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 4 |
| operator | 1 |
| readiness_report | 1 |
| model_default | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T11:14:44+00:00

## D002 (build): I chose Node.js (JavaScript/TypeScript not used) for the sample app.

- **Instead of:** Language: Python; Language: Node.js
- **Because:** The prompt explicitly requests a Node.js sample; Node.js is installed in the run environment (Node v24).
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'Using the DocumentDB skill, build a Node.js LlamaIndex agent'
- **When:** 2026-11-25T11:15:11+00:00

## D003 (build): I chose the official 'mongodb' Node.js driver pinned to ^5.7.0.

- **Instead of:** mongodb ^4.x; mongodb ^5.x (latest 5.x); mongodb 6.x
- **Because:** mongodb 5.x is compatible with Node 24 and MongoDB 7.0 wire protocol; it matches the prompt review guidance and the documentdb-driver skill's singleton pattern.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use the official "mongodb" Node.js driver, pinned to a recent stable major (e.g., mongodb ^5.0.x) compatible with Node 24 and MongoDB 7.0 wire protocol; follow the documentdb-driver guidance to instantiate a process-wide MongoClient singleton.'
- **When:** 2026-11-25T11:15:14+00:00

## D004 (build): I chose to implement 'LlamaIndex-style' prompt engineering and call OpenAI Chat completions directly (openai npm package).

- **Instead of:** Use LlamaIndex JS library (if available); Implement LlamaIndex-style prompt engineering and call OpenAI Chat API directly
- **Because:** No authoritative LlamaIndex Node SDK is installed in the environment; implementing the agent as a small LlamaIndex-like wrapper that constructs a context-rich prompt and calls an LLM is simpler, more reliable, and transparent in a sample. This keeps secrets out of the repo and uses standard OpenAI environment variables.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'Information gaps: LLM provider and model selection ... The builder must choose'. There is no installed LlamaIndex JS skill available in the workspace.
- **When:** 2026-11-25T11:15:17+00:00

## D005 (build): I chose to read all secrets and connection strings from environment variables (DOCUMENTDB_URI, OPENAI_API_KEY, MODEL_NAME).

- **Instead of:** Read credentials from a file; Read credentials from environment variables
- **Because:** Matches prompt instructions and run-policy constraints; avoids committing secrets to repo.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'Never write a secret, password, key or full connection string into a file. Read them from environment variables, and ship a .env.example with placeholder values.'
- **When:** 2026-11-25T11:15:19+00:00

## D006 (build): I chose collection name 'touchpoints' with schema {_id, customerId, timestamp, channel, eventType, metadata}.

- **Instead of:** Collection name 'events'; Collection name 'touchpoints'
- **Because:** The name 'touchpoints' is descriptive for customer journey events and matches prompt suggestions.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Builder will create a 'touchpoints' (or 'events') collection ...'
- **When:** 2026-11-25T11:15:36+00:00

## D007 (build): I chose to insert 1000 synthetic touchpoint events across 10 customers in the seed script.

- **Instead of:** Insert 500 events; Insert 1000 events; Insert 2000 events
- **Because:** 1000 is in the middle of the suggested range: large enough to demonstrate aggregation behavior but small enough to keep seed and runtime quick.
- **Reason came from:** `model_default`
- **Evidence:** Prompt review suggested 500–2,000 events and idempotent seeding.
- **When:** 2026-11-25T11:15:38+00:00
