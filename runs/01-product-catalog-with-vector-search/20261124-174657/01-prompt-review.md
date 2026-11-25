# 1. Prompt review: 01-product-catalog-with-vector-search

**Verdict: sufficient_with_assumptions**

The prompt gives a clear high-level goal (Flask product-catalog with vector search) and the key implementation pieces (use text-embedding-ada-002, store embeddings as BSON binary, create a vector-ivf index, expose /search returning top-10). Many implementation defaults (Python/runtime versions, driver version, where to run — local vs cloud, secrets, sample data shape/size, index tuning, run instructions, definition-of-done) are not specified but can be sensibly assumed or supplied by the installed skills (notably documentdb-vector-search, documentdb-driver, documentdb-local-deployment). The build can start but will require the builder to pick reasonable defaults for the missing items listed below.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 2: Goal and scenario, App surface |
| Covered by a skill | 1: Queries and indexes |
| Ambiguous: builder will guess | 7: Workflow type, Language and runtime, Driver and version, Target service and tier, Data model, AI components, Provisioning and deployment |
| Missing: builder will guess | 6: Authentication and secrets, Sample data, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

None flagged, or no reference file was supplied.

## Questions for the prompt author

- Should the sample provision a real Azure DocumentDB cluster (and include Bicep/az/Terraform) or target local development only (DocumentDB Gateway Docker)?
- Which Python runtime and pinned package versions should be used (e.g., Python 3.10, pymongo 4.x, Flask 2.x, openai SDK version)?
- Which provider/SDK should be used for embeddings — OpenAI's API (openai python package) is assumed — and is text-embedding-ada-002 acceptable given any rate/usage limits?
- Do you want a bundled seed dataset (and roughly how many products) or instructions to load a user-provided dataset? Any licensing constraints?
- Any preferred IVF index tuning parameters (nlist/nprobe or other vector-index params) or should the implementer use reasonable defaults from the documentdb-vector-search skill?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | build a Python Flask app with a product catalog stored in DocumentDB ... expose a /search endpoint ... top 10 semantically similar products | - | - | - |
| Workflow type | ambiguous | no | "Using the DocumentDB skill" | - | Single-agent sample: a single code-generating agent / developer producing a self-contained Flask app (no multi-agent orchestration or special agent framework). | Prompt implies use of DocumentDB-related skills but does not specify an agent framework or orchestration. |
| Language and runtime | ambiguous | no | build a Python Flask app | - | Target Python 3.10 (or 3.11) runtime and Flask 2.x (e.g., Flask>=2.0). Provide a requirements.txt and Dockerfile for Python 3.10 as an optional deliverable. | Prompt names language and framework but not versions. |
| Driver and version | ambiguous | no | - | documentdb-driver | Use the official PyMongo driver (pymongo) 4.x (latest stable), with recommended singleton MongoClient patterns per the documentdb-driver skill. | Skill offers best-practices but does not pick a concrete pinned version; builder will pick a recent 4.x release. |
| Target service and tier | ambiguous | no | DocumentDB | documentdb-local-deployment, documentdb-azure-deployment | Sample will target local development by default (DocumentDB Gateway docker image on port 10260) and provide instructions to switch to a cloud DocumentDB cluster via an env-provided connection string if the user wants to deploy to Azure. | Prompt does not say whether to provision cloud resources; skills exist for either path. |
| Authentication and secrets | missing | no | - | documentdb-mcp-setup, documentdb-connection | Secrets stored in environment variables (.env): MONGODB_URI (or DOCUMENTDB_URI) for the DB connection and OPENAI_API_KEY (or equivalent) for embeddings. The app reads these from env or a .env file; no managed identity is configured. | The prompt does not specify auth mechanism or secret location. |
| Data model | ambiguous | no | product catalog ... Embed product titles and descriptions ... store them as BSON binary vectors | documentdb-data-modeling | Database: product_catalog (or products_db); Collection: products. Document fields: _id, title, description, price, category, metadata, embedding (BSON binary float32 array). The embedding field is used for vector search; documents are small (well under 16MB). | Prompt requires embeddings and basic product fields but doesn't specify exact schema or field names. |
| Sample data | missing | no | - | documentdb-local-deployment | Include a small seed dataset (e.g., 10–50 synthetic/example products) bundled in data/seed.json and a loader script to insert them and compute/store their embeddings. No external licensed dataset is required. | Prompt does not provide data source, size, or loader details. |
| Queries and indexes | covered_by_skill | no | create a vector-ivf index | documentdb-vector-search, documentdb-indexing | Builder will create a vector index of type IVF (vector-ivf) on the embedding field with reasonable defaults (e.g., nList/nProbe tuned for sample size — nlist=100, or use the documentdb-vector-search recommended defaults). Also include a standard index on _id and any filterable fields used in results. | The skills cover vector-index choices and tradeoffs; exact IVF params must be chosen by the implementer. |
| AI components | ambiguous | no | Embed product titles and descriptions using text-embedding-ada-002 ... embed it | - | Use OpenAI's text-embedding-ada-002 via the openai Python client. Assume embedding dimension 1536 (text-embedding-ada-002). Embeddings are computed at ingestion and on each /search request. | Model name is given but provider, dimensions, and API client are not specified explicitly. |
| App surface | specified | no | a Python Flask app ... expose a /search endpoint that takes a natural language query ... returns the top 10 | - | The sample will provide a Flask app with at least a GET or POST /search endpoint accepting JSON {"query": "..."} and returning JSON with top-10 product documents and similarity scores. | Main endpoint and behavior are specified; other routes are up to implementer. |
| Provisioning and deployment | ambiguous | no | - | documentdb-azure-deployment, documentdb-local-deployment | Do not provision cloud resources by default. Provide instructions for both local dev (Docker gateway) and optional Bicep/az CLI snippets (via documentdb-azure-deployment skill) if the user wants to deploy a real Azure DocumentDB cluster. | Prompt does not authorize creating cloud resources. |
| Run and test instructions | missing | no | - | - | Provide README with steps: pip install -r requirements.txt; set env vars MONGODB_URI and OPENAI_API_KEY (or run docker gateway); python app.py (or flask run); example curl POST to /search demonstrating expected JSON response. | Necessary for a usable sample but not present in the prompt. |
| Definition of done | missing | no | - | - | Definition of done: repository contains working Flask app, seed data loader that stores embeddings, vector-ivf index created, /search returns top-10 semantically similar products for example queries, and README documents how to run locally. | Prompt gives a goal but not explicit acceptance criteria. |
| Constraints and non-goals | missing | no | - | - | Keep sample small and low-cost: prefer local gateway for development; do not include production-grade auth, monitoring, or billing-heavy cloud provisioning. No commercial dataset licensing required. | No cost or scope limits were provided. |
| Repository conventions | missing | no | - | - | Standard simple layout: app.py or src/, requirements.txt, README.md, data/seed.json, scripts/load_data.py, and a LICENSE (e.g., MIT). | Prompt does not specify repo layout or README contents. |
