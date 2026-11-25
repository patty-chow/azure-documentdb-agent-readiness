# 1. Prompt review: 06-order-history-timeline-agent

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines the core goal (a Python LangChain single-agent with memory and three tools) and, together with the supplied run-environment skill.md and the installed documentdb-* skills, provides enough to start a build. Several implementation details are unspecified (Python version, LLM/embedding choices, exact orders schema, seed-data source, indexing choices, run/test commands), so the builder will make sensible defaults described below.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Workflow type, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Covered by a skill | 1: Driver and version |
| Ambiguous: builder will guess | 5: Language and runtime, Data model, Queries and indexes, App surface, Repository conventions |
| Missing: builder will guess | 5: Sample data, AI components, Run and test instructions, Definition of done, Constraints and non-goals |
| Not applicable | 0: - |

## Reference requirements at risk

- fetch_order_history tool must include pagination/limit logic — prompt implies fetch but does not specify pagination; builder will likely implement a page/limit but this requirement is not explicit.
- seed script that loads sample data and creates the index and can be run twice without duplicating data — prompt/skill.md asks to load sample data but does not require idempotent seeding; installed skills don't provide a repo seed script.
- Executable example or unit test that demonstrates conversational context resolution — prompt requests correct resolution of 'what about last month?' but does not explicitly require an automated example/test; risk the builder provides only a manual demo.
- Handling empty results and DB errors gracefully — prompt doesn't explicitly require friendly error handling; risk of minimal error messages if builder omits explicit handling.
- Vector index dimensions must match embedding model output and index parameters chosen for sample size — prompt mentions cluster is vector-capable in skill.md but does not choose embedding model or index dims; this mapping is not specified.
- .env.example lists every setting with placeholder values — skill.md suggests using a .env.example but does not enumerate all env vars required by the agent (LLM keys, other options).
- Search results include similarity score (if vector search used) — prompt doesn't mention vector search result formatting; skill.md notes vector-capable cluster but not how to surface scores.
- Dependencies pinned in requirements.txt — neither prompt nor skills require pinned dependencies; builder may or may not pin versions.
- Unit tests run without a live cluster — prompt/skill.md expect verification against live cluster but do not require tests to mock the DB for offline execution.
- Infrastructure-as-code for the cluster — prompt/skill.md explicitly say a cluster already exists and not to provision another; the gallery requirement to provide infra code is not covered.

## Questions for the prompt author

- Which LLM and embedding provider/models should the sample use by default (OpenAI, Anthropic, local model)? This affects embeddings dims and code examples.
- Which exact Python minor version should we target (e.g., 3.10 or 3.11)?
- Should unit tests be runnable without a live cluster (i.e., use mocks) or is verifying against the live cluster acceptable for CI/local testing?

## Contradictions and missing references

- The prompt says "Using the DocumentDB skill" but there is no single installed skill named exactly "DocumentDB"; instead multiple documentdb-* skills are available (documentdb-driver, documentdb-connection, documentdb-data-modeling, etc.). Builder will combine these skills, but the wording could be interpreted as a missing single-skill name.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python LangChain agent with agent memory that connects to DocumentDB and has tools for fetching order history, running aggregation pipelines for spend summaries, and looking up individual order status" | - | - | Clear user/problem and what sample should demonstrate (conversation-aware order history & spend summaries). |
| Workflow type | specified | no | "Python LangChain agent" (single agent with tools / agent memory) | - | - | Single-agent LangChain is explicit. |
| Language and runtime | ambiguous | no | "Python" | - | Target a modern Python 3.10+ runtime (virtualenv), e.g., support CPython 3.10 or 3.11. Use pip for dependency installation. | Prompt and skill.md mention Python and pip but do not fix a minor version; builder will pick a recent 3.x version. |
| Driver and version | covered_by_skill | no | - | documentdb-driver | Use pymongo (the official Python MongoDB driver), e.g., pymongo >= 4.3 compatible with MongoDB 7.x; create a singleton MongoClient reused across requests. | Installed documentdb-driver skill gives driver best-practices (singleton MongoClient, connection reuse). |
| Target service and tier | specified | no | skill.md: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) ... connection string in environment variable DOCUMENTDB_URI ... Use the database named sample_retail_06" | - | - | The supplied run-environment skill.md gives explicit cluster/tier and database to use; the build must target this existing cluster. |
| Authentication and secrets | specified | no | skill.md: "connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time. Never write its value into any file... use a config file or .env.example with a placeholder" | - | - | Where to read the connection string and that it must not be committed is explicit. |
| Data model | ambiguous | no | "fetching order history ... lookup individual order status" (implies an orders collection) | documentdb-data-modeling | Builder will create an orders collection with a simple, conventional retail schema: order_id (string, unique), customer_id, order_date (ISODate), items[] (sku, qty, price), total_amount (number), status (string). No sharding by default (single-shard cluster), no >16MB docs. | The prompt implies an orders collection but does not specify exact fields, types, or shard key; documentdb-data-modeling can guide choices but not the exact schema. |
| Sample data | missing | no | - | documentdb-local-deployment | Include a small synthetic seed script (seed.py) that inserts a few hundred orders across several customers. The seed script should be idempotent (upsert by order_id) so it can be re-run. | No source, size, or load method specified; skill.md asks to "load the sample data" during verification but doesn't supply it. |
| Queries and indexes | ambiguous | no | "tools for fetching order history, running aggregation pipelines for spend summaries, and looking up individual order status" | documentdb-natural-language-querying, documentdb-indexing | Implement find() for customer order history (filter by customer_id, sort by order_date desc, limit/paginate). Implement aggregation pipelines for spend summaries (total_spent, order_count) including a 'last month' pipeline. Create indexes: single-field index on customer_id, compound (customer_id + order_date) or separate order_date index, and unique index on order_id. | The prompt requires find() and aggregation pipelines but does not specify index shapes; installed indexing skill can guide index choices. |
| AI components | missing | no | mentions LangChain agent but no LLM/embedding provider or models | - | Default to OpenAI for models: Chat model via environment variable OPENAI_API_KEY (e.g., gpt-4o-mini or gpt-4o), and embeddings via OpenAI text-embedding-3-small (1536 dims). Provide env var placeholders in .env.example for provider keys. | Model/embedding provider, exact models and dims are not specified and will materially affect vector index choices if used. |
| App surface | ambiguous | no | - | - | Provide a simple CLI interactive script (run_agent.py) demonstrating conversation turns and a small programmatic example/test that shows sequence: ask history -> follow-up 'what about last month?'. Optionally include a minimal HTTP API wrapper, but primary surface is CLI/test. | Prompt does not mandate CLI vs API or web UI; builder will pick an interactive CLI + automated test to demonstrate behavior. |
| Provisioning and deployment | specified | no | skill.md: "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable... Do not read or change other databases on the cluster." | - | - | The environment explicitly says use the existing cluster; do not provision new resources. |
| Run and test instructions | missing | no | - | - | README will include: pip install -r requirements.txt; copy .env.example -> .env and fill DOCUMENTDB_URI and OPENAI_API_KEY; python seed.py; python run_agent.py; pytest to run unit tests. The builder will add concrete commands for the chosen Python version and virtualenv activation. | No concrete commands or expected outputs are present in the prompt or skills. |
| Definition of done | missing | no | - | - | Acceptance criteria: agent runs, tools are registered, memory persists last-customer and last-time-range across turns, aggregation and find tools run against sample_retail_06.orders, and the example/test demonstrates resolving 'what about last month?' to the correct customer/time-range results. | Not explicitly stated; builder will create pragmatic acceptance checks. |
| Constraints and non-goals | missing | no | - | skill.md (partial) | Do not provision new cloud resources; keep secrets out of repo; keep sample lightweight and free-tier friendly where possible. No production HA or CMK work is required. | Prompt does not call out cost or scope constraints except via skill.md guidance not to create resources. |
| Repository conventions | ambiguous | no | skill.md: "use a config file or .env.example with a placeholder" | - | Repository will include: README.md, requirements.txt (pinned), .env.example with placeholders (DOCUMENTDB_URI, OPENAI_API_KEY), src/ or agent/ layout, seed.py, run_agent.py, tests/, .gitignore. Use the name 'Azure DocumentDB' in docs. | Some conventions are implied by skill.md (.env.example), but many conventions (pin deps, tests) are not explicitly specified. |
