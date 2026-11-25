# 1. Prompt review: 07-customer-review-sentiment-pipeline

**Verdict: sufficient_with_assumptions**

The starter prompt clearly states the goal (an async Python Beanie pipeline that calls OpenAI, enriches reviews, upserts to DocumentDB, and runs an aggregation). It leaves many engineering choices unspecified (Python/runtime versions, OpenAI model and env vars, exact schema, indexes, app surface, seeding, README, tests, infra). The build can start, but the implementer will need to pick sensible defaults for those missing items.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 3: Goal and scenario, Target service and tier, Provisioning and deployment |
| Covered by a skill | 1: Queries and indexes |
| Ambiguous: builder will guess | 4: Language and runtime, Driver and version, Authentication and secrets, AI components |
| Missing: builder will guess | 8: Workflow type, Data model, Sample data, App surface, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- .env.example lists every setting with placeholder values — prompt/skill_md only specify DOCUMENTDB_URI; OpenAI and other env vars are not specified.
- The vector index dimensions match the embedding model's output — the prompt doesn't request embeddings at all; nothing specifies embedding use or vector-dims.
- The vector index parameters are chosen for the sample's data size, and the README says how to change them — indexing parameters are not specified in the prompt.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — prompt does not mention sample data or a seed script.
- /search returns a clear error for an empty query and when the embedding call fails — the prompt doesn't include a search endpoint or error-handling requirements.
- Search results include the similarity score — no search or similarity scoring is requested in the prompt.
- Dependencies are pinned in requirements.txt — the prompt doesn't request exact pins; builder must choose them.
- Unit tests run without a live cluster — no testing strategy is given; building offline-capable unit tests is not implied.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type — the run environment already provides a cluster and the prompt says to use it, so infra-as-code is not requested.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up — the prompt doesn't ask for README contents explicitly; it's at risk of being omitted or underspecified.
- The sample uses the name 'Azure DocumentDB' throughout — the prompt doesn't mandate naming conventions; builder might use 'DocumentDB' or other variants inconsistently.

## Questions for the prompt author

- Do you want the sample to use public OpenAI (openai.com) or Azure OpenAI? This changes the client library, env vars, and model names.
- Should the sample expose an HTTP API (e.g., FastAPI) or just provide a CLI/script to run the pipeline and aggregation?
- Do you want explicit pinned dependency versions and unit tests (that run without a live cluster) included, or are those out of scope for this sample?
- Is it acceptable to assume Python 3.11 and to choose a default OpenAI model (e.g. gpt-3.5-turbo) and an OPENAI_API_KEY env var if you haven't specified them?

## Contradictions and missing references

- "Using the DocumentDB skill" is requested but there is no single installed skill named exactly 'DocumentDB' — there are many documentdb-* skills. Builder will pick relevant skills, but the phrasing is ambiguous.
- The prompt says 'calls OpenAI' but gives no guidance whether to use OpenAI.com or Azure OpenAI; skill_md talks only about DocumentDB and the MCP server and does not cover the OpenAI provider or API keys.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | build an async Python pipeline using Beanie ODM that reads raw product reviews, calls OpenAI to classify sentiment and extract key themes, enriches each document with a sentiment score and tags field, and upserts the result back into DocumentDB. Include a summary aggregation query grouped by product and sentiment. | - | - | Business problem, user-facing goal and the DB-related behaviour are clearly stated. |
| Workflow type | missing | no | - | - | Implement as a single-process async Python application (no agent orchestration framework). The prompt's 'Using the DocumentDB skill' is an instruction to the builder agent, not to embed an agent in the sample. | Prompt doesn't specify single-agent vs multi-agent or any agent framework; builder will most likely produce a standalone script / CLI. |
| Language and runtime | ambiguous | no | async Python pipeline using Beanie ODM | - | Use Python 3.11 (current LTS / modern default). | Python is specified but no version or venv/packaging convention is given; defaulting to a recent 3.x is the most likely choice. |
| Driver and version | ambiguous | no | using Beanie ODM | - | Use Beanie (latest stable compatible) with Motor async driver (motor >= 3.x) and a matching Pydantic version as needed; pin exact versions in requirements.txt (e.g. beanie==1.13.0, motor==3.1.0) chosen by the builder. | Beanie implies Motor under the hood, but no explicit driver or versions are specified. The documentdb-driver skill gives connection-best-practice guidance (singleton client), but not explicit version pins. |
| Target service and tier | specified | no | Skill run environment: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) is reachable... Read it from environment variable DOCUMENTDB_URI... Use the database named sample_retail_07." | - | - | The provided skill_md/run-environment asserts an existing, reachable cluster and the DB name sample_retail_07. Builder must use that cluster and DB. |
| Authentication and secrets | ambiguous | no | skill_md: "Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time. Never write its value into any file..." | - | Use DOCUMENTDB_URI environment variable for the database connection. Use an OPENAI_API_KEY environment variable for OpenAI (or AZURE_OPENAI_* variables only if Azure OpenAI is explicitly chosen). Do not commit secrets; provide a .env.example with placeholders. | DocumentDB connection secret location is specified in skill_md, but the prompt doesn't say where OpenAI credentials live or whether Azure OpenAI should be used. |
| Data model | missing | no | enriches each document with a sentiment score and tags field | - | Create a reviews collection (name: reviews) in database sample_retail_07. Review document shape (example fields): {_id:ObjectId, review_id: str, product_id: str, user_id: str, review_text: str, created_at: datetime, sentiment_score: float, tags: [str], model_version: str, enriched_at: datetime}. | Prompt says to enrich documents but does not define the full schema, collection name, id fields or field types; the builder will invent a concrete model for Beanie. |
| Sample data | missing | no | - | - | Include a small synthetic sample file (e.g. data/sample_reviews.json with ~50–200 records) and a seed script that upserts them into the reviews collection; the seed script is idempotent. | Prompt doesn't provide or point to example data or a seeding mechanism. |
| Queries and indexes | covered_by_skill | no | Include a summary aggregation query grouped by product and sentiment. | documentdb-indexing | Create a compound index or single-field indexes appropriate for grouping and filtering: e.g. index on {product_id:1, sentiment_score:1} and a textSearch index on review_text for full-text queries. For aggregation counts by product + sentiment, ensure product_id and sentiment_score are covered for efficient grouping. | The prompt asks for an aggregation but not index shapes. The documentdb-indexing skill provides the guidance to pick sensible index shapes; the builder will choose indexes such as product_id + sentiment_score and a textSearch index on review_text. |
| AI components | ambiguous | no | calls OpenAI to classify the review's sentiment and to extract its key themes | - | Use the OpenAI public API (OPENAI_API_KEY) with an async client and a chat model such as gpt-3.5-turbo for classification and theme extraction. The OpenAI call should return structured JSON (e.g. sentiment label + score and an array of themes). The call is awaited per review and run concurrently with a bounded semaphore. | No model, exact API, or response format is specified. The implementation must choose a model and a JSON output schema and implement error handling and rate-limiting. |
| App surface | missing | no | build an async Python pipeline | - | Provide a CLI-driven pipeline script (e.g. python -m sample_retail_07.run_pipeline) plus a small helper CLI command to run the aggregation and print results. No web UI unless asked for. | The prompt doesn't say whether to expose an HTTP API, web UI, or only a CLI script; a CLI script is the simplest, least-opinionated choice. |
| Provisioning and deployment | specified | no | skill_md: "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable... Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use." | - | Do not create or deploy new Azure resources; use the existing DOCUMENTDB_URI cluster. Do not include cloud provisioning in the sample unless explicitly requested. | The run environment in skill_md dictates use of the existing cluster; provisioning code is not required and must be avoided unless allowed. |
| Run and test instructions | missing | no | - | - | Provide README steps: create venv, pip install -r requirements.txt, export DOCUMENTDB_URI and OPENAI_API_KEY, run data/seed.py, then run the pipeline script and the aggregation script. Include example expected output snippets. | Prompt doesn't require or describe the run commands or test expectations; the builder will add them. |
| Definition of done | missing | no | - | - | Definition of done: pipeline processes sample data, each review document in sample_retail_07.reviews has sentiment_score and tags fields populated, upserts are observed in the DB, and the aggregation returns counts grouped by product and sentiment. | No explicit acceptance criteria were included in the prompt. |
| Constraints and non-goals | missing | no | - | - | Keep dataset small to avoid costs; do not provision Azure resources; avoid shipping secrets; keep the example simple (no production HA, DR, or CMK). | No cost or compliance constraints were stated. |
| Repository conventions | missing | no | - | - | Use standard layout: src/, data/, scripts/ (seed), tests/, requirements.txt, README.md, .env.example. Name the sample package e.g. sample_retail_07 and use the phrase 'Azure DocumentDB' in the README and comments. | No repo layout, README requirements, or naming conventions were provided. |
