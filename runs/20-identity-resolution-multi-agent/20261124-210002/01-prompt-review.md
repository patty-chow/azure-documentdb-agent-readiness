# 1. Prompt review: 20-identity-resolution-multi-agent

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines a Python + LangChain multi-agent identity-resolution scenario using Beanie ODM and an orchestrator that writes a golden record to Azure DocumentDB; the run environment (live M30 vector-capable cluster, database name, and DOCUMENTDB_URI env var) is specified in skill.md. Several implementation details are left unspecified (Python version, exact driver versions, embedding/chat models and providers, API vs CLI surface, index parameters, README/tests/packaging), but installed DocumentDB skills cover best-practice choices for client usage, seeding, vector index design, and connection handling, so a builder can start and will fill the rest with sensible defaults unless the author specifies otherwise.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Workflow type, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Covered by a skill | 1: Queries and indexes |
| Ambiguous: builder will guess | 4: Language and runtime, Driver and version, Data model, App surface |
| Missing: builder will guess | 6: Sample data, AI components, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- Model credentials come from environment variables: The run environment declares DOCUMENTDB_URI in env, but the prompt does not require LLM/model credentials to be loaded from env; no skill enforces this. (At risk.)
- .env.example lists every setting with placeholder values: The prompt and skill.md state to avoid writing the connection string and to use a .env.example, but the starter prompt does not explicitly require creating a .env.example; builder may or may not include it. (At risk.)
- Vector index dimensions match the embedding model's output: The prompt requests LLM-assisted similarity scoring but does not name an embedding model or its dimensionality; without that the builder must assume a model and choose index dimensions. (At risk.)
- Vector index parameters chosen for the sample's data size and README guidance: The prompt does not specify index parameters or a README explanation; although documentdb-vector-search skill gives guidance, the sample may omit README-level tuning instructions. (At risk.)
- /search returns a clear error for an empty query and when the embedding call fails: The prompt asks for matching and scoring but does not require robust API error handling; no installed skill explicitly mandates these endpoint error behaviors. (At risk.)
- Dependencies are pinned in requirements.txt: Prompt doesn't require pinned versions; installed skills give best-practice advice but don't enforce pinned dependency files. (At risk.)
- Unit tests run without a live cluster: The prompt and skill.md expect testing against the live cluster for verification but don't mandate unit tests that run offline (mocking). No installed skill provides a test harness for offline unit tests. (At risk.)
- Infrastructure for the cluster provided as code using the Azure DocumentDB resource type: The run environment explicitly says a cluster exists and forbids provisioning; the prompt doesn't request IaC. If the gallery requires IaC, this will be missing. (At risk.)
- README covers what the sample shows, prerequisites, setup, run, and clean-up: The prompt does not ask for README content explicitly; builder may or may not produce a full README with required sections. (At risk.)

## Questions for the prompt author

- Which embedding model and LLM/chat provider should the sample use (e.g., OpenAI text-embedding-3-small and GPT-4o-mini)? This choice determines vector dimension and index parameters.
- Should the sample expose a REST API (e.g., FastAPI /resolve) or only a CLI/script-based orchestrator? This affects the app surface and example usage.
- Do you require infrastructure-as-code (Bicep/Terraform) for provisioning an Azure DocumentDB resource as part of the sample, or must the sample strictly use the provided live cluster?
- Do you want pinned dependency versions in requirements.txt and unit tests that run without a live cluster (mocks/fakes), or is a simpler integration-style test sufficient?

## Contradictions and missing references

- Prompt says "Using the DocumentDB skill" (singular). There is no single installed skill named exactly "documentdb"; functionality is split across many 'documentdb-*' skills. Builder will need to pick which DocumentDB skills to consult.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python LangChain multi-agent identity resolution system ... where a match agent finds candidate duplicate profiles ... a merge agent consolidates ... an audit agent logs every merge decision ... The orchestrator writes the final golden record to DocumentDB." | - | - | Clear business problem and sample demonstration are stated. |
| Workflow type | specified | no | "Python LangChain multi-agent ... match agent ... merge agent ... audit agent ... orchestrator" | - | - | Multi-agent orchestration with LangChain is explicit. |
| Language and runtime | ambiguous | no | "Python LangChain" and skill.md: "python and pip resolve to a virtual environment created for this run" | documentdb-local-deployment | Use Python 3.10 (or 3.11) in a virtualenv; pip installs target that interpreter. | Prompt says Python but gives no explicit version; skill.md only states python/pip are available in the environment. |
| Driver and version | ambiguous | no | - | documentdb-driver | Use pymongo + motor compatible with MongoDB 7.0 (e.g., pymongo 4.x and motor 3.x) and Beanie recent stable release; use driver-singleton-client pattern. | Prompt requires Beanie ODM (which implies motor/pymongo) but does not name driver versions; documentdb-driver provides singleton/reuse guidance but not exact pinned versions. |
| Target service and tier | specified | no | skill.md: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) ... DOCUMENTDB_URI ... Use the database named `sample_customer_360_20`" | - | - | Live cluster and database name are provided by the run environment in skill.md; builder must not provision another cluster. |
| Authentication and secrets | specified | no | skill.md: "connection string is in the environment variable `DOCUMENTDB_URI`. Read it from the environment at run time. Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder" | - | - | DocumentDB connection secret location is explicit; LLM/model credentials are not specified (see AI components). |
| Data model | ambiguous | no | "using Beanie ODM ... customer profiles, golden records and audit entries" (prompt asks for models) | documentdb-data-modeling | Builder will create minimal Beanie Document models: Profile (name, emails, phones, address, embedding vector, source metadata), GoldenRecord (merged fields, provenance refs), AuditEntry (timestamp, merged_ids, confidence, source_docs or refs). Collections named `profiles`, `golden_profiles`, `merge_audits`. | Prompt requires models but does not specify field shapes, indexes, or shard keys; documentdb-data-modeling can guide modeling decisions. |
| Sample data | missing | no | - | documentdb-local-deployment | Provide a small synthetic seed (e.g., 50–500 sample profiles with controlled duplicates) via an idempotent seed script; include CSV/JSON generator; license = MIT/sample. | No dataset, size, license, or loading script is specified in the prompt; local-deployment skill suggests patterns but the starter prompt does not request sample data explicitly. |
| Queries and indexes | covered_by_skill | no | "match agent finds candidate duplicate profiles in DocumentDB ... LLM-assisted similarity scoring" (implies vector/semantic matching) | documentdb-vector-search | Create a `cosmosSearch` vector index (likely `vector-diskann` for M30) on a stored embedding field with `dimensions` matching chosen embedding model; also add single-field indexes (email, phone) for pre-filtering. | The prompt implies vector search but does not state index types/parameters; documentdb-vector-search gives concrete guidance for index type and tuning. |
| AI components | missing | no | "LLM-assisted similarity scoring" | - | Builder will choose an embedding model and a chat/LLM provider (commonly OpenAI embeddings for semantic similarity, e.g., text-embedding-3-small or similar) and store embeddings with known dimensionality (e.g., 1536). The LLM used for decision/merge steps will be supplied via env vars (API keys) and called from the orchestrator/agents. | Prompt requires LLM-assisted scoring but provides no provider, model names, dimensions, or call locations; these choices materially affect index dimension and code. |
| App surface | ambiguous | no | Orchestrator writes final golden record to DocumentDB; agents built with LangChain | - | Builder will implement a simple CLI and a minimal REST API (FastAPI) with an endpoint like POST /resolve that runs the orchestrator; also provide a CLI `python -m sample.resolve --file sample.json` for local runs. | Prompt does not prescribe CLI vs API vs UI; choice affects example usage and tests. |
| Provisioning and deployment | specified | no | skill.md: "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned ... Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use." | - | - | The environment explicitly provides a live cluster and forbids creating another; no infra provisioning is required by the prompt. |
| Run and test instructions | missing | no | - | documentdb-local-deployment | README will include commands: pip install -r requirements.txt, export DOCUMENTDB_URI and LLM env vars, python seed_data.py, python run_orchestrator.py, pytest (unit tests will mock DB). | Prompt does not include run/test steps; skill.md gives environment expectations but not explicit commands or tests. |
| Definition of done | missing | no | - | - | Definition of done will be: sample runs end-to-end against provided cluster, seed script executed, run that resolves at least one duplicate yielding a golden record written to `sample_customer_360_20`, and an audit entry recorded with confidence and source references. | No explicit acceptance criteria were provided in the prompt. |
| Constraints and non-goals | missing | no | - | - | Avoid provisioning new clusters; keep sample small and cost-conscious; do not include production-grade security (beyond using env vars) unless requested. | No cost limits, compliance notes, or non-goals are given. |
| Repository conventions | missing | no | - | - | Use conventional layout: README.md, requirements.txt, src/ (package), tests/, seed_data.py, .env.example; use name "Azure DocumentDB" in docs. | Prompt doesn't specify folder layout, README sections, or dependency pinning; these are implementation-level choices. |
