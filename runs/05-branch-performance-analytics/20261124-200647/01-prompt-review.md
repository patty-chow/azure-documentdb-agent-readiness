# 1. Prompt review: 05-branch-performance-analytics

**Verdict: sufficient_with_assumptions**

The starter prompt clearly states the high-level goal: a Python FastAPI service with $facet aggregations, cached per-branch summaries in Azure DocumentDB, and a LangChain tool for NL queries over the summaries. Many implementation details are left to the builder (driver choice/version, embedding/chat models, exact routes, seed data, indexes, tests, README, infra). Installed skills cover important implementation guidance (singleton MongoClient, connection tuning, data modeling, indexing, vector search), so the build can start but will rely on reasonable defaults and assumptions.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 3: Goal and scenario, Language and runtime, Target service and tier |
| Covered by a skill | 0: - |
| Ambiguous: builder will guess | 7: Workflow type, Driver and version, Authentication and secrets, Data model, Queries and indexes, App surface, Repository conventions |
| Missing: builder will guess | 6: Sample data, AI components, Provisioning and deployment, Run and test instructions, Definition of done, Constraints and non-goals |
| Not applicable | 0: - |

## Reference requirements at risk

- The connection string and model credentials come from environment variables; none appear in the repository. Reason: Prompt/skill_md specify DOCUMENTDB_URI for the cluster, but model credentials are not specified — likely left to builder defaults.
- .env.example lists every setting with placeholder values. Reason: Prompt mentions using a .env.example, but does not enumerate all required settings (AI provider keys, model names, other flags).
- The vector index dimensions match the embedding model's output. Reason: Prompt doesn't specify which embedding model/dimensions to use; without that the builder must assume a model and choose dims.
- Vector index parameters are chosen for the sample's data size, and the README says how to change them. Reason: Prompt requests vector-capable features but does not specify data size or index tuning guidance.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data. Reason: Prompt asks to verify against the live cluster but does not provide a seed script; the builder must produce one (at risk if omitted or non-idempotent).
- /search returns a clear error for an empty query and when the embedding call fails. Reason: Prompt asks for natural-language querying but does not specify error handling requirements.
- Search results include the similarity score. Reason: Prompt does not require exposing similarity scores; builder may omit them unless assumed.
- Dependencies are pinned in requirements.txt. Reason: Prompt does not mention dependency pinning; builders may or may not pin versions.
- Unit tests run without a live cluster. Reason: Prompt requires verification against the live cluster; it does not require offline tests or mock fixtures.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. Reason: Prompt instructs to use the existing cluster and not provision another; repository infra-as-code is not requested.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up. Reason: Prompt does not specify README contents; it's likely the builder will add one but it's not guaranteed.
- The sample uses the name 'Azure DocumentDB' throughout, and no former or neighbouring product name. Reason: Prompt uses 'DocumentDB' generically; enforcing exact naming across docs is not specified.

## Questions for the prompt author

- Do you want the sample to run against the live cluster described in the run environment (DOCUMENTDB_URI) only, or should the repo include a Docker/local gateway dev option?
- Which MongoDB Python driver and major version should I pin (e.g., pymongo 4.5)? Should I use async PyMongo (AsyncMongoClient) or synchronous MongoClient?
- Which embedding model and chat model/provider should the LangChain tool use (e.g., OpenAI 'text-embedding-3-small' and 'gpt-4o-mini')? What env var names should be used for model credentials?
- How large should the sample dataset be (number of branches / transactions) for the seeded data, and must the seed script be idempotent (yes recommended)?
- Do you require infra-as-code (Bicep/Terraform) to be included in the repo for the DocumentDB cluster, or should the sample explicitly avoid provisioning and rely solely on the provided cluster?

## Contradictions and missing references

- Prompt says 'Using the DocumentDB skill' but there is no installed skill named exactly 'DocumentDB skill'. There are many DocumentDB-related skills available (documentdb-*, e.g., documentdb-driver, documentdb-connection) but the singular name in the prompt is not an exact match. The builder will map that instruction to the suite of documentdb-* skills.
- Prompt requests a LangChain tool but does not specify provider/model/credentials; the skill_md requires that the DocumentDB cluster is vector-capable but does not say which embedding model will be used — this affects vector-index dimensions.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | build a Python FastAPI service that exposes aggregation-backed endpoints for a branch performance dashboard. Use $facet to compute transaction volume, average ticket size, and product mix per branch. Cache rolled-up summary documents in DocumentDB and add a LangChain tool that lets analysts ask natural language questions against the cached summaries. | - | - | Business problem, user, and demonstration are clearly stated. |
| Workflow type | ambiguous | no | add a LangChain tool ... | - | Builder will implement a single-agent service: a FastAPI app that embeds a LangChain tool/agent inside the server process (no multi-agent orchestration). | Prompt doesn't say whether to use any external agent framework or multi-agent orchestration. |
| Language and runtime | specified | no | Python FastAPI | - | Use the repository's existing virtualenv; assume Python 3.10+ (prefer 3.11) for modern FastAPI and LangChain compatibility. | The run-environment block also indicates python/pip are available in a virtual env. |
| Driver and version | ambiguous | no | - | documentdb-driver | Use PyMongo (pymongo) 4.x (latest compatible with MongoDB 7.0), and use the AsyncMongoClient for async FastAPI endpoints when using async code paths. | The documentdb-driver skill gives patterns (singleton client) but does not pick a specific version; the builder will choose a PyMongo 4.x release. |
| Target service and tier | specified | no | - | - | Use the already-provisioned, reachable vector-capable Azure DocumentDB cluster described in the run environment: compute tier M30, MongoDB 7.0 wire protocol, DiskANN/HNSW/IVF available (connect via DOCUMENTDB_URI). | The run-environment skill_md supplies the cluster details; the prompt instructs to use that cluster. |
| Authentication and secrets | ambiguous | no | Read it from the environment at run time. Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder, as the prompt asks. | documentdb-security | The DocumentDB connection string is read from DOCUMENTDB_URI; AI provider/model API keys are read from environment variables like OPENAI_API_KEY (builder will choose env var names and document them in `.env.example`). | Connection string location is stated in skill_md; model credentials are not specified by the prompt. |
| Data model | ambiguous | no | Cache rolled-up summary documents in DocumentDB ... per branch | documentdb-data-modeling | Builder will create: a `transactions` collection with documents including branchId, amount, products (array / productId/count), transactionDate; and a `summaries` (or `branch_summaries`) collection with one document per branch containing computed fields: totalVolume, avgTicket, productMix, lastUpdated. | Prompt gives the high-level roll-up target but not field names, collection names, or shard key. |
| Sample data | missing | no | - | documentdb-local-deployment | Builder will provide a seed script that synthesizes transactions for ~10 branches and a few thousand transactions (idempotent upsert semantics). | Prompt doesn't include data source, size, or seed behavior; documentdb-local-deployment has guidance but not a concrete dataset. |
| Queries and indexes | ambiguous | no | Use $facet to compute transaction volume, average ticket size, and product mix per branch. | documentdb-indexing | Builder will create indexes on branchId and transactionDate and possibly productId (single-field or compound) to support aggregation filtering; for vector queries, a vector index with dimensions matching the chosen embedding model will be created. | Prompt requires $facet pipelines but doesn't list indexes; documentdb-indexing guides index choices. |
| AI components | missing | no | add a LangChain tool that lets analysts ask natural language questions against the cached summaries. | - | Builder will use a popular embedding model and LLM provider by default (e.g., OpenAI embeddings model `text-embedding-3-small` and an OpenAI chat model), with API keys read from env vars. Specific model/dimensions will be documented in README and `.env.example`. | Prompt requires LangChain but does not name embedding/chat models or env var names; this will materially affect vector index dims and code. |
| App surface | ambiguous | no | build a Python FastAPI service that exposes aggregation-backed endpoints for a branch performance dashboard ... add a LangChain tool ... | - | Builder will expose endpoints such as: GET /metrics/branches/{branch_id} (reads cached summary), POST /summaries/refresh (trigger rebuild of summaries), and POST /ask or /nlq for natural-language questions (calls LangChain tool). Inputs/outputs will be JSON; NL query returns a string plus provenance/summary of matched branches. | High-level surface is given, but exact route names, request/response formats, and auth are left to the implementer. |
| Provisioning and deployment | missing | no | This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable. | documentdb-azure-deployment | No new cloud resources will be provisioned by the sample; the sample will use the pre-existing cluster. If infra-as-code is required later, the documentdb-azure-deployment skill can produce Bicep/Terraform examples. | Prompt explicitly instructs to use the existing cluster and not to create another. |
| Run and test instructions | missing | no | - | - | Builder will add README steps: pip install -r requirements.txt, copy .env.example->.env, run seed script, then start FastAPI (uvicorn) and exercise endpoints. Tests may be minimal or omitted unless requested. | Prompt doesn't include concrete commands or test matrix. |
| Definition of done | missing | no | - | - | Builder will treat 'done' as: endpoints implemented, $facet aggregation produces per-branch summaries, summaries cached in DocumentDB and refreshable, LangChain tool wired to endpoint and returns plausible NL answers, and README documents how to run everything. | No explicit acceptance criteria in prompt. |
| Constraints and non-goals | missing | no | - | - | Keep costs low by using the existing cluster; avoid provisioning new cloud resources; do not include production hardening or advanced HA (non-goal). | No cost limits or non-goals were specified. |
| Repository conventions | ambiguous | no | use a config file or `.env.example` with a placeholder, as the prompt asks. | - | Builder will create a conventional layout: src/ or app/, requirements.txt, README.md, .env.example, scripts/seed.py, tests/ (pytest). | Some conventions implied by run-environment, but repo layout and dependency pinning not specified. |
