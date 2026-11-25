# 1. Prompt review: 13-algorithmic-trade-journal

**Verdict: sufficient_with_assumptions**

The prompt gives a clear high-level goal (Python service to store immutable trade-journal documents, compute win-rate/avg P&L/drawdown, and format results for LLM review). Key operational details (DB connection env var and the live cluster DB name) are provided in the run environment. Several implementation details will be chosen by the builder (HTTP vs function surface, Python/driver versions, exact index choices, seeding + tests, LLM model/provider). Those defaults are not blocking but will be assumed by the builder.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 4: Goal and scenario, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Covered by a skill | 2: Driver and version, Data model |
| Ambiguous: builder will guess | 4: Workflow type, Language and runtime, Queries and indexes, App surface |
| Missing: builder will guess | 6: Sample data, AI components, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- Include a numeric 'pnl' field on outcome documents — prompt did not explicitly require the 'pnl' field; skills don't enforce it (risk: the builder may omit or make it optional).
- Document-level 'version' integer and versioning behavior (write new document with same strategy_id and incremented version) — prompt mentions immutability but not the specific versioning scheme; skill guidance (schemaVersion) exists but the exact requirement may be missed.
- Index on (strategy_id, timestamp) or time-series-optimized collection — prompt didn't require index creation explicitly; builder may not create the compound index unless assumed.
- Aggregation pipeline for max drawdown that uses cumulative P&L ordered by timestamp and windowing ($setWindowFields) — prompt asks for drawdown but not the exact pipeline shape; automatic use of window stages may be omitted.
- Packaging aggregation pipelines as reusable functions that accept strategy_id and optional time range and return structured numeric results — prompt asks for pipelines but doesn't mandate this exact callable API, so the builder might implement them differently.
- Context-engineering layer that deterministically formats the aggregation output into an LLM-ready summary including top 3 trades — prompt requests formatting but doesn't mandate deterministic layout or top-3 trade selection; builder choices may diverge.
- Python data-seeding script that inserts representative data for at least two strategies with known expected metric values — the starter prompt does not request a seeding script; without explicit ask the builder might not include it.
- Automated tests asserting win rate, average P&L, and max drawdown against seeded data and asserting the formatted summary — prompt does not require tests; likely to be omitted unless the builder assumes them.
- .env.example listing all environment settings with placeholders — run environment forbids writing the real connection string, but the prompt didn't explicitly require a .env.example; gallery convention may be missed.
- Pinned dependencies in requirements.txt — prompt doesn't require pinning; builder may leave unpinned versions.
- Unit tests designed to run without a live cluster (mocks/fakes) — prompt/run environment expects live cluster usage; tests may require a live cluster and thus violate the gallery requirement that unit tests run offline.
- Infrastructure as code for the cluster (Bicep/ARM/Terraform) — run environment provides a cluster and the prompt forbids provisioning another, so infra IaC may be omitted.
- README that documents what the sample shows, prerequisites, setup, run, and clean-up — prompt doesn't request a full README; builder might provide only minimal usage notes.

## Questions for the prompt author

- Do you want an HTTP API (e.g., FastAPI) or a library with callable functions for inserts and aggregation endpoints?
- Which Python version should be targeted (3.11, 3.10)? Which pymongo / driver version should be pinned?
- Should the context-engineering layer make live LLM/embedding calls (and if so, which provider/model and which env vars for credentials) or remain a deterministic formatter only?
- Should the sample include a seed script and automated tests (unit/integration) that assert exact numeric values? If so, provide the expected metric numbers for the seeded dataset or allow the builder to choose a deterministic seeded dataset and expected values.
- May the sample create indexes on the live cluster (e.g., compound index on {strategy_id:1, timestamp:1}) and other collection-level changes, or must it only read/write documents?

## Contradictions and missing references

- The prompt starts "Using the DocumentDB skill..." but there is no installed skill named exactly "DocumentDB skill" — instead the environment provides multiple documentdb-* skills (documentdb-driver, documentdb-indexing, etc.).
- Prompt asks only to 'use DocumentDB' but skill_md makes a stronger statement: a live vector-capable cluster is already provisioned and must be used; the prompt does not explicitly state not to provision a new cluster.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "stores each trading signal, execution, and outcome as a separate immutable document ... with a strategy ID and timestamp" and "build aggregation pipelines that compute win rate, average P&L, and drawdown per strategy" | - | - | Business problem and what the sample demonstrates are clearly stated. |
| Workflow type | ambiguous | no | - | - | Implement as a single-agent, no-agent sample: a standalone Python service (no external agent framework). | Prompt doesn't say whether this is an agent-driven sample or a plain app; builder will assume plain Python service. |
| Language and runtime | ambiguous | no | "build a Python service" | documentdb-local-deployment | Target modern CPython 3.11 (or 3.10) in a virtualenv; 'python' in skill.md maps to that environment. | Python is specified but no precise version; skill.md says 'python' and pip resolve to a virtualenv for the run. |
| Driver and version | covered_by_skill | no | - | documentdb-driver | Use the Python MongoDB driver (pymongo) and pin a recent 4.x release (e.g., pymongo>=4.4,<5) in requirements.txt. Use a singleton MongoClient per documentdb-driver guidance. | The documentdb-driver skill supplies the usage pattern (singleton MongoClient) but does not force an exact package version; the builder will pick and pin a pymongo 4.x version. |
| Target service and tier | specified | no | skill_md: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol...) is reachable ... read connection string from DOCUMENTDB_URI" and "Use the database named `sample_fintech_13`" | - | - | Run environment gives the live cluster details and the database name to use. |
| Authentication and secrets | specified | no | skill_md: "Its connection string is in the environment variable `DOCUMENTDB_URI`. Read it from the environment at run time. Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder, as the prompt asks." | - | - | Secrets are expected from env vars; the exact env var name is given in the run environment. |
| Data model | covered_by_skill | no | "stores each trading signal, execution, and outcome as a separate immutable document ... with a strategy ID and timestamp" | documentdb-data-modeling | Builder will create a single 'journal' collection in database `sample_fintech_13` with documents including _id, strategy_id (string), timestamp (ISO 8601 UTC stored as ISODate), type ("signal"\|"execution"\|"outcome"), outcome documents include numeric pnl, and include an integer version/schemaVersion field for schema/versioning. | The prompt names the three event types and the minimal key fields; documentdb-data-modeling covers schema/versioning guidance and limits. |
| Sample data | missing | no | - | - | Builder will add a Python seed script that populates representative signals/executions/outcomes for at least two strategy_id values across a time range and is idempotent for re-runs. | Prompt does not request a seed script; the reference requires one, so the builder will add it by assumption. |
| Queries and indexes | ambiguous | no | "Build aggregation pipelines that compute win rate, average P&L, and drawdown per strategy." | documentdb-natural-language-querying, documentdb-indexing | Builder will implement aggregation pipelines as arrays of MongoDB stages in code and (to optimize time-series queries) create a compound index on {strategy_id:1, timestamp:1}. Index parameters (e.g., unique/partial) will be simple defaults; vector/indexing details not required for these aggregations. | Prompt asks for pipelines but does not name indexes or shapes; index guidance is available from documentdb-indexing. |
| AI components | missing | no | "Add a context engineering layer that formats the aggregated stats for LLM-driven strategy review." | documentdb-vector-search | Implement the context-engineering layer as a deterministic text formatter in Python only (no live LLM calls) unless an LLM provider/model is specified; do not add embeddings or model calls by default. | Prompt requests LLM-ready formatting but doesn't specify an LLM provider, chat/embedding model, or dimensions. documentdb-vector-search covers vector index best-practices but does not select a specific model. |
| App surface | ambiguous | no | "expose functions or HTTP endpoints that insert..." | - | Implement a small FastAPI-based HTTP service with endpoints like POST /journal/signal, /journal/execution, /journal/outcome for inserts and GET /stats/{strategy_id} (with optional start/end query params) to run pipelines and return structured JSON and formatted summary. | Prompt allows either functions or endpoints; the builder will choose HTTP endpoints for a runnable sample. |
| Provisioning and deployment | specified | no | skill_md: "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable... Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use." | - | - | No infra provisioning required; run environment forbids creating another cluster for the sample. |
| Run and test instructions | missing | no | - | - | Builder will add a README and simple commands: create .env from .env.example, pip install -r requirements.txt, python -m seed_data to load sample data, run the FastAPI app (uvicorn app:app --reload), and pytest to run tests. | Prompt doesn't specify explicit run/test commands or expected outputs; builder will add standard instructions. |
| Definition of done | missing | no | - | - | Definition of done: service inserts immutable documents, aggregation functions return correct numeric metrics (win rate, avg P&L, total P&L, trade count, max_drawdown) on seeded data, context layer formats a deterministic LLM-ready summary, and unit/integration tests pass. | Prompt lacks explicit acceptance criteria; the builder will adopt the reference's expected checks. |
| Constraints and non-goals | missing | no | - | documentdb-storage | No hard cost or region constraints beyond using the provided cluster; avoid costly HA or provisioning changes. Do not add production-only features like CMK unless requested. | Prompt doesn't call out cost/scale constraints or security non-goals. |
| Repository conventions | missing | no | - | documentdb-driver | Repository will include .env.example, requirements.txt (pinned), README, src/ or app/ layout, tests/ and scripts/seed_data.py; create a single MongoClient singleton per documentdb-driver guidance. | Prompt doesn't mandate layout or files; builder will use common sample conventions. |
