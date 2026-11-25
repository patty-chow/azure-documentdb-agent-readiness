# 1. Prompt review: 11-market-news-sentiment-orchestration

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines the high-level goal (a Node.js LangChain orchestration pipeline with scraper, sentiment and alert agents that persist scored articles into Azure DocumentDB). The provided run-environment (skill_md) supplies the live DocumentDB cluster details and runtime (Node 24) so a build can start, but many implementation choices are unspecified (LLM/embedding models, MongoDB driver version, collection names, notification mechanism, seed data, indexes, and run/test docs) and will be decided by the builder's defaults.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 2: Goal and scenario, Workflow type |
| Covered by a skill | 3: Language and runtime, Target service and tier, Provisioning and deployment |
| Ambiguous: builder will guess | 5: Authentication and secrets, Data model, AI components, App surface, Constraints and non-goals |
| Missing: builder will guess | 6: Driver and version, Sample data, Queries and indexes, Run and test instructions, Definition of done, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- Use a Node.js MongoDB driver for Azure DocumentDB with a specified version: missing — neither prompt nor skill_md names or pins the driver/version.
- Notification implementation details: missing — prompt requires 'fires notifications' but gives no transport or mechanism; skill_md does not cover this.
- Model credentials in environment variables: partially covered — skill_md provides DOCUMENTDB_URI but does not specify how model/API keys are supplied; prompt is silent.
- .env.example listing every setting with placeholders: missing — neither prompt nor skill_md requires or provides this.
- Vector index dimensions must match embedding model output: missing — embedding model not chosen, so dimensions and index creation are unspecified.
- Vector index parameters chosen for sample data and README guidance: missing — no index parameter choices or README guidance in prompt or skill_md.
- One database client created and reused across requests: missing — not specified.
- Seed script loads sample data and creates the index and is idempotent: missing — prompt asks to store data but doesn't require a seed script or idempotency.
- /search error handling (empty query and failed embedding call) and returning similarity score: missing — no /search endpoint specified and no error handling requirements provided.
- Dependencies pinned in requirements.txt: missing / mismatched — reference expects pinned deps; for Node this would be package-lock.json or pinned package.json versions, but prompt/skill_md do not mandate pinning.
- Unit tests run without a live cluster: missing — tests and mocking strategy are not specified.
- Infrastructure-as-code for the cluster: missing — skill_md instructs to use the provided cluster but does not provide IaC; reference requires IaC which is not covered.
- README covering what the sample shows, prerequisites, setup, run, and clean-up: missing — prompt does not require or describe README contents.
- Use the name 'Azure DocumentDB' throughout: missing — prompt does not mandate consistent naming in repo; risk that other product names will be used.

## Questions for the prompt author

- Which LLM/embedding provider and specific models should the sample use (OpenAI/Azure OpenAI and exact model names)? This determines embedding dimensions and index parameters.
- Which notification mechanism should the alert agent use to 'fire notifications' (console log, webhook, email, Slack, or a stub/mock for demo)?
- Which Node MongoDB driver version should be used (which major/minor do you require) and what collection names/schema should be canonical (e.g. 'articles' and 'watchlist')?
- Should the sample include an HTTP API surface (endpoints) or only a CLI/script to run the orchestration? Will unit tests be allowed to use a live cluster or must they run fully mocked?

## Contradictions and missing references

- Prompt: "Using the DocumentDB skill" — no installed agent skill named 'DocumentDB' is present in installed_skills. (Only run-environment skill_md was provided; there is no implemented skill that the prompt explicitly references.)
- Reference asks for dependencies pinned in 'requirements.txt' (Python) but this sample is Node.js; mismatch between reference checklist and sample language.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Node.js LangChain orchestration pipeline with a scraper agent that fetches financial news headlines, a sentiment agent that scores each headline and extracts ticker mentions, and an alert agent that checks DocumentDB for matching watchlist entries and fires notifications. Store all scored articles as documents in DocumentDB." | - | - | - |
| Workflow type | specified | no | "Node.js LangChain orchestration pipeline" and named agents (scraper, sentiment, alert) run in order | - | - | - |
| Language and runtime | covered_by_skill | no | "Node.js" | Run environment (skill_md) | - | skill_md states Node.js 24 is available; builder will use that runtime. |
| Driver and version | missing | no | - | - | Use the official 'mongodb' npm package (Node driver) and pin a recent stable major that supports MongoDB 7.0 wire protocol, e.g. 'mongodb' ^5.7.0 in package.json. | Prompt asks to store documents in DocumentDB but does not name the Node MongoDB driver or version. |
| Target service and tier | covered_by_skill | no | References DocumentDB as the target | Run environment (skill_md) | - | skill_md provides a reachable vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF) and database name 'sample_fintech_11'. |
| Authentication and secrets | ambiguous | no | - | Run environment (skill_md) | Database connection string is read from DOCUMENTDB_URI env var (per skill_md). Model/API credentials will be read from standard env vars (e.g. OPENAI_API_KEY or AZURE_OPENAI_KEY) — builder must choose a provider and env var names. | skill_md prescribes DOCUMENTDB_URI for the DB secret. The prompt does not say which LLM/provider or where its credentials live. |
| Data model | ambiguous | no | "Store all scored articles as documents in DocumentDB" and sentiment + extracted tickers | Run environment (skill_md) | Create a database 'sample_fintech_11' with collections 'articles' and 'watchlist'. Article documents include fields: _id, headline (string), sentiment (number or enum), tickers (array of strings), timestamp. Watchlist documents include ticker and notification metadata. | Prompt states the per-article fields but not collection names, watchlist schema, shard key, or precise types. |
| Sample data | missing | no | - | Run environment (skill_md) | Provide a small seed dataset (e.g. ~20 headlines with associated tickers and a watchlist of a few tickers) loaded by an idempotent seed script in scripts/seed.js. | Neither prompt nor skill_md specifies sample data source, size, licensing, or an explicit seed script. |
| Queries and indexes | missing | no | - | Run environment (skill_md) | Create a text index on headline and a vector index sized to the chosen embedding model (assume embedding dims 1536 if using text-embedding-3-small). Default index parameters will be used appropriate for small sample data; README will note how to change them. | Prompt requires checking DocumentDB for watchlist matches and storing documents, but does not specify index types or query patterns. skill_md notes vector-capable cluster but no index details. |
| AI components | ambiguous | no | "sentiment agent that scores each headline and extracts ticker mentions" | - | Use an LLM (OpenAI-compatible) for sentiment and ticker extraction, with model creds in env (e.g. OPENAI_API_KEY). Use an embedding model (e.g. text-embedding-3-small, dims 1536) if embeddings are needed for similarity search. | Prompt requires an AI sentiment/extraction step but gives no provider, model names, or embedding usage. |
| App surface | ambiguous | no | An orchestration pipeline with agents (no explicit API/CLI/UI specified) | - | Implement a CLI / npm script to run the orchestration end-to-end and a minimal Express-based HTTP endpoint (e.g. POST /run or GET /run) to trigger the pipeline for demo purposes. Provide npm scripts: 'seed', 'start', 'run'. | Prompt doesn't prescribe CLI vs API vs UI. |
| Provisioning and deployment | covered_by_skill | no | - | Run environment (skill_md) | Do not provision another DocumentDB cluster; use the cluster referenced in DOCUMENTDB_URI. No IaC will be added unless repository policy allows it. | skill_md explicitly states an existing cluster is available and advises against provisioning another cluster for the sample run. |
| Run and test instructions | missing | no | - | Run environment (skill_md) | README will include commands: npm install, npm run seed, npm start (or npm run demo), and npm test. Tests will be defined but may need a live cluster unless using mocking. | Prompt does not include concrete commands or test expectations. |
| Definition of done | missing | no | - | - | Definition of done: orchestrator runs end-to-end; each headline is scored and stored in 'articles' collection with sentiment and tickers; alert agent queries watchlist and emits at least one demonstrable notification during demo; seed script runs idempotently. | - |
| Constraints and non-goals | ambiguous | no | - | Run environment (skill_md) | Keep cloud writes limited to the provided cluster only; do not provision additional infra. No production-grade SLA/HA, no telemetry or payment integration; cost sensitivity not explicitly constrained. | skill_md enforces not provisioning another cluster and not logging secrets; other constraints (cost, compliance) are not specified. |
| Repository conventions | missing | no | - | - | Repository will have standard layout: README.md, src/, scripts/ (seed), tests/, package.json, .env.example, .gitignore. Use 'Azure DocumentDB' terminology in README and code comments. | Prompt doesn't specify naming, layout, README sections, or packaging conventions. |
