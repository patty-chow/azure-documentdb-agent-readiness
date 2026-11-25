# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 5 |
| prompt | 3 |
| operator | 1 |
| skill | 1 |
| readiness_report | 1 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T09:03:12+00:00

## D002 (build): I chose Python (system 'python' in the dev virtualenv) for the sample app and scripts.

- **Instead of:** Use Node.js/JavaScript; Use Python
- **Because:** The user explicitly requested a Python LlamaIndex pipeline and the run environment provides Python and pip.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt review: 'Use Python 3.10 (or the system `python` which is a dev virtualenv)'; and the sample prompt asked for a Python LlamaIndex pipeline.
- **When:** 2026-11-25T09:04:07+00:00

## D003 (build): I chose PyMongo (pymongo >= 4.5) and will implement a singleton MongoClient for the sample.

- **Instead of:** Use a MongoDB wrapper for LlamaIndex if available; Use PyMongo (pymongo >= 4.5) and manage vector storage directly
- **Because:** Direct control over vector uploads and $search queries is needed to create the DocumentDB vector index and issue cosmosSearch queries; PyMongo gives precise control and follows documentdb-driver/connection guidance.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Prefer using LlamaIndex's built-in Azure/Mongo vector store if available; otherwise use PyMongo (pymongo >= 4.5) and the official MongoDB Python driver.'
- **When:** 2026-11-25T09:04:10+00:00

## D004 (build): I chose OpenAI text-embedding-3-small for embeddings and will require OPENAI_API_KEY in env.

- **Instead of:** Use OpenAI text-embedding-3-small; Use another provider such as HuggingFace models
- **Because:** OpenAI embeddings are commonly used, integrate with LlamaIndex easily, and are convenient for a small sample; selecting text-embedding-3-small balances cost and quality for abstracts.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Use a commonly used embedding provider such as OpenAI... require OPENAI_API_KEY'.
- **When:** 2026-11-25T09:04:18+00:00

## D005 (build): I chose OpenAI gpt-3.5-turbo for the answer-generation LLM.

- **Instead of:** Use gpt-4o for answers; Use gpt-3.5-turbo for answers
- **Because:** gpt-3.5-turbo is broadly available and adequate for a sample; it reduces cost for CI and demo runs while still producing good quality answers.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'use an LLM for the generation step (e.g., OpenAI GPT-4o/3.5)'.
- **When:** 2026-11-25T09:04:20+00:00

## D006 (build): I chose a single denormalized collection 'pubmed_chunks' in database 'sample_healthcare_17' with documents { _id, pmid, year, chunk_id, text, embedding, model, schemaVersion }.

- **Instead of:** Store chunks and metadata in separate collections; Use a single denormalized collection 'pubmed_chunks' with embedded vectors
- **Because:** Simplicity for the sample and to follow the prompt review's suggested data model; it simplifies retrieval and vector indexing for cosmosSearch.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Create a collection named `pubmed_chunks` ... denormalized chunks (embed) rather than separate chunk and metadata collections.'
- **When:** 2026-11-25T09:04:25+00:00

## D007 (build): I chose vector-diskann (DiskANN) for the vector index.

- **Instead of:** vector-hnsw (HNSW); vector-diskann (DiskANN)
- **Because:** DiskANN is the recommended default for production and suits the provided M30 cluster; it supports cosine similarity and high vector counts.
- **Reason came from:** `skill`
- **Evidence:** documentdb-vector-search skill recommends DiskANN for larger sets and the readiness report indicated DiskANN is supported on M30 clusters.
- **When:** 2026-11-25T09:04:33+00:00

## D008 (build): I chose to require 'llama-index>=0.9.0' in requirements.txt rather than pinning to a single patch version.

- **Instead of:** Pin llama-index to an exact version (e.g., 0.9.x); Allow a flexible requirement 'llama-index>=0.9.0'
- **Because:** Using a minimum compatible version preserves flexibility while keeping the package recent enough to support TokenTextSplitter and OpenAI embeddings; exact pins can be adjusted later by maintainers.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report noted lack of exact LlamaIndex version guidance; the prompt review flagged this as a gap.
- **When:** 2026-11-25T09:04:38+00:00

## D009 (build): I chose FastAPI for the HTTP API (POST /query).

- **Instead of:** FastAPI; Flask
- **Because:** FastAPI provides async support, automatic docs, and is popular for Python APIs; it integrates well with uvicorn for local runs.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Expose a simple HTTP API (Flask or FastAPI)'.
- **When:** 2026-11-25T09:04:42+00:00

## D010 (build): I chose to insert a few dummy documents with zero vectors for verification instead of running the full OpenAI-backed seed, to avoid requiring an OPENAI_API_KEY during automated verification.

- **Instead of:** Run the full seed that calls OpenAI embeddings (requires OPENAI_API_KEY); Insert a small set of dummy documents with random/zero embeddings for verification without external API calls
- **Because:** This lets us verify collection creation, index creation, and $search behavior (score metadata) without relying on external API keys during the build run. We will document how to run the full seed with OpenAI in the README.
- **Reason came from:** `model_default`
- **Evidence:** Run environment may not have OPENAI_API_KEY set; the readiness report noted embedding-provider choice gap and tests should mock embedding calls.
- **When:** 2026-11-25T09:06:33+00:00

## D011 (build): I chose to use the documentdb MCP server's documentdb_create_index tool to create the cosmosSearch vector-diskann index for verification.

- **Instead of:** Create index via PyMongo runCommand; Use the documentdb MCP server documentdb_create_index tool
- **Because:** Using the MCP server gives a standardized, auditable way to create the DocumentDB-specific cosmosSearch index options for DiskANN that may not be supported by vanilla PyMongo wrappers.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'documentdb MCP server present and responsive; offers data-plane tools (create/index)'.
- **When:** 2026-11-25T09:06:41+00:00

## D012 (build): I chose to fallback to PyMongo db.command(createIndexes) because the MCP documentdb_create_index call failed.

- **Instead of:** Retry documentdb_create_index MCP call; Fallback to PyMongo db.command(createIndexes)
- **Because:** Direct runCommand via the driver is a supported alternative and allows us to create the cosmosSearchOptions index; it works even if the MCP tool had transient issues.
- **Reason came from:** `tool_result`
- **Evidence:** The MCP call returned 'Error: Function failed.' when attempting to create the index.
- **When:** 2026-11-25T09:06:48+00:00
