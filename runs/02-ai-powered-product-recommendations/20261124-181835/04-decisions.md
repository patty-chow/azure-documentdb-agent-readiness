# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 2 |
| readiness_report | 2 |
| operator | 1 |
| model_default | 1 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T02:23:13+00:00

## D002 (build): I chose the official mongodb npm driver pinned to ^5.9.0 and to instantiate a singleton MongoClient.

- **Instead of:** mongodb driver v4.x; mongodb driver v5.x (^5.9.0); mongoose ORM
- **Because:** Official driver is lightweight, recommended in skills, and aligns with the documentdb-driver skill which prescribes a singleton MongoClient; mongoose would add unnecessary complexity.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Use the official mongodb npm driver (package 'mongodb') pinned to a recent stable major compatible with Node 24 (e.g. ^5.0), and follow the documentdb-driver guidance to instantiate a singleton MongoClient."
- **When:** 2026-11-25T02:23:35+00:00

## D003 (build): I chose to support OpenAI embeddings when OPENAI_API_KEY is provided, but fall back to deterministic synthetic embeddings when not provided.

- **Instead of:** Use OpenAI embeddings only and fail if key missing; Use synthetic deterministic embeddings when OPENAI_API_KEY is missing; Require user to provide embeddings ahead of time and skip embedding generation
- **Because:** This keeps the sample runnable without credentials while allowing end-to-end behavior when keys are available.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: "Missing: an embedding/LLM provider integration and credentials... The embedding→DiskANN part and agent reasoning cannot be executed end-to-end; the sample would have to use mocked embeddings or skip the LLM reasoning."
- **When:** 2026-11-25T02:23:37+00:00

## D004 (build): I chose to implement a lightweight agent-like flow (embedding store + vector search + optional OpenAI LLM reasoning) instead of relying on LlamaIndex Node bindings.

- **Instead of:** Install and use LlamaIndex Node bindings (unknown availability); Implement a simple agent pattern using embeddings + OpenAI LLM calls and DocumentDB vector search; Require the user to install LlamaIndex separately
- **Because:** LlamaIndex Node SDK availability and example patterns are uncertain; implementing the agent flow directly keeps the sample small, understandable, and runnable while matching the functional goals (recommendations + reasoning).
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: "LLM provider & LlamaIndex Node bindings... not installed/verified" and prompt requirement to make sample runnable.
- **When:** 2026-11-25T02:23:40+00:00

## D005 (build): I chose to persist agent session memory in a DocumentDB collection named 'sessions' in the sample_retail_02 database.

- **Instead of:** Store session memory in Redis; Store session memory in-memory (process); Store session memory in a DocumentDB collection
- **Because:** Persisting sessions in DocumentDB makes per-session personalization durable across process restarts and demonstrates using DocumentDB for session storage, which is instructive for sample readers.
- **Reason came from:** `model_default`
- **Evidence:** No skill prescribed session-store; using DocumentDB aligns with sample goals and keeps dependencies minimal (readiness_report 'information_gaps').
- **When:** 2026-11-25T02:23:48+00:00

## D006 (build): I chose to create a DiskANN vector index with dimensions 1536 (matching OpenAI text-embedding-3-small) on the products collection.

- **Instead of:** vector-hnsw; vector-ivf; vector-diskann
- **Because:** DiskANN is recommended for larger vector stores and the readiness report suggested DiskANN; 1536 is standard for OpenAI's text-embedding-3-small and is a reasonable default for the sample.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review and documentdb-vector-search skill recommending DiskANN for scale and guidance to set dimensions to embedding model.
- **When:** 2026-11-25T02:23:50+00:00

## D007 (build): I chose to remove node-fetch and rely on the global fetch available in Node 18+/24.

- **Instead of:** Keep node-fetch dependency; Remove node-fetch and use global fetch available in Node 18+ / use native fetch
- **Because:** Avoid dependency resolution issues and use the built-in fetch in Node 24 as the runtime supports it.
- **Reason came from:** `tool_result`
- **Evidence:** npm install failed: "No matching version found for node-fetch@^3.4.0." and Node 24 provides global fetch per run environment.
- **When:** 2026-11-25T02:24:54+00:00
