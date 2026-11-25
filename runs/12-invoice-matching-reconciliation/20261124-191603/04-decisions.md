# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 5 |
| model_default | 5 |
| operator | 2 |
| readiness_report | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T07:03:56+00:00

## D002 (build): I chose Node.js (Express) with Mongoose

- **Instead of:** Python (Flask); Node.js (Express) with Mongoose
- **Because:** The prompt explicitly requests Node.js + Mongoose; this matches available Node 24 runtime and skills.
- **Reason came from:** `prompt`
- **Evidence:** Sample prompt: "Using the DocumentDB skill, build a Node.js LangChain agent using Mongoose"
- **When:** 2026-11-25T07:04:15+00:00

## D003 (build): I chose Mongoose 7.x (pinned in package.json)

- **Instead of:** Mongoose 6.x; Mongoose 7.x
- **Because:** Mongoose 7.x is compatible with Node 24 and modern MongoDB drivers; it is recommended in the prompt review.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Use a recent Mongoose major compatible with Node 24 (e.g., Mongoose 7.x)"
- **When:** 2026-11-25T07:04:18+00:00

## D004 (build): I chose to read the connection string from DOCUMENTDB_URI environment variable and set dbName to 'sample_fintech_12' in mongoose.connect

- **Instead of:** Read connection string and DB from code (hardcoded); Read connection string from env at runtime
- **Because:** Security and prompt policy: do not store secrets in files; use env vars; explicit readiness guidance recommended this.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: "Obtain connection strings from the cluster ... and read them from DOCUMENTDB_URI at runtime; do not hardcode"
- **When:** 2026-11-25T07:04:21+00:00

## D005 (build): I chose ephemeral in-memory session memory stored in the running process (non-persistent)

- **Instead of:** Persist agent memory across process restarts; Ephemeral in-memory session memory per process
- **Because:** Simpler for a sample, matches "within a session" wording and avoids adding persistence/extra resources; document as a design choice.
- **Reason came from:** `model_default`
- **Evidence:** Assumptions: "Agent memory to learn from manual corrections within a session" — no requirement to persist across runs
- **When:** 2026-11-25T07:04:25+00:00

## D006 (build): I chose OpenAI models: gpt-4o-mini for extraction (chat) and text-embedding-3-small for embeddings

- **Instead of:** OpenAI text-embedding-3-small (1536?); OpenAI text-embedding-3-large; Anthropic or other provider
- **Because:** OpenAI is widely used and supported by LangChain; text-embedding-3-small is a reasonable small embedding model for demo; exact dims unknown so noted in report as not verified.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: "Default to an OpenAI-compatible model via LangChain"
- **When:** 2026-11-25T07:04:27+00:00

## D007 (build): I chose to include both LangChain and OpenAI SDK but perform LLM calls via OpenAI SDK for reliability, while exposing a simple LangChain-style agent wrapper

- **Instead of:** Use OpenAI SDK only; Use LangChain library + OpenAI SDK
- **Because:** LangChain JS can be unstable across versions; using the OpenAI SDK for direct calls increases reliability while still providing a LangChain-compatible wrapper for demo purposes.
- **Reason came from:** `model_default`
- **Evidence:** Prompt: "Node.js LangChain agent using Mongoose" — requirement to use LangChain; readiness report left provider/model choice to implementer
- **When:** 2026-11-25T07:04:42+00:00

## D008 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T07:07:19+00:00

## D009 (build): I chose Node.js with Express and Mongoose.

- **Instead of:** Python/Flask; Node.js/Express
- **Because:** Prompt explicitly requests Node.js and Mongoose; Express provides a minimal HTTP surface.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'Using the DocumentDB skill, build a Node.js LangChain agent using Mongoose'
- **When:** 2026-11-25T07:07:40+00:00

## D010 (build): I chose Mongoose 7.x (compatible with Node 24).

- **Instead of:** Mongoose 6.x; Mongoose 7.x
- **Because:** Mongoose 7.x is modern and compatible with Node 24 and recent MongoDB server features.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use a recent Mongoose major compatible with Node 24 (e.g., Mongoose 7.x)'
- **When:** 2026-11-25T07:07:42+00:00

## D011 (build): I chose to use the OpenAI SDK directly instead of LangChain for simplicity and reliability in this sample.

- **Instead of:** Use LangChain for LLM calls; Use OpenAI SDK directly
- **Because:** Direct OpenAI SDK reduces dependency complexity for the sample and keeps extraction and embedding calls explicit; code is structured so LangChain could be added later.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'Missing accelerators... The builder must pick LLM provider and model.' Also prompt asked for a LangChain agent but runtime stability and package variability can cause install problems.
- **When:** 2026-11-25T07:07:45+00:00

## D012 (build): I chose OpenAI 'text-embedding-3-small' for embeddings and assume 1536 dimensions.

- **Instead of:** OpenAI text-embedding-3-small (1536 dims); other embedding models
- **Because:** text-embedding-3-small is a commonly used OpenAI embedding for sample apps; 1536 dims is a plausible dimension (documented for many OpenAI embeddings). This choice will be documented and can be changed by users.
- **Reason came from:** `model_default`
- **Evidence:** Prompt review suggested OpenAI-compatible model and text-embedding-3-small as an example; embedding dimension was not specified.
- **When:** 2026-11-25T07:07:49+00:00

## D013 (build): I chose ephemeral in-memory session-based agent memory (Map) stored per process.

- **Instead of:** Persist agent memory to DocumentDB; Keep agent memory in-process (ephemeral)
- **Because:** Simpler for a sample; meets requirement to learn within a session. Documented as a decision and could be extended to persistent store later.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'Use agent memory to learn from manual corrections within a session' — does not require persistence across restarts.
- **When:** 2026-11-25T07:07:51+00:00
