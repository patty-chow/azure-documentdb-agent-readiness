# 1. Prompt review: 18-chargeback-dispute-multi-agent

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines a chargeback-dispute multi-agent Node.js sample using LangChain with an orchestrator + three agents and an end-to-end flow. The run environment (Node.js 24, a reachable DocumentDB cluster, and DATABASE name sample_fintech_18) is provided in the accompanying skill_md and multiple installed skills cover DocumentDB best practices (driver singleton, connection guidance, indexing, vector search, etc.). Several important engineering details are left unspecified (driver version, collection/document schema, AI model/provider, API surface, seed data and indexing parameters, README/tests), so a builder will fill these with reasonable defaults (Express API, mongodb npm driver latest 5.x, OpenAI models via env vars, small idempotent seed script, single MongoClient singleton).

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 2: Goal and scenario, Workflow type |
| Covered by a skill | 4: Language and runtime, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Ambiguous: builder will guess | 5: Driver and version, Data model, Queries and indexes, App surface, Constraints and non-goals |
| Missing: builder will guess | 5: Sample data, AI components, Run and test instructions, Definition of done, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- A `.env.example` lists every setting with placeholder values — not specified in starter prompt or skill_md; builder must add it.
- The vector index dimensions match the embedding model's output — embedding model not specified, so index dims are at risk of mismatching.
- Vector index parameters chosen for the sample's data size and README explains how to change them — index parameters not provided in prompt; builder will invent defaults, so this is at risk.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — prompt does not request a seed script; this is likely to be omitted unless builder adds it.
- /search returns a clear error for an empty query and when the embedding call fails — no search endpoint is specified and error handling for embedding failures is not in the prompt.
- Search results include the similarity score — semantic-search behavior is not requested; similarity scoring is at risk of being omitted.
- Dependencies are pinned in `requirements.txt` — Node projects don't use requirements.txt; the equivalent (pinned package.json versions and lockfile) is not specified and may be inconsistent with the reference expectation.
- Unit tests run without a live cluster — tests and mocks are not described; builder may not include offline-capable unit tests.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type — skill_md forbids provisioning in this environment and the starter prompt doesn't request IaC; this requirement is at risk.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up — README is not requested explicitly in the starter prompt and may be incomplete if the builder omits it.

## Questions for the prompt author

- Which AI provider and exact models should be used for embeddings and policy reasoning (this affects vector dimensions, env vars, and index choices)?
- Do you want an HTTP API (recommended) or a CLI/other interface for submitting claims and showing results?
- Should the sample include an idempotent seed script with sample transactions/communications and exact collection names (if yes, please confirm preferred collection names like 'transactions' and 'communications')?

## Contradictions and missing references

- The prompt says 'Using the DocumentDB skill' but there is no single installed skill named exactly 'DocumentDB' — instead several DocumentDB-related skills are installed (documentdb-driver, documentdb-connection, etc.). The builder will need to decide which of the installed skills to consult.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | build a Node.js LangChain multi-agent system where an orchestrator receives a chargeback claim, delegates to an evidence-gathering agent ... policy-reasoning agent ... decision agent that writes the accept/reject outcome back to DocumentDB. | - | - | Business problem and what the sample demonstrates are clearly stated. |
| Workflow type | specified | no | Node.js LangChain multi-agent system ... orchestrator, evidence-gathering agent, policy-reasoning agent, decision agent | - | - | Multi-agent orchestration with LangChain is explicitly requested. |
| Language and runtime | covered_by_skill | no | Using the DocumentDB skill, build a Node.js LangChain ... | skill_md run environment | Use Node.js 24 (the run environment states Node.js 24 is available). | Prompt states Node.js; skill_md provides concrete runtime (Node.js 24). |
| Driver and version | ambiguous | no | - | documentdb-driver | Use the official mongodb Node.js driver (npm package 'mongodb') at a current 5.x release that supports MongoDB 7.0; follow documentdb-driver guidance to instantiate a singleton MongoClient. | Starter prompt doesn't name the driver or version. documentdb-driver covers usage patterns (singleton) but not an exact package version. |
| Target service and tier | covered_by_skill | no | Using the DocumentDB skill ... write ... back to DocumentDB. | skill_md run environment | Use the provided live, vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol) reachable via DOCUMENTDB_URI as described in skill_md. | skill_md explicitly describes the available cluster and forbids creating a different one for the sample. |
| Authentication and secrets | covered_by_skill | no | - | skill_md run environment | Connection string is read from env var DOCUMENTDB_URI at runtime; other secrets / model keys placed in env vars and not checked into repo. | skill_md instructs to read DOCUMENTDB_URI from the environment and to avoid writing secrets into files or README. |
| Data model | ambiguous | no | evidence-gathering agent that fetches transaction and communication documents from DocumentDB | documentdb-data-modeling | Create a dedicated database named 'sample_fintech_18' (skill_md). Collections assumed: 'transactions', 'communications' (and likely 'claims' or 'decisions'). Documents include claimId/transactionId, timestamps, amounts, message text, and any metadata. Use schemaVersion field and avoid >16MB docs. | Prompt requires fetching transactions & communications but does not specify collection names, field names, or exact document shapes; documentdb-data-modeling can guide choices but doesn't supply concrete schema. |
| Sample data | missing | no | - | - | Builder will create a small idempotent seed script that upserts a handful of transactions, communications and a sample claim (e.g., using claimId) into 'sample_fintech_18'. The seed script will check for existing docs or upsert to allow re-run without duplication. | Starter prompt doesn't include sample data or how to load it; reference requirements expect a seed script but it's not specified here. |
| Queries and indexes | ambiguous | no | fetches transaction and communication documents ... associated with the provided claim identifier | documentdb-indexing | Implement simple queries that filter by claimId or transactionId. Create single-field indexes on claimId/transactionId. No vector or full-text index is strictly required unless the policy or evidence agent needs semantic search; if embeddings are used, create a vector index sized to the chosen embedding dims. | Specific index shapes and parameters are not specified; documentdb-indexing can guide decisions but the builder must choose index keys and parameters. |
| AI components | missing | no | LangChain multi-agent system ... policy-reasoning agent | documentdb-vector-search | Builder will use LangChain Node.js with an LLM provider via env vars (e.g., OPENAI_API_KEY). For embeddings, assume OpenAI text-embedding-3-small and for reasoning use an LLM like gpt-4o-mini or a similar hosted model. Embedding dimension assumed to match the chosen model (e.g., 1536 dims for text-embedding-3-small). | No embedding model or chat model/provider is named in the prompt; that materially affects index dimensions and call sites. |
| App surface | ambiguous | no | orchestrator receives a chargeback claim | - | Implement a minimal HTTP API (Express) with POST /claims/submit or POST /claims/:id/decide which accepts a claim payload or claimId and triggers the orchestrator. Include simple JSON responses and a /health endpoint. | Prompt doesn't specify CLI vs API vs UI; an API is the most likely and practical choice for demonstration. |
| Provisioning and deployment | covered_by_skill | no | - | skill_md run environment | Do not provision a cluster. Use the existing DocumentDB cluster described in the run environment. If infrastructure-as-code is required, use documentdb-azure-deployment skill, but the run instructions currently forbid creating another cluster. | skill_md explicitly states the cluster is already provisioned and should be used for verification. |
| Run and test instructions | missing | no | - | - | Provide README with commands: npm install, cp .env.example .env (fill vars), npm run seed, npm start; tests via npm test (Jest) with unit tests using mocks so they run without a live cluster. | Prompt doesn't include step-by-step run/test instructions; builder must add them. |
| Definition of done | missing | no | - | - | Define done as: (1) orchestrator accepts a claim and invokes agents in order; (2) evidence agent retrieves docs from DocumentDB; (3) policy agent outputs a recommendation; (4) decision agent writes an accept/reject document back to sample_fintech_18 and the flow is demonstrated in the README and a recorded run. | No acceptance criteria in prompt; builder will need to define them to complete the sample. |
| Constraints and non-goals | ambiguous | no | Using the DocumentDB skill ... | skill_md run environment | Avoid provisioning new clusters or writing secrets to repo. Keep example data small to limit costs. Do not attempt production-grade HA, RBAC or CMK configuration beyond recommended best practices. | Prompt and skill_md impose some constraints (use existing cluster), but cost limits and non-goals are not fully enumerated. |
| Repository conventions | missing | no | - | - | Use standard Node layout: package.json, src/, tests/, README.md, .env.example (placeholders only). Use 'Azure DocumentDB' name consistently. Pin dependency versions in package.json (lockfile via package-lock.json). | No explicit repo layout rules are provided; builder will apply common Node.js conventions. |
