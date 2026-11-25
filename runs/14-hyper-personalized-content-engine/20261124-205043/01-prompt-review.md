# 1. Prompt review: 14-hyper-personalized-content-engine

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines the high-level goal (a Node.js LlamaIndex single-agent that fetches customer docs, does a vector search, and emits a personalised rationale + ranked list) and the run-environment adds key runtime details. Several implementation details (driver version, exact index parameters, embedding/chat model choice, API surface, seed data, README and tests, infra-as-code) are left unspecified and will be filled by installed skills or the builder's defaults.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Workflow type, Language and runtime, Target service and tier, Authentication and secrets |
| Covered by a skill | 1: Queries and indexes |
| Ambiguous: builder will guess | 5: Driver and version, Data model, AI components, Run and test instructions, Repository conventions |
| Missing: builder will guess | 5: Sample data, App surface, Provisioning and deployment, Definition of done, Constraints and non-goals |
| Not applicable | 0: - |

## Reference requirements at risk

- Model credentials come from environment variables: run environment specifies DOCUMENTDB_URI but does not mention embedding/chat model credentials; prompt doesn't require model creds in env — at risk.
- .env.example lists every setting with placeholder values: prompt/run env imply at least DOCUMENTDB_URI exists, but not a complete .env.example listing embeddings/chat provider settings — at risk.
- The vector index dimensions match the embedding model's output: prompt does not specify the embedding model; although vector-search skill advises this, the build could pick a default model and mismatch — at risk.
- The vector index parameters are chosen for the sample's data size, and the README explains how to change them: prompt omits index parameters and README content — at risk.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data: prompt doesn't require a seed script; builder must add it explicitly — at risk.
- /search returns a clear error for an empty query and when the embedding call fails: prompt doesn't specify API surface or error behavior — at risk.
- Search results include the similarity score: prompt asks for ranked results but doesn't explicitly require returning numeric similarity scores — at risk.
- Dependencies are pinned in requirements.txt: reference expects requirements.txt but sample is Node.js (package.json + package-lock.json) — naming/format mismatch and pinning requirement may be unmet — at risk.
- Unit tests run without a live cluster: prompt/run env instructs verification against the live cluster but doesn't require test mocks; so test design may not meet this requirement — at risk.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type: prompt/run env say a cluster is already present and do not ask to provision; infra-as-code may be omitted — at risk.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up: prompt doesn't demand an exhaustive README; builder must author it — at risk.
- The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name: prompt uses 'DocumentDB' but builder could accidentally use other names (Cosmos DB etc.) in docs — at risk.

## Questions for the prompt author

- Which embedding and chat models should be used as defaults (or should they be fully configurable via env vars)? The embedding model choice determines index dimensions and must be known to create the vector index correctly.
- Should the sample include an HTTP API (e.g., /search) and example route names, or is a CLI script acceptable? The reference expects a /search endpoint but the prompt is silent.
- Do you want the sample to include infrastructure-as-code (Bicep/Terraform) for provisioning the DocumentDB cluster, or should it assume the provided, pre-provisioned cluster (as the run environment suggests)?
- Are unit tests required to run without a live cluster (i.e., must DB and embedding calls be mocked)? This affects test design and added dependencies.

## Contradictions and missing references

- "Using the DocumentDB skill" is ambiguous — there is no single installed skill named exactly 'DocumentDB'. Several documentdb-* skills are installed (e.g., documentdb-vector-search, documentdb-driver).
- Reference requirements expect a requirements.txt with pinned dependencies; this is Python-centric while the prompt explicitly requests a Node.js sample (Node will use package.json + package-lock.json).

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | “build a Node.js LlamaIndex agent ... that fetches the customer's profile, segment, and recent interaction documents from DocumentDB, retrieves semantically relevant content pieces via vector search, and ... generate a personalised content selection rationale and ranked list for the customer.” | - | - | The business goal, user-facing output, and what the sample demonstrates are explicitly stated. |
| Workflow type | specified | no | “Node.js LlamaIndex agent with agent memory” — single-agent flow | - | - | Single LlamaIndex agent with memory is requested. |
| Language and runtime | specified | no | Run environment: Node.js 24 is available (see skill_md run environment). | - | - | Prompt itself says Node.js; the provided run environment explicitly states Node.js 24. |
| Driver and version | ambiguous | no | - | documentdb-driver | Builder will use the official mongodb Node.js driver (npm package 'mongodb'), follow the documentdb-driver guidance (singleton MongoClient) and pick a current stable major compatible with Node 24 (pin a concrete version in package.json/package-lock). | The prompt doesn't name a driver or version. documentdb-driver supplies best-practice patterns but not a concrete version string. |
| Target service and tier | specified | no | skill_md: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) is reachable ..." and "Use the database named sample_customer_360_14" | - | - | The run environment supplies the exact cluster tier and database to use; the prompt assumes that cluster. |
| Authentication and secrets | specified | no | skill_md: "Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time." | - | - | DOCUMENTDB_URI env var is explicitly required in the run environment. Model credentials are not specified here. |
| Data model | ambiguous | no | Prompt: fetch the customer's profile, segment and recent interaction documents and content pieces with embeddings. | documentdb-data-modeling | Builder will create collections named (for example) profiles, segments, interactions, content_pieces. Customer documents will be looked up by a customer identifier (e.g., customerId). Content pieces will include fields like _id, title, body, embedding (number[]), embedding_model and maybe metadata. No sharding is assumed for the sample; schemaVersion field may be present. | The prompt names the logical document types but does not define field names, collection names, or shard keys; documentdb-data-modeling gives patterns but not exact schema. |
| Sample data | missing | no | - | - | Builder will include a small, synthetic sample dataset in the repository and provide a seed script (idempotent upserts) to load it into sample_customer_360_14. The sample will be small (tens or low hundreds of documents) to keep costs low. | Prompt doesn't state where sample data comes from or its shape/size. |
| Queries and indexes | covered_by_skill | no | Prompt: "retrieves semantically relevant content pieces via vector search" (no index details given). | documentdb-vector-search, documentdb-indexing | Builder will create a cosmosSearch vector index on the embedding field (choose vector-diskann / vector-hnsw / vector-ivf appropriate to data size) with 'dimensions' matching the embedding model and set similarity (COS, L2, or IP) per chosen embedding normalization. | The installed vector-search and indexing skills provide exact commands and guidance for creating the cosmosSearch vector index and composing $search queries. |
| AI components | ambiguous | no | Prompt: LlamaIndex agent with agent memory; fetches docs and retrieves content via vector search before generation. | documentdb-vector-search | Builder will make embedding and chat model provider configurable via environment variables (e.g., EMBEDDING_PROVIDER, EMBEDDING_MODEL, CHAT_PROVIDER, CHAT_MODEL). Reasonable defaults will be selected (e.g., an OpenAI embedding model and a compatible chat model) and README will explain how to change them. Index dimensions will be set to the chosen embedding model's output dim at seed time. | The prompt requires LlamaIndex, but does not specify embedding or chat models or how embeddings are sourced — this materially affects index dimensions. |
| App surface | missing | no | - | - | Builder will expose a minimal HTTP API (e.g., Express) with a /search endpoint that accepts a customerId (and optional query) and returns the personalised rationale and ranked list; memory will be stored in-process for the sample. CLI examples (seed, start) will also be provided. | Prompt doesn't require whether this is CLI, API, or UI; repository requirements expect an API route but the prompt is silent. |
| Provisioning and deployment | missing | no | skill_md: cluster is already provisioned and reachable; do not create another cluster unless allowed. | documentdb-azure-deployment | Because the run environment already provides a cluster, builder will not include infra provisioning for the cluster; README will declare the pre-provisioned requirement. If infra is added it will use the documentdb-azure-deployment skill's Bicep or Terraform templates, but it's optional for this sample. | The prompt and run environment imply no provisioning is needed; an infra-as-code requirement in the gallery's reference is not satisfied by the prompt. |
| Run and test instructions | ambiguous | no | skill_md: indicates pip/node/npm are present and that verification should be run against the live cluster, but doesn't list concrete commands. | - | Builder will include a README with step-by-step commands: create .env from .env.example, npm install, npm run seed, npm start, and npm test. Unit tests will mock the DB so they can run without a live cluster. | Explicit commands and test details are not in the prompt; run-environment hints exist but not a full run/test plan. |
| Definition of done | missing | no | - | - | Builder will use a practical acceptance checklist: sample DB populated, vector index created, /search returns personalised rationale + ranked content with similarity scores, unit tests pass, and README instructions succeed locally against the provided cluster. | No explicit acceptance criteria are given in the prompt. |
| Constraints and non-goals | missing | no | - | - | Builder will avoid provisioning new paid resources, keep sample dataset small to limit costs, and mark production hardening (security, HA) as out-of-scope while referencing relevant skills (documentdb-security, documentdb-high-availability). | No cost or scope constraints are listed in the prompt. |
| Repository conventions | ambiguous | no | skill_md instructs not to store connection strings in repo and to use a .env.example placeholder; documentdb-local-deployment covers env-driven configuration. | documentdb-local-deployment, documentdb-driver | Builder will include a .env.example (with placeholders), package.json and package-lock.json to pin dependencies, src/ for app code, scripts/ for seed and teardown, tests/ for unit tests, and a README with required sections. | Some conventions (no secrets in repo, .env.example) are implied by the run environment and local-deployment skill; other conventions (exact layout, lockfile usage) are not fully specified. |
