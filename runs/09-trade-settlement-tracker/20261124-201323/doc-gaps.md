# Documentation and tooling gaps: 09-trade-settlement-tracker

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Driver version pinning and tested versions

- **What was missing:** A single, prominent statement in the quickstart/agent-kit that recommends which Mongoose and underlying MongoDB Node driver versions were tested with Azure DocumentDB (vCore) for Node.js 24 and which exact versions to pin for samples.
- **Where the agent looked:** Searched Microsoft Learn quickstarts and tutorials (learn.microsoft.com quickstart-nodejs-mongoose and tutorial-nodejs-mongoose). The docs include tested-driver info but it is not surfaced as a short rule the agent would automatically apply when selecting a version.
- **Effect on this build:** The builder chose a Mongoose 7.x version by model-default and then tried to pick an available 7.x version. The transient npm registry errors compounded the choice. The sample ends up using a caret range (^7.9.0) rather than a recommended pinned Mongoose 9.x release; this blocked reproducible installs and verification in this environment.
- **Suggested fix (discoverability):** Add a one-paragraph 'Tested driver versions' section to the Node.js quickstarts and to the documentdb-driver skill README: list exact Mongoose and MongoDB driver versions tested with Node 24 (e.g., Mongoose 9.12.1 / mongodb driver 7.8.0) and a recommended package.json snippet to pin them. Example snippet and a note: 'Commit package-lock.json to the sample repo.'

## [high] RetryWrites behavior is different from prior knowledge

- **What was missing:** A prominent note that Azure DocumentDB samples commonly set retryWrites=false and recommend application-level idempotency rather than assuming driver-managed retryWrites=true.
- **Where the agent looked:** Quickstart and tutorial pages (learn.microsoft.com quickstart-nodejs-mongoose and tutorial-nodejs-mongoose) and documentdb guidance; the discovery showed prior belief about enabling retryWrites was contradicted by Azure DocumentDB guidance.
- **Effect on this build:** A model or builder following general MongoDB advice (enable retryWrites) could choose a configuration that contradicts Azure DocumentDB guidance and risk unexpected duplicate non-idempotent writes. The sample explicitly set retryWrites:false in connection options (app/src/db.js line 23), which is correct for Azure DocumentDB, but the guidance must be prominent to prevent agent/model confusion.
- **Suggested fix (naming_or_disambiguation):** Add a short, high-visibility note to the top of the Node.js quickstart and to the documentdb-driver skill: 'Note: Azure DocumentDB samples set retryWrites=false. Design idempotent application retries instead of enabling driver retryWrites for non-idempotent operations.' Include a brief example showing how to implement a persisted deduplication key for idempotent writes.

## [high] Resume-token persistence for change streams (guidance prominence)

- **What was missing:** While change-stream guidance exists, an agent authoring samples may not treat resume-token persistence as required for production change-stream code. Make checkpointing a required line item in the change-stream sample template.
- **Where the agent looked:** learn.microsoft.com change streams doc and documentdb change-stream skills; the guidance exists but the sample's watcher currently only logs a TODO.
- **Effect on this build:** The sample's watcher was implemented but lacked resume-token persistence and robust restart behavior; this was noted in the builder's open_issues and is visible in code (no checkpointing).
- **Suggested fix (agent_kit_rule):** Add a rule to the change-stream sample template: 'Always persist resume tokens after processing each batch. Provide a sample control collection schema and sample code showing resumeAfter on startup.' Include a short code snippet and a test that simulates restart and resume.

## [high] Tests run without cluster (example/mocking guidance)

- **What was missing:** A concrete sample in the agent kit showing how to write unit tests for Mongoose models and request handlers that do not need a live cluster (e.g., using mongodb-memory-server or mocking Mongoose).
- **Where the agent looked:** documentdb-local-deployment skill and repository; no explicit sample tests or test harness present in this repo.
- **Effect on this build:** No tests were added (package.json test is a stub). Agents/builders may omit tests or add tests that require a live cluster. Lack of test harness reduces confidence in publishable sample quality.
- **Suggested fix (sample_or_quickstart):** Ship a minimal test harness example in the agent kit: a test/ directory with a simple set of unit tests that run against mongodb-memory-server (or mocked Mongoose), sample jest/mocha config, and a README section 'How to run tests locally without a cluster.'

## [high] Infra-as-code ambiguity (mongoClusters vs databaseAccounts)

- **What was missing:** Clear, top-level note and examples that the vCore Azure DocumentDB control-plane resource is Microsoft.DocumentDB/mongoClusters (not Microsoft.DocumentDB/databaseAccounts).
- **Where the agent looked:** Readiness findings and the cold-answer confusion (readiness_findings Q01..Q03). The available docs include the correct resource but the agent model confusion is real.
- **Effect on this build:** If a builder attempted to add provisioning, they might choose the wrong ARM/Terraform resource type and target Cosmos DB's databaseAccounts resource instead of the vCore mongoClusters resource, causing deployment errors or incorrect automation.
- **Suggested fix (naming_or_disambiguation):** Add a short 'Naming and resource types' paragraph to quickstarts and the agent kit that explicitly maps: 'For vCore DocumentDB clusters use Microsoft.DocumentDB/mongoClusters (examples Bicep/Terraform included). Do not use databaseAccounts which is for Cosmos DB RU model.' Include a minimal Bicep snippet for mongoClusters.

## [medium] .env.example completeness

- **What was missing:** .env.example contains only DOCUMENTDB_URI. The sample also uses PORT and could require other knobs (NODE_ENV, logging).
- **Where the agent looked:** Repository .env.example and README; examined src/index.js and src/db.js to identify used environment variables.
- **Effect on this build:** The sample included .env.example but omitted other expected environment settings. This increases friction for users and automated agents, who may not know to set PORT or other runtime flags.
- **Suggested fix (learn_doc):** Update .env.example to list all required and optional settings with placeholders and short descriptions (DOCUMENTDB_URI, PORT, NODE_ENV, ENABLE_WRITE_TOOLS (if used), and an example). Add a short 'local development' paragraph in the README describing copying .env.example and what to set.

