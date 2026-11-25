# Documentation and tooling gaps: 10-multi-tenant-storefront-saas

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Public example Mongoose tenant-safety plugin

- **What was missing:** A public Azure DocumentDB page or quickstart that documents and publishes a canonical Mongoose 'tenant safety' plugin pattern (inject tenantId into queries and reject tenant-less operations).
- **Where the agent looked:** Loaded documentdb skills, searched Azure docs and the agent-kit; found the pattern as prior knowledge only (discovered_practices K01, K19 are prior_knowledge_only).
- **Effect on this build:** The builder nevertheless implemented a plugin from prior knowledge; however, agents that lacked this memory might not invent the defensively-safe pattern and could produce samples that allow cross-tenant queries.
- **Suggested fix (learn_doc):** A short docs page titled 'Enforcing tenant isolation in Mongoose' with: (1) rationale; (2) canonical plugin code snippet that rejects query/update/delete middleware lacking tenantId; (3) how to apply the plugin to schemas and integrate with repository constructors; (4) a small test pattern that asserts a query without tenantId throws. Include copy-paste examples and a link from the Mongoose quickstart.

## [high] Guidance and example for seeding idempotently (orders)

- **What was missing:** While the local-deployment skill documents idempotent seeds in general, a concrete sample pattern for order-like resources (unique on tenantId+orderNumber) was not in the sample docs. The builder partially implemented idempotent upserts for products/inventory but left Order.create non-idempotent.
- **Where the agent looked:** documentdb-local-deployment skill and index/seed docs; repository code inspection.
- **Effect on this build:** Seed is only partially idempotent: running the seed repeatedly creates duplicate Order documents.
- **Suggested fix (sample_or_quickstart):** Add a short subsection to the seed quickstart: 'Making seeds idempotent' with examples for using findOneAndUpdate/upsert keyed by tenantId+natural-key (e.g., orderNumber), and recommend using bulkWrite for larger datasets. Provide the exact code snippet to replace Order.create with a findOneAndUpdate upsert.

## [medium] Recommendation for retry/backoff patterns for Node/Mongoose clients

- **What was missing:** The agent-kit lists retry guidance, but there is no small, copy-paste Node/Mongoose retry helper that shows how to wrap repository operations and handle 429/Retry-After using exponential backoff.
- **Where the agent looked:** documentdb-connection and documentdb-driver skills; quickstarts and sample code.
- **Effect on this build:** The builder did not implement retry/backoff logic; absent a concise example, sample authors may omit retries and be vulnerable to transient throttling or transient network errors.
- **Suggested fix (sample_or_quickstart):** Add a one-page snippet 'Handling 429 and transient errors' for Node: include a small retry wrapper (Promise-based) that checks MongoError codes and 429, honors Retry-After when present, and uses exponential backoff with jitter. Show how to integrate it at the repository layer.

## [medium] Pinning recommended driver versions in quickstart

- **What was missing:** A clear single-line recommendation in the Mongoose quickstart that states the tested/pinned driver version to use with the shown code (e.g., 'Use Mongoose 9.12.1 with MongoDB driver X for these docs').
- **Where the agent looked:** Mongoose quickstart and Azure DocumentDB Node.js examples; readiness notes showed mixed signals about suggested version.
- **Effect on this build:** The builder chose Mongoose ^7.4.0 by model_default (decision D003). This diverges from newer quickstart examples and may cause subtle incompatibilities or confusion for readers about which driver version was tested with the sample.
- **Suggested fix (discoverability):** Add a 'Tested driver versions' box to the Node/Mongoose quickstart that lists the exact Mongoose and underlying mongodb-driver versions used to validate examples (and the Node.js engine version).

## [medium] Canonical guidance for local test runs (DocumentDB Gateway image usage)

- **What was missing:** A short, highlighted snippet in the Mongoose quickstart showing the exact docker-compose or docker run invocation for the DocumentDB Gateway image (port 10260, TLS details) and how to run tests against it.
- **Where the agent looked:** documentdb-local-deployment skill; quickstarts; sample README.
- **Effect on this build:** tests/isolation.test.js run against the live cluster. Authors wanting offline-only CI or reproducible developer runs need a documented, one-line recipe to run tests locally without a live cluster.
- **Suggested fix (agent_kit_rule):** Add a minimal docker-compose snippet in the quickstart and a 'Testing without cloud' section that shows how to set DOCUMENTDB_URI to point to the Gateway image, supply the certificate, and run npm test. Include an example env file for local runs.

## [low] List of repo-supplied environment variables

- **What was missing:** The sample .env.example only lists DOCUMENTDB_URI. A consistent convention and a short manifest of env variables (PORT, NODE_ENV, LOG_LEVEL) would help agents and builders produce full .env.example files.
- **Where the agent looked:** repo .env.example and README; no centralized guidance found for sample env conventions.
- **Effect on this build:** The .env.example omitted PORT and other knobs; readers may be uncertain which env vars are required or optional.
- **Suggested fix (agent_kit_rule):** A one-paragraph rule for sample starters: include DOCUMENTDB_URI plus typical runtime env placeholders (PORT, NODE_ENV, LOG_LEVEL) in .env.example. Provide a minimal template to copy into projects.

