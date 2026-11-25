# 1. Prompt review: 14-telehealth-session-summarizer

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines the core goal: a Python LlamaIndex pipeline that ingests a telehealth transcript, prompts OpenAI with a context-engineered prompt (chief complaint, assessment, plan, follow-up), parses the response into structured fields, and stores it in Azure DocumentDB linked by patientId. This is enough to start a build, but many implementation details are left to the builder (Python runtime version, exact drivers and versions, embedding model and dimensions, index shapes, runtime interface, secrets naming, seed data and tests, README and infra). The build will proceed but will rely on plausible defaults for those gaps.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 2: Goal and scenario, Target service and tier |
| Covered by a skill | 0: - |
| Ambiguous: builder will guess | 7: Workflow type, Language and runtime, Authentication and secrets, Data model, Queries and indexes, AI components, App surface |
| Missing: builder will guess | 7: Driver and version, Sample data, Provisioning and deployment, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- PyMongo explicit usage for storing summary (prompt says store in DocumentDB but does not require PyMongo) — the builder may choose a different client.
- OpenAI credentials and all model credentials in environment variables — DOCUMENTDB_URI is specified in skill_md, but OpenAI env var names are not specified.
- .env.example listing every required setting with placeholder values — not mentioned in prompt or skills.
- Vector index dimensions match the embedding model's output — embedding model and dimensions are not specified in the prompt.
- Vector index parameters chosen for sample data size, README guidance to change them for larger data — not specified.
- Seed script that loads sample data and creates the index, idempotent on repeated runs — prompt doesn't mention seed data or idempotency.
- /search error handling (empty query and embedding failures) and returning similarity scores — the sample is a summariser but reference expects robust search behavior; not covered by prompt.
- Dependencies pinned in requirements.txt — not specified in prompt; builder must add manually.
- Unit tests run without a live cluster — tests are not specified and usually need mocking; prompt doesn't mention tests.
- Infrastructure-as-code for the cluster (Azure DocumentDB resource type) — prompt doesn't request provisioning and run environment already provides a cluster.
- README covering what the sample shows, prerequisites, setup, run, and clean-up — prompt doesn't require a README but gallery samples need one.

## Questions for the prompt author

- Which OpenAI model(s) should be used for the text-generation LLM and for embeddings? (Specify exact model names and desired trade-offs for cost/quality.)
- What exact runtime/interface do you want as the sample entry point: a Python function only, a CLI, or an HTTP endpoint (Flask/FastAPI)?
- Do you require use of PyMongo specifically for storage (the reference asks for PyMongo), or is any MongoDB client acceptable?
- What should the collection name and final document schema be (exact field names, any additional metadata like schemaVersion, createdAt)?
- Should the repo include IaC to provision an Azure DocumentDB cluster (Bicep/Terraform), or should it assume the cluster in the run environment and not create cloud resources?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python LlamaIndex pipeline that accepts a telehealth session transcript... generates a structured clinical summary ... and stores the result as a structured DocumentDB document linked to the patient record by patientId." | - | - | The business problem, user and demonstration (telehealth summariser storing summaries in DocumentDB) is explicit. |
| Workflow type | ambiguous | no | "LlamaIndex pipeline" | - | Implement as a single-process Python application (no multi-agent orchestration). Provide a callable function and a minimal HTTP endpoint (Flask/FastAPI) or CLI wrapper rather than building a multi-agent orchestration. | The prompt does not say whether this should be run as a CLI, API service, or integrated into an agent framework; LlamaIndex implies a local pipeline. |
| Language and runtime | ambiguous | no | "Python" | documentdb-local-deployment | Target Python 3.10+ (e.g., 3.10 or 3.11). Use a virtualenv and pip; sample uses `python` / `pip` as entrypoints per skill_md. | No explicit Python version; skill_md notes `python` and `pip` are available in the run environment but not the version. |
| Driver and version | missing | no | - | documentdb-driver | Use PyMongo (pymongo) as the MongoDB driver, pinned in requirements.txt to a recent stable major (for example `pymongo>=4.3,<5`). Follow documentdb-driver guidance (singleton MongoClient). | Prompt asks to store into DocumentDB but does not name the driver or version. documentdb-driver skill covers client patterns but not exact package/version. |
| Target service and tier | specified | no | "Using the DocumentDB skill" and skill_md: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol...) is reachable... DOCUMENTDB_URI env var." | - | - | Run-environment (skill_md) explicitly states the cluster: M30, MongoDB 7.0, vector-capable. The sample must use database `sample_healthcare_14` per skill_md. |
| Authentication and secrets | ambiguous | no | "stores the result ... linked to the patient record by patientId." and skill_md: "connection string ... is in the environment variable `DOCUMENTDB_URI`." | documentdb-mcp-setup | Expect DOCUMENTDB_URI (connection string) in env. For OpenAI, expect OPENAI_API_KEY (and optional OPENAI_API_BASE / MODEL names) in env; add a .env.example listing these env vars. | DocumentDB secret location is in the provided run environment. The prompt does not specify LLM provider credentials naming — builder will assume standard OpenAI env vars. |
| Data model | ambiguous | no | "stores the result as a structured DocumentDB document linked to the patient record by patientId." | documentdb-data-modeling | Create a `clinical_summaries` collection in database `sample_healthcare_14`. Document shape: { _id, patientId, chief_complaint, assessment, plan, follow_up, createdAt, schemaVersion }. Add schemaVersion field and createdAt timestamp. | Prompt requires linking by patientId but does not name the collection or other metadata. Use data-modeling skill recommendations (schemaVersion, avoid >16MB). |
| Sample data | missing | no | - | - | Include a small seed script that inserts a few (2–5) synthetic telehealth transcripts and a patient record. The script should be idempotent (upsert by a deterministic key) so it can be run multiple times without duplication. | Starter prompt doesn't include sample transcripts or a seed procedure; a gallery sample usually needs this. |
| Queries and indexes | ambiguous | no | - | documentdb-indexing, documentdb-vector-search | Create a single-field index on patientId (for lookups) and, if embeddings are used for search, create a vector `cosmosSearch` index (DiskANN for M30) with `dimensions` matching the chosen embedding model. Also consider TTL on transient records if desired. | Prompt does not say whether to build vector indexes or search endpoints; vector-index details must match embedding dimensions (not specified). |
| AI components | ambiguous | no | "generates a structured clinical summary using OpenAI" and "Python LlamaIndex pipeline" | documentdb-vector-search | Use OpenAI for the LLM call that produces the summary (e.g., `gpt-4o-mini` or `gpt-4o`/`gpt-4` family) and OpenAI embedding model `text-embedding-3-small` (1536 dims) or `text-embedding-3-large` (3072 dims) for any embedding steps. Normalize and store dimensions alongside vectors. | Prompt names OpenAI and LlamaIndex but does not specify the exact models or embedding choice. Those choices affect index dimensions and cost. |
| App surface | ambiguous | no | "pipeline that accepts a telehealth session transcript together with the patientId" | - | Implement a Python function `summarize_transcript(transcript: str, patient_id: str)` as the entry point; provide a minimal CLI `scripts/summarize_cli.py` and an optional Flask/FastAPI endpoint `/summarize` that accepts JSON {patientId, transcript}. Provide example usage in README. | The prompt doesn't require a specific surface (CLI, API, web UI); builder will pick a minimal, testable interface. |
| Provisioning and deployment | missing | no | - | documentdb-azure-deployment | Do not provision a cluster in the sample (the run environment already provides a live cluster). If infra is desired, include an optional Bicep/Terraform snippet but do not execute it by default. | The prompt does not ask for IaC. The provided run environment explicitly points to an existing cluster; gallery samples sometimes include IaC but this prompt didn't request it. |
| Run and test instructions | missing | no | - | - | Add a README with steps to create a virtualenv, install pinned requirements, set env vars (DOCUMENTDB_URI, OPENAI_API_KEY), run the seed script, and run a demo CLI or start the API. Provide expected output example. | No run/test commands provided in the prompt. |
| Definition of done | missing | no | - | - | Definition of done: the repo contains a function/API that accepts transcript+patientId, produces a 4-field structured summary (chief complaint, assessment, plan, follow-up), inserts a document into `clinical_summaries` with patientId, and includes a reproducible seed + README demonstrating the flow. | No explicit acceptance criteria in prompt. |
| Constraints and non-goals | missing | no | - | documentdb-security | Treat PHI carefully in README: this is a sample; DO NOT submit real PHI. Keep cost / cluster provisioning out of the sample. Use TLS and env-based secrets. Do not claim production readiness or HIPAA compliance. | Security/compliance constraints are not specified; the documentdb-security skill can help drafting recommended notes. |
| Repository conventions | missing | no | - | - | Follow typical layout: README.md, src/ or app/, scripts/seed.py, requirements.txt (pinned), tests/ with unit tests, .env.example, LICENSE. Use 'Azure DocumentDB' name in README and code comments. | Prompt doesn't state repo layout or conventions; the builder will apply standard gallery conventions. |
