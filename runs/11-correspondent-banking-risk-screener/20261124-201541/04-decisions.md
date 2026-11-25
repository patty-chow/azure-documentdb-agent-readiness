# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 5 |
| prompt | 4 |
| operator | 3 |
| skill | 3 |
| readiness_report | 2 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T10:07:38+00:00

## D002 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T10:09:33+00:00

## D003 (build): I chose Python 3 (modern 3.x runtime) for the sample.

- **Instead of:** Node.js/TypeScript; Python 3.x; C#/.NET
- **Because:** Python is the requested language in the sample prompt ('build a Python LangChain agent'), widely used for LangChain and pymongo, and matches the environment's available runtimes.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Builder will use a modern Python 3.x (likely 3.10 or 3.11) and create a virtualenv; tests and requirements will target that runtime.'
- **When:** 2026-11-25T10:09:59+00:00

## D004 (build): I chose pymongo 4.x (>=4.3,<5.0) as the MongoDB driver.

- **Instead of:** pymongo 3.x; pymongo 4.x
- **Because:** pymongo 4.x is current, matches DocumentDB examples, and is recommended by the installed documentdb-driver skill guidance.
- **Reason came from:** `prompt`
- **Evidence:** Prompt review assumption: 'Use the pymongo Python driver (pymongo 4.x, e.g. >=4.3,<5.0) and follow singleton MongoClient pattern per documentdb-driver guidance.'
- **When:** 2026-11-25T10:10:03+00:00

## D005 (build): I chose OpenAI embeddings (text-embedding-3-small) with 1536 dimensions by default, configurable via env.

- **Instead of:** OpenAI (text-embedding-3-small, 1536 dims); Azure OpenAI; HuggingFace local model
- **Because:** OpenAI embeddings are commonly available and simple to demonstrate; 1536 is the correct dimension for text-embedding-3-small; making it configurable ensures users can change provider in real runs.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report information gap: 'Embedding model & dimensions' and assumption in the prompt review recommending OpenAI text-embedding-3-small (1536 dims).
- **When:** 2026-11-25T10:10:05+00:00

## D006 (build): I chose to read the Azure DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Read connection string from a file; Read from environment variable DOCUMENTDB_URI; Prompt user interactively
- **Because:** Keeps secrets out of files and follows the provided environment setup; matches run constraints and README expectations.
- **Reason came from:** `prompt`
- **Evidence:** Skill run environment note: 'Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time.'
- **When:** 2026-11-25T10:10:08+00:00

## D007 (build): I chose not to provision resources and to use the existing cluster provided by the environment.

- **Instead of:** Provision new cluster (az/bicep/terraform); Use existing cluster (no provisioning)
- **Because:** Cluster is pre-provisioned and run policy disallows Azure write operations; sample must use live cluster at DOCUMENTDB_URI.
- **Reason came from:** `prompt`
- **Evidence:** Run environment: 'This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable.' Also run_policy forbids Azure resource changes.
- **When:** 2026-11-25T10:10:11+00:00

## D008 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T10:13:40+00:00

## D009 (build): I chose Python 3.13 (use Python for the sample)

- **Instead of:** Use JavaScript/Node.js; Use Python 3.x
- **Because:** The run environment already provides Python 3.13.13 and the sample is requested as a Python LangChain agent.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report: "Python 3.13.13"
- **When:** 2026-11-25T10:13:57+00:00

## D010 (build): I chose pymongo 4.x (>=4.3,<5.0) as the MongoDB driver.

- **Instead of:** pymongo 3.x; pymongo 4.x (>=4.3,<5.0)
- **Because:** PyMongo 4.x is current and supports modern MongoDB 7.0 wire protocol features used by the cluster.
- **Reason came from:** `skill`
- **Evidence:** documentdb-driver: 'MongoDB driver usage patterns that apply...'; readiness_report references PyMongo 4.x examples.
- **When:** 2026-11-25T10:14:17+00:00

## D011 (build): I chose to use the default MongoClient options (no custom pool tuning) for the sample.

- **Instead of:** Use default MongoClient options; Tune pool (maxPoolSize=50, minPoolSize=10)
- **Because:** This sample is a small demo running locally; tuning pool sizes is unnecessary and may mislead users. Keep code simple and use singleton client.
- **Reason came from:** `skill`
- **Evidence:** documentdb-connection skill: 'Use default max pool size (100) unless you have specific needs' and 'Before suggesting any configuration changes, ensure you have sufficient context'
- **When:** 2026-11-25T10:14:27+00:00

## D012 (build): I chose OpenAI text-embedding-3-small (1536 dimensions) for embeddings.

- **Instead of:** Use OpenAI text-embedding-3-small (1536 dims); Use local HuggingFace model (varies dims)
- **Because:** OpenAI embeddings are commonly available, simple to use in samples, and 1536 dims matches many LangChain examples and the cluster's vector-index examples; keeps index dimension manageable for demos.
- **Reason came from:** `model_default`
- **Evidence:** assumptions_from_prompt_review and readiness_report note embedding model needs to be chosen; text-embedding-3-small is a common choice producing 1536-d vectors.
- **When:** 2026-11-25T10:14:38+00:00

## D013 (build): I chose OpenAI gpt-3.5-turbo for generating the plain-language narrative.

- **Instead of:** Use gpt-4o-mini for narrative; Use gpt-3.5-turbo for narrative
- **Because:** gpt-3.5-turbo is broadly available and sufficient for generating short narratives in samples; it reduces chance of requiring special access compared to newer models.
- **Reason came from:** `model_default`
- **Evidence:** assumptions_from_prompt_review: 'Use a chat/completion model via LangChain' and common availability of gpt-3.5-turbo.
- **When:** 2026-11-25T10:14:41+00:00

## D014 (build): I chose to provide a small FastAPI app with a POST /review endpoint and a CLI demo script.

- **Instead of:** FastAPI HTTP API; CLI-only script
- **Because:** FastAPI makes the sample easy to run locally and call via curl; also provides a clear API surface for integrations.
- **Reason came from:** `model_default`
- **Evidence:** assumptions_from_prompt_review suggested FastAPI and a CLI driver for demo; FastAPI is lightweight and suitable for showing the agent interface.
- **When:** 2026-11-25T10:14:44+00:00

## D015 (build): I chose to inject synthetic normalized random embeddings into seed documents when OPENAI_API_KEY is not present to allow verification of vector indexes and queries.

- **Instead of:** Require OPENAI_API_KEY to run verification; Inject synthetic random embeddings for verification when OPENAI_API_KEY not present
- **Because:** OPENAI_API_KEY was not set in the run environment, so to verify vector-index behavior and queries we will generate deterministic random vectors for the sample documents. This keeps secrets out of files and allows the sample to run in CI or a developer machine without an API key.
- **Reason came from:** `model_default`
- **Evidence:** readiness_report: 'Embedding model & dimensions are an information gap' and current environment lacks OPENAI_API_KEY; seeding with synthetic vectors allows testing index/search without revealing or requiring keys.
- **When:** 2026-11-25T10:16:04+00:00

## D016 (build): I chose to create vector (cosmosSearch) indexes on correspondents, sanctions, and adverse_media collections for the sample.

- **Instead of:** Create vector index only on correspondents; Create vector index on correspondents, sanctions, and adverse_media
- **Because:** To enable vector similarity searches against sanctions and adverse_media for hybrid retrieval in the sample, each collection must have a vector index on the embedding field; adding them for the small demo is low-cost and enables verification.
- **Reason came from:** `skill`
- **Evidence:** documentdb-vector-search guidance: "Create the vector index on the collection(s) you will search against"; sample uses sanctions and adverse_media as retrieval sources.
- **When:** 2026-11-25T10:16:28+00:00

## D017 (build): I chose to add deterministic metadata fallback queries (exact entity_name match for sanctions and simple substring match on adverse_media headlines) when vector/$search is not available.

- **Instead of:** Rely only on vector/$search and fail if not available; Add deterministic metadata fallback queries (entity_name match, headline regex) when $search is not available
- **Because:** Provide a reliable demo behavior that works even when server-side search features are limited; fallback metadata queries are deterministic and safe for a sample app.
- **Reason came from:** `readiness_report`
- **Evidence:** The live cluster may not support search index creation (createSearchIndexes returned CommandNotSupported) and vector similarity indices were not found on some collections during verification.
- **When:** 2026-11-25T10:16:52+00:00
