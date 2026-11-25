# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 3 |
| readiness_report | 3 |
| operator | 1 |
| prompt | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T14:20:55+00:00

## D002 (build): I chose Python 3 (modern 3.x) for the sample app.

- **Instead of:** Node/TypeScript; Python 3.x
- **Because:** The prompt requested a Python LangChain agent and the run environment has Python available; Python is the natural fit for LangChain and pymongo.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Builder will use a modern Python 3.x (commonly 3.10 or 3.11) virtual environment and target that runtime; pip/venv semantics per skill.md.'
- **When:** 2026-11-25T14:21:09+00:00

## D003 (build): I chose pymongo (the synchronous driver) pinned as pymongo>=4.0,<5.0 in requirements.txt.

- **Instead of:** motor (async); pymongo (sync)
- **Because:** Synchronous pymongo is simple to use for small samples and works well with FastAPI for simple endpoints; it avoids adding async complexity for this sample.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Use PyMongo (pymongo) driver, a current stable 4.x release, pinned in requirements.txt (e.g. pymongo>=4.0,<5.0).'
- **When:** 2026-11-25T14:21:11+00:00

## D004 (build): I chose to use LangChain with OpenAI embeddings when OPENAI_API_KEY is provided, and fall back to deterministic mock embeddings if not present.

- **Instead of:** OpenAI via LangChain; Local mock embeddings only
- **Because:** The prompt asked for a LangChain agent; using LangChain + OpenAI provides realistic embeddings but a fallback is necessary so the sample can be run without secrets.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'Embedding provider credentials (e.g. OPENAI_API_KEY) not present; without an embedding key the end-to-end sample cannot be executed.'
- **When:** 2026-11-25T14:21:14+00:00

## D005 (build): I chose to attempt to create a server-side vector index using a plausible create_index call, but the seed script will detect failures and fall back to storing embeddings as arrays and performing client-side cosine similarity search.

- **Instead of:** Server-side DocumentDB vector index (unknown syntax); Client-side similarity fallback
- **Because:** Because the exact server-side index syntax and search operators could not be verified, the safe approach is to try to create the server-side index where possible but ensure the sample still works by falling back to client-side search if that fails.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report information gaps: 'Exact index-creation syntax' and 'Vector-search aggregation/operator names' are unknown; no MCP/learn server available to verify them.
- **When:** 2026-11-25T14:21:17+00:00

## D006 (build): I chose FastAPI to provide a minimal HTTP API (/score) that accepts a transaction and returns risk score, explanation and matches.

- **Instead of:** FastAPI HTTP API; CLI only
- **Because:** An HTTP API is more demonstrable and easy to exercise with curl; FastAPI is lightweight and standard for Python samples.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Implement a minimal HTTP API (FastAPI) with a /search or /score endpoint ... default will be an API because that is more demonstrable.'
- **When:** 2026-11-25T14:21:19+00:00

## D007 (build): I chose to read the DocumentDB connection string from the DOCUMENTDB_URI environment variable at runtime and never write it into the repository.

- **Instead of:** Write DB credentials into files; Read DOCUMENTDB_URI from environment at runtime
- **Because:** Security best practice and explicit instruction in the readiness report; prevents secrets being committed.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness guidance: 'Read the DocumentDB connection string from the DOCUMENTDB_URI environment variable at runtime and use the provided database sample_fintech_01 for all created collections and indexes.'
- **When:** 2026-11-25T14:21:21+00:00

## D008 (build): I chose to require langchain>=0.0.300,<1.0 in requirements.txt as a reasonable modern version constraint.

- **Instead of:** Pin exact LangChain version; Use a permissive LangChain version constraint
- **Because:** Use a reasonably recent LangChain version while avoiding major breaking future releases; this is a model_default choice due to missing specific version guidance.
- **Reason came from:** `model_default`
- **Evidence:** Need to use LangChain per prompt; exact runtime versions not specified in prompt. No local skill enforces a particular LangChain version.
- **When:** 2026-11-25T14:21:24+00:00
