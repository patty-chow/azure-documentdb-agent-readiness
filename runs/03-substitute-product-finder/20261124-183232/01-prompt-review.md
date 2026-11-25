# 1. Prompt review: 03-substitute-product-finder

**Verdict: sufficient_with_assumptions**

The starter prompt clearly specifies the main goal: a Python FastAPI + Beanie sample that stores product documents with OpenAI embeddings in Azure DocumentDB, exposes a /substitute endpoint performing server-side vector search, ingests 10k synthetic products, and serves an artistic retailer-style UI. Several implementation defaults are not specified (Python version, exact embedding model & dims, index parameters, runtime commands, README/tests/requirements pinning). These will be filled by the builder's defaults or by installed skills (notably driver, vector-search and indexing guidance).

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 3: Goal and scenario, Target service and tier, App surface |
| Covered by a skill | 1: Driver and version |
| Ambiguous: builder will guess | 6: Language and runtime, Authentication and secrets, Data model, Sample data, Queries and indexes, AI components |
| Missing: builder will guess | 5: Workflow type, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 1: Provisioning and deployment |

## Reference requirements at risk

- Ingestion script must read the same Azure DocumentDB connection string from the application config file and verify the insert count is 10,000 — prompt asks ingestion script to ingest 10k but doesn't explicitly say the ingestion script must read the same config file and report/assert the count.
- .env.example lists every setting with placeholder values — prompt asks for a config file but does not explicitly request a .env.example; a builder may or may not add one.
- The vector index dimensions match the embedding model's output — prompt requires embeddings but doesn't name model/dimensions; without explicit model the builder must pick a default and ensure index dims match.
- Vector index parameters are chosen for the sample's data size and the README explains how to change them — prompt asks for a vector index but not parameters or README guidance for tuning.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — ingestion script is required, but idempotency and index-creation specifics are not specified.
- /search returns a clear error for an empty query and when the embedding call fails — prompt asks /substitute by product ID (not by text query) and does not require these error cases to be handled.
- Search results include the similarity score — prompt asks for 'closest alternatives' but doesn't explicitly require similarity scores in the JSON response (the reference requirements do); this may be omitted unless builder chooses to include scores.
- Dependencies are pinned in requirements.txt — prompt doesn't demand pinned deps; builder may or may not pin them.
- Unit tests run without a live cluster — no tests requested by prompt; the sample may omit such tests.
- Infrastructure for the cluster is provided as code — prompt assumes an existing cluster; infra-as-code is not requested and may be omitted.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up — prompt does not require a full README; builders sometimes omit detailed README in short samples.

## Questions for the prompt author

- Which OpenAI embedding model should be used (model name) and do you want the sample to pin the embedding dimension accordingly? (e.g., text-embedding-3-small)
- Which Python version should the sample target (3.10, 3.11)?
- Do you want a .env.example included listing DOCUMENTDB_URI and OPENAI_API_KEY placeholders, and should ingestion/read code read the connection string from the same config module?
- Should the sample include pinned requirements.txt and minimal unit tests (mocks) that run without a live cluster, or is that out of scope?

## Contradictions and missing references

- Prompt requests 'Use a config file for the Azure DocumentDB connection string', while the run-environment (skill_md) instructs that the connection string is provided in the environment variable DOCUMENTDB_URI and 'Never write its value into any file, log, README or test fixture'. The builder will likely implement a config/settings module that reads DOCUMENTDB_URI from the environment (and provide .env.example placeholders) to satisfy both, but the wording is potentially confusing.
- Skill/run-environment instructs a specific DB name (sample_retail_03) and that the cluster is already reachable; the prompt does not mention the DB name. This is not a fatal contradiction but is an additional constraint from the run environment that the prompt doesn't state.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | Build a simple Python FastAPI app using Beanie ODM and Azure DocumentDB ... expose a /substitute endpoint that accepts a product ID and returns the 5 closest alternatives by cosine similarity using Azure DocumentDB vector search. | - | - | Prompt states business problem, audience (developer sample) and what the sample should demonstrate. |
| Workflow type | missing | no | - | - | Assume a standard single-agent/no-agent sample (no orchestration or multi-agent framework). The builder will produce a self-contained FastAPI app and scripts. | Prompt does not mention any agent framework or workflow orchestration. This is not blocking. |
| Language and runtime | ambiguous | no | Build a simple Python FastAPI app | - | Assume Python 3.11 (or latest stable 3.10/3.11) and a virtualenv; use uvicorn for running the app. | Prompt gives language/runtime (Python + FastAPI) but not exact Python version or runtime details. |
| Driver and version | covered_by_skill | no | using Beanie ODM | documentdb-driver | Use a Beanie release compatible with Motor/pymongo that supports MongoDB 7.0; use Motor as async driver and reuse a singleton MongoClient per documentdb-driver guidance. | documentdb-driver skill covers MongoDB driver best practices (singleton MongoClient, connection reuse). The prompt doesn't name exact package versions; the skill will guide defaults. |
| Target service and tier | specified | no | Azure DocumentDB | - | Run against the existing vector-capable Azure DocumentDB cluster described in the run environment (compute tier M30, MongoDB 7.0 wire protocol with DiskANN/HNSW/IVF available). Use database name sample_retail_03 per run-environment note. | The included run-environment (skill_md) states the cluster details and the DB name to use. |
| Authentication and secrets | ambiguous | no | Use a config file for the Azure DocumentDB connection string and display a clear error if the connection string is missing or invalid. | - | Implement a config/settings module (e.g., pydantic BaseSettings or python-dotenv) that reads DOCUMENTDB_URI from environment (and loads .env locally). Show a clear, user-friendly error if not set or if connection attempt fails. Never write the secret into repo files — provide .env.example with placeholder only. | Run-environment guidance says DOCUMENTDB_URI is in env and should never be written; the prompt requests a 'config file.' Builder will most likely implement a config that reads env vars, avoiding storing secrets. This mismatch is noted in contradictions. |
| Data model | ambiguous | no | store product JSON documents ... Generate embeddings for product attributes, store the vectors in the database | documentdb-data-modeling | Define a Product document with fields: _id (ObjectId/str), product_id (string), name, description, category, price (numeric), attributes (dict), embedding (List[float]), created_at. Embedding stored as a numeric array field suitable for vector index. Use database sample_retail_03 and a single collection 'products'. | Prompt mandates product docs + embeddings but does not supply full schema. documentdb-data-modeling can guide shape decisions; builder will pick a simple schema as assumed. |
| Sample data | ambiguous | no | The app should include a script to ingest 10,000 product transactions. | - | Generate 10,000 synthetic product documents (e.g., using Faker or deterministic random data). No external dataset/license used. Each generated product gets an OpenAI embedding before insertion. | Prompt requires an ingestion script but doesn't specify source/licence of data; builder will likely synthesize data. |
| Queries and indexes | ambiguous | no | create or declare an Azure DocumentDB vector search index on the document embedding field ... return the 5 closest alternatives by cosine similarity using Azure DocumentDB vector search. | documentdb-vector-search, documentdb-indexing | Create a server-side vector index on the embedding field, with dimensions matching the chosen embedding model (see AI assumptions). Use a reasonable default index type (HNSW or DiskANN depending on cluster capability) and small parameter settings appropriate for 10k vectors. Use createSearchIndexes / createIndex APIs from the vector-search skill guidance. | Prompt requires a vector index but leaves index parameters (index type, dims, lSearch/lBuild, etc.) unspecified. documentdb-vector-search and documentdb-indexing skills will guide defaults. |
| AI components | ambiguous | no | Generate embeddings for product attributes | - | Use OpenAI embedding API, with the API key provided via OPENAI_API_KEY env var. Default model: text-embedding-3-small (assumed dims 1536). Call the embedding API synchronously during ingestion and when computing a query embedding; handle API failures with clear errors. | Prompt specifies OpenAI embeddings but does not name model or env var names. |
| App surface | specified | no | /substitute endpoint that accepts a product ID ... artistic UI to look like an online retailer's website ... include script to ingest 10,000 product transactions. | - | - | Prompt clearly defines API surface (root UI, /substitute) and ingestion script. |
| Provisioning and deployment | not_applicable | no | - | documentdb-azure-deployment | No new cloud resources will be provisioned — the run-environment provides an existing cluster. If provisioning were needed, documentdb-azure-deployment skill would be used. | Prompt and run-environment indicate a reachable cluster exists; the starter prompt does not ask to create infra. |
| Run and test instructions | missing | no | - | - | Provide typical commands: pip install -r requirements.txt, export DOCUMENTDB_URI and OPENAI_API_KEY (or copy .env.example to .env), python scripts/ingest.py (to load 10k), uvicorn app.main:app --reload. No tests were requested; include basic smoke instructions in README. | Prompt asks for code and scripts but does not list CLI commands or test instructions. |
| Definition of done | missing | no | - | - | Accept when: app runs, ingestion script inserts 10,000 documents, / returns retailer UI, /substitute(product_id) returns 5 nearest products from server-side vector search including similarity scores, code reads connection string from config/env and errors clearly on missing/invalid value. | No explicit acceptance criteria provided by prompt; builder will use the above as implied DoD. |
| Constraints and non-goals | missing | no | - | - | Avoid provisioning new paid cloud resources; keep the sample lightweight (10k vectors) to limit cost; do not include secrets in repo. | Prompt doesn't specify cost constraints or compliance limits; builder will prefer minimal-cost approach. |
| Repository conventions | missing | no | Use a config file for the Azure DocumentDB connection string ... Keep the code as simple and readable as possible. | - | Use a conventional layout: app/ (FastAPI code), app/models.py (Beanie models), app/routes.py, scripts/ingest.py, static/ and templates/ for UI, requirements.txt (pinned where feasible), README.md, .env.example, and no secrets checked in. | Prompt requests a config file and comments but doesn't prescribe repo layout, dependency pinning, or README contents. |
