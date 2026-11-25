# 1. Prompt review: 09-crypto-wallet-activity-analyzer

**Verdict: sufficient_with_assumptions**

The starter prompt gives a clear goal (a Python LangChain single-agent that runs a MongoDB aggregation to compute daily volume/frequency and flags outliers) and enough specifics to start building. Several implementation details (Python runtime version, driver version, exact entrypoint shape, LLM/embedding choices, sample-data and repo conventions) are left to the builder and will be chosen by defaults or guided by installed skills (notably the DocumentDB query and indexing skills). No blocking gaps were found, but expect the builder to make assumptions about runtime, driver, data schema, sample data, and how the agent is invoked.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Workflow type, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Covered by a skill | 1: Queries and indexes |
| Ambiguous: builder will guess | 8: Language and runtime, Driver and version, Data model, AI components, App surface, Run and test instructions, Definition of done, Constraints and non-goals |
| Missing: builder will guess | 2: Sample data, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- .env.example listing every setting with placeholder values — prompt/skills mention DOCUMENTDB_URI but don't require or supply a full .env.example.
- Vector index dimensions must match the embedding model's output — embeddings/model choice not specified, so vector-dim coordination is at risk.
- Vector index parameters chosen for sample data size, and README guidance how to change them — vector-index tuning and README guidance not requested.
- Seed script that loads sample data and creates the index, runnable twice without duplicating data — prompt doesn't request a seed script; the sample-data requirement is missing.
- /search returns a clear error for an empty query and when the embedding call fails — the starter prompt does not include a /search route.
- Search results include the similarity score — search behavior is not part of the prompt.
- Dependencies pinned in requirements.txt — prompt does not mandate pinning; builder may or may not pin versions.
- Unit tests run without a live cluster — tests (mocking or local emulation) are not requested or specified.
- Infrastructure-as-code for the cluster (Azure DocumentDB resource type) — the run-environment provides an existing cluster and the prompt explicitly avoids provisioning; IaC is not provided.
- README covering what the sample shows, prerequisites, setup, run, and clean-up — README content is not specified in the starter prompt (likely included by the builder, but at risk).
- The sample uses the name 'Azure DocumentDB' throughout — the prompt uses 'DocumentDB' but does not explicitly require consistent naming in docs; this is easy to miss.

## Questions for the prompt author

- Do you want the sample to expose a library function only (e.g., analyze_wallet(address: str)), a CLI, or an HTTP API endpoint? This changes the top-level entrypoint and examples.
- Which LLM/provider and model should be used for the plain-language summary (if any)? If you prefer no external LLM, the agent can synthesize the summary locally using deterministic templates and statistics.
- Should the sample include an idempotent seed data script (and if so, do you prefer synthetic generated data or an anonymized public dataset)?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "group wallet transactions by day, computes volume and frequency metrics, and flags statistical outliers... accept a wallet address, run the analysis pipeline, and return a plain-language summary of activity patterns and any anomalies detected." | - | - | Clear business problem and demonstrated capabilities. |
| Workflow type | specified | no | "build a Python LangChain agent with a DocumentDB aggregation tool" — single-agent using LangChain. | - | - | Single-agent (LangChain) is explicitly requested. |
| Language and runtime | ambiguous | no | "Python LangChain agent" | - | Builder will target a modern Python 3.x, most likely 3.10 or 3.11 (common default). The sample will include a virtualenv and use `python`/`pip` per the provided run-environment notes. | No explicit Python version or runtime constraints were given. |
| Driver and version | ambiguous | no | - | documentdb-driver | Use the official PyMongo driver (pymongo) compatible with MongoDB 7.0, e.g. pymongo >=4.3,<5.0, and follow documentdb-driver guidance to reuse a singleton MongoClient. | The documentdb-driver skill provides best-practice patterns (singleton client) but does not mandate a concrete driver version; the builder will pick a compatible pymongo release. |
| Target service and tier | specified | no | skill_md: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) is reachable... use database named `sample_fintech_09`" | - | - | Run-environment (skill_md) supplies the exact cluster/tier and DB name to use for the sample. |
| Authentication and secrets | specified | no | skill_md: "Its connection string is in the environment variable `DOCUMENTDB_URI`. Read it from the environment at run time. Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder, as the prompt asks." | - | - | Specifies env var location and a secrecy rule; MCP profile 'default' is also available. |
| Data model | ambiguous | no | "transactions time-series collection" (prompt) and database `sample_fintech_09` (skill_md) | documentdb-data-modeling | Builder will create/use a `transactions` collection with documents having at least: { wallet_address: string, timestamp: ISODate, amount: number, currency?: string, tx_id?: string }. No shard key by default (single-shard), and daily grouping uses the `timestamp` field. | Prompt requires a time-series transactions collection but does not define field names or exact schema; the data-modeling skill gives patterns but not the concrete schema. |
| Sample data | missing | no | - | documentdb-local-deployment | Builder will add a small synthetic seed script that creates `transactions` documents (e.g., a few hundred rows spanning several dates) and can be re-run idempotently (upsert or check-before-insert). | Starter prompt asks to run the analysis pipeline but does not provide or point to seed data. The local-deployment skill talks about seed-data best practices but doesn't supply the sample. |
| Queries and indexes | covered_by_skill | no | "aggregation tool that groups wallet transactions by day... computes volume and frequency..." | documentdb-natural-language-querying, documentdb-indexing | The aggregation pipeline will include an early $match on wallet_address and a $group or $dateTrunc-based stage to compute daily sum(count) and sum(amount). Builder will create an index on { wallet_address: 1, timestamp: 1 } to support the $match + date-range/group pattern. | The natural-language-querying skill covers how to generate correct aggregation pipelines and the safety rules; the indexing skill covers recommended index shapes. |
| AI components | ambiguous | no | - | - | Builder will likely use a small chat model via LangChain for plain-language summarization (e.g., OpenAI chat model) or rely on local summarization; embeddings are probably not required because the analysis is statistical; if used, a common embedding model (text-embedding-3-small) with 1536 dims may be chosen. | Prompt doesn't specify any LLM/embedding model, provider, or dimensions; this affects README and vector-index choices if vectors are used. |
| App surface | ambiguous | no | "The agent should accept a wallet address, run the analysis pipeline, and return a plain-language summary" | documentdb-natural-language-querying | Builder will implement a Python entrypoint function such as analyze_wallet(address: str) -> str and expose a small CLI (`python -m sample_fintech_09 analyze <wallet>`) that calls the LangChain agent; unit/integration runnable script will be provided. | Prompt requires the agent to accept a wallet address but doesn't mandate CLI vs API vs library function. The reference requires a function analyze_wallet; builder will likely include it. |
| Provisioning and deployment | specified | no | skill_md: "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable... use the database named `sample_fintech_09`... Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use." | - | - | The environment is already provisioned for this sample; the builder will not create cloud infra as part of the normal run. |
| Run and test instructions | ambiguous | no | - | documentdb-local-deployment | Builder will include basic run instructions (create virtualenv, pip install -r requirements.txt, set DOCUMENTDB_URI, run `python -m sample_fintech_09` or invoke analyze_wallet). Tests likely limited; detailed CI/test commands will be minimal unless requested. | No explicit run/test commands were requested; skill_md includes suggested verification steps but not concrete README commands. |
| Definition of done | ambiguous | no | "agent ... groups wallet transactions by day, computes volume and frequency metrics, and flags statistical outliers... return a plain-language summary" | - | Builder will treat 'done' as: a working Python LangChain agent that accepts a wallet address, calls a tool named exactly 'DocumentDB aggregation tool' which runs a server-side aggregation returning daily date/daily_volume/daily_count, the agent performs statistical outlier detection and returns a plain-language summary enumerating anomalies. | No formal acceptance checklist was provided; the above pragmatic definition follows the prompt and the reference. |
| Constraints and non-goals | ambiguous | no | skill_md: "Never write its [DOCUMENTDB_URI] value into any file, log, README or test fixture... Do not provision another cluster unless allowed." | documentdb-security | Builder will avoid persisting secrets and will not attempt to provision new infrastructure; cost limits and other non-goals are not specified and will not be enforced. | Some security constraints are supplied in the run-environment, but cost/scale non-goals are not specified. |
| Repository conventions | missing | no | - | - | Builder will follow common sample conventions: include README, requirements.txt, .env.example, src/ package, scripts/seed_data.py, and a main CLI that invokes analyze_wallet. Dependencies may be pinned but that is not guaranteed without instruction. | The starter prompt does not specify repo layout, README content, or dependency-pinning conventions. |
