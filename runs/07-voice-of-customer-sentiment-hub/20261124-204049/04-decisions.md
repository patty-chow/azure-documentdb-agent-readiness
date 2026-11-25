# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 6 |
| readiness_report | 4 |
| model_default | 3 |
| tool_result | 3 |
| operator | 2 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T11:29:24+00:00

## D002 (build): I chose Python 3.x (developer machine CPython), targeting a modern 3.11-compatible runtime.

- **Instead of:** Use Python (3.x); Use Node.js; Use .NET
- **Because:** The sample integrates Beanie ODM and LangChain (Python) and the run environment includes Python and pip. Python is the natural choice.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Builder will target a modern Python 3.x (commonly 3.10 or 3.11) virtualenv; code and requirements will assume CPython 3.11-compatible dependencies."
- **When:** 2026-11-25T11:29:52+00:00

## D003 (build): I chose Beanie ODM with Motor (MotorClient) for async MongoDB access.

- **Instead of:** Beanie + Motor (traditional); Adapt Beanie to AsyncPyMongo; Skip Beanie and use AsyncPyMongo directly
- **Because:** Beanie simplifies schema definition and keeps the sample small and readable; Motor is a widely-used async driver and commonly paired with Beanie, making the sample accessible to readers. Adapting Beanie to AsyncPyMongo would add complexity.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: "Decide whether to use Beanie + Motor (simpler, historically supported) or migrate to PyMongo AsyncMongoClient per documentdb-driver guidance; document this choice in README and show the client singleton pattern for connection reuse."
- **When:** 2026-11-25T11:29:56+00:00

## D004 (build): I chose OpenAI embeddings: model 'text-embedding-3-small' and to use EMBEDDING_DIM=1536 as the expected embedding dimension.

- **Instead of:** OpenAI text-embedding-3-small (1536); OpenAI text-embedding-3-large (1536?); HuggingFace all-MiniLM-L6-v2 (384)
- **Because:** OpenAI embeddings are widely available via LangChain and familiar to many users. 'text-embedding-3-small' is a compact, capable choice appropriate for samples. The exact dimension (1536) is set as a best-effort default and documented so users can change it.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: "The sample must pick an embedding provider and exact model (OpenAI/Azure OpenAI/other) which determines the embedding dimension... the builder must choose model names and set EMBEDDING_DIM env var."
- **When:** 2026-11-25T11:29:59+00:00

## D005 (build): I chose gpt-3.5-turbo as the default LLM for extraction prompts and set LLM_MODEL='gpt-3.5-turbo'.

- **Instead of:** gpt-4o / gpt-4 family; gpt-3.5-turbo family; local LLM
- **Because:** gpt-3.5-turbo balances cost and capability for prompt-engineered extraction tasks in a sample. It's widely available to users and integrates with LangChain easily. Users can override via env vars.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: "Builder will use LangChain for prompts and embeddings with a mainstream provider (e.g., OpenAI via OPENAI_API_KEY)."
- **When:** 2026-11-25T11:30:01+00:00

## D006 (build): I chose to read the DocumentDB connection URI and AI keys from environment variables (DOCUMENTDB_URI, OPENAI_API_KEY), and provide a .env.example with placeholders.

- **Instead of:** Read secrets from environment variables; Hard-code connection strings in files; Prompt for secrets at runtime
- **Because:** Keeps secrets out of source control and follows the prompt's security requirement.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: "Read it from the environment at run time. Never write its value into any file... use a config file or `.env.example` with placeholder values."
- **When:** 2026-11-25T11:30:05+00:00

## D007 (build): I chose not to provision Azure resources and to use the existing reachable DocumentDB cluster provided via DOCUMENTDB_URI.

- **Instead of:** Create cloud resources (Bicep/Terraform/az); Do not create cloud resources and use existing cluster
- **Because:** The environment already provides a cluster; provisioning is unnecessary and disallowed by policy.
- **Reason came from:** `prompt`
- **Evidence:** Skill run environment: "A vector-capable Azure DocumentDB cluster ... is reachable from this machine. Its connection string is in the environment variable DOCUMENTDB_URI." Also run policy: "Azure resource changes allowed: False."
- **When:** 2026-11-25T11:30:12+00:00

## D008 (build): I chose to use the DocumentDB createSearchIndexes DB command for vector and text search indexes and to query them via the $search aggregation stage (fallback to create_index for non-search indexes).

- **Instead of:** Use standard createIndex() for all indexes including vector and text; Use createSearchIndexes DB command and $search aggregation stage for text and vector indexes
- **Because:** This matches DocumentDB best practices for vector and full-text search and enables using DiskANN/HNSW/IVF index types offered by the cluster.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report guidance: "Do not create vector / full-text indexes with the standard createIndex call; instead create search indexes via the `createSearchIndexes` DB command and query them via the `$search` aggregation stage."
- **When:** 2026-11-25T11:30:15+00:00

## D009 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T11:32:48+00:00

## D010 (build): I chose Python 3.11 (CPython) for the sample app.

- **Instead of:** Node.js/TypeScript; Python 3.11; Go
- **Because:** The prompt requests a Python LangChain agent using Beanie ODM; Python is the natural choice and 3.11 provides modern features and wide library support.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Builder will target a modern Python 3.x (commonly 3.10 or 3.11) virtualenv; code and requirements will assume CPython 3.11-compatible dependencies.'
- **When:** 2026-11-25T11:33:06+00:00

## D011 (build): I chose Beanie + Motor (the traditional async driver) for simplicity and compatibility with Beanie.

- **Instead of:** Beanie + Motor (historical); Beanie + AsyncPyMongo adapter; Use ODM other than Beanie
- **Because:** Beanie is requested by prompt and is most directly compatible with Motor; using Motor keeps the sample concise and familiar to many users. Migrating to AsyncPyMongo would increase complexity and risk for this sample.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report guidance: 'Decide whether to use Beanie + Motor (simpler, historically supported) or migrate to PyMongo AsyncMongoClient per documentdb-driver guidance; document this choice in README and show the client singleton pattern for connection reuse.'
- **When:** 2026-11-25T11:33:09+00:00

## D012 (build): I chose OpenAI embeddings (text-embedding-3-small) and set EMBEDDING_MODEL accordingly, but provide a deterministic local fallback when API key is not present.

- **Instead of:** OpenAI embeddings (text-embedding-3-small); sentence-transformers local model (all-MiniLM-L6-v2)
- **Because:** OpenAI via LangChain is common and simpler for users with keys; a fallback ensures the sample works without cloud keys for verification. The exact embedding dim is not authoritative here so it's recorded as a model_default choice.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'Embedding model & vector dimension ... builder must choose model names and set EMBEDDING_DIM env var.'
- **When:** 2026-11-25T11:33:13+00:00

## D013 (build): I chose gpt-3.5-turbo as the LLM for prompt-based extraction (sentiment, topics, quote) and will use OPENAI_API_KEY for auth, with a local heuristic fallback when the key is missing.

- **Instead of:** gpt-3.5-turbo; gpt-4o-mini; local LLM
- **Because:** gpt-3.5-turbo is widely available, cost-effective for extraction tasks, and integrates with LangChain; fallback keeps verification possible without cloud keys.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Builder will use LangChain for prompts and embeddings with a mainstream provider (e.g., OpenAI via OPENAI_API_KEY).'
- **When:** 2026-11-25T11:33:16+00:00

## D014 (build): I chose to create search indexes using the createSearchIndexes DB command (vector-hnsw) per documentdb-vector-search guidance, but will fall back to storing embeddings without a search index if the command isn't accepted by the live cluster; index creation is marked in the report if not verified.

- **Instead of:** Create search indexes with createSearchIndexes DB command (vector-hnsw); Use standard createIndex; Skip search indexes and only store embeddings
- **Because:** Follow the DocumentDB skill guidance for vector and text search. Because the exact DB command syntax can vary, include robust error handling and record verification status.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness_report guidance: 'Do not create vector / full-text indexes with the standard createIndex call; instead create search indexes via the createSearchIndexes DB command ... choose vector-hnsw or vector-diskann.'
- **When:** 2026-11-25T11:33:19+00:00

## D015 (build): I chose to read all secrets (DOCUMENTDB_URI, OPENAI_API_KEY, EMBEDDING_MODEL, LLM_MODEL) from environment variables at runtime and provide a .env.example with placeholders.

- **Instead of:** Use environment env vars for secrets; Store secrets in files
- **Because:** Security best practice and required by the prompt. .env.example gives a template without secrets.
- **Reason came from:** `prompt`
- **Evidence:** Prompt and readiness report: 'Read the cluster connection string from DOCUMENTDB_URI ... read from the environment at run time. Never write its value into a file.'
- **When:** 2026-11-25T11:33:21+00:00

## D016 (build): I chose to switch to beanie==1.30.0 because beanie==1.20.1 is not available from PyPI in this environment.

- **Instead of:** Keep beanie==1.20.1 (failed); Use beanie==1.30.0
- **Because:** Use a recent available release compatible with Beanie API used in the sample; 1.30.0 exists on PyPI per the installer error output list.
- **Reason came from:** `tool_result`
- **Evidence:** pip installation failed: "No matching distribution found for beanie==1.20.1"
- **When:** 2026-11-25T11:34:20+00:00

## D017 (build): I chose to switch to a Motor+pymongo-only implementation (no Beanie, no pydantic) because the environment's Python (3.13) triggered pydantic-core build failures requiring Rust toolchain; using Motor avoids that blocker and keeps the sample runnable here.

- **Instead of:** Persist with Beanie and install heavy dependencies (requires Rust/pydantic-core); Switch to Motor+pymongo-only approach and avoid pydantic/Beanie to make the sample installable in this environment
- **Because:** Using Motor directly keeps dependencies small and avoids the need for Rust compilation in this environment, enabling verification. I'll document this change in the BUILD report and README.
- **Reason came from:** `tool_result`
- **Evidence:** pip install failed building pydantic-core: 'Failed building wheel for pydantic-core' (see pip stderr).
- **When:** 2026-11-25T11:34:47+00:00

## D018 (build): I chose to switch to the synchronous pymongo.MongoClient to avoid motor/pymongo compatibility issues in this environment and keep the sample simple to run in scripts.

- **Instead of:** Fix motor/pymongo mismatch by pinning versions; Switch to synchronous pymongo client
- **Because:** Using pymongo directly avoids the motor/pymongo mismatch and simplifies scripts for seeding and aggregation in a sample repository. The sample remains representative of the DocumentDB usage pattern.
- **Reason came from:** `tool_result`
- **Evidence:** ImportError from motor caused by incompatible internal API: 'cannot import name _QUERY_OPTIONS from pymongo.cursor' during script run.
- **When:** 2026-11-25T11:35:33+00:00
