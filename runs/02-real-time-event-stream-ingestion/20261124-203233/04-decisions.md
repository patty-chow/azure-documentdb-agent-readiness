# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 3 |
| model_default | 2 |
| skill | 2 |
| operator | 1 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T11:06:07+00:00

## D002 (build): I chose Node.js with Express (Node 24) for the sample service implementation.

- **Instead of:** Python/Flask; Go; Node.js/Express
- **Because:** Prompt explicitly requests Node.js; Express is a small, common HTTP framework for such samples.
- **Reason came from:** `prompt`
- **Evidence:** Sample prompt: 'Using the DocumentDB skill, build a Node.js event ingestion service'
- **When:** 2026-11-25T11:06:26+00:00

## D003 (build): I chose the official npm 'mongodb' driver version ^5.10.0.

- **Instead of:** mongodb@4.x; mongodb@5.x; mongodb@6.x
- **Because:** Driver v5.x is stable, supports MongoDB 7 features used (bulkWrite, change streams), and is compatible with Node 24; exact recommended version was not provided in docs so I used a conservative recent 5.x pin.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Use the official npm 'mongodb' driver (current stable compatible with MongoDB 7.0 and Node.js 24)'. No single pinned version in docs, so I pick a recent 5.x release known to support change streams and bulkWrite.
- **When:** 2026-11-25T11:06:29+00:00

## D004 (build): I chose to read the cluster connection string from the DOCUMENTDB_URI environment variable at runtime.

- **Instead of:** Read secrets from code; Read from environment variables; Read from a mounted secret store
- **Because:** Matches guidance and safe-practice requirement not to embed secrets; environment variables are simple for samples.
- **Reason came from:** `skill`
- **Evidence:** Readiness guidance: 'Read the cluster connection string from DOCUMENTDB_URI (env) and connect with the official MongoDB Node.js driver; do not log secrets.'
- **When:** 2026-11-25T11:06:33+00:00

## D005 (build): I chose to use the existing pre-provisioned cluster pointed to by DOCUMENTDB_URI and not provision any Azure resources.

- **Instead of:** Provision a new cluster via CLI/Bicep; Provision via Terraform; Use existing pre-provisioned cluster
- **Because:** Sample environment already provides a reachable cluster; provisioning is disallowed by policy. Create only code and index resources on that cluster.
- **Reason came from:** `prompt`
- **Evidence:** Run environment skill_md: 'A vector-capable Azure DocumentDB cluster ... connection string is in the environment variable DOCUMENTDB_URI.' Also run_policy: 'Azure resource changes allowed: False.'
- **When:** 2026-11-25T11:06:36+00:00

## D006 (build): I chose unordered bulkWrite with insertOne operations for the ingestion path and will rely on the compound unique index for deduplication; the seed script will use upsert to be idempotent.

- **Instead of:** Use ordered bulkWrite; Use unordered bulkWrite with insert ops; Use upsert (updateOne upsert) in bulk
- **Because:** Unordered insert bulkWrite maximizes throughput and, when combined with unique index, will reject duplicates but allow other writes to succeed. Seed uses upserts to allow repeated runs without duplicates for demo verification.
- **Reason came from:** `prompt`
- **Evidence:** Prompt: 'bulk-writes them to DocumentDB using unordered bulk operations for throughput. Use a composite unique index on (customerId, eventId) for deduplication.' Assumption: seed uses upserts for idempotency.
- **When:** 2026-11-25T11:06:40+00:00

## D007 (build): I chose to create the compound unique index exactly as: { customerId: 1, eventId: 1 } with name 'customer_event_unique'.

- **Instead of:** Compound unique index on (eventId, customerId) ascending; Compound unique index on (customerId, eventId) ascending
- **Because:** Follows explicit guidance from documentdb-indexing skill guidance in the readiness report.
- **Reason came from:** `skill`
- **Evidence:** Readiness guidance: 'Create the compound unique index exactly as: db.events.createIndex({ customerId: 1, eventId: 1 }, { unique: true, name: 'customer_event_unique' })'
- **When:** 2026-11-25T11:06:43+00:00

## D008 (build): I chose a default unordered-bulk batch size of 1000, configurable via EVENTS_BATCH_SIZE env var.

- **Instead of:** Batch size 25,000; Batch size 5000; Batch size 1000 (default)
- **Because:** 1000 balances throughput vs memory and is a reasonable default for a sample; exposing env var lets users tune it for their cluster tier (e.g., M30).
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'tune batch size for memory and latency rather than exceeding the documented batch limit (max 25,000)'; no prescriptive default provided, so pick a conservative default.
- **When:** 2026-11-25T11:06:46+00:00

## D009 (build): I chose to change the driver dependency to mongodb@^5.9.0 because npm install failed for ^5.10.0 (no matching version).

- **Instead of:** Keep mongodb@^5.10.0 despite install error; Pick a different 5.x version
- **Because:** Installer failure forced a different available version; 5.9.x is a conservative 5.x choice likely to support change streams and bulkWrite.
- **Reason came from:** `tool_result`
- **Evidence:** npm error: 'No matching version found for mongodb@^5.10.0.'
- **When:** 2026-11-25T11:07:42+00:00
