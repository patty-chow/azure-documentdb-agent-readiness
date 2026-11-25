# 1. Prompt review: 01-anti-money-laundering-pattern-detector

**Verdict: sufficient_with_assumptions**

The starter prompt plus the provided skill_md gives a clear, implementable goal (Python LangChain agent that runs aggregation pipelines to build counterparty chains and flag AML typologies) and runtime constraints (live cluster, DB name, DOCUMENTDB_URI). Several engineering choices are left unspecified (Python version, exact MongoDB driver/version, embedding and chat models, app surface, seed data and infra-as-code). The build can start, but the implementer will fill those gaps with defaults; list of risky reference requirements is included.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Workflow type, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Covered by a skill | 1: Queries and indexes |
| Ambiguous: builder will guess | 5: Language and runtime, Driver and version, Data model, App surface, Repository conventions |
| Missing: builder will guess | 5: Sample data, AI components, Run and test instructions, Definition of done, Constraints and non-goals |
| Not applicable | 0: - |

## Reference requirements at risk

- The connection string and model credentials come from environment variables; none appear in the repository. Reason: skill_md requires DOCUMENTDB_URI in env, but starter prompt doesn't explicitly require creation of a `.env.example` file. (Partly covered by skill_md but repository artifact not specified.)
- A `.env.example` lists every setting with placeholder values. Reason: Not requested explicitly in starter prompt; skill_md recommends `.env.example` but does not provide one.
- The vector index dimensions match the embedding model's output. Reason: Embedding model not specified, so index-dimension alignment is at risk.
- The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. Reason: No data size or index parameters specified.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data. Reason: Sample data and seed script are not mentioned in the prompt; implementer will need to add one.
- Search results include the similarity score. Reason: Prompt doesn't mention similarity scoring or search endpoints; if vectors are used, returning score is not mandated.
- Dependencies are pinned in `requirements.txt`. Reason: starter prompt does not require pinned versions; implementer must choose to pin dependencies.
- Unit tests run without a live cluster. Reason: No guidance about test isolation / fixtures or mocking the DB; tests that don't require a live cluster must be authored explicitly.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. Reason: Prompt and skill_md instruct to use the existing cluster; infra-as-code is not requested.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up. Reason: README content is not specified in the prompt; implementer must author it.

## Questions for the prompt author

- Which MongoDB Python driver and version should the sample use (PyMongo 4.x assumed)?
- Which Python runtime version should the sample target (e.g., 3.10 or 3.11)?
- Which embedding and chat models / provider should the LangChain agent use (e.g., OpenAI text-embedding-3-small and gpt-4o-mini)?
- Should the sample include an infra-as-code artifact for provisioning the DocumentDB cluster, or explicitly avoid provisioning and rely on the existing cluster (the skill_md instructs to use the existing cluster)?
- What is the expected app surface: CLI only, or include a small REST API (Flask/FastAPI) and example request/response? (This changes packaging and run instructions.)

## Contradictions and missing references

- Prompt says "Using the DocumentDB skill" but there is no single installed skill named exactly "DocumentDB skill"; multiple documentdb-* skills are available. Implementer will need to pick which installed skills to consult (e.g., documentdb-driver, documentdb-indexing).

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python LangChain agent ... follows transaction document references to build counterparty chains, applies known AML typology rules via aggregation, and flags suspicious patterns." | - | - | Business problem and what to demonstrate are clearly stated. |
| Workflow type | specified | no | "Python LangChain agent with a DocumentDB aggregation tool" | - | - | Single-agent LangChain setup specified. |
| Language and runtime | ambiguous | no | "Python LangChain agent"; skill_md: "python and pip resolve to a virtual environment" | - | Builder will use a modern CPython 3.10 or 3.11 runtime (assume 3.10 for compatibility) and create a virtualenv. | Python is specified but exact version is not. skill_md implies a Python venv is available. |
| Driver and version | ambiguous | no | Prompt implies MongoDB driver usage via aggregation tools but doesn't name a driver. | documentdb-driver | Use PyMongo (mongodb-driver for Python) v4.x (e.g., latest 4.x stable) and implement a process-level MongoClient singleton per documentdb-driver guidance. | The documentdb-driver skill provides best-practice patterns (singleton client) but does not pick a specific driver version; builder will pick PyMongo. |
| Target service and tier | specified | no | - | - | - | skill_md supplies the live cluster details: vector-capable cluster, compute tier M30, MongoDB 7.0 wire protocol; database name sample_banking_01; use this cluster rather than provisioning a new one. |
| Authentication and secrets | specified | no | skill_md: "connection string is in the environment variable DOCUMENTDB_URI ... Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder" | - | - | Secrets source and handling are given in skill_md. |
| Data model | ambiguous | no | "Transactions are modelled as documents that reference other documents" | documentdb-data-modeling | Builder will create a database `sample_banking_01` with collections such as `transactions` and `accounts`. Transaction docs will include fields like `_id`, `from_account`, `to_account`, `amount`, `timestamp`, and optional `linked_tx_ids` for references. Use `$graphLookup`/`$lookup` to follow references. | Relationship is specified but concrete collection names, field names and shard decisions are not; documentdb-data-modeling gives guidance for modeling choices. |
| Sample data | missing | no | - | documentdb-local-deployment | Builder will implement a seed script that inserts a small synthetic dataset (e.g., a few hundred transactions including examples of circular transfers, structuring, rapid pass-through) under an MIT-like permissive sample license. The seed script will be idempotent (upsert by _id). | Starter prompt doesn't mention source/size/license or seed script; documentdb-local-deployment has best-practices for sample data but doesn't provide the data. |
| Queries and indexes | covered_by_skill | no | "aggregation tool that follows transaction document references ... typology rules expressed as stages of the aggregation pipeline" | documentdb-indexing | Builder will implement aggregation using `$graphLookup` / `$lookup` and add single-field indexes on `from_account`, `to_account`, and `timestamp` and any fields used by match stages (e.g., `amount`) to avoid COLLSCAN. If vector or text search is added, sample index shapes will be documented per documentdb-indexing guidance. | Prompt requires aggregation in-DB. documentdb-indexing skill will guide which indexes to create; exact index list must be chosen by the implementer. |
| AI components | missing | no | "Python LangChain agent" but no embedding/model choices specified | - | Builder will default to a common hosted provider (e.g., OpenAI) for embeddings and LLMs: use an OpenAI embedding model (e.g., text-embedding-3-small or similar) and an OpenAI chat model (e.g., gpt-4o-mini or gpt-4 series) with model names and API key read from environment variables. | Which embedding and chat models to use, and embedding dimensions, are not specified and will affect vector-index shape and README instructions. |
| App surface | ambiguous | no | "agent" but no app interface specified | - | Builder will provide a simple CLI entrypoint (e.g., `python -m aml_agent analyze`) and a small Flask/FastAPI HTTP endpoint `/analyze` that accepts a request to run an analysis and returns JSON narratives for flagged chains. | Prompt only specifies an agent; UI/CLI/API choices are left to implementer. |
| Provisioning and deployment | specified | no | skill_md: "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable... Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use." | - | No cloud provisioning will be implemented; code should assume the existing cluster (DOCUMENTDB_URI). | The environment explicitly instructs not to provision new clusters for the sample run. The repository-level requirement to include infra-as-code is not requested by starter prompt. |
| Run and test instructions | missing | no | - | documentdb-local-deployment | Builder will include README steps: `pip install -r requirements.txt`, fill `.env` from `.env.example`, run `python seed.py` to populate sample data, then `python run.py` or `uvicorn app:app --reload` to start the API. Tests will be runnable via `pytest` with instructions. | Concrete commands and test descriptions are not provided in the prompt or skill_md. |
| Definition of done | missing | no | - | - | Builder will treat success as: the agent can run against the seeded dataset, return flagged chains for at least three typology examples in the seed data, and produce structured JSON narratives for each flagged chain. | No acceptance criteria provided; implementer will create practical run-time checks. |
| Constraints and non-goals | missing | no | - | documentdb-security | Builder will avoid production-grade network changes, will not implement CMK or full enterprise RBAC in the sample, and will document security caveats in the README (do not store secrets in code). | Cost/scale constraints and explicit non-goals are not stated. |
| Repository conventions | ambiguous | no | skill_md: "Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder, as the prompt asks." | - | Builder will include `.env.example`, `requirements.txt` with pinned versions, `seed.py`, `app/` folder with code, `README.md` with sections (what it shows, prerequisites, setup, run, cleanup). Tests under `tests/` using pytest. | Some conventions are hinted in skill_md but many repository-level conventions (pinning, test strategy) are left to the implementer. |
