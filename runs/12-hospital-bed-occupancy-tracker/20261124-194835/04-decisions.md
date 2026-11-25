# Decision log

| Reason came from | Decisions |
|---|---|
| readiness_report | 4 |
| prompt | 2 |
| operator | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T08:39:35+00:00

## D002 (build): I chose Node.js with Mongoose 7.x

- **Instead of:** Python/Flask with PyMongo; Node.js with native MongoDB driver; Node.js with Mongoose ORM
- **Because:** Mongoose aligns with the prompt, provides schema modeling for sample app, and is recommended in the readiness guidance for Node.js/DocumentDB.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "Builder will pick a modern Mongoose 7.x compatible with Node 24" and readiness guidance: "Use standard MongoDB drivers (Mongoose) to access the cluster".
- **When:** 2026-11-25T08:39:51+00:00

## D003 (build): I chose to set tls=true, authMechanism=SCRAM-SHA-256, and retryWrites=false in the MongoDB connection options (passed via connection string or mongoose options)

- **Instead of:** Use plain connection string without TLS/auth tuning; Set tls=true, authMechanism=SCRAM-SHA-256, retryWrites=false
- **Because:** These options are recommended for Azure DocumentDB compatibility and to avoid retryWrites issues on server-managed clusters.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report guidance: "set tls=true, authMechanism=SCRAM-SHA-256, and retryWrites=false; follow the singleton MongoClient pattern".
- **When:** 2026-11-25T08:40:05+00:00

## D004 (build): I chose not to provision any Azure resources and to use the existing cluster referenced by DOCUMENTDB_URI

- **Instead of:** Provision resources via az/Bicep/terraform; Do not provision resources (use existing cluster)
- **Because:** The environment already provides a live cluster; run policy disallows provisioning; sample should target that cluster.
- **Reason came from:** `readiness_report`
- **Evidence:** Run environment: "a Azure DocumentDB cluster is already provisioned and reachable... DOCUMENTDB_URI" and run policy forbids Azure resource changes.
- **When:** 2026-11-25T08:40:09+00:00

## D005 (build): I chose to maintain a separate ward summary collection with documents like { wardId, counts: { occupied, available, cleaning }, capacity } updated atomically via $inc upsert

- **Instead of:** Embed ward summary inside ward document; Maintain a separate ward summary collection with per-ward counters
- **Because:** Separate summary collection allows atomic counter updates via $inc and efficient reads for dashboards without aggregating live bed collection on every request.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: "summary docs like { wardId, counts... }" and readiness guidance: "Implement per-ward summary updates using atomic updateOne with $inc and upsert:true".
- **When:** 2026-11-25T08:40:12+00:00

## D006 (build): I chose to use a TTL index on a Date field cleaningExpiresAt with expireAfterSeconds set to 0 (so documents expire at that instant) and set that field when entering 'cleaning'

- **Instead of:** Expire cleaning state by background job; Use TTL index on a Date field like cleaningExpiresAt with expireAfterSeconds:0
- **Because:** TTL index is supported and simpler than a job; aligns with guidance and simplifies demo of automatic expiry.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report guidance: "Expire cleaning-state documents with a TTL index on a Date field (e.g., createIndex({ cleaningExpiresAt: 1 }, { expireAfterSeconds: 0 }))".
- **When:** 2026-11-25T08:40:16+00:00

## D007 (build): I chose to perform a live TTL test by setting a small TTL on a bed (5s) and polling to observe whether the document is removed, to validate TTL semantics on the target cluster.

- **Instead of:** Rely on index metadata for TTL correctness; Perform a live short TTL test by setting a small TTL and observing deletion
- **Because:** Index metadata shows expireAfterSeconds, but practical behavior (when deletions occur) can vary; a live check confirms TTL semantics on this cluster.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report instruction: "validate expiry on the target cluster before relying on deletion timing."
- **When:** 2026-11-25T08:42:03+00:00
