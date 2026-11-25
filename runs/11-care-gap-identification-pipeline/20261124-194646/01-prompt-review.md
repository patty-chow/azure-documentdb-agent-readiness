# 1. Prompt review: 11-care-gap-identification-pipeline

**Verdict: sufficient_with_assumptions**

The prompt clearly defines the goal (a Python LangChain agent that uses a DocumentDB aggregation tool to find care gaps, prioritise patients, and generate talking points) and that it should inject care-gap guidelines into the agent context. Many infra, runtime, and repo conventions are unspecified and will be filled by the builder's defaults or the installed DocumentDB skills (connection, driver, indexing, query generation). Several gallery-level items (env file, pinned deps, idempotent seed, tests, infra-as-code, explicit model choice) are missing and should be assumed or clarified before building.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 3: Goal and scenario, Workflow type, Target service and tier |
| Covered by a skill | 1: Queries and indexes |
| Ambiguous: builder will guess | 7: Language and runtime, Driver and version, Authentication and secrets, Data model, AI components, App surface, Repository conventions |
| Missing: builder will guess | 5: Sample data, Provisioning and deployment, Run and test instructions, Definition of done, Constraints and non-goals |
| Not applicable | 0: - |

## Reference requirements at risk

- The connection string and model credentials come from environment variables; none appear in the starter prompt (skill_md only specifies DOCUMENTDB_URI). The model credentials env vars are not specified and are likely to be omitted.
- .env.example lists every setting with placeholder values — starter prompt does not request or detail this; at risk.
- The vector index dimensions match the embedding model's output — prompt does not specify an embedding model or dims; at risk.
- The vector index parameters are chosen for the sample's data size, and the README says how to change them — not specified; at risk.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — the prompt requests sample behavior but gives no seed script details; at risk.
- /search returns a clear error for an empty query and when the embedding call fails — no API surface or error handling details provided; at risk.
- Search results include the similarity score — prompt does not require returning similarity scores; at risk.
- Dependencies are pinned in requirements.txt — prompt doesn't state pinned versions; at risk.
- Unit tests run without a live cluster — prompt doesn't require test design or mocks/stubs; at risk.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type — prompt asks to use 'the DocumentDB skill' but does not request infra-as-code; at risk.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up — prompt doesn't require a full README; at risk.

## Questions for the prompt author

- Which LLM provider and model(s) should the LangChain agent use for reasoning and for embeddings (e.g., OpenAI gpt-4o/gpt-4, embeddings text-embedding-3-small)? This affects embedding dimension, index choices, and env vars.
- Should the sample expose a CLI-only demo, or also provide a minimal HTTP API (e.g., /prioritise or /search) or web UI? This will change the app surface and run instructions.
- Do you require infra-as-code for provisioning (Bicep/Terraform) as part of the gallery sample, or should the sample assume the provided cluster and omit provisioning scripts?
- Do you want the repo to include an idempotent seed script and unit tests that mock the cluster, or is a simpler seed + integration demonstration against the provided cluster acceptable?

## Contradictions and missing references

- Starter prompt says 'Using the DocumentDB skill' (singular). There is no single 'DocumentDB' skill—there is a suite of documentdb-* skills installed. The builder will need to pick which skills to consult (connection, driver, indexing, natural-language-querying, etc.).

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "identify patients missing recommended screenings based on age, diagnosis, and last-visit documents"; "prioritise the patient list and generate outreach talking points" | - | - | Prompt clearly states the business problem and what the sample demonstrates. |
| Workflow type | specified | no | "build a Python LangChain agent" — single-agent LangChain | - | - | Single LangChain agent (not multi-agent) is explicit. |
| Language and runtime | ambiguous | no | "build a Python LangChain agent" | documentdb-local-deployment | Use current system python (assume Python 3.10 or 3.11) and a venv; write code compatible with Python 3.10+. | Prompt names Python but does not fix a version. skill_md notes 'python' is available on the developer machine but not a specific version. |
| Driver and version | ambiguous | no | Prompt requests a DocumentDB aggregation tool (implies using a MongoDB Python driver) | documentdb-driver | Use PyMongo (pymongo >=4.0, e.g., latest 4.x) and follow documentdb-driver guidance (singleton MongoClient). | Prompt does not name the driver or version. The documentdb-driver skill gives usage patterns but not an exact pin. |
| Target service and tier | specified | no | - | - | Use the existing, reachable vector-capable Azure DocumentDB cluster described in the provided run context (compute tier M30, MongoDB 7.0 wire protocol). | The provided skill_md/run environment states the cluster details (M30, MongoDB 7.0, vector-capable). |
| Authentication and secrets | ambiguous | no | "Using the DocumentDB skill" (no secrets mention) | documentdb-mcp-setup | DocumentDB connection string read from env var DOCUMENTDB_URI (per skill_md). LLM/model credentials will be read from provider-standard env vars (e.g., OPENAI_API_KEY) and not committed to the repo. | DocumentDB connection env var is specified in the run context; model credentials are not specified and must be assumed or clarified. |
| Data model | ambiguous | no | "patients missing recommended screenings based on age, diagnosis, and last-visit documents" | documentdb-data-modeling | Create collections such as 'patients' and 'visits' (or embed last-visit in patients). Documents include patient_id, dob or age, diagnosis_codes (array), last_visit_date. Use sample_healthcare_11 database as required by skill_md. | Prompt indicates which document types influence care gaps but does not specify schema or whether last-visit is embedded or a separate collection. |
| Sample data | missing | no | - | documentdb-local-deployment | Builder will create a small synthetic dataset (dozens to a few hundred patients) and include a seed script in repo. Source will be synthetic or anonymized and licensed as sample data. | Prompt does not specify data source, size, or loader. The run context asks to 'load the sample data' but does not provide contents. |
| Queries and indexes | covered_by_skill | no | "aggregation tool" and requirement to determine missing screenings using age/diagnosis/last-visit | documentdb-indexing | Create indexes on fields used in the aggregation: patient_id, diagnosis_codes (multikey), last_visit_date (single-field, maybe partial), and any compound index following ESR guidance (equality on patient_id or diagnosis, range on date). | documentdb-indexing skill supplies index-design guidance; prompt asks for aggregation but leaves index selection to the implementer. |
| AI components | ambiguous | no | "LangChain agent" and that the agent should "prioritise" using injected guidelines | documentdb-vector-search | Default to a common provider (OpenAI) with embeddings (e.g., text-embedding-3-small) and a chat/completion model for reasoning (e.g., gpt-4o-mini or gpt-4o). Environment variables (e.g., OPENAI_API_KEY) will be used. If vector search is used, choose embedding dims matching the model (e.g., 1536 for 'text-embedding-3-large' or 1536/1024 depending on model). | Prompt requires an LLM-driven prioritisation step but does not specify provider, models, or how/where embeddings are called. |
| App surface | ambiguous | no | "build a Python LangChain agent" (no UI or endpoints specified) | - | Implement as a CLI/console application (main script that runs the agent and prints ordered patient list and talking points). Optionally include a minimal API endpoint in Flask/FastAPI only if requested later. | Prompt does not declare whether a web UI, API, or CLI is required; the simplest reasonable default is a CLI/demo script. |
| Provisioning and deployment | missing | no | - | documentdb-azure-deployment | Do not provision a new cluster; use the existing cluster described in skill_md. No Azure infra-as-code will be added unless the author asks for it. | The run context explicitly provides an existing cluster and prohibits provisioning a new one for the sample run; the starter prompt does not request infra code. |
| Run and test instructions | missing | no | - | documentdb-local-deployment | Include README steps: create venv, pip install -r requirements.txt, copy .env.example to .env, run seed.py, then run main.py. Tests (if present) run via pytest. The build will create minimal run instructions based on these defaults. | Prompt does not provide concrete run commands or expected outputs. |
| Definition of done | missing | no | - | - | Consider done when: (1) a Python LangChain agent calls the aggregation tool, (2) returns a patient list flagged by gap type, (3) LLM-prioritised ordered list output with a priority level per patient, and (4) per-gap-type talking points are generated and paired with patients. | Prompt implies the final outputs but doesn't provide a testable acceptance checklist. |
| Constraints and non-goals | missing | no | - | documentdb-security | Do not use real PHI, keep dataset synthetic; keep cloud resource changes minimal; do not implement production-grade security beyond best-practice notes. | No cost / compliance constraints or non-goals are specified in the prompt. |
| Repository conventions | ambiguous | no | "Use the database named `sample_healthcare_11`" (in skill_md) | - | Standard layout: src/, tests/, scripts/seed.py, README.md, .env.example, requirements.txt. Use 'Azure DocumentDB' naming in docs as requested by gallery guidance. | Some conventions (DB name) are in the run context, but the wider repo layout and README sections are not specified. |
