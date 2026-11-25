# 1. Prompt review: 05-churn-prediction-pipeline

**Verdict: sufficient_with_assumptions**

The starter prompt gives a clear high-level goal (Python LangChain agent that computes RFM, embeds vectors, stores them in a DocumentDB vector index, retrieves similar churned profiles, and generates narrative/actions). The run environment (live cluster, database name, and an instruction to read DOCUMENTDB_URI from env) in skill_md fills several infra details. Several important implementation choices are left unspecified (Python version, embedding model & dims, exact data model, app surface, seed/idempotency, tests, IaC), so the builder will make reasonable defaults using installed skills for guidance.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 4: Goal and scenario, Workflow type, Target service and tier, Authentication and secrets |
| Covered by a skill | 2: Queries and indexes, Repository conventions |
| Ambiguous: builder will guess | 4: Language and runtime, Driver and version, Data model, App surface |
| Missing: builder will guess | 6: Sample data, AI components, Provisioning and deployment, Run and test instructions, Definition of done, Constraints and non-goals |
| Not applicable | 0: - |

## Reference requirements at risk

- The connection string and model credentials come from environment variables; none appear in the repository. (Partially covered by skill_md for DOCUMENTDB_URI, but embedding/model creds not specified.)
- A `.env.example` lists every setting with placeholder values. (skill_md requests `.env.example` but the starter prompt doesn't; builder will probably add it, but not explicit.)
- The vector index dimensions match the embedding model's output. (Embedding model/dims not specified — high risk.)
- The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. (Index parameters left unspecified; vector skill gives guidance but README detail is not in prompt.)
- A seed script loads sample data and creates the index, and can be run twice without duplicating data. (No seed/idempotency instruction in prompt.)
- /search returns a clear error for an empty query and when the embedding call fails. (Prompt does not specify API surface or error behavior.)
- Search results include the similarity score. (Prompt requests retrieval of most similar churned profiles but doesn't say to return scores; likely omitted unless builder adds it.)
- Dependencies are pinned in `requirements.txt`. (Prompt doesn't mention pinning; often omitted unless specified.)
- Unit tests run without a live cluster. (No testing strategy given; likely missing or mocked tests required but not specified.)
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. (Prompt does not ask for provisioning; skill exists but builder may not include IaC.)
- The README covers what the sample shows, prerequisites, setup, run, and clean-up. (Prompt doesn't require README contents; builder may add, but not guaranteed.)
- The sample uses the name "Azure DocumentDB" throughout. (Prompt says 'DocumentDB' but doesn't mandate consistent naming in README; skill_md uses 'Azure DocumentDB'.)

## Questions for the prompt author

- Which embedding provider and model should the sample use (provider and model name), and what are the embedding dimensions? This determines the vector index dimensions.
- Do you want a runnable HTTP endpoint (e.g., `/search`) as part of the sample, or is a CLI/script demo sufficient?
- Should the sample include IaC to provision the DocumentDB cluster, or must it rely on the pre-provisioned cluster (skill_md suggests a live cluster is already available)?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "compute RFM scores per customer and embed the resulting feature vectors... retrieve the most similar churned customer profiles... generate a churn risk narrative and recommended retention action per customer." | - | - | Business problem, user story and what to demonstrate are clearly stated. |
| Workflow type | specified | no | "a Python LangChain agent with tools" | - | - | Single-agent LangChain workflow is explicit. |
| Language and runtime | ambiguous | no | "Python LangChain" | - | Use Python 3.10 or 3.11 (a modern 3.x runtime available via `python` in the environment). | Python is specified but no explicit version. skill_md implies a dev Python environment exists but not version. |
| Driver and version | ambiguous | no | - | documentdb-driver | Use PyMongo (the official Python MongoDB driver) at a recent stable 4.x release; follow documentdb-driver guidance to reuse a singleton MongoClient. | Prompt doesn't name the driver or version. documentdb-driver covers client usage patterns but does not pick a concrete PyMongo version. |
| Target service and tier | specified | no | "Using the DocumentDB skill" | - | - | skill_md gives explicit run-environment details: a live vector-capable DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN/HNSW/IVF support) and the DB name `sample_customer_360_05`. |
| Authentication and secrets | specified | no | - | - | - | skill_md instructs reading the cluster connection string from environment variable DOCUMENTDB_URI and to never write it into files/logs; that settles where secrets come from. |
| Data model | ambiguous | no | "compute RFM scores per customer" | documentdb-data-modeling | Create two collections: `customers` (customer doc with _id, churn boolean, embedding field, schemaVersion) and `transactions` (each transaction: _id, customer_id, amount, timestamp). RFM aggregation runs on `transactions` grouped by customer_id and upserts RFM + embedding into `customers`. | Prompt requires RFM but does not define collection names or document shape. documentdb-data-modeling provides design guidance but not a concrete schema; the builder will pick a customers + transactions model as most straightforward. |
| Sample data | missing | no | - | documentdb-local-deployment | Include a small synthetic sample (e.g., ~1k customers and their transactions) in a seed script under `scripts/seed.py`, licensed MIT, and the repo includes a note about data provenance. | The prompt and skill_md do not specify data source, size, license, or an explicit seed dataset; documentdb-local-deployment mentions patterns for local sample-data but no concrete dataset. |
| Queries and indexes | covered_by_skill | no | "tools that run DocumentDB aggregations to compute RFM scores... Store embeddings in a DocumentDB vector index and retrieve the most similar churned customer profiles" | documentdb-vector-search, documentdb-indexing | Create a cosmosSearch vector index on a per-customer embedding field with `dimensions` matching chosen embedding model; for M30 prefer `vector-diskann` (or `vector-hnsw` for smaller dev datasets). Also create any single-field indexes needed for churn boolean and customer lookup. Use `$search` + `cosmosSearch` with a pre-filter on churned=true when retrieving similar churned profiles. | Prompt requires vector index and aggregations but leaves specific index type and parameters unspecified; vector/indexing skills provide the choices and tuning guidance the builder will apply. |
| AI components | missing | no | "embed the resulting feature vectors... Use prompt engineering to generate a churn risk narrative" | - | Use OpenAI embeddings (e.g., `text-embedding-3-small` or `text-embedding-3-large`) via LangChain's OpenAI embeddings interface; assume 1536 or 3072 dimensions depending on model chosen and set index `dimensions` accordingly. Use an LLM (OpenAI GPT-4o-mini or gpt-4.1) via LangChain for the narrative prompt template. | No embedding model, dims, provider or chat model is specified. This materially affects the vector index shape and must be decided by the builder or clarified by the author. |
| App surface | ambiguous | no | "build a Python LangChain agent" | - | Provide a CLI script (`run_agent.py`) that runs the LangChain agent for a given customer_id; include an optional minimal FastAPI `/search` endpoint example for demonstration but keep the sample focused on the agent CLI. | Prompt says to build a LangChain agent but does not specify if there should be an API route, CLI, or UI. The reference requirements expect a `/search` endpoint, but it's not in the prompt. |
| Provisioning and deployment | missing | no | - | documentdb-azure-deployment | Do not provision cloud resources in the sample; rely on the pre-existing cluster (as stated in skill_md). If IaC is added, include an optional Bicep sample using documentdb-azure-deployment, but do not run it by default. | Prompt doesn't ask to create a cluster; reference requirements expect IaC but the prompt does not. The documentdb-azure-deployment skill could supply IaC if requested. |
| Run and test instructions | missing | no | - | - | README will include: create virtualenv, pip install -r requirements.txt, copy .env.example to .env and fill DOCUMENTDB_URI and API keys, run `scripts/seed.py`, then `python run_agent.py --customer CUSTOMER_ID`. Tests: `pytest` with environment overrides for offline/unit tests. | No concrete run/test commands are in the prompt or skill_md. |
| Definition of done | missing | no | - | - | Consider done when: (1) agent computes and stores RFM + embedding for a customer, (2) vector index is created with correct dimensions, (3) a retrieval on churned profiles returns k neighbors with scores, and (4) the prompt template produces a narrative and action. | No acceptance criteria explicitly provided in the prompt. |
| Constraints and non-goals | missing | no | - | - | Keep costs low: use small sample data and dev-tier settings; do not provision new cloud infra by default; avoid storing secrets in repo. | No cost/scale constraints or non-goals stated. |
| Repository conventions | covered_by_skill | no | "Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder, as the prompt asks." (skill_md) | - | Include `.env.example`, `requirements.txt` with pinned versions, `README.md` that uses the phrase 'Azure DocumentDB' consistently, `scripts/seed.py`, `src/` for code, and `tests/` for unit tests. Use a singleton MongoClient pattern per documentdb-driver guidance. | skill_md explicitly instructs using `.env.example` placeholders and not writing the connection string; documentdb-driver enforces singleton client usage. However prompt did not enumerate all conventions (pinning deps, README sections). |
