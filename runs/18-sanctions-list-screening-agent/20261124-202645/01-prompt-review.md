# 1. Prompt review: 18-sanctions-list-screening-agent

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines the business goal (a Python LangChain screening agent performing vector + regex matching and returning a scored report) and that Azure DocumentDB will hold embedded sanctions entries. Several implementation details are left to the builder (embedding model/provider and its dims, API surface, seed-data size, index tuning, tests, README, infra-as-code), but installed DocumentDB skills cover driver, vector-indexing and data-model guidance so a developer can start and produce a usable sample by making a few concrete assumptions.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 4: Goal and scenario, Workflow type, Target service and tier, Authentication and secrets |
| Covered by a skill | 2: Data model, Queries and indexes |
| Ambiguous: builder will guess | 4: Language and runtime, Driver and version, AI components, App surface |
| Missing: builder will guess | 6: Sample data, Provisioning and deployment, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- Vector index dimensions must match the chosen embedding model — the prompt does not specify an embedding model, so dimensions are undefined.
- Embedding model selection and credentials must come from environment variables — the prompt/skill_md only specify DOCUMENTDB_URI for DB; model creds are not specified.
- A .env.example listing every setting with placeholders — not requested in the prompt and absent from skill_md.
- Vector index parameters tuned to sample data size and README guidance for scaling — prompt asks for a vector index but not parameter choices or documentation on scaling.
- Idempotent seed script that loads sample data and creates the index — sample data/seed script is not provided or specified.
- Search endpoint error handling: returning clear errors for empty queries and embedding failures — the prompt doesn't define API surface or error contract.
- Search results include the raw similarity score — prompt requests match confidence but does not explicitly require returning the vector similarity score in results.
- Dependencies pinned in requirements.txt — prompt does not require pinned deps; skill guidance covers patterns but not pinning.
- Unit tests that run without a live cluster — missing from prompt and skill_md; requires mocking and test scaffolding.
- Infrastructure for the cluster as code using Azure DocumentDB resource type — prompt does not request infra code; although a deployment skill exists, repo may not include it.
- README covering sample, prerequisites, setup, run, and clean-up — not requested in starter prompt and therefore at risk of omission.

## Questions for the prompt author

- Which embedding model and provider should the sample use (and what env var(s) hold its credentials)? This determines index dimensions and seed-time embedding computation.
- Do you want an HTTP API endpoint (e.g., FastAPI /screen) or a CLI/library interface as the primary app surface for the sample?
- Should the sample include infra-as-code (Bicep/Terraform) for the DocumentDB cluster, or explicitly avoid provisioning and rely on the provided live cluster?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python LangChain agent that stores embedded sanctions list entries in a DocumentDB vector index ... performs both vector similarity search and $regex-based fuzzy matching ... returns a structured screening report with match confidence and recommended action." | - | - | Business problem, user workflow, and what the sample demonstrates are stated directly. |
| Workflow type | specified | no | "a Python LangChain agent" | - | - | Single-agent LangChain workflow requested explicitly. |
| Language and runtime | ambiguous | no | "Python LangChain agent" | - | Use Python 3.10 or 3.11 (latest stable on developer machine), run inside a venv; document exact version in README and requirements. | Prompt requires Python but does not fix a version. skill_md only says `python`/`pip` resolve to a venv. |
| Driver and version | ambiguous | no | - | documentdb-driver | Use PyMongo (pymongo>=4.0,<5.0) and follow the documentdb-driver guidance to create a singleton MongoClient reused across requests. | Prompt asks to operate via MongoDB driver (index creation via driver) but doesn't name a driver or version. The documentdb-driver skill provides connection/client patterns but not a pinned version. |
| Target service and tier | specified | no | - | - | Use the existing, reachable vector-capable Azure DocumentDB cluster referenced in skill_md (compute tier M30, MongoDB 7.0). | skill_md run-environment explicitly describes the live cluster to use and database name. |
| Authentication and secrets | specified | no | - | - | Read the DocumentDB connection string from environment variable DOCUMENTDB_URI at runtime; never write it to repo files. (skill_md requires this.) | DB secret handling is specified in skill_md. Embedding/model creds are not specified here (see AI components). |
| Data model | covered_by_skill | no | "stores embedded sanctions list entries" | documentdb-data-modeling | Create a `sanctions` collection in database `sample_banking_18` with documents like { _id, name, aliases, details, embedding: [float], schemaVersion }. Store embeddings in a field named `embedding` and add `schemaVersion`. | Prompt requires embeddings be stored on documents. documentdb-data-modeling skill guides on embedding, schemaVersion, and document-size considerations. The database name is provided in skill_md. |
| Sample data | missing | no | - | - | Provide a small synthetic seed set (e.g., 50–500 sample sanctions entries) created by an idempotent seed script that also computes embeddings at seed time. Use permissive synthetic licensing and include sample CSV/JSON in repo. | Starter prompt and skill_md do not supply a concrete data source, sample size, or a seed script; the builder will need to create synthetic or small example data. |
| Queries and indexes | covered_by_skill | no | "vector index" and "$regex-based fuzzy matching" and "$search / cosmosSearch" | documentdb-vector-search | Create a `cosmosSearch` vector index (choose vector-diskann if target scale is large; for a small sample the builder may pick vector-hnsw or vector-ivf). Match the index `dimensions` to the chosen embedding model's output. Implement vector KNN via `$search` + `cosmosSearch` and do regex queries against name/aliases fields. | The prompt requires both vector search and regex fuzzy matching; the documentdb-vector-search skill provides guidance on index type selection and parameters. |
| AI components | ambiguous | no | "stores embedded ... entries" (implies embeddings) but no model named | - | Use an off-the-shelf embedding provider (e.g., OpenAI text-embedding-3-small) with env var OPENAI_API_KEY; assume embedding dimension (e.g., 1536) and record it in `.env.example`. Normalize embeddings for cosine similarity per vector-search guidance. | Prompt asks for embeddings but does not specify which model/provider or where credentials come from. This affects index dimensions and seed-time embedding computation. |
| App surface | ambiguous | no | "On each screening request ... returns a structured screening report" | - | Provide a small HTTP API (FastAPI) with a /screen endpoint that accepts a JSON screening request and returns the structured JSON report; include a CLI script for ad-hoc local testing. | Prompt does not state whether the agent should be exposed via CLI, HTTP API, or library function; README and examples should show at least one surface. |
| Provisioning and deployment | missing | no | - | documentdb-azure-deployment | Do not provision a new cluster in the sample run (skill_md forbids it). Optionally include example Bicep/Terraform templates under an `infra/` folder (using documentdb-azure-deployment skill) but mark them as optional and not executed in the demo. | Starter prompt doesn't request infra-as-code; a separate skill exists to create clusters but skill_md says use the existing cluster. |
| Run and test instructions | missing | no | - | - | Add README steps: create .env from .env.example, pip install -r requirements.txt, run seed script, start FastAPI (uvicorn), and demo a sample /screen call. Provide unit tests that mock DB and embedding calls for CI. | Prompt and skill_md do not include explicit run/test commands; developer must author them. |
| Definition of done | missing | no | - | - | Define done as: (1) seed script creates collection and index and loads sample data idempotently; (2) /screen endpoint or CLI returns structured report with candidate matches, similarity scores, confidence and recommended action; (3) tests run locally without live cluster. | No explicit acceptance criteria provided in prompt. |
| Constraints and non-goals | missing | no | - | - | Do not provision cloud resources during the demo; keep sample data small to avoid cost. Note compliance considerations in README but do not implement production-grade RBAC or CMK by default. | Prompt doesn't specify cost or security non-goals; skill_md gives an operational constraint (use existing cluster). |
| Repository conventions | missing | no | - | - | Follow typical layout: README.md, .env.example, requirements.txt (pinned), src/, tests/, scripts/seed.py, infra/ (optional). Use 'Azure DocumentDB' in docs. | No repository layout or naming conventions were supplied. |
