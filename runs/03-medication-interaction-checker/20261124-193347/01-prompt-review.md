# 1. Prompt review: 03-medication-interaction-checker

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines the core goal (Node.js LangChain single-agent using Mongoose to query a DocumentDB drug-interaction KB, have an LLM assess severity, and return a ranked list). The provided run-environment notes supply the concrete cluster and Node.js version. Many implementation details are unspecified (Mongoose version, exact schema, model/provider choice, API surface, indexing parameters, seed data and README conventions). These will be chosen by the builder unless the author clarifies them.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 2: Goal and scenario, Workflow type |
| Covered by a skill | 4: Language and runtime, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Ambiguous: builder will guess | 4: Driver and version, Data model, Queries and indexes, App surface |
| Missing: builder will guess | 6: Sample data, AI components, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- Provide Mongoose-based functions to add and update interaction documents — The prompt implies maintenance but does not explicitly require create/update functions; no installed skill supplies concrete CRUD scaffolding for Mongoose, so this may be omitted or implemented only partially.
- In the prompt/template, require the LLM to return a sortable severity assessment — The prompt asks the LLM to assess severity but does not require a structured numeric score or ordered label; the builder must decide to force a numeric/ordered output for ranking.
- Deduplicate results so each medication pair appears only once in final output — The prompt doesn't explicitly require deduplication, so the builder might return duplicate entries if multiple DB documents match both orders.
- The connection string and model credentials come from environment variables; none appear in the repository — Run environment documents DOCUMENTDB_URI but the prompt does not mention model credential env vars or .env.example; likely to be missed unless the builder adds it.
- .env.example lists every setting with placeholder values — Not mentioned in prompt; at risk of omission.
- The vector index dimensions match the embedding model's output — Prompt is silent about embeddings/dimensions and index creation; at risk unless builder chooses embeddings and matches dims.
- Vector index parameters chosen for the sample's data size, README guidance on changing them — Not specified; at risk.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — Prompt doesn't mention idempotent seed script; likely to be omitted or non-idempotent unless builder explicitly implements upserts.
- /search returns a clear error for an empty query and when the embedding call fails — The prompt does not mandate a /search route nor explicit error handling for embedding failures.
- Search results include the similarity score — Not described in prompt; at risk if retrieval/embedding path is used.
- Dependencies are pinned in requirements.txt — For Node, pinned dependencies should be in package.json/package-lock.json; the prompt doesn't mention pinning or lockfile, so pinned dependency practice may be missing.
- Unit tests run without a live cluster — The prompt does not ask for mocking tests; likely unit tests that require a live cluster will be omitted, or no tests provided.
- Infrastructure for the cluster is provided as code using the Azure DocumentDB resource type — The prompt does not require infra-as-code; the run environment forbids provisioning during the run, so infra-as-code may be omitted.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up — The prompt doesn't explicitly ask for README content; this is often omitted or incomplete.
- The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name — Prompt says DocumentDB but does not mandate naming consistency; builder might accidentally use 'Cosmos DB' or 'MongoDB' in docs.

## Questions for the prompt author

- Which LLM provider and model should the sample use for clinical severity assessment (e.g., OpenAI gpt-4o, Anthropic Claude, or a placeholder)? This changes environment variable names and prompt/token limits.
- Should the sample include embeddings/vector search (and therefore a vector index) for retrieval, or is a direct document lookup by normalized pair sufficient?
- What exact Mongoose schema fields and conventions do you expect (field names like drugA/drugB vs. a normalizedPair array; include evidence, severityScore numeric, lastUpdated)?
- What app surface do you want demonstrated: HTTP JSON API (recommended), CLI only, or a small web UI?
- Do you require infrastructure-as-code (Bicep/Terraform) to be included in the repo, or must the sample avoid any provisioning and only operate against the provided cluster?

## Contradictions and missing references

- Prompt says "Using the DocumentDB skill" but there is no single installed skill named exactly "DocumentDB skill"; instead multiple documentdb-* skills are available (documentdb-driver, documentdb-indexing, etc.). This is not fatal, but the builder must pick which skills to consult.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | build a Node.js LangChain agent using Mongoose that maintains a drug interaction knowledge base in DocumentDB ... Given a list of medications, the agent queries all pairwise interaction documents ... returns a ranked list of interactions with clinical recommendations. | - | - | - |
| Workflow type | specified | no | "Node.js LangChain agent" (single-agent) | - | - | Prompt explicitly asks for a LangChain agent; reference requirements also expect a single-agent implementation. |
| Language and runtime | covered_by_skill | no | Node.js | run environment (skill_md) | Use Node.js 24 (as documented in the run environment). | The starter prompt names Node.js; the provided run-environment notes specify Node.js 24 is available. |
| Driver and version | ambiguous | no | Mongoose | documentdb-driver | Use Mongoose latest 7.x compatible with Node 24 (e.g., ^7.0.0). Implement a singleton Mongoose connection per process and reuse it for requests. | Prompt specifies Mongoose but not a version. documentdb-driver covers connection best-practices but not a concrete Mongoose version. |
| Target service and tier | covered_by_skill | no | DocumentDB | run environment (skill_md) | Use the pre-provisioned, vector-capable Azure DocumentDB cluster described in the run environment (compute tier M30, MongoDB 7.0 wire protocol). Do not provision a new cluster. | Run environment explicitly describes the live cluster to use. |
| Authentication and secrets | covered_by_skill | no | - | run environment (skill_md) | Read the cluster connection string from the environment variable DOCUMENTDB_URI at runtime. Model API keys will also come from environment variables (builder will create OPENAI_API_KEY or provider-equivalent). | The run environment instructs to read DOCUMENTDB_URI from env and not to write it anywhere. |
| Data model | ambiguous | no | maintains a drug interaction knowledge base in DocumentDB; queries all pairwise interaction documents | documentdb-data-modeling | Implement an Interaction Mongoose schema with fields: drugA (string), drugB (string), normalizedPair (string: sorted/drugA\|drugB), severityScore (optional number), clinicalRecommendation (string), evidence (array of strings/refs), updatedAt. Normalize pairs by sorting drug names so queries can search a single field. | Prompt requires pairwise queries but does not prescribe field names or normalization strategy; documentdb-data-modeling can guide decisions but doesn't supply exact schema. |
| Sample data | missing | no | - | documentdb-local-deployment | Provide a small, idempotent seed script that loads ~10-20 example interaction documents (common drug pairs) into sample_healthcare_03. The seed script will upsert by normalizedPair to avoid duplicates on re-run. | Starter prompt does not describe sample dataset, size, or license. |
| Queries and indexes | ambiguous | no | queries all pairwise interaction documents | documentdb-indexing | Create a compound or single-field index on normalizedPair and additional indexes on drugA and drugB. If embedding/vector search is added, builders will create a vector index matching embedding dims. Default: no vector index unless embeddings are used. | Prompt requires pairwise queries but doesn't specify index shapes or whether to use text/vector indexes. documentdb-indexing can advise index selection. |
| AI components | missing | no | uses prompt engineering to instruct the LLM to assess severity | - | Use a provider-compatible chat model via LangChain (e.g., OpenAI chat model) and put API key in OPENAI_API_KEY (or PROVIDER_API_KEY). Use a prompt template that requests a numeric severity score (0-10) plus a short clinical recommendation. If embeddings are needed for retrieval, use an embedding model with 1536 dims (text-embedding-3-small) and set vector index dims accordingly. | Prompt says to call an LLM but doesn't pick model, provider, or env var names. |
| App surface | ambiguous | no | Given a list of medications, the agent ... returns a ranked list of interactions | - | Implement an HTTP JSON API (Express) with POST /check-interactions that accepts {medications: ["drug1","drug2",...] } and returns JSON array of ranked interactions. Provide a small CLI script that calls the same logic for ad-hoc runs. | Starter prompt doesn't say whether to build a CLI, API, or UI. Builder will likely choose an API for demonstration. |
| Provisioning and deployment | covered_by_skill | no | - | run environment (skill_md) | Don't provision new cloud resources in the build; use the pre-provisioned cluster. If infra-as-code is desired, the documentdb-azure-deployment skill can supply Bicep/Terraform examples, but the run is expected to target the existing cluster. | Run environment explicitly instructs not to create another cluster for this sample run. |
| Run and test instructions | missing | no | - | - | Provide README commands: npm install, copy .env.example to .env, set DOCUMENTDB_URI and model API key, npm run seed, npm start. Include a test script (npm test) that runs unit tests with mocks; integration verification documented separately. | The prompt and run notes do not list explicit run/test commands or expected outputs. |
| Definition of done | missing | no | - | - | Accept when: sample runs locally against provided cluster, seed script creates upserted data, POST /check-interactions returns deduplicated, ranked JSON with severity and recommendation for each unique pair, and build report documents what was executed. | No explicit acceptance criteria are in the starter prompt. |
| Constraints and non-goals | missing | no | - | documentdb-security | Add README note: sample is for demo/dev only (not for clinical decision making), keep costs low by using existing cluster, and do not include PHI. Recommend security best-practices but do not implement enterprise controls in the sample. | No cost or compliance constraints are specified; documentdb-security can provide guidance if needed. |
| Repository conventions | missing | no | - | - | Use a standard Node layout: src/, test/, scripts/seed.js, package.json, .env.example, README.md. Use the product name "Azure DocumentDB" throughout the README and code comments. | Starter prompt does not give repo layout or README expectations. |
