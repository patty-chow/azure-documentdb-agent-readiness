# 1. Prompt review: 11-care-gap-identification-pipeline

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines the goal (a Python LangChain agent that uses a DocumentDB aggregation tool to find care gaps, injects guidelines, prioritises patients, and writes outreach talking points). It omits many engineering details (Python version, driver/version, exact data model, model/provider, indexes, app surface, infra, tests). The skill.md run environment supplies the live cluster details and the DATABASE name and the DOCUMENTDB_URI env var, but no 'DocumentDB skill' is actually installed. A builder can start, but will make a number of concrete assumptions (Python 3.10+, PyMongo driver, collections named 'patients' etc., a CLI demo script, OpenAI-compatible LLM) unless the author specifies otherwise.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 2: Goal and scenario, Workflow type |
| Covered by a skill | 2: Target service and tier, Authentication and secrets |
| Ambiguous: builder will guess | 5: Language and runtime, Data model, Queries and indexes, App surface, Repository conventions |
| Missing: builder will guess | 7: Driver and version, Sample data, AI components, Provisioning and deployment, Run and test instructions, Definition of done, Constraints and non-goals |
| Not applicable | 0: - |

## Reference requirements at risk

- The connection string and model credentials come from environment variables; none appear in the repository. Reason: prompt/skill.md give DOCUMENTDB_URI but do not specify model credential env var names or other model-related settings.
- A .env.example lists every setting with placeholder values. Reason: skill.md suggests using .env.example for the connection string, but does not enumerate all required env vars (LLM keys, model names, etc.).
- The vector index dimensions match the embedding model's output. Reason: prompt doesn't name an embedding model nor dimensions; skill.md mentions vector indexes exist but not dimensions tied to a model.
- The vector index parameters are chosen for the sample's data size, and the README says how to change them. Reason: neither prompt nor skill.md specify index parameters or guidance.
- One database client is created and reused across requests. Reason: not specified; builder may or may not implement a singleton client pattern.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data. Reason: prompt doesn't request a seed script; skill.md asks to 'load the sample data' during verification but does not provide a seed script or idempotency requirement explicitly.
- /search returns a clear error for an empty query and when the embedding call fails. Reason: prompt does not define an HTTP endpoint or search route; requirement appears out of scope for this prompt.
- Search results include the similarity score. Reason: no search API is specified in the prompt; similarity scoring and presentation are unspecified.
- Dependencies are pinned in requirements.txt. Reason: not mentioned; builder may or may not pin exact versions.
- Unit tests run without a live cluster. Reason: prompt does not request unit tests; skill.md expects verification against the live cluster but provides no guidance for offline tests.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. Reason: skill.md explicitly provides an existing cluster and forbids creating another unless allowed; prompt doesn't request infra-as-code.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up. Reason: prompt asks for the sample but doesn't require a README; skill.md expects verification but doesn't state README content.
- The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name. Reason: prompt uses 'DocumentDB' and references a 'DocumentDB skill' but does not insist on naming conventions; builder might use other product names unless instructed.

## Questions for the prompt author

- Which LLM provider and model should the sample use for prioritisation and talking-point generation (e.g. OpenAI gpt-4/gpt-4o-mini)? This affects SDKs, env var names and dimensions if embeddings are used.
- Do you want a CLI demo (single script), an HTTP API, or a small web UI? This changes the app surface and what routes/commands to include.
- Should the repository include a synthetic seed dataset and an idempotent seed script? If so, any desired size/variety (dozens, hundreds of patients)?
- Do you require infrastructure-as-code (Bicep/Terraform) to be included, or must the sample avoid provisioning resources entirely and rely on the provided cluster?

## Contradictions and missing references

- Starter prompt: "Using the DocumentDB skill" but installed_skills lists no 'DocumentDB' or related agent skill. (There is no installed skill by that name to call.)
- skill.md requires use of an existing live cluster and says 'verify against the live cluster' but the prompt's invocation of a 'DocumentDB skill' implies a callable tool that is not installed.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | identify patients missing recommended screenings based on age, diagnosis, and last-visit documents; prioritise the patient list and generate outreach talking points | - | - | Business problem and what the sample demonstrates are stated. |
| Workflow type | specified | no | build a Python LangChain agent with a DocumentDB aggregation tool | - | - | Single-agent LangChain workflow is explicit. |
| Language and runtime | ambiguous | no | build a Python LangChain agent | skill.md | Target Python 3.10+ (code and CI/test suites written for Python 3.10 or 3.11). | Prompt says Python; skill.md says python/pip are available but does not fix a version. Builder will pick a modern supported Python (3.10/3.11). |
| Driver and version | missing | no | - | - | Use the PyMongo driver (pymongo) compatible with MongoDB 7.0; pin to a recent stable release, e.g. pymongo>=4.3,<5.0. | Prompt asks for a DocumentDB aggregation tool but doesn't name the Python MongoDB driver or version. |
| Target service and tier | covered_by_skill | no | - | skill.md | - | skill.md provides cluster details: compute tier M30, MongoDB 7.0 wire protocol, vector-capable with DiskANN/HNSW/IVF, and the DATABASE name sample_healthcare_11. |
| Authentication and secrets | covered_by_skill | no | - | skill.md | - | skill.md instructs the connection string is in DOCUMENTDB_URI and must not be written into files; use .env.example for placeholders. |
| Data model | ambiguous | no | based on age, diagnosis, and last-visit documents | - | Create a 'patients' collection with documents containing _id, dob or age, diagnoses (array), and last_visit_date; optionally a 'visits' collection linking patient_id to visit_date if separate visit docs are preferred. | Prompt names the required fields but not collection names, document shapes, relationships, or whether last-visit is embedded or a separate collection. |
| Sample data | missing | no | - | skill.md | Include a seeded synthetic dataset loader (seed script) that inserts a small set of representative patient and visit documents (dozens to a few hundred) and is idempotent. | Prompt asks for pipeline behavior but provides no sample data or source; skill.md expects the sample to 'load the sample data' during verification but does not supply it. |
| Queries and indexes | ambiguous | no | DocumentDB aggregation tool that identifies patients missing recommended screenings | skill.md | Builder will implement a MongoDB aggregation pipeline ($match on age/diagnosis, $lookup or grouping to find last_visit, $project to compute elapsed interval and compare to guideline thresholds). Create indexes on patients._id, patients.diagnoses, and last_visit_date (or visits.patient_id + visit_date) for performance. Vector indexes mentioned in skill.md are present but vector-dimensions/providers not specified. | The functional query is requested; index definitions and parameters are not specified. skill.md mentions vector indexes exist but doesn't give field names or dimensions relevant to this sample. |
| AI components | missing | no | LangChain agent...prioritise the patient list and generate outreach talking points | - | Use an OpenAI-compatible chat model via LangChain (e.g. gpt-4o-mini or gpt-4) for prioritisation and content generation; if embeddings are used for any retrieval, use a text-embedding-3-small style model and set vector-dimension to match that model (e.g. 1536 or as documented). Credentials come from environment variables (e.g. OPENAI_API_KEY). | No provider, model names, or embedding model/dimensions/where called are specified. |
| App surface | ambiguous | no | build a Python LangChain agent ... have the agent prioritise the patient list and generate outreach talking points | - | Provide a CLI/demo script (e.g. python run_pipeline.py) that runs the agent end-to-end and prints or writes an ordered patient list with priority and talking points. Optionally include a Jupyter notebook for interactive exploration. | Prompt doesn't specify CLI, API, or UI; a simple CLI demo is the least-surprising default. |
| Provisioning and deployment | missing | no | - | skill.md | Do not provision new Azure resources; use the existing cluster per skill.md. No infra-as-code will be provided unless requested. | skill.md forbids creating a new cluster unless policy allows; the prompt doesn't ask for infra as code. |
| Run and test instructions | missing | no | - | skill.md | Include a README with commands to create a virtualenv, pip install -r requirements.txt, run the seed script, and run the demo CLI. Unit tests may be minimal and not require a live cluster unless explicitly provided. | skill.md gives environment constraints but no explicit run/test commands. |
| Definition of done | missing | no | - | - | Definition of done: sample runs end-to-end against the provided cluster, creates required collections/indexes idempotently, returns an ordered list of patients with priority and talking points, and includes a README and .env.example. | Prompt does not provide acceptance criteria. |
| Constraints and non-goals | missing | no | - | skill.md | Keep the sample read-only for patient data (no destructive writes), avoid provisioning cloud infra, and keep sample dataset small to limit cost and privacy exposure. | No cost limits, privacy constraints, or non-goals were provided except the skill.md guidance about not writing the connection string. |
| Repository conventions | ambiguous | no | - | skill.md | Use a conventional layout (src/, tests/, scripts/, README.md); include a pinned requirements.txt; include a .env.example with DOCUMENTDB_URI and any model keys. | skill.md instructs to use a .env.example and not to log secrets; other repo conventions (pinning deps, test structure) are not specified. |
