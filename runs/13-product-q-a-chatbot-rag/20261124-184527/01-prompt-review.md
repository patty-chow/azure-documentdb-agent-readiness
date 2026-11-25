# 1. Prompt review: 13-product-q-a-chatbot-rag

**Verdict: sufficient_with_assumptions**

The starter prompt is clear about the core goal (a Python LlamaIndex RAG chatbot that indexes product descriptions/specs/reviews into an Azure DocumentDB vector store and returns top-5 chunks). The run environment (existing M30 cluster, DOCUMENTDB_URI, use of .env.example, etc.) and many DocumentDB best-practices are present in the supplied skill.md and installed skills, so a builder can start; several implementation details (Python version, exact driver and model choices, app surface, tests, index parameters, and explicit citation format) will be filled in by the builder's defaults unless the author clarifies them.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Workflow type, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Covered by a skill | 1: Queries and indexes |
| Ambiguous: builder will guess | 6: Language and runtime, Driver and version, Data model, App surface, Constraints and non-goals, Repository conventions |
| Missing: builder will guess | 4: Sample data, AI components, Run and test instructions, Definition of done |
| Not applicable | 0: - |

## Reference requirements at risk

- Ingest product data types and create Document objects with metadata indicating product_id and source_type — prompt mentions content types but does not require or specify per-chunk metadata fields; no installed skill prescribes the exact metadata format.
- Chunk long product documents and store chunk-level metadata — prompt asks for context engineering but doesn't explicitly require chunking or chunk-metadata persistence; the builder must decide chunk size and metadata scheme.
- Implement configurable max context/token budget and trimming/summarization to fit the budget — prompt asks to apply context engineering but doesn't specify configuration interfaces or exact techniques; this is underspecified.
- Ensure generated answers are grounded with explicit citations (product_id and chunk_id or source_type) — prompt requests grounded answers but does not mandate citation format or placement; the builder may or may not include explicit identifiers in the response.
- Provide an end-to-end example or automated test that indexes sample data, queries with a sample question, verifies retrieval returned 5 chunks, and asserts the LLM output contains grounded citations — prompt does not request tests/examples explicitly.
- AI credentials and embedding model config come from environment variables — DOCUMENTDB_URI is specified in skill.md, but embedding/LLM provider credentials are not specified; the prompt does not require .env entries for model credentials.
- Vector index dimensions match embedding model's output — embedding model not specified, so the code may not set index dimensions correctly unless the builder chooses a model and records dimensions.
- Vector index parameters are chosen for the sample's data size and README explains how to change them — prompt doesn't define index parameter values or documentation requirements.
- Seed script that loads sample data and can be run twice without duplicating data — prompt doesn't require idempotent seed behavior nor provide a seed script contract.
- /search returns clear errors for empty query and when the embedding call fails — the prompt doesn't require specific HTTP behavior or error handling for these cases.
- Search results include similarity score — prompt asks for top-5 retrieval and grounded answer but doesn't require returning similarity scores.
- Dependencies pinned in requirements.txt — not requested; the builder must decide to pin versions.
- Unit tests run without a live cluster — the reference expects tests that run offline; the prompt asks to verify against the live cluster in skill.md, which suggests integration tests but doesn't specify offline unit tests.
- Infrastructure for the cluster provided as code (Azure DocumentDB resource type) — the run environment forbids provisioning another cluster; the prompt doesn't request IaC, so this will likely be missing.
- README covering what the sample shows, prerequisites, setup, run, and clean-up — the prompt doesn't explicitly require a README, though it's expected for gallery samples.

## Questions for the prompt author

- Which embedding model and LLM should the sample use (provider and specific model)? This determines vector dimensionality, index creation, and example config (e.g., OpenAI text-embedding-3-small vs a local embedding model).
- Which Python minor version should the sample target (3.10, 3.11)? This affects dependency pins and CI/test config.
- Do you want a minimal HTTP API (e.g., FastAPI /search endpoint) in the sample, or is a CLI-only example sufficient? The reference expects a /search route and error behaviors.
- Should the sample include infrastructure-as-code for the DocumentDB cluster, or explicitly avoid provisioning new cloud resources (the run environment indicates an existing cluster)?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python LlamaIndex RAG chatbot that indexes product descriptions, specs, and reviews into a DocumentDB vector store." | - | - | - |
| Workflow type | specified | no | Single-app chatbot request (no orchestration or multi-agent mention). | - | - | The prompt implies a single-agent single-process app (RAG pipeline in one program). |
| Language and runtime | ambiguous | no | "Python LlamaIndex" and the skill.md note that `python` and `pip` point to a virtual environment. | - | Builder will target a modern Python 3.x (commonly 3.10 or 3.11). I would assume Python 3.10 for packaging and compatibility. | No explicit Python minor version or packaging/runtime (venv, poetry) was specified. |
| Driver and version | ambiguous | no | - | documentdb-driver | Use the Python pymongo driver compatible with MongoDB 7.0 (e.g., pymongo 4.x). Follow the documentdb-driver guidance to implement a singleton MongoClient. | The documentdb-driver skill gives best-practice patterns (singleton client) but doesn't mandate a concrete driver version. |
| Target service and tier | specified | no | skill.md: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) is reachable..." | - | - | The run environment explicitly describes the live cluster and database name (`sample_retail_13`). |
| Authentication and secrets | specified | no | skill.md: "connection string is in the environment variable `DOCUMENTDB_URI`. Read it from the environment at run time. Never write its value into any file... use a config file or `.env.example` with a placeholder" | - | - | This clearly specifies where the cluster connection secret lives and how to treat it. |
| Data model | ambiguous | no | "indexes product descriptions, specs, and reviews into a DocumentDB vector store." | documentdb-data-modeling | Builder will create a collection (e.g., `product_chunks`) storing chunk documents with fields: product_id, source_type (description/spec/review), chunk_id, text, embedding (vector), plus optional metadata (title, language, created_at). Chunk-level metadata will be used as citations. | Prompt names the content types but doesn't specify exact DB/collection names, field shapes, or whether to embed documents vs references. The data-modeling skill provides patterns but no concrete schema was given in the prompt. |
| Sample data | missing | no | - | - | Include a small synthetic sample set in repo (e.g., 3 products with description/spec/reviews in JSON/CSV) and a seed script to ingest them. The dataset will be small (dozens of chunks) so the sample can run cheaply against the provided cluster. | The prompt doesn't include or reference sample data; the builder must add one to demonstrate the pipeline. |
| Queries and indexes | covered_by_skill | no | "index into a DocumentDB vector store" and retrieval of top 5 chunks | documentdb-vector-search | Builder will follow documentdb-vector-search guidance: create a `cosmosSearch` vector index (likely `vector-diskann` on the M30 cluster) with dimensions matching chosen embedding model and similarity=cosine, and will query via `$search` + `cosmosSearch` knn. | The skill contains guidance on index sub-types (DiskANN/HNSW/IVF) and query tuning; the prompt leaves index choice to the implementer. |
| AI components | missing | no | "LlamaIndex RAG chatbot" but no model or embedding provider specified | - | Builder will pick specific embedding and chat models (common choice: OpenAI embeddings like text-embedding-3-* and an OpenAI chat model) and wire credentials via environment variables (e.g., OPENAI_API_KEY). Embedding output dimension must be recorded and used to create the vector index. | No embedding model, dimension, LLM provider or call site was specified; these materially affect index dimensions and code. |
| App surface | ambiguous | no | The prompt calls the project a "chatbot" and requests a per-question retrieval + generation flow. | - | Implement a single-process app exposing: (1) a CLI/`index.py` to ingest/seed data and build the index; (2) a minimal HTTP API (FastAPI or Flask) with a /chat or /search endpoint that accepts a user query, returns the top-5 chunks, similarity scores and a grounded answer. Also include an example script that runs a sample query locally. | The prompt does not mandate CLI vs web UI; builders commonly include a minimal API plus an example CLI. |
| Provisioning and deployment | specified | no | skill.md: "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable... Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use." | - | - | The run environment explicitly says to use the existing cluster — sample should not create cloud resources by default. |
| Run and test instructions | missing | no | - | - | Builder will add a README with commands to create a virtualenv, pip install -r requirements.txt, run `seed.py` to ingest sample data, start the API, and run a sample query. Tests: include an end-to-end test that uses the seed data and asserts retrieval/top-5 and citations; tests may be tagged as integration and require a live cluster unless mocked. | No explicit run/test commands were provided in the prompt. |
| Definition of done | missing | no | - | - | The sample's acceptance criteria will be: code runs locally with required env vars, seed script populates the DB, a sample query returns exactly 5 retrieved chunks and an LLM-generated answer that includes citations (product_id/chunk_id/source_type), and unit/integration tests pass. | The prompt describes behavior but not a concise checklist; builder will infer acceptance criteria. |
| Constraints and non-goals | ambiguous | no | "Apply context engineering to keep the prompt within token limits when product docs are long." | - | Constrain sample to small dataset to control compute/cost; do not provision new cloud resources; implement a configurable token/context budget and a simple summarization/trimming strategy to enforce it. | Cost constraints, licensing, and compliance requirements are not stated; only token-limit handling is requested. |
| Repository conventions | ambiguous | no | skill.md instruction: "use a config file or `.env.example` with a placeholder" and run env describing virtualenv, python, node availability. | documentdb-local-deployment | Follow common gallery layout: README.md, requirements.txt (pinned versions), src/ or app/, tests/, scripts/seed.py, .env.example, and a small example dataset folder. | The prompt and skill.md hint at .env.example and virtualenv usage, but do not spell out full repo conventions (folder layout, pinned deps, README sections). |
