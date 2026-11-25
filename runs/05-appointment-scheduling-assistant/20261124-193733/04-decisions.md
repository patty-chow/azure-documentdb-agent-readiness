# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 6 |
| operator | 3 |
| prompt | 3 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T08:14:11+00:00

## D002 (build): I chose Node.js (v24) with Express for the sample app and scripts.

- **Instead of:** Python/Flask; Node.js/Express
- **Because:** The user requested Node.js and LangChain; Node.js/Express is standard for minimal HTTP API and matches environment.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'build a Node.js LangChain agent' and readiness_report listing Node.js v24 available.
- **When:** 2026-11-25T08:14:32+00:00

## D003 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T08:16:26+00:00

## D004 (build): I chose Node.js (v24) with Express for the sample app.

- **Instead of:** Python (Flask); Node.js (Express)
- **Because:** The prompt explicitly requests Node.js; Express is a minimal, familiar web framework that suits a small sample HTTP API.
- **Reason came from:** `prompt`
- **Evidence:** Sample prompt: 'Using the DocumentDB skill, build a Node.js LangChain agent...'.
- **When:** 2026-11-25T08:16:51+00:00

## D005 (build): I chose OpenAI (OPENAI_API_KEY) as the LLM provider for the sample.

- **Instead of:** OpenAI; Azure OpenAI; local LLM
- **Because:** OpenAI is commonly available to developers and works with LangChain; choosing OpenAI keeps the sample familiar. The sample will read OPENAI_API_KEY from env and fall back to a no-LLM mode if unset.
- **Reason came from:** `model_default`
- **Evidence:** readiness_report: 'LLM provider and model selection' is missing; the builder must choose and document env vars.
- **When:** 2026-11-25T08:17:05+00:00

## D006 (build): I chose in-memory LangChain ConversationBufferMemory for agent memory.

- **Instead of:** in-memory ConversationBufferMemory; Redis/persistent store; DocumentDB-backed memory
- **Because:** In-memory memory keeps the sample simple to run locally and demonstrates the conversational behavior (e.g., 'move it an hour later'); persistent memory can be added later.
- **Reason came from:** `model_default`
- **Evidence:** Assumptions_from_prompt_review: 'agent memory' unspecified; need to pick memory store.
- **When:** 2026-11-25T08:17:08+00:00

## D007 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T08:20:21+00:00

## D008 (build): I chose Node.js with Express and TypeScript-free JavaScript (Node 24) for the sample agent.

- **Instead of:** Python/Flask; Node.js/Express; Go/Fiber
- **Because:** The user explicitly requested Node.js; Express is a lightweight familiar HTTP framework for small samples and pairs well with LangChain JS.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'build a Node.js LangChain agent'
- **When:** 2026-11-25T08:20:46+00:00

## D009 (build): I chose OpenAI (via OPENAI_API_KEY) as the chat model provider for the LangChain agent.

- **Instead of:** OpenAI (openai.com); Azure OpenAI; local LLM (llama)
- **Because:** OpenAI is widely available for samples, has a stable LangChain integration, and is easy for readers to configure via OPENAI_API_KEY. I will document required env vars in .env.example.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'LLM provider and model selection missing'
- **When:** 2026-11-25T08:20:54+00:00

## D010 (build): I chose in-memory BufferMemory for conversation memory in this sample.

- **Instead of:** Persist conversation memory in DocumentDB collection; In-memory BufferMemory (ephemeral); Redis-backed memory
- **Because:** In-memory memory keeps the sample small and simple; it demonstrates the LangChain memory concept so users can extend to persistent stores in their projects. I'll document this limitation in README.
- **Reason came from:** `model_default`
- **Evidence:** Assumptions: 'agent memory' required but persistence unspecified.
- **When:** 2026-11-25T08:20:56+00:00

## D011 (build): I chose two collections: 'slots' and 'appointments' in database 'sample_healthcare_05' with the schema described in the prompt review assumptions.

- **Instead of:** Use collections 'slots'/'appointments'; Single collection 'appointments' with embedded slot doc
- **Because:** Two collections map clearly to the domain: slots are availability resources and appointments reference slots; this simplifies queries and demonstrates atomic updates across documents.
- **Reason came from:** `model_default`
- **Evidence:** Assumptions_from_prompt_review: 'Builder will create database sample_healthcare_05 with collections slots and appointments.'
- **When:** 2026-11-25T08:21:06+00:00

## D012 (build): I chose a compound index { providerId: 1, start: 1, status: 1 } on the slots collection.

- **Instead of:** Compound index {providerId:1, start:1, status:1}; Separate single-field indexes; Hashed index on providerId
- **Because:** This compound index follows the ESR pattern (equality providerId → range start → filter status) and supports the sample queries efficiently.
- **Reason came from:** `model_default`
- **Evidence:** Assumptions: 'Builder will implement queries to find slots by providerId and time range and create an index such as { providerId: 1, start: 1, status: 1 }'.
- **When:** 2026-11-25T08:21:09+00:00
