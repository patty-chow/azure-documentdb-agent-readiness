# 1. Prompt review: 04-medical-imaging-metadata-store

**Verdict: sufficient_with_assumptions**

The starter prompt clearly states the core goal (Python service, store modality/body part/findings, embed findings with OpenAI, store embeddings as BSON binary vectors, create a vector-ivf index, and expose a semantic /search endpoint). Several important implementation details are unspecified and will be decided by the builder (Python runtime version, exact OpenAI model and embedding dims, collection name, env var names, seed-data size, tests, README, and infra/IaC). The installed DocumentDB skills cover vector-indexing, driver best-practices, connection guidance and data-modeling, so the build can start but will rely on reasonable defaults for multiple items.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 3: Goal and scenario, Target service and tier, App surface |
| Covered by a skill | 1: Queries and indexes |
| Ambiguous: builder will guess | 6: Workflow type, Language and runtime, Driver and version, Authentication and secrets, Data model, AI components |
| Missing: builder will guess | 6: Sample data, Provisioning and deployment, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- The connection string and model credentials come from environment variables; none appear in the repository. (Partial coverage: skill_md mentions DOCUMENTDB_URI, but the prompt doesn't require .env.example or explicit env var names for OpenAI.)
- A .env.example lists every setting with placeholder values. (Prompt doesn't ask for it; no installed skill mandates creating .env.example.)
- The vector index dimensions match the embedding model's output. (Prompt requires creation of vector-ivf index but doesn't specify model/dimensions; builder must ensure dimensions match chosen embedding model.)
- The vector index parameters are chosen for the sample's data size, and the README says how to change them. (Index parameter choices are not specified; documentdb-vector-search skill can recommend defaults but README guidance is not specified.)
- One database client is created and reused across requests. (Prompt doesn't mandate singleton client; documentdb-driver skill recommends it but it could be missed.)
- A seed script loads sample data and creates the index, and can be run twice without duplicating data. (Prompt doesn't request a seed script or idempotency safeguards.)
- /search returns a clear error for an empty query and when the embedding call fails. (Prompt doesn't define error handling behavior.)
- Search results include the similarity score. (Prompt asks to retrieve images by similarity but does not explicitly require returning the DB-side similarity score.)
- Dependencies are pinned in requirements.txt. (Prompt doesn't require pinned dependencies.)
- Unit tests run without a live cluster. (Prompt doesn't request tests or mocks; builder may not include offline unit tests.)
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. (Prompt does not request IaC; skill_md instructs to use the existing cluster.)
- The README covers what the sample shows, prerequisites, setup, run, and clean-up. (Prompt expects a sample but does not ask for README contents explicitly.)
- The sample uses the name 'Azure DocumentDB' throughout. (Prompt uses 'DocumentDB' generically; the builder may accidentally use other product names unless instructed.)

## Questions for the prompt author

- Which OpenAI embeddings model should be used (exact model name) and do you have a preference for embedding dimension/precision (float32 vs float16)?
- Which Python minor version should the sample target (e.g., 3.10 or 3.11)?
- Which HTTP framework do you prefer (Flask or FastAPI), and what should the exact search route be (e.g., POST /search)?
- What should the collection name be (e.g., 'medical_images')? Any additional document fields required (IDs, timestamps, patient identifiers — note privacy concerns)?
- What environment variable names should be used for secrets (OPENAI_API_KEY, OPENAI_MODEL, DOCUMENTDB_URI)? Should a .env.example be created?
- Do you require infrastructure-as-code for provisioning the cluster, or must the sample avoid provisioning and rely on the pre-provisioned cluster described in skill_md?
- Should the sample return the raw DB similarity score in results, or a normalized/converted score?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | build a Python service that stores medical imaging metadata (modality, body part, findings) as DocumentDB documents and embeds the findings text using OpenAI. ... Expose a search endpoint that retrieves images by semantic similarity to a clinical query string. | - | - | Business problem and demonstration are explicit: semantic vector search over medical-imaging metadata. |
| Workflow type | ambiguous | no | Using the DocumentDB skill | - | Treat as a single-agent code sample (no multi-agent orchestration); the builder will write a stand-alone Python HTTP service (no agent framework). | Prompt references 'DocumentDB skill' but doesn't specify an agent framework or orchestration model. |
| Language and runtime | ambiguous | no | build a Python service | - | Use Python 3.10 or 3.11 (builder will target a current 3.x LTS; assume 3.10 for packaging/CI). | No explicit Python minor version given; skill.md only says 'python' is available in the run environment. |
| Driver and version | ambiguous | no | - | documentdb-driver | Use PyMongo (pymongo) as the MongoDB driver; pin a recent 4.x release (e.g., pymongo>=4.4,<5) in requirements.txt, and follow the documentdb-driver skill guidance for client reuse. | Prompt does not name a driver or version; a builder will reasonably pick PyMongo and the installed driver skill covers best practices. |
| Target service and tier | specified | no | Skill.md run environment: 'A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) is reachable ... connection string in env DOCUMENTDB_URI.' | - | - | Run environment (provided in skill_md) specifies the cluster and database name to use (sample_healthcare_04). Builder must not provision a new cluster. |
| Authentication and secrets | ambiguous | no | skill_md: 'connection string in the environment variable DOCUMENTDB_URI.' | documentdb-mcp-setup | Use environment variables: DOCUMENTDB_URI for DB connection and OPENAI_API_KEY (and optionally OPENAI_MODEL) for embedding calls. Do not write secrets into repo; include a .env.example with placeholders. | OpenAI key and model name are not specified; documentdb skills mention env-driven config patterns but do not set exact variable names for the AI provider. |
| Data model | ambiguous | no | stores medical imaging metadata (modality, body part, findings) as DocumentDB documents and embeds the findings text | documentdb-data-modeling | Use database sample_healthcare_04 (skill_md). Create a collection named 'medical_images' (or 'images') where each document has fields: modality (string), body_part (string), findings (string), embedding (Binary BSON). Use embedding field name 'embedding' and store as pymongo.binary.Binary of float32 or float16 bytes depending on chosen index precision. | Prompt specifies the fields but not collection name, types, or whether to include timestamp/ID naming conventions or indexes beyond the vector index. |
| Sample data | missing | no | - | documentdb-local-deployment | Builder will create a small synthetic seed dataset (e.g., ~20–100 example metadata documents) in a seed script. No external dataset is specified; use generated realistic examples for modality/body part/findings. | Prompt doesn't supply source/size/licence or a seed script. documentdb-local-deployment skill describes sample-data patterns but does not provide the concrete dataset required by the sample. |
| Queries and indexes | covered_by_skill | no | Store embeddings as BSON binary vectors and create a vector-ivf index. Expose a search endpoint that retrieves images by semantic similarity ... | documentdb-vector-search | Programmatically call createSearchIndexes to create a cosmosSearch vector-ivf index on the embedding field; set index kind to vector-ivf and set dimensions to the chosen embedding length. Use a supported similarity metric (e.g., COS or L2) in the vector query. | Vector-index creation and query shape are covered by the documentdb-vector-search skill; builder must still pick index parameters (nlist, nprobe, metric) suitable for the small sample. |
| AI components | ambiguous | no | embeds the findings text using OpenAI | - | Use OpenAI embeddings model (e.g., text-embedding-3-small or text-embedding-3-large). Choose text-embedding-3-small for cost and speed; assume embedding dimensionality appropriate to that model (builder must read the model's output dims to set the index). | Prompt requires OpenAI but doesn't specify model or dimensionality; these choices directly affect index dimensions and must be chosen by the builder. |
| App surface | specified | no | build a Python service ... Expose a search endpoint that retrieves images by semantic similarity to a clinical query string. | - | Implement an HTTP JSON API with a POST /search or GET /search?query=... endpoint that accepts a clinical query and returns ranked metadata. Use a lightweight framework (Flask or FastAPI); assume JSON in/out and port 8000 default. | Route name, method, request/response schema and framework are not specified; builder will pick conventional defaults. |
| Provisioning and deployment | missing | no | - | documentdb-azure-deployment | Do not provision or deploy new cloud resources; use the pre-provisioned cluster described in skill_md. No IaC will be created unless the author instructs otherwise. | Starter prompt does not ask for IaC or deployment; reference requirements expect infrastructure code but the prompt does not. |
| Run and test instructions | missing | no | - | - | Builder will include a README with commands: pip install -r requirements.txt, export env vars or copy .env.example, python seed.py, python app.py (or uvicorn), and example curl to call /search. Unit tests are not specified; builder may add minimal tests but they won't run without a live cluster unless mocks are provided. | No explicit commands or test requirements in the prompt. |
| Definition of done | missing | no | - | - | Definition of done: service runs locally against the provided cluster, seed script creates collection and index, /search returns ranked documents for sample queries showing semantic matches. Builder will use this as acceptance criteria. | Prompt does not provide explicit acceptance criteria. |
| Constraints and non-goals | missing | no | - | documentdb-security | No strict constraints (cost limits, compliance) are specified; builder will keep sample small and note that this is only a demo (not production-ready / HIPAA-compliant), and follow TLS/secret best-practices. | Medical data raises compliance questions; the prompt does not address them. |
| Repository conventions | missing | no | - | - | Repository will include: README, requirements.txt, .env.example (placeholders only), app/ package, seed.py, tests/ with mocks, and no secrets checked in. Use 'Azure DocumentDB' in documentation. | Starter prompt doesn't state folder layout, pinning, or README structure; these are typical defaults the builder will apply. |
