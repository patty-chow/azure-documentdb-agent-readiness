# 1. Prompt review: 19-proactive-outreach-orchestration

**Verdict: sufficient_with_assumptions**

The starter prompt defines a clear multi-agent Node.js LangChain orchestration (trigger → copy → send) targeting an existing Azure DocumentDB cluster; the provided run-context (skill_md) fills important environment details (Node 24, DATABASE name, DOCUMENTDB_URI). Several practical details are left to the builder (driver version, exact schema/collections, LLM/provider choices, send-channel integrations, seed scripts, CI-friendly tests, .env.example, index dimensions and params), so the build can start but will require explicit assumptions or guidance for these gaps.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Workflow type, Language and runtime, Target service and tier, Provisioning and deployment |
| Covered by a skill | 0: - |
| Ambiguous: builder will guess | 6: Driver and version, Authentication and secrets, Data model, Queries and indexes, App surface, Constraints and non-goals |
| Missing: builder will guess | 5: Sample data, AI components, Run and test instructions, Definition of done, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- A `.env.example` lists every setting with placeholder values — not specified in prompt/skills; builder must add it.
- The vector index dimensions match the embedding model's output — embedding model not chosen, so dims not specified.
- The vector index parameters are chosen for the sample's data size, and README says how to change them — no index parameter guidance in prompt.
- One database client is created and reused across requests — documentdb-driver suggests pattern but not enforced; at risk if builder doesn't follow it.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — sample data/seed script not specified.
- /search returns a clear error for an empty query and when the embedding call fails — search endpoint behavior not part of the starter prompt.
- Search results include the similarity score — not specified anywhere for the outreach sample.
- Dependencies are pinned in `requirements.txt` — prompt is Node.js so equivalent lockfile (package-lock.json) expected but not specified; pinning/locking is at risk.
- Unit tests run without a live cluster — no test strategy for mocking the cluster is specified.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type — prompt/run instructions say a cluster already exists and do not request IaC; this requirement is at risk.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up — prompt/skills mention verification but don't supply a README template; builder must produce it.
- The sample uses the name 'Azure DocumentDB' throughout, and no former or neighbouring product name — prompt says 'DocumentDB skill' but not explicit wording rules for README; at risk unless enforced.

## Questions for the prompt author

- Should the send agent integrate with real providers (SMTP, Twilio, push) or should it use mocked/simulated sending for the gallery sample? This changes required env vars and testing strategy.
- Which LLM provider and embedding model should the sample use by default (e.g., OpenAI, Anthropic, local LLM)? Provide the env var names and a default model name so the sample can be wired to working credentials.
- Do you want the sample to include infrastructure-as-code (Bicep/Terraform) for the DocumentDB cluster, or must it strictly avoid any cluster provisioning because a cluster is already provided in the run environment?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | Using the DocumentDB skill, build a Node.js LangChain orchestration pipeline where a trigger agent monitors DocumentDB change streams for qualifying customer events (cart abandon, contract renewal, birthday), passes the event to a copy agent that generates personalised outreach using context engineering, then to a send agent that dispatches via the customer's preferred channel. Log outcomes to DocumentDB. | - | - | Business problem, user and demonstrated DB behaviour are clearly stated in the prompt. |
| Workflow type | specified | no | Node.js LangChain orchestration pipeline ... trigger agent ... copy agent ... send agent | - | - | Multi-agent orchestration using LangChain is explicit. |
| Language and runtime | specified | no | Node.js LangChain orchestration pipeline | documentdb-local-deployment | Use Node.js 24 (skill_md run environment states Node.js 24 is available). | The provided run environment in skill_md states Node.js 24 with npm/npx is available; that resolves the version choice. |
| Driver and version | ambiguous | no | - | documentdb-driver | Use the official MongoDB Node.js driver (mongodb npm package) latest stable compatible with Node.js 24 (e.g., mongodb 5.x/6.x depending on release at build time). Instantiate a singleton MongoClient and reuse it across modules. | The driver choice/version isn't specified. documentdb-driver gives patterns but not a pinned version; builder will pick a recent mongodb driver and apply the singleton pattern. |
| Target service and tier | specified | no | skill_md: A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) is reachable; use database named sample_customer_360_19. | - | - | Run context explicitly provides the existing cluster and database name; do not provision another cluster. |
| Authentication and secrets | ambiguous | no | skill_md: Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time. Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder, as the prompt asks. | documentdb-security | Use env vars for all secrets: DOCUMENTDB_URI for the DB; add OPENAI_API_KEY (or PROVIDER_API_KEY) and MODEL_NAME for LLM credentials; other provider creds (SMTP/SMS) in env vars. Do not commit secrets to repo; provide a `.env.example`. | DB connection string is specified via env var in skill_md, but LLM and channel provider credentials are not mentioned and must be assumed. |
| Data model | ambiguous | no | skill_md: Use the database named `sample_customer_360_19` for everything this sample creates. | documentdb-data-modeling | Create clear collections: `customers` (customerId, name, contact methods, preferred_channel, profile fields), `events` (eventId, customerId, type, timestamp, payload), and `outreach_logs` (logId, eventId, customerId, channel, message, status, timestamp). No sharding (single-shard) for the sample cluster; documents kept small and denormalized for read performance. | Database name is given, but collection names and document shapes are not; use conventional small set of collections and single-shard design for the sample. |
| Sample data | missing | no | - | - | Provide a small idempotent seed script that inserts ~10–50 customers and a handful of event documents (cart abandon, contract renewal, birthday). Seed script should be runnable multiple times without creating duplicates (use upsert or check by unique keys). | The prompt/skill_md ask to verify against live cluster but do not include sample-data source, size, licence, or how to load it. |
| Queries and indexes | ambiguous | no | Prompt expects change streams (watch()) and logging to DocumentDB; skill_md notes vector-capable cluster and indexes available. | documentdb-indexing | Create indexes on `events.customerId`, `events.type`, an index for `outreach_logs.eventId` and a vector index for embeddings on a `customers` or `outreach_embeddings` collection with dims matching chosen embedding model. Provide comments/readme describing how to tune index parameters for larger datasets. | Exact index shapes and vector index parameters (dims, algorithm config) are not stated; documentdb-indexing and vector skills will guide choices but builder must pick concrete values. |
| AI components | missing | no | Prompt: copy agent generates personalised outreach using LangChain LLM calls; skill_md does not mention model/provider. | - | Expose LLM provider and model via env vars (e.g., OPENAI_API_KEY, MODEL_NAME). Default to an accessible LLM (e.g., OpenAI-compatible endpoint) and an embedding model whose dimensions are documented (e.g., text-embedding-3-small with 1536 dims) and call the LLM via LangChain from Node.js. The copy agent will call an LLM to synthesize the message; embedding calls only as needed for personalization/search. | No provider, model name, or embedding model is specified; these must be chosen and exposed via env vars. |
| App surface | ambiguous | no | Prompt: build a Node.js LangChain orchestration pipeline where a trigger agent monitors DocumentDB change streams ... | - | Implement as a small Node.js service with a CLI to run the listener and a minimal REST API to view status and recent outreach logs (e.g., GET /logs). The primary runtime is a long-running process that opens change streams and processes events in real time. | The prompt doesn't specify whether to expose web endpoints, CLI, or UI; the builder will pick a minimal service + CLI for demonstration. |
| Provisioning and deployment | specified | no | skill_md: 'This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable.' 'Do not provision another cluster unless run policy allows.' | documentdb-azure-deployment | Do not create or modify cloud infrastructure for this sample; use the provided cluster. If infra-as-code is desired later, the documentdb-azure-deployment skill can be used to produce Bicep/Terraform. | Cluster is pre-provisioned in the run environment; the sample should not create a new cluster. |
| Run and test instructions | missing | no | skill_md: 'Verify against the live cluster: create the collections and indexes, load the sample data, run the queries the sample exists to show, and record ...' | - | Provide README with commands: npm install, npm run seed, npm start (or npm run dev), and npm test. Tests should include unit tests that can run with mocks and an integration test that can be run manually against the live cluster. | No concrete commands or test contracts are provided in the starter prompt. |
| Definition of done | missing | no | - | - | Definition of done: listener process starts and keeps running; it detects sample qualifying events, the orchestrator calls the copy agent and send agent in order, DB logs are written to `outreach_logs`, and sample seed data is used to demonstrate at least one end-to-end flow. | No explicit acceptance criteria in the prompt. |
| Constraints and non-goals | ambiguous | no | skill_md: 'Never write DOCUMENTDB_URI into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder.' 'Do not provision another cluster unless allowed.' | documentdb-security | Constrain sample to avoid committing secrets, avoid provisioning infra, and avoid sending real marketing messages in uncontrolled ways — use a mock or a clearly documented sandbox option for send agent by default. | Some run constraints are present in skill_md, but non-goals like 'do not send real messages' were not explicit in the starter prompt and should be clarified. |
| Repository conventions | missing | no | - | - | Follow common repo conventions: top-level README with sections (what it shows, prerequisites, setup, run, cleanup), `.env.example` with placeholders, package.json with pinned deps via lockfile, src/, tests/, scripts/ (seed, start, test), and sample uses the phrase 'Azure DocumentDB' throughout. | Prompt and run context do not define repository layout or required artifacts like `.env.example` or README content. |
