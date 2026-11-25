# Documentation and tooling gaps: 03-portfolio-tracker-with-live-alerts

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Driver version compatibility

- **What was missing:** Concrete guidance mapping Azure DocumentDB supported MongoDB wire protocol/server version to exact driver (mongodb) and Mongoose versions to pin for samples (e.g., tested Mongoose/mongodb pairs for MongoDB 7.x clusters).
- **Where the agent looked:** documentdb-driver, documentdb-connection skills and Microsoft Learn compatibility pages were checked; no single explicit pinned-version recommendation for samples was found.
- **Effect on this build:** Builder used model-default Mongoose 7.x and caret ranges in package.json. This leaves ambiguity for future builds about exact minor/patch versions to pin for reproducible samples.
- **Suggested fix (learn_doc):** A short 'Driver compatibility' page in the agent-kit or product docs that lists the tested driver versions and the recommended pinned package.json snippet for Node (e.g., "mongoose": "7.6.0", "mongodb": "5.6.0"), plus the command 'npm ci' to guarantee lockfile installs.

## [high] Resume-token persistence for change streams

- **What was missing:** A short example and guidance (with sample code) showing durable persistence of the last processed change stream resume token and how to resume using resumeAfter/startAtOperationTime safely (including backoff when resume fails).
- **Where the agent looked:** Change stream docs (Microsoft Learn) and documentdb-driver/connection skills—docs mention resume tokens but no small, copy-paste sample for a Node/Mongoose watcher that persists tokens to a collection.
- **Effect on this build:** The sample opens change streams with fullDocument: 'updateLookup' but does not persist resume tokens, leaving the watcher unable to resume exactly where it left off after a restart and increasing risk of missed or duplicated processing.
- **Suggested fix (sample_or_quickstart):** A 1-page quickstart 'Change-stream resilience' showing: code to write change._id to a durable 'stream_tokens' collection after processing; startup code that reads the last token and calls Model.watch(..., { resumeAfter: token }); guidance on how to handle resume failures and token expiry.

## [high] Change-stream handler best-practice: offload webhook delivery

- **What was missing:** A sample pattern and short justification showing non-blocking change-stream handlers (enqueue work to a deliveries collection or to a queue) and a separate worker that performs HTTP deliveries, with sample code for node/express/mongoose.
- **Where the agent looked:** Change streams docs and documentdb-connection/driver skills; general guidance exists but no tiny example packaged for use in agent-authored samples.
- **Effect on this build:** Builder kept webhook deliveries in the handler for simplicity; this is acceptable for a toy sample but could mislead builders into synchronous handlers in production.
- **Suggested fix (sample_or_quickstart):** A short sample showing 'watch -> write delivery request to deliveries collection -> worker polls deliveries collection and sends webhooks with retries & dead-lettering'.

## [high] Webhook payload & idempotency guidance

- **What was missing:** A recommended webhook payload schema (fields to include: eventId/resumeToken/changeId, ruleId, userId, symbol, metric, value, threshold, timestamp) and a small recommended delivery-record schema (webhook_deliveries) for deduplication and observability.
- **Where the agent looked:** Searches for 'Azure DocumentDB webhook idempotent delivery' produced no authoritative guidance; general webhook best-practices exist but not for DocumentDB change-stream based events.
- **Effect on this build:** The sample sends a reasonable payload but does not include a durable deduplication key or delivery-record persistence; this makes idempotency and delivery observability unclear for integrators.
- **Suggested fix (learn_doc):** A short 'Webhooks from change streams' note in the sample README or product docs with example payload and schema for webhook_deliveries collection and sample code to include change._id as eventId.

## [high] Agent confusion & naming guidance

- **What was missing:** Clear, prominent wording to disambiguate 'Azure DocumentDB' (this product), older 'Cosmos DB for MongoDB' variants, and neighbours such as 'Amazon DocumentDB'.
- **Where the agent looked:** Readiness findings and multiple skills: the product naming is a common confusion source; documentation exists but is scattered.
- **Effect on this build:** The builder used 'Azure DocumentDB' correctly, but future agents may pick the wrong resource type or CLI group (az cosmosdb vs az documentdb).
- **Suggested fix (naming_or_disambiguation):** One-paragraph 'Naming and compatibility' in README that states: 'This sample targets Microsoft.DocumentDB/mongoClusters (az documentdb mongocluster) — not az cosmosdb or Cosmos DB databaseAccounts; use the cluster connection strings view to copy the SRV URI.'

## [medium] allowDiskUse for large aggregations

- **What was missing:** A short note: when to pass allowDiskUse:true for aggregation pipelines and example of how to do that from Mongoose/Node.
- **Where the agent looked:** Aggregate docs on Microsoft Learn and query-optimizer skill; guidance exists but a one-liner example in the sample README would be helpful.
- **Effect on this build:** Sample aggregation omits allowDiskUse and could be surprising when users run larger datasets. It's a small change in code but worth documenting.
- **Suggested fix (discoverability):** Add a subsection in README 'Large aggregations' showing how to call Position.aggregate(pipeline, { allowDiskUse: true }).

## [medium] Dependencies pinning example for Node samples

- **What was missing:** An explicit guidance in the agent-kit on how to present pinned dependencies for Node samples (recommend commit of package-lock.json, use npm ci, optionally pin exact versions in package.json).
- **Where the agent looked:** No single how-to found in the agent-kit; package-lock.json is present but package.json uses ^ ranges which can confuse reproducibility expectations.
- **Effect on this build:** Builder committed package-lock.json (good) but package.json still uses ranges; future rebuilds may produce different transient installs if lockfile is not used.
- **Suggested fix (agent_kit_rule):** Agent-kit rule: 'For Node samples, commit package-lock.json, call npm ci in Quickstart, and either pin versions in package.json or document that users should run npm ci for reproducible installs.'

## [medium] IaC quickstart for Microsoft.DocumentDB/mongoClusters

- **What was missing:** A minimal Bicep / Terraform example that creates a Microsoft.DocumentDB/mongoClusters resource with low-cost defaults suitable for sample runs and an example az documentdb mongocluster command, plus a note that the sample can skip provisioning when a cluster is provided.
- **Where the agent looked:** documentdb-azure-deployment skill and Learn pages (some examples exist) but there was no single small sample-ized IaC template included in the agent kit for sample apps.
- **Effect on this build:** No IaC included in repo (by design for this run). Adding a small, optional IaC file would let users provision a throwaway cluster in environments that allow it.
- **Suggested fix (sample_or_quickstart):** A minimal Bicep file and an example az documentdb mongocluster create command with low-cost defaults and a 'do not run in restricted CI' note.

## [medium] Prior-knowledge-only practices (Mongoose .lean, caching alert metadata)

- **What was missing:** Public, sample-specific documentation affirming whether prior-knowledge rules (use .lean() in hot paths; cache static metadata for alert evaluation) apply to Azure DocumentDB or are general Mongoose guidance.
- **Where the agent looked:** Searches returned prior knowledge but no product-specific guidance.
- **Effect on this build:** Agents (and builders) may act on general Mongoose memory/performance heuristics without an Azure-specific confirmation.
- **Suggested fix (discoverability):** Agent-kit rule page: 'Performance tips for Mongoose on DocumentDB' listing .lean() and caching examples and when to use them for alert-evaluation workloads.

## [low] Decision logging: changeStream options and HTTP client choices

- **What was missing:** Small auditing guidance telling builders to record non-obvious design choices (e.g., fullDocument:updateLookup, HTTP client selection) in decisions.jsonl so audits can explain why a sample used a particular pattern.
- **Where the agent looked:** No such audit template existed in the agent-kit for sample builds.
- **Effect on this build:** Several code choices were made but not logged (fullDocument option, mixing axios and node-fetch). This complicates later audits.
- **Suggested fix (agent_kit_rule):** Add a two-line decision template to the agent-kit that builders must fill out for choices affecting behavior/ops (driver versions, change-stream options, retry/backoff policy, HTTP client).

