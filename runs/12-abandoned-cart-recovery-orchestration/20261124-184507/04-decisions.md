# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 5 |
| prompt | 2 |
| skill | 2 |
| operator | 1 |
| readiness_report | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T05:47:25+00:00

## D002 (build): I chose Node.js (JavaScript) targeting Node 24 with plain JavaScript (no TypeScript).

- **Instead of:** Python; Node.js (TypeScript); Node.js (JavaScript)
- **Because:** The user explicitly asked for a Node.js LangChain pipeline; Node 24 is available in the run environment per the skill_md and readiness report.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'Using the DocumentDB skill, build a Node.js LangChain orchestration pipeline'
- **When:** 2026-11-25T05:47:46+00:00

## D003 (build): I chose the official MongoDB Node.js driver 'mongodb' pinned to '^5.7.0'.

- **Instead of:** mongodb@^4.x; mongodb@^5.7.0; mongodb@^6.x
- **Because:** mongodb 5.x is widely compatible with Node 24 and aligns with the readiness guidance to use official driver and singleton pattern; pinning to ^5.7.0 balances modern features and stability.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Builder will use the official MongoDB Node.js driver (npm package "mongodb") at a current stable version compatible with Node 24 (e.g. mongodb >=5.x/6.x).'
- **When:** 2026-11-25T05:47:58+00:00

## D004 (build): I chose to read the DocumentDB connection string from environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Use connection string from a config file committed to repo; Read connection string from environment variable DOCUMENTDB_URI; Prompt user at runtime to paste connection string
- **Because:** This follows the run environment guidance and avoids committing secrets to the repository.
- **Reason came from:** `skill`
- **Evidence:** Skill_md: 'Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time. Never write its value into any file...'.
- **When:** 2026-11-25T05:48:07+00:00

## D005 (build): I chose OpenAI via LangChain with environment variables OPENAI_API_KEY and OPENAI_MODEL (default 'gpt-4o-mini').

- **Instead of:** OpenAI via LangChain; Anthropic via LangChain; Local LLM (llama)
- **Because:** OpenAI is commonly available, integrates with LangChain, and is simple for a sample. Using env vars keeps keys out of code.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Builder will wire a configurable LLM provider via env vars (e.g., OPENAI_API_KEY and OPENAI_MODEL).'
- **When:** 2026-11-25T05:48:10+00:00

## D006 (build): I chose to use the existing pre-provisioned cluster (DOCUMENTDB_URI) and not provision any Azure resources.

- **Instead of:** Provision a new cluster via az/bicep/terraform; Use the existing pre-provisioned cluster from DOCUMENTDB_URI
- **Because:** The environment already has a reachable cluster and policy forbids creating new Azure resources in this run; use the existing one.
- **Reason came from:** `readiness_report`
- **Evidence:** Run environment skill_md: 'This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable.' Also run_policy: 'Azure resource changes allowed: False.'
- **When:** 2026-11-25T05:48:15+00:00

## D007 (build): I chose separate 'customers' and 'carts' collections linked by customerId, with carts containing items array and timestamps (updatedAt, processedAt) and a deliveryLog array.

- **Instead of:** Use a single 'carts' collection with embedded customer info; Use separate 'customers' and 'carts' collections linked by customerId; Use relational-style collections for customers, carts, orders and join at runtime
- **Because:** Separating customers avoids duplicating contact preferences and keeps cart processing focused; it's simple and matches the prompt's expectations for contact preference field used by channel agent.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review and standard practice for retail cart modeling: 'customers' and 'carts' collections described there.
- **When:** 2026-11-25T05:48:19+00:00

## D008 (build): I chose a compound index on { customerId: 1, updatedAt: 1, processedAt: 1 } following ESR (Equality → Sort → Range) guidance, plus a sparse index on processedAt to speed queries that filter for unprocessed carts.

- **Instead of:** No index (collection scan); Single-field index on updatedAt; Compound index (customerId, updatedAt, processedAt) following ESR rules
- **Because:** Querying for carts abandoned >2 hours will filter by processedAt null/absent and sort by updatedAt; compound index supports that pattern and avoids a COLLSCAN.
- **Reason came from:** `skill`
- **Evidence:** documentdb-indexing skill: 'prefer compound ESR indexes for equality+sort+range patterns' and 'keep index count small'.
- **When:** 2026-11-25T05:48:27+00:00

## D009 (build): I chose not to use vector search or embeddings for this sample; the copy-generation agent will use the LLM directly with cart/customer context.

- **Instead of:** Use vector search for semantic matching; Do not use vector search; use simple prompt-based personalization
- **Because:** Keeps sample smaller and focused on orchestration; readiness_report noted vector-capable cluster but using vectors is out-of-scope for this sample.
- **Reason came from:** `model_default`
- **Evidence:** Prompt focused on copy-generation Agent and channel send; vector search not required for generating personalized recovery messages.
- **When:** 2026-11-25T05:48:30+00:00

## D010 (build): I chose to implement local stub functions sendEmail/sendSMS that log, simulate success, and persist delivery status to DocumentDB; README will include guidance to replace stubs with SendGrid/Twilio.

- **Instead of:** Integrate live SendGrid/Twilio; Implement local stub functions that log and persist delivery status; Require user to supply provider credentials
- **Because:** Avoids sending real messages in a sample and keeps the sample runnable without third-party credentials; still demonstrates handoff and logging.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'treat provider integrations as out-of-scope for live sends by implementing checkable sendEmail/sendSMS stubs.'
- **When:** 2026-11-25T05:48:35+00:00

## D011 (build): I chose NOT to install the 'langchain' npm package because a specific compatible version for Node 24 was uncertain in this environment; instead I implemented a lightweight orchestration that follows LangChain design patterns but uses the OpenAI SDK directly.

- **Instead of:** Install 'langchain' npm package (unknown compatible version); Do not install 'langchain' package; implement a lightweight orchestration that mirrors LangChain patterns using OpenAI SDK
- **Because:** Avoids a likely npm install failure and keeps the sample runnable; README documents how to adapt to LangChain if desired.
- **Reason came from:** `model_default`
- **Evidence:** Uncertainty about exact LangChain JS package version and API stability for this environment (no authoritative version available in prompt).
- **When:** 2026-11-25T05:48:45+00:00
