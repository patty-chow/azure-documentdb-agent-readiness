# 1. Prompt review: 19-option-chain-data-store

**Verdict: sufficient_with_assumptions**

The starter prompt gives a clear, implementable goal (Python ingestion service, unordered bulk writes, compound index, endpoints to return full chains) and the provided skill.md supplies important runtime constraints (DB URI env var, database name, live cluster). Several lower-level decisions (web framework, driver version, batch-size, exact collection/schema, sorting behavior) are not specified and will be chosen by the implementer; these are not blocking but will be assumed by the builder.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Language and runtime, Target service and tier, Queries and indexes, Provisioning and deployment |
| Covered by a skill | 1: Authentication and secrets |
| Ambiguous: builder will guess | 7: Workflow type, Driver and version, Data model, App surface, Run and test instructions, Constraints and non-goals, Repository conventions |
| Missing: builder will guess | 2: Sample data, Definition of done |
| Not applicable | 1: AI components |

## Reference requirements at risk

- Use pymongo bulk operations (InsertOne/ReplaceOne/UpdateOne) in the bulk_write call so snapshot option documents are written in one bulk operation with ordered=False — prompt implies unordered bulk writes but does not explicitly name pymongo or those APIs; no installed skill mandates the exact driver/API.
- When a snapshot contains more option documents than a single bulk operation should hold, split the snapshot into multiple bulk_write batches — the prompt doesn't mention batching behavior or batch size; implementer must decide.
- The endpoint’s query must use both underlying and expiry as equality filters and return the full chain sorted by strike ascending — prompt requires returning the full chain but does not explicitly require sorting order; reference requires ascending strike order.
- A `.env.example` lists every setting with placeholder values — the skill.md recommends an .env.example but does not enumerate every setting required.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — prompt asks to bulk-write data and create index but does not require an idempotent seed script.
- Dependencies are pinned in `requirements.txt` — prompt doesn't say to pin versions; implementer must decide.
- Unit tests run without a live cluster — prompt and skills do not require or provide mocks/test harness; tests may be omitted or depend on a live cluster unless the implementer adds mocking.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type — prompt assumes an existing cluster and does not ask for infra-as-code.

## Questions for the prompt author

- Which Python web framework do you prefer (FastAPI, Flask, aiohttp)? This will change route signatures and example run commands.
- Do you require a specific driver and minimum version (pymongo version) to be used and pinned in requirements.txt?
- What collection name should be used (options, option_chains, option_snapshots) and should snapshots be stored as separate documents or expanded into per-option documents?
- Preferred batch size for splitting very large snapshots into multiple bulk_write calls?
- Should the retrieval endpoint accept expiry as ISO date string or as timestamp? Should expiry match exact equality on a Date field or string?
- Do you want a seed dataset included in the repo, and if so, what format/size/source should it be?

## Contradictions and missing references

- "Using the DocumentDB skill" is ambiguous: there is no single installed skill named exactly "DocumentDB skill". Multiple documentdb-* skills are installed (documentdb-driver, documentdb-connection, documentdb-indexing, etc.) and the implementer will choose which to consult.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python ingestion service that receives options chain snapshots and bulk-writes them to DocumentDB using ordered=False bulk writes ... Create compound indexes on (underlying, expiry, strike) ... Expose endpoints that return the full chain for a given underlying and expiry date." | - | - | The business need (ingest option chains and serve full chains) is stated directly. |
| Workflow type | ambiguous | no | "Using the DocumentDB skill, build a Python ingestion service ..." | - | Single-agent, no special agent framework; this is a standalone sample application a developer runs locally or on a simple host. | Prompt references 'DocumentDB skill' generically but does not request an agent or orchestration framework. |
| Language and runtime | specified | no | "build a Python ingestion service" | - | - | Python is specified. Version is not; the run-environment block (skill.md) indicates a developer machine with python and pip available. |
| Driver and version | ambiguous | no | "bulk-writes them to DocumentDB using ordered=False bulk writes" (implies pymongo-style bulk_write) | documentdb-driver | Use the Python pymongo driver (pymongo>=4.0,<5.0), and use pymongo's bulk_write with InsertOne/UpdateOne/ReplaceOne objects. The builder will pick a recent pymongo 4.x release and pin it in requirements.txt. | The prompt implies pymongo-style API but does not explicitly name the driver or version. documentdb-driver gives client best-practice guidance (singleton MongoClient) but does not pin a version. |
| Target service and tier | specified | no | - | - | Use the existing, reachable DocumentDB cluster as described in skill.md. | The provided skill.md/run-environment states a vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol) is reachable and its connection string is in DOCUMENTDB_URI; the sample must use database 'sample_fintech_19'. |
| Authentication and secrets | covered_by_skill | no | - | documentdb-mcp-setup | - | The skill.md explicitly requires reading the connection string from DOCUMENTDB_URI and warns not to write it into files. The MCP profile 'default' is connected to the cluster and available for inspection. |
| Data model | ambiguous | no | "Create compound indexes on (underlying, expiry, strike)" | documentdb-data-modeling | One collection (e.g., 'options' or 'option_chains') in database 'sample_fintech_19'; each option document contains fields: underlying (string), expiry (ISO 8601 date or date type), strike (number), optionType ('call'\|'put'), lastPrice, bid, ask, timestamp, plus any metadata. Use expiry as a Date field and strike as numeric to sort. | Prompt specifies the index keys but not collection name or full document shape; documentdb-data-modeling gives modeling guidance but not exact schema. |
| Sample data | missing | no | - | documentdb-local-deployment | Provide a small JSON or NDJSON seed file in the repo (e.g., seeds/sample_chain.json) and a seed script to load it. The sample data will be small (hundreds of documents) sufficient to demonstrate queries. | The prompt does not provide sample data, source, size, or license. The skill.md asks the builder to 'load the sample data' for verification but does not provide it. |
| Queries and indexes | specified | no | "Create compound indexes on (underlying, expiry, strike) to support efficient queries." | documentdb-indexing | Create a compound ascending index on { underlying: 1, expiry: 1, strike: 1 } using pymongo.create_index. Ensure index exists at startup before serving queries. | Prompt explicitly asks for the compound index. documentdb-indexing covers how to design compound indexes and the ESR principle. |
| AI components | not_applicable | no | - | - | - | No embeddings, LLMs, or AI models are required by the prompt. |
| App surface | ambiguous | no | "Expose endpoints that return the full chain for a given underlying and expiry date." | - | Implement HTTP API using FastAPI (or Flask) with endpoints such as POST /ingest (accepts snapshot JSON) and GET /chains?underlying=XXX&expiry=YYYY-MM-DD returning JSON list sorted by strike. Use JSON body for ingest snapshots and query parameters for retrieval. | Prompt requires endpoints but does not choose a web framework or specific routes or parameter style. |
| Provisioning and deployment | specified | no | - | - | - | skill.md explicitly states an existing cluster is reachable and that the sample should use it and not provision another cluster unless allowed. |
| Run and test instructions | ambiguous | no | - | - | README will include commands: python -m venv .venv; pip install -r requirements.txt; export DOCUMENTDB_URI='...' (or .env); uvicorn app:app --reload; a seed script: python seed.py. Tests: pytest to run unit tests that mock the DB. | Prompt and skill.md describe runtime environment but do not provide explicit CLI commands or test instructions. |
| Definition of done | missing | no | - | - | Definition of done the implementer will use: ingestion endpoint accepts snapshot and writes documents via bulk_write(ordered=False), index created at startup, retrieval endpoint returns all docs matching underlying+expiry sorted by strike, and seed script loads sample data idempotently. | No explicit acceptance criteria were given in the prompt; the implementer will infer them from the stated goals. |
| Constraints and non-goals | ambiguous | no | - | documentdb-security | Do not provision new clusters; keep credentials in env vars; keep run costs minimal (use existing cluster). No heavy production HA or CMK setup in the sample. | skill.md and security skill provide some constraints (do not log connection string, use env var) but there are no explicit cost or compliance limits in the prompt. |
| Repository conventions | ambiguous | no | "Read it from the environment at run time. Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder, as the prompt asks." (skill.md) | documentdb-local-deployment | Standard layout: app/ (source), tests/, scripts/seed.py, requirements.txt (pinned), .env.example, README.md. Reuse single MongoClient and do not commit secrets. | Prompt/skill.md note about .env.example exists but full repo conventions are not spelled out. |
