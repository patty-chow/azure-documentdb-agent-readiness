# Documentation and tooling gaps: 02-swift-message-parser-store

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Pin versions for Beanie/Motor/PyMongo

- **What was missing:** Authoritative, tested package-version matrix for Beanie + Motor + PyMongo targeting Azure DocumentDB (MongoDB 7.0 wire version). The build used pinned packages in the execution environment but the committed requirements file uses ranges; there is no documentation saying which exact versions were validated against the cluster.
- **Where the agent looked:** Inspected project requirements and run logs; searched installed skills and Microsoft Learn (events.jsonl queries around MongoDB 7.0 compatibility).
- **Effect on this build:** Led to ambiguity: pip install during the build used pinned versions, but the repo's requirements file allows ranges. This means future reproductions may install incompatible versions and fail or behave differently.
- **Suggested fix (sample_or_quickstart):** Add a short 'Supported packages' section to the README and commit a requirements.txt with pinned, tested versions (example: beanie==1.22.1, motor==3.1.1, pymongo==4.4.0). Also add a constraints.txt for CI and a note explaining which versions were validated against MongoDB 7.0.

## [high] WriteConcern semantics (client writeConcern ignored)

- **What was missing:** Clear, prominent documentation that Azure DocumentDB (vCore mongoClusters) ignores client-specified MongoDB writeConcern settings and that platform replication/consistency semantics should be relied upon.
- **Where the agent looked:** Microsoft Learn docs and installed skills; readiness_findings flagged that prior belief about writeConcern was contradicted by Azure docs (events.jsonl search results).
- **Effect on this build:** If a developer attempted to tune durability via client writeConcern they would be misled; sample does not set writeConcern, but other samples might attempt to tune it incorrectly.
- **Suggested fix (naming_or_disambiguation):** A short note in documentdb-driver (and the sample README) titled 'Write concern and durability' that states: 'Azure DocumentDB ignores client-specified writeConcern (w/wtimeout). Rely on the cluster's tier and platform durability guarantees. Do not expect client writeConcern to change server durability.' Include a link to the authoritative Learn page.

## [high] Connection tuning and retry/backoff examples

- **What was missing:** Concrete, copy-paste code showing how to set serverSelectionTimeoutMS/socketTimeoutMS and how to implement exponential backoff with jitter on 429/TransientNetworkError for Motor/AsyncIOMotorClient.
- **Where the agent looked:** documentdb-connection skill and Microsoft Learn; the skill exists but the sample does not include practical code snippets demonstrating those settings.
- **Effect on this build:** The sample currently uses the default client configuration and lacks retry/backoff, increasing the chance of transient failures or blocked calls in production-like conditions.
- **Suggested fix (agent_kit_rule):** Add a short code snippet to documentdb-connection and the sample's db.init_db showing AsyncIOMotorClient(..., serverSelectionTimeoutMS=5000, socketTimeoutMS=120000) and a helper retry decorator that respects Retry-After, with an example of wrapping insert_many calls. Include recommended default values and a note about ordered=False for bulk writes.

## [high] IaC resource type and CLI group clarity (mongoClusters vs databaseAccounts / az documentdb vs az cosmosdb)

- **What was missing:** A single prominent note clarifying the correct resource type and CLI group to use for vCore-managed Mongo clusters: Microsoft.DocumentDB/mongoClusters and az documentdb mongocluster. Many older docs and examples reference databaseAccounts / az cosmosdb which is the RU-based Cosmos model.
- **Where the agent looked:** Readiness findings and Microsoft Learn; searches found the correct pages but the confusion is common.
- **Effect on this build:** If a developer attempted to write IaC using Microsoft.DocumentDB/databaseAccounts or az cosmosdb they would create or target the wrong control-plane resource and fail to provision the intended vCore mongoCluster.
- **Suggested fix (discoverability):** Add a 'Resource type decision' note to the documentdb-azure-deployment skill, and a short 'Do not use az cosmosdb for vCore mongo clusters' callout in README. Include a minimal Bicep snippet showing Microsoft.DocumentDB/mongoClusters and example az documentdb mongocluster CLI commands.

## [medium] Enable Microsoft Entra ID (OIDC) examples

- **What was missing:** A short how-to and an example connection string showing how to enable Microsoft Entra ID authentication on a cluster and how a Python client connects using OIDC / MONGODB-OIDC.
- **Where the agent looked:** Installed documentdb-security skill and Microsoft Learn; the skill documents Entra ID but the sample and README do not mention it.
- **Effect on this build:** Users will default to connection-string auth; the sample does not explain whether Entra ID is available or how to use it. This leads to weaker samples that encourage long-lived credentials for TLS endpoints.
- **Suggested fix (learn_doc):** Add a short page or README section 'Authentication options' describing (1) native SCRAM username/password, (2) Microsoft Entra ID / OIDC support including CLI/Bicep flags to enable it, and (3) example connection strings and Python snippet for OIDC-enabled clusters.

## [medium] Make daily aggregation indexable

- **What was missing:** Recommendation and example to store a pre-computed truncated date field (e.g., message_date_day) at insert time and index it, so daily grouping/aggregation is index-friendly and fast.
- **Where the agent looked:** documentdb-data-modeling skill and $dateTrunc docs; the skill suggests this pattern but the sample did not implement it.
- **Effect on this build:** Aggregation works but may not use an optimal index shape; for larger datasets this will cause full-collection work and slower pipelines.
- **Suggested fix (learn_doc):** Add a short 'Time-series aggregation' snippet to the data-modeling skill and the sample README: compute message_date_day at ingest and seed time (YYYY-MM-DD) and add compound index (message_type, message_date_day). Show how to migrate existing data to include the new field idempotently.

## [medium] Repository decision audit: storing amounts as floats

- **What was missing:** There is no logged decision documenting the deliberate choice to store amounts as floats for simplicity, nor an explicit 'temporary/educational' flag in the README about the financial precision trade-offs.
- **Where the agent looked:** decisions.jsonl and repository files; decisions.jsonl does not contain an entry explaining the choice to use float for amount.
- **Effect on this build:** The lack of an explicit decision makes it easier for maintainers to overlook the precision problem when publishing; a reviewer may assume the sample is production-ready with floats.
- **Suggested fix (other):** Add an explicit decision entry in decisions.jsonl or README: 'Amounts stored as float in sample for simplicity; production systems must use Decimal128 or integer cents; migration guidance provided.'

