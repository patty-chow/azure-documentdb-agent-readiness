# 1. Prompt review: 01-patient-record-summarizer-rag

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines the goal (a Python LlamaIndex RAG agent that stores chunked patient records with patientId and returns grounded, referenced clinical summaries) and the single-agent workflow. Many important engineering details (Python version, driver, exact embedding/chat models, index parameters, API surface, seed data shape and scripts, tests, and README/infra conventions) are not specified and will be chosen by the builder; these are predictable defaults but should be confirmed.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 2: Goal and scenario, Workflow type |
| Covered by a skill | 3: Target service and tier, Authentication and secrets, Provisioning and deployment |
| Ambiguous: builder will guess | 7: Language and runtime, Data model, Queries and indexes, App surface, Run and test instructions, Constraints and non-goals, Repository conventions |
| Missing: builder will guess | 4: Driver and version, Sample data, AI components, Definition of done |
| Not applicable | 0: - |

## Reference requirements at risk

- A cosmosSearch vector index is created in code with dimensions matching the embedding model the app uses — prompt and skill.md do not specify index creation parameters or dimensions; builder will have to choose index kind and dimensions (at risk).
- Retrieval runs the similarity search in Azure DocumentDB with $search / cosmosSearch — the prompt says use a DocumentDB vector index but does not require the $search/cosmosSearch API explicitly (at risk).
- Retrieval is limited to the requested patient's records by patientId filter inside cosmosSearch — prompt requires patientId field but does not specify how to enforce filtering in the DB-level query (at risk).
- The connection string and model credentials come from environment variables; none appear in the repository — skill.md covers DOCUMENTDB_URI but model credential env vars are not specified (at risk).
- .env.example lists every setting with placeholder values — skill.md asks for .env.example but does not list every setting required (at risk).
- Vector index parameters are chosen for the sample's data size, and the README says how to change them — neither index parameter choices nor README guidance are specified (at risk).
- One database client is created and reused across requests — neither prompt nor skill.md specifies client reuse patterns (at risk).
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — no seed script provided or specified (at risk).
- /search returns a clear error for an empty query and when the embedding call fails — error-handling requirements are not specified (at risk).
- Search results include the similarity score — prompt asks for references but does not require returning scores (at risk).
- Dependencies are pinned in requirements.txt — not specified (at risk).
- Unit tests run without a live cluster — testing strategy is not specified (at risk).
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type — skill.md says a cluster is already provisioned and does not ask to provide infra-as-code; the sample will likely not include infra code (at risk).
- The README covers what the sample shows, prerequisites, setup, run, and clean-up — not specified (at risk).

## Questions for the prompt author

- Which embedding and chat model(s) and provider should the sample use (exact model names)? This determines index dimensions and the env vars to document.
- What application surface do you want: HTTP API (FastAPI/Flask), CLI, or a minimal web UI? This changes the sample structure and the routes/commands to implement.
- Should unit tests be written to run entirely without a live cluster (mocking/patched client), or is a live-cluster integration test allowed for CI/local verification?

## Contradictions and missing references

- Prompt: "Using the DocumentDB skill" but the installed_skills list is empty. (There is a provided skill.md Run environment that documents the cluster and environment variables; confirm whether the prompt refers to that.)

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python LlamaIndex RAG agent that stores chunked patient records in a DocumentDB vector index... On request, retrieve the most relevant sections for a given clinical question... return a grounded answer with document references." | - | - | - |
| Workflow type | specified | no | "a Python LlamaIndex RAG agent" | - | - | Single-agent RAG via LlamaIndex is explicit. |
| Language and runtime | ambiguous | no | "Python" | skill.md (Run environment) | Use a modern Python 3.x runtime for developer machines; assume Python 3.10 (or 3.11) as the target for virtualenv and package installs. | Prompt says Python; skill.md confirms python/pip in a venv but gives no version. |
| Driver and version | missing | no | - | - | Use pymongo (MongoDB-compatible driver) pinned to a recent 4.x release (e.g. pymongo>=4.0,<5.0). For LlamaIndex store integration, use the latest compatible llama-index package (pin exact version in requirements.txt). | Neither prompt nor skill.md names the Python DB driver or versions. |
| Target service and tier | covered_by_skill | no | - | skill.md (Run environment) | - | skill.md explicitly describes a vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN/HNSW/IVF support) and says use it. |
| Authentication and secrets | covered_by_skill | no | - | skill.md (Run environment) | - | skill.md instructs reading the cluster connection string from DOCUMENTDB_URI and to use a .env.example placeholder. |
| Data model | ambiguous | no | "Model records with a patientId field for access control." | skill.md (Run environment) -- database name sample_healthcare_01 | Create a collection named patient_records (or records). Each chunk document will include: _id, patientId, source_doc_id, chunk_id, text (chunk content), embedding (array of floats), metadata (dict), created_at ISO timestamp. No explicit shard key; single logical collection in sample_healthcare_01. | Database name is supplied by skill.md. The rest of the document shape and collection naming are not specified. |
| Sample data | missing | no | - | - | Provide a small synthetic dataset (e.g., 3–5 patients, 10–20 chunks each) included in repo under data/ with a seed script that is idempotent. Mark data as synthetic and MIT-licensed (or state "synthetic demo data") in the README. | No sample data source, size, license, or loading script specified. |
| Queries and indexes | ambiguous | no | "stores chunked patient records in a DocumentDB vector index" | skill.md (Run environment) -- cluster supports DiskANN, HNSW, IVF | Create a cosmosSearch vector index of kind vector-hnsw (or vector-ivf) on the embedding field. Use similarity metric COS (cosine). Set dimensions to match embedding model output (assume 1536). Keep index parameters conservative for small demo dataset (default or small M/efConstruction values) and document in README how to tune for larger datasets. | Prompt implies a vector index but does not fix type, metric, dimensions, or parameters; skill.md only states what the cluster supports. |
| AI components | missing | no | "LlamaIndex RAG agent" | skill.md (Run environment) -- no model specifics | Use OpenAI for embeddings and chat calls: embeddings model text-embedding-3-small (1536 dims) and a GPT-style chat model (e.g. gpt-4o-mini or gpt-4o) for summarization. Expect credentials via OPENAI_API_KEY in environment. Integrate embedding calls where LlamaIndex expects them. | Embedding and chat model provider and exact models/dimensions are not specified. |
| App surface | ambiguous | no | "On request, retrieve the most relevant sections... and return..." | - | Expose a small HTTP API (FastAPI) with a POST /search endpoint that accepts JSON {patientId, question, top_k?} and returns JSON {answer, sources:[{doc_id,chunk_id,score,excerpt}], debug: {retrieved_count}}. Include a simple CLI wrapper for local demo runs. | Prompt implies an interactive request/response surface but doesn't choose API vs CLI vs UI. |
| Provisioning and deployment | covered_by_skill | no | - | skill.md (Run environment) | - | skill.md instructs to use the existing reachable cluster and not to provision another one unless allowed. |
| Run and test instructions | ambiguous | no | - | skill.md (Run environment) -- suggests verification against live cluster | Provide README commands: set env vars (DOCUMENTDB_URI, OPENAI_API_KEY), pip install -r requirements.txt, python seed.py, uvicorn app.main:app --reload, and pytest to run unit tests (unit tests written to run without a live cluster). | skill.md includes verification guidance but not concrete commands to run the sample and tests. |
| Definition of done | missing | no | - | - | Define Done as: seed script executed and populated sample DB (idempotent); /search returns a grounded clinical summary with document references and similarity scores for a given patientId; code runs locally with documented environment variables; requirements.txt pinned; unit tests pass locally without a live cluster. | Prompt describes desired behavior but does not give acceptance criteria or checks. |
| Constraints and non-goals | ambiguous | no | "clinical" context and patientId for access control | skill.md (Run environment) -- do not write connection string into files, use existing cluster | Treat this as a demo/sample only (not production), do not provision cloud infra, keep dataset small to limit cost, avoid logging secrets, and note privacy/compliance non-goals in README (do not use real PHI). | Some run constraints are in skill.md; other non-goals (cost limits, compliance) are not specified. |
| Repository conventions | ambiguous | no | - | skill.md (Run environment) -- requests a .env.example placeholder | Follow common sample layout: README.md, requirements.txt (pinned), .env.example, src/ or app/, data/, tests/, seed.py, and a top-level LICENSE (MIT). Mention use of the name "Azure DocumentDB" in the README and avoid alternate product names. | Prompt and skill.md hint at some conventions (.env.example), but not full repo layout or pinning policies. |
