# Decision log

| Reason came from | Decisions |
|---|---|
| readiness_report | 3 |
| prompt | 3 |
| operator | 1 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T14:33:17+00:00

## D002 (build): I chose Python as the language and runtime, using the system Python 3.13 where available.

- **Instead of:** Node.js/TypeScript; Python 3.x (various)
- **Because:** Python is the most appropriate for LlamaIndex, pymongo drivers, and rapid sample development; the environment provides Python 3.13 so use that.
- **Reason came from:** `readiness_report`
- **Evidence:** Assumption: 'Use a modern Python 3.x runtime' and readiness report showing Python 3.13 available.
- **When:** 2026-11-25T14:33:35+00:00

## D003 (build): I chose pymongo pinned to a 4.x release (pymongo==4.6.1) as the MongoDB driver.

- **Instead of:** pymongo>=4,<5; motor (async) driver; mongoengine ORM
- **Because:** pymongo is the standard synchronous driver, simple for samples and matches readiness guidance to use standard drivers for MongoDB 7.0 wire protocol.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Use pymongo (MongoDB-compatible driver) pinned to a recent 4.x release' from prompt review.
- **When:** 2026-11-25T14:33:37+00:00

## D004 (build): I chose OpenAI for embeddings and chat (expect OPENAI_API_KEY in env), using text-embedding-3-small (1536 dims) as the embedding model.

- **Instead of:** Use OpenAI for embeddings and chat; Use local sentence-transformers embeddings and local LLM; Use Anthropic or other provider
- **Because:** OpenAI is commonly available and aligns with LlamaIndex examples; 1536 dims aligns with the embedding model cited in the assumptions.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Use OpenAI for embeddings and chat ... text-embedding-3-small (1536 dims)' from prompt review.
- **When:** 2026-11-25T14:33:39+00:00

## D005 (build): I chose to store embeddings in DocumentDB and perform application-side kNN re-ranking (cosine) in Python as the retrieval method, with an optional native vector-index path left as TODO in README.

- **Instead of:** Create provider-specific vector index in DB using undocumented syntax; Store embeddings and re-rank in application code
- **Because:** The local environment lacks authoritative index-creation docs; application-side re-rank is robust and works across clusters without relying on provider-specific index creation syntax.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness guidance: 'Do not assume Atlas-style $search/knnBeta exists; implement retrieval so it works with either (a) native kNN/$search aggregation if validated, or (b) application-side re-rank fallback.'
- **When:** 2026-11-25T14:33:41+00:00

## D006 (build): I chose to read connection string and keys from environment variables (DOCUMENTDB_URI and OPENAI_API_KEY) and include a .env.example with placeholders.

- **Instead of:** Use environment variables only (DOCUMENTDB_URI, OPENAI_API_KEY); Embed secrets in files; Use Azure CLI to fetch secrets
- **Because:** Do not store secrets in repo; environment variables are standard and match the run environment description.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness guidance: 'Read the cluster connection string from DOCUMENTDB_URI at runtime and never write or hard-code it; ...'
- **When:** 2026-11-25T14:33:43+00:00

## D007 (build): I chose not to create or modify any Azure resources and to use the existing DocumentDB cluster via DOCUMENTDB_URI.

- **Instead of:** Provision Azure resources (az/ARM/Bicep); Do not change Azure resources
- **Because:** The run policy forbids creating/modifying Azure resources; sample will operate against the provided cluster and document any provider-specific index steps in README.
- **Reason came from:** `prompt`
- **Evidence:** Run policy: 'Azure resource changes allowed: False.' from prompt.
- **When:** 2026-11-25T14:33:47+00:00

## D008 (build): I chose to remove numpy from the dependencies and implement embedding/vector math using pure-Python to avoid build issues in the environment.

- **Instead of:** Keep numpy dependency and attempt to install system build tools; Remove numpy and use pure-Python math for vector ops
- **Because:** Avoids environment-specific native build issues and keeps the sample lightweight; for small demo vectors pure-Python math is sufficient.
- **Reason came from:** `tool_result`
- **Evidence:** pip install failed building numpy with error 'No module named distutils' during wheel build.
- **When:** 2026-11-25T14:34:51+00:00
