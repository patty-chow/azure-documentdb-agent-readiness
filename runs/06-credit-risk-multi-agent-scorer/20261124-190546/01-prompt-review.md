# 1. Prompt review: 06-credit-risk-multi-agent-scorer

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines the goal (a Python LangChain multi-agent credit-scoring pipeline) and the three agents; together with the supplied skill.md it gives enough to start coding. Several implementation details are missing (Python version, exact Mongo driver/version, exact applicant schema, LLM provider/model, seed data, indexes, tests and README), so the builder will fill those in with reasonable defaults unless the author clarifies them.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Workflow type, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Covered by a skill | 0: - |
| Ambiguous: builder will guess | 6: Language and runtime, Driver and version, Data model, AI components, App surface, Repository conventions |
| Missing: builder will guess | 5: Sample data, Queries and indexes, Run and test instructions, Definition of done, Constraints and non-goals |
| Not applicable | 0: - |

## Reference requirements at risk

- Data-fetch agent must return a structured Python dict/JSON containing the retrieved fields — prompt says retrieve applicant history but does not mandate the exact structured shape; no skill provides the concrete shape.
- Scoring agent must include at least two explicit deterministic, inspectable risk rules and expose rule evaluations — prompt requires "risk rules" but does not enumerate or mandate at least two named rule implementations; no installed skill supplies scoring rules.
- Scoring agent must include both rule-based score and LLM-derived final score in its output — the prompt expects an LLM call but does not specify the exact output contract; risk of mismatch in output format.
- Pipeline orchestration order (data-fetch -> scoring -> explainer) must be enforced programmatically — prompt implies sequential agents but does not explicitly state ordering; builder may infer the order but it's not spelled out.
- Write-back must add a timestamp and agent metadata (agent names, rule summary, LLM output snippet) to the applicant document — prompt asks to store score and explanation but does not specify timestamp or metadata fields; risk that builder omits these extras.
- Code must handle missing applicants and DB errors gracefully and avoid writing incomplete results — prompt does not explicitly require error handling details; builder might not include thorough error-avoidance behavior without direction.
- Include an automated test or runnable example that exercises the full pipeline end-to-end against a test Azure DocumentDB dataset and asserts final write-back — prompt asks to build the pipeline but does not mandate tests or a seed dataset; this is likely to be omitted unless the author requires it.
- `.env.example` must list every setting with placeholders — skill.md recommends `.env.example` but does not list all required settings (LLM keys, model names, etc.), so the builder must choose and could omit some.
- Vector index dimensions and parameters must match the embedding model and dataset size — prompt and skill.md mention vector-capable cluster but do not give embedding model/dimensions or index parameters; this is at risk if embeddings are used.
- Dependencies pinned in `requirements.txt` — the prompt does not require pinned dependencies; builders may or may not pin versions unless instructed.
- Unit tests that can run without a live cluster — prompt expects verification against the live cluster; nothing requires mocks or tests that run offline, so unit-test isolation is at risk.
- Infrastructure-as-code for the cluster using the Azure DocumentDB resource type — the run environment forbids provisioning a cluster for this sample so IaC is not requested; if the gallery expects IaC, it's at risk of being missing.

## Questions for the prompt author

- Which LLM provider and model should the scoring agent call (e.g., OpenAI gpt-3.5-turbo, gpt-4o-mini, Azure OpenAI with a specific deployment)?
- Which exact Python runtime should the sample target (e.g., 3.10 or 3.11)?
- What is the canonical collection name and exact applicant document schema (field names and types) the sample should use and seed in tests?
- Do you want the sample to include an idempotent seed script with synthetic applicant records, or will you provide a test dataset?
- Should the repo include infrastructure-as-code to provision an Azure DocumentDB cluster, or must it strictly use the pre-provisioned cluster from skill.md?

## Contradictions and missing references

- The prompt asks to use "the DocumentDB skill" but there is no single installed skill named exactly "DocumentDB skill"; instead multiple documentdb-* skills are installed (e.g., documentdb-driver, documentdb-connection). The builder must decide which skill(s) to consult.
- The starter prompt asks to use LangChain and an LLM but does not specify a model/provider; this is not contradicted by skills but is an unresolved gap that materially affects implementation details (credentials, embedding dims).

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python LangChain multi-agent pipeline with three agents: a data-fetch agent ..., a scoring agent ..., and an explainer agent" | - | - | Business problem (credit risk scoring) and what the sample demonstrates are explicit. |
| Workflow type | specified | no | "Python LangChain multi-agent pipeline" — three named agents | - | - | Multi-agent orchestration via LangChain is requested explicitly. |
| Language and runtime | ambiguous | no | "Python" | - | Use Python 3.10 (or 3.11) virtual environment; pip available as in skill.md. | Prompt specifies Python but gives no exact version. skill.md says `python` and `pip` resolve to a virtual environment but does not name a version. |
| Driver and version | ambiguous | no | - | documentdb-driver | Use the Python pymongo driver (pymongo >= 4.3, e.g., 4.4) and follow the documentdb-driver guidance (process-wide MongoClient singleton). | The installed `documentdb-driver` skill covers best practices (singleton client) but does not prescribe an exact driver version; the prompt does not name one. |
| Target service and tier | specified | no | "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable." Skill.md: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) is reachable..." | - | - | The run environment (skill.md) pins the existing cluster tier and server version to be used for verification. |
| Authentication and secrets | specified | no | "Its connection string is in the environment variable `DOCUMENTDB_URI`. Read it from the environment at run time. Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder, as the prompt asks." | - | - | skill.md explicitly mandates env-driven connection string and `.env.example` usage. |
| Data model | ambiguous | no | "retrieves applicant history from DocumentDB" | documentdb-data-modeling | Create a collection named `applicants` in database `sample_fintech_06` (skill.md) with documents containing fields such as `_id` (applicant_id), `income`, `debts`, `transactions` (array), `pastLoans` (array) and `schemaVersion`. Embed transaction entries rather than separate collections for this sample. | Prompt asks for applicant history but gives no explicit collection name or exact document shape; `documentdb-data-modeling` provides pattern guidance but not the concrete schema the sample's tests will rely on. |
| Sample data | missing | no | - | documentdb-local-deployment | Provide a small synthetic seed file (JSON) with one or a few applicant documents and a seed script that upserts them; the builder will create an idempotent seed script. | No source, size, or license is given. The local-deployment skill explains how to manage seed scripts, but no dataset is supplied. |
| Queries and indexes | missing | no | "query an applicant collection by applicant ID" | documentdb-indexing | Use a simple equality query on `_id` (which has the default index). No additional indexes required for the minimal sample; if embeddings/vector search are added, create a vector index sized to the chosen embedding model. | Prompt requires a lookup by applicant ID but does not list any explicit indexes or vector-index parameters. `documentdb-indexing` can guide index choices, but concrete index specs are not provided. |
| AI components | ambiguous | no | "scoring agent that applies risk rules and an LLM to produce a credit score" | - | Use LangChain with an OpenAI provider: model `gpt-3.5-turbo` (or `gpt-4o-mini` if available) for the scoring/refinement LLM; LLM API key read from OPENAI_API_KEY. Embeddings (if used) from `text-embedding-3-small`, with dims consistent with that model. | Prompt mandates calling an LLM via LangChain but does not name provider/model, nor embedding model/dimensions. The repo will need environment variables for model credentials. |
| App surface | ambiguous | no | The prompt asks for a Python LangChain multi-agent pipeline but does not specify CLI/API/UI. | - | Implement as a CLI runnable Python script (e.g., `python -m sample_fintech_06.run --applicant-id <id>`), with a small example `run_example.py` to exercise the pipeline end-to-end; include a programmatic function API to allow tests to call the pipeline. | No explicit route/command surface is defined. The builder will likely expose a main-runner and a function-level API for testing. |
| Provisioning and deployment | specified | no | "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable." Skill.md: "Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use." | documentdb-azure-deployment | - | The environment is pre-provisioned and the run policy forbids creating another cluster for this sample. The `documentdb-azure-deployment` skill exists for when provisioning is requested, but the sample should not provision by default. |
| Run and test instructions | missing | no | - | - | Builder will add a README with commands like `pip install -r requirements.txt`, `cp .env.example .env` and `python -m sample_fintech_06.run --applicant-id <id>` plus an example test runner `pytest tests/test_pipeline.py` that requires a live test applicant unless the test is mocked. | No explicit commands or expected outputs are in the prompt or skill.md (skill.md only gives environment hints). |
| Definition of done | missing | no | - | - | Accept if the pipeline runs end-to-end, the final score and explanation are written back to the applicant document in `sample_fintech_06`, and an example run/test demonstrates that behavior. | The prompt lists behaviors but does not include an explicit acceptance checklist; the reference requirements define more precise checks, many of which are not fully settled here. |
| Constraints and non-goals | missing | no | - | documentdb-security | Keep cost/scale low for the sample (use the existing cluster), avoid production HA changes, and do not include customer-managed keys or private endpoints for the sample's dev flow. | No explicit cost or compliance constraints are provided in the prompt; security skill can guide production recommendations but not the sample's constraints. |
| Repository conventions | ambiguous | no | "Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder" (skill.md) | documentdb-driver | Standard Python repo layout (`sample_fintech_06/`, `tests/`, `README.md`, `requirements.txt`, `.env.example`). Reuse a single MongoClient singleton per process as per `documentdb-driver`. | skill.md gives some conventions (.env.example, DB name) and `documentdb-driver` covers client reuse; broader conventions (requirements pinning, README sections) are not fully specified. |
