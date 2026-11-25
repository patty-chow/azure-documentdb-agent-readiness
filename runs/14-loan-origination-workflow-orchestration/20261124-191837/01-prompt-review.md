# 1. Prompt review: 14-loan-origination-workflow-orchestration

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines the core goal: a Python LangChain orchestration that models loan applications as Beanie state-machine documents in Azure DocumentDB, advances states via specialist agents, performs atomic state updates, and logs transitions. It omits several practical details the builder will have to assume (Python version, LLM/provider, exact collection/field names, CLI vs API surface, indexes, pinned deps, seed/idempotent data script, README), but installed skills + the run-environment skill_md cover most infra, connection, and driver guidance so a build can start.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Workflow type, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Covered by a skill | 2: Driver and version, Constraints and non-goals |
| Ambiguous: builder will guess | 3: Language and runtime, Data model, App surface |
| Missing: builder will guess | 6: Sample data, Queries and indexes, AI components, Run and test instructions, Definition of done, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- Implement three specialist agents named underwriting, compliance, and applicant communication — prompt mentions 'specialist agents' but does not name or require a separate 'applicant communication' agent; builder may omit or name differently.
- Transition log schema: prompt asks to log transitions with timestamp but doesn't require all fields (previous_state, new_state, agent name, decision/outcome, ISO8601 timestamp); builder may implement a minimal log missing one of those fields.
- .env.example listing every required setting with placeholder values — the prompt/skill_md require DOCUMENTDB_URI but do not mandate a complete .env.example; likely to be missing unless the builder adds it.
- Seed script that can be run twice without duplicating data — prompt doesn't require idempotent seed; builder may provide a simple one-shot seed only.
- Dependencies pinned in requirements.txt — prompt doesn't mention pinning; builder may leave loose version ranges.
- Unit tests that run without a live cluster — prompt asks for runnable against the live cluster; offline-capable unit tests are not mentioned and are likely not provided.
- Vector index dimensions and parameters matching the embedding model and README guidance — prompt doesn't mention embeddings or vector indexes, despite the run-environment cluster being vector-capable; builder may skip vector index config.
- Search behaviour requirements (e.g., /search error handling, similarity score in results) — the prompt is not a search sample and does not cover these endpoints, so these gallery requirements are at risk.
- Infrastructure-as-code for the cluster — the run-environment says a cluster already exists and the prompt doesn't request infra code; therefore the repo may lack deployment Bicep/Terraform even though gallery policy often expects infra examples.

## Questions for the prompt author

- Which Python version should the sample target (e.g., 3.10, 3.11)? This affects dependency pins and CI.
- Which LLM provider and model should the LangChain agents use in the example (e.g., OPENAI gpt-4o-mini, a local stub/dummy LLM for offline tests, or another provider)?
- Do you require a real LLM call in the runnable end-to-end example, or should the sample include deterministic stubbed agents so the example runs without API keys?

## Contradictions and missing references

- Prompt text: "Using the DocumentDB skill" — there is no installed skill literally named "DocumentDB skill". Several documentdb-* skills are installed, but the phrase could mislead the builder into looking for a single monolithic skill that doesn't exist. Treat as ambiguous instruction; the run-environment skill_md is the source of truth.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "models each loan application as a state machine document... The orchestrator advances the application through states (submitted, underwriting, compliance, approved/rejected) by delegating to specialist agents" | - | - | Business goal and demo scenario are explicit. |
| Workflow type | specified | no | "Python LangChain orchestration pipeline" and "specialist agents" | - | - | Multi-agent orchestration with LangChain is clearly requested. |
| Language and runtime | ambiguous | no | "Python LangChain" | - | Assume Python 3.11 (or latest stable 3.x available in the run environment). Use a virtualenv referenced by `python`/`pip` as in skill_md. | Python is named but version/runtime details are not; skill_md says `python`/`pip` exist in a virtualenv, so builder will pick a modern 3.x. |
| Driver and version | covered_by_skill | no | "Beanie" (implies Python async ODM and underlying Mongo driver) | documentdb-driver | Use a recent PyMongo/Beanie compatible stack: Beanie (v1.x or latest stable), and follow documentdb-driver guidance to create a single shared MongoClient/async client. | documentdb-driver provides singleton client and driver guidance; also the documentdb-connection skill further clarifies async client choices. |
| Target service and tier | specified | no | skill_md: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol...) is reachable... connection string in DOCUMENTDB_URI" | - | - | Run-environment (skill_md) explicitly provides the live cluster and tier to use. |
| Authentication and secrets | specified | no | skill_md: "Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time." | - | - | skill_md prescribes env var for the connection string; Azure secret handling guidance is available in documentdb-azure-deployment. |
| Data model | ambiguous | no | "models each loan application as a state machine document... logging every transition" | documentdb-data-modeling | Collection name `loan_applications` in database `sample_fintech_14`. Document fields: _id (ObjectId), current_state (enum string: submitted\|underwriting\|compliance\|approved\|rejected), applicant (dict/object with applicant fields), transitions (array of objects with previous_state, new_state, agent, decision, timestamp ISO8601). | Prompt defines the concept but not explicit field names, types, or collection naming — builder will pick sensible defaults and can consult documentdb-data-modeling for embedding vs referencing guidance. |
| Sample data | missing | no | - | - | Create a tiny idempotent seed script `seed.py` that inserts one sample loan application in state `submitted` and uses upsert semantics so it can be run multiple times without duplication. | Starter prompt doesn't specify sample-data content, size, or license; the run-environment requires verification against the live cluster but doesn't include a seed dataset. |
| Queries and indexes | missing | no | - | documentdb-indexing | Create an index on `current_state` and an index on transition timestamps (or rely on collection-level default). No vector or full-text index is required for the core orchestration sample. | Prompt requires atomic updates but does not specify index shapes; the documentdb-indexing skill can be used if the builder wants to add indexes. |
| AI components | missing | no | "LangChain" and "specialist agents" — but no LLM/embedding provider or model named | - | Use LangChain with a simple local/dummy LLM for deterministic demo (or optional OpenAI provider read from env OPENAI_API_KEY). If using a real provider, default to OpenAI Chat model (e.g., gpt-4o-mini or gpt-4o) and document the env var required. | Which LLM/embedding model and provider to use is not specified and will change integration and vector/index choices; builder must choose and document it. |
| App surface | ambiguous | no | "build a Python LangChain orchestration pipeline" — no explicit CLI/API/UI definition | - | Provide a CLI-style runnable script `run_orchestrator.py` demonstrating end-to-end execution; include `seed.py` and `examples/` showing invocation and expected logs. | The prompt asks for a pipeline and a runnable example in the reference requirements; builder will most likely deliver a script rather than a web UI. |
| Provisioning and deployment | specified | no | skill_md: "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable... use database sample_fintech_14... Do not provision another cluster unless the run policy says Azure writes are allowed" | documentdb-azure-deployment | - | The run environment explicitly forbids creating a new cluster for this sample; a deployment skill is installed but the sample should use the provided cluster. |
| Run and test instructions | missing | no | - | documentdb-local-deployment | Provide README and simple commands: `pip install -r requirements.txt`, set env vars (DOCUMENTDB_URI, optional OPENAI_API_KEY), `python seed.py`, then `python run_orchestrator.py`. Describe expected terminal state and how to inspect document in database. | The prompt asks for a runnable sample but does not give concrete commands; builder must add them. |
| Definition of done | missing | no | - | - | Accept when the included example: creates a `submitted` application, runs through underwriting and compliance agents, persists atomic state updates and transition logs, and ends in approved/rejected with all transitions visible in the DB. | No explicit acceptance criteria are in the prompt; the above is a reasonable testable definition. |
| Constraints and non-goals | covered_by_skill | no | skill_md: TLS and cluster usage constraints; documentdb-security provides TLS and networking guidance | documentdb-security | Follow security guidance: always use TLS, read connection string from env var, do not disable cert validation in production, and do not provision a new cluster for the sample. | Security and networking constraints (TLS, private endpoint) are covered by installed skills and skill_md. |
| Repository conventions | missing | no | - | documentdb-local-deployment | Use standard layout: `src/` or `app/` for code, `examples/`, `scripts/seed.py`, `run_orchestrator.py`, `requirements.txt`, `README.md`, `.env.example`, and `tests/` for unit tests. | Prompt does not prescribe repo structure; documentdb-local-deployment gives related local-development guidance but not exact repo conventions required by the gallery. |
