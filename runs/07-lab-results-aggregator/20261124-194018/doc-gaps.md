# Documentation and tooling gaps: 07-lab-results-aggregator

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Beanie/Motor compatibility matrix

- **What was missing:** A clear, published compatibility matrix mapping Beanie versions, Motor (or AsyncMongoClient) versions, PyMongo versions and supported Azure DocumentDB wire-protocol/server versions (5.0..8.0).
- **Where the agent looked:** documentdb-driver and documentdb-connection skills, Microsoft Learn compatibility pages; events.jsonl readiness findings noted this information gap.
- **Effect on this build:** The builder pinned working library versions but had to iterate (initial beanie==1.20.1 failed then switched to 1.22.6). Without an authoritative matrix the builder cannot be certain their pinned versions will be compatible across other cluster versions.
- **Suggested fix (learn_doc):** A short Learn-style page and an agent-kit resource that lists supported combinations: Beanie versions ↔ Motor / AsyncMongoClient / PyMongo versions ↔ recommended Python versions ↔ minimal server 'wire-protocol' (MongoDB) versions required for $setWindowFields/change streams. Include a one-line example 'If using Beanie X.Y use Motor/PyMongo A.B; if you need AsyncMongoClient use PyMongo >=X'.

## [high] Unit tests that run without a live cluster

- **What was missing:** A sample test harness and examples showing how to run unit tests and integration tests without a live DocumentDB cluster (mocks, DocumentDB gateway usage, or recommended test doubles).
- **Where the agent looked:** Repository (no tests), documentdb-local-deployment skill docs for a local Gateway image (found), but no sample pytest files demonstrating offline tests.
- **Effect on this build:** No tests are present; maintainers and reviewers cannot run regression checks offline. This increases friction for contributors and CI.
- **Suggested fix (sample_or_quickstart):** Add a tests/ directory with pytest examples: (1) unit tests that mock Beanie/Motor operations using monkeypatch or mongomock, and (2) an optional integration test that uses the DocumentDB Gateway docker image (documentdb-local-deployment) started by a script or a docker-compose snippet. Include CI job examples that run unit tests without network access.

## [medium] Provisioning examples using Microsoft.DocumentDB/mongoClusters

- **What was missing:** Minimal infrastructure-as-code examples (Bicep and Terraform/AzAPI) targeting the DocumentDB mongoClusters resource type with safe low-cost defaults and cleanup steps.
- **Where the agent looked:** documentdb-azure-deployment skill and Microsoft Learn templates; repository contains no IaC files.
- **Effect on this build:** The sample assumes an existing cluster; reviewers/contributors cannot provision a matching cluster from this repo. Without IaC examples, users may try older Cosmos 'databaseAccounts' templates and fail to create the right resource type.
- **Suggested fix (sample_or_quickstart):** Provide a 'deploy' directory with one Bicep example that creates Microsoft.DocumentDB/mongoClusters with minimal tier and a terraform/AzAPI example. Include parameters for region/tier and a 'destroy'/cleanup step. Note: reference CLI examples in the README and link to the agent-kit deployment doc.

## [medium] Demo/reference-range guidance

- **What was missing:** Authoritative guidance or a recommended pattern for where demo reference ranges should live (in-code vs DB collection vs external service) for gallery samples.
- **Where the agent looked:** Prompt, readiness notes, and no public guidance located that prescribes the demo approach.
- **Effect on this build:** Builder chose to hard-code ranges (decision D005) under a 'model_default' rationale. This is acceptable for a small demo but affects how alerts and pipeline flagging are implemented and tested.
- **Suggested fix (agent_kit_rule):** Add an agent-kit rule and a one-paragraph Learn note recommending: for minimal demos, a small in-code mapping is acceptable but include README instructions and a DB-backed option and tests; for production demos prefer a separate 'reference_ranges' collection with a sample loader and document schema example.

## [medium] Resume-token persistence for change streams (best-practice example)

- **What was missing:** While public docs describe resume tokens, a short example showing durable checkpointing (writing resume tokens to a local collection and resuming on restart) suitable for a gallery sample was not in the repo.
- **Where the agent looked:** documentdb change-stream docs (found), repository (no durable checkpoint example).
- **Effect on this build:** The sample's change-stream demo is short-lived and prints alerts to console; reviewers wanting a robust example must implement durable checkpointing themselves.
- **Suggested fix (sample_or_quickstart):** Add a short example script that demonstrates: (1) writing resume token to 'change_stream_checkpoints' collection periodically, (2) on startup reading last token and calling coll.watch(resumeAfter=token), (3) handling resumable errors. Place this as 'scripts/change_stream_checkpoint_demo.py'.

## [low] Robust connection-string merging guidance

- **What was missing:** A small utility or documented snippet that safely merges or canonicalizes MongoDB URIs (SRV and non-SRV) and query parameters rather than naïvely appending strings, to avoid duplicate-query-parameter warnings.
- **Where the agent looked:** app/src/db.py uses a simple append; events.jsonl shows 'Duplicate URI option "retryWrites"' warning emitted by pymongo uri parser during runs.
- **Effect on this build:** Users supplying a DOCUMENTDB_URI that already includes retryWrites or TLS options will see a 'Duplicate URI option' warning; this is harmless but noisy and may confuse users.
- **Suggested fix (agent_kit_rule):** Ship a small helper in the agent kit (or sample utilities) that parses URIs with urllib.parse or pymongo.uri_parser, merges existing query params with required ones without duplication, supports mongodb+srv forms, and normalizes the final URI. Add a brief README example showing correct usage.

