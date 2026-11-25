# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 16 |
| readiness_report | 5 |
| operator | 4 |
| model_default | 4 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T09:13:15+00:00

## D002 (build): I chose Python 3.13 (targeting Python 3.10+ compatibility) as the language/runtime for the sample app.

- **Instead of:** Node.js/TypeScript; Python 3.10+
- **Because:** The sample and LangChain examples are commonly written in Python; the run environment provides Python 3.13 and pip. Python best matches LangChain and PyMongo ecosystems.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Builder will target a modern Python 3.x runtime (likely 3.10 or 3.11). I.e., assume Python 3.10+ for dependencies and type hints."
- **When:** 2026-11-25T09:13:30+00:00

## D003 (build): I chose pymongo >= 4.3 (latest-compatible) as the MongoDB driver for Azure DocumentDB.

- **Instead of:** pymongo 3.x; pymongo >=4.3
- **Because:** pymongo 4.x is compatible with MongoDB 7.0 wire protocol and supports modern connection options; documentdb-driver skill recommends singleton MongoClient.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Use the Python MongoDB driver (PyMongo) and a recent stable release compatible with MongoDB 7.0 (e.g., pymongo >= 4.3). Follow the documentdb-driver guidance to use a singleton MongoClient."
- **When:** 2026-11-25T09:13:33+00:00

## D004 (build): I chose to read the connection string from the DOCUMENTDB_URI environment variable at runtime and never store secrets in files.

- **Instead of:** Use connection string with embedded user/pass in code; Read DOCUMENTDB_URI from environment variable at runtime
- **Because:** Security and prompt requirements prohibit writing secrets into files; using env var is standard practice.
- **Reason came from:** `prompt`
- **Evidence:** Run environment: "Its connection string is in the environment variable `DOCUMENTDB_URI`. Read it from the environment at run time. Never write its value into any file"
- **When:** 2026-11-25T09:13:36+00:00

## D005 (build): I chose to use a text embedding model 'text-embedding-3-small' (1536 dims) as the sample default and to create only simple patient_id single-field indexes for verification; vector indexing is included in code but gate-run by presence of OPENAI_API_KEY.

- **Instead of:** Create vector index and use embeddings with actual LLM calls; Skip vector index and only create simple indexes since LLM key may be missing
- **Because:** Embedding model requires an API key to generate vectors; the run environment lacks an LLM key. To avoid failures during verification, vector index creation will be conditional and documented; single-field indexes suffice for the demo data and queries.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: "choose an embedding model and dimension" and assumptions recommending text-embedding-3-small producing 1536-dim vectors.
- **When:** 2026-11-25T09:13:39+00:00

## D006 (build): I chose separate collections for patients, referrals, medications, and care_plans (one collection per document type) with simple JSON shapes referencing patient_id.

- **Instead of:** Embed referrals and medications inside patients collection; Use separate collections for patients, referrals, medications, care_plans
- **Because:** Separate collections keep sample logic clear and mirror common healthcare data models; for small sample embedding might be OK but separate collections demonstrate queries and indexes more clearly.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Builder will create collections: patients (primary care records keyed by patient_id), referrals (referral notes with patient_id), medications (current meds with patient_id), and care_plans (synthesised documents)."
- **When:** 2026-11-25T09:13:55+00:00

## D007 (build): I chose to create single-field indexes on patient_id for patients, referrals, and medications collections unconditionally; vector index creation will be conditional on presence of embedding key and documented.

- **Instead of:** Create single-field indexes on patient_id only; Create single-field indexes plus vector index unconditionally
- **Because:** Single-field indexes are low-cost and useful for sample queries; vector index requires embedding model and API key, so defer to optional creation.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Create single-field indexes on patient_id for the patients/referrals/medications collections. If using vector retrieval..., create a vector index..."
- **When:** 2026-11-25T09:13:58+00:00

## D008 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T09:16:52+00:00

## D009 (build): I chose Python 3.10+ for the sample (modern Python runtime).

- **Instead of:** Node.js/TypeScript; Python 3.10+; C#/.NET
- **Because:** The sample and LangChain ecosystem are commonly used with Python; the run environment has Python available. Python enables concise scripts, simple FastAPI endpoint, and compatibility with pymongo and LangChain.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Builder will target a modern Python 3.x runtime (likely 3.10 or 3.11).'
- **When:** 2026-11-25T09:17:10+00:00

## D010 (build): I chose pymongo (synchronous) >=4.3 as the MongoDB driver and will implement a singleton MongoClient.

- **Instead of:** motor (async); pymongo (sync)
- **Because:** Synchronous pymongo is simple and well-supported; sample is small and easier to reason about synchronously. The documentdb-driver skill recommends a singleton MongoClient.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use the Python MongoDB driver (PyMongo) and a recent stable release compatible with MongoDB 7.0 (e.g., pymongo >= 4.3).'
- **When:** 2026-11-25T09:17:14+00:00

## D011 (build): I chose not to use vector retrieval or create vector indexes for this sample; the sample will use standard text aggregation and an LLM for synthesis.

- **Instead of:** Use vector retrieval with embeddings and vector indexes; Use only classic DB queries and no vector retrieval
- **Because:** To reduce complexity, avoid having to pick an embedding model/dimension and create vector indexes; the orchestrator can synthesize from fetched text via an LLM. This keeps the sample simpler and avoids needing OPENAI_API_KEY to verify DB operations.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'Vector indexes and full-text search are supported... builder must pick an embedding model and dimension...' and assumption: 'If using vector retrieval... create vector index.'
- **When:** 2026-11-25T09:17:21+00:00

## D012 (build): I chose OpenAI-compatible provider with embedding model text-embedding-3-small (1536 dims) and chat model gpt-4o-mini for synthesis, configured via OPENAI_API_KEY environment variable.

- **Instead of:** OpenAI (text-embedding-3-small + gpt-4o-mini); Anthropic or Azure OpenAI
- **Because:** OpenAI is widely available and compatible with LangChain; text-embedding-3-small is a moderate-dimension embedding and gpt-4o-mini is cost-effective for synthesis. Using env vars keeps secrets out of the repo.
- **Reason came from:** `prompt`
- **Evidence:** Assumptions from prompt review: 'Use an OpenAI-compatible provider (env var OPENAI_API_KEY). Use text-embedding-3-small producing 1536-d vectors and a chat model (gpt-4o-mini).'
- **When:** 2026-11-25T09:17:26+00:00

## D013 (build): I chose to use the existing live Azure DocumentDB cluster and not provision any resources.

- **Instead of:** Provision cluster with Bicep/az/terraform; Use existing live cluster and do not provision
- **Because:** Policy forbids provisioning; an existing cluster is available and documented, so use it for sample data and verification.
- **Reason came from:** `prompt`
- **Evidence:** Run environment: 'This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable.' Run policy: 'Azure resource changes allowed: False.'
- **When:** 2026-11-25T09:17:29+00:00

## D014 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T09:22:01+00:00

## D015 (build): I chose Python 3.10+ as the language/runtime for the sample.

- **Instead of:** Node.js/TypeScript; Python 3.10+
- **Because:** Python is the language requested by the prompt and is the natural choice for LangChain and Azure SDKs; the run environment has Python 3.13 available.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Builder will target a modern Python 3.x runtime (likely 3.10 or 3.11). I.e., assume Python 3.10+ for dependencies and type hints.'
- **When:** 2026-11-25T09:22:22+00:00

## D016 (build): I chose PyMongo (pymongo) >=4.7 as the MongoDB driver.

- **Instead of:** pymongo 3.x; pymongo >=4.7
- **Because:** PyMongo is the official MongoDB driver and recent 4.x releases support MongoDB 7.0 wire protocol features; the documentdb-driver skill recommends a singleton MongoClient.
- **Reason came from:** `model_default`
- **Evidence:** Assumption: 'Use the Python MongoDB driver (PyMongo) and a recent stable release compatible with MongoDB 7.0 (e.g., pymongo >= 4.3). Follow the documentdb-driver guidance to use a singleton MongoClient.'
- **When:** 2026-11-25T09:22:25+00:00

## D017 (build): I chose to read the DocumentDB connection string from the DOCUMENTDB_URI environment variable at runtime.

- **Instead of:** Use connection strings from a file; Read DOCUMENTDB_URI from environment
- **Because:** Security: avoid committing secrets; follow run-environment instruction and sample policy.
- **Reason came from:** `prompt`
- **Evidence:** Run environment: 'Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time. Never write its value into a file, log, README or test fixture; use a config file or .env.example with a placeholder, as the prompt asks.'
- **When:** 2026-11-25T09:22:27+00:00

## D018 (build): I chose not to provision any Azure resources and to use the existing live cluster described in the run environment.

- **Instead of:** Provision resources via Azure CLI/Bicep/Terraform; Do not provision resources and use the existing live cluster
- **Because:** Provisioning is disallowed by policy and unnecessary; use the provided cluster.
- **Reason came from:** `prompt`
- **Evidence:** Run policy: 'Azure resource changes allowed: False.' and readiness_report: 'a cluster is already provisioned and reachable... Do not provision another cluster.'
- **When:** 2026-11-25T09:22:30+00:00

## D019 (build): I chose to include simple single-field indexes for patient lookups and NOT create a vector index in the sample runtime. The code supports adding vector retrieval later and documents how to add vector indexes.

- **Instead of:** Use vector retrieval and create vector index; Do not use vector retrieval in this demo
- **Because:** No LLM/embedding credentials were provided in the environment, so creating a vector index tied to a chosen embedding dimension may be misleading; a single-field index suffices for this tutorial and low-volume sample data. The README documents how to add vector indexes later.
- **Reason came from:** `model_default`
- **Evidence:** Assumption: 'Create single-field indexes on patient_id for the patients/referrals/medications collections. If using vector retrieval ... create a vector index with dimensions matching the chosen embedding model.' Readiness_report: 'builder must pick an embedding model and dimension.'
- **When:** 2026-11-25T09:22:35+00:00

## D020 (build): I chose OpenAI-compatible provider via OPENAI_API_KEY as the default LLM/embedding provider, with a code-path fallback to a deterministic 'mock' synthesizer if no key is present at runtime.

- **Instead of:** Use OpenAI as LLM/embeddings provider; Leave provider unspecified
- **Because:** OpenAI is a common provider for LangChain examples; to keep the sample runnable without secrets we'll implement a safe fallback so the seed and orchestrator can be demonstrated offline.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Use an OpenAI-compatible provider (env var OPENAI_API_KEY). Use ... text-embedding-3-small ... and a chat/completion model.' Readiness_report: 'LLM/embedding provider credentials not present; builder must document env vars.'
- **When:** 2026-11-25T09:22:39+00:00

## D021 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T13:06:16+00:00

## D022 (build): I chose Python 3.10+ as the language/runtime for the sample app, targeting modern Python (3.10/3.11/3.13 compatibility).

- **Instead of:** Node.js/TypeScript; Python 3.10+; Go
- **Because:** Python is the requested language in the prompt and has strong LangChain and pymongo support; it's the most natural fit for the sample and the environment has Python available.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Builder will target a modern Python 3.x runtime (likely 3.10 or 3.11). I.e., assume Python 3.10+ for dependencies and type hints.'
- **When:** 2026-11-25T13:06:34+00:00

## D023 (build): I chose the Python pymongo driver (pymongo >=4.3) and will follow a singleton MongoClient pattern.

- **Instead of:** pymongo latest; motor (async); mongoengine ORM
- **Because:** pymongo is the standard sync driver compatible with MongoDB 7.0 and documented in DocumentDB skills; singleton MongoClient avoids connection-pool issues.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use the Python MongoDB driver (PyMongo) and a recent stable release compatible with MongoDB 7.0 (e.g., pymongo >= 4.3). Follow the documentdb-driver guidance to use a singleton MongoClient.'
- **When:** 2026-11-25T13:06:40+00:00

## D024 (build): I chose to use the connection string read from environment variable DOCUMENTDB_URI for data-plane auth at runtime.

- **Instead of:** Use managed identity / AAD OIDC; Use connection string from env var DOCUMENTDB_URI
- **Because:** Environment variable-based connection string is simplest for a sample, aligns with run environment, and avoids embedding secrets; documentation supports SRV or non-SRV connection strings in this variable.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'A vector-capable Azure DocumentDB cluster ... connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time.'
- **When:** 2026-11-25T13:06:52+00:00

## D025 (build): I chose not to provision any Azure resources and to use the existing live cluster specified by DOCUMENTDB_URI.

- **Instead of:** Provision a new cluster with Bicep/Terraform/azd; Use the existing live cluster and do not provision
- **Because:** Provisioning is disallowed by policy; the run environment already provides a reachable cluster.
- **Reason came from:** `readiness_report`
- **Evidence:** Run policy forbids Azure resource changes and readiness report: 'Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use.'
- **When:** 2026-11-25T13:06:55+00:00

## D026 (build): I chose to create only single-field indexes (patient_id) in the sample seed script and to skip creating a vector index by default. Vector index creation is optional and documented in README; it will be enabled only if an embedding key is present.

- **Instead of:** Create vector index by default; Create only single-field indexes; skip vector index unless LLM creds present
- **Because:** Embedding/LLM credentials are not guaranteed in the environment; creating a vector index without matching embedding dimensions or embeddings is unnecessary for the core sample and may confuse users. We'll document how to create it when credentials are available.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'Vector indexes ... set dimensions to the chosen embedding model's output dimension' and 'LLM/embedding provider credentials ... available: false'.
- **When:** 2026-11-25T13:06:59+00:00

## D027 (build): I chose OpenAI-compatible models: text-embedding-3-small (1536 dims) for embeddings and gpt-4o-mini as the synthesis chat model, configurable via env vars OPENAI_API_KEY and LLM_MODEL.

- **Instead of:** OpenAI text-embedding-3-small (1536 dims) + gpt-4o-mini; OpenAI text-embedding-3-large + gpt-4o; Other provider
- **Because:** text-embedding-3-small is a reasonable compact embedding model with 1536 dims; gpt-4o-mini is a cost-conscious chat model. Both are commonly available from OpenAI-compatible endpoints and easy to configure. Users can override via env vars.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use an OpenAI-compatible provider (env var OPENAI_API_KEY). Use a commonly used embedding model (e.g., text-embedding-3-small producing 1536-d vectors) and a chat/completion model for synthesis (e.g., gpt-4o-mini or gpt-4o where available). Put provider credentials in environment variables and document them in .env.example.'
- **When:** 2026-11-25T13:07:02+00:00

## D028 (build): I chose to pin reasonable, recent package versions for requirements.txt: pymongo==4.8.0, langchain==0.0.349, openai==1.36.0, fastapi==0.95.2, uvicorn==0.22.0, python-dotenv==1.0.0, pytest==7.4.0, pytest-mock==3.11.0.

- **Instead of:** Pin broad versions; Pin specific versions for requirements.txt
- **Because:** Pinning specific versions reduces surprise for users; chosen versions are recent and compatible with modern Python and driver, and are commonly used with LangChain and OpenAI SDKs. They can be adjusted by users as needed.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'Pinned dependency versions for Python stack' missing; need to choose versions compatible with Python 3.10+ and MongoDB 7.0.
- **When:** 2026-11-25T13:07:06+00:00

## D029 (build): I chose to install dependencies via pip install -r requirements.txt so unit tests can run in this environment.

- **Instead of:** Do not install dependencies and skip running tests; pip install -r requirements.txt then run pytest
- **Because:** To verify the sample, tests must run; installing pinned deps from requirements.txt is standard in this environment.
- **Reason came from:** `tool_result`
- **Evidence:** pytest not found on PATH (tool message) and requirements.txt includes pytest; run policy allows pip.
- **When:** 2026-11-25T13:08:19+00:00

## D030 (build): I chose to run seed_data.py against the live cluster using DOCUMENTDB_URI from the environment to create sample collections, indexes, and seed documents for verification.

- **Instead of:** Skip seeding live cluster (only run tests); Run seed_data.py against the live cluster using DOCUMENTDB_URI from environment
- **Because:** The sample must demonstrate creating collections and indexes and inserting sample data; the run environment provides a live cluster and DOCUMENTDB_URI, so it's appropriate to seed it for verification.
- **Reason came from:** `readiness_report`
- **Evidence:** Run environment description: 'A vector-capable Azure DocumentDB cluster ... connection string is in the environment variable DOCUMENTDB_URI' and readiness report instructs to verify against the live cluster.
- **When:** 2026-11-25T13:09:41+00:00
