# 1. Prompt review: 01-anti-money-laundering-pattern-detector

**Verdict: sufficient_with_assumptions**

The starter prompt clearly states the goal (an AML pattern detector) and that it should be a single Python LangChain agent that uses a DocumentDB aggregation tool to follow references, apply typology rules via aggregation, and emit structured narratives. The provided run-environment skill.md supplies important operational constraints (live cluster, DB name, env var), but many engineering details are unspecified (Python version, MongoDB driver/version, exact data schema, AI model choices, app surface, seed data, indexes, tests, and infra-as-code) and will be filled by the implementer with reasonable defaults.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 2: Goal and scenario, Workflow type |
| Covered by a skill | 2: Target service and tier, Authentication and secrets |
| Ambiguous: builder will guess | 4: Language and runtime, Data model, Queries and indexes, Repository conventions |
| Missing: builder will guess | 8: Driver and version, Sample data, AI components, App surface, Provisioning and deployment, Run and test instructions, Definition of done, Constraints and non-goals |
| Not applicable | 0: - |

## Reference requirements at risk

- The aggregation tool runs through a MongoDB driver (e.g., PyMongo aggregate) — driver and version not specified by the prompt or skill.md, so implementer choice is likely but not guided.
- Connection string and model credentials come from environment variables — skill.md covers DOCUMENTDB_URI, but model credentials (LLM/embedding API keys) are not specified in prompt or skill.md.
- .env.example lists every setting with placeholders — skill.md advises using .env.example, but the prompt does not require or enumerate environment settings; may be omitted or incomplete.
- Vector index dimensions match the embedding model's output — embedding model/dimension are not specified, so matching may not be implemented correctly.
- Vector index parameters chosen for data size, and README explains how to change them — neither parameters nor README guidance are specified.
- One database client is created and reused across requests — prompt does not require this pattern; implementer may create per-call clients.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — no seed script is specified or provided.
- /search returns a clear error for an empty query and when the embedding call fails — no web search endpoint is requested by the prompt, and error behavior is unspecified.
- Search results include the similarity score — no search endpoint or return schema specified.
- Dependencies are pinned in requirements.txt — prompt does not require pinned requirements; implementer may or may not pin versions.
- Unit tests run without a live cluster — skill.md assumes a live cluster for verification; offline-capable unit tests are not specified.
- Infrastructure for the cluster provided as code (Azure DocumentDB resource type) — skill.md says a cluster already exists and forbids provisioning; infra-as-code is not provided.
- README covers what the sample shows, prerequisites, setup, run, and clean-up — README content is not specified by the starter prompt or skill.md and may be incomplete.

## Questions for the prompt author

- Do you want a CLI/demo script (local run) or an HTTP API/web UI for invoking the agent? This changes the app surface and the need for endpoints like /search.
- Which LLM and embedding provider/model should the sample use (e.g., OpenAI text-embedding-3-small with dim=1536 and gpt-4o-mini)? This determines vector index dimensions and model env vars.
- Which MongoDB driver and version do you want used (e.g., PyMongo 4.x)?

## Contradictions and missing references

- Prompt: "Using the DocumentDB skill" but installed_skills: "No agent skills are installed." — no DocumentDB skill is actually installed to satisfy that instruction.
- skill.md forbids provisioning another cluster while some gallery reference requirements ask for infra-as-code; the prompt does not reconcile this.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python LangChain agent ... that follows transaction document references ... applies known AML typology rules ... and flags suspicious patterns" | - | - | Business problem and what to demonstrate are explicit in the prompt. |
| Workflow type | specified | no | "a Python LangChain agent ... a DocumentDB aggregation tool" (single agent) | - | - | Prompt requests a single LangChain agent using a DocumentDB aggregation tool. |
| Language and runtime | ambiguous | no | "Python LangChain agent" | skill.md (Run environment) | Use Python 3.10 or 3.11 (latest stable 3.x available), create a venv and use 'python'/'pip' from that environment as skill.md implies. | Prompt names Python but gives no explicit version. skill.md only says 'python' and pip resolve to a virtual environment. |
| Driver and version | missing | no | "DocumentDB aggregation tool" and "aggregation pipelines" | skill.md (Run environment) mentions MongoDB 7.0 wire protocol but not a driver | Use PyMongo (pymongo>=4.0, e.g. pymongo==4.4) and call collection.aggregate(...) for pipelines. | Prompt implies MongoDB-compatible access but does not name a driver or version; skill.md gives wire protocol only. |
| Target service and tier | covered_by_skill | no | - | skill.md (Run environment) | - | skill.md explicitly describes a vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN/HNSW/IVF vector indexes) and requires using database sample_banking_01. |
| Authentication and secrets | covered_by_skill | no | - | skill.md (Run environment) | - | skill.md requires reading connection string from env var DOCUMENTDB_URI and disallows writing it to files/logs; this covers where the DB secret lives. |
| Data model | ambiguous | no | "Transactions are modelled as documents that reference other documents ... counterparty chains" | skill.md (Run environment) supplies the database name sample_banking_01 | Create collections named 'transactions' (documents with _id, amount, timestamp, from_account, to_account, related_tx_ids) and 'accounts' (account_id, holder_name); use ObjectId/_id for links; implement $graphLookup on transactions referencing counterparty ids. | Prompt requires documents that reference other documents but does not provide concrete field names, collections, or sample schema. skill.md only fixes the database name. |
| Sample data | missing | no | - | skill.md (Run environment) notes verifying by loading sample data but does not include the data | Author will provide a small synthetic dataset seeded by a script (e.g., tens to low hundreds of transactions) demonstrating circular transfers, structuring, and rapid pass-through patterns; seed script will be idempotent (upsert or check existence). | No sample data source, size, license, or loader described. |
| Queries and indexes | ambiguous | no | "aggregation" and "follows transaction document references ... with $graphLookup or chained $lookup" | skill.md (Run environment) documents available vector index types on the cluster but does not prescribe index names/fields/parameters | Create indexes on reference fields used by lookups (e.g., index on transactions.from_account and transactions.to_account), create a vector index sized to the chosen embedding dims, and include reasonable parameters for a small sample (e.g., HNSW with default efConstruction/efSearch). | Aggregation strategy is specified, but precise indexes, vector index dimensions and parameters are not. |
| AI components | missing | no | "Python LangChain agent" (implies LLM/embeddings) but no models/providers/dimensions named | skill.md (Run environment) does not provide model credentials or model choices | Use OpenAI for embeddings and chat: e.g., text-embedding-3-small (dimension 1536) for embeddings and gpt-4o-mini or gpt-4o for narrative generation; read OpenAI API key from environment (e.g., OPENAI_API_KEY). | Prompt requires LangChain agent but does not state embedding or LLM models, providers, or embedding dimensions; these choices affect vector index sizing. |
| App surface | missing | no | "agent" but no mention of CLI, API, or UI or routes | skill.md (Run environment) expects verification scripts but does not prescribe an app surface | Provide a CLI/demo script (e.g., run_detector.py) that invokes the agent to analyze either seeded sample data or a provided transaction ID and prints JSON narratives. No HTTP server unless requested later. | Prompt does not require a web API or CLI; implementer must pick one. This choice affects endpoints (/search) in the reference requirements. |
| Provisioning and deployment | missing | no | - | skill.md (Run environment) explicitly says a cluster is already provisioned and 'Do not provision another cluster' unless allowed | Do not include infra-as-code that creates the production cluster; provide only local setup scripts and instructions for using the existing cluster. If infra is required, it will be omitted unless explicitly permitted. | Prompt and skill.md assume a pre-existing cluster; infrastructure-as-code for the cluster is not provided or requested. |
| Run and test instructions | missing | no | "Verify against the live cluster" appears in skill.md but no concrete commands or tests are listed in the prompt | skill.md (Run environment) requires recording what was executed in the build report | Include README steps: pip install -r requirements.txt, cp .env.example .env (fill DOCUMENTDB_URI and API keys), python seed_data.py, python run_detector.py; tests will be lightweight/integration and optional. | Concrete commands and expected success outputs are not specified. |
| Definition of done | missing | no | - | skill.md (Run environment) only says to verify and record what was executed | Definition of done will be: agent runs against seeded data, aggregation tool returns flagged chains, and the agent emits a structured JSON/Pydantic narrative per flagged chain; scripts run without leaking secrets. | No explicit acceptance criteria provided. |
| Constraints and non-goals | missing | no | - | skill.md (Run environment) provides operational constraints about using the provided cluster and secrets handling | Assume cost-sensitive constraints: keep sample data small, do not provision cloud resources, and avoid storing secrets in repo. No production hardening required. | No explicit cost or non-goal statements in the starter prompt. |
| Repository conventions | ambiguous | no | - | skill.md (Run environment) instructs to use a config file or .env.example and not to write the connection string into files | Follow common gallery conventions: create README.md, requirements.txt (pinned), .env.example, src/ package, tests/, seed_data.py, and a top-level run_detector.py CLI. | Some conventions are implied by skill.md (e.g., .env.example), but full repo layout and naming rules are not specified. |
