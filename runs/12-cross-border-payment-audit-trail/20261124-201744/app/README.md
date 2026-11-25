# DocumentDB Audit Trail Sample (Node.js + Mongoose)

This sample demonstrates an immutable audit trail pattern: the application writes one immutable document per stage of a cross-border payment lifecycle (initiated, routed, fx_converted, settled) into Azure DocumentDB (MongoDB-compatible). It also exposes an aggregation that reconstructs the chronologically-ordered timeline for a payment.

Prerequisites
- Node.js 24 (available in the run environment)
- A reachable Azure DocumentDB cluster. Put its connection string in DOCUMENTDB_URI in a local `.env` file (see `.env.example`). The run environment already provides DOCUMENTDB_URI.

What this sample shows
- A Mongoose schema and application-layer guards that prevent updates (pre-hooks reject update/replace/save on existing documents)
- A compound index { paymentReference: 1, stageTimestamp: 1 } for efficient timeline reconstruction
- Seed script to insert idempotent sample events
- A small Express API that accepts new audit events and exposes a timeline endpoint

Setup
1. Copy `.env.example` -> `.env` and set DOCUMENTDB_URI to your cluster connection string.
2. npm install
3. (Optional) Create the compound index; the sample will create it if missing via Mongoose, but the included verification script uses the documentdb MCP server.

Commands
- npm run seed     # inserts sample events (idempotent)
- npm run timeline # runs the timeline aggregation for PAY-1001 and prints results
- npm start        # runs the Express server (POST /audit, GET /timeline/:paymentReference)

Security
- This sample reads the connection string from an environment variable. Do not commit secrets. See `.env.example`.

Cleaning up
- Remove documents from the `sample_banking_12.audit_events` collection using your tooling (mongosh, Azure portal, or the documentdb MCP server). This sample does not provision resources.

Guidance
- The compound index { paymentReference: 1, stageTimestamp: 1 } is recommended for equality+sort patterns. The readiness report and the documentdb-indexing skill recommend creating and verifying this index before running the timeline aggregation.

Limitations
- This is a small demo. For production you'll want network-level restrictions (private endpoints), RBAC, and additional validation.
