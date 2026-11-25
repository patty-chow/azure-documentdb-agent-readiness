# Documentation and tooling gaps: 03-core-banking-transaction-ledger

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Public pattern for Mongoose transactions + session usage

- **What was missing:** A concise, public example on Microsoft Learn that demonstrates the exact Mongoose pattern: startSession(), session.withTransaction(async callback), and the need to pass { session } to every Model operation inside the callback, plus correct endSession() placement and error-label handling for retries.
- **Where the agent looked:** documentdb quickstarts and installed documentdb-* skills; searches for 'Mongoose withTransaction example' returned tutorial text but no small copy-paste snippet that shows retry labels and session passing in one place.
- **Effect on this build:** The builder implemented the pattern correctly, but an agent searching for a single authoritative snippet might not have found it quickly (P02 was prior_knowledge_only).
- **Suggested fix (learn_doc):** A short 'Transactions with Mongoose on Azure DocumentDB' page: 1) sample code showing startSession()/withTransaction(), 2) explicit passing of { session } to every Model method, 3) example finally block with session.endSession(), 4) guidance on handling TransientTransactionError and UnknownTransactionCommitResult labels with a bounded retry/backoff loop.

## [high] Public snippet for transaction retry semantics

- **What was missing:** A small public example showing how to detect retryable transaction errors (TransientTransactionError, UnknownTransactionCommitResult) and perform bounded exponential-backoff retries in Node/Mongoose against Azure DocumentDB.
- **Where the agent looked:** documentdb-connection and quickstart docs; pieces exist but not a compact, copy-paste retry wrapper.
- **Effect on this build:** The sample does not implement a retry wrapper; having the snippet would make it straightforward to add and would reduce the risk of incorrect retry implementations.
- **Suggested fix (sample_or_quickstart):** A small retry helper in the Node quickstart showing error-label checks, backoff, and max-attempts, plus tests that simulate transient errors.

## [medium] Guidance on audit fields for ledger transactions

- **What was missing:** A concise public recommendation listing recommended immutable audit fields for ledger transactions (createdAt, createdBy, transactionRef, source, idempotency metadata) and an example schema.
- **Where the agent looked:** Microsoft Learn and the documentdb-data-modeling skill; searches for 'audit metadata ledger DocumentDB' returned no single authoritative page.
- **Effect on this build:** The sample included basic audit fields (transactionRef, createdAt, metadata) but omitted createdBy; an agent might decide different fields based on prior knowledge and produce inconsistent schemas.
- **Suggested fix (learn_doc):** A 'Ledger design patterns' subsection listing recommended immutable audit fields, example Mongoose schema, and notes on what to store in 'metadata' versus explicit fields.

## [medium] Explicit note: avoid TTL on transaction/ledger collections

- **What was missing:** No Microsoft Learn page explicitly states 'do not use TTL indexes for immutable ledger collections' (this is currently only in prior knowledge conversations).
- **Where the agent looked:** Microsoft Learn and skill docs, queries searching for TTL + ledger guidance.
- **Effect on this build:** No TTL index present in this sample. However, absent explicit guidance an agent might accidentally add a TTL index to a ledger.
- **Suggested fix (discoverability):** Add a small paragraph on the data-modeling page: 'Ledger collections should not use TTL indexes; store expirable data in separate collections.'

## [medium] Entra ID example for Mongoose drivers

- **What was missing:** A short Node snippet showing how to wire DefaultAzureCredential into the MongoDB driver's OIDC callback for a cluster that has MicrosoftEntraID auth enabled.
- **Where the agent looked:** documentdb security docs and quickstarts; docs mention it but lack a short copy-paste example.
- **Effect on this build:** Sample defaults to SCRAM and documents Entra ID as an option. A short example would help teams adopt Entra ID securely.
- **Suggested fix (learn_doc):** A 10-line code example demonstrating the driver's token refresh callback and using @azure/identity DefaultAzureCredential to obtain tokens for the MongoDB driver.

## [low] Mongoose driver/version pinning guidance

- **What was missing:** A single short note in the quickstart that recommends exact pinning semantics for sample repositories (for Node: pin exact version in package.json or commit package-lock.json and recommend `npm ci`).
- **Where the agent looked:** Quickstart and tutorial pages: they describe tested driver versions but do not prescribe sample repo pinning policy.
- **Effect on this build:** Builder initially attempted to pin an exact version, hit a registry mismatch, and used a caret range. This left the repo with a range rather than an explicit pinned package.json entry.
- **Suggested fix (discoverability):** Add a 'Pin dependencies' short guidance paragraph in the Node quickstart: preferred sample repository pattern (exact pins in package.json OR commit package-lock.json and instruct `npm ci`).

## [low] Agent-facing decision guidance for API surface

- **What was missing:** There is no explicit guidance in the skills/quickstarts telling an agent whether to prefer CLI-only samples vs REST+CLI in small demos.
- **Where the agent looked:** Skill docs and quickstarts; this decision is currently left to the builder as model_default.
- **Effect on this build:** Builder selected REST+CLI by default (reasonable), but agents may make inconsistent surface choices for similar samples.
- **Suggested fix (agent_kit_rule):** Add an agent-kit rule: 'For service quickstart samples that demonstrate read/write flows, prefer a minimal REST surface plus a CLI seed/demo script unless user explicitly asks for CLI-only.'

