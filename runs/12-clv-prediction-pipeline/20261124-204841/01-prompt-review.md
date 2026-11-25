# 1. Prompt review: 12-clv-prediction-pipeline

**Verdict: sufficient_with_assumptions**

The starter prompt plus the supplied skill.md give a clear, actionable goal (Python LangChain agent that computes per-customer frequency, AOV, tenure, classifies CLV, and writes results back to customer documents). Several implementation details (Python version, driver version, exact schema/collection names, model/provider selection, sample data and seed scripts, indexes, run/test instructions, README and infra-as-code) are not specified and will be chosen by the builder unless the author clarifies them. No single blocking unknown prevents a sensible start.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Workflow type, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Covered by a skill | 0: - |
| Ambiguous: builder will guess | 6: Language and runtime, Data model, Queries and indexes, Definition of done, Constraints and non-goals, Repository conventions |
| Missing: builder will guess | 5: Driver and version, Sample data, AI components, App surface, Run and test instructions |
| Not applicable | 0: - |

## Reference requirements at risk

- A `.env.example` that lists every setting with placeholder values — prompt/skills do not mandate creation of a complete .env.example covering LLM credentials; skill.md hints at .env.example for DOCUMENTDB_URI but not for model creds.
- Vector index dimensions matching the embedding model's output — not specified; if vectors are used, dims must be aligned with the chosen embedding model.
- Vector index parameters chosen for the sample's data size and README guidance for changing them — not addressed by prompt.
- A seed script that loads sample data and creates the index and is safe to run twice without duplicating data — no seed script is requested in the prompt.
- /search returning a clear error for an empty query and when the embedding call fails — prompt does not require a search endpoint; robustness behaviors are not specified.
- Search results including similarity score — search is not in the prompt; no guarantee this will be implemented.
- Dependencies pinned in `requirements.txt` — prompt does not require pinned dependencies; builder may or may not pin versions.
- Unit tests that run without a live cluster — not specified; skill.md expects verification against live cluster but not offline unit tests.
- Infrastructure-as-code for the cluster using Azure DocumentDB resource type — prompt and skill.md explicitly say to use the existing cluster and not to provision new resources, so infra-as-code is not provided.
- README covering what the sample shows, prerequisites, setup, run, and clean-up — prompt asks to build the sample but does not explicitly require a full README with these sections (skill.md asks to record what was executed but not to include a complete README).

## Questions for the prompt author

- Which LLM provider and model should the sample use for the classification/rationale step (e.g., OpenAI GPT-4, Azure OpenAI, local model)?
- Which exact Python version should the sample target (e.g., 3.10 or 3.11)?
- Do you want a specific collection name and a concrete customer document schema (fields for orders, amounts, dates) to be used, or should the builder design a reasonable schema?
- Should the sample include a seed script with synthetic/sample data and an idempotency requirement, or will you supply sample data?
- Is a CLI-only demonstration acceptable, or do you require a web API or UI (endpoint /search was listed in the gallery checklist but not in the prompt)?

## Contradictions and missing references

- Prompt says "Using the DocumentDB skill" (singular). There is no single installed skill named exactly "DocumentDB skill"; instead multiple documentdb-* skills are available. Builder will need to decide which installed documentdb skill(s) to invoke (e.g., documentdb-natural-language-querying, documentdb-driver).

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "compute historical purchase frequency, average order value, and tenure per customer"; "estimate CLV tier (low, medium, high, VIP), generate a rationale, and write the CLV score and tier back to the customer profile document in DocumentDB." | - | - | Business problem and what the sample demonstrates are clearly stated. |
| Workflow type | specified | no | "build a Python LangChain agent with a DocumentDB aggregation tool" | - | - | Single-agent LangChain workflow is explicit. |
| Language and runtime | ambiguous | no | "Python LangChain agent"; skill.md: "python and pip resolve to a virtual environment created for this run" | - | Builder will target a modern Python 3.x (likely 3.10 or 3.11) and use a venv; tests and examples will assume Python >=3.10. | Prompt and skill.md name Python but do not fix a specific version. |
| Driver and version | missing | no | - | documentdb-driver | Use PyMongo (pymongo>=4.0, pinned in requirements.txt) and the official MongoDB URI from DOCUMENTDB_URI; follow documentdb-driver guidance for singleton MongoClient. | No specific MongoDB driver or version is specified in prompt or skill.md; documentdb-driver gives patterns but not exact package/version. |
| Target service and tier | specified | no | skill.md: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) is reachable..." and "Use the database named `sample_customer_360_12`" | - | - | Run environment explicitly names the live cluster and DB to use. |
| Authentication and secrets | specified | no | skill.md: "connection string is in the environment variable `DOCUMENTDB_URI`. Read it from the environment at run time. Never write its value into any file... use a config file or `.env.example` with a placeholder, as the prompt asks." | - | - | DocumentDB connection secret location is defined. Model/LLM credentials are not specified (see AI components). |
| Data model | ambiguous | no | "write the CLV score and tier back to the customer profile document in DocumentDB" | documentdb-data-modeling | Builder will create a `customers` collection (or `customer_profiles`) with documents containing _id, purchases (array of order docs with date and amount) and add fields like `clv_score` and `clv_tier`. Schema will be denormalized for read-heavy analytics. | The prompt requires updating customer profile docs but gives no collection name or document shape; documentdb-data-modeling can guide best practices but won't fix the concrete schema. |
| Sample data | missing | no | - | documentdb-local-deployment | Builder will provide a small synthetic seed script (e.g., tens to hundreds of customers with purchase histories) and include it in repo; seed script will be idempotent (upsert by customer id). | No sample dataset source, size, license, or loader is specified. |
| Queries and indexes | ambiguous | no | "DocumentDB aggregation tool that computes historical purchase frequency, average order value, and tenure per customer." | documentdb-natural-language-querying | Aggregation pipeline will use $unwind/$group/$avg/$count and $min/$max on order dates to compute tenure; builder will add sensible indexes (e.g., index on customer_id and on purchases.date or on top-level purchase date fields) but exact index shapes are not specified. | The pipeline requirement is explicit; index choices and exact query shapes are not fully specified. documentdb-natural-language-querying can generate the aggregation pipeline. |
| AI components | missing | no | "Use prompt engineering to instruct the LLM to estimate CLV tier..." | - | Builder will pick a hosted LLM provider (commonly OpenAI) and use a chat/completion model (e.g., gpt-4 or gpt-4o) for the classification/rationale step; embeddings are likely not required unless augmenting with semantic data. Model credentials will be loaded from env (e.g., OPENAI_API_KEY). | No provider, model name, or how/where to call the model is specified; this affects reproducibility and .env.example contents. |
| App surface | missing | no | - | - | Builder will implement a simple CLI runner and/or minimal script (e.g., python run_clv.py --customer-id <id>) demonstrating the agent. Optionally include an example Flask/FastAPI endpoint for running the agent, but prompt doesn't require a web UI. | Prompt doesn't specify CLI vs API vs web UI; a minimal CLI demonstration is the least-effort sensible default. |
| Provisioning and deployment | specified | no | skill.md: "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable... Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use." | - | - | Use of an existing live cluster is explicit; no infra-as-code requirement is in the prompt. |
| Run and test instructions | missing | no | - | - | Builder will add a README with commands: pip install -r requirements.txt, export DOCUMENTDB_URI=..., export OPENAI_API_KEY=..., python -m venv .venv, python run_clv.py --sample or --customer-id; include example output demonstrating DB updates. | skill.md asks to verify against live cluster but doesn't provide exact run/test commands or CI/test harness. |
| Definition of done | ambiguous | no | "write the CLV score and tier back to the customer profile document in DocumentDB." | - | Builder will treat 'done' as: aggregation tool computes metrics correctly, agent calls LLM and receives a CLV score+tier+rationale, and the code updates a sample customer's document; README and example run prove this. Tests may assert update occurred. | No precise acceptance criteria or numeric thresholds provided. |
| Constraints and non-goals | ambiguous | no | skill.md: "Never write its [DOCUMENTDB_URI] value into any file, log, README or test fixture... do not provision another cluster unless..." | documentdb-security | Builder will avoid leaking secrets, not provision new cloud resources, and not require paid infra beyond the existing cluster; other constraints (cost caps, data privacy, performance SLAs) are not specified. | Some operational constraints are present in skill.md, but broader non-goals are not stated. |
| Repository conventions | ambiguous | no | skill.md: "use a config file or `.env.example` with a placeholder, as the prompt asks." | - | Builder will follow common conventions: top-level README, src/ or package, requirements.txt with pinned deps, .env.example, tests/ folder, and a simple MIT/Apache license header. Use 'Azure DocumentDB' in docs as requested by gallery requirements. | Prompt and skill.md hint at .env.example but do not define full repo layout or naming conventions. |
