# Documentation and tooling gaps: 18-returns-refund-workflow-orchestration

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] LangChain import compatibility & examples

- **What was missing:** No public guidance in the sample or README about how to set up a Node project so the 'langchain' package subpaths resolve (ESM vs CommonJS import guidance) and a tested example showing LangChain agent wiring in CommonJS or ESM for Node 24.
- **Where the agent looked:** events.jsonl (langchain import error), package.json in repo, installed skill docs; Microsoft docs search not applicable.
- **Effect on this build:** The builder attempted to import LangChain subpaths and hit ERR_PACKAGE_PATH_NOT_EXPORTED, so they replaced LangChain usage with direct OpenAI client calls. As a result the sample fulfills orchestration semantics but does not demonstrate LangChain classes; this could confuse gallery reviewers expecting LangChain code.
- **Suggested fix (discoverability):** Add a short README section and a troubleshooting note: (1) which langchain versions are compatible with CommonJS/Node 24, (2) example package.json + "type": "module" ESM conversion steps, and (3) a minimal ESM LangChain agent example that the sample maintainers can opt into.

## [high] Which Azure resource to deploy (mongoClusters)

- **What was missing:** Clear, discoverable guidance that the correct resource type for provisioning Azure DocumentDB clusters is Microsoft.DocumentDB/mongoClusters (API 2025-09-01) and that az cosmosdb create is not the correct shortcut for this resource.
- **Where the agent looked:** documentdb-azure-deployment skill, Microsoft Learn; readiness_findings (Q01–Q03) show confusion between databaseAccounts and mongoClusters.
- **Effect on this build:** If the sample included IaC, an incorrect resource type would produce broken templates and confuse users. The builder avoided provisioning due to policy, but consumers may copy incorrect patterns if not corrected.
- **Suggested fix (learn_doc):** A short 'Deploying the cluster' doc explaining the correct resource types (Microsoft.DocumentDB/mongoClusters), example Bicep snippet, and an az deployment/az resource create example. Also note the difference to older databaseAccounts examples.

## [high] Agent output schemas

- **What was missing:** There was no canonical, public schema for the three agents' outputs (policyAgent, refundAgent, commsAgent) that an agent or another builder could rely on.
- **Where the agent looked:** no installed skill provided exact agent output schema; readiness_findings noted this as a gap.
- **Effect on this build:** The builder defined ad-hoc shapes (policyResult.eligible + reasons, refundResult.amount + breakdown, commsResult.subject/body). Because the starter prompt did not require specific JSON schemas, these were chosen by the builder — different builders might choose incompatible shapes.
- **Suggested fix (agent_kit_rule):** Ship a short 'Returns orchestration' agent-kit rule that defines canonical JSON schemas for the three agents (policy: { eligible:boolean, eligibilityReason?:string, reasons?:string[] }, refund: { amount:number, breakdown?:[{reason:string,amount:number}] }, comms: { customerId?:string, eligibility:boolean, refundAmount?:number, eligibilityReason?:string, messageBody:string, notificationChannel?:string }). Include example prompts and expected JSON output in skill docs.

## [high] Seed script safety and database target

- **What was missing:** Seed script does not explicitly verify it's operating on the sample_retail_18 database or require confirmation before destructive actions.
- **Where the agent looked:** app/scripts/seed.js and README; documentdb tutorial guidance (P23).
- **Effect on this build:** If a user runs the seed against the wrong connection string, it may modify unintended databases. The builder relied on the supplied run environment and did not add a safety check.
- **Suggested fix (learn_doc):** Add a short note and a code snippet to seed.js that checks the connected DB name against process.env.SAMPLE_DB_NAME (default 'sample_retail_18') and requires a --confirm flag to proceed. Include this safety pattern in seeding quickstarts.

## [high] Tests that run offline (mocked DocumentDB)

- **What was missing:** No unit tests that run without a live cluster; the README documents demo and live verification but not how to run automated tests offline.
- **Where the agent looked:** repo, README, scripts; no test files found.
- **Effect on this build:** CI and contributors cannot validate logic (especially orchestration branching and error handling) without a live cluster, which reduces confidence and slows review.
- **Suggested fix (sample_or_quickstart):** Add a test directory with a couple Jest tests that stub Mongoose models (or use an in-memory mock) to exercise approved and rejected return paths. Document how to run tests locally/CI without DOCUMENTDB_URI.

## [medium] Connection-string example and retryWrites guidance

- **What was missing:** A canonical example connection string shape for Azure DocumentDB (mongodb+srv host form) and explicit note in .env.example/README explaining retryWrites=false and why it should be set.
- **Where the agent looked:** learn.microsoft.com quickstarts and documentdb-azure-deployment skill; readiness_findings Q04 shows prior confusion.
- **Effect on this build:** The sample .env.example already includes a legacy-style host:port example on 10260 and retryWrites=false, but readers could still be confused between legacy Cosmos host/port examples and the newer mongodb+srv form.
- **Suggested fix (discoverability):** Update .env.example and README to show both the typical mongodb+srv example returned by the portal and the legacy port form (with a note to prefer the portal-provided string). Explain why retryWrites=false is recommended here.

## [medium] Retry/backoff & circuit-breaker guidance for agent calls

- **What was missing:** Guidance or a small helper that shows how to wrap LLM calls with timeouts, retries with exponential backoff and a circuit-breaker, and how to fall back to mock mode on repeated failures.
- **Where the agent looked:** documentdb-connection & documentdb-monitoring skills; no small code sample for wrapping LLM calls.
- **Effect on this build:** callOpenAI currently has no timeout or circuit-breaker; a long-running LLM call could block orchestration or cause flaky demos.
- **Suggested fix (agent_kit_rule):** Provide a small helper module (e.g., tools/llm-wrapper.js) implementing timeout + retry + circuit-breaker with a documented interface and an example for the sample.

## [medium] Decision provenance for model-default choices

- **What was missing:** Some decisions (e.g., selecting LangChain by default) have reason_source 'model_default'. These should reference a public guidance page or note so future builders know the rationale and risks.
- **Where the agent looked:** decisions.jsonl and readiness_findings.
- **Effect on this build:** Model-default choices were acceptable, but the team should prefer explicit, discoverable guidance for gallery samples so agent-built samples are consistent.
- **Suggested fix (discoverability):** Add a short 'default patterns' page in the agent kit that lists preferred defaults (LLM provider fallback policy, mocking strategy, example models) and links to the skills that justify them.

## [medium] Projection / query best-practice example

- **What was missing:** An explicit sample snippet for using projections (select only fields needed by agents) in an orchestration scenario.
- **Where the agent looked:** documentdb-indexing skill and docs; no small snippet tailored to switching from full document to projected document for agents.
- **Effect on this build:** The builder fetched full order documents; agents received full payloads rather than minimal projected data.
- **Suggested fix (sample_or_quickstart):** Add a one-paragraph note and code snippet to the driver skill or sample README showing Order.findOne({orderId}, {items:1,total:1}) usage and explain security/perf reasons.

