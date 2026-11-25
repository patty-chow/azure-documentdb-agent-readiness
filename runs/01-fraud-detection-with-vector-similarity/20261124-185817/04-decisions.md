# Decision log

| Reason came from | Decisions |
|---|---|
| readiness_report | 3 |
| model_default | 3 |
| operator | 1 |
| docs | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T06:27:15+00:00

## D002 (build): I chose Python 3.10+ (use system Python 3.13 present) as the language/runtime for the sample.

- **Instead of:** Use Node.js/TypeScript; Use Python 3.10+ (virtualenv)
- **Because:** Python is standard for LangChain samples and the environment already provides Python; it keeps the sample accessible to Python developers.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'Python 3.13.13 on PATH.'
- **When:** 2026-11-25T06:27:48+00:00

## D003 (build): I chose the Python pymongo driver (pymongo>=4.4,<5.0) for connecting to Azure DocumentDB.

- **Instead of:** Use node 'mongodb' driver; Use Python pymongo driver
- **Because:** pymongo is the officially supported MongoDB driver for Python and is compatible with the DocumentDB MongoDB wire protocol; the driver aligns with the chosen language.
- **Reason came from:** `model_default`
- **Evidence:** Assumption in prompt review: 'Use the Python pymongo driver, pinned to a modern 4.x release compatible with MongoDB 7.0 (e.g., pymongo>=4.4,<5.0).'
- **When:** 2026-11-25T06:27:51+00:00

## D004 (build): I chose sentence-transformers/all-MiniLM-L6-v2 (local) with 384 dimensions for embeddings.

- **Instead of:** Use OpenAI embeddings (1536 dims); Use sentence-transformers/all-MiniLM-L6-v2 (384 dims)
- **Because:** Using a local sentence-transformers model avoids requiring cloud API keys in the sample and keeps the example reproducible for developers; 384 dims are standard for that model and fit small demo indexes.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report information gap: 'Embedding model & dimensions' and suggestion to use local/open-source model to avoid requiring cloud API keys.
- **When:** 2026-11-25T06:27:53+00:00

## D005 (build): I chose a vector-ivf index with dimensions=384 and numLists=1 for the sample fraud_patterns collection.

- **Instead of:** vector-hnsw; vector-ivf; vector-diskann
- **Because:** IVF with numLists=1 is simple, works for small demo datasets, and is explicitly documented as acceptable for experimentation in Azure DocumentDB docs.
- **Reason came from:** `docs`
- **Evidence:** Learn docs: 'To create a vector index using the IVF algorithm, set "kind": "vector-ivf" and set numLists; for small demo you can set numLists to 1 (brute-force)'.
- **When:** 2026-11-25T06:27:56+00:00

## D006 (build): I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Use Entra/OIDC auth flow in sample; Use connection string (DOCUMENTDB_URI) read from environment
- **Because:** Avoids embedding secrets in the repository and matches the sample's run environment described in the prompt.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report guidance: 'Copy your Connection string value from the Azure portal for your DocumentDB cluster and store it as DOCUMENTDB_URI.'
- **When:** 2026-11-25T06:28:03+00:00

## D007 (build): I chose deterministic, template-based explanations for the LangChain agent when an LLM key is not provided; if OPENAI_API_KEY is present the sample can optionally use OpenAI for richer explanations.

- **Instead of:** Require OpenAI API key and use OpenAI LLM for explanations; Use deterministic, template-based explanations (no external LLM required)
- **Because:** Keeps the sample runnable without cloud LLM keys and still demonstrates LangChain tooling; provides an optional LLM path for users who do have API keys.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report information gap: 'LangChain integration details' and 'Use a local/open-source embedding model to avoid requiring cloud API keys.'
- **When:** 2026-11-25T06:28:05+00:00

## D008 (build): I chose to use the documentdb MCP server tools to create the vector index and insert sample documents for verification rather than running the local seed script, because DOCUMENTDB_URI may not be set in this environment.

- **Instead of:** Run seed.py locally (requires DOCUMENTDB_URI set); Use the documentdb MCP tools to create index and insert sample documents for verification
- **Because:** MCP tools allow data-plane verification programmatically without requiring the environment variable to be set for the subprocess run; they are available in this run.
- **Reason came from:** `readiness_report`
- **Evidence:** Run environment: DOCUMENTDB_URI is expected in the environment on the developer machine per skill_md, but this workspace may not have it set; MCP tools are available (readiness_report).
- **When:** 2026-11-25T06:28:52+00:00
