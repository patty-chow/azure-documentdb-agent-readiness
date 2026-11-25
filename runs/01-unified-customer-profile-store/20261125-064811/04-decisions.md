# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 3 |
| readiness_report | 2 |
| operator | 1 |
| skill | 1 |
| model_default | 1 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T14:50:42+00:00

## D002 (build): I chose Node.js with Express and Mongoose (Mongoose 7.x) for the sample service.

- **Instead of:** Python/Flask with PyMongo; Node.js with native MongoDB driver; Node.js with Express and Mongoose
- **Because:** The prompt explicitly requested a Node.js Mongoose service; Mongoose provides a familiar ODM and manages the MongoDB driver options for MongoDB 7.0 compatibility.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt review: 'Use a recent stable Mongoose compatible with Node 24' and the sample prompt asking for 'Node.js Mongoose service'.
- **When:** 2026-11-25T14:50:56+00:00

## D003 (build): I chose to read DOCUMENTDB_URI from the environment at runtime.

- **Instead of:** Embed connection string in files; Read env var DOCUMENTDB_URI
- **Because:** Avoid committing secrets and follow guidance.
- **Reason came from:** `skill`
- **Evidence:** Readiness guidance: 'read the cluster connection string only from process.env.DOCUMENTDB_URI at runtime; do not write the URI into any file or log.'
- **When:** 2026-11-25T14:51:09+00:00

## D004 (build): I chose not to provision Azure resources and to use the existing cluster referenced by DOCUMENTDB_URI.

- **Instead of:** Provision new DocumentDB cluster via az/ARM/Bicep/Terraform; Do not provision and use existing cluster from DOCUMENTDB_URI
- **Because:** Policy forbids provisioning; sample should run against the provided cluster and include IaC as optional files only.
- **Reason came from:** `model_default`
- **Evidence:** Run policy: 'Azure resource changes allowed: False.'
- **When:** 2026-11-25T14:51:12+00:00

## D005 (build): I chose to create a unique index on customerId in the sample's seed/initialization code and schema.

- **Instead of:** No index creation; Create a unique index on customerId during seed/initialization
- **Because:** A unique index ensures efficient upserts and enforces identity resolution by customerId as requested.
- **Reason came from:** `readiness_report`
- **Evidence:** Guidance: 'Create a unique index on the stable customerId (e.g., db.customers.createIndex({ customerId: 1 }, { unique: true })) during the sample seed/initialization'.
- **When:** 2026-11-25T14:51:14+00:00

## D006 (build): I chose a canonical profile document with nested sub-documents per source system (fields: sources.crm, sources.ecommerce, sources.support).

- **Instead of:** Single flat document merging all attributes; Canonical profile with nested sub-documents per source system
- **Because:** This directly follows the prompt and makes it clear where each source's attributes are stored and merged.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'model nested sub-documents for each source system's attributes, merging with $set to avoid overwriting unrelated fields.'
- **When:** 2026-11-25T14:51:26+00:00

## D007 (build): I chose to implement idempotent upserts using updateOne with $set on the nested 'sources.<source>' path and upsert:true.

- **Instead of:** Replace whole document on each event; Use updateOne/findOneAndUpdate with $set on nested source path and upsert:true
- **Because:** This avoids overwriting unrelated fields and supports merging per-source attributes as requested.
- **Reason came from:** `readiness_report`
- **Evidence:** Guidance: 'Implement idempotent upserts using findOneAndUpdate/updateOne with { upsert: true } and $set on nested source sub-document paths.'
- **When:** 2026-11-25T14:51:29+00:00

## D008 (build): I chose Mongoose 7.x (package.json pins ^7.6.1).

- **Instead of:** Mongoose 6.x; Mongoose 7.x
- **Because:** Mongoose 7.x is compatible with Node 24 and supports MongoDB 7.0 driver features; it's the current major Mongoose line.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt review: 'Use a recent stable Mongoose compatible with Node 24 (e.g. latest 7.x release)'.
- **When:** 2026-11-25T14:52:08+00:00

## D009 (build): I chose to detect an existing conflicting index and skip creating the unique index to avoid destructive changes to the customer's cluster.

- **Instead of:** Attempt to drop existing conflicting index and recreate unique index; Detect conflict and skip creating unique index to avoid destructive changes
- **Because:** We must not drop or alter existing indexes on a live cluster without operator approval; skipping creation preserves safety while letting the sample continue to function. The sample will still perform upserts using filter and upsert:true; the unique index is recommended but optional if already present in a different spec.
- **Reason came from:** `tool_result`
- **Evidence:** Seed run error: MongoServerError IndexKeySpecsConflict when attempting to create unique index that conflicts with existing index.
- **When:** 2026-11-25T14:52:22+00:00
