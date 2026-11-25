# 1. Prompt review: 17-rare-disease-literature-search

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines the core goal (Python + LlamaIndex pipeline ingesting PubMed abstracts, storing chunk embeddings in Azure DocumentDB, and exposing a RAG agent that returns citations with PubMed ID and year). It leaves many engineering details unspecified (embedding provider/model & dims, exact driver choice/version, API surface, index tuning, README/tests/infrastructure), but installed DocumentDB skills cover best-practice guidance for client reuse, vector-index choices, and data-modeling patterns, so a builder can start and will make reasonable defaults for the missing items.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 3: Goal and scenario, Workflow type, Target service and tier |
| Covered by a skill | 1: Queries and indexes |
| Ambiguous: builder will guess | 6: Language and runtime, Driver and version, Authentication and secrets, Data model, Sample data, App surface |
| Missing: builder will guess | 6: AI components, Provisioning and deployment, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- Model credentials from environment: DocumentDB connection string is specified in skill_md, but embedding/LLM provider credentials are not specified in the starter prompt or skills — builder must assume and add env vars.
- .env.example lists every setting with placeholder values: Not mentioned in the prompt; at risk unless builder adds it.
- Vector index dimensions match the embedding model's output: embedding model is not specified, so dimensions cannot be fixed in code until a model is chosen — at risk.
- Vector index parameters chosen for the sample's data size, and README explains how to change them: prompt requests index creation but not parameter selection guidance or README explanations — at risk.
- Seed script idempotency (can be run twice without duplicating data): ingestion is required but idempotency is not specified — at risk.
- /search returns a clear error for an empty query and when the embedding call fails: error handling is not specified in the prompt — at risk.
- Search results include the similarity score: prompt requires ranking and PubMed ID/year in citations but does not require exposing the similarity score — at risk.
- Dependencies are pinned in requirements.txt: dependency pinning is not mentioned — at risk.
- Unit tests run without a live cluster: tests are not specified; mocking requirements are not mentioned — at risk.
- Infrastructure-as-code for the cluster: prompt/run environment precludes provisioning in this run and does not request infra code — at risk.
- README covers prerequisites, setup, run, and clean-up: not specified in the prompt; at risk unless builder adds comprehensive README.

## Questions for the prompt author

- Which embedding provider and model should be used? (This determines embedding dimensionality and the vector-index `dimensions` parameter.)
- Which LLM provider/model should be used for generation (and do you want the provider credentials in specific env var names)?
- Should the sample include infrastructure-as-code for the Azure DocumentDB cluster (Bicep/Terraform) or explicitly avoid provisioning and use only the provided live cluster?
- Do you want a web API (Flask/FastAPI) endpoint (e.g., POST /search) as the sample's app surface, or a CLI/demo notebook?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "ingests PubMed abstracts for rare diseases ... stores vectors in DocumentDB ... exposes a RAG agent that answers researcher questions with grounded citations" | - | - | The user, business problem (researcher literature search), and demonstration (RAG over PubMed abstracts in Azure DocumentDB) are plainly stated. |
| Workflow type | specified | no | "LlamaIndex pipeline ... exposes a RAG agent" (single-agent retrieval-augmented generation workflow using LlamaIndex) | - | - | LlamaIndex + RAG implies a single-agent retrieval + generation flow; no multi-agent orchestration requested. |
| Language and runtime | ambiguous | no | "build a Python LlamaIndex pipeline"; skill_md: `python` and `pip` resolve to a virtual environment | - | Use Python 3.10 (or the system `python` which is a dev virtualenv); package installs via pip into that environment. Tests and CI should target Python 3.10/3.11 compatibility. | Language is specified (Python) but no explicit major/minor version is given. |
| Driver and version | ambiguous | no | "store vectors in DocumentDB ... LlamaIndex's Azure DocumentDB vector store integration or a MongoDB-compatible Python driver such as PyMongo" | documentdb-driver | Prefer using LlamaIndex's built-in Azure/Mongo vector store if available; otherwise use PyMongo (pymongo >= 4.5) and the official MongoDB Python driver. Follow documentdb-driver guidance to instantiate a process-wide MongoClient singleton. | The prompt allows either LlamaIndex integration or raw PyMongo; version is not specified. documentdb-driver provides client-reuse best practices but not explicit version pins. |
| Target service and tier | specified | no | skill_md: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) is reachable ... connection string in DOCUMENTDB_URI" | - | - | Run environment explicitly states the cluster and database name (`sample_healthcare_17`). Builder must use that cluster and DB. |
| Authentication and secrets | ambiguous | no | skill_md: "connection string in the environment variable DOCUMENTDB_URI" | - | DocumentDB connection string is read from DOCUMENTDB_URI. For embeddings / LLMs, assume OpenAI and require OPENAI_API_KEY (or another provider API key) via env vars; builder will place provider/model names and keys into environment variables and a .env.example. | DocumentDB secret location is given. The starter prompt does not specify embedding/LLM provider credentials or how they are supplied; the builder will need to pick defaults (e.g., OPENAI_API_KEY). |
| Data model | ambiguous | no | "keeps each abstract's text, PubMed ID and publication year ... Split each ingested abstract into text chunks ... carry the source abstract's PubMed ID and year on every chunk as metadata" | documentdb-data-modeling | Create a collection named `pubmed_chunks` (in DB `sample_healthcare_17`) with documents like: { _id, pmid, year, chunk_id, text, embedding: [float], model: "<model-name>", schemaVersion: 1 }. No sharding (single-shard) for the sample. Use denormalized chunks (embed) rather than separate chunk and metadata collections. | Prompt requires PubMed ID and year propagated to each chunk. Exact field names, collection name, and shard key are not specified; documentdb-data-modeling provides patterns to follow. |
| Sample data | ambiguous | no | "ingests PubMed abstracts for rare diseases (e.g. through the PubMed E-utilities API)" | - | Implement ingestion using NCBI E-utilities (esearch + efetch) and store PubMed ID, title, abstract text, and publication year. For a gallery sample, default to fetching up to 100 abstracts (querying a reasonable rare-disease search term set) with respect for NCBI rate limits. Document the source and license (PubMed abstracts are publicly available). | Source is specified. Size, selection criteria, and seeding idempotency are not specified and will be chosen by the builder. |
| Queries and indexes | covered_by_skill | no | "Create a cosmosSearch vector index ... with dimensions matching the embedding model's output and a similarity of COS, L2 or IP"; "run the vector similarity search inside Azure DocumentDB with $search / cosmosSearch" | documentdb-vector-search | Builder will choose `vector-diskann` (recommended for M30) or `vector-hnsw` for small sample sets; dimensions will be set to match the chosen embedding model at runtime; use COS (cosine) similarity and normalize embeddings if needed. Code will create the vector index via the database's index-creation API. | The prompt asks for code that creates a vector index. documentdb-vector-search contains the index-type guidance and parameters to follow. Non-vector indexes (e.g., a text index or index on pmid/year) are not explicitly requested but are likely to be added by the implementer. |
| AI components | missing | no | "LlamaIndex pipeline ... chunks and embeds them ... generates an answer conditioned on those chunks" | - | Use a commonly used embedding provider such as OpenAI (e.g., text-embedding-3-family) or HuggingFace; use LlamaIndex's integration for embeddings and an LLM for the generation step (e.g., OpenAI GPT-4o/3.5). Record model name and dimensions in metadata at runtime. Builder will require an env var for the provider key (e.g., OPENAI_API_KEY). | No embedding model name, embedding dimensionality, or chat model/provider is specified; these choices materially affect index dimensions and must be decided by the implementer. |
| App surface | ambiguous | no | "exposes a RAG agent that answers researcher questions" | - | Expose a simple HTTP API (Flask or FastAPI) with a POST /search (or /query) endpoint that accepts a question and returns an answer plus the ranked citations (pmid, year, optionally similarity scores and source snippets). The gallery sample will include a minimal CLI helper for seeding data. | The prompt does not require a UI vs API; a small HTTP API is the typical choice and is what the builder will most likely implement. |
| Provisioning and deployment | missing | no | skill_md: "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable ... Do not provision another cluster unless the run policy says Azure writes are allowed" | documentdb-azure-deployment | Do not attempt to create new cloud resources in the sample run. The documentdb-azure-deployment skill is available for authors who later want terraform/Bicep, but this gallery sample will use the provided live cluster and will not include provisioning code unless explicitly requested. | Reference requirements ask for infra-as-code, but the starter prompt/run environment forbids provisioning in this build — builder will likely omit infrastructure code. |
| Run and test instructions | missing | no | - | - | Builder will add a README with commands to create a venv, pip install -r requirements.txt, populate .env from .env.example, run a seed script, and start the server. Tests will be provided but unit tests will mock the DB/embedding calls so they can run without a live cluster. | No explicit run/test commands are provided in the starter prompt. |
| Definition of done | missing | no | - | - | Definition of done will be: seed script completes without errors; sample DB and index created in sample_healthcare_17; a query to /search returns an answer that cites at least one PubMed ID and year; the retrieved chunks are ranked by the DB similarity score. | No acceptance criteria are included in the prompt. |
| Constraints and non-goals | missing | no | skill_md: "Do not read or change other databases on the cluster; Do not provision another cluster unless allowed" | - | Cost/scale limits: keep the sample small (e.g., <= a few thousand vectors) and document how to scale. Non-goals: not intended as a production-ready secure deployment; no cross-region DR or CMK work in sample. | Only a few operational constraints are in skill_md; broader cost/non-goal guidance is not in the prompt. |
| Repository conventions | missing | no | - | - | Builder will create conventional layout (README.md, requirements.txt with pinned versions, src/ or app/, tests/, scripts/seed.py, .env.example) and use the name "Azure DocumentDB" throughout documentation. | The prompt did not specify .env.example, pinned requirements, test patterns, or README sections; these are gallery expectations and must be added by the implementer. |
