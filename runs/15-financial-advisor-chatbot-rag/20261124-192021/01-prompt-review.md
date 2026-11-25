# 1. Prompt review: 15-financial-advisor-chatbot-rag

**Verdict: sufficient_with_assumptions**

The starter prompt defines a clear goal: a Node.js LlamaIndex RAG agent that retrieves DocumentDB vectorized financial knowledge and combines it with live portfolio data via a tool, and it requires agent memory for follow-ups. The run context (live, vector-capable Azure DocumentDB cluster; Node.js 24 available; connection string in DOCUMENTDB_URI) fills in several infra details via the supplied skill.md and installed DocumentDB skills cover vector-index and connection best practices. Several important implementation choices are left unspecified (embedding model/provider, LLM provider, exact app surface, test harness, citation format, and whether the portfolio tool is a mock or real integration) — the builder will make reasonable defaults unless the author clarifies them.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 4: Goal and scenario, Workflow type, Language and runtime, Target service and tier |
| Covered by a skill | 3: Authentication and secrets, Queries and indexes, Provisioning and deployment |
| Ambiguous: builder will guess | 4: Driver and version, Data model, AI components, App surface |
| Missing: builder will guess | 5: Sample data, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- Create and populate an Azure DocumentDB vector index including code that upserts docs with embeddings — the prompt implies retrieval but does not explicitly require upsert/seed code; skill guidance exists but the sample may skip a robust idempotent seeding script.
- Ensure agent final responses reference/cite the specific DocumentDB knowledge articles and relevant portfolio values — the prompt asks to combine sources but does not explicitly require citation formatting or including IDs/numbers in responses.
- Provide automated/manual tests verifying vector search returns expected articles, portfolio tool returns structured client data, and follow-up conversational behavior changes when memory or portfolio data are modified — tests are not requested explicitly in the starter prompt.
- The connection string and model credentials come from environment variables; `.env.example` lists every setting — skill.md instructs DOCUMENTDB_URI usage, but embedding/LLM model credentials and a complete `.env.example` are not specified in the starter prompt.
- Vector index dimensions match the embedding model's output — embedding model is unspecified, so matching dimensions and documenting them is at risk.
- Vector index parameters chosen for the sample's data size and README guidance on changing them — documentdb-vector-search gives advice, but the prompt doesn't ask the builder to document or justify chosen parameters.
- Seed script loads sample data and can be run twice without duplicating data — seeding is not explicitly requested and idempotency would be a likely omission unless the builder adds it.
- /search returns a clear error for an empty query and when the embedding call fails — error handling for empty queries/embedding failures is not specified.
- Search results include the similarity score — prompt asks for relevant snippets but does not require returning similarity scores.
- Dependencies are pinned in a requirements file or package manifest — prompt does not require pinned dependency versions or lockfile policy.
- Unit tests run without a live cluster — test strategy is unspecified; unit tests that mock DocumentDB might not be provided.
- Infrastructure for the cluster is provided as code (Azure DocumentDB resource type) — the run environment states a cluster already exists and forbids provisioning, so IAC may be omitted from the sample.
- README covers what the sample shows, prerequisites, setup, run, and clean-up — the prompt doesn't ask for a comprehensive README, though the gallery requires it.
- The sample uses the name 'Azure DocumentDB' throughout — prompt says 'DocumentDB skill' but does not explicitly require consistent product naming in docs and code.

## Questions for the prompt author

- Which embedding provider and exact embedding model should the sample use (e.g., OpenAI text-embedding-3-small) — this determines vector dimension and env vars?
- Which chat/LLM provider & model should LlamaIndex call for generation (OpenAI, local LLM, Anthropic, etc.)? Provide model name or allow the builder to default to a commonly used hosted model.
- Should the portfolio 'tool' be implemented as a mocked local HTTP endpoint/adapter (recommended for reproducible samples), or must it integrate with a live brokerage API? If mocked, please specify expected fields/shape.
- What app surface do you prefer for the sample: minimal Express HTTP API endpoints (e.g., /chat, /search), a CLI script demonstrating conversation, or a small web UI?
- Do you require automated tests that run without a live cluster (unit tests + mocks) in addition to live integration tests against the provided cluster?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Node.js LlamaIndex RAG agent ... retrieves relevant financial knowledge articles from a DocumentDB vector index and combines them with the client's live portfolio data fetched via a tool" | - | - | Business problem and demonstration are clear: RAG over DocumentDB vectors combined with live portfolio tool + agent memory for follow-ups. |
| Workflow type | specified | no | "LlamaIndex RAG agent" with a tool for portfolio data and agent memory | - | - | Single-agent RAG with tool integration (the agent calls a tool to fetch portfolio data). |
| Language and runtime | specified | no | "Node.js" in the starter prompt; skill.md states "Node.js 24 with npm and npx is available." | - | - | Implementation language is Node.js; the provided run environment indicates Node.js 24 is available and should be used. |
| Driver and version | ambiguous | no | - | documentdb-driver | Use the mongodb Node.js driver (npm package `mongodb`) v5.x, and implement the singleton MongoClient pattern (per documentdb-driver guidance). | Starter prompt doesn't name a driver or version. documentdb-driver skill covers the singleton pattern and reuse but does not mandate an exact driver version; builder will pick a recent driver compatible with MongoDB 7.0 (e.g., mongodb v5.x). |
| Target service and tier | specified | no | Skill.md: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) is reachable" | - | - | Run environment gives the exact cluster characteristics to use; the sample should target database `sample_fintech_15` per skill.md. |
| Authentication and secrets | covered_by_skill | no | skill.md: "Its connection string is in the environment variable `DOCUMENTDB_URI`. Read it from the environment at run time. Never write its value into any file... use a config file or `.env.example` with a placeholder" | documentdb-security, documentdb-connection | - | Secrets: DOCUMENTDB_URI in env. documentdb-security provides TLS/Entra/PrivateEndpoint best-practices; documentdb-connection gives connection-string format and TLS requirement guidance. |
| Data model | ambiguous | no | "financial knowledge articles" and portfolio data via a tool (no schema specified) | documentdb-data-modeling | Builder will create a `knowledge` collection with documents like { _id, title, content, embedding, metadata: {source, id, date} } and store embeddings in an `embedding` field; portfolio data will be returned by the tool as structured JSON and not necessarily persisted in DocumentDB. | Prompt doesn't specify exact collections or document shapes. documentdb-data-modeling will guide embedding storage and schema choices; builder must pick concrete shapes and document size restrictions (<=16 MB). |
| Sample data | missing | no | - | documentdb-local-deployment | Include a small curated seed (~20–100 short articles) in a seed script (idempotent upsert) bundled with the sample; client portfolio can be a mocked JSON returned by the tool for the example conversation. | The prompt asks to retrieve knowledge articles but doesn't include or point to seed data. documentdb-local-deployment gives seeding best-practices but does not supply the content. |
| Queries and indexes | covered_by_skill | no | "DocumentDB vector index" and retrieval of relevant knowledge articles | documentdb-vector-search, documentdb-indexing | Use a `vector-diskann` (DiskANN) index given the M30 cluster; choose similarity = COS (cosine) and top-k = 5 by default; index `dimensions` will match the chosen embedding model. | Vector index creation and KNN query guidance is available in documentdb-vector-search; exact parameters (dimensions, lBuild/lSearch/maxDegree) must be chosen by the builder and should be documented in the README. |
| AI components | ambiguous | no | "LlamaIndex" specified for the RAG agent, but embedding model and chat model/provider not named | - | Builder will pick a public embedding provider (e.g., OpenAI text-embedding-3-small or similar) and a chat model compatible with LlamaIndex, and add required env vars (e.g., OPENAI_API_KEY or PROVIDER_API_KEY) in `.env.example`. The embedding model's dimension will determine the vector index dimensions. | The prompt requires LlamaIndex but leaves unspecified the embedding/LLM providers and models; these materially affect vector dimensionality and credentials handling, so author clarification is important. |
| App surface | ambiguous | no | No explicit app interface in the prompt; it only requires an agent with memory and tool integration | - | Builder will implement a minimal Express API with endpoints like POST /chat (conversational agent) and POST /tool/portfolio (mocked tool or adapter), plus a local script that runs an end-to-end conversation for the README and tests. | Starter prompt doesn't say CLI/API/UI; a small HTTP API is the common default for such samples. |
| Provisioning and deployment | covered_by_skill | no | skill.md: "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable." | documentdb-azure-deployment | - | No new cluster should be provisioned for the sample run. documentdb-azure-deployment can be used if the author later wants IAC, but the run instructions prohibit creating a new cluster for this sample. |
| Run and test instructions | missing | no | - | - | Include README with commands: npm install, environment setup, npm run seed (idempotent), npm start, and an npm test script that runs the end-to-end conversation using a mocked portfolio tool. Document what a successful run looks like (sample conversation output and citation of article IDs). | Prompt asks to verify against live cluster per skill.md, but no explicit run/test instruction list is provided in the starter prompt. |
| Definition of done | missing | no | - | - | Adopt the reference acceptance criteria: Node.js LlamaIndex agent that (a) stores/queries DocumentDB vector index, (b) calls portfolio tool at runtime, (c) uses agent memory to resolve follow-ups, and (d) cites article IDs and portfolio numbers in answers; include end-to-end example and tests. | Author didn't state pass/fail criteria; use the reference requirements as the sample's definition of done. |
| Constraints and non-goals | missing | no | - | documentdb-security | Keep cloud changes minimal (no provisioning), avoid storing secrets in repo, keep sample small to limit costs, and treat the portfolio tool as a demo integration (not a production connector). | Prompt lacks cost/licence/compliance constraints; documentdb-security advises security constraints but doesn't specify cost or non-goals. |
| Repository conventions | missing | no | - | - | Follow gallery conventions: top-level README, `src/`, `scripts/seed.js`, `tests/`, `.env.example`, and use `package.json` with pinned versions (or lockfile) and a clear run/test script set. | Starter prompt doesn't specify folder layout, README sections or naming conventions. |
