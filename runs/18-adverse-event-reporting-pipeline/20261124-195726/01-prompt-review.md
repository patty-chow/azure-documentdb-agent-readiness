# 1. Prompt review: 18-adverse-event-reporting-pipeline

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines the main goal (Python Beanie pipeline that extracts four fields via an LLM, validates with Pydantic, stores to Azure DocumentDB, and exposes an aggregation). It omits several operational details (Python version, driver versions, LLM/provider, app surface, sample-data provenance, README/CI/packaging). The installed DocumentDB skills cover driver best-practices, indexing guidance and the live-run constraints in skill_md, so a builder can start; several decisions will be made by reasonable defaults during the build.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 4: Goal and scenario, Target service and tier, Authentication and secrets, Definition of done |
| Covered by a skill | 1: Queries and indexes |
| Ambiguous: builder will guess | 5: Workflow type, Language and runtime, Driver and version, Data model, App surface |
| Missing: builder will guess | 6: Sample data, AI components, Provisioning and deployment, Run and test instructions, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- .env.example lists every setting with placeholder values — prompt/skills do not require or specify creating a .env.example; likely omitted unless the builder adds it.
- The vector index dimensions match the embedding model's output — no embedding model or dimension is specified, so vector index config is at risk.
- The vector index parameters are chosen for the sample's data size, and the README says how to change them — not specified; builder would need to invent sensible defaults and documentation.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — prompt asks to write and verify data but gives no seed-script contract; idempotent seed is likely to be missed unless implemented.
- /search returns a clear error for an empty query and when the embedding call fails — search behavior and error handling are not described; likely omitted.
- Search results include the similarity score — prompt does not mention search results or embeddings; likely omitted.
- Dependencies are pinned in requirements.txt — versions are not specified; builder may forget to pin exact versions.
- Unit tests run without a live cluster — no test strategy (unit vs integration) specified; tests that mock the DB may be omitted.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type — prompt and skill_md do not ask for IaC; likely omitted unless explicitly requested.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up — prompt doesn't require a full README; this is at risk unless the builder adds it.

## Questions for the prompt author

- Which LLM provider and model should the extraction prompt call (e.g., OpenAI GPT-4, Anthropic Claude, or a local LLM)?
- Do you want an HTTP API (e.g., FastAPI) or a simple CLI pipeline for submitting free-text reports?
- Which Python runtime and exact package versions should be targeted/pinned (Python 3.10 or 3.11? specific beanie/motor/pymongo versions)?
- Should the sample include infra-as-code for the Azure DocumentDB cluster, or must it rely only on the provided live cluster?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python pipeline using Beanie ODM that accepts free-text adverse event reports...extract structured fields (drug, event, severity, onset date)...validates against a Pydantic schema, and writes the structured document to DocumentDB. Build an aggregation query that surfaces the most frequently reported events by drug." | - | - | Business problem and demonstrated features are clearly stated. |
| Workflow type | ambiguous | no | "Using the DocumentDB skill" | - | Assume a single-agent coding run (one automated builder using the installed DocumentDB skills) producing a runnable sample repository. | Prompt references a 'skill' but does not name an agent framework or multi-agent orchestration. |
| Language and runtime | ambiguous | no | "build a Python pipeline" | documentdb-driver | Use Python 3.10+ (prefer 3.11) and a standard venv; `python`/`pip` available per run environment. | Prompt specifies Python but not the exact runtime version; skill_md indicates a Python virtualenv is available. |
| Driver and version | ambiguous | no | "Beanie ODM" | documentdb-driver | Use Motor + PyMongo compatible versions (e.g., motor 3.x + pymongo 4.3+) and a Beanie release compatible with those (e.g., beanie >=1.12). Pin concrete versions in requirements.txt during the build. | documentdb-driver provides singleton-client best practice but does not pick exact package versions. |
| Target service and tier | specified | no | - | - | Use the live cluster as described in skill_md. | Run-time context (from skill_md) specifies a vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol) and DATABASE sample_healthcare_18. |
| Authentication and secrets | specified | no | - | - | - | skill_md instructs to read connection string from DOCUMENTDB_URI env var and not to write it into repository files. |
| Data model | ambiguous | no | "extract structured fields (drug, event, severity, onset date)...Bea nie ODM...Pydantic schema" | documentdb-data-modeling | Collection named 'adverse_events' in database 'sample_healthcare_18'; four fields stored as top-level fields, onset_date as ISO date; no explicit shard key (single-shard assumed). | Fields are specified but collection naming, additional metadata fields, indexing fields and sharding are not. |
| Sample data | missing | no | - | documentdb-local-deployment | Builder will create a small synthetic seed dataset (10–50 sample free-text reports) for the demo, marked as sample/CC0 and generated inside the repo; seed script will insert them. | Prompt and skills do not provide a concrete source, size, licence, or exact load method. |
| Queries and indexes | covered_by_skill | no | "Build an aggregation query that surfaces the most frequently reported events by drug." | documentdb-indexing | Aggregation implemented in Beanie using aggregation pipeline grouping by drug and event, counting and sorting; create a compound index on {drug:1, event:1} to support grouping/aggregation if appropriate. | Prompt specifies the aggregation; index shape is not specified but documentdb-indexing provides guidance and will be used to pick indexes. |
| AI components | missing | no | "uses prompt engineering to extract structured fields" | - | Builder will call a hosted LLM (e.g., OpenAI GPT-4-family via openai-python) with a deterministic extraction prompt and expect JSON output; no embedding model is required for extraction only. | No LLM provider, exact model, API client, or call location is specified; this will be chosen by the builder. |
| App surface | ambiguous | no | "build a Python pipeline" | - | Provide a minimal FastAPI HTTP API: POST /reports (free-text input → extraction → validation → store) and GET /reports/aggregations or /reports/top-events for the aggregation result; include a CLI seed script. | Prompt does not say whether to expose a CLI, API, or UI. |
| Provisioning and deployment | missing | no | "Using the DocumentDB skill" | documentdb-azure-deployment | No new cluster will be provisioned (skill_md forbids provisioning); infra-as-code will not be included unless explicitly requested. If included, the documentdb-azure-deployment skill would be used. | Starter prompt does not request or specify infra code; run environment already supplies a cluster. |
| Run and test instructions | missing | no | - | - | README will include common commands: pip install -r requirements.txt, export DOCUMENTDB_URI=..., python seed.py, uvicorn app:app --reload, and tests run via pytest; show expected outputs for demo commands. | Prompt does not enumerate exact commands or test expectations. |
| Definition of done | specified | no | "extract structured fields (drug, event, severity, onset date)...validates against a Pydantic schema, and writes the structured document to DocumentDB...aggregation query...most frequently reported events by drug." | - | - | Acceptance criteria are implied by the feature list in the prompt. |
| Constraints and non-goals | missing | no | - | documentdb-security | Follow run-environment constraint: do not write secrets into files; avoid provisioning new cloud resources; keep sample data small to limit cost. | No explicit cost, compliance or dataset restrictions were provided. |
| Repository conventions | missing | no | - | - | Use conventional layout: src/, tests/, README.md, requirements.txt (pinned), .env.example, seed.py, app/ or api/; use 'Azure DocumentDB' naming in README. | Starter prompt does not specify folder layout, file names or README contents; gallery expectations listed in reference_requirements will need to be added by the builder. |
