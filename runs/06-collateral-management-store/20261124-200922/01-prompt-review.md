# 1. Prompt review: 06-collateral-management-store

**Verdict: sufficient_with_assumptions**

The starter prompt clearly states the main goal (Node.js/Mongoose service that stores versioned collateral and valuations, LLM classification, and an aggregation endpoint for coverage ratio) and the run-environment skill_md supplies important runtime details (Node 24, existing cluster, DB name). Several implementation details (driver version, exact schema, LLM provider/model, indexes, seeding, tests, README, and infra-as-code) are not specified and will be filled by the builder's defaults or by consulting installed skills.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Language and runtime, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Covered by a skill | 0: - |
| Ambiguous: builder will guess | 3: Data model, Queries and indexes, App surface |
| Missing: builder will guess | 8: Workflow type, Driver and version, Sample data, AI components, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- A `.env.example` lists every setting with placeholder values — no `.env.example` is requested in the starter prompt; the run-environment mentions env usage but does not require an example file.
- The vector index dimensions match the embedding model's output — the prompt references an LLM classification step but does not state whether embeddings or a vector index are used, nor the embedding model/dimensions.
- Vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one — indexing params are not specified; skill guidance exists but the prompt doesn't require documenting tuning guidance.
- One database client is created and reused across requests — the prompt doesn't mention connection management explicitly. (The documentdb-driver skill covers this practice but the starter prompt does not mandate it.)
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — starter prompt asks to build service but doesn't request an idempotent seed; the reference expects such a script.
- /search returns a clear error for an empty query and when the embedding call fails — the prompt does not mention a search endpoint or its error handling requirements; the reference expects robust search error handling.
- Search results include the similarity score — not mentioned; if the builder adds a semantic-search feature it may or may not include scores.
- Dependencies are pinned in `requirements.txt` — (Python-oriented requirement). For Node.js the equivalent would be pinned deps/package-lock; the starter prompt doesn't require or mention pinned dependencies.
- Unit tests run without a live cluster — tests are not specified; the reference expects offline-capable unit tests (mocks/in-memory DB).
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type — starter prompt assumes a pre-provisioned cluster; it does not ask for IaC; a reviewer may expect IaC artefacts.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up — the prompt doesn't require a README; the reference expects a complete README.
- The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name — the prompt says "DocumentDB" but doesn't explicitly require naming policy; ensure README and comments use "Azure DocumentDB" consistently.

## Questions for the prompt author

- How should the total collateral coverage ratio be computed exactly? (e.g., sum(latest collateral valuations) / sum(liabilities) — what fields represent liabilities, and are there filters by eligibility tier or asset type?)
- Which LLM provider and model should be used for classification, and should the code include a default provider/model? (e.g., OpenAI with model X; or make provider configurable via env variables?)
- Should valuations be stored in a single collection together with assets (versioned documents sharing assetId), or in two collections (assets and valuations) linked by assetId? Which naming convention for collections does the reviewer prefer?
- Do you want infrastructure-as-code (Bicep/Terraform) for the cluster included in the repo, or should the sample rely only on the pre-provisioned cluster described in skill_md?
- Are unit tests required to run without a live cluster (i.e., using mocks or an in-memory MongoDB), and if so, prefer mongodb-memory-server or jest+sinon mocks?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Node.js Mongoose collateral management service that stores each collateral asset and valuation update as a versioned document ... Add an LLM classification step ... expose an aggregation endpoint that computes total collateral coverage ratio." | - | - | Clear business goal and demo scenario. |
| Workflow type | missing | no | - | - | Implement as a normal single-process Node.js sample (no agent orchestration). The builder agent will run locally to generate files; the sample app itself is a no-agent REST service. | Prompt doesn't say whether to demonstrate agent orchestration or to rely on an agent framework; the natural assumption for a sample app is no-agent. |
| Language and runtime | specified | no | skill_md: "Node.js 24 with npm and npx is available." | - | - | Node.js runtime version is provided in the run-environment context. |
| Driver and version | missing | no | "Mongoose" is named but no version is given. | - | Use a current Mongoose 7.x release compatible with Node 24 (e.g., "mongoose@7"), and pin it in package.json / package-lock.json. | The prompt requests Mongoose but does not specify a version or exact driver details. |
| Target service and tier | specified | no | skill_md: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol ...) is reachable ... connection string in env var DOCUMENTDB_URI" | - | - | Run environment gives the cluster tier and protocol to use; builder should use the provided live cluster. |
| Authentication and secrets | specified | no | skill_md: "Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time. Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder, as the prompt asks." | - | LLM/API credentials are expected to be provided from environment variables (e.g., OPENAI_API_KEY or LLM_PROVIDER_*), and keys must not be committed. | Database secret handling is specified by the run-environment context; LLM/model credentials are not named in the starter prompt and must be placed in env variables (builder's default). |
| Data model | ambiguous | no | "stores each collateral asset and valuation update as a versioned document in DocumentDB (using a version field and createdAt timestamp)." | - | Create one collection (e.g. `collateral_assets`) in database `sample_banking_06` (from skill_md). Each document includes: assetId (logical id), version (integer), createdAt (ISO timestamp), valuation {amount, currency}, asset metadata, llmTags {assetType, eligibilityTier}, and optionally an embedding vector. Updates insert a new document with same assetId and higher version. | Prompt requires versioning and timestamps but leaves collection naming, field names, and whether valuations are embedded or separate documents to the builder. |
| Sample data | missing | no | - | - | Include a small idempotent seed script that inserts ~5 sample assets with 1–3 valuation versions each and creates required indexes. The seed script should be safe to run multiple times (upsert or dedupe by a stable key). | Starter prompt doesn't mention sample data source, size, or seed automation; reference requirements expect a seed script. |
| Queries and indexes | ambiguous | no | "expose an aggregation endpoint that computes total collateral coverage ratio" and requirement to use most recent version per asset. | - | Implement a Mongoose aggregation that groups by assetId and picks the document with max version or max createdAt; create indexes on { assetId: 1, version: -1 } (or compound on assetId+createdAt) and on createdAt. If embeddings are used, a vector index will be created separately but vector dims and params will be chosen conservatively for the sample. | Index shapes/prescriptions are not specified; the documentdb-indexing skill can be consulted for optimizations. |
| AI components | missing | no | "Add an LLM classification step that tags each asset by type and eligibility tier." | - | Call an LLM via a provider configured in env vars (e.g., OPENAI_API_KEY). Default to a lightweight classification model (e.g., an OpenAI classification-capable model such as `gpt-4o-mini` or `gpt-4o-mini-classification`) and store returned tags in the document under llmTags. The model name and provider should be configurable in .env. | Prompt requires an LLM classification step but does not name provider, model, or exact API; this choice materially affects code and env requirements. |
| App surface | ambiguous | no | "build a Node.js Mongoose collateral management service ... expose an aggregation endpoint that computes total collateral coverage ratio." | - | Provide a simple REST API (Express or similar) with at minimum: POST /assets (create or update—inserts a new versioned doc), GET /coverage (returns the computed coverage ratio and input totals), and GET /assets/:assetId/history (returns version history). POST /assets triggers the LLM classification step. | Prompt specifies the aggregation endpoint but leaves the overall route design and inputs/outputs to the implementer. |
| Provisioning and deployment | specified | no | skill_md: "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable." | - | Do not provision another cluster; use the provided live cluster. Optionally include IaC as a separate artifact using the documentdb-azure-deployment skill if requested later. | Starter prompt and run environment explicitly say the cluster already exists; provisioning is not required for the sample run. |
| Run and test instructions | missing | no | - | - | Provide README and run scripts: npm install; copy .env.example to .env and populate DOCUMENTDB_URI and LLM creds; npm run seed; npm start. Include basic unit tests using mocking for the DB and LLM so tests can run offline (e.g., jest with mongodb-memory-server or sinon stubs). | No explicit run/test commands or offline-test approach are given in the starter prompt. |
| Definition of done | missing | no | - | - | Accept when: REST endpoints implemented, aggregation endpoint returns correct coverage computed from the latest valuations, new updates append docs with incremented version and earlier docs preserved, LLM tags stored on documents, and basic seed + run steps successfully execute against the provided cluster. | No precise acceptance criteria were supplied; the above are plausible criteria derived from the prompt. |
| Constraints and non-goals | missing | no | - | - | Keep the sample small and low-cost (no new cluster creation), avoid production HA or CMK configurations, and do not include PII in sample data. | Prompt is silent about cost or compliance constraints. |
| Repository conventions | missing | no | skill_md: "Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder, as the prompt asks." | - | Use a conventional layout: src/, tests/, scripts/seed.js, .env.example, README.md, package.json with pinned deps (package-lock.json). Use the phrase "Azure DocumentDB" consistently in docs. | Only a single convention (env handling) is mentioned; most repository conventions are left to the implementer. |
