# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 7 |
| readiness_report | 3 |
| operator | 2 |
| model_default | 2 |
| tool_result | 2 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T11:58:38+00:00

## D002 (build): I chose Node.js with Express and Mongoose for the sample service.

- **Instead of:** Python Flask + PyMongo; Node.js Express + Mongoose; Go + mgo driver
- **Because:** The user requested a Node.js Mongoose service; Node + Mongoose is the natural fit and matches the prompt.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Builder will treat this as a single-agent code generation task producing a standalone Node.js service with REST endpoints.'
- **When:** 2026-11-25T11:58:56+00:00

## D003 (build): I chose Mongoose 7.x (latest 7.x) and the matching mongodb driver that Mongoose depends on.

- **Instead of:** Mongoose 6.x; Mongoose 7.x; Use native MongoDB driver only
- **Because:** Mongoose 7.x is current, compatible with Node 24, and simplifies schema + ref modeling required by the sample.
- **Reason came from:** `prompt`
- **Evidence:** Assumption_from_prompt_review: 'Builder will pick a modern Mongoose version compatible with Node.js 24 (e.g., Mongoose 7.x) and the MongoDB Node driver matching Mongoose's peer dependency (mongodb 5.x).'
- **When:** 2026-11-25T11:59:00+00:00

## D004 (build): I chose to read the full connection string from the environment variable DOCUMENTDB_URI at runtime and use it as provided (do not embed credentials in repo).

- **Instead of:** Use MONGODB-OIDC / Entra ID auth; Use SCRAM-SHA-256 / user+password; Read full connection string from environment and trust its auth mechanism
- **Because:** The sample must not contain secrets and the environment-provided URI may already encode the recommended auth mechanism; using it keeps the sample simple and secure.
- **Reason came from:** `prompt`
- **Evidence:** Run environment: 'Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time.'
- **When:** 2026-11-25T11:59:02+00:00

## D005 (build): I chose not to provision any Azure resources and to use the existing cluster from DOCUMENTDB_URI.

- **Instead of:** Provision a new DocumentDB cluster as part of sample; Use the existing cluster pointed to by DOCUMENTDB_URI and do not provision
- **Because:** Provisioning is disallowed by policy; a live reachable cluster is provided for verification.
- **Reason came from:** `readiness_report`
- **Evidence:** Run policy and run-environment: 'Azure resource changes allowed: False.' and 'A DocumentDB cluster is already provisioned and reachable.'
- **When:** 2026-11-25T11:59:04+00:00

## D006 (build): I chose to create a separate 'households' collection with documents that reference members (array of ObjectId refs to customers).

- **Instead of:** Embed household members within Customer documents; Store separate Household documents with member refs (ObjectId)
- **Because:** A separate Household collection makes household-level aggregates (CLV, products) straightforward and avoids expanding customer documents; it's a clearer model for this demo.
- **Reason came from:** `prompt`
- **Evidence:** Assumption_from_prompt_review: 'Customer documents include ...; Household documents contain an array of ObjectId refs to customers (Mongoose ref).'
Also documentdb-data-modeling skill guidance that references embedding vs referencing for many-to-many/read patterns.
- **When:** 2026-11-25T11:59:07+00:00

## D007 (build): I chose to create a compound index on { normalizedAddress:1, phone:1, surname:1 } using the documentdb MCP server create_index API, and also declare the index in the Mongoose schema for parity.

- **Instead of:** Create only Mongoose indexes via schema.ensureIndexes; Use documentdb MCP server to create and verify indexes; Do nothing about indexes for the demo
- **Because:** Using MCP server lets us verify index creation and inspect explain plans in the live cluster; declaring in Mongoose ensures the schema is explicit and local dev parity.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness_report: 'the documentdb MCP server is available for live verification' and assumptions about creating a compound index to support grouping/matching.
- **When:** 2026-11-25T11:59:10+00:00

## D008 (build): I chose @faker-js/faker for synthetic data generation.

- **Instead of:** faker (old 'faker' package); @faker-js/faker (actively maintained)
- **Because:** Avoid module-not-found and use a maintained faker library compatible with Node 24.
- **Reason came from:** `model_default`
- **Evidence:** The seed script needs a maintained faker library; the older 'faker' package may not have a valid main entry. @faker-js/faker is actively maintained.
- **When:** 2026-11-25T12:00:36+00:00

## D009 (build): I chose to create the compound index via Mongoose's schema.ensureIndexes programmatically because the documentdb_create_index MCP call failed.

- **Instead of:** Continue trying documentdb_create_index via MCP; Create index via Mongoose programmatically (ensureIndexes)
- **Because:** MCP API failed in this environment; using Mongoose to create the index achieves the same outcome for the sample without provisioning changes.
- **Reason came from:** `tool_result`
- **Evidence:** Attempted functions.documentdb_create_index returned 'Error: Function failed.' when creating index on customers collection.
- **When:** 2026-11-25T12:01:16+00:00

## D010 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T12:03:00+00:00

## D011 (build): I chose Node.js with Express and Mongoose (a small REST service).

- **Instead of:** Python/Flask with PyMongo; Node.js/Express with Mongoose
- **Because:** The prompt explicitly requests Node.js and Mongoose.
- **Reason came from:** `prompt`
- **Evidence:** Sample prompt: 'build a Node.js Mongoose service'
- **When:** 2026-11-25T12:03:16+00:00

## D012 (build): I chose Mongoose 7.x (latest 7 series compatible with Node 24).

- **Instead of:** Mongoose 6.x; Mongoose 7.x
- **Because:** Mongoose 7.x is current and compatible with Node 24 and offers stable APIs; it matches the run-environment assumptions.
- **Reason came from:** `model_default`
- **Evidence:** Assumption: 'Builder will pick a modern Mongoose version compatible with Node.js 24 (e.g., Mongoose 7.x)'.
- **When:** 2026-11-25T12:03:19+00:00

## D013 (build): I chose SCRAM-SHA-256 via the DOCUMENTDB_URI env var (default connection string).

- **Instead of:** Use Entra ID (MONGODB-OIDC) authentication; Use SCRAM-SHA-256 via connection string in DOCUMENTDB_URI
- **Because:** Simpler for a sample repo and matches the run-environment guidance; avoid requiring additional interactive Entra ID setup. Will document Entra ID alternative in README.
- **Reason came from:** `prompt`
- **Evidence:** Run environment: 'connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time.'
- **When:** 2026-11-25T12:03:22+00:00

## D014 (build): I chose a compound index on { normalizedAddress:1, phone:1, surname:1 } plus a numeric index on clv and a multikey index on products to support product aggregation.

- **Instead of:** Compound index on normalizedAddress, phone, surname; Separate single-field indexes on address, phone, surname; No additional indexes
- **Because:** Compound index follows ESR guidance and will help the grouping queries used in sample; additional clv and products indexes optimize aggregates.
- **Reason came from:** `prompt`
- **Evidence:** Assumptions from prompt review: 'Create aggregation pipelines that group on normalized address/phone/surname. Add a compound index on { normalizedAddress:1, phone:1, surname:1 }'.
- **When:** 2026-11-25T12:03:50+00:00

## D015 (build): I chose to use @faker-js/faker (latest 8.x) instead of faker, because npm reported faker@^9.0.0 not found.

- **Instead of:** faker@^9.0.0 (failed); @faker-js/faker@^8 (community-maintained fork)
- **Because:** @faker-js/faker is the maintained fork and available on npm; update package.json to use it.
- **Reason came from:** `tool_result`
- **Evidence:** npm error: 'No matching version found for faker@^9.0.0'
- **When:** 2026-11-25T12:04:51+00:00

## D016 (build): I chose to use the documentdb MCP server tools to verify collections and sample documents in the live cluster.

- **Instead of:** Verify data using only local scripts (mongoose); Use documentdb MCP server for data-plane verification (list collections, sample docs)
- **Because:** Provides authoritative, service-oriented verification (index listing, explain) beyond the application-level checks.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'the documentdb MCP server's connection profile `default` is connected to that same cluster. Use its tools to inspect collections, indexes and query plans and to verify what the app created.'
- **When:** 2026-11-25T12:05:33+00:00
