# Documentation and tooling gaps: 16-multi-touch-attribution-model

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Atomic version increments / safe versioning pattern

- **What was missing:** Public Azure DocumentDB guidance that prescribes a canonical approach for atomic per-customer version increments or recommended multi-version document patterns (findOneAndUpdate + $inc vs read-last-then-insert).
- **Where the agent looked:** documentdb skills (documentdb-data-modeling, documentdb-indexing) and general Microsoft Learn pages; search terms included 'azure documentdb versioned write atomic increment findOneAndUpdate'.
- **Effect on this build:** The builder implemented a read-last-then-insert pattern (app/src/attribution.py:41-56). Under concurrent runs this pattern can produce version collisions or race conditions. The lack of explicit service guidance led the builder to implement a simple but non-atomic approach.
- **Suggested fix (learn_doc):** A short guidance page titled 'Versioned documents and atomic increments' describing recommended patterns: (1) per-customer counter document + findOneAndUpdate($inc) to allocate monotonic version numbers, (2) using transactions when multi-document atomicity is required, (3) examples in Python showing find_one_and_update with upsert and $inc, and tradeoffs re: concurrency and cost.

## [high] Transaction & single-document preference

- **What was missing:** Clear provider-level guidance comparing multi-document transactions vs single-document atomic updates for versioned writes and their cost/latency trade-offs for Azure DocumentDB.
- **Where the agent looked:** documentdb skills and Microsoft Learn; queries like 'azure documentdb multi-document transactions cost latency' yielded no definitive guidance.
- **Effect on this build:** The builder chose a simple non-transactional pattern for versioning; without explicit guidance builders may either overuse transactions (cost/latency) or under-protect data correctness.
- **Suggested fix (learn_doc):** FAQ/short doc 'Transactions and versioned writes' with recommended default patterns for versioned documents, when to use transactions, and code examples for safe upserts and atomic increments in Python.

## [high] LangChain/OpenAI integration controls

- **What was missing:** No service-level guidance on LLM/embedding provider selection, credential handling, rate-limiting and per-user quota controls for a marketer-facing LangChain tool integrated with DocumentDB.
- **Where the agent looked:** documentdb skills, LangChain docs and Microsoft Learn; searches for 'azure documentdb openai integration best practices' had no service-specific prescriptions.
- **Effect on this build:** The builder used a model-default choice (OpenAI) and checks OPENAI_API_KEY presence but did not implement rate-limiting or quota enforcement. This is a recurring operational gap for samples that surface LLM access.
- **Suggested fix (agent_kit_rule):** An agent-kit rule or sample README section titled 'LLM integration safety' recommending: require API key via env, do not echo keys, provide example configuration for Azure OpenAI and OpenAI, and include a small rate-limiter middleware snippet and guidance to add auditing/quotas in production.

## [medium] WriteConcern/readConcern tuning guidance

- **What was missing:** No clear service-level recommendation for tuning writeConcern/readConcern (w/wtimeoutMS) for application durability vs latency for the vCore DocumentDB offering.
- **Where the agent looked:** documentdb skill materials and Microsoft Learn; searches for 'azure documentdb writeConcern w=majority guidance' returned no concise recommendation.
- **Effect on this build:** The sample uses the driver defaults; teams with stricter durability requirements may be unsure how to set w/wtimeoutMS appropriately for DocumentDB vCore clusters.
- **Suggested fix (discoverability):** A short note on the connection/driver guidance page that explains writeConcern/readConcern support, recommended defaults for analytics vs transactional workloads, and example MongoClient URIs showing how to set w/wtimeoutMS.

## [medium] Testing guidance: mongomock vs dedicated test DB

- **What was missing:** No explicit service recommendation advising whether to use mongomock for unit tests versus a dedicated test database (and how to get parity with DocumentDB-specific features).
- **Where the agent looked:** documentdb skills and general repo docs; search 'azure documentdb testing recommendations mongomock' returned no clear service-level instruction.
- **Effect on this build:** The builder used mongomock for unit tests and it passed locally. Without guidance other builders might use the wrong local emulator and miss service-specific features (e.g., cosmosSearch).
- **Suggested fix (learn_doc):** A 'Testing' page giving recommended strategies: unit tests with mongomock for pure-logic tests, integration tests against a versioned test cluster or the local DocumentDB Gateway image (docker) for feature parity, and sample pytest fixtures for both approaches.

## [medium] PII logging & redaction guidance

- **What was missing:** No service-specific best-practice doc that tells sample authors to avoid logging or to redact customer identifiers / PII for DocumentDB apps.
- **Where the agent looked:** documentdb security skills and Microsoft Learn; searches for 'azure documentdb logging PII redaction' returned no service-specific guidance.
- **Effect on this build:** Sample does not log PII, but there is no explicit note in README advising redaction; absence of guidance risks sample authors logging sensitive identifiers in other samples.
- **Suggested fix (learn_doc):** A short security note or checklist entry for sample authors: 'Avoid logging customer PII; if needed, hash or mask identifiers in logs; show code snippets demonstrating redaction before logging.'

## [medium] Seed should create indexes (discoverability)

- **What was missing:** The checklist expects seed scripts to both load data and ensure required indexes; the sample's seed is idempotent but doesn't create indexes (index creation occurs in run_attribution).
- **Where the agent looked:** Repo files and skills (indexing, local-deployment); no single canonical place in the repo clarifies the expected location for index creation.
- **Effect on this build:** Users who run only the seed may not have the necessary indexes before running queries; the builder placed index creation in run_attribution, which works, but the mismatch can surprise users.
- **Suggested fix (agent_kit_rule):** A small guidance note in the sample template: 'Seed scripts should be idempotent and ensure indexes exist (create_index) so a fresh environment is usable after seeding alone.' Provide a 2-line example to add to seed scripts.

