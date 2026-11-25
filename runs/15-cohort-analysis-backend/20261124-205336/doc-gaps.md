# Documentation and tooling gaps: 15-cohort-analysis-backend

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] DB-based job lease guidance

- **What was missing:** Clear public guidance for Azure DocumentDB recommending or discouraging a DB-based lease (findOneAndUpdate) pattern for scheduled job locking.
- **Where the agent looked:** Searches: "Azure DocumentDB findOneAndUpdate 'lease' 'distributed lock'", and installed skill docs (documentdb-*). No authoritative Azure doc prescribing this pattern was found; it remains prior-knowledge.
- **Effect on this build:** The sample uses APScheduler in-process and does not implement a distributed lease. For single-process demo this is fine, but a user copying the sample into multi-instance production may get overlapping jobs.
- **Suggested fix (learn_doc):** A short 'Job scheduling and locking' page in the Agent Kit or docs that: (1) states whether Azure DocumentDB has a recommended DB-based lease pattern; (2) shows a safe example using findOneAndUpdate for a lease record (idempotent, timestamp, owner) and how to handle lease expiry; (3) shows a cloud-native alternative (use Azure Functions Timer + Durable Functions or Azure Automation + a leader-election pattern).

## [high] $bucket feature-support note

- **What was missing:** A prominent note in quickstarts/readme explaining which aggregation stages (e.g. $bucket/$bucketAuto) are supported only on certain Mongo-API server versions and how to check compatibility.
- **Where the agent looked:** Azure feature-support pages (learn.microsoft.com) and skills (documentdb-query-optimizer). The feature-support pages mention the limitation but this guidance was not surfaced to the sample or README prominently.
- **Effect on this build:** The sample uses $bucket and worked against the provided cluster, but on other clusters (older server-versions) the pipeline would fail. An agent replicating the sample could build a non-working sample if it assumes $bucket is always supported.
- **Suggested fix (discoverability):** Add a short 'aggregation compatibility' section to sample README and to the Agent Kit: 'Before using $bucket/$bucketAuto, check your cluster server-version or run the included compatibility_check.py; if unsupported, use client-side bucketing or alternate aggregation shapes.' Include a one-liner to detect server wire-version via driver or to run a small test pipeline and explain() it.

## [high] Explain()/diagnostics for aggregation

- **What was missing:** A sample or short recipe demonstrating how to call explain('executionStats') for aggregation pipelines against Azure DocumentDB and how to capture RU metrics from the explain output.
- **Where the agent looked:** documentdb-query-optimizer skill and Azure docs; the skill mentions explain() but the sample did not include an example.
- **Effect on this build:** The builder did not add explain() reporting to the snapshot script; missing explain makes it harder to tune the pipeline or to show RU consumption to users.
- **Suggested fix (sample_or_quickstart):** Add a small script (scripts/aggregation_explain.py) that runs the cohort pipeline via explain('executionStats'), prints key fields (totalDocsExamined, totalKeysExamined, executionTimeMillis, RU estimates if available) and stores the explain output to a diagnostics collection.

## [high] Change-feed / incremental-snapshots guidance

- **What was missing:** A short guide showing how to implement incremental snapshot updates using the change feed/change streams rather than full recomputes.
- **Where the agent looked:** Azure caching docs, change feed docs and installed skills (documentdb-data-modeling, documentdb-monitoring).
- **Effect on this build:** The sample performs full recompute weekly; for large datasets this is RU-expensive. Lack of a small change-feed example means agents are likely to implement full recomputes by default.
- **Suggested fix (sample_or_quickstart):** A small example showing (1) enable change feed or change streams for a collection; (2) a simple consumer that updates per-cohort aggregates on change events; (3) best-practice for checkpointing and failure handling.

## [medium] JSON schema / collection validators for Mongo API

- **What was missing:** Authoritative guidance on whether collection-level JSON schema validators are supported and recommended for Azure DocumentDB with MongoDB compatibility (this is a prior-knowledge area with limited public docs).
- **Where the agent looked:** Searches: 'Azure DocumentDB collection validator', '$jsonSchema operator Azure Cosmos DB', and installed skills. No clear consistent guidance found in public docs.
- **Effect on this build:** Sample does not create collection validators. Validators could prevent malformed documents and make aggregation assumptions safer.
- **Suggested fix (learn_doc):** A short page in the docs/Agent Kit describing whether the MongoDB API supports collection validators for the supported server-versions, example createCollection with validator, and guidance on when to use validators vs application validation.

