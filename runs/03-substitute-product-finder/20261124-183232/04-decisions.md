# Decision log

| Reason came from | Decisions |
|---|---|
| docs | 3 |
| tool_result | 2 |
| prompt | 2 |
| operator | 1 |
| skill | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T05:16:55+00:00

## D002 (build): I chose Python (FastAPI) with Beanie ODM and Motor MongoDB driver targeting the Python runtime available on the machine.

- **Instead of:** Node.js (Express, TypeScript); Python (FastAPI, Beanie)
- **Because:** Prompt explicitly requested Python + FastAPI + Beanie; machine has Python available so use the requested stack for minimal friction.
- **Reason came from:** `tool_result`
- **Evidence:** readiness_report: "Python 3.13.13" and prompt: "Build a simple Python FastAPI app using Beanie ODM".
- **When:** 2026-11-25T05:17:18+00:00

## D003 (build): I chose OpenAI text-embedding-3-small with 1536 dimensions for embeddings, falling back to deterministic random vectors if OPENAI_API_KEY is not provided.

- **Instead of:** text-embedding-3-small (1536 dims); text-embedding-3-large (higher dims); local/random vectors
- **Because:** text-embedding-3-small is cost-effective for 10k vectors and widely used for semantic search; deterministic fallback supports running the sample without an API key.
- **Reason came from:** `prompt`
- **Evidence:** assumptions_from_prompt_review: "Default model: text-embedding-3-small (assumed dims 1536)."
- **When:** 2026-11-25T05:17:21+00:00

## D004 (build): I chose HNSW ('vector-hnsw') index for the embedding field with moderate parameters suitable for ~10k vectors (m=16, efConstruction=200).

- **Instead of:** HNSW vector index ('vector-hnsw'); DiskANN ('vector-diskann'); IVF ('vector-ivf')
- **Because:** HNSW offers a good balance of recall and latency for mid-size datasets (~10k) and is widely supported; choose moderate params to keep build-time reasonable.
- **Reason came from:** `docs`
- **Evidence:** readiness_report guidance: "create vector indexes using ... kind = 'vector-hnsw'|'vector-diskann'|'vector-ivf' and ensure dimensions match the model."
- **When:** 2026-11-25T05:17:25+00:00

## D005 (build): I chose to read DOCUMENTDB_URI from environment using pydantic BaseSettings and .env file support; the app will error clearly if missing or invalid.

- **Instead of:** Read DOCUMENTDB_URI from environment (pydantic BaseSettings); Hard-code connection string in config (not allowed); Prompt user at runtime
- **Because:** Secure and matches prompt's requirement to not store secrets in repo and provide clear user-friendly errors.
- **Reason came from:** `docs`
- **Evidence:** readiness_report instruction: "Read the production cluster's connection string from DOCUMENTDB_URI (environment); include a .env.example with placeholder, and have the app show a clear error and exit if the env var is missing or if the connection attempt fails."
- **When:** 2026-11-25T05:17:28+00:00

## D006 (build): I chose a denormalized Product document with fields: product_id (str), name, description, category, price, attributes (dict), embedding (List[float]), created_at.

- **Instead of:** Relational-like normalized model; Denormalized document model with embedding array inside product document
- **Because:** Denormalized documents are simpler for read-heavy product lookup and vector search; embedding stored directly on the product simplifies vector-search queries.
- **Reason came from:** `prompt`
- **Evidence:** assumptions_from_prompt_review: "Define a Product document with fields: ... embedding (List[float])."
- **When:** 2026-11-25T05:17:31+00:00

## D007 (build): I chose to use a singleton AsyncIOMotorClient and initialize Beanie once at app startup following documentdb-driver guidance.

- **Instead of:** Create a new Motor client per request; Use a singleton Motor client reused across app lifetime
- **Because:** Avoid connection overhead and pool exhaustion; matches skill guidance.
- **Reason came from:** `skill`
- **Evidence:** documentdb-driver skill: 'Reuse MongoClient as a process-wide singleton; never create a new client per request.'
- **When:** 2026-11-25T05:17:34+00:00

## D008 (build): I chose to create the vector index using the documentdb MCP server (documentdb_create_index) during verification and also provide a Python helper script that can attempt the same via the MongoDB command if desired.

- **Instead of:** Create vector index from sample app using motor/pymongo; Use the documentdb MCP server's documentdb_create_index tool for index creation/verification
- **Because:** MCP tool is authoritative and avoids subtle compatibility issues; including a Python helper provides portability for users not using MCP.
- **Reason came from:** `docs`
- **Evidence:** readiness_report guidance: "Create vector indexes using the DocumentDB 'createIndexes' runCommand JSON shape ..." and availability of documentdb MCP server in the environment.
- **When:** 2026-11-25T05:17:38+00:00

## D009 (build): I chose to use the documentdb MCP server tools to perform verification (create index, insert sample documents, count documents, and run an aggregate vector query) because installing Python dependencies failed due to pydantic-core build errors on the available Python runtime.

- **Instead of:** Install full Python dependencies and run local ingestion and query scripts; Use the DocumentDB MCP data-plane tools to create index and insert sample documents for verification
- **Because:** MCP tools are available, authoritative, and can perform the necessary data-plane checks without requiring heavy local package compilation; this keeps verification speedy and avoids environment-specific build failures.
- **Reason came from:** `tool_result`
- **Evidence:** pip install failed building pydantic-core (maturin/cargo errors) in the run output.
- **When:** 2026-11-25T05:19:56+00:00
