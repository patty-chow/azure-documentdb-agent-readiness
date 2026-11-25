# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 6 |
| model_default | 2 |
| operator | 1 |
| readiness_report | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T11:19:39+00:00

## D002 (build): I chose Python 3.11 (via the `python` on PATH) with PyMongo and LangChain for the agent.

- **Instead of:** Use Node.js/Typescript; Use Python 3.10+ with pymongo and LangChain
- **Because:** Python is specified by the prompt review assumptions and is appropriate for LangChain and PyMongo; it matches the available environment.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use Python 3.10 or 3.11' and 'Use PyMongo (the official Python MongoDB driver)'.
- **When:** 2026-11-25T11:20:05+00:00

## D003 (build): I chose PyMongo 4.x (the current stable 4+ series) as the MongoDB driver.

- **Instead of:** PyMongo 3.x; PyMongo 4.x (recent)
- **Because:** PyMongo 4.x is the current stable driver and supports MongoDB 7+ features and db.command used for createIndexes, plus it integrates well with LangChain code in Python.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use PyMongo (the official Python MongoDB driver) at a recent stable 4.x release'
- **When:** 2026-11-25T11:20:08+00:00

## D004 (build): I chose to read the cluster connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Read connection string from code (hard-code); Read connection string from environment variable DOCUMENTDB_URI
- **Because:** Never write secrets into files; using env var follows the run environment guidance and sample constraints.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report and skill_md: 'Read the cluster connection string from DOCUMENTDB_URI (env) and pass it to pymongo.MongoClient(uri)'.
- **When:** 2026-11-25T11:20:12+00:00

## D005 (build): I chose not to provision cloud resources and to use the pre-existing DocumentDB cluster as stated in the run environment.

- **Instead of:** Provision new Azure DocumentDB cluster via Bicep/az/terraform; Use the pre-existing cluster and do not provision resources
- **Because:** Run policy forbids creating cloud resources in this sample and a cluster is already present; the sample should use it.
- **Reason came from:** `prompt`
- **Evidence:** Skill_md: 'This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable.'
- **When:** 2026-11-25T11:20:15+00:00

## D006 (build): I chose a two-collection data model: 'customers' and 'transactions'.

- **Instead of:** Single collection with embedded transactions; Two collections: 'customers' and 'transactions'
- **Because:** This separation is common for RFM pipelines and matches the prompt's assumed data model; allows aggregation over transactions grouped by customer.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Create two collections: `customers` and `transactions`'
- **When:** 2026-11-25T11:20:18+00:00

## D007 (build): I chose OpenAI 'text-embedding-3-small' (1536 dimensions) for embeddings and to document required env vars OPENAI_API_KEY and OPENAI_EMBEDDING_MODEL.

- **Instead of:** OpenAI text-embedding-3-large (3072 dims); OpenAI text-embedding-3-small (1536 dims); Azure OpenAI equivalent
- **Because:** text-embedding-3-small is cost-effective for a sample app, widely available, and 1536 dims is a common dimensionality; embedding dimensionality must match vector index dimensions.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review recommended OpenAI models; readiness report noted embedding model/dimensions missing and must be chosen before creating the vector index.
- **When:** 2026-11-25T11:20:27+00:00

## D008 (build): I chose to use LangChain with OpenAI for embeddings and OpenAI LLM for narrative generation (configurable via env vars).

- **Instead of:** Use LangChain with OpenAI provider for embeddings/LLM; Use a local embedding/LLM
- **Because:** LangChain provides a small, readable agent pattern and integrates with OpenAI for both embeddings and LLM calls; it's suitable for a sample app.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use OpenAI embeddings via LangChain... Use an LLM (OpenAI GPT-4o-mini or gpt-4.1) via LangChain'.
- **When:** 2026-11-25T11:20:30+00:00

## D009 (build): I chose to provide a CLI script (`run_agent.py`) as the primary interface and include an optional FastAPI snippet in README for demonstration only.

- **Instead of:** Provide only a library API; Provide a CLI + optional FastAPI endpoint
- **Because:** A CLI keeps the sample simple to run in CI and locally; FastAPI is optional and documented for extension.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Provide a CLI script (`run_agent.py`) that runs the LangChain agent... include an optional minimal FastAPI `/search` endpoint example'.
- **When:** 2026-11-25T11:20:33+00:00

## D010 (build): I chose to seed 200 synthetic customers and associated transactions for the sample.

- **Instead of:** Seed ~1000 customers; Seed ~200 customers (smaller)
- **Because:** Keeps runtime and storage small while still demonstrating aggregation and vector search behavior; easier for local runs and CI.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review suggested ~1k but cost concern and run-time favor a smaller dataset.
- **When:** 2026-11-25T11:20:36+00:00
