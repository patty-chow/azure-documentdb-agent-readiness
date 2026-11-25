# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 8 |
| readiness_report | 5 |
| operator | 3 |
| skill | 2 |
| prompt | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T12:29:34+00:00

## D002 (build): I chose Python 3.13 as the runtime for the sample.

- **Instead of:** Python 3.10/3.11 virtualenv; Python 3.13 (system)
- **Because:** The environment already has Python 3.13 installed; using it avoids creating an alternate virtualenv and matches the run environment.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: "Python 3.13.13 on PATH"
- **When:** 2026-11-25T12:30:16+00:00

## D003 (build): I chose Motor (AsyncIOMotorClient) together with Beanie ODM.

- **Instead of:** Motor (AsyncIOMotorClient) + Beanie ODM; PyMongo AsyncMongoClient (no Motor)
- **Because:** Beanie requires Motor for its async ORM support, so to use Beanie models and follow library patterns we must use Motor as the async client.
- **Reason came from:** `model_default`
- **Evidence:** documentdb-driver skill and readiness guidance recommending motor + Beanie for async Python code; Beanie historically depends on Motor.
- **When:** 2026-11-25T12:30:19+00:00

## D004 (build): I chose OpenAI text-embedding-3-small with 1536 dimensions for embeddings.

- **Instead of:** OpenAI text-embedding-3-small (1536 dims); Other embedding models (provider unspecified)
- **Because:** Pick a concrete, commonly used embedding model so vector-index dimensions and code are deterministic; 1536 is standard for several OpenAI embedding models.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report identified missing embedding model and dimension; vector-search skill examples use 1536 for OpenAI text-embedding-3-small.
- **When:** 2026-11-25T12:30:22+00:00

## D005 (build): I chose OpenAI gpt-3.5-turbo for LLM-assisted merge/decision steps.

- **Instead of:** OpenAI gpt-3.5-turbo for LLM steps; Azure OpenAI or Anthropic etc.
- **Because:** Use a broadly available and low-cost chat model for merge decision logic in the sample; keep it configurable via env var OPENAI_API_MODEL.
- **Reason came from:** `model_default`
- **Evidence:** Prompt did not specify provider; OpenAI is commonly available and supported by LangChain.
- **When:** 2026-11-25T12:30:27+00:00

## D006 (build): I chose vector-hnsw for the sample's vector index.

- **Instead of:** Create vector index type vector-diskann (DiskANN); Use vector-hnsw for sample-sized data
- **Because:** Small sample (<5k vectors) and HNSW is easy to build and demonstrates cosine similarity; index dimensions will be 1536 and similarity COS.
- **Reason came from:** `skill`
- **Evidence:** documentdb-vector-search guidance: HNSW is suitable up to ~50k vectors and is simpler for small sample datasets.
- **When:** 2026-11-25T12:30:57+00:00

## D007 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T12:33:38+00:00

## D008 (build): I chose Python (async) with motor + Beanie (Python 3.13), using motor 3.x/pymongo 4.x and Beanie latest.

- **Instead of:** Node.js/TypeScript; Python (sync) with PyMongo; Python (async) with motor + Beanie
- **Because:** The sample and skills recommend async Python with Beanie; environment already has Python 3.13 and documentdb-driver skill guidance.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'Python 3.13.13 on PATH' and guidance: 'Use motor + Beanie for async Python code and follow the documentdb-driver skill patterns (singleton AsyncIOMotorClient, reuse client)'.
- **When:** 2026-11-25T12:33:52+00:00

## D009 (build): I chose OpenAI text-embedding-3-small with 1536 dimensions for embeddings, stored in document field `embedding` and used to create an HNSW vector index.

- **Instead of:** OpenAI text-embedding-3-small (1536 dims); OpenAI text-embedding-3-large (3072 dims); Azure OpenAI text-embedding-3-small via endpoint
- **Because:** text-embedding-3-small is commonly used in samples for semantic similarity and has manageable dimensionality (1536) for example datasets; HNSW offers a good recall/latency balance.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report information gap: 'Embedding model and vector dimension' — no model specified. documentdb-vector-search skill recommends picking a model first and setting index 'dimensions' accordingly.
- **When:** 2026-11-25T12:33:59+00:00

## D010 (build): I chose OpenAI API for embeddings and LLM calls; API key provided through OPENAI_API_KEY environment variable.

- **Instead of:** OpenAI (openai.com); Azure OpenAI (Azure endpoint); Anthropic
- **Because:** OpenAI is widely used, matches tooling (embeddings + chat), and simplifies sample setup; using OPENAI_API_KEY keeps credentials out of code.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report gap: 'LLM/chat provider and credentials' — not specified. LangChain supports OpenAI and it's common in samples.
- **When:** 2026-11-25T12:34:04+00:00

## D011 (build): I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Read connection string from config file; Read connection string from environment variable DOCUMENTDB_URI; Prompt user at runtime
- **Because:** Security and run policy require not hardcoding secrets; README and .env.example will instruct setting DOCUMENTDB_URI.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'Read the complete connection string from DOCUMENTDB_URI environment variable at runtime (do not hardcode ports or host suffixes)'.
- **When:** 2026-11-25T12:34:07+00:00

## D012 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T12:37:27+00:00

## D013 (build): I chose Python 3.13 with async Motor + Beanie (async Python stack).

- **Instead of:** Node.js/TypeScript; Python 3.10/3.11; Python 3.13
- **Because:** Environment already has Python 3.13; async Motor+Beanie is recommended by documentdb-driver skill for async Beanie code.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report: 'Python 3.13.13 on PATH'
- **When:** 2026-11-25T12:38:09+00:00

## D014 (build): I chose pymongo>=4.5, motor>=3.1 and beanie>=1.12 (modern drivers compatible with MongoDB 7.0).

- **Instead of:** pymongo 3.x + motor 2.x + beanie older; pymongo 4.x + motor 3.x + beanie 1.x
- **Because:** These versions are compatible with MongoDB 7.0 wire protocol and Beanie async usage; they align with the environment and installed requirements.
- **Reason came from:** `model_default`
- **Evidence:** requirements.txt includes 'pymongo>=4.5.0', 'motor>=3.1.1', 'beanie>=1.12.0'
- **When:** 2026-11-25T12:38:12+00:00

## D015 (build): I chose to read the DocumentDB connection string from the DOCUMENTDB_URI environment variable at runtime.

- **Instead of:** Use connection string from file; Read DOCUMENTDB_URI from environment; Use Azure Key Vault
- **Because:** Prompt and readiness report require not to write secrets to files and to read connection string from env var.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report guidance: 'Read the complete connection string from DOCUMENTDB_URI environment variable at runtime'
- **When:** 2026-11-25T12:38:15+00:00

## D016 (build): I chose OpenAI for embeddings and LLM: embeddings model 'text-embedding-3-small' (1536 dims) and LLM 'gpt-3.5-turbo' as the default. The code falls back to synthetic embeddings when OPENAI_API_KEY is not set.

- **Instead of:** OpenAI embeddings + LLM (text-embedding-3-small, gpt-3.5-turbo); Azure OpenAI; Anthropic Claude
- **Because:** OpenAI is a common default, and the sample must allow running without keys; fallback synthetic embeddings enable offline runs and verification.
- **Reason came from:** `model_default`
- **Evidence:** readiness_report: 'Information gaps: Embedding model and vector dimension' and sample code uses OPENAI_* env vars
- **When:** 2026-11-25T12:38:18+00:00

## D017 (build): I chose a vector-hnsw index on profiles.embedding with dimensions=1536 and similarity='COS' for the sample.

- **Instead of:** vector-diskann; vector-hnsw; vector-ivf
- **Because:** Sample size is small (~200), HNSW is simple and supported; COS aligns with normalized embeddings.
- **Reason came from:** `skill`
- **Evidence:** documentdb-vector-search skill: 'Prefer DiskANN for production; use HNSW up to ~50k vectors'
- **When:** 2026-11-25T12:38:24+00:00

## D018 (build): I chose not to provision resources and to use the existing cluster referenced by DOCUMENTDB_URI.

- **Instead of:** Provision a new cluster via Bicep/az; Use the existing cluster specified by DOCUMENTDB_URI
- **Because:** Run policy forbids creating or changing Azure resources; prompt explicitly provided a reachable cluster to use.
- **Reason came from:** `prompt`
- **Evidence:** prompt: 'A vector-capable Azure DocumentDB cluster ... connection string is in the environment variable DOCUMENTDB_URI.'; run_policy forbids Azure resource changes.
- **When:** 2026-11-25T12:38:26+00:00

## D019 (build): I chose the data model and collections named 'profiles', 'golden_profiles', and 'merge_audits' (Profile, GoldenRecord, AuditEntry Beanie models).

- **Instead of:** profiles/golden_profiles/merge_audits; users/accounts/transactions
- **Because:** Matches the prompt and keeps the sample focused on identity-resolution artifacts; models are already implemented in src/models.py.
- **Reason came from:** `model_default`
- **Evidence:** assumptions_from_prompt_review and existing src/models.py which defines these models
- **When:** 2026-11-25T12:38:30+00:00
