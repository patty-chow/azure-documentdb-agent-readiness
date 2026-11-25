# 1. Prompt review: 13-product-q-a-chatbot-rag

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines the core goal: a Python LlamaIndex RAG chatbot that stores chunk embeddings in Azure DocumentDB and retrieves top-5 chunks for grounded answers. The installed DocumentDB skills (notably vector-search, connection, and driver guidance) cover many operational choices, but several concrete details are left to the builder (embedding + chat model, exact data/collection shape, seed data, README/run/test infra). The build can start, but the implementer will make several visible assumptions.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 3: Goal and scenario, Workflow type, Target service and tier |
| Covered by a skill | 3: Driver and version, Authentication and secrets, Queries and indexes |
| Ambiguous: builder will guess | 3: Language and runtime, Data model, App surface |
| Missing: builder will guess | 7: Sample data, AI components, Provisioning and deployment, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- The connection string and model credentials come from environment variables; none appear in the repository. (Partially covered: DOCUMENTDB_URI is mentioned in skill_md; model credentials are unspecified in prompt.)
- A `.env.example` lists every setting with placeholder values. (Prompt didn't request this explicitly.)
- The vector index dimensions match the embedding model's output. (Embedding model not specified; index dims at risk.)
- The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. (Prompt asks for vector index but not parameter choices or README guidance.)
- One database client is created and reused across requests. (Skills recommend singleton client, but prompt doesn't require it explicitly; implementer must apply driver guidance.)
- A seed script loads sample data and creates the index, and can be run twice without duplicating data. (Prompt asks to index docs but gives no idempotency requirement.)
- /search returns a clear error for an empty query and when the embedding call fails. (Error-handling behavior not specified.)
- Search results include the similarity score. (Prompt asks to retrieve top 5 but not to return scores.)
- Dependencies are pinned in `requirements.txt`. (Prompt does not say pinned or unpinned.)
- Unit tests run without a live cluster. (Prompt doesn't require tests or mock-based unit tests.)
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. (Prompt expects using existing cluster; infra-as-code not requested.)
- The README covers what the sample shows, prerequisites, setup, run, and clean-up. (Prompt doesn't specify README contents.)
- The sample uses the name "Azure DocumentDB" throughout. (Prompt says DocumentDB but does not enforce naming conventions in docs.)

## Questions for the prompt author

- Which embedding model and dimensions should the sample use (provider and model name)? This determines the vector index `dimensions`.
- Which LLM provider/model should be used for answer generation (OpenAI, local Llama, etc.)? Do you want provider credentials illustrated via .env.example?
- Should the sample provide a CLI REPL only, or also a minimal HTTP endpoint (FastAPI) for chat?
- Do you want an infra IaC artifact (Bicep/Terraform) included in the repo, or should the sample explicitly avoid creating cluster resources and rely on the provided cluster?
- Is there a preferred format/source for sample product data, or should the builder synthesize small sample JSON?

## Contradictions and missing references

- Prompt says "Using the DocumentDB skill" but there is not a single skill named exactly "DocumentDB"; instead multiple documentdb-* skills are installed (vector-search, connection, driver, etc.). This is a mild mismatch but workable because relevant skills exist.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python LlamaIndex RAG chatbot that indexes product descriptions, specs, and reviews into a DocumentDB vector store" | - | - | Clear business problem and what sample demonstrates (RAG on product docs using Azure DocumentDB). |
| Workflow type | specified | no | "build a Python LlamaIndex RAG chatbot" (single-app RAG pipeline) | - | - | Implies a single-agent single-process sample (no multi-agent orchestration requested). |
| Language and runtime | ambiguous | no | "Python LlamaIndex" | documentdb-local-deployment | Use Python 3.10+ (the system environment has Python; implement using a venv, test against Python 3.10 or 3.11). | Prompt names Python but gives no version; skill_md says python/pip are available in the run environment but not the exact interpreter version. |
| Driver and version | covered_by_skill | no | - | documentdb-connection / documentdb-driver | Use PyMongo (pymongo >= 4.x) and follow singleton MongoClient pattern; for async code use PyMongo AsyncMongoClient (4.9+). | Installed skills prescribe singleton client and connection patterns; they don't force an exact PyMongo minor version but indicate recent PyMongo (4.9+) for async. |
| Target service and tier | specified | no | "DocumentDB" and skill_md: cluster already provisioned; compute tier M30, MongoDB 7.0 wire, DiskANN/HNSW/IVF available, DOCUMENTDB_URI env var | - | - | The provided run-environment (skill_md) states the live cluster and tier to use (M30). |
| Authentication and secrets | covered_by_skill | no | - | documentdb-connection | Read connection string from DOCUMENTDB_URI env var; TLS required, SCRAM-SHA-256 auth. Do not write secrets to repo; provide .env.example with placeholders. | documentdb-connection and the run-environment note instruct reading DOCUMENTDB_URI from env and TLS/SCRAM expectations. |
| Data model | ambiguous | no | "indexes product descriptions, specs, and reviews into a DocumentDB vector store" | documentdb-data-modeling | Create a single database `sample_retail_13` (as required by skill_md) and one collection `products` where documents include: product_id, title, description, specs (object), reviews (array). Store chunks as separate documents or subdocuments with fields: chunk_id, product_id, chunk_text, embedding (float array), metadata. Use no custom shard key (single-shard collection). | Prompt asks only for indexing product docs; it does not specify exact collection names or whether chunks are separate documents vs embedded subdocuments—builder will pick a sensible schema informed by documentdb-data-modeling. |
| Sample data | missing | no | "product descriptions, specs, and reviews" (no source or sample set specified) | - | Include a small synthetic sample dataset in data/sample_products.json (10–50 products with descriptions/specs/reviews) and provide a seed script that inserts/upserts these documents. | Prompt does not provide a data source, license, or size; the builder will need to create or vendor small sample data. |
| Queries and indexes | covered_by_skill | no | "retrieve the top 5 relevant chunks" and "indexes ... into a DocumentDB vector store" | documentdb-vector-search / documentdb-indexing | Create a cosmosSearch vector index on the `embedding` field (choose subtype per data size; e.g., `vector-diskann` for M30 and larger sets). Use cosine similarity or inner-product consistent with chosen embedding normalization. Also create basic metadata indexes (e.g., product_id) as needed. | Installed vector-search skill contains the rules to create appropriate cosmosSearch vector indexes and to query with `$search` + `cosmosSearch`. |
| AI components | missing | no | "LlamaIndex RAG" (no embedding model or LLM provider/dimensions specified) | - | Use an embedding model and LLM that are commonly used with LlamaIndex in Python, e.g., OpenAI text-embedding-3-small (1536 dims) for embeddings and OpenAI gpt-4o-mini or a local Llama-compatible model for generation. Ensure index `dimensions` match the chosen embedding model output and document this choice in README/.env.example. | Prompt names LlamaIndex but gives no embedding/LLM model or provider; this will materially affect index dimensions and sample code (credentials, API calls). |
| App surface | ambiguous | no | "Accept user questions interactively and return the generated answer (e.g. a chat loop or chat endpoint)" | - | Implement a simple CLI REPL chat loop (python app.py) for interactive queries and optionally provide a minimal HTTP /search endpoint (Flask/FastAPI) behind a flag. Inputs: user text; Outputs: grounded answer plus list of retrieved chunk ids and similarity scores. | Prompt allows either CLI or endpoint; builder will pick CLI REPL for simplicity unless asked otherwise. |
| Provisioning and deployment | missing | no | - | documentdb-azure-deployment | Do not provision a new cluster in the sample; use the provided live cluster. Optionally include an IaC example (Bicep) in `infra/` as a non-executed reference template, but do not run it during sample verification per run-environment constraints. | Prompt did not ask to create infra; a separate skill exists to do so, but the run-environment instructs to use the existing cluster. |
| Run and test instructions | missing | no | - | - | Provide README with commands: python -m venv .venv; pip install -r requirements.txt; copy .env.example to .env and fill DOCUMENTDB_URI + MODEL keys; python seed.py; python app.py (REPL). Include basic success criteria: seeding created X documents, a sample query returns an answer and shows 5 chunks. | Prompt asks for interactive behavior but leaves out concrete run commands and test expectations. |
| Definition of done | missing | no | - | - | Definition of done: repo contains working Python code that seeds sample data and index, starts an interactive chat that returns grounded answers for queries (retrieves top-5 chunks), respects token-limit context engineering, and includes README and .env.example. | No explicit acceptance criteria provided in the prompt. |
| Constraints and non-goals | missing | no | - | - | Keep sample small and low-cost (small seed dataset, single collection). Do not provision new clusters or enable production HA. Mention cost and non-goals in README. | No cost, licensing, or other constraints were provided. |
| Repository conventions | missing | no | - | - | Use conventional layout: README.md, requirements.txt (pinned deps), app/, data/, infra/ (optional), tests/ with unit tests that mock DocumentDB, .env.example, and seed.py. Use 'Azure DocumentDB' terminology in docs. | Prompt does not require any particular repo layout or naming policies. |
