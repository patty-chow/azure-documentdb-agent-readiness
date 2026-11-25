# Documentation and tooling gaps: 20-store-locator-with-geospatial-search

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Mongoose autoIndex production guidance

- **What was missing:** No Azure-DocumentDB-specific public guidance on whether Mongoose autoIndex should be disabled in production (the discovery returned prior knowledge only).
- **Where the agent looked:** Searched installed skills and web for 'Mongoose autoIndex Azure DocumentDB' and repository search (events.jsonl search_text).
- **Effect on this build:** Builder did not disable autoIndex explicitly; seed script creates indexes but there is no explicit production configuration to disable autoIndex. Agents relying on memory may not disable autoIndex when they should.
- **Suggested fix (learn_doc):** A short 'Mongoose on Azure DocumentDB' doc: state that autoIndex should be disabled in production (autoIndex:false) and show the recommended pattern (create indexes in migration/seed scripts) with a code snippet and example env-based toggle. Include a 1-paragraph rationale and example Bicep/az CLI migration step.

## [high] Lat/lon & radius validation guidance

- **What was missing:** No public DocumentDB-specific guidance found during discovery on validating latitude/longitude ranges and enforcing max radius for geo endpoints.
- **Where the agent looked:** Searched skills and web: 'validate lat lon input azure documentdb', 'sanitize geospatial query radius best practice'.
- **Effect on this build:** The /nearby endpoint only checks numeric params (NaN) and does not clamp/reject out-of-range coordinates or limit max radius, leaving API vulnerable to expensive or abusive queries unless the developer adds safeguards.
- **Suggested fix (learn_doc):** Add a short paragraph to the Geo queries page advising: validate lat ∈ [-90,90], lon ∈ [-180,180], enforce a default maximum radius (e.g., 50km), and include code snippets for server-side validation and returning 400 on invalid input.

## [high] Retry & transient error guidance

- **What was missing:** Samples and quickstarts mention connection options but a concise example of application-level retries (exponential backoff + honoring Retry-After) for the Node.js/Mongoose stack on DocumentDB was not prominent.
- **Where the agent looked:** documentdb-connection skill and quickstart pages; discovery located general guidance but not a compact Node.js example.
- **Effect on this build:** No retry logic was added to the sample; transient failures and HTTP 429s are not handled specifically by the API, increasing risk in real deployments.
- **Suggested fix (sample_or_quickstart):** A short 'Retries and backoff' example in the documentdb-connection skill: Node.js snippet showing a small retry wrapper (with exponential backoff) for DB operations and handling 429 with Retry-After. Include guidance when driver-level retries are sufficient vs when app-level retries are required.

## [high] IaC example using mongoClusters

- **What was missing:** No example IaC template (Bicep/Terraform) showing Microsoft.DocumentDB/mongoClusters resource for vCore clusters was included.
- **Where the agent looked:** Repo and quickstart IaC; none in sample. Readiness findings noted agent confusion between databaseAccounts and mongoClusters.
- **Effect on this build:** Operators who try to supply infrastructure-as-code may target the wrong resource type (databaseAccounts) or leave out tier/storage parameters; this increases risk of incorrect provisioning.
- **Suggested fix (sample_or_quickstart):** Provide a minimal Bicep template that creates Microsoft.DocumentDB/mongoClusters with parameterized sku/tier and region, plus sample az CLI commands; add a short note clarifying difference from Microsoft.DocumentDB/databaseAccounts (RU-based Cosmos).

## [medium] Driver version pinning discoverability

- **What was missing:** Agent did not surface the official guidance about tested Mongoose/MongoDB driver versions by discovery; it was found only by name search. The quickstart docs do list tested driver versions.
- **Where the agent looked:** learn.microsoft.com quickstart and tutorial pages for Mongoose + Azure DocumentDB (found by targeted search).
- **Effect on this build:** Builder used caret ranges in package.json but package-lock.json pinned versions for the build. Agents following default choices might not pick a driver version that the docs explicitly tested.
- **Suggested fix (discoverability):** Make the 'Tested driver versions' and 'Recommended Mongoose/driver pairing' more visible on the quickstart/tutorial landing page; add one-line 'Tested with Mongoose X.Y.Z (MongoDB driver A.B.C)' near the top so agents find it by general search.

## [medium] README clean-up and test guidance

- **What was missing:** README did not include explicit cleanup steps nor guidance for running tests without a live cluster.
- **Where the agent looked:** Repository README and quickstart; no cleanup or test instructions found.
- **Effect on this build:** Users receiving the sample may not know how to remove the created sample data or run tests offline; it increases friction for CI and local experimentation.
- **Suggested fix (sample_or_quickstart):** Add a 'Clean-up' section showing how to drop the stores collection (mongo shell or node snippet) and an optional 'Testing' section that shows how to run unit tests with mongodb-memory-server or mocks and what environment variables are required.

## [medium] MCP management tool opt-in note

- **What was missing:** The MCP 'create_index' tool failed in this run with an opt-in requirement (ENABLE_MANAGEMENT_TOOLS). There was no repo-level note about MCP opt-in settings.
- **Where the agent looked:** events.jsonl (tool error) and repository (no mention).
- **Effect on this build:** Builder attempted to use MCP create_index and the tool failed; they fell back to seed.createIndexes. Future builders/agents will retry the MCP tool unless informed about opt-in.
- **Suggested fix (agent_kit_rule):** A short agent-kit rule or README note: 'When using MCP management tools in this environment you may need to set ENABLE_MANAGEMENT_TOOLS=true; otherwise fall back to application-level index creation.'

