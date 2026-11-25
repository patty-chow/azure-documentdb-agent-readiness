# 1. Prompt review: 04-regulatory-reporting-orchestration

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines a Python LangChain orchestration with three agents (data-extraction, validation, filing) and asks the orchestrator to log workflow documents in Azure DocumentDB. The provided run-environment skill.md supplies an existing cluster, DB name, and the DOCUMENTDB_URI environment variable. Several implementation details are missing (Python version, concrete data model, indexes, AI model selection, app surface, infra-as-code, tests, and README), which a builder will fill with reasonable defaults unless the author clarifies them.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 4: Goal and scenario, Workflow type, Target service and tier, Authentication and secrets |
| Covered by a skill | 1: Driver and version |
| Ambiguous: builder will guess | 1: Repository conventions |
| Missing: builder will guess | 10: Language and runtime, Data model, Sample data, Queries and indexes, AI components, App surface, Provisioning and deployment, Run and test instructions, Definition of done, Constraints and non-goals |
| Not applicable | 0: - |

## Reference requirements at risk

- The connection string and model credentials come from environment variables; none appear in the repository. — skill.md gives DOCUMENTDB_URI for the DB, but model credentials for LLM/embedding are unspecified in prompt and skills, so builder will need to choose env var names and .env.example entries.
- A .env.example lists every setting with placeholder values. — prompt does not request this explicitly; skill.md says read URI from env but does not require .env.example; likely missing.
- The vector index dimensions match the embedding model's output. — embedding model/dimensions are not specified, so index dimensions are at risk of mismatch.
- The vector index parameters are chosen for the sample's data size and README explains how to change them. — prompt does not specify index parameters nor document sizing guidance.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data. — prompt does not request a seed script; skill.md expects verification against the live cluster but sample data creation is not specified.
- /search returns a clear error for an empty query and when the embedding call fails. — prompt does not define a /search endpoint or error handling requirements.
- Search results include the similarity score. — the prompt does not request search output format or similarity scores.
- Dependencies are pinned in requirements.txt. — prompt does not mention dependency pinning; builder may or may not pin versions.
- Unit tests run without a live cluster. — no testing strategy in prompt; writer must add mocks or fixtures to avoid requiring a live cluster.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. — prompt and skill.md discourage provisioning a new cluster; infra-as-code is not requested and likely will be omitted unless author requests it.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up. — prompt does not explicitly demand a full README, though skill.md implies some run-time checks; this is at risk if the builder doesn't add it.

## Questions for the prompt author

- Which Python interpreter version should the sample target? (e.g., 3.10, 3.11)
- Do you want the sample to include infra-as-code (Bicep / Terraform / az CLI) to create the cluster, or must it rely solely on the existing cluster declared in skill.md?
- Which LLM/embedding provider and model do you want the sample to use for the agents (e.g., OpenAI text-embedding-3-small + gpt-4o-mini), or should model selection be entirely configurable via environment variables with no default?
- Should the sample expose a CLI only, or also provide a simple HTTP endpoint (FastAPI/Flask) to trigger the pipeline?
- Do you have a target regulatory schema (e.g., an XBRL fragment, a provided JSON schema) the filing agent must produce, or should the sample use a small illustrative JSON schema?
- How large should the seed dataset be for the sample (a handful of documents, hundreds, or a few thousand)?

## Contradictions and missing references

- Prompt says "Using the DocumentDB skill" — there is not a single installed skill named exactly "DocumentDB skill", but many 'documentdb-*' skills are available. This is not blocking, but the builder must pick the appropriate skills (connection, driver, indexing, etc.).
- skill.md/run environment instructs 'Do not provision another cluster unless the run policy says Azure writes are allowed'; the prompt does not request provisioning but an implementer might be tempted to add infra-as-code — the run environment restricts that unless permitted.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python LangChain orchestration pipeline where a data-extraction agent queries multiple DocumentDB collections... a validation agent checks completeness..., and a filing agent formats the output to the required regulatory schema." | - | - | Business goal and demo scenario are clearly stated in the starter prompt. |
| Workflow type | specified | no | "Python LangChain orchestration pipeline" with distinct agent roles (data-extraction, validation, filing) and an orchestrator. | - | - | Multi-agent orchestration using LangChain is explicit. |
| Language and runtime | missing | no | "Python" (LangChain) is specified but no interpreter version or runtime constraints are given. | - | Builder will assume a modern, commonly-available Python 3.x — e.g., Python 3.10 (or 3.11) virtualenv/venv. The repo will include a requirements.txt and dev instructions for creating a virtualenv. | No explicit Python version; this affects dependency pinning and CI. |
| Driver and version | covered_by_skill | no | - | documentdb-connection (and documentdb-driver) | Use PyMongo (pymongo) and follow guidance in documentdb-connection (recommend PyMongo 4.9+ for async support; reuse a singleton MongoClient). | Skills recommend PyMongo and the singleton MongoClient pattern; connection tuning guidance is available. |
| Target service and tier | specified | no | - | - | - | skill.md/run environment: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) is reachable... use database named `sample_banking_04` and DOCUMENTDB_URI env var." |
| Authentication and secrets | specified | no | - | - | - | skill.md instructs the connection string is available in environment variable DOCUMENTDB_URI and must not be written into files or logs. |
| Data model | missing | no | "queries multiple DocumentDB collections for reporting period data" — but no collection names, document shapes, or shard keys are given. | documentdb-data-modeling (guidance only) | Builder will invent a small example schema suitable for regulatory reporting, e.g.: collections 'accounts', 'transactions', 'positions', plus a 'workflow_runs' collection for orchestrator logging. Example document shapes: transactions { _id, account_id, date, amount, currency, reporting_period }, accounts { _id, name, region }, workflow_runs { run_id, steps: [{name,status,timestamp,msg}], start_ts, end_ts }. | Skill can guide modeling but does not supply the concrete schema the sample needs. |
| Sample data | missing | no | - | documentdb-local-deployment (general dev-data practices) | Create a small idempotent seed script (scripts/seed.py) that upserts ~50–500 sample documents across the example collections. The script should be safe to run twice (use upsert on a unique key). | Starter prompt does not request or describe seed data; skill.md asks to verify against the live cluster but does not include the sample dataset. |
| Queries and indexes | missing | no | "queries multiple DocumentDB collections... filtered to the reporting period" — query patterns are implied but no indexes are specified. | documentdb-indexing (guidance available) | Builder will add indexes supporting the reporting-period queries, e.g. compound index on { reporting_period: 1, date: 1 }, index on account_id, and an index for the workflow_runs collection on run_id / start_ts. If vector search is used, create a vector index with example parameters compatible with the chosen embedding model (dimensions set to model output). | Index shapes and parameters need explicit design; a documentdb-indexing skill can help choose them. |
| AI components | missing | no | "LangChain orchestration pipeline" — but no embedding model, chat model, provider, or dimensions are specified. | documentdb-vector-search (guidance) and general LangChain usage is implied but not supplied as an installed skill here. | Make model/provider configurable via environment variables (e.g., OPENAI_API_KEY and MODEL_NAME). Example defaults in the sample: OpenAI embeddings (text-embedding-3-small, 1536 dims) and an OpenAI chat model (e.g., gpt-4o-mini). All model parameters should be configurable in .env.example. | Which models to call, where to call them (agents), and embedding dims are not specified and will materially affect indexes and behaviour. |
| App surface | missing | no | Orchestrator, agents and logging are requested but no CLI/API/UI surface is specified. | - | Builder will implement a simple CLI entrypoint (e.g., scripts/run_report.py or src/main.py) to run the orchestration and a small optional Flask/FastAPI endpoint for on-demand runs. The primary demo will be the CLI script that runs the pipeline and prints / writes the formatted regulatory output file. | App surface affects how credentials are loaded, logging, and tests. |
| Provisioning and deployment | missing | no | - | documentdb-azure-deployment (available if the author wants infra-as-code) | Do not provision a cluster in the sample; use the existing cluster described in skill.md. The sample will not include Bicep/ARM/Terraform by default unless the author requests it. | The run environment explicitly says a cluster already exists and warns not to provision another unless allowed; that constrains whether infra-as-code is provided. |
| Run and test instructions | missing | no | - | - | Builder will include a README with commands: create venv, pip install -r requirements.txt, set env vars (.env from .env.example), run scripts/seed.py, run scripts/run_report.py. Tests will be local unit tests that mock the DB unless the author requests live integration tests. | No explicit run/test steps are in the prompt or skill.md; skill.md gives runtime constraints but not the exact commands to include in README. |
| Definition of done | missing | no | - | - | Acceptance criteria the builder will adopt: (1) a CLI that runs the orchestrator end-to-end; (2) extracted data comes from at least two collections filtered by reporting period; (3) validation agent emits pass/fail with details; (4) filing agent produces a formatted regulatory document (JSON or a small example schema) saved to disk and stored/annotated in a workflow_runs document; (5) a workflow_runs document records step statuses. | No explicit 'done' checklist in the prompt; builder will use these pragmatic criteria. |
| Constraints and non-goals | missing | no | - | documentdb-security (guidance available) | Sample will be limited to a small, synthetic dataset for local demo; it will not implement production-grade security (no CMK, no private endpoints) but will document best-practices and warnings in README. | No cost, privacy, or compliance constraints are specified in the prompt. |
| Repository conventions | ambiguous | no | skill.md specifies database name `sample_banking_04` and env var DOCUMENTDB_URI and forbids writing the connection string to files. | - | Builder will follow common conventions: top-level README, src/ package, scripts/ (seed.py, run_report.py), tests/, .env.example with placeholders, requirements.txt with pinned dependencies, and an examples/ output folder. The sample will use the term 'Azure DocumentDB' in docs as requested by gallery conventions. | Some repo conventions are implied by skill.md but many details (pinning policy, CI, telemetry) are not specified. |
