# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 11 |
| model_default | 7 |
| readiness_report | 5 |
| skill | 5 |
| operator | 4 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T12:18:27+00:00

## D002 (build): I chose Python 3.x (use the system 'python' which resolves to a virtualenv) with pymongo and LangChain for orchestration.

- **Instead of:** Node.js/TypeScript; Python 3.11
- **Because:** The prompt requested a Python LangChain orchestration pipeline; Python is the natural choice and the run environment already provides python/pip in a virtualenv.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Builder will target a recent Python 3.x LTS (likely 3.10 or 3.11) via a virtualenv; use `python`/`pip` from that venv (skill_md says `python`/`pip` resolve to a virtual environment).
- **When:** 2026-11-25T12:18:45+00:00

## D003 (build): I chose to use pymongo as the MongoDB driver and LangChain with an OpenAI-compatible provider for LLM-assisted matching and embeddings.

- **Instead of:** pymongo standalone without LangChain; pymongo + LangChain + OpenAI embeddings
- **Because:** LangChain simplifies LLM orchestration and is commonly used; pymongo is the supported MongoDB driver and recommended by the documentdb-driver skill.
- **Reason came from:** `prompt`
- **Evidence:** Skills: documentdb-driver recommends singleton MongoClient; prompt asked for LangChain orchestration with LLM-assisted matching.
- **When:** 2026-11-25T12:18:48+00:00

## D004 (build): I chose a two-collection model: 'staging_customers' for raw ingest and 'customers' for normalized canonical profiles, plus 'workflows' for run metadata.

- **Instead of:** Separate collections for staging and customers; Single collection with workflow flags
- **Because:** This keeps seed idempotent and separates raw inputs from canonical profiles, making dedup/merge simpler to demonstrate.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Builder will create one primary collection (e.g. `customers`)...'; also common ETL patterns use staging.
- **When:** 2026-11-25T12:19:01+00:00

## D005 (build): I chose OpenAI 'text-embedding-3-small' (1536 dims) for embeddings and normalized cosine similarity; the embedding DIM will be 1536 and stored on each document as 'embedding'.

- **Instead of:** text-embedding-3-small (1536 dims); other embedding model
- **Because:** Provides good quality and is commonly available for demos; vector-search skill recommends documenting dims and normalizing embeddings for cosine.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: recommended 'text-embedding-3-small' as reasonable default and information gap noted about embedding dimensions.
- **When:** 2026-11-25T12:19:03+00:00

## D006 (build): I chose to create a textSearch index on 'normalized_name' and a hashed index on 'email'. I will attempt to create a vector index (vector-diskann) for the 'embedding' field using the documentdb_create_index MCP tool; if the tool call fails in this environment I will still proceed and document the failure in the build report.

- **Instead of:** Create vector index (DiskANN); Skip vector index
- **Because:** Text and hashed indexes support dedupe lookups; vector index enables semantic matching and enrichment vectors. Creating the vector index via MCP is the recommended data-plane way; failure would be logged.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report guidance: 'Enable and demonstrate native vector search and hybrid $search usage... create a vector index (vector-diskann / vector-hnsw / vector-ivf)'.
- **When:** 2026-11-25T12:19:07+00:00

## D007 (build): I chose to implement a runtime fallback: if OPENAI_API_KEY (or equivalent LangChain provider config) is not present, the dedup agent will use a deterministic heuristic (email equality + normalized name equality) and skip LLM calls. This keeps the sample runnable without LLM keys while still demonstrating LLM integration when keys are provided.

- **Instead of:** Require OPENAI_API_KEY and fail if missing; Fallback to heuristic dedupe when OPENAI_API_KEY missing
- **Because:** To ensure the sample runs in environments without LLM credentials and to respect secret-handling rules.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Model credentials will be read from environment variables (e.g. OPENAI_API_KEY).' The run environment may or may not have keys available.
- **When:** 2026-11-25T12:19:10+00:00

## D008 (build): I chose to create the basic indexes (hashed on email and text on normalized_name) via a small pymongo script (ensure_indexes.py) rather than attempting complex vector index creation via the MCP tool in this run. I'll still attempt a vector index creation via the documentdb_create_index MCP tool afterwards and record any failures.

- **Instead of:** Create indexes via MCP documentdb_create_index; Create indexes via pymongo in-sample script
- **Because:** Pymongo create_index is straightforward and will succeed for hashed and text indexes; MCP can be used as a second step for vector index where supported and verified.
- **Reason came from:** `model_default`
- **Evidence:** documentdb-indexing skill suggests creating indexes; pymongo create_index is reliable for single-field and text indexes. The MCP vector index parameters are more specialized and may fail in this environment.
- **When:** 2026-11-25T12:20:00+00:00

## D009 (build): I chose to pin langchain to a PyPI-available version 0.0.341 to allow pip install to succeed in this environment.

- **Instead of:** Keep langchain==0.0.375 and fail; Use a stable available langchain version from PyPI
- **Because:** Install must succeed; 0.0.341 is present in the pip index per the install error output listing available versions.
- **Reason came from:** `tool_result`
- **Evidence:** pip error: 'No matching distribution found for langchain==0.0.375' from the previous pip install attempt.
- **When:** 2026-11-25T12:20:14+00:00

## D010 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T12:22:16+00:00

## D011 (build): I chose Python 3 (use the existing virtualenv 'python'/'pip') for the sample app and scripts.

- **Instead of:** Node.js/TypeScript; Python 3.11; Go; C#
- **Because:** The prompt requested a Python LangChain orchestration pipeline; Python is the natural runtime for LangChain and the environment already provides python/pip.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Builder will target a recent Python 3.x LTS... use `python`/`pip` from that venv' and the run environment states python and pip resolve to a virtual environment.
- **When:** 2026-11-25T12:22:38+00:00

## D012 (build): I chose OpenAI-compatible models accessed via LangChain (OPENAI_API_KEY env var) for LLM and embeddings.

- **Instead of:** OpenAI (openai.com); Azure OpenAI; local LLM (llama); Anthropic
- **Because:** OpenAI is widely available, LangChain has first-class support, and the environment convention in the prompt suggests OPENAI_API_KEY. This simplifies the sample and tests (mockable).
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Builder will integrate a LangChain-compatible LLM provider (commonly OpenAI) ... Model credentials will be read from environment variables (e.g. OPENAI_API_KEY).'
- **When:** 2026-11-25T12:22:40+00:00

## D013 (build): I chose text-embedding-3-small with 1536 dimensions for embeddings.

- **Instead of:** text-embedding-3-small (1536); text-embedding-3-large (3072); openai-ada-embeddings (unknown dims)
- **Because:** This is a good trade-off for demo-sized datasets and matches commonly available embedding models; vector-index parameters and storage are chosen accordingly.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt_review: 'Reasonable defaults: an OpenAI-compatible chat model for LLM-assisted matching and `text-embedding-3-small` or similar for embeddings (e.g. 1536 dims).'
- **When:** 2026-11-25T12:22:44+00:00

## D014 (build): I chose pymongo (synchronous) as the MongoDB driver and will follow the singleton MongoClient pattern.

- **Instead of:** pymongo; motor (async); mongodb+driver via mongoengine
- **Because:** pymongo is the standard MongoDB driver for Python, simple for a small sample and compatible with synchronous scripts and tests.
- **Reason came from:** `skill`
- **Evidence:** documentdb-driver skill: 'Reuse MongoClient as a process-wide singleton.'
- **When:** 2026-11-25T12:22:47+00:00

## D015 (build): I chose to use the existing cluster referenced by DOCUMENTDB_URI (do not provision any Azure resources).

- **Instead of:** Create cluster via IaC (Bicep/Terraform); Provision nothing and use existing cluster DOCUMENTDB_URI
- **Because:** The environment already provides a reachable cluster and run_policy forbids creating Azure resources; using the existing cluster aligns with these constraints.
- **Reason came from:** `readiness_report`
- **Evidence:** Run environment: 'A vector-capable Azure DocumentDB cluster ... connection string is in DOCUMENTDB_URI' and run_policy forbids Azure resource changes.
- **When:** 2026-11-25T12:22:52+00:00

## D016 (build): I chose vector-hnsw for the sample vector index (suitable for up to ~50k demo vectors) and will set dimensions=1536 and similarity='COS'.

- **Instead of:** Use diskann vector index; Use hnsw vector index; Use ivf vector index
- **Because:** HNSW is a good demo choice for small datasets and supported by the cluster; cosine similarity requires normalized embeddings and is common for semantic search.
- **Reason came from:** `skill`
- **Evidence:** documentdb-vector-search skill: 'vector-hnsw is suitable up to ~50k vectors' and earlier decision to use 1536-dim embeddings.
- **When:** 2026-11-25T12:22:55+00:00

## D017 (build): I chose to store normalized embedding vectors on each customer document in the 'embedding' field (list of floats) and also record 'embedding_model' and 'embedding_dims' metadata.

- **Instead of:** Per-collection embedding field named 'embedding' and store normalized vectors; Store embeddings in separate collection; Don't store embeddings
- **Because:** Storing vectors per-document simplifies per-profile vector search and aligns with vector-search skill guidance.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report guidance: 'Normalize embeddings when using cosine similarity; store model + dimensions alongside vectors.'
- **When:** 2026-11-25T12:22:59+00:00

## D018 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T12:27:08+00:00

## D019 (build): I chose Python 3 (use the existing virtualenv via `python`/`pip`) and will target a recent 3.x runtime as available on PATH (the environment's `python`), using a venv-managed workflow.

- **Instead of:** Node.js/TypeScript; Python 3.10/3.11
- **Because:** The sample and LangChain ecosystem are simplest in Python; prompt requested a Python LangChain orchestration pipeline.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt_review: 'Builder will target a recent Python 3.x LTS... use `python`/`pip` from that venv (skill_md says `python`/`pip` resolve to a virtual environment).
- **When:** 2026-11-25T12:27:36+00:00

## D020 (build): I chose OpenAI (OPENAI_API_KEY) as the LLM provider and LangChain's ChatOpenAI for LLM-assisted matching, with environment-variable configuration.

- **Instead of:** OpenAI (openai); Azure OpenAI; local LLM
- **Because:** OpenAI is the common default and works with LangChain; reading API key from env avoids storing secrets.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt_review: 'Builder will integrate a LangChain-compatible LLM provider (commonly OpenAI)'.
- **When:** 2026-11-25T12:27:50+00:00

## D021 (build): I chose text-embedding-3-small (1536 dims) as the embedding model and set embedding dimensionality to 1536.

- **Instead of:** text-embedding-3-small (1536 dims); text-embedding-ada-002 (1536?); other
- **Because:** This is a reasonable, modern OpenAI embedding model and matches vector-index expectations; it keeps vector sizes moderate for a demo.
- **Reason came from:** `model_default`
- **Evidence:** Prompt_review suggested 'text-embedding-3-small' and typical dims ~1536.
- **When:** 2026-11-25T12:27:59+00:00

## D022 (build): I chose the singleton MongoClient pattern (I chose a single MongoClient instance reused across the app).

- **Instead of:** MongoClient per-request; Singleton MongoClient pattern
- **Because:** Best practice to avoid connection-pool exhaustion and follow the documentdb-driver guidance.
- **Reason came from:** `skill`
- **Evidence:** documentdb-driver skill: 'Reuse `MongoClient` as a process-wide singleton; never create a new client per request.'
- **When:** 2026-11-25T12:28:11+00:00

## D023 (build): I chose vector-hnsw for the demo vector index.

- **Instead of:** vector-diskann; vector-hnsw; vector-ivf
- **Because:** Small sample dataset fits HNSW and it's easier for demos.
- **Reason came from:** `skill`
- **Evidence:** documentdb-vector-search skill: 'vector-hnsw: Up to ~50k vectors; use HNSW up to 50k.'
- **When:** 2026-11-25T12:28:19+00:00

## D024 (build): I chose a single 'customers' collection with embedded arrays/objects for addresses and firmographics.

- **Instead of:** Separate collections for addresses/firmographics; Single customers collection with embedded fields
- **Because:** Embedding simplifies read queries for customer 360, follows documentdb-data-modeling guidance for read-heavy profiles and keeps the sample simple.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt_review: 'Builder will create one primary collection (e.g. `customers`) ... Documents will include ... addresses array, firmographics object.'
- **When:** 2026-11-25T12:28:23+00:00

## D025 (build): I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Read connection string from code (hard-coded); Read from environment variables (DOCUMENTDB_URI)
- **Because:** Avoids storing secrets in repo and matches provided run environment and skill_md instructions.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report guidance: 'Read the cluster connection string from DOCUMENTDB_URI and expect mongodb+srv hostnames...'
- **When:** 2026-11-25T12:28:29+00:00

## D026 (build): I chose to read the OpenAI API key from environment variable OPENAI_API_KEY at runtime.

- **Instead of:** Store OPENAI key in file; Read OPENAI API key from environment
- **Because:** Avoids storing secrets and keeps sample secure and portable.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt_review: 'Model credentials will be read from environment variables (e.g. OPENAI_API_KEY).'
- **When:** 2026-11-25T12:28:32+00:00

## D027 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T13:31:10+00:00

## D028 (build): I chose Python (3.x) as the language and runtime for the sample, using the existing virtualenv accessible as `python`/`pip`.

- **Instead of:** Node.js/TypeScript; Python 3.11
- **Because:** The prompt requested a Python LangChain orchestration pipeline and the run environment already provides Python and pip inside a virtualenv.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt review: 'Builder will target a recent Python 3.x LTS... skill_md says `python`/`pip` resolve to a virtual environment.'
- **When:** 2026-11-25T13:31:40+00:00

## D029 (build): I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime and never store secrets in the repo.

- **Instead of:** Read credentials from a file in the repo; Read the cluster connection string from env var DOCUMENTDB_URI
- **Because:** Security best-practice and explicit guidance in readiness report and prompt. Allows sample to run against the provided cluster.
- **Reason came from:** `prompt`
- **Evidence:** Readiness report: 'Read the cluster connection string from DOCUMENTDB_URI' and prompt rule: 'Never write a secret... Read them from environment variables, and ship a .env.example with placeholder values.'
- **When:** 2026-11-25T13:31:43+00:00

## D030 (build): I chose not to provision Azure resources and to use the provided live cluster (DOCUMENTDB_URI) for verification; the sample will include optional IaC files but will not run any provisioning.

- **Instead of:** Attempt to provision cluster programmatically (Bicep/Terraform/az); Do not provision any Azure resources; operate against the existing cluster described in skill_md
- **Because:** Run policy forbids creating resources; the prompt also said to use the existing cluster. Provide IaC as files only if useful.
- **Reason came from:** `prompt`
- **Evidence:** Run policy: 'Azure resource changes allowed: False.' and readiness report: 'Build can start ... cluster reachable'.
- **When:** 2026-11-25T13:31:46+00:00

## D031 (build): I chose a single `customers` collection in database `sample_customer_360_18` with embedded addresses, a `firmographics` subdocument, `schemaVersion`, `normalized_name`, an `embedding` vector field, and `workflow_history` audit array.

- **Instead of:** Relational-style normalized model with references; Single customers collection with embedded addresses and firmographics
- **Because:** Azure DocumentDB favors denormalization/read-optimized designs; this schema keeps customer profile together and supports vector search and enrichment.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Builder will create one primary collection ... Documents will include standard fields: ...'
- **When:** 2026-11-25T13:31:49+00:00

## D032 (build): I chose OpenAI `text-embedding-3-small` (1536 dims) as the default embedding model, with a coded fallback to a deterministic hashed pseudo-embedding when an API key is not present.

- **Instead of:** Use OpenAI text-embedding-3-small (1536 dims); Use local small transformer embeddings (sentence-transformers)
- **Because:** OpenAI embeddings integrate well with LangChain and the sample cluster supports vector indexes of this dimensionality; fallback ensures the sample can run in environments without API keys for verification.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Reasonable defaults: an OpenAI-compatible chat model for LLM-assisted matching and `text-embedding-3-small` or similar for embeddings (e.g. 1536 dims).'
- **When:** 2026-11-25T13:31:52+00:00

## D033 (build): I chose to create standard indexes (email unique) via application code (pymongo) and create the vector `cosmosSearch` index via the documentdb MCP server (`documentdb_create_index`) for correctness and verification.

- **Instead of:** Create indexes only via application code using pymongo; Use the documentdb MCP server API to create the vector index and inspect indexes for verification
- **Because:** pymongo cannot express DocumentDB-specific `cosmosSearch` vector-index options; the documentdb MCP server supports creation and verification of native vector indexes and allows us to inspect the index shape.
- **Reason came from:** `skill`
- **Evidence:** documentdb-vector-search skill guidance: 'Create a `vector-diskann` index with correct `dimensions`...' and readiness report guidance to 'Enable and demonstrate native vector search and hybrid $search usage.'
- **When:** 2026-11-25T13:32:00+00:00
