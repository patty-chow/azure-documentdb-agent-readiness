# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 5 |
| tool_result | 3 |
| readiness_report | 2 |
| operator | 1 |
| skill | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T07:25:01+00:00

## D002 (build): I chose Python 3.10+ (use the environment's python) for the sample app.

- **Instead of:** Node.js; Python 3.10+
- **Because:** The sample was requested as a Python LangChain agent; Python is the natural choice and the environment provides Python.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Use Python 3.10 (or the venv's python)".
- **When:** 2026-11-25T07:25:22+00:00

## D003 (build): I chose to read all secrets (DOCUMENTDB_URI and LLM/embedding keys) from environment variables and provide a .env.example with placeholders.

- **Instead of:** Embed/LLM keys in files; Read secrets from environment variables
- **Because:** Security best practice and matches prompt requirement.
- **Reason came from:** `prompt`
- **Evidence:** Prompt review: "Never write a secret... Read them from environment variables, and ship a `.env.example`".
- **When:** 2026-11-25T07:25:25+00:00

## D004 (build): I chose OpenAI as the default LLM/embedding provider, using OPENAI_API_KEY and models text-embedding-3-small (1536 dims) and gpt-4o-mini for LLM calls.

- **Instead of:** OpenAI; Azure OpenAI; Hugging Face
- **Because:** OpenAI is a common default, LangChain integrates with it, and readiness report suggested OpenAI as a reasonable default; embedding dims (1536) determine vector index shape.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Use OpenAI as a default provider with an embedding model such as text-embedding-3-small (1536 dims) and an LLM (gpt-4o-mini or gpt-4o) via LangChain."
- **When:** 2026-11-25T07:25:27+00:00

## D005 (build): I chose to use 1536 dimensions (text-embedding-3-small) for the vector index and embedding arrays.

- **Instead of:** Store embedding dims dynamically; Hardcode embedding dims
- **Because:** We must pick a dims value to create the vector index; 1536 is the known size for text-embedding-3-small and a reasonable default for demos.
- **Reason came from:** `prompt`
- **Evidence:** Readiness report / assumptions: "text-embedding-3-small (1536 dims)" and guidance that vector index dims must match the embedding model output.
- **When:** 2026-11-25T07:25:30+00:00

## D006 (build): I chose the collection name 'esg_companies' and the schema fields described in the prompt review (name, raw_esg_text, score_E/S/G, rationale strings, rationale_embedding, schemaVersion).

- **Instead of:** Collection name 'companies'; Collection name 'esg_companies'
- **Because:** Clear naming for a focused sample; matches prompt review assumptions and makes code readable.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: suggested schema and collection name.
- **When:** 2026-11-25T07:25:33+00:00

## D007 (build): I chose to create standard (name, schemaVersion, score fields) indexes in the seed script using pymongo and create the vector index using the documentdb MCP server during build-time verification.

- **Instead of:** Create vector index via pymongo createIndexes command in seed script; Create only standard indexes in seed script and create vector index via MCP server in verification step
- **Because:** Safer and follows the readiness report recommendation to use the createIndexes JSON form and the MCP server for vector index. Keeps sample runnable without special privileges and still automates vector-index creation in the verification step.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness guidance: vector index creation requires the cosmosSearch/cosmosSearchOptions JSON shape and the MCP server offers create_index tool; local pymongo might not correctly create vector indexes for DocumentDB.
- **When:** 2026-11-25T07:25:42+00:00

## D008 (build): I chose 'vector-hnsw' for the sample vector index (kind: 'vector-hnsw').

- **Instead of:** vector-diskann; vector-hnsw; vector-ivf
- **Because:** The demo dataset is small (<=12 documents); HNSW is easier to create and suitable for demos while matching readiness guidance.
- **Reason came from:** `skill`
- **Evidence:** documentdb-vector-search guidance: HNSW is appropriate up to ~50k vectors and is suitable for small demo datasets.
- **When:** 2026-11-25T07:25:54+00:00

## D009 (build): I chose to implement a fallback deterministic scorer and embedding generator when OPENAI API key is not configured.

- **Instead of:** Fail when OPENAI_API_KEY missing; Fallback to deterministic scorer/embeddings
- **Because:** Allows the sample to be runnable and testable even when API keys are not present in the environment; tests and seed/process can run in CI and offline dev environments.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: "LLM / Embedding provider credentials... available: false... Workaround: simulate with a small random embedding generator for offline tests if keys are not available."
- **When:** 2026-11-25T07:27:07+00:00

## D010 (build): I chose to relax the langchain requirement to 'langchain>=0.0.240,<1.0' to allow pip to install a compatible release available in PyPI.

- **Instead of:** Keep pinned langchain==0.0.401 and fail; Relax langchain version to a broadly available release specifier
- **Because:** To allow dependency installation in this environment while keeping compatibility with LangChain APIs used in the sample.
- **Reason came from:** `tool_result`
- **Evidence:** pip error showed langchain==0.0.401 not available; many older versions exist. Relaxing to a range increases chance of install success.
- **When:** 2026-11-25T07:27:15+00:00

## D011 (build): I chose to relax numpy requirement to 'numpy>=1.24,<2.0' to allow pip to pick a compatible wheel for the environment's Python version.

- **Instead of:** Keep numpy==1.26.0; Relax numpy to a broadly available range
- **Because:** Relaxing numpy avoids install errors while keeping compatibility for the sample's numeric operations.
- **Reason came from:** `tool_result`
- **Evidence:** pip error: No matching distribution for numpy==1.26.0; environment uses Python 3.13 and some numpy versions have tight Python bounds.
- **When:** 2026-11-25T07:27:27+00:00

## D012 (build): I chose to stop retrying create_index via the MCP server after two failed attempts and proceed by verifying that documents were written and creating a report entry explaining the failure.

- **Instead of:** Retry create_index until success; Stop and proceed without creating vector index via MCP server
- **Because:** Tool failed repeatedly; per instructions stop after second attempt and take another route (verify non-vector parts and note index creation as not_verified).
- **Reason came from:** `tool_result`
- **Evidence:** documentdb_create_index tool returned 'Error: Function failed.' on two attempts.
- **When:** 2026-11-25T07:28:09+00:00
