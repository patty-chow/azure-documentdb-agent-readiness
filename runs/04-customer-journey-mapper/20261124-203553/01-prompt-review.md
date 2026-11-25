# 1. Prompt review: 04-customer-journey-mapper

**Verdict: sufficient_with_assumptions**

The prompt and the provided run-environment (skill_md) give enough to start building a Node.js LlamaIndex agent that runs a DocumentDB aggregation pipeline and formats a timeline+summary. Several engineering details are left to the builder (driver version, concrete collection/field names, LLM provider/model, app surface, seed data, README/IaC, and index parameter details) and will be filled by sensible defaults or the installed DocumentDB skills.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 6: Goal and scenario, Workflow type, Language and runtime, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Covered by a skill | 0: - |
| Ambiguous: builder will guess | 3: Data model, Queries and indexes, Constraints and non-goals |
| Missing: builder will guess | 7: Driver and version, Sample data, AI components, App surface, Run and test instructions, Definition of done, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- The model credentials come from environment variables — model credentials are not specified in the prompt or skill_md (skill_md only specifies DOCUMENTDB_URI). Reason: no guidance on which provider/env variables to use for LLM; implementer will choose defaults.
- .env.example lists every setting with placeholder values. Reason: not specified in prompt; builder must add it (at risk if omitted).
- The vector index dimensions match the embedding model's output. Reason: embedding model/dimensions unspecified, so index dims can't be guaranteed.
- Vector index parameters chosen for the sample's data size and README explaining how to change them. Reason: index parameter tuning not specified; documentdb-vector-search skill can advise, but implementer must choose and document parameters.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data. Reason: sample data and idempotent seed behavior are not specified in prompt or skills.
- /search returns a clear error for an empty query and when the embedding call fails. Reason: the prompt requests a journey endpoint, not a search endpoint; error-handling behaviors for search endpoints are not specified.
- Search results include the similarity score. Reason: not applicable to journey summary feature and not specified; at risk if the gallery expects a /search endpoint with scores.
- Dependencies are pinned in requirements.txt. Reason: Node.js sample would use package-lock.json; the reference asks for pinned dependencies but the prompt doesn't require a requirements file; implementer may not produce a requirements.txt.
- Unit tests run without a live cluster. Reason: no testing strategy provided; builder must add mocks or use in-memory stubs — this is not specified.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. Reason: run environment forbids provisioning another cluster by default; prompt doesn't request IaC; implementer may omit IaC.
- README covers what the sample shows, prerequisites, setup, run, and clean-up. Reason: not in the prompt (common gallery requirement, but the starter didn't mention README contents explicitly).
- The sample uses the name 'Azure DocumentDB' throughout, and no former or neighbouring product name. Reason: prompt does not specify naming conventions; skill_md mentions 'Azure DocumentDB' but repository authoring may omit or use alternative names.

## Questions for the prompt author

- Which LLM provider and exact model(s) should the sample use for (a) embeddings and (b) the generative summary? (e.g., OpenAI + model names, or a local Llama model). This will determine embedding dims and env variables.
- What are the exact collection name and field names for touchpoint documents (customer id field name, timestamp field name, channel field name)?
- Preferred app surface: should the sample expose an HTTP API endpoint (recommended), a CLI, or only a script that prints output?
- How large should the sample dataset be, and do you require a seed script to be idempotent (yes/no)?

## Contradictions and missing references

- Prompt says 'Using the DocumentDB skill' but there is no single installed skill named exactly 'documentdb' — instead multiple documentdb-* skills are available (documentdb-driver, documentdb-indexing, etc.).
- Starter prompt requests a 'LlamaIndex agent' but no dedicated LlamaIndex skill is installed; the builder will need to implement LlamaIndex usage from general Node.js/llm libraries rather than invoking a preinstalled 'LlamaIndex' skill.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "...reconstructs a customer's journey by sorting and grouping touchpoint event documents by timestamp and channel... generate a plain-language journey summary with key inflection points highlighted." | - | - | Business problem and demo outcome are clear. |
| Workflow type | specified | no | "build a Node.js LlamaIndex agent with a DocumentDB aggregation tool" — single agent (LlamaIndex) owns the flow. | - | - | - |
| Language and runtime | specified | no | skill_md: "Node.js 24 with npm and npx is available." | - | - | Node.js is specified in starter prompt; skill_md gives exact runtime (Node.js 24). |
| Driver and version | missing | no | - | documentdb-driver | Use the official 'mongodb' Node.js driver, pinned to a recent stable major (e.g., mongodb ^5.0.x) compatible with Node 24 and MongoDB 7.0 wire protocol; follow the documentdb-driver guidance to instantiate a process-wide MongoClient singleton. | documentdb-driver covers best practices (singleton client) but does not pick an exact NPM package version. The builder will pick a driver release and pin it. |
| Target service and tier | specified | no | skill_md: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) is reachable... connection string in DOCUMENTDB_URI." | - | - | The run environment defines the live cluster to use; do not provision a new cluster. |
| Authentication and secrets | specified | no | skill_md: "Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time. Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder..." | - | - | DocumentDB connection secret location is specified; LLM/model credentials are not specified (see AI components). |
| Data model | ambiguous | no | "...touchpoint event documents... sorting and grouping ... by timestamp and channel." | documentdb-data-modeling | Builder will create a 'touchpoints' (or 'events') collection in database 'sample_customer_360_04' with documents shaped like { _id, customerId, timestamp (ISODate), channel, eventType, metadata }. Use 'customerId' to match the customer, 'timestamp' for sorting, and 'channel' for grouping. | Prompt specifies the logical fields (timestamp, channel) and operation, but concrete collection name and full schema are not specified. documentdb-data-modeling gives guidance but not the exact schema. |
| Sample data | missing | no | - | documentdb-local-deployment | Include an idempotent seed script (e.g., scripts/seed.js) that inserts a modest synthetic dataset (e.g., 500–2,000 touchpoint events for several customers) and creates required indexes. The seed script should be safe to run twice (use upsert or check for existing data by a seed marker). | No sample-data source/size specified. documentdb-local-deployment discusses local sample-data knobs but does not supply the specific seed used by this sample. |
| Queries and indexes | ambiguous | no | "aggregation tool that reconstructs a customer's journey by sorting and grouping touchpoint event documents by timestamp and channel." | documentdb-indexing | Implement an aggregation pipeline: $match by customerId, $sort by timestamp, and $group by channel (or $group into an array of events per channel while preserving order). Create a compound index { customerId: 1, timestamp: 1 } to support the match+sort; consider including channel in a covering index if queries filter by channel. Index creation parameters will be conservative (single-field/compound) suitable for a small sample dataset; README will explain how to change for larger data. | Prompt specifies the pipeline shape, but index types/parameters are not specified; documentdb-indexing provides guidance to choose indexes. |
| AI components | missing | no | "LlamaIndex agent" and formatting timeline in the prompt to the model. | - | Use environment variables for LLM provider and credentials (e.g., OPENAI_API_KEY, MODEL_NAME). Default to a commonly used embedding+LLM combo accessible via LlamaIndex (e.g., OpenAI embeddings 'text-embedding-3-small' with 1536 dims and an OpenAI chat model name set by MODEL_NAME). Document choices in README and allow overrides via env. | The prompt requires using LlamaIndex but does not name the LLM provider, model names, or embedding dims; these must be chosen by the implementer and made configurable via env. |
| App surface | missing | no | "agent ... that reconstructs a customer's journey" — but no CLI/API/UI specified. | - | Provide a minimal HTTP API (Express) with a POST /journey or GET /journey?customerId=<id> endpoint that accepts a customer identifier, calls the aggregation tool, and returns the structured timeline and plain-language summary. Also include a small CLI script (npm run journey -- --customer <id>) for demos. | Reference requirements expect the agent to take a customer identifier as input (this will be implemented as an API/CLI). |
| Provisioning and deployment | specified | no | skill_md: "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable... Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use." | documentdb-azure-deployment | Do not create new cloud resources in the sample run; use provided cluster. If IaC is included, it should be marked optional and not executed by default. | The run environment restricts provisioning; an Azure deployment skill exists but should not be used by default. |
| Run and test instructions | missing | no | - | documentdb-local-deployment | README will list commands: npm install; cp .env.example .env and fill values; npm run seed (idempotent); npm start; curl to API to demo. Unit tests run with npm test and use mocking to avoid needing a live cluster. | No explicit run/test commands in the prompt; builder will add conventional instructions. |
| Definition of done | missing | no | - | - | Accept when: the agent accepts a customer identifier, the aggregation tool reconstructs and returns a chronological structured timeline, the LLM prompt is constructed from that timeline and returns a plain-language summary that highlights inflection points, README and .env.example provided, and seed script + sample data present. Unit tests and basic demonstrations run locally. | No explicit acceptance criteria in the prompt; these are sensible defaults. |
| Constraints and non-goals | ambiguous | no | "Using the DocumentDB skill" and skill_md' policy: do not provision another cluster unless allowed." | documentdb-security | Constrain the sample to non-production-safe defaults: use TLS via connection string, keep secrets out of repo, don't attempt production HA or CMK; explicitly note costs and that the sample is for demo only. | The run environment imposes a constraint about not provisioning resources, but cost/production/QA constraints are not fully specified. |
| Repository conventions | missing | no | - | - | Follow common conventions: src/, scripts/, tests/, README.md, .env.example, package.json with pinned dependencies in package-lock.json, and a scripts/seed.js. Use 'Azure DocumentDB' name throughout the README. | Starter prompt doesn't specify repo layout or README contents; builder will follow gallery conventions. |
