# 1. Prompt review: 05-appointment-scheduling-assistant

**Verdict: sufficient_with_assumptions**

The starter prompt plus the supplied run-environment skill.md and the installed DocumentDB skills give a clear high-level goal: a Node.js LangChain conversational agent that reads/writes slot and appointment documents and does atomic reschedules. Enough is present to start implementation, but many concrete choices (driver version, exact schema, APIs/entrypoint, LLM model, seed data, tests, README and infra-as-code) are left to the builder and will be chosen by reasonable defaults unless the author clarifies them.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 7: Goal and scenario, Workflow type, Language and runtime, Target service and tier, Authentication and secrets, Provisioning and deployment, Constraints and non-goals |
| Covered by a skill | 1: Driver and version |
| Ambiguous: builder will guess | 3: Data model, Queries and indexes, App surface |
| Missing: builder will guess | 5: Sample data, AI components, Run and test instructions, Definition of done, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- A `.env.example` lists every setting with placeholder values — not specified in the prompt or covered by skills.
- The vector index dimensions match the embedding model's output — embedding model/dimensions are not specified, so any vector index choices are at risk.
- The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one — no guidance provided.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — sample data loader is not specified.
- /search returns a clear error for an empty query and when the embedding call fails — the sample doesn't request a search endpoint, so this behavior is unlikely to be implemented.
- Search results include the similarity score — not applicable unless semantic search is added; at risk if gallery expects this.
- Dependencies are pinned in `requirements.txt` — for a Node project, dependency pinning and a lockfile need explicit instruction; not specified.
- Unit tests run without a live cluster — no instruction to include tests with mocked DBs, so this may be missing.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type — the run environment provides a cluster and the prompt forbids provisioning; IaC is not included.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up — README contents are not specified and may be incomplete.
- The sample uses the name "Azure DocumentDB" throughout — not enforced by the prompt; implementer might use different product names unless instructed.

## Questions for the prompt author

- Which LLM/chat provider and model should the LangChain agent use (e.g., OpenAI gpt-4, gpt-4o-mini, or an on-prem model)? This changes env vars and example configuration.
- Should the sample expose an HTTP API endpoint (e.g., Express /chat) for conversational clients, provide a CLI demo, or include a small web UI? The choice affects included client/demo code and README instructions.
- Do you require a seed script, unit tests that run without a live cluster (mocks), and infrastructure-as-code for the DocumentDB cluster? The prompt's run environment supplies a cluster, but gallery standards often also want these artifacts.

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Node.js LangChain agent ... that query DocumentDB for provider availability slots, create appointment documents, and handle rescheduling by updating slot status atomically." | - | - | High-level business goal and scenario are explicit in the prompt. |
| Workflow type | specified | no | "Node.js LangChain agent with agent memory and tools" | - | - | Single-agent, LangChain, with tools and memory is explicitly requested. |
| Language and runtime | specified | no | "Node.js" and from skill.md: "Node.js 24 with npm and npx is available." | - | - | Runtime version is provided in the sample's run-environment (skill.md). |
| Driver and version | covered_by_skill | no | - | documentdb-driver | Use the official 'mongodb' npm package (latest stable major at build time, pinned in package.json), and follow the documentdb-driver guidance to create a singleton MongoClient. | The documentdb-driver skill gives the pattern (singleton client) and guidance but does not mandate an exact driver version; the builder will pick a reasonable recent driver and pin it. |
| Target service and tier | specified | no | "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) is reachable ..." (skill.md) | - | - | Run-environment explicitly names the live cluster and tier to use; do not provision another cluster. |
| Authentication and secrets | specified | no | "Its connection string is in the environment variable `DOCUMENTDB_URI`. Read it from the environment at run time. Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder, as the prompt asks." (skill.md) | - | - | Secrets location (env var) is specified; driver skill also recommends SCRAM-SHA-256 and TLS. |
| Data model | ambiguous | no | "Provider availability is modelled as slot documents ... booking creates an appointment document ..." | documentdb-data-modeling | Builder will create database 'sample_healthcare_05' (skill.md) with collections 'slots' and 'appointments'. slots documents: {_id, providerId, start: ISODate, end: ISODate, status: 'available'\|'booked'\|'cancelled', metadata: {...}}. appointments documents: {_id, patientId, slotId, status, createdAt, notes}. No explicit shard key (single-shard/small sample). | Conceptual model is stated, but exact field names, types, indexes and relationships are left to the implementer; documentdb-data-modeling gives guidance. |
| Sample data | missing | no | - | - | Builder will supply a small idempotent seed script (e.g., seed.js) that upserts a few providers, slots for multiple times, and one or two appointments for demo purposes. | No sample data source, size, license or idempotent loader is specified or covered by skills. documentdb-local-deployment discusses sample-data tooling but doesn't provide sample content. |
| Queries and indexes | ambiguous | no | "tools that query DocumentDB for provider availability slots" and atomic updates to slot status | documentdb-indexing | Builder will implement queries to find slots by providerId and time range and create an index such as { providerId: 1, start: 1, status: 1 } to support those queries. For atomic updates the code will use a conditional update or a transaction as described in the prompt. | The prompt requires the behavior but leaves index shapes and parameters to the implementer; documentdb-indexing provides guidance for picking indexes. |
| AI components | missing | no | "LangChain agent" is requested but no chat/embedding model or provider is specified. | - | Builder will wire LangChain to a commonly used chat model (e.g., OpenAI-compatible model via env var OPENAI_API_KEY) and document the required env vars in .env.example. No embeddings are strictly required for booking/rescheduling conversational context (use LangChain conversation memory), so embedding model selection can be omitted unless the builder adds semantic search. | Model provider and exact model/dimensions are not specified; that will change how the LangChain agent is configured. |
| App surface | ambiguous | no | "build a Node.js LangChain agent ... so a patient can say 'move it an hour later'" | - | Builder will expose a simple HTTP API (Express) with a /chat endpoint that accepts conversational messages and returns agent responses; developer CLI tooling (scripts) may be included for local interactive testing. The agent's tools will be implemented as LangChain Tools invoked by the agent during processing. | Prompt implies conversational interface but does not mandate an HTTP API vs CLI vs web UI; the choice affects example client and README. |
| Provisioning and deployment | specified | no | "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned... Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use." (skill.md) | - | No infra provisioning will be included; builder will operate against the existing cluster. | An infra-as-code artifact is not requested; the run-environment explicitly provides the live cluster to use. |
| Run and test instructions | missing | no | - | - | Builder will add a README with commands: npm install, npm run seed, npm start, and a demo interaction. Tests will be runnable via npm test with mocked DB clients. | No concrete run or test commands were provided. |
| Definition of done | missing | no | - | - | Builder will treat successful demo interactions that (1) query available slots, (2) create a booking and mark slot booked, (3) reschedule atomically to a new available slot when asked relative times, and (4) cancel an appointment returning slot to available as the criteria for done. | Prompt states desired behaviors but doesn't provide an acceptance checklist; the implementer will create one. |
| Constraints and non-goals | specified | no | "Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use." (skill.md) | - | - | The run environment limits writes to provisioning; otherwise cost/DR constraints are not enumerated. |
| Repository conventions | missing | no | - | - | Builder will follow common Node sample conventions: package.json, src/, scripts/ (seed.js, start script), .env.example, README.md and tests/ with mocks. Dependencies pinned in package.json; lockfile (package-lock.json) included. | No explicit repo layout, README section list or dependency-pinning rule is given. |
