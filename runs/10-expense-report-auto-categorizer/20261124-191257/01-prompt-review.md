# 1. Prompt review: 10-expense-report-auto-categorizer

**Verdict: sufficient_with_assumptions**

The starter prompt clearly states the core goal (a Python LangChain agent using Beanie to read, categorise, flag, and write expense reports) and agent-memory requirement; many DocumentDB operational details are supplied in the run environment (skill_md). Several implementation details are left unspecified (Python/runtime version, exact driver versions, AI model choices, app surface, indexes, seed data, CI/tests, README/infrastructure), so the builder will proceed with sensible defaults unless the author clarifies those items.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 4: Goal and scenario, Workflow type, Target service and tier, Authentication and secrets |
| Covered by a skill | 0: - |
| Ambiguous: builder will guess | 5: Language and runtime, Driver and version, Data model, Queries and indexes, App surface |
| Missing: builder will guess | 7: Sample data, AI components, Provisioning and deployment, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- The connection string and model credentials come from environment variables; none appear in the repository. Reason: The starter prompt doesn't say which env var names beyond DocumentDB (skill_md sets DOCUMENTDB_URI but model/API keys are unspecified).
- .env.example lists every setting with placeholder values. Reason: Prompt does not request a .env.example; builder may or may not include it unless instructed.
- The vector index dimensions match the embedding model's output. Reason: No embedding model is specified, so index dims cannot be chosen confidently.
- The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. Reason: No guidance on data size or specific vector-model; left to implementer.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data. Reason: Prompt doesn't request sample-data seed script; likely missing unless the builder opts to add one.
- /search returns a clear error for an empty query and when the embedding call fails. Reason: Prompt doesn't mention a search endpoint; if added, these error cases must be implemented explicitly.
- Search results include the similarity score. Reason: Prompt doesn't state there will be a search feature; similarity score handling is therefore at risk.
- Dependencies are pinned in requirements.txt. Reason: Prompt did not ask for pinned deps; implementer may or may not pin versions.
- Unit tests run without a live cluster. Reason: Tests are not mentioned and mocking requirements aren't specified.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. Reason: Prompt does not request infrastructure-as-code; skill_md suggests using an existing cluster.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up. Reason: Prompt doesn't request README contents explicitly; builder may add a README but specifics are not provided.
- The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name. Reason: Prompt doesn't instruct documentation wording; builder may not follow branding guidance unless told.

## Questions for the prompt author

- Which LLM / embedding provider and exact model(s) should be used (e.g., OpenAI text-embedding-3-small and gpt-4o-mini)? This determines embedding dimensions and env vars.
- Do you want a CLI/demo script only, or should the sample expose an HTTP API or web UI route (e.g., /process, /search)?
- Should the sample include infra-as-code (Bicep/Terraform) to provision the DocumentDB cluster, or must it always use the existing cluster described in skill_md?
- Which Python version should the sample target (3.10, 3.11)?
- Please confirm required test behaviour: must unit tests run without a live cluster (mocking) — should tests be included?
- Do you want a seed script and, if so, roughly how many sample reports (small ~8–20) and whether the seed must be strictly idempotent?

## Contradictions and missing references

- Prompt: "Using the DocumentDB skill" — there is no single installed skill named exactly "DocumentDB skill"; the environment provides several documentdb-* skills (documentdb-driver, documentdb-indexing, documentdb-vector-search, etc.). Builder must map the instruction to the available skills.
- skill_md/run environment forbids provisioning another cluster and specifies a live M30 cluster; the prompt doesn't mention this constraint explicitly. The builder must not attempt to create a new cluster unless told otherwise.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "reads submitted expense reports from DocumentDB, uses prompt engineering to categorise each line item against company policy, flags policy violations, and writes the enriched report back." | - | - | Clear business problem and expected behaviour. |
| Workflow type | specified | no | "build a Python LangChain agent using Beanie ODM" — single LangChain agent orchestrating per-report processing. | - | - | Single-agent LangChain orchestration is explicitly requested. |
| Language and runtime | ambiguous | no | "Python" | - | Assume modern CPython 3.10 or 3.11 (most samples target 3.11); create a virtualenv and document that requirement in README/.env.example. | Prompt names Python but gives no version or runtime details; a builder will pick a recent stable Python (3.10/3.11). |
| Driver and version | ambiguous | no | "Use Beanie ODM" | documentdb-driver | Use Beanie (latest compatible release) with Motor (async) and a current PyMongo-compatible driver (PyMongo 4.x, Motor 3.x) and apply the documentdb-driver guidance to reuse a singleton MongoClient/MotorClient. | The prompt requires Beanie but does not name driver versions; the documentdb-driver skill gives client-reuse best practices but not exact version pins. |
| Target service and tier | specified | no | Run environment (skill_md): "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) is reachable... Use the database named `sample_fintech_10` for everything this sample creates." | - | - | Run environment explicitly supplies the live cluster and database to use. |
| Authentication and secrets | specified | no | Run environment (skill_md): "Its connection string is in the environment variable `DOCUMENTDB_URI`. Read it from the environment at run time. Never write its value into any file..." | documentdb-mcp-setup | - | Connection string location and secrecy rules are provided in the run environment and MCP guidance. |
| Data model | ambiguous | no | "Use Beanie ODM ... define Beanie Document models representing expense reports and their line items." | documentdb-data-modeling | Builder will implement a Report document with fields: _id, report_id, status (e.g., 'submitted'), submitter metadata, items: [ { item_id, date, merchant, amount, description, category, policy_violation (bool), violation_reason (str) } ], plus schema_version and timestamps. No shard key chosen (single-shard usage). | The prompt requires models but doesn't list fields; the documentdb-data-modeling skill can advise on embedding vs referencing and document size limits. |
| Sample data | missing | no | - | - | Include a small idempotent seed script that inserts ~8–20 example reports covering a variety of line items / violations; make seed idempotent by using a stable report_id or upsert semantics. | No sample-data source, size, license, or loader is specified; the builder will need to add a seed script. |
| Queries and indexes | ambiguous | no | - | documentdb-indexing | Create an index on report status (e.g., {status:1}) to find submitted reports, possibly an index on submitter/date for list queries; if embedding/vector search is added, create a vector index sized to the chosen embedding dimension and a text index for free-text search. Use documentdb-indexing and documentdb-vector-search guidance to select types/parameters. | Prompt doesn't list explicit query patterns or indexes; installed indexing/vector skills provide guidance but the exact index shapes & parameters are left to the implementer. |
| AI components | missing | no | "uses prompt engineering to categorise each line item" and "LangChain agent" | - | Builder will pick an LLM provider and embedding model (typical choice: OpenAI embeddings via TEXT-EMBEDDING-3 or similar, and an OpenAI-compatible chat/completion model via LangChain). API keys will be read from environment variables (e.g., OPENAI_API_KEY). The code should be written so models are injectable/configurable. | No specific chat or embedding model, dimensions, or provider are named — this materially affects vector index dimension and sample behaviour. |
| App surface | ambiguous | no | "build a Python LangChain agent ... reads submitted expense reports ... writes the enriched report back" | - | Implement a CLI / script entrypoint (e.g., `process_reports.py` or `main.py`) that runs a session processing multiple reports; include a small demo runner that shows processing several reports in one agent session. No full web UI unless the author requests it. | Prompt does not specify CLI vs API vs UI; a CLI/demo script is the least-surprising default. |
| Provisioning and deployment | missing | no | - | documentdb-azure-deployment | Do not provision new cloud resources; use the existing cluster described in the run environment. If infra-as-code is required later, use the documentdb-azure-deployment skill to add Bicep/Terraform. | The run environment explicitly says a cluster already exists and warns not to provision another; the starter prompt doesn't request deployment code. |
| Run and test instructions | missing | no | - | - | Include README steps: set up Python venv, pip install -r requirements.txt, copy .env.example to .env and fill DOCUMENTDB_URI and model keys, run seed script, then run the main CLI to process reports. Provide example outputs and verification steps. | No commands or test contract are given in the prompt; builder will add standard instructions. |
| Definition of done | missing | no | - | - | Definition of done will be: sample runs without errors against the provided cluster, seed data inserted, reports with status 'submitted' are processed, each line item updated with category/policy_violation/violation_reason, enriched documents persisted back, and a short demo run and README show these outcomes. | No explicit acceptance criteria were provided. |
| Constraints and non-goals | missing | no | - | - | Keep resource usage low (no new cluster provisioning), do not include production-grade HA/DR or CMK by default, and do not log secrets. Costly operations (e.g., large vector indexes) avoided or explained in README. | No cost or scope constraints are stated in the prompt. |
| Repository conventions | missing | no | - | - | Follow typical sample layout: src/ or app/, tests/, seed_data/, scripts/, README.md, requirements.txt (pinned), and .env.example listing DOCUMENTDB_URI, OPENAI_API_KEY (or other model key), and any other env settings. Use 'Azure DocumentDB' in docs. Provide a simple license and contribution notes. | Prompt omits repo layout and docs conventions; these are usually added by the builder. |
