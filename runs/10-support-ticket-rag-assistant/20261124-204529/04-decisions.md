# Decision log

| Reason came from | Decisions |
|---|---|
| readiness_report | 9 |
| prompt | 4 |
| model_default | 3 |
| tool_result | 3 |
| operator | 2 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T11:44:18+00:00

## D002 (build): I chose Python (use Python 3.13 runtime available on PATH).

- **Instead of:** Node.js; Python
- **Because:** The run environment provides Python 3.13 and the sample prompt expected Python; using the available Python runtime avoids portability issues.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: "Python 3.13.13 on PATH" and assumptions suggested Python 3.11; runtime available is 3.13.
- **When:** 2026-11-25T11:44:54+00:00

## D003 (build): I chose OpenAI text-embedding-3-small with 1536 dimensions as the default embedding model.

- **Instead of:** OpenAI text-embedding-3-small (1536 dims); OpenAI text-embedding-3-large; Azure OpenAI embeddings
- **Because:** Provides a good tradeoff of size/quality and matches DocumentDB vector index support; it's a common default and dimensions (1536) are widely supported.
- **Reason came from:** `prompt`
- **Evidence:** Assumption and readiness report suggested embeddings = text-embedding-3-small (1536 dims).
- **When:** 2026-11-25T11:44:57+00:00

## D004 (build): I chose gpt-4o-mini as the default chat/generation model for concise suggestions.

- **Instead of:** gpt-4o-mini; gpt-4o; gpt-4o-mini-preview
- **Because:** gpt-4o-mini is a lower-cost, fast conversational model suitable for concise answer generation in a sample app.
- **Reason came from:** `model_default`
- **Evidence:** Assumptions suggested gpt-4o-mini or gpt-4o as examples.
- **When:** 2026-11-25T11:45:00+00:00

## D005 (build): I chose to create the vector index from the seed script using pymongo's createIndexes command (data-plane createIndexes) and to use the documentdb MCP server for inspection/verification.

- **Instead of:** Use documentdb MCP server to create index; Use pymongo createIndexes command from seed.py
- **Because:** Using pymongo's createIndexes from the seed script is simple, reproducible, and can run without extra MCP tooling; developers can also use the documentdb MCP tools to inspect the indexes created.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness guidance: "When creating a vector index, use createIndexes with cosmosSearch/cosmosSearchOptions (kind: vector-hnsw | vector-ivf | vector-diskann) and set `dimensions` to exactly match your chosen embedding model; create a standard filter index on any prefilter fields."
- **When:** 2026-11-25T11:45:11+00:00

## D006 (build): I chose to store embeddings directly on documents in DocumentDB as a number[] field named 'embedding' and create an HNSW vector index on that field.

- **Instead of:** Store embeddings as float[] and create DocumentDB vector index; Use external vector DB like FAISS
- **Because:** Matches Azure DocumentDB vector search requirements and keeps the sample focused on using DocumentDB as the vector store.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness instructions: "Vectors must be a `number[]` to be indexed" and vector index examples use a path to a property containing the vector.
- **When:** 2026-11-25T11:45:14+00:00

## D007 (build): I chose to read the DOCUMENTDB_URI connection string from environment variables at runtime and use it for SCRAM or SRV connection; do not embed secrets in code.

- **Instead of:** Use Azure AD / MONGODB-OIDC passwordless auth; Use connection string with SCRAM credentials
- **Because:** Follows the run environment instructions and avoids storing secrets.
- **Reason came from:** `prompt`
- **Evidence:** Run environment: "connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time. Never write its value into any file".
- **When:** 2026-11-25T11:45:18+00:00

## D008 (build): I chose HNSW (vector-hnsw) for the sample vector index.

- **Instead of:** IVF index; HNSW index; DiskANN index
- **Because:** HNSW offers good balance of speed/recall for demo datasets and is straightforward to configure for a small sample. It is recommended for many demo scenarios.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness guidance: "HNSW is supported; to perform vector search use $search cosmosSearch with efSearch parameter".
- **When:** 2026-11-25T11:45:20+00:00

## D009 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T11:47:13+00:00

## D010 (build): I chose Python 3.13 as the language/runtime for the sample (use system python/venv).

- **Instead of:** Use Node.js; Use Python 3.13 virtualenv
- **Because:** The run environment provides Python 3.13 and pip; the sample and LlamaIndex code are commonly written in Python.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: "Python 3.13.13 on PATH" and skill_md run environment notes.
- **When:** 2026-11-25T11:47:42+00:00

## D011 (build): I chose a single collection 'kb_documents' with schema {_id, type, title, content, embedding, metadata, created_at}.

- **Instead of:** Use separate collection per doc type; Use a single collection named 'kb_documents'
- **Because:** Simpler for a sample and matches README; no sharding required for the demo.
- **Reason came from:** `prompt`
- **Evidence:** Assumptions from prompt review suggested a single collection; sample README previously mentions `kb_documents`.
- **When:** 2026-11-25T11:47:44+00:00

## D012 (build): I chose OpenAI as the default provider for embeddings and LLMs (models: text-embedding-3-small, gpt-4o-mini), reading keys from OPENAI_API_KEY / OPENAI_API_BASE env vars. If not present, the sample falls back to deterministic pseudo-embeddings and a template response.

- **Instead of:** Use OpenAI embeddings + OpenAI chat; Use local pseudo-embeddings and template responses
- **Because:** OpenAI is commonly available; text-embedding-3-small produces 1536-d embeddings which matches vector index dimension guidance; fallback keeps the sample runnable without secrets.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report noted missing embedding/LLM choice and suggested defaults; .env.example includes OPENAI_* variables and models.
- **When:** 2026-11-25T11:47:47+00:00

## D013 (build): I chose to create sample documents via seed.py and create the vector index separately using the documentdb MCP server in the verification step (so seed stays idempotent and simple).

- **Instead of:** Create vector index via pymongo createIndexes in seed.py; Create vector index via documentdb MCP server createIndex tool during verification
- **Because:** The MCP tool provides the right semantics for vector index creation; doing it as a separate explicit step keeps seed.py simple and ensures index options are correctly applied.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: MCP server available with documentdb_create_index and guidance that vector indexes are created with createIndexes + cosmosSearch options.
- **When:** 2026-11-25T11:47:50+00:00

## D014 (build): I chose an HNSW vector index for the sample (good for up to ~50k vectors) with dimensions=1536 to match text-embedding-3-small.

- **Instead of:** HNSW; DiskANN; IVF
- **Because:** Sample is small (<=200 docs), HNSW is simple and supported and matches the sample scale; 1536 dims matches text-embedding-3-small.
- **Reason came from:** `readiness_report`
- **Evidence:** documentdb-vector-search guidance: 'Prefer DiskANN for production; use HNSW up to 50k' and embedding dimension must match model.
- **When:** 2026-11-25T11:48:20+00:00

## D015 (build): I chose pinned dependency versions in requirements.txt to improve reproducibility (pins for pymongo, Flask, python-dotenv, openai, llama-index).

- **Instead of:** Use latest unpinned dependencies; Pin specific tested versions
- **Because:** Pinned versions avoid surprising incompatibilities during pip install in the sample run environment.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report noted missing pinned dependency set and recommended choosing one.
- **When:** 2026-11-25T11:48:25+00:00

## D016 (build): I chose the pinned versions in requirements.txt: pymongo==4.5.1, Flask==2.3.2, python-dotenv==1.0.0, openai==0.28.1, llama-index==0.9.2, requests==2.31.0.

- **Instead of:** Use latest packages; Use pinned versions in requirements.txt (pymongo==4.5.1, Flask==2.3.2, python-dotenv==1.0.0, openai==0.28.1, llama-index==0.9.2)
- **Because:** Pinned versions reduce the chance of incompatibilities during installation and verification in this run environment.
- **Reason came from:** `model_default`
- **Evidence:** I added requirements.txt to the workspace with these versions.
- **When:** 2026-11-25T11:49:13+00:00

## D017 (build): I chose to use pymongo==4.5.0 instead of 4.5.1 to match available PyPI versions in this environment.

- **Instead of:** Keep pymongo==4.5.1 and fail; Use pymongo==4.5.0 which exists
- **Because:** Use a nearby available version to allow installation to proceed.
- **Reason came from:** `tool_result`
- **Evidence:** pip install reported pymongo==4.5.1 not found but 4.5.0 is in available versions.
- **When:** 2026-11-25T11:49:22+00:00

## D018 (build): I chose to remove llama-index from requirements and use direct OpenAI API calls in the sample instead of LlamaIndex to avoid incompatible package versions in this Python 3.13 environment.

- **Instead of:** Keep llama-index in requirements; Remove llama-index and implement simple direct OpenAI calls
- **Because:** Using direct OpenAI calls keeps the sample simpler and avoids dependency/version conflicts while still demonstrating RAG flow.
- **Reason came from:** `tool_result`
- **Evidence:** pip install error showed no matching llama-index==0.9.2 and many versions have Python version constraints.
- **When:** 2026-11-25T11:49:33+00:00

## D019 (build): I chose to run seed.py to populate the sample documents into the live cluster defined by DOCUMENTDB_URI.

- **Instead of:** Don't run seed.py; Run seed.py to populate sample documents
- **Because:** Seeding is necessary to demonstrate retrieval and to verify vector search pipeline; seed.py is idempotent and inserts only into the sample database.
- **Reason came from:** `prompt`
- **Evidence:** README and skill_md require seeding the database; the run environment provides a reachable DocumentDB cluster in DOCUMENTDB_URI.
- **When:** 2026-11-25T11:49:47+00:00

## D020 (build): I chose to compute deterministic pseudo-embeddings locally to populate the 'embedding' field for seed documents (keeps sample runnable without OPENAI_API_KEY).

- **Instead of:** Compute embeddings via OpenAI; Compute deterministic pseudo-embeddings locally
- **Because:** Avoid requiring API key for initial verification; deterministic embeddings allow retrieval flow to be exercised.
- **Reason came from:** `model_default`
- **Evidence:** seed.py did not store embeddings; verify_retrieval failed because embedding arrays were missing. Pseudo-embeddings are deterministic and suitable for the sample/demo.
- **When:** 2026-11-25T11:50:43+00:00

## D021 (build): I chose to create the vector index using pymongo's database command createIndexes after the documentdb MCP tool's documentdb_create_index call failed.

- **Instead of:** Give up on creating vector index; Create vector index via pymongo createIndexes command
- **Because:** pymongo createIndexes accepts the required cosmosSearchOptions and succeeded, allowing the sample to be fully verified.
- **Reason came from:** `tool_result`
- **Evidence:** documentdb_create_index tool call returned an error; pymongo db.command({'createIndexes': ...}) returned ok:1 and created the index.
- **When:** 2026-11-25T11:52:49+00:00
