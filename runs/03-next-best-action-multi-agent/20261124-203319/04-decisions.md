# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 8 |
| model_default | 4 |
| readiness_report | 4 |
| operator | 2 |
| skill | 2 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T11:14:27+00:00

## D002 (build): I chose Python 3.10+ (use the system 'python' virtualenv) as the language/runtime for the sample.

- **Instead of:** Node.js; Python
- **Because:** Python is well-supported for LangChain and PyMongo; the run environment already has python and pip available.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Builder will target Python 3.10 or 3.11 (common current defaults) and a virtualenv where `python` and `pip` already point to that interpreter (skill_md indicates python/pip are available).
- **When:** 2026-11-25T11:15:04+00:00

## D003 (build): I chose pymongo (PyMongo 4.x) as the MongoDB driver and will implement a singleton MongoClient per the documentdb-driver guidance.

- **Instead of:** motor (async); pymongo (sync); PyMongo async client
- **Because:** PyMongo is the standard synchronous driver and matches the simple sample app flow; singleton pattern avoids connection churn.
- **Reason came from:** `skill`
- **Evidence:** Readiness_report and documentdb-driver skill: 'Reuse MongoClient as a process-wide singleton'.
- **When:** 2026-11-25T11:15:07+00:00

## D004 (build): I chose to read the cluster connection string from the environment variable DOCUMENTDB_URI at runtime and never write secrets to files.

- **Instead of:** Use Azure Entra/managed identity; Read connection string from env var DOCUMENTDB_URI; Prompt user for credentials interactively
- **Because:** Environment variables are secure for samples and required by prompt constraints (no secrets in repo).
- **Reason came from:** `prompt`
- **Evidence:** Readiness_report and skill_md: 'Read the cluster connection string from DOCUMENTDB_URI' and 'Never write a secret... Read them from environment variables'.
- **When:** 2026-11-25T11:15:11+00:00

## D005 (build): I chose OpenAI text-embedding-3-small with 1536 dimensions for embeddings as the default for the sample, documented and used when OPENAI_API_KEY is provided.

- **Instead of:** OpenAI text-embedding-3-small (1536); OpenAI text-embedding-3-large (3072); Other provider
- **Because:** 1536 is common for OpenAI embedding models and matches the readiness_report assumption; it's a reasonable default for the sample and easy to document.
- **Reason came from:** `model_default`
- **Evidence:** Readiness_report: 'Assume 1536 dims unless a different embedding is selected.' No skill prescribes the provider or model.
- **When:** 2026-11-25T11:15:14+00:00

## D006 (build): I chose to make LLM usage optional: use OpenAI (model gpt-4o-mini) when OPENAI_API_KEY is provided; otherwise run deterministic heuristic agents so the sample runs without LLM credentials.

- **Instead of:** Require LLM (OpenAI) for agents; Make LLM optional and fall back to deterministic heuristics
- **Because:** This keeps the sample runnable without paid API keys yet shows how to integrate LangChain when keys are available.
- **Reason came from:** `model_default`
- **Evidence:** Readiness_report gap: 'LLM choice and credentials not prescribed; builder decision required.'
- **When:** 2026-11-25T11:15:17+00:00

## D007 (build): I chose to create standard MongoDB indexes via the seed script and create the vector `cosmosSearch` index during verification using the documentdb MCP server's documentdb_create_index tool.

- **Instead of:** Create vector index via driver (db.command); Use documentdb MCP server to create cosmosSearch vector index; Skip vector index creation
- **Because:** The MCP tool is the authoritative, service-specific way to create DocumentDB vector indexes and avoids driver-specific admin command issues in the sample code.
- **Reason came from:** `skill`
- **Evidence:** Readiness_report guidance: 'Create vector indexes using the `cosmosSearch` index kind and `cosmosSearchOptions`' and availability of the documentdb MCP server.
- **When:** 2026-11-25T11:15:23+00:00

## D008 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T11:19:04+00:00

## D009 (build): I chose Python (3.10/3.11 compatible) as the language and runtime for the sample.

- **Instead of:** Node/TypeScript; Python 3.10+ (virtualenv)
- **Because:** The existing repository is Python-based and runtime availability was confirmed in the readiness report; Python is the natural choice for LangChain examples.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Builder will target Python 3.10 or 3.11 (common current defaults) and a virtualenv where `python` and `pip` already point to that interpreter (skill_md indicates python/pip are available).
- **When:** 2026-11-25T11:19:44+00:00

## D010 (build): I chose PyMongo (pymongo >=4.5.0) as the MongoDB driver and will implement MongoClient as a singleton.

- **Instead of:** pymongo 3.x; pymongo 4.x
- **Because:** PyMongo is the official driver and the repo's requirements.txt already pins pymongo>=4.5.0; singleton pattern avoids connection exhaustion per driver guidance.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use PyMongo (the official Python MongoDB driver), e.g. pymongo 4.x (latest stable compatible with MongoDB 7.x); implement MongoClient as a process-wide singleton per documentdb-driver guidance.'
- **When:** 2026-11-25T11:19:46+00:00

## D011 (build): I chose to read the DocumentDB connection string and model API keys from environment variables (DOCUMENTDB_URI, OPENAI_API_KEY).

- **Instead of:** Store secrets in files; Read secrets from environment variables
- **Because:** Security constraint: never write secrets to files; environment variables are standard for samples and the repo already expects them.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report guidance: 'Read the cluster connection string from DOCUMENTDB_URI' and repo .env.example contains placeholders.
- **When:** 2026-11-25T11:19:49+00:00

## D012 (build): I chose NOT to provision any Azure resources and to use the existing DocumentDB cluster referenced by DOCUMENTDB_URI.

- **Instead of:** Provision a new cluster using Bicep/Terraform; Do not provision (use existing cluster)
- **Because:** Provisioning is disallowed by policy and an existing cluster is provided by the run environment; use that cluster for verification.
- **Reason came from:** `readiness_report`
- **Evidence:** Run environment: 'A vector-capable Azure DocumentDB cluster ... is reachable from this machine. Its connection string is in the environment variable DOCUMENTDB_URI.' Also run_policy: Azure resource changes allowed: False.
- **When:** 2026-11-25T11:19:52+00:00

## D013 (build): I chose a simple sample data model: collections interactions, preferences, nba_recommendations with fields documented in README and implemented in seed.py.

- **Instead of:** Design a large, production schema; Keep a small, simple schema for examples
- **Because:** Keeps the sample readable and focused for learning while matching the prompt's suggested collections.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: recommended collections and fields (interactions, preferences, nba_recommendations).
- **When:** 2026-11-25T11:19:58+00:00

## D014 (build): I chose OpenAI text-embedding-3-small (embedding dims 1536) as the embedding model for the sample.

- **Instead of:** Use OpenAI text-embedding-3-small 1536-dim; Use a different embedding model
- **Because:** Common default, matches .env.example, and vector index dimensions in DocumentDB must match the embedding dims per documentdb-vector-search guidance.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Builder will use common defaults: OpenAI embeddings (text-embedding-3-small / 1536-dim)'. .env.example sets EMBEDDING_MODEL=text-embedding-3-small and EMBEDDING_DIMS=1536.
- **When:** 2026-11-25T11:20:01+00:00

## D015 (build): I chose to design agents to run deterministically without requiring an LLM, while supporting optional OpenAI LLM/embeddings when OPENAI_API_KEY is set.

- **Instead of:** Use specific LLM (e.g., gpt-4o-mini); Use heuristic deterministic agents without LLM
- **Because:** Ensures the sample runs in environments without API keys while allowing extension to LLM-based agents when keys are available.
- **Reason came from:** `model_default`
- **Evidence:** Repo files: agents.py indicates heuristics if OPENAI_API_KEY not present. Readiness report: AI model choice is a gap and must be documented; .env.example sets LLM_MODEL=gpt-4o-mini.
- **When:** 2026-11-25T11:20:04+00:00

## D016 (build): I chose to create standard MongoDB indexes via the seed.py script (pymongo) and to create/verify the vector index using the documentdb MCP server tools during verification.

- **Instead of:** Create vector index via pymongo driver; Create vector index via MCP server documentdb_create_index tool
- **Because:** The seed script can run idempotently across Mongo drivers; vector-index creation requires provider-specific options better handled via MCP server tool for correct cosmosSearchOptions settings.
- **Reason came from:** `readiness_report`
- **Evidence:** seed.py currently creates non-vector indexes; readiness guidance: 'Vector index is created separately during verification.' documentdb-vector-search skill documents vector index creation specifics.
- **When:** 2026-11-25T11:20:06+00:00

## D017 (build): I chose to install Python dependencies from requirements.txt using pip.

- **Instead of:** Skip installing dependencies; Install dependencies from requirements.txt
- **Because:** To run seed script, demo and tests we need dependencies installed in the virtualenv.
- **Reason came from:** `model_default`
- **Evidence:** Repository contains requirements.txt listing pymongo, langchain, fastapi, openai, etc. The run environment allows pip.
- **When:** 2026-11-25T11:20:19+00:00

## D018 (build): I chose to run seed.py to populate sample data and standard non-vector indexes in sample_customer_360_03.

- **Instead of:** Do not seed database; Run seed.py to create sample data and indexes
- **Because:** To verify app behavior and to have data for agent heuristics and NBA writes.
- **Reason came from:** `prompt`
- **Evidence:** seed.py present and README instructs to run it; seed script creates indexes and synthetic data for interactions and preferences.
- **When:** 2026-11-25T11:20:26+00:00

## D019 (build): I chose to run the demo CLI (python main.py --demo) to generate and write an NBA recommendation for cust_001.

- **Instead of:** Do not run demo; Run demo via python main.py --demo to generate NBA for cust_001
- **Because:** To verify orchestrator writes nba_recommendations to database and demonstrate sample output.
- **Reason came from:** `prompt`
- **Evidence:** main.py supports --demo; README suggests running demo after seeding.
- **When:** 2026-11-25T11:21:02+00:00

## D020 (build): I chose to create a cosmosSearch vector-diskann index on sample_customer_360_03.interactions.embedding with dimensions=1536 and similarity COS (maxDegree=32, lBuild=50).

- **Instead of:** Skip vector index creation; Create a vector-diskann index on interactions.embedding with dimensions=1536
- **Because:** To enable vector search compatibility with embeddings chosen and to demonstrate vector-index creation using MCP tooling; dimensions must match embedding model.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report & documentdb-vector-search skill: 'Create a `vector-diskann` index with correct `dimensions`, `similarity`, `maxDegree`, and `lBuild`' and .env.example sets EMBEDDING_DIMS=1536.
- **When:** 2026-11-25T11:21:27+00:00

## D021 (build): I tried to create the vector index with documentdb_create_index but the MCP call failed; I chose to stop retrying and to document the vector-index creation steps in README and leave the index creation unverified.

- **Instead of:** Retry documentdb_create_index; Do not create vector index programmatically and document steps in README
- **Because:** Tool failure occurred; per build instructions, stop retrying after second attempt and take another route. Creating the vector index requires MCP or direct admin commands; documenting steps preserves reproducibility without risking further tool errors.
- **Reason came from:** `tool_result`
- **Evidence:** documentdb_create_index returned: 'Error: Function failed.' when called to create the vector-diskann index.
- **When:** 2026-11-25T11:21:35+00:00
