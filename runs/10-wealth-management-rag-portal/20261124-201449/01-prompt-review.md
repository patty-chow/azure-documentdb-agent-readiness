# 1. Prompt review: 10-wealth-management-rag-portal

**Verdict: sufficient_with_assumptions**

The starter prompt + provided skill.md give a clear goal (Python LlamaIndex RAG agent, portfolio-tool, DocumentDB vector store) and enough infra details (existing cluster, DB name, env var) to start building. Several important engineering choices are unspecified (Python version, embedding & LLM models and embedding dims, exact collection/schema, app surface, seed-data and tests, infra as code). Those will be chosen by the builder (see assumptions) unless the author clarifies them.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 4: Goal and scenario, Workflow type, Target service and tier, Authentication and secrets |
| Covered by a skill | 1: Queries and indexes |
| Ambiguous: builder will guess | 5: Language and runtime, Driver and version, Data model, App surface, Repository conventions |
| Missing: builder will guess | 6: Sample data, AI components, Provisioning and deployment, Run and test instructions, Definition of done, Constraints and non-goals |
| Not applicable | 0: - |

## Reference requirements at risk

- The vector index dimensions match the embedding model's output — embedding model/dimensions not specified in prompt or skill.md, so index-dimension correctness is at risk.
- The vector index parameters are chosen for the sample's data size, and the README says how to change them — index parameter choices and README guidance are not specified and likely to be minimal unless the author requests details.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — prompt doesn't require a seed script or idempotence; this is at risk.
- Search results include the similarity score — prompt does not require returning similarity scores; unless enforced by the builder this could be omitted.
- Dependencies are pinned in requirements.txt — prompt doesn't mandate pinned versions; this is commonly done but at risk if not specified.
- Unit tests run without a live cluster — tests are not mentioned; providing mocks and CI-friendly tests is at risk.
- Infrastructure for the cluster is provided as code — prompt and skill.md imply use of an existing cluster; providing IaC is at risk/likely omitted.
- The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name — the prompt doesn't insist on naming conventions; the repo might use 'DocumentDB' but could accidentally include 'Cosmos' or other names unless the author enforces it.

## Questions for the prompt author

- Which embedding model and provider should the sample use (e.g., OpenAI text-embedding-3-small, a HuggingFace model, or local Llama embeddings)? This sets the vector dimensionality used when creating the cosmosSearch index.
- Which chat LLM provider/model should the agent use for generation (OpenAI, Anthropic, local Llama)?
- Which Python version should be targeted (3.10, 3.11)?
- What app surface do you prefer for the gallery: simple HTTP API (FastAPI/Flask), a CLI interactive demo, or a small web UI (Streamlit)?
- Should the sample include infrastructure-as-code (Bicep/Terraform) for the cluster, or explicitly avoid provisioning and rely only on the provided cluster (skill.md indicates a cluster is already present)?
- Do you have canonical seed data to load, or should the builder synthesize small sample research and portfolio documents?

## Contradictions and missing references

- Prompt says "Using the DocumentDB skill" but there is no single installed skill named exactly "DocumentDB skill" — instead a set of granular documentdb-* skills are installed (e.g., documentdb-vector-search, documentdb-driver). This is a mild ambiguity about which skill(s) the builder should invoke.
- Reference requirements demand that vector index dimensions match the embedding model. The prompt does not specify an embedding model/dimension; skill.md and installed skills discuss vector indexes but do not supply the embedding model/dimension. This is a consequential gap rather than a direct contradiction.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python LlamaIndex RAG agent with agent memory that indexes wealth management research documents in a DocumentDB vector store... tool that fetches the client's portfolio document... combine portfolio context with retrieved research to answer relationship manager questions" | - | - | Clear business problem and user scenario. |
| Workflow type | specified | no | "LlamaIndex RAG agent with agent memory" | - | - | Single-agent RAG using LlamaIndex; agent memory explicitly requested. |
| Language and runtime | ambiguous | no | "Python" | documentdb-local-deployment | Builder will target a recent stable Python (likely 3.10 or 3.11). I would assume Python 3.11 for tooling and LlamaIndex compatibility. | Prompt says Python but no explicit version. skill.md says `python` resolves to a virtualenv on the developer machine but does not pin a version. |
| Driver and version | ambiguous | no | - | documentdb-driver | Use the official PyMongo driver (pymongo) with a recent 4.x release compatible with MongoDB wire protocol 7.0 (e.g., pymongo>=4.3,<5). Use MongoClient singleton pattern per documentdb-driver guidance. | No explicit driver/version in prompt; installed skill covers best practice but not a concrete pinned version. |
| Target service and tier | specified | no | - | - | Use the provided live vector-capable Azure DocumentDB cluster described in skill.md (compute tier M30, MongoDB 7.0, vector indexes available). | The shared skill.md run environment supplies the cluster/tier details. |
| Authentication and secrets | specified | no | - | - | The connection string is read from DOCUMENTDB_URI environment variable; do not write secrets into files or logs; use .env.example placeholders per skill.md. | skill.md explicitly instructs environment variable usage and MCP profile availability. |
| Data model | ambiguous | no | "indexes wealth management research documents ... agent has a tool that fetches the client's portfolio document" | documentdb-data-modeling | Create/use database `sample_banking_10` (skill.md). Create collections named `research_documents` (fields: _id, title, content/text, metadata, embedding) and `portfolios` (fields: client_id, positions array, metadata). Embeddings stored as a numeric array field on the research_documents documents. | Prompt does not specify collection names, document shapes, or keys; data-modeling skill provides patterns but not exact schema. |
| Sample data | missing | no | - | documentdb-local-deployment | Provide a small synthetic sample: ~30–100 research docs and a few portfolio documents, loaded by a seed script in `scripts/seed.py`. License: internal sample / permissive placeholder. The seed script should be idempotent (upsert by document id). | No source, size, or license; local-deployment skill discusses sample-data management but not the actual dataset. |
| Queries and indexes | covered_by_skill | no | "indexes ... in a DocumentDB vector store" and use of DocumentDB for retrieval | documentdb-vector-search, documentdb-indexing | Create a cosmosSearch vector index (choose one of vector-hnsw / vector-ivf / vector-diskann) in code on the embedding field. Index parameters will be tuned for the small sample by default (small ef/search params); README will note how to change for larger datasets. | Skills cover cosmosSearch vector indexes and index-shape guidance; however the required embedding dimension depends on the embedding model (not specified), which affects the index creation call. |
| AI components | missing | no | "LlamaIndex RAG agent" | - | Builder will pick a hosted embedding + chat model combination. A plausible default: OpenAI embeddings (text-embedding-3-small) and an OpenAI-compatible chat model (e.g., gpt-4o-mini or gpt-4o) invoked via LlamaIndex connectors. Embedding dimensionality will be assumed (e.g., 1536) and used to create the vector index unless the author specifies otherwise. | Embedding model and dimensions, chat model provider and calls are not specified — these choices materially affect index dims and API wiring. |
| App surface | ambiguous | no | - | - | Provide a minimal API and CLI: a small FastAPI/Flask `/query` HTTP endpoint that accepts a question and client_id and returns the agent answer plus source docs and similarity scores, plus a CLI demo script that runs interactive queries. Include `/seed` or separate `seed.py` to populate sample data. | Prompt does not say whether to build CLI, API, or UI; builder will pick a simple API + CLI for demos. |
| Provisioning and deployment | missing | no | "Using the DocumentDB skill" | documentdb-azure-deployment | Do not provision another cluster (skill.md forbids provisioning); use the existing cluster. The repo may include example IaC (Bicep) as optional/advisory, but the build will not create cloud resources during the sample run. | Prompt doesn't ask for infra-as-code. An infra skill exists but skill.md instructs to use the provided cluster. |
| Run and test instructions | missing | no | - | documentdb-local-deployment | README will include commands: `pip install -r requirements.txt`, set env vars (DOCUMENTDB_URI, OPENAI_API_KEY if used, MODEL names), `python scripts/seed.py`, `uvicorn app:app` (or `python app.py`), and sample query commands. Tests will be minimal; unit tests that do not require a live cluster will be provided (see tests mocking pymongo). | skill.md gives runtime env constraints but not full run/test steps; builder will author a README and scripts as usual. |
| Definition of done | missing | no | - | - | Acceptance: the app indexes research docs into DocumentDB with embeddings stored on documents and a cosmosSearch vector index created in code; the agent can fetch a portfolio by client_id, combine the portfolio context with retrieved research, and answer RM questions with memory across turns; sample queries and logs demonstrating retrieval and similarity scores are present. | No explicit acceptance criteria in the prompt. |
| Constraints and non-goals | missing | no | - | documentdb-security | Keep dataset small to limit cost; do not provision resources; secrets in env; do not attempt to productionize security or networking beyond mentioning best practices in README. Documentation will point to documentdb-security for production guidance. | No explicit constraints in prompt; security and cost guidance will be advisory. |
| Repository conventions | ambiguous | no | - | documentdb-local-deployment | Include README, `src/` (app code), `scripts/seed.py`, `requirements.txt` with pinned versions, `tests/` with unit tests that mock DB, and `.env.example` listing required env vars (DOCUMENTDB_URI, MODEL/OPENAI keys). Do not store secrets in repo. | skill.md explicitly instructs not to write connection strings and to use `.env.example`; other repo conventions are not mandated but follow common sample patterns. |
