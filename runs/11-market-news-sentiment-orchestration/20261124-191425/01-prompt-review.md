# 1. Prompt review: 11-market-news-sentiment-orchestration

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines a multi-agent LangChain pipeline in Node.js that scrapes headlines, scores sentiment/tickers, stores results in Azure DocumentDB, and fires alerts. Most infrastructural and DocumentDB details are provided in the supplied run-environment (skill_md) and relevant installed DocumentDB skills cover driver/connection/indexing patterns; several implementation choices (driver version, exact schemas, AI model, news source, webhook auth, and indexing details) are left to the builder and will be assumed if not answered.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 6: Goal and scenario, Workflow type, Language and runtime, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Covered by a skill | 2: Driver and version, Repository conventions |
| Ambiguous: builder will guess | 6: Data model, Sample data, Queries and indexes, App surface, Run and test instructions, Definition of done |
| Missing: builder will guess | 2: AI components, Constraints and non-goals |
| Not applicable | 0: - |

## Reference requirements at risk

- Exact notification JSON payload shape and observable delivery: prompt requires firing notifications but does not prescribe the exact fields; builder will choose a payload shape unless asked to use a specific schema.
- Persisted document field-level schema: prompt says store scored articles but does not enumerate exact field names/types (unique id format, field names for sentiment/tickers, metadata).
- `.env.example` listing every setting: run-environment suggests using a .env.example but the prompt doesn't explicitly request it; builder may or may not include a complete example.
- Vector index dimensions and parameters matched to any embedding model: no embedding model or dimension is specified, so any vector index created could mismatch or be omitted.
- Idempotent seed script that loads sample data and creates indexes: prompt asks to fetch live headlines, not to include an idempotent seed script; a seed script may be omitted.
- Dependencies pinned in a requirements file: prompt is Node.js-based; it does not require pinned dependency manifest (package-lock.json or pinned versions).
- Unit tests that run without a live cluster: prompt asks to verify against the live cluster; it doesn't require offline/unit tests that mock the cluster.
- Infrastructure-as-code for the Azure DocumentDB cluster: the run-environment provides a pre-provisioned cluster and the prompt does not request IaC, so infra code may be absent.
- README completeness: prompt doesn't enumerate README sections; the builder may produce a minimal README that lacks one of: prerequisites, setup, run, clean-up.
- Explicit demonstration script that also verifies a document was written and shows an alert firing: prompt asks for the pipeline, but does not mandate an automated demo that asserts DB writes and webhook receipt; the demo could be manual observation only.

## Questions for the prompt author

- Which news source(s) should the scraper use (public RSS feeds, NewsAPI, a paid feed)? If NewsAPI or a paid API is desired, will an API key be provided in an env var?
- Which LLM / provider do you want used for sentiment and ticker extraction (e.g., OpenAI, local model, or a simple rule-based extractor)? This affects env vars and dependency choices.
- Should alert webhook calls require authentication or a specific JSON schema/signature (the reference requires a payload with specific fields — confirm exact required fields and any auth headers)?
- Do you want an idempotent seed script and unit tests that mock the cluster (yes/no)? Tests and a seed script would change the repository contents and CI assumptions.

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | “build a Node.js LangChain orchestration pipeline with a scraper agent ... a sentiment agent ... and an alert agent ... Store all scored articles as documents in DocumentDB.” | - | - | Business goal and what the sample demonstrates are explicit in the starter prompt. |
| Workflow type | specified | no | “LangChain orchestration pipeline ... scraper agent ... sentiment agent ... alert agent” | - | - | Multi-agent orchestration with LangChain is explicitly requested. |
| Language and runtime | specified | no | Prompt: “Node.js”; skill_md: “Node.js 24 with npm and npx is available.” | - | - | Node.js is requested; the provided run-environment (skill_md) supplies Node.js 24. |
| Driver and version | covered_by_skill | no | - | documentdb-driver | Use the official mongodb Node.js driver (mongodb) compatible with Node.js 24 — e.g., mongodb@5.x — and follow the documentdb-driver guidance (singleton MongoClient, connection reuse). | Starter prompt doesn't name a driver; documentdb-driver skill prescribes best practices but not an exact npm version. Builder will pick a stable mongodb driver compatible with Node.js 24. |
| Target service and tier | specified | no | Prompt: “DocumentDB” and skill_md: “A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol ...) is reachable... use database named `sample_fintech_11`.” | - | - | The run environment supplies a live, vector-capable cluster and the exact DB name to use. |
| Authentication and secrets | specified | no | skill_md: “Its connection string is in the environment variable `DOCUMENTDB_URI`. Read it from the environment at run time. Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder, as the prompt asks.” | - | - | Connection string location and handling are defined in the provided run-environment guidance. |
| Data model | ambiguous | no | Prompt: store scored articles in DocumentDB; extract tickers; watchlist lookup and alerts. | documentdb-data-modeling | Builder will create two collections in database `sample_fintech_11`: `sentiment_signals` (documents with _id, headline, sentiment_score (number), tickers (array), source, timestamp, optional metadata) and `watchlist` (documents with _id and ticker string and optional watch metadata). | Prompt requires persistence but does not define concrete field names, id format, or watchlist schema. documentdb-data-modeling provides design guidance but not exact schema; builder must choose field names and types. |
| Sample data | ambiguous | no | Prompt: “scraper agent that fetches financial news headlines” (live via HTTP). | documentdb-local-deployment | Use public RSS feeds (e.g., Reuters/Investing.com/MarketWatch RSS) or a free NewsAPI if key provided; no licensed bulk dataset. No large seed dataset expected — demo runs on a few live headlines. If seed data is desired, add an idempotent seed script that inserts a small set of example watchlist rows and sample articles. | Prompt mandates live scraping but does not require a seed script, dataset licensing, or data size. The run-environment suggests sample-data patterns but doesn't provide a specific seed. |
| Queries and indexes | ambiguous | no | - | documentdb-indexing | Create a multikey index on `tickers`, an index on `timestamp` for recent-first queries, and a text / textSearch index on `headline` for keyword queries. If embeddings/vector search are used later, create a vector index with parameters appropriate for the demo (small nlist / HNSW defaults). | Prompt asks to store and query watchlist matches but does not call out specific index shapes; documentdb-indexing skill can be used to pick appropriate indexes. |
| AI components | missing | no | - | - | Use an external LLM provider (commonly OpenAI) via LangChain for the sentiment/ticker-extraction agent, with API key in env var (e.g., OPENAI_API_KEY). Use a chat model for classification/symbol extraction; embeddings are optional and not required for the core sample. | Starter prompt asks for a sentiment agent but gives no model/provider, credentials, or embedding dimensions. This will be a key implementation choice the builder must pick. |
| App surface | ambiguous | no | Prompt: build a Node.js LangChain orchestration pipeline — no explicit CLI/API/UI specified. | - | Provide a command-line demo script (`npm run demo`) that runs the LangChain orchestrator for a small batch of scraped headlines and also include a small optional HTTP webhook test server to receive and show outgoing notifications during the demo. | Prompt does not require a web UI or API surface; a CLI/demo script is the minimal and likely implementation. |
| Provisioning and deployment | specified | no | skill_md: “This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable ... Use the database named `sample_fintech_11` ... Do not provision another cluster unless the run policy says Azure writes are allowed.” | - | - | Run environment explicitly supplies a pre-provisioned cluster and forbids creating a new one for the sample run. |
| Run and test instructions | ambiguous | no | Prompt: build the pipeline; skill_md: environment notes including env var DOCUMENTDB_URI, Node.js 24 available; verify against the live cluster. | - | Provide README with steps: set env vars (DOCUMENTDB_URI, OPENAI_API_KEY, WEBHOOK_URL), npm install, npm run demo; demo prints sentiment/tickers, verifies DB write (via a read), and demonstrates webhook call. | The run-environment gives some operational constraints but not exact run/test commands. The builder will author explicit commands in README and npm scripts. |
| Definition of done | ambiguous | no | Prompt: implement scraping, scoring, storing, and alerting; save scored articles to DocumentDB. | - | Definition of done: pipeline runs end-to-end on at least one scraped headline, sentiment + tickers are structured outputs, the article is written to `sample_fintech_11.sentiment_signals`, and a webhook receives a JSON notification when a ticker is on the `watchlist`. | No formal acceptance criteria were given; builder will use the reference requirements as the checklist. |
| Constraints and non-goals | missing | no | - | - | Keep cloud costs minimal (no new cluster provisioned). Do not attempt production HA, CMK, or private networking in the sample. No compliance certification effort is required for the demo. | No cost or non-goal constraints are stated in the prompt; the run-environment does suggest not provisioning a cluster. |
| Repository conventions | covered_by_skill | no | skill_md: “Read it from the environment at run time. Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder, as the prompt asks.” | documentdb-local-deployment | Repo will include a `.env.example` with placeholder variables (DOCUMENTDB_URI, OPENAI_API_KEY, WEBHOOK_URL), a top-level README, an `src/` layout with agents as separate modules, and npm scripts `demo`, `seed`. | Skills and run-environment instruct env-driven config and avoiding secrets in repo; specific folder layout and README content will be chosen by the builder. |
