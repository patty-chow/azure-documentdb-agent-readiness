# 1. Prompt review: 04-earnings-call-rag-assistant

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines the goal (Python + LlamaIndex RAG for earnings-call PDFs, chunking, embedding, storing vectors in Azure DocumentDB, retrieval with context-window-aware composition, and citation-by-source+timestamp). Many operational details (Python minor version, exact embedding/LLM models, dependency pinning, sample data source, CLI vs HTTP choice, and README/test/infrastructure artifacts) are left to the builder and will be chosen by convention or by installed skills. No single blocking unknown prevents a sensible start.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 6: Goal and scenario, Workflow type, Target service and tier, Authentication and secrets, Data model, Provisioning and deployment |
| Covered by a skill | 1: Queries and indexes |
| Ambiguous: builder will guess | 7: Language and runtime, Driver and version, Sample data, AI components, App surface, Constraints and non-goals, Repository conventions |
| Missing: builder will guess | 2: Run and test instructions, Definition of done |
| Not applicable | 0: - |

## Reference requirements at risk

- Include an automated or example script that demonstrates end-to-end flow (seed + query) — prompt does not explicitly require a repeatable seed script; builder may or may not add an idempotent seed script.
- The connection string and model credentials come from environment variables — skill_md covers DOCUMENTDB_URI, but embedding/LLM credentials are unspecified and at risk.
- A .env.example lists every setting with placeholder values — skill_md suggests using .env.example for DocumentDB URI but does not enumerate all model/LLM env vars; at risk unless builder adds them.
- The vector index dimensions match the embedding model's output — embedding model not specified, so matching dimensions are at risk.
- The vector index parameters are chosen for the sample's data size and README explains how to change them — index guidance exists in skills, but explicit parameters and README instructions are not specified by the prompt.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — not specified in the prompt; builder may omit idempotency.
- /search returns a clear error for an empty query and when the embedding call fails — error handling specifics are not described in the prompt.
- Search results include the similarity score — prompt asks to return top relevant chunks but doesn't require the similarity score to be returned.
- Dependencies are pinned in requirements.txt — prompt doesn't require pinned deps; at risk unless builder pins them.
- Unit tests run without a live cluster — prompt doesn't require offline/unit tests; at risk unless the builder provides mocks or fixtures.
- Infrastructure for the cluster is provided as code using the Azure DocumentDB resource type — prompt and skill_md advise using existing cluster; infra-as-code is not required and may be missing.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up — not specified in the prompt; likely to be incomplete unless the builder adds it.

## Questions for the prompt author

- Which embedding model and dimensions should be used (and which environment variable will hold its credentials)?
- Which LLM / chat model (provider and model name) should be used for answer synthesis (and how will credentials be provided)?
- Do you prefer a CLI demo, an HTTP endpoint, or both for the runnable demo entrypoint?
- Should the sample bundle include one or more example earnings-call PDFs (and is there a preferred public source or license to use)?
- Should the repo include pinned dependency versions (requirements.txt) and unit tests that run offline (mocking the cluster)?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python LlamaIndex RAG pipeline that ingests earnings call PDF transcripts, chunks and embeds them, stores the vectors in DocumentDB, and answers analyst questions by retrieving the top relevant chunks" | - | - | Clear business problem and demo scenario. |
| Workflow type | specified | no | "build a Python LlamaIndex RAG pipeline" (implies single-agent pipeline/process using LlamaIndex) | - | Builder will implement as a single-process (single-agent) application using Python + LlamaIndex (no multi-agent orchestration). | LlamaIndex-based RAG implies a single-agent pipeline; agent framework not needed. |
| Language and runtime | ambiguous | no | "Python LlamaIndex" | - | Use a recent Python 3.x runtime (typical choice: Python 3.10 or 3.11) and a virtualenv; document in README and requirements.txt. | Prompt specifies Python but not the exact version. skill_md says 'python' is available in run environment but gives no version. |
| Driver and version | ambiguous | no | - | documentdb-driver | Use the official pymongo Python driver (pymongo 4.x compatible with MongoDB 7.0), instantiate a singleton MongoClient per process as recommended by documentdb-driver. | documentdb-driver skill covers singleton / reuse patterns but does not prescribe an exact driver version. |
| Target service and tier | specified | no | Prompt requests Azure DocumentDB usage; run environment skill_md specifies an M30 cluster and MongoDB 7.0 wire protocol. | - | - | skill_md run environment: vector-capable Azure DocumentDB cluster, compute tier M30, MongoDB 7.0. |
| Authentication and secrets | specified | no | - | - | The DocumentDB connection string is read from the environment variable DOCUMENTDB_URI (do not write it into files); use a .env.example with placeholders. | skill_md explicitly requires DOCUMENTDB_URI env var and forbids embedding secrets in repo artifacts. |
| Data model | specified | no | "persist the embedding vectors and chunk text into Azure DocumentDB, storing for each vector a document containing at minimum: the embedding array, chunk text, source transcript identifier, and chunk timestamp range" | - | - | Document shape and required metadata are specified. Database name required by skill_md: sample_fintech_04. |
| Sample data | ambiguous | no | "ingests earnings call PDF transcripts" | - | Builder will include a small placeholder PDF in samples/ (e.g., samples/earnings_call_sample.pdf) and document that users should replace it with real transcripts; or provide a script that accepts user-supplied PDFs. | Prompt requires ingesting PDFs but does not prescribe a bundled sample, source, licensing, or size. |
| Queries and indexes | covered_by_skill | no | "similarity-search retrieval" and "store vectors in DocumentDB" | documentdb-vector-search, documentdb-indexing | Builder will create a cosmosSearch vector index (DiskANN recommended for M30) with dimensions matching the chosen embedding model and use $search + cosmosSearch for KNN queries. | Vector index strategy and query patterns are covered by documentdb-vector-search and documentdb-indexing skills. |
| AI components | ambiguous | no | "LlamaIndex" (implies an LLM + embeddings) but no model names or dimensions provided | - | Builder will pick a widely-used embedding model (e.g., OpenAI embeddings or an open MiniLM) and a compatible LLM backend accessible from LlamaIndex; explicitly document model names and embedding dimension and record them alongside vectors. | Prompt doesn't specify embedding model, embedding dimension, or which chat model/provider to call. Those choices materially affect index dimensions and vector index creation. |
| App surface | ambiguous | no | "Provide a runnable demo entrypoint (CLI or minimal HTTP endpoint) that accepts an analyst natural-language question" | - | Builder will include a minimal CLI entrypoint (e.g., ingest.py and query.py) and may optionally add a small FastAPI / Flask / HTTP example route (/search) for demonstration. | Prompt requires a runnable demo but leaves the form (CLI vs HTTP) open. |
| Provisioning and deployment | specified | no | - | - | Use the existing cluster reachable from the developer machine; do not provision a new cluster. If infra-as-code is provided, make it optional and do not run it in the default demo flow. | skill_md explicitly instructs to use the existing cluster and not to provision another unless allowed. |
| Run and test instructions | missing | no | - | - | Builder will add a README with commands: create venv, pip install -r requirements.txt, set DOCUMENTDB_URI and model env vars, run sample ingestion script, then run query CLI/HTTP to demonstrate retrieval and citation. | Prompt does not include runnable commands or test instructions; these must be added by the builder. |
| Definition of done | missing | no | - | - | Use the reasonable acceptance criteria: ingest at least one PDF into the sample_fintech_04 DB, create vector index, retrieve top-k chunks for a sample query, and produce an answer with source filename + timestamp citations. | No explicit success criteria provided in the prompt; the reference requirements define expected checks. |
| Constraints and non-goals | ambiguous | no | "Use context engineering to fit retrieved passages within the LLM context window" (some constraint) and skill_md forbids writing secrets | - | Keep dataset small for demo, do not provision cloud infra, use env vars for secrets, and avoid including real credentials or large datasets in the repo. | Cost/scale limits, licenses, and other non-goals are not fully specified; skill_md provides a few security constraints. |
| Repository conventions | ambiguous | no | - | - | Include README, requirements.txt with pinned deps, .env.example with placeholders, src/ or app/ layout, samples/ for PDFs, a scripts/ folder for ingest/query demos. | skill_md requires DATABASE name and environment variable usage; broader repo conventions are not stated in the prompt. |
