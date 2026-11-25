# 1. Prompt review: 01-product-catalog-with-vector-search

**Verdict: sufficient_with_assumptions**

The prompt clearly states a Python Flask product-catalog demo that uses embeddings (text-embedding-ada-002), stores vectors as BSON binary, creates a vector-ivf index, and exposes a /search endpoint returning top-10 semantic matches — enough to start building. Many environment, deployment, and implementation details are left to the builder (Python/runtime, driver/version, index hyperparameters, auth/secrets, sample data and run instructions). Installed skills (notably documentdb-vector-search, documentdb-local-deployment, documentdb-driver/connection/data-modeling) will fill many gaps, but the builder will make defaults for runtime, driver version, storage field names, how embeddings are obtained, and local vs cloud provisioning.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 3: Goal and scenario, AI components, App surface |
| Covered by a skill | 1: Queries and indexes |
| Ambiguous: builder will guess | 6: Workflow type, Language and runtime, Driver and version, Target service and tier, Authentication and secrets, Data model |
| Missing: builder will guess | 6: Sample data, Provisioning and deployment, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

None flagged, or no reference file was supplied.

## Questions for the prompt author

- Should the sample run against a local DocumentDB dev gateway (docker) by default, or should the sample provision an Azure DocumentDB cluster (and if so, what tier/region)?
- Which Python runtime should be targeted (3.8, 3.9, 3.10, 3.11)?
- Which MongoDB/Python driver/version do you want pinned (pymongo X.Y)?
- Which similarity metric and vector index hyperparameters do you want (cosine vs L2; IVF params like nlist)?
- Do you require use of OpenAI specifically for embeddings (text-embedding-ada-002) and should we assume embedding dimensionality = 1536?
- Do you want a specific sample dataset source or is a generated/synthetic set acceptable?
- What should the /search response schema look like (full product documents, truncated fields, include scores)?

## Contradictions and missing references

- Prompt says 'Using the DocumentDB skill' (singular). There is no single 'DocumentDB' skill installed; instead multiple documentdb-* skills are available (e.g., documentdb-vector-search, documentdb-driver). The builder will map the request across the relevant installed skills.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | build a Python Flask app with a product catalog stored in DocumentDB... expose a /search endpoint that takes a natural language query, embeds it, and returns the top 10 semantically similar products. | - | - | Clear demo goal and user-visible scenario (product catalog + semantic search). |
| Workflow type | ambiguous | no | Using the DocumentDB skill, build a Python Flask app... | - | Single-agent/no-agent local build (a single coding agent will generate code; no multi-agent orchestration or special agent framework required). | Prompt mentions 'DocumentDB skill' but does not specify an agent framework; builder will assume ordinary single-agent code generation. |
| Language and runtime | ambiguous | no | Python Flask app | - | Target Python 3.10 (or 3.11) runtime; use Flask latest compatible release (Flask >=2.0). | Language is specified but exact Python version and runtime constraints are not. |
| Driver and version | ambiguous | no | - | documentdb-driver | Use the official pymongo driver (pymongo >=4.0; e.g., 4.4.x) with the MongoClient singleton pattern per documentdb-driver guidance. | Prompt doesn't name a driver or version; documentdb-driver skill supplies best-practice usage but not a specific pinned version. |
| Target service and tier | ambiguous | no | DocumentDB | documentdb-local-deployment | Demo will target a local DocumentDB gateway / Docker-based dev instance by default (instructions to swap to a cloud connection string if the user has one). No cloud cluster provisioning unless user asks. | Prompt does not state whether to provision a cloud cluster or run locally; local dev is a reasonable default and supported by an installed skill. |
| Authentication and secrets | ambiguous | no | - | documentdb-security | Use environment variables for secrets: MONGO_URI (connection string) for DocumentDB, and OPENAI_API_KEY (or equivalent) for embeddings. TLS and SCRAM-SHA-256 assumed if connecting remotely. | Prompt doesn't mention how to authenticate or where secrets live; skills can provide best practices but builder must pick a default. |
| Data model | ambiguous | no | product catalog | documentdb-data-modeling | One database with a 'products' collection. Each document: {_id, title, description, price, metadata, embedding} where 'embedding' stores the vector as BSON binary (field name 'embedding'). | Prompt gives only high-level data domain; exact schema, field names and optional fields are left to the implementer (documentdb-data-modeling can guide choices). |
| Sample data | missing | no | - | documentdb-local-deployment | Provide a small seed JSON (e.g., 50–200 synthetic sample products) included in repository under data/sample_products.json and a script to load them; no external licensed dataset used. | Prompt does not indicate source, size, or loading mechanism for sample data — builder will add a small generated dataset for demo purposes. |
| Queries and indexes | covered_by_skill | no | store them as BSON binary vectors, create a vector-ivf index | documentdb-vector-search | Index field named 'embedding'; use an IVF vector index with reasonable defaults (e.g., nlist=100) and cosine similarity (normalize vectors) unless the skill suggests other defaults. Search will use an ANN query to retrieve top-10 and then optionally rerank by exact distance if needed. | Prompt specifies vector storage and vector-ivf index but leaves hyperparameters and similarity metric unspecified; documentdb-vector-search skill provides guidance to pick sensible defaults. |
| AI components | specified | no | Embed product titles and descriptions using text-embedding-ada-002 | - | Use OpenAI's text-embedding-ada-002 model; assume embedding dimension 1536 and call it when importing/ingesting products and when handling /search queries. | Model name is explicit; the prompt doesn't state provider or dimension, so builder will assume OpenAI and ada-002's standard dims (1536). |
| App surface | specified | no | Python Flask app... expose a /search endpoint that takes a natural language query... returns the top 10 semantically similar products. | - | Return JSON array of up to 10 product documents with relevance scores; accept POST or GET with parameter 'q' (query text) in JSON or query string. | Endpoint and behavior are specified; exact request/response schema is not, but defaults are obvious. |
| Provisioning and deployment | missing | no | - | documentdb-azure-deployment | No cloud provisioning by default; include local run instructions and optionally include a Bicep/az CLI example (commented) to deploy cloud resources if the user chooses to. | Prompt does not request creation of cloud resources; skill exists to provision but builder must decide whether to use it. |
| Run and test instructions | missing | no | - | - | README will include pip install -r requirements.txt, set MONGO_URI and OPENAI_API_KEY, run 'flask run' or 'python app.py', and example curl command to test /search; simple smoke test checks HTTP 200 and JSON with <=10 results. | Prompt omits run/test steps; builder will add basic instructions. |
| Definition of done | missing | no | - | - | Done when the Flask app runs locally, products can be ingested with embeddings, an IVF vector index is created, and a /search request returns up to 10 semantically relevant product documents in JSON. | No explicit acceptance criteria provided; builder will invent straightforward demo criteria. |
| Constraints and non-goals | missing | no | - | - | Treat this as a demo: not production hardened (no full RBAC, no CMK, minimal logging); avoid provisioning expensive cloud resources by default. | Prompt doesn't mention cost, licensing, or compliance constraints; builder will assume demo-scoped non-goals. |
| Repository conventions | missing | no | - | - | Standard layout: app.py (or src/), requirements.txt, README.md, data/sample_products.json, scripts/load_data.py, and an examples/ curl commands file. | No repo layout guidance provided; builder will follow common minimal conventions. |
