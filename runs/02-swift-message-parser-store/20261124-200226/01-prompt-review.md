# 1. Prompt review: 02-swift-message-parser-store

**Verdict: sufficient_with_assumptions**

The prompt clearly states the main goal (async Python + Beanie ingestion of MT103/MT202, validation, bulk writes, and an aggregation endpoint). It leaves many implementation details (API surface, driver versions, collection layout, indexing, seed data, tests, README, infra-as-code) unspecified; installed DocumentDB skills and the provided run-environment notes cover some gaps (connection string, target DB, client best-practices). The build can start but will depend on reasonable defaults for language/runtime, API choice, collection design, indexes, and test/packaging conventions.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 3: Goal and scenario, Target service and tier, Authentication and secrets |
| Covered by a skill | 0: - |
| Ambiguous: builder will guess | 7: Workflow type, Language and runtime, Driver and version, Data model, Queries and indexes, App surface, Provisioning and deployment |
| Missing: builder will guess | 5: Sample data, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 1: AI components |

## Reference requirements at risk

- .env.example lists every setting with placeholder values — prompt does not ask for .env.example; skill_md mentions DOCUMENTDB_URI but not that .env.example must be produced.
- The vector index dimensions match the embedding model's output — not applicable to prompt's feature set; the run environment mentions vector-capable cluster but the sample doesn't use vector indexes.
- The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one — no vector search usage requested, so this is at risk.
- One database client is created and reused across requests — prompt does not explicitly require singleton client; documentdb-driver skill covers the pattern but the prompt leaves it implicit.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — prompt doesn't mention seed script or idempotency; likely to be omitted unless the implementer adds it.
- /search returns a clear error for an empty query and when the embedding call fails — sample doesn't include search or embedding; this requirement is at risk.
- Search results include the similarity score — not relevant unless adding vector search; at risk.
- Dependencies are pinned in requirements.txt — prompt doesn't require pinned deps; implementer must choose to pin them.
- Unit tests run without a live cluster — prompt doesn't ask for tests or mocks; test strategy is at risk.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type — prompt and skill_md indicate an existing cluster; IaC is not requested and may be omitted.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up — prompt doesn't require README; likely to be added by implementer but at risk if omitted.
- The sample uses the name 'Azure DocumentDB' throughout, and no former or neighbouring product name — prompt says 'DocumentDB' but implementer must ensure naming; at risk if they use other names (Cosmos DB, etc.).

## Questions for the prompt author

- Do you want an HTTP API (e.g., FastAPI) as the ingestion/aggregation surface, or should the sample expose plain async functions (library) instead?
- Should MT103 and MT202 be stored in one polymorphic collection named 'swift_messages' with a 'message_type' field, or in separate collections (e.g., 'mt103', 'mt202')?
- Which Python minor version should be targeted (3.10 or 3.11) and do you want specific package version pins for Beanie/Motor/pymongo provided?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build an async Python SWIFT message ingestion service ... that parses MT103 and MT202 ... validates required fields, and bulk-writes batches ... Include an aggregation endpoint that summarises daily message volume and total value by message type." | - | - | Business problem, input (MT103/MT202), actions (parse, validate, bulk write), and aggregation outcome are explicitly stated. |
| Workflow type | ambiguous | no | "build an async Python ... service" (no agent framework specified) | - | Build a standalone, single-process async application (no multi-agent orchestration). The builder will implement a normal app (e.g., FastAPI) rather than an agent pipeline. | Prompt references 'DocumentDB skill' (instruction to the coding agent) but does not request a multi-agent workflow. |
| Language and runtime | ambiguous | no | "async Python" and "Beanie ODM" | documentdb-local-deployment | Use a current CPython 3.11 (or 3.10) runtime for the sample and author requirements for that version in README and requirements.txt. | No explicit Python version was requested; the run-environment notes say 'python' resolves to a virtualenv but not which major/minor. |
| Driver and version | ambiguous | no | "Beanie ODM" | documentdb-driver | Use Beanie (1.x) with Motor (async PyMongo driver) 3.x and pymongo 4.x — i.e., recent compatible versions. Use singleton Motor client pattern per documentdb-driver guidance. | Prompt names Beanie but does not state exact package versions; the driver skill covers patterns but not explicit version pins. |
| Target service and tier | specified | no | - | - | Use the live cluster described in skill_md. | The provided skill_md run-environment supplies the cluster details (vector-capable cluster, compute tier M30, MongoDB 7.0 wire protocol) and the database name sample_banking_02; builder must use that cluster and DB. |
| Authentication and secrets | specified | no | - | - | - | skill_md requires reading the cluster connection string at runtime from env var DOCUMENTDB_URI and forbids persisting it in code or logs. |
| Data model | ambiguous | no | "Beanie ODM that parses MT103 and MT202 message fields into structured DocumentDB documents ... each parsed SWIFT field held as its own typed document field" | documentdb-data-modeling | Implement two Beanie Document models or a single polymorphic model in one collection named 'swift_messages' with a required 'message_type' field; include typed fields like sender, receiver, amount, currency, value_date. Use a single collection unless the builder chooses separate collections for MT103 and MT202. | Prompt requires mapping fields but doesn't specify collection names, whether separate collections per message type, or shard key. The data-modeling skill can guide choices but doesn't force them. |
| Sample data | missing | no | - | documentdb-local-deployment | Add an idempotent seed script that inserts a small set (dozens) of example MT103 and MT202 raw texts and their parsed documents; include the seed script in repo and mark it safe to run repeatedly (check for existing message IDs). | Prompt does not provide sample messages or how to load them; local-deployment skill helps but does not supply domain-specific sample data. |
| Queries and indexes | ambiguous | no | "Include an aggregation endpoint that summarises daily message volume and total value by message type." | documentdb-indexing | Create indexes on fields used in aggregation and lookups: e.g., compound index on (message_type, value_date) and an index on amount/value fields. The builder will implement the aggregation using a MongoDB $group/ $sum pipeline executed via Beanie/driver. | Prompt requires the aggregation pipeline but doesn't specify indexes or index types; documentdb-indexing skill can recommend index shapes. |
| AI components | not_applicable | no | - | - | - | No embeddings or models are requested; vector-capable cluster exists but the sample doesn't require AI. |
| App surface | ambiguous | no | "an async ingestion entry point that accepts incoming SWIFT MT messages ... (e.g. an HTTP endpoint or an async function)" and "Include an aggregation endpoint" | - | Implement an HTTP API using FastAPI with at least two endpoints: POST /ingest that accepts a batch of raw MT messages (JSON array of strings) and GET /aggregations/daily-summary that returns daily counts and total value per message_type. Use JSON I/O and 202/200 style responses. | Prompt leaves protocol and route names to the implementer; FastAPI is the common default for async Python web samples. |
| Provisioning and deployment | ambiguous | no | "Using the DocumentDB skill" and skill_md note that a cluster is already provisioned and reachable; "Do not provision another cluster unless the run policy says Azure writes are allowed" | documentdb-azure-deployment | Do not provision cloud resources during the sample run; rely on the existing cluster. Optionally include a placeholder Bicep/Terraform file or instructions but do not execute provisioning by default. | The infra-deployment skill is available if the builder chooses to include IaC, but the run-environment instructs not to create resources. |
| Run and test instructions | missing | no | - | documentdb-local-deployment | Add a README and commands: pip install -r requirements.txt, copy .env.example to .env with DOCUMENTDB_URI, run python seed.py, run uvicorn app:app --reload, curl sample requests; include expected outputs for successful ingest and aggregation. | Prompt doesn't ask for explicit run or test steps; the run-environment suggests verifying against live cluster but leaves doc creation to builder. |
| Definition of done | missing | no | - | - | Definition of done: code parses MT103/MT202 fields to Beanie documents, validates required fields (skips or rejects invalid messages), bulk-inserts batches into sample_banking_02 collection(s), and GET aggregation returns daily counts and summed transaction values by message type. Tests or demo scripts exercise these behaviors. | No acceptance criteria were provided in prompt. |
| Constraints and non-goals | missing | no | - | documentdb-security | Do not provision new cloud resources; do not log secrets; avoid production HA/DR configuration; keep sample small and low-cost. Security best-practices (TLS/env vars) applied. | Prompt does not list cost or compliance constraints; follow the run-environment guidance and security skill recommendations. |
| Repository conventions | missing | no | - | - | Use a standard layout: src/, app/, tests/, README.md, requirements.txt (pinned), .env.example, seed.py, and a LICENSE. Name the project and references using the phrase 'Azure DocumentDB'. | Prompt doesn't prescribe repo layout or naming; reference requirements expect these items for gallery samples. |
