# 1. Prompt review: 01-patient-record-summarizer-rag

**Verdict: sufficient_with_assumptions**

The starter prompt clearly states the core goal (Python LlamaIndex RAG storing chunked patient records with patientId-based access control and vector retrieval). Many DocumentDB-specific details (index creation, connection handling, vector-query patterns) are covered by installed skills, so a builder can start; several implementation choices are unspecified and will be decided by the builder (Python minor version, exact embedding/chat models, index dimensions/params, sample-data and test strategy).

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 4: Goal and scenario, Workflow type, Target service and tier, Provisioning and deployment |
| Covered by a skill | 1: Authentication and secrets |
| Ambiguous: builder will guess | 5: Language and runtime, Driver and version, Data model, Queries and indexes, App surface |
| Missing: builder will guess | 6: Sample data, AI components, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- Create a cosmosSearch vector index with dimensions matching the embedding model's output — embedding model not specified in prompt, so the builder cannot deterministically choose index `dimensions`.
- `.env.example` lists every setting with placeholders — the prompt / skills do not request or provide a complete .env.example; implementer must author it.
- Vector index parameters chosen for the sample's data size, and README describing how to change for larger datasets — parameters/scale are unspecified and must be documented manually.
- Seed script that loads sample data and creates the index and can be run twice without duplicating data — no seed/ idempotence behavior is specified in the prompt.
- `/search` returns a clear error for an empty query and when the embedding call fails — error-handling specifics are not given and must be added by implementer.
- Search results include the similarity score — the prompt asks for retrieval but doesn't require returning the score; implementer must explicitly add it.
- Dependencies pinned in `requirements.txt` — prompt doesn't require pinned versions; implementer must add them.
- Unit tests run without a live cluster — prompt doesn't require mocks or offline tests; creating such tests is not implied by prompt or installed skills.
- Infrastructure-as-code for the cluster (Azure DocumentDB resource type) — prompt assumes an existing cluster and does not require IaC; reference requirements ask for it, so it's at risk unless the builder deliberately includes it.
- README covering what the sample shows, prerequisites, setup, run, and clean-up — prompt does not mandate README details; implementer must author it to satisfy the gallery.

## Questions for the prompt author

- Which embedding model and chat/completion model should the sample use (provider and exact model)? This determines the vector `dimensions` for the index.
- Which app surface do you prefer: an HTTP API (POST /search), a CLI, or a small web UI? The reference tests expect a `/search` endpoint — please confirm.
- Which Python version should be targeted (3.9, 3.10, 3.11)?
- Should the sample include IaC that declares an Azure DocumentDB cluster, even though a live cluster is provided? (Reference requirements ask for IaC; the run environment forbids provisioning.)
- Do you want real medical data or only pseudonymized / synthetic sample data (the former would have legal/compliance implications)?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python LlamaIndex RAG agent that stores chunked patient records in a DocumentDB vector index... Model records with a patientId field for access control." | - | - | Clear business problem and demonstration: RAG for clinical summaries with per-patient access control. |
| Workflow type | specified | no | "Python LlamaIndex RAG agent" (single-agent RAG) | - | - | Single-agent RAG workflow with LlamaIndex is explicitly requested. |
| Language and runtime | ambiguous | no | "Python" | - | Use Python 3.10 or 3.11 (common current LlamaIndex/typing support); virtualenv-based environment where `python` and `pip` resolve to the repo's venv as described in skill.md. | Prompt specifies Python but not a version. The run-environment note implies a working python/pip, but the exact interpreter version should be assumed or asked. |
| Driver and version | ambiguous | no | - | documentdb-driver | Use pymongo as the Mongo-compatible Python driver (pymongo >= 4.3, pinned in requirements.txt). Create a process-wide singleton MongoClient per documentdb-driver guidance. | The documentdb-driver skill covers singleton client patterns but does not mandate a specific Python driver/version; builders will default to pymongo. |
| Target service and tier | specified | no | skill.md run environment: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) is reachable ... use database named `sample_healthcare_01`." | - | - | Cluster already exists and is vector-capable; sample must use that live cluster and database. |
| Authentication and secrets | covered_by_skill | no | skill.md: "Its connection string is in the environment variable `DOCUMENTDB_URI`. Read it from the environment at run time. Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder, as the prompt asks." | documentdb-mcp-setup | - | MCP skill also documents secret-handling rules. Connection string stored in env; do not echo/write credentials. |
| Data model | ambiguous | no | "Model records with a patientId field for access control." Also: "stores chunked patient records... with an embedding field" | documentdb-data-modeling | Collection name: `patient_chunks` (or similar). Document fields: `_id`, `patientId`, `sourceDocId`, `chunkId` (or offset), `text` (chunk content), `embedding` (vector), `schemaVersion`. Use embedding as a top-level numeric array field named `embedding` for cosmosSearch. | Prompt requires patientId and chunking; not all schema details (collection name, chunk-id naming, schemaVersion) are specified and will be chosen by the builder, guided by the data-modeling skill. |
| Sample data | missing | no | - | documentdb-local-deployment | Include a small synthetic sample dataset generator (e.g., 10 patients, ~5–10 records each, pseudonymized). Provide a `scripts/seed.py` that can be re-run idempotently and documents the (synthetic) source and license (MIT or CC0). | Starter prompt does not specify data source, size, or licensing; required sample-data artifacts must be designed by the implementer. |
| Queries and indexes | ambiguous | no | "store chunked patient records in a DocumentDB vector index" and "retrieve the most relevant sections..." | documentdb-vector-search, documentdb-indexing | Create a `cosmosSearch` vector index on the `embedding` field. For this sample (small dataset) use `vector-hnsw` (or `vector-diskann` if using larger sample). Set `dimensions` to match chosen embedding model (assume 1536). Similarity: COS (cosine) with normalized embeddings. Use `$search`/`cosmosSearch` in a pipeline, pre-filtered by `patientId`, returning top-k with similarity score. | Vector-index creation and query shape are within installed skills, but index `dimensions` depend on the embedding model (unspecified). Builder will rely on skill guidance to pick HNSW/DiskANN based on sample size. |
| AI components | missing | no | "Python LlamaIndex RAG agent" and "apply context engineering to structure the prompt for a clinical summary" | - | Use an external embedding provider (default: OpenAI text-embedding-3-small with 1536-dim embeddings) and OpenAI chat model for summarization (e.g., gpt-4o-mini or gpt-4o). Environment variables will hold model API keys (e.g., OPENAI_API_KEY). Document these choices and how to change them in README. | Prompt names LlamaIndex but does not specify which embedding/chat models or their dimensions. This materially affects index dimensions and must be assumed or asked. |
| App surface | ambiguous | no | "On request, retrieve... and return a grounded answer with document references." | - | Provide a small HTTP API (FastAPI or Flask) with a POST /search endpoint that accepts JSON: {"patientId": "...", "question": "..."}. Endpoint returns: summary text, list of source chunks (chunkId/_id + patientId + score), and per-chunk similarity scores. CLI helper also included for interactive testing. | The prompt says 'on request' but doesn't choose CLI vs API vs UI; an API is the usual default for a sample. |
| Provisioning and deployment | specified | no | skill.md run environment: cluster already provisioned and reachable; "Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use." | documentdb-azure-deployment | - | No new Azure provisioning is required for the sample; an IaC script may be included optionally but must not be executed against the live account without permission. |
| Run and test instructions | missing | no | - | - | Add README instructions: create venv, pip install -r requirements.txt, copy .env.example to .env and set DOCUMENTDB_URI and model keys, python scripts/seed.py, python app.py (or uvicorn), and pytest for tests. Document expected output and verification steps (e.g., run a sample /search and show summary + citations). | Prompt doesn't give run/test commands; implementer must author them. |
| Definition of done | missing | no | - | - | Accept when: (1) documents are ingested as chunked docs with embeddings and patientId; (2) vector index exists with matching dimensions; (3) /search returns grounded clinical summary with per-chunk references and similarity scores; (4) README and .env.example present; (5) seed script runs idempotently. | No explicit acceptance criteria in the prompt; use the reference checklist as the definition-of-done. |
| Constraints and non-goals | missing | no | - | documentdb-security | Treat sample data as pseudonymized (no PHI). Recommend TLS and env-based secrets, do not include production-level HA or DMZ networking. Mention that production PHI requires compliance (HIPAA) and is out of sample scope. | Security best practices exist in installed skills but the prompt does not state constraints explicitly—implementer must add warnings/limits in README. |
| Repository conventions | missing | no | - | - | Use conventional layout: src/ or app/, scripts/ (seed), tests/, requirements.txt pinned, README.md, .env.example, and a top-level LICENSE. Use 'Azure DocumentDB' term consistently in docs. | Conventions are not specified; builder will use typical sample-repo structure. |
