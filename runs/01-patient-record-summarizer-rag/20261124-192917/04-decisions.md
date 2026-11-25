# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 4 |
| operator | 1 |
| model_default | 1 |
| skill | 1 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T07:49:30+00:00

## D002 (build): I chose Python 3.11 as the language/runtime for the sample app.

- **Instead of:** Node.js/TypeScript; Python 3.10/3.11
- **Because:** The prompt requested a Python LlamaIndex RAG agent and Python 3.11 is compatible with modern LlamaIndex and typing support.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Use Python 3.10 or 3.11 (common current LlamaIndex/typing support)".
- **When:** 2026-11-25T07:49:49+00:00

## D003 (build): I chose pymongo (sync) as the Mongo-compatible Python driver, pinned to >=4.3 in requirements.txt.

- **Instead of:** use motor async driver; use pymongo sync driver
- **Because:** Synchronous pymongo is simpler for a small sample script and aligns with documentdb-driver guidance about singleton MongoClient. Also the environment uses simple scripts and verification rather than async servers.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: "Use pymongo as the Mongo-compatible Python driver (pymongo >= 4.3, pinned in requirements.txt)."
- **When:** 2026-11-25T07:49:53+00:00

## D004 (build): I chose OpenAI text-embedding-3-small (1536 dims) as the default embedding model, but seed script will fall back to deterministic random normalized vectors if OPENAI_API_KEY is not present.

- **Instead of:** use OpenAI text-embedding-3-small (1536d); use random embeddings for sample data
- **Because:** Choosing a known 1536-dim embedding keeps index dimensions consistent; fallback ensures reproducible local runs without requiring API keys.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Use an external embedding provider (default: OpenAI text-embedding-3-small with 1536-dim embeddings)" and readiness report noting embedding model choice not specified.
- **When:** 2026-11-25T07:49:56+00:00

## D005 (build): I chose vector-hnsw for the sample collection's vector index.

- **Instead of:** vector-hnsw; vector-diskann; ivf
- **Because:** HNSW provides good accuracy/latency tradeoff for small-to-medium samples and is simpler to configure for a sample app.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Create a `cosmosSearch` vector index on the `embedding` field... use `vector-hnsw`" and guidance in readiness_report recommending HNSW for many cases.
- **When:** 2026-11-25T07:49:59+00:00

## D006 (build): I chose to read DOCUMENTDB_URI and OPENAI_API_KEY (and optional OPENAI_API_BASE) from environment variables at runtime, with a .env.example providing placeholders.

- **Instead of:** store secrets in files; read connection string from environment variable
- **Because:** Security best practice and the prompt explicitly required using env vars and .env.example placeholders.
- **Reason came from:** `prompt`
- **Evidence:** Skill MD: "Its connection string is in the environment variable `DOCUMENTDB_URI`. Read it from the environment at run time. Never write its value into a file".
- **When:** 2026-11-25T07:50:02+00:00

## D007 (build): I chose to use the documentdb MCP server's documentdb_create_index tool to create the cosmosSearch vector index on the cluster.

- **Instead of:** create vector index programmatically via pymongo createIndexes command; use the documentdb MCP server's documentdb_create_index tool
- **Because:** The MCP tool is designed for data-plane index operations and avoids using unsupported naive createIndex calls; it also centralizes index semantics for Azure DocumentDB.
- **Reason came from:** `skill`
- **Evidence:** Readiness report and documentdb-vector-search skill: "Create vector indexes using the documented createIndexes/runCommand pattern with cosmosSearch/cosmosSearchOptions" and the MCP server provides documentdb_create_index to perform data-plane index creation.
- **When:** 2026-11-25T07:51:18+00:00

## D008 (build): I chose to fallback to issuing a createIndexes database command via pymongo (db.command) after the documentdb_create_index MCP tool failed.

- **Instead of:** retry documentdb_create_index tool; use pymongo db.command(createIndexes)
- **Because:** db.command(createIndexes) is the documented createIndexes/runCommand pattern for vector-index creation and gives more control from the client library; it avoids the opaque MCP tool failure and is still a supported data-plane action.
- **Reason came from:** `tool_result`
- **Evidence:** Attempt to call documentdb_create_index returned 'Error: Function failed.' with no details.
- **When:** 2026-11-25T07:51:50+00:00
