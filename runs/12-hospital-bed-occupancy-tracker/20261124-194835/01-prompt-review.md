# 1. Prompt review: 12-hospital-bed-occupancy-tracker

**Verdict: sufficient_with_assumptions**

The starter prompt clearly states the core sample: a Node.js (Mongoose) service that writes bed-status documents, opens a change stream to detect status transitions, maintains a per-ward occupancy summary using atomic updates, and uses TTL to expire cleaning-state documents after a configurable timeout. The run environment (skill_md) supplies useful defaults (Node 24, a reachable DocumentDB cluster via DOCUMENTDB_URI). Several important implementation details are left to the builder (exact schema/field names, API surface, how alerts are surfaced, TTL implementation details, seed data and README). These will be filled by installed skills (documentdb-driver, documentdb-connection, documentdb-data-modeling, documentdb-indexing, etc.) or by reasonable defaults chosen by the builder.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 4: Goal and scenario, Language and runtime, Target service and tier, Provisioning and deployment |
| Covered by a skill | 1: Authentication and secrets |
| Ambiguous: builder will guess | 4: Driver and version, Data model, Queries and indexes, App surface |
| Missing: builder will guess | 6: Workflow type, Sample data, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 1: AI components |

## Reference requirements at risk

- TTL index implementation exactness: reference requires a TTL index on a Date field with expireAfterSeconds derived from a configurable cleaning timeout. The starter prompt mentions using TTL indexes and a configurable timeout but does not specify whether to use expireAfterSeconds vs a Date field; no installed skill enforces that exact approach.
- Only cleaning-state documents carry the Date value and it is removed when leaving cleaning: prompt asks for TTL expiring cleaning-state documents but doesn't specify the mechanics to set/remove the Date field when entering/leaving cleaning; that behavioral detail is not covered by a skill.
- Service surfaces capacity alerts in a way bed managers can see: the prompt does not state how alerts should be surfaced (alert document, emitted notification, webhook, UI).
- .env.example listing every setting with placeholders: prompt/skill_md say use env vars (DOCUMENTDB_URI) but do not require or provide an .env.example file covering all settings.
- Seed script that loads sample data and is idempotent: prompt does not request seed script; documentdb-local-deployment skill discusses sample-data management but does not automatically provide an idempotent seed script for this sample.
- Unit tests that run without a live cluster: prompt does not require test design or mocking strategy, and installed skills do not promise cluster-less unit tests.
- Dependencies pinned in a requirements file: prompt is for Node.js; reference expects pinned dependency manifesto (requirements.txt). The prompt doesn't mandate lockfile or exact pinning policy for Node (package-lock.json), so this is at risk.
- Infrastructure-as-code for the cluster: prompt and skill_md direct use of an existing cluster; reference asks for deployment code for the cluster which the prompt did not request.
- README coverage (what sample shows, prerequisites, setup, run, clean-up): prompt does not explicitly require a full README; builder may include one but it is not mandated.

## Questions for the prompt author

- Do you want an HTTP API (e.g., Express endpoints) for creating/updating bed status and retrieving ward summaries, or is a process-only demo (CLI + console) acceptable?
- Which field name should hold the TTL Date (e.g., cleaningExpiresAt) and should the implementation use a TTL index with expireAfterSeconds or set a date value to be used by a TTL index? (The requirement text expects a Date field whose value is what expires.)
- How should capacity and alerts be represented and surfaced? (e.g., store per-ward capacity in the summary doc and create an 'alert' collection, or emit notifications to stdout/webhook?)
- Do you require a seed script and README with explicit run/test instructions and an idempotent seeding process?
- Should the repository include infrastructure-as-code (Bicep/Terraform) to provision the cluster, or must the sample strictly use the existing cluster provided by DOCUMENTDB_URI?

## Contradictions and missing references

- Prompt says 'Using the DocumentDB skill' but there is no installed skill named exactly 'DocumentDB skill'. Multiple granular documentdb-* skills are installed (documentdb-driver, documentdb-connection, etc.), so the instruction is ambiguous about which skill to use.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | “build a Node.js Mongoose service that stores bed status documents in DocumentDB... maintain a live occupancy summary document per ward using atomic updates, and use TTL indexes to expire cleaning-state documents” | - | - | Business intent, user (bed/ward management) and what sample demonstrates are stated. |
| Workflow type | missing | no | - | - | Builder will treat this as a single-agent sample (one Node.js service process that both writes bed docs and consumes change streams). | Prompt does not state agent-orchestration model; not needed to start but would affect test harness and CI integration. |
| Language and runtime | specified | no | “Node.js Mongoose service” | - | Use Node.js 24 (the run environment in skill_md) and latest stable npm tooling. | skill_md explicitly states Node.js 24 is available on the developer machine. |
| Driver and version | ambiguous | no | “Mongoose” | documentdb-driver | Builder will pick a modern Mongoose 7.x compatible with Node 24 and MongoDB 7.0; MongoDB native driver usage will follow patterns from documentdb-driver (singleton client). | Prompt names Mongoose but does not pin a version; installed documentdb-driver covers MongoClient best practices but not Mongoose-specific version pinning. |
| Target service and tier | specified | no | Prompt: 'DocumentDB' and skill_md: 'vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol) reachable; connection string in DOCUMENTDB_URI.' | - | - | Run environment (skill_md) supplies the concrete target cluster and constraints (do not provision another cluster). |
| Authentication and secrets | covered_by_skill | no | - | documentdb-mcp-setup | Use environment variables for credentials; connection string read at runtime from DOCUMENTDB_URI (as described in skill_md). Do not write credentials into repo. | skill_md explicitly instructs DOCUMENTDB_URI in env; installed skills include documentdb-mcp-setup which can be used to inspect the cluster, and other skills assume env-driven config. |
| Data model | ambiguous | no | “bed status documents... each bed document belongs to a ward and carries a status that is one of occupied, available or cleaning” and “live occupancy summary document per ward” | documentdb-data-modeling | Builder will use bed documents with fields like { _id, bedId, wardId, status, lastStatusChangeAt, cleaningExpiresAt } and summary docs like { wardId, counts: { occupied: n, available: n, cleaning: n }, capacity: optional }. Field names and capacity storage will be chosen by the author. | High-level model is present, but exact field names, whether status is an enum type, and how capacity is stored are unspecified; documentdb-data-modeling provides guidance but not required field names. |
| Sample data | missing | no | - | documentdb-local-deployment | Builder will add a small idempotent seed script that creates a few wards and sample bed documents for demo (e.g., 2–3 wards with 5–10 beds each). | Prompt does not mention seed data or seed-script details. documentdb-local-deployment skill includes sample-data management practices but does not automatically provide the sample for this app. |
| Queries and indexes | ambiguous | no | “use TTL indexes to expire cleaning-state documents automatically after a configurable timeout” | documentdb-indexing | Builder will create: a TTL index on a Date field (e.g., cleaningExpiresAt) based on a configurable timeout; additional pragmatic indexes on wardId and status (or compound indexes) to support lookups and change-stream resume checks. | TTL requirement is present, but the prompt does not specify the Date field name vs expireAfterSeconds approach, nor other indexes; documentdb-indexing skill can guide index choices. |
| AI components | not_applicable | no | - | - | - | No embeddings or LLM components requested. |
| App surface | ambiguous | no | “build a Node.js Mongoose service ... Open a change stream ... maintain a live occupancy summary document per ward” | - | Builder will produce a small HTTP API (Express) with at least endpoints to: create/update bed status, get ward summary, and optionally list alerts. Alternatively, the sample might be implemented as a process-only demo with console output and a CLI script to create status changes. | Prompt doesn't mandate REST endpoints, CLI commands, or UI—builder must choose how the sample is exercised and demonstrated. |
| Provisioning and deployment | specified | no | skill_md: 'This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable... Do not provision another cluster unless run policy says Azure writes are allowed.' | - | No infrastructure provisioning code is required; use existing cluster reachable via DOCUMENTDB_URI. | Prompt and skill_md instruct using an existing cluster rather than provisioning new infra. |
| Run and test instructions | missing | no | - | - | Builder will include README with install (npm install), env setup (DOCUMENTDB_URI), seed script (npm run seed), run (npm start), and how to observe change-stream processing; exact commands are not specified and will be authored by builder. | skill_md gives environment constraints but not explicit run/test commands. |
| Definition of done | missing | no | - | - | Acceptance criteria will likely be: bed changes written, change stream processed, per-ward summary counts updated atomically, TTL deletes cleaning docs after timeout, and a visible alert created when capacity exceeded. | Prompt is functional but does not enumerate explicit acceptance tests or artifacts. |
| Constraints and non-goals | missing | no | - | documentdb-high-availability | Builder will treat sample as a small dev/demo app (no production SLA, no multi-region DR), will avoid provisioning expensive resources, and use env-based configuration for timeouts. | No cost or compliance constraints are specified; HA skills are available if needed. |
| Repository conventions | missing | no | - | - | Builder will follow typical Node sample conventions: package.json, src/, tests/, README.md, .env.example with placeholders, and .gitignore. But these are not mandated by prompt. | Prompt did not require .env.example, README content, or folder layout explicitly. |
