# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 12 |
| readiness_report | 10 |
| model_default | 5 |
| operator | 3 |
| tool_result | 2 |
| skill | 2 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T08:40:57+00:00

## D002 (build): I chose Python 3.11 for the sample runtime.

- **Instead of:** Use Node.js/TypeScript; Use Python 3.11
- **Because:** Python is the most common language for LlamaIndex and the environment already has Python; using 3.11 maximizes compatibility with modern libraries.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Use Python 3.10 (or 3.11) for the sample; ensure compatibility with latest LlamaIndex and pymongo driver.", and the readiness report shows Python available.
- **When:** 2026-11-25T08:41:15+00:00

## D003 (build): I chose pymongo (sync) pinned to pymongo>=4.4,<5.0 and a singleton MongoClient per process.

- **Instead of:** motor (async) MongoDB driver; pymongo (sync)
- **Because:** pymongo is the official driver and recommended by the documentdb-driver skill; a singleton client is best practice to avoid connection pool exhaustion.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Use pymongo as the MongoDB driver, pinned to a recent 4.x release compatible with MongoDB 7.0 (e.g. pymongo>=4.4,<5.0). Create a singleton MongoClient per process as recommended by documentdb-driver."
- **When:** 2026-11-25T08:41:18+00:00

## D004 (build): I chose OpenAI text-embedding-3-small as the embedding model with 1536 dimensions.

- **Instead of:** text-embedding-3-large (OpenAI); text-embedding-3-small (OpenAI); other provider
- **Because:** Provides a good balance of cost and quality; 1536 dims is widely supported and recommended in the assumptions.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: "Embedding model and dimensionality ... builder must pick a model..." and common choice text-embedding-3-small = 1536 dims.
- **When:** 2026-11-25T08:41:21+00:00

## D005 (build): I chose OpenAI (api.openai.com) as the LLM provider for LlamaIndex agent, configured via OPENAI_API_KEY.

- **Instead of:** Azure OpenAI; OpenAI (api.openai.com); local LLM
- **Because:** OpenAI is commonly used with LlamaIndex, and the environment can provide the API key via env vars; keeps sample simpler to run.
- **Reason came from:** `prompt`
- **Evidence:** Assumptions: "Use an OpenAI embedding model... expose API keys via environment variables (e.g., OPENAI_API_KEY)."
- **When:** 2026-11-25T08:41:29+00:00

## D006 (build): I chose a single collection named 'high_risk_profiles' with documents shaped { patient_id, features, embedding, risk_label, recommended_interventions } and embedding field named 'embedding'.

- **Instead of:** Store profiles in multiple collections; Use single collection 'high_risk_profiles'
- **Because:** Sufficient for demo, simple to query, consistent with skills guidance on embedding field naming.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Create a single collection named `high_risk_profiles` with documents like { patient_id, features: {...}, embedding: [float], risk_label, recommended_interventions }. Use embedding field name `embedding`."
- **When:** 2026-11-25T08:41:32+00:00

## D007 (build): I chose to use server-side DocumentDB vector search via the 'cosmosSearch' operator and create a vector index with dimensions 1536. If server-side vector index is unavailable, code will fall back to client-side cosine search (explicit fallback).

- **Instead of:** Create vector index server-side using DocumentDB 'cosmosSearch' APIs; Compute embeddings locally and build an in-memory ANN index
- **Because:** Server-side ANN provides better performance and is recommended; fallback included for safety.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report guidance: "Create vector indexes using the DocumentDB 'cosmosSearch' vector-index APIs ... set the index 'dimensions' to match your chosen embedding model; prefer server-side vector retrieval via $search/cosmosSearch."
- **When:** 2026-11-25T08:41:35+00:00

## D008 (build): I chose to install dependencies via pip (pip install -r requirements.txt) before running tests.

- **Instead of:** Skip installing dependencies and run tests (likely to fail); Install Python deps via pip install -r requirements.txt
- **Because:** Tests and sample need external libraries (pytest, llama-index, openai, pymongo); installing them is necessary to run verification steps.
- **Reason came from:** `tool_result`
- **Evidence:** pytest was not found when attempting to run tests; requirements.txt lists pytest and other libs.
- **When:** 2026-11-25T08:42:47+00:00

## D009 (build): I chose to use the documentdb MCP server tools to inspect and create collection/index metadata on the live cluster.

- **Instead of:** Inspect cluster using pymongo direct calls; Use documentdb MCP server tools to inspect collections and indexes
- **Because:** MCP tool provides data-plane operations and explain plans tailored for DocumentDB vector indexes and is the recommended verification path in the readiness report.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: "the `documentdb` MCP server's connection profile `default` is connected to that same cluster. Use its tools to inspect collections, indexes and query plans and to verify what the app created."
- **When:** 2026-11-25T08:45:44+00:00

## D010 (build): I chose to create a server-side vector index named 'high_risk_embedding_diskann' on sample_healthcare_13.high_risk_profiles using cosmosSearch vector-diskann with dimensions=1536 and similarity='COS', maxDegree=32, lBuild=50.

- **Because:** Server-side DiskANN is recommended for production-scale vectors and the sample uses OpenAI text-embedding-3-small (1536 dims). Creating the index enables server-side ANN queries.
- **Reason came from:** `skill`
- **Evidence:** documentdb-vector-search skill resource 'vector-create-diskann-index.md' and readiness report guidance to use cosmosSearch and match dimensions to embedding model.
- **When:** 2026-11-25T08:46:24+00:00

## D011 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T08:48:07+00:00

## D012 (build): I chose Python 3.10+ (use system 'python') for the sample.

- **Instead of:** Node.js/TypeScript; Python 3.10/3.11/3.12
- **Because:** Python is requested in the prompt and the run environment supplies Python; LlamaIndex is Python-native and ecosystem libraries (pymongo, openai) are Python packages.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Use Python 3.10 (or 3.11) for the sample; ensure compatibility with latest LlamaIndex and pymongo driver."
- **When:** 2026-11-25T08:48:28+00:00

## D013 (build): I chose pymongo (>=4.4,<5.0) and will use a singleton MongoClient per process.

- **Instead of:** motor async driver; pymongo 4.x
- **Because:** pymongo is the standard MongoDB driver for Python and matches the installed DocumentDB skills guidance about a singleton client.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Use pymongo as the MongoDB driver, pinned to a recent 4.x release compatible with MongoDB 7.0 (e.g. pymongo>=4.4,<5.0). Create a singleton MongoClient per process as recommended by documentdb-driver."
- **When:** 2026-11-25T08:48:31+00:00

## D014 (build): I chose OpenAI text-embedding-3-small with 1536 dimensions for embeddings.

- **Instead of:** OpenAI text-embedding-3-small (1536d); OpenAI text-embedding-3-large (3072d); Azure OpenAI embeddings
- **Because:** 1536 dims is a reasonable tradeoff between quality and storage/compute cost and is commonly available; DocumentDB vector index dimensions will be set to 1536 accordingly.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'Use an OpenAI embedding model (e.g., text-embedding-3-small, 1536 dims)'.
- **When:** 2026-11-25T08:48:37+00:00

## D015 (build): I chose OpenAI (REST API) as the LLM/Embedding provider, keys via OPENAI_API_KEY env var.

- **Instead of:** Azure OpenAI; OpenAI REST API; Local LLM
- **Because:** OpenAI is well-supported by LlamaIndex examples; making the provider configurable via env keeps the sample simple and flexible.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use an OpenAI embedding model ... expose API keys via environment variables (e.g., OPENAI_API_KEY).'
- **When:** 2026-11-25T08:48:42+00:00

## D016 (build): I chose FastAPI for the HTTP API.

- **Instead of:** Flask; FastAPI
- **Because:** FastAPI provides a modern, async-friendly API surface and integrates well with Uvicorn for local testing; it's concise for examples.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Provide a small Flask (or FastAPI) HTTP API with a /predict endpoint.'
- **When:** 2026-11-25T08:48:45+00:00

## D017 (build): I chose to create a server-side cosmosSearch vector index on the collection using the documentdb MCP server (documentdb_create_index) / createIndexes command with cosmosSearchOptions.

- **Instead of:** Create vector index client-side (ANN library); Create server-side vector index with DocumentDB cosmosSearch
- **Because:** Server-side vector index provides efficient, scalable ANN search and matches DocumentDB best-practices; using the MCP tool lets us verify index creation programmatically.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report guidance: 'Create vector indexes using the DocumentDB "cosmosSearch" vector-index APIs ... set the index "dimensions" to match your chosen embedding model; do not use a hypothetical knnVector createIndex shape.'
- **When:** 2026-11-25T08:48:56+00:00

## D018 (build): I chose the lightweight OpenAI ChatCompletion prompt for narrative generation instead of deep LlamaIndex integration.

- **Instead of:** Use full LlamaIndex integration (GPTVectorStoreIndex, LLMPredictor); Use a lightweight OpenAI ChatCompletion prompt for narrative generation
- **Because:** Simpler, reduces dependency surface and avoids failing imports during tests; behavior remains representative of agent reasoning for this sample. The code still uses LlamaIndex-related package in requirements for users who want deeper integration.
- **Reason came from:** `tool_result`
- **Evidence:** ImportError during tests: 'cannot import name LLMPredictor from llama_index' and the readiness report noted no turnkey LlamaIndex->DocumentDB retriever mapping.
- **When:** 2026-11-25T08:49:58+00:00

## D019 (build): I used the documentdb MCP tool documentdb_create_index to create the cosmosSearch vector index on the collection.

- **Instead of:** Create vector index via pymongo db.command(createIndexes); Use documentdb MCP tool documentdb_create_index
- **Because:** The MCP tool provides a programmatic, verified way to create the DocumentDB-specific vector index and to inspect it afterward. It avoids driver-level compatibility issues.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report guidance: 'Create vector indexes using the DocumentDB "cosmosSearch" vector-index APIs (createIndexes with cosmosSearchOptions)...'
- **When:** 2026-11-25T08:51:59+00:00

## D020 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T08:55:22+00:00

## D021 (build): I chose Python 3.13 (use system python available on PATH) for development and runtime.

- **Instead of:** Python 3.10; Python 3.11; Python 3.13
- **Because:** Runtime on the build machine provides Python 3.13; it is backwards-compatible with libraries targeted at 3.10–3.11 and avoids needing to install another interpreter.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: "Python 3.13.13 is on PATH (inventory)."
- **When:** 2026-11-25T08:55:50+00:00

## D022 (build): I chose pymongo >=4.4,<5.0 and will use PyMongo's (sync) MongoClient as a singleton.

- **Instead of:** pymongo 3.x; pymongo >=4.4,<5.0; motor async client
- **Because:** PyMongo 4.x supports MongoDB 7.0 and the documentdb-connection skill recommends PyMongo; using a singleton MongoClient follows the documentdb-driver guidance.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Use pymongo as the MongoDB driver, pinned to a recent 4.x release compatible with MongoDB 7.0 (e.g. pymongo>=4.4,<5.0)."
- **When:** 2026-11-25T08:55:53+00:00

## D023 (build): I chose OpenAI text-embedding-3-small with 1536 dimensions for embeddings.

- **Instead of:** Embed model unspecified; OpenAI text-embedding-3-small (1536d); OpenAI ada (legacy)
- **Because:** 1536-d embeddings are a common choice (text-embedding-3-small), balance size and quality, and match DocumentDB vector-index dimension examples in guidance.
- **Reason came from:** `prompt`
- **Evidence:** Assumptions from prompt review: "Use an OpenAI embedding model (e.g., text-embedding-3-small, 1536 dims)" and readiness_report information_gaps about model choice.
- **When:** 2026-11-25T08:56:00+00:00

## D024 (build): I chose OpenAI (api.openai.com) for the LLM provider, configurable via OPENAI_API_KEY.

- **Instead of:** Azure OpenAI; OpenAI (api.openai.com); Local LLM
- **Because:** OpenAI is widely available, supported by LlamaIndex, and straightforward for a sample; code will gracefully fall back to a deterministic template if no API key is present to allow offline runs.
- **Reason came from:** `model_default`
- **Evidence:** Assumption: no provider specified; common and simple option is OpenAI and LlamaIndex supports it. Readiness report: LLM provider unspecified.
- **When:** 2026-11-25T08:56:03+00:00

## D025 (build): I chose FastAPI for the HTTP API surface (uvicorn-runable).

- **Instead of:** Flask; FastAPI
- **Because:** FastAPI provides easy async endpoints, automatic OpenAPI docs, and works well with uvicorn used in tests and examples.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: "Provide a small Flask (or FastAPI) HTTP API".
- **When:** 2026-11-25T08:56:06+00:00

## D026 (build): I chose server-side vector retrieval via DocumentDB $search (cosmosSearch) and will implement a server-side aggregator pipeline; client-side ANN fallback will be available when DOCUMENTDB_URI is not set or vector index missing.

- **Instead of:** Server-side vector retrieval via $search; Client-side ANN fallback
- **Because:** Server-side retrieval is more efficient and matches DocumentDB capabilities; fallback allows development without a configured vector index or API key.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report guidance: "Prefer server-side vector retrieval via $search/cosmosSearch when the vector index is present; implement a fallback ANN client-side only if server-side indexing is not available".
- **When:** 2026-11-25T08:56:09+00:00

## D027 (build): I chose not to provision Azure resources; the sample will use the existing cluster referenced by DOCUMENTDB_URI.

- **Instead of:** Create cluster via az or Bicep; Do not provision resources (use existing cluster)
- **Because:** The environment already provides a reachable cluster and run policy forbids provisioning; samples should not change infra.
- **Reason came from:** `readiness_report`
- **Evidence:** Run environment: "A vector-capable Azure DocumentDB cluster ... connection string is in the environment variable DOCUMENTDB_URI." Also run_policy disallows Azure resource changes.
- **When:** 2026-11-25T08:56:23+00:00

## D028 (build): I chose a single collection named `high_risk_profiles` with documents: { patient_id, features, embedding, risk_label, recommended_interventions }

- **Instead of:** Multiple collections per cohort; Single collection `high_risk_profiles`
- **Because:** Keeps the sample simple and demonstrates vector search+metadata filtering; matches skills guidance on data modelling.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Create a single collection named `high_risk_profiles` with documents like { patient_id, features: {...}, embedding: [float], risk_label, recommended_interventions }."
- **When:** 2026-11-25T08:56:26+00:00

## D029 (build): I chose `vector-diskann` index subtype with similarity COS (cosine) and dimensions 1536.

- **Instead of:** vector-hnsw; vector-diskann; vector-ivf
- **Because:** DiskANN scales well and matches readiness_report note that the live cluster supports DiskANN/HNSW/IVF; cosine similarity recommended for normalized embeddings.
- **Reason came from:** `skill`
- **Evidence:** documentdb-vector-search skill: "Prefer DiskANN for production; create a `vector-diskann` index with correct `dimensions` and `similarity`."
- **When:** 2026-11-25T08:56:32+00:00

## D030 (build): I chose to generate 200 synthetic high-risk profiles by default in the seed script (configurable via SEED_COUNT env var).

- **Instead of:** Seed size 10–50; Seed size 100–500; Seed size 1000+
- **Because:** 200 is in the suggested range, sufficient to demonstrate retrieval and performance without being large to seed quickly in CI.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Provide a seed script that generates synthetic high-risk profiles (e.g., 100–500 records)".
- **When:** 2026-11-25T08:56:35+00:00

## D031 (build): I chose to use OpenAI embeddings when OPENAI_API_KEY is present; otherwise generate random normalized embeddings for offline runs.

- **Instead of:** Use OpenAI for embeddings always; Use OpenAI if key present else random embeddings (fallback)
- **Because:** Allows both realistic embedding use in live runs and reproducible offline testing for CI without storing secrets.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: embedding model unspecified and suggestion to allow fallback; also sample must be runnable without external API keys for tests.
- **When:** 2026-11-25T08:56:37+00:00

## D032 (build): I chose to integrate LlamaIndex as an optional component: when OPENAI_API_KEY is present, use OpenAI chat via LlamaIndex to generate the personalised narrative; otherwise produce a deterministic template combining retrieved profiles.

- **Instead of:** Use LlamaIndex-only agent; Use LlamaIndex with OpenAI chat model, fallback to template when no key
- **Because:** Keeps sample faithful to prompt while allowing runs/tests without external LLM calls; documents configuration in README.
- **Reason came from:** `model_default`
- **Evidence:** Assumptions: LlamaIndex requested by prompt but LLM provider unspecified; need graceful offline fallback.
- **When:** 2026-11-25T08:56:41+00:00

## D033 (build): I chose the API response to return the generated risk narrative plus the top-k retrieved profiles and their similarity scores.

- **Instead of:** Return narrative only; Return narrative + retrieved profiles + similarity scores
- **Because:** Helps developers inspect why the agent made recommendations and validates retrieval correctness.
- **Reason came from:** `model_default`
- **Evidence:** Information_gap: "Response schema and similarity scores not specified" — returning both is more useful for a demo and shows vector search results.
- **When:** 2026-11-25T08:56:43+00:00

## D034 (build): I chose to run the seed script against the live cluster (it will upsert synthetic profiles into high_risk_profiles).

- **Instead of:** Don't run seed script on live cluster; Run seed script on live cluster (will upsert into collection)
- **Because:** Demonstrates end-to-end insertion and populates documents for retrieval; seed script is idempotent (upserts) and uses synthetic data only.
- **Reason came from:** `readiness_report`
- **Evidence:** Run environment: "The starter environment is a developer machine where an Azure DocumentDB cluster is already provisioned and reachable... DOCUMENTDB_URI set."
- **When:** 2026-11-25T08:59:25+00:00
