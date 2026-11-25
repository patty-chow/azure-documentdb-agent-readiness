# 1. Prompt review: 03-next-best-action-multi-agent

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines the business goal (a Python LangChain multi-agent next-best-action system) and the required agents and orchestration. Many low-level engineering details (Python version, driver version, exact data model, embedding/LLM choices, seed data, indexes, API surface, README and CI/test expectations) are left unspecified and will be decided by the builder or filled in by the available DocumentDB skills; the build can start but will rely on sensible defaults for these items.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 4: Goal and scenario, Workflow type, Target service and tier, Provisioning and deployment |
| Covered by a skill | 1: Authentication and secrets |
| Ambiguous: builder will guess | 5: Language and runtime, Driver and version, Data model, Queries and indexes, Constraints and non-goals |
| Missing: builder will guess | 6: Sample data, AI components, App surface, Run and test instructions, Definition of done, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- The connection string and model credentials come from environment variables; none appear in the repository. (skill_md covers DOCUMENTDB_URI but model credentials are unspecified; risk: embedding/LLM credentials not specified.)
- .env.example lists every setting with placeholder values. (Not specified in starter prompt or skills.)
- The vector index dimensions match the embedding model's output. (Embedding model not specified, so vector-dimension matching is at risk.)
- The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. (Indexes and README guidance not specified.)
- A seed script loads sample data and creates the index, and can be run twice without duplicating data. (No seed script or idempotency specified.)
- /search returns a clear error for an empty query and when the embedding call fails. (API/error behaviors not specified.)
- Search results include the similarity score. (Result format not specified.)
- Dependencies are pinned in requirements.txt. (Not specified.)
- Unit tests run without a live cluster. (Tests not specified; mocking strategy not defined.)
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. (Prompt implies using existing cluster and skill exists to provision, but the starter prompt did not ask for IaC; risk that no infra-as-code will be included.)
- The README covers what the sample shows, prerequisites, setup, run, and clean-up. (Not specified in the starter prompt; likely to be added by builder but at risk.)
- The sample uses the name 'Azure DocumentDB' throughout, and no former or neighbouring product name. (Naming convention not mandated in prompt; may be omitted or inconsistent.)

## Questions for the prompt author

- Which Python version should be targeted (3.9 / 3.10 / 3.11)?
- Which embedding model and LLM provider/model should the sample use (e.g., OpenAI text-embedding-3-small with 1536 dims and gpt-4o-mini), and do model credentials come from specific env vars?
- Should the sample expose a web API (FastAPI) endpoint, a CLI only, or both?
- Do you want an infra-as-code artifact that can provision the DocumentDB cluster, or must the sample strictly avoid any provisioning and only use the provided live cluster?

## Contradictions and missing references

- Prompt says 'Using the DocumentDB skill' but there is no single installed skill named exactly 'DocumentDB skill'. Multiple documentdb-* skills and a run-environment skill_md are available; the builder must map the request to the appropriate skills.
- Prompt asks to write/read from 'DocumentDB' while the installed skills and skill_md explicitly describe an Azure DocumentDB cluster and tools; this is consistent but the prompt does not explicitly reference the run-environment constraints (database name, env var DOCUMENTDB_URI) which are supplied separately in skill_md.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | build a Python LangChain multi-agent system where a propensity agent scores the customer's likelihood of responding to each action type ..., a channel agent selects the optimal contact channel ..., and a timing agent determines the best send time. An orchestrator combines the outputs and writes the NBA recommendation to DocumentDB. | - | - | Clear business problem and what the sample should demonstrate. |
| Workflow type | specified | no | Python LangChain multi-agent system ... propensity agent, channel agent, timing agent, and an orchestrator | - | - | Multi-agent orchestration using LangChain (Python) is explicitly requested. |
| Language and runtime | ambiguous | no | Using the DocumentDB skill, build a Python LangChain multi-agent system | skill_md (run environment) | Builder will target Python 3.10 or 3.11 (common current defaults) and a virtualenv where `python` and `pip` already point to that interpreter (skill_md indicates python/pip are available). | Python is specified but no explicit version or runtime constraints provided in the prompt. skill_md notes 'python and pip resolve to a virtual environment'. |
| Driver and version | ambiguous | no | - | documentdb-driver | Use PyMongo (the official Python MongoDB driver), e.g. pymongo 4.x (latest stable compatible with MongoDB 7.x); implement MongoClient as a process-wide singleton per documentdb-driver guidance. | Prompt does not name a driver/version. documentdb-driver skill provides patterns (singleton client) but not a pinned version. |
| Target service and tier | specified | no | writes the NBA recommendation to DocumentDB | skill_md (run environment) | - | The provided run-environment skill_md explicitly states a vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0) is available and must be used (database name sample_customer_360_03). |
| Authentication and secrets | covered_by_skill | no | - | skill_md (run environment) | - | skill_md requires reading the cluster connection string from DOCUMENTDB_URI env var and forbids writing the secret into files or logs. |
| Data model | ambiguous | no | propensity agent scores ... using DocumentDB history, channel agent selects ... from preference documents, ... writes the NBA recommendation to DocumentDB | documentdb-data-modeling | Builder will create simple collections in database sample_customer_360_03 such as: `interactions` (customer_id, timestamp, action_type, outcome, embedding?), `preferences` (customer_id, channel_rankings, contact_times), and `nba_recommendations` (customer_id, action, channel, send_time, score, created_at). Use embedding fields if vector search is used. | Prompt names types of documents but not explicit collection names or document schemas; documentdb-data-modeling can guide design but does not fix concrete shapes. |
| Sample data | missing | no | - | - | Builder will include a small synthetic seed dataset (dozens–low hundreds of customers) created by a seed script that upserts idempotently into `interactions`, `preferences`, and optionally precomputes embeddings. The dataset will be synthetic and included in the repo. | No source, size, license, or seed details are given; this must be invented by the builder. |
| Queries and indexes | ambiguous | no | - | documentdb-indexing, documentdb-vector-search | Builder will create at least: index on customer_id, a time-descending index on (customer_id, timestamp), and a vector index for any embedding field. Vector index dimensions will be chosen to match the chosen embedding model (assume 1536 dims unless a different embedding is selected). Index parameters (HNSW/DiskANN settings) will be conservative for a small sample and documented in the README. | The prompt refers to using DocumentDB history and preference docs, but specific query patterns and exact index shapes are not provided; indexing guidance is available from installed skills. |
| AI components | missing | no | build a Python LangChain multi-agent system ... propensity agent ... channel agent ... timing agent ... | - | Builder will use common defaults: OpenAI embeddings (text-embedding-3-small / 1536-dim) and an OpenAI LLM (e.g., gpt-4o-mini or gpt-4o) via environment variable OPENAI_API_KEY; LangChain will call embeddings for vectorization and an LLM for agent reasoning. All model credentials come from env vars. | No provider, model names, dimensions or credential env vars are specified in the prompt; these choices materially affect index dimension and API usage. |
| App surface | missing | no | - | - | Builder will expose a small programmatic surface: a CLI (python main.py --customer-id <id>) and a minimal FastAPI HTTP endpoint POST /nba or GET /nba?customer_id=<id> that runs the orchestrator and returns the recommendation; also include a demo script that runs through a sample customer. | Prompt does not define whether a CLI, API or UI is desired; default to CLI + simple API for demonstration. |
| Provisioning and deployment | specified | no | - | skill_md (run environment), documentdb-azure-deployment | - | skill_md states a live cluster is already provisioned and must be used; documentdb-azure-deployment skill exists if infra-as-code is later requested, but the prompt implies using existing cluster rather than provisioning new resources. |
| Run and test instructions | missing | no | - | - | Builder will add README run steps: set env vars (DOCUMENTDB_URI, OPENAI_API_KEY), pip install -r requirements.txt, python seed.py, uvicorn main:app --reload or python main.py --demo, and pytest to run tests (with network calls mocked). | No explicit run/test commands in the starter prompt. |
| Definition of done | missing | no | - | - | Acceptance criteria: seed script ran successfully, app returns a Next-Best-Action for a sample customer, NBA document is written to sample_customer_360_03.nba_recommendations, and README documents what was executed. | Prompt lacks concrete acceptance criteria; builder will invent them. |
| Constraints and non-goals | ambiguous | no | Using the DocumentDB skill ... | skill_md (run environment) | Follow skill_md constraint: do not provision another cluster; keep sample small to limit costs; avoid any production-level security changes (no CMK or tenant changes). Do not include real customer PII in sample data. | Prompt doesn't call out costs or non-goals explicitly; skill_md gives the main constraint about using the existing cluster. |
| Repository conventions | missing | no | - | - | Standard layout: README.md, src/ (or package), tests/, seed.py, requirements.txt (pinned), .env.example with placeholders, and no secrets checked in. | No repo layout or file conventions are specified in the prompt; reference requirements expect certain files (e.g., .env.example). |
