# 1. Prompt review: 17-stress-testing-multi-agent-runner

**Verdict: sufficient_with_assumptions**

The starter prompt gives a clear high-level goal (Python + LangChain multi-agent stress tester that reads position data from Azure DocumentDB, runs aggregation pipelines, stores runs, and returns a structured report). The run environment / skill.md supplies important operational constraints (existing M30 cluster, DATABASE name, DOCUMENTDB_URI env var) and several installed skills cover driver/connection and indexing best-practices, so a builder can begin. Several concrete engineering choices are unspecified (Python version, driver sync vs async, specific schema, seed-data format, model provider and dims, index shapes, CLI vs API surface, README/test details) and will be chosen by the builder by reasonable defaults unless the author clarifies them.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Workflow type, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Covered by a skill | 0: - |
| Ambiguous: builder will guess | 5: Language and runtime, Driver and version, Queries and indexes, App surface, Repository conventions |
| Missing: builder will guess | 6: Data model, Sample data, AI components, Run and test instructions, Definition of done, Constraints and non-goals |
| Not applicable | 0: - |

## Reference requirements at risk

- A .env.example lists every setting with placeholder values — skill.md suggests using .env.example but does not enumerate every setting; the builder must author and list all env keys.
- The vector index dimensions match the embedding model's output — the prompt does not name an embedding model, so matching dims are not guaranteed.
- Vector index parameters chosen for the sample's data size and README guidance for changing them — neither index parameters nor size guidance are provided; vector-index tuning is not specified.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — the prompt asks to store runs but doesn't require an idempotent seed script; builder must write it.
- "/search" returns a clear error for an empty query and when the embedding call fails — the starter prompt does not require a search endpoint at all, so this behaviour is unlikely to be implemented.
- Search results include the similarity score — not requested by the prompt; unless the builder adds search, similarity scores won't be present.
- Dependencies are pinned in requirements.txt — the prompt does not mandate pinned versions; the builder must add them explicitly.
- Unit tests run without a live cluster — tests are not specified; builder must create mocked tests to meet this requirement.
- Infrastructure for the cluster is provided as code — the run environment prohibits provisioning a new cluster and the prompt doesn't ask for IaC, so an IaC artifact is unlikely to be included.
- README covers what the sample shows, prerequisites, setup, run, and clean-up — README content is not specified and must be created by the builder to satisfy this requirement.

## Questions for the prompt author

- Which Python major version should the sample target (e.g., 3.10, 3.11)? This affects dependency pins and async choices.
- Should the implementation use synchronous PyMongo or async (AsyncMongoClient / PyMongo 4.9+)?
- Which LLM provider and models should the sample assume for the LangChain agents (chat model and embedding model)? Also confirm that credentials will be provided via environment variables.
- Do you want an interactive CLI-only sample, or also a minimal HTTP API endpoint to run stress tests?
- Should the repo include an idempotent seed dataset (synthetic) and, if so, what scale/fields should it contain (small demo vs realistic-sized)?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python LangChain multi-agent stress testing system where a scenario agent generates macroeconomic shock parameters, an impact agent runs aggregation pipelines against DocumentDB position data to compute P&L impacts, and a reporting agent synthesises the results into a structured stress test report. Store all scenario runs as DocumentDB documents for audit." | - | - | The business goal, actors (scenario/impact/reporting agents), main database usage and audit storage are all present in the prompt. |
| Workflow type | specified | no | "multi-agent" and "LangChain" are explicitly named. | - | - | LangChain multi-agent orchestration is required by the prompt. |
| Language and runtime | ambiguous | no | "Python LangChain" (language specified) but no interpreter/major-version is given. | - | Builder will target a modern Python 3.x LTS typically used for samples (assume Python 3.10 or 3.11). | Python is specified but not the exact version; that will influence dependency pins and async choices. |
| Driver and version | ambiguous | no | The prompt requires running aggregation pipelines against DocumentDB but does not name the MongoDB Python driver or version. | documentdb-connection | Builder will use the official PyMongo driver; if async is chosen, follow documentdb-connection guidance and use PyMongo 4.9+ AsyncMongoClient. If sync code is simpler, use PyMongo 4.0+ (latest stable). | documentdb-connection recommends PyMongo 4.9+ for async usage and describes connection options — that guides the choice but the prompt does not mandate sync vs async. |
| Target service and tier | specified | no | - | - | - | The provided skill.md/run-environment explicitly states there is already a reachable vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0) and the database to use (sample_banking_17). That fixes the target cluster/tier for the sample. |
| Authentication and secrets | specified | no | skill.md: "connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time. Never write its value into any file... use a config file or `.env.example` with a placeholder" | - | - | Secrets location and handling are defined by the run environment guidance. |
| Data model | missing | no | Prompt: impact agent runs aggregation pipelines against position data — but no schema is provided. | documentdb-data-modeling | Builder will create a minimal 'positions' collection and a 'stress_runs' (or 'scenario_runs') collection. A plausible 'positions' doc: { _id, account_id, instrument, quantity, market_value, risk_factors: {rate:..., fx:...}, currency, timestamp }. The 'stress_runs' document will contain { _id, scenario_params, impact_summary, per_instrument_breakdown, created_at, schemaVersion }. | documentdb-data-modeling gives modeling guidance but no concrete sample schema — the builder must invent one for the demo. |
| Sample data | missing | no | Prompt instructs running aggregations over position data but does not describe sample data source, format or size. | documentdb-local-deployment | Builder will include a small synthetic seed dataset (hundreds to low-thousands of position docs) included in the repo (JSON/CSV) and add an idempotent seed script that creates collections and inserts or upserts documents. | The run-environment says to 'load the sample data' but does not provide or name a dataset; the builder must create it. |
| Queries and indexes | ambiguous | no | Prompt: "impact agent runs aggregation pipelines" — query pattern described at a high level but no exact aggregation pipeline or index definitions. | documentdb-indexing | Builder will implement example PyMongo aggregation pipelines using $match (filter by instruments/accounts) and $group (sum P&L), and create supporting indexes such as single-field indexes on instrument, account_id, and risk_factor fields. If vector search is used for any embedding lookup, choose DiskANN/HNSW per documentdb-vector-search guidance depending on data size. | Index shapes and pipeline details are not specified; indexing/optimization guidance is available from installed skills. |
| AI components | missing | no | Prompt requires a LangChain multi-agent system (implies LLM usage) but does not name provider, chat model, or embedding model/dimensions. | documentdb-natural-language-querying | Builder will use an LLM provider configured via environment variables (e.g., OpenAI API key in OPENAI_API_KEY). For embeddings use a standard embedding model (e.g., text-embedding-3-small, 1536 dims) and for chat use a contemporary chat model (e.g., gpt-4o-mini or gpt-4-family). The repo will read LLM credentials from env and will not hard-code them. | Model choices change index dims and RAG/LLM call code; these must be picked and documented by the builder. |
| App surface | ambiguous | no | Prompt describes a multi-agent runner but does not state whether it's a CLI, API, or web UI. | - | Builder will implement a simple CLI entrypoint (e.g., run_stress_test.py or a `main()` CLI using click/argparse) that runs the orchestrator and prints/writes the structured report. Optionally include a minimal HTTP API example as an extra. | Choice affects packaging, tests and examples in README. |
| Provisioning and deployment | specified | no | skill.md: "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable... Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use." | - | - | The build should not create cloud infrastructure; use the existing cluster. There is an installed documentdb-azure-deployment skill available if provisioning were requested. |
| Run and test instructions | missing | no | Prompt asks to build the system but provides no commands or test recipe. | documentdb-local-deployment | Builder will add README steps: create virtualenv, pip install -r requirements.txt, populate .env from .env.example, run seed script, run run_stress_test.py. Tests: include pytest unit tests that mock the DB and LLM calls; CI instructions optional. | skill.md suggests verifying against the live cluster, but explicit runnable steps and test commands are not in the prompt and must be authored. |
| Definition of done | missing | no | No explicit acceptance criteria beyond 'build the system'. | - | Accept when: orchestrator runs end-to-end producing a structured report, the run is saved as a DocumentDB document, example aggregation queries execute successfully against the sample data, and README lists how to reproduce these steps. | The builder will have to pick concrete acceptance tests / smoke checks. |
| Constraints and non-goals | missing | no | Prompt does not state cost limits, privacy constraints or non-goals. | - | Builder will avoid provisioning extra Azure resources, keep dataset small for cost, and not attempt production hardening (HA, CMK, or multi-region DR) beyond basic best-practice comments. | skill.md warns not to provision a new cluster; otherwise no cost/limit guidance is given. |
| Repository conventions | ambiguous | no | skill.md: use database sample_banking_17, read DOCUMENTDB_URI from env, "use a config file or `.env.example` with a placeholder"; other repo conventions (layout, README sections, pinned deps) are not detailed. | documentdb-local-deployment, documentdb-driver | Builder will follow common sample layout: src/, tests/, scripts/seed.py, README.md, requirements.txt, .env.example. Use 'Azure DocumentDB' name in docs per reference guidance. | Some conventions (env, database name, singleton client) are guided by skill.md and installed skills, but not everything (pinning deps, README sections) is explicit. |
