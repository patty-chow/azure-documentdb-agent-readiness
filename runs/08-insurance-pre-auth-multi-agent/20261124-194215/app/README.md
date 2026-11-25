# DocumentDB Pre-auth Multi-Agent Sample

Overview

This sample demonstrates a small Node.js multi-agent workflow that reads a pre-authorization request from an Azure DocumentDB (MongoDB-compatible) cluster, runs a medical-review agent to assess clinical necessity against stored criteria, and then runs an insurer-communications agent to draft a submission letter. The final submission document and updated status are stored back in DocumentDB.

Prerequisites

- Node.js 24 (installed). The workspace was built to run on Node 24.
- An Azure DocumentDB cluster reachable from your machine. Set the connection string in DOCUMENTDB_URI.
- (Optional) OpenAI API key in OPENAI_API_KEY to enable LLM-powered agents. Without it, the agents use deterministic fallbacks.

Setup

1. Install dependencies:

   npm install

2. Copy .env.example to .env and fill in DOCUMENTDB_URI (and OPENAI_API_KEY if you want LLMs).

3. Seed sample data into the configured database:

   npm run seed

This will create three collections in the database `sample_healthcare_08` (or the DB name set in DOCUMENTDB_DB): `preauth_requests`, `clinical_criteria`, and `submissions`.

Run

- CLI: process a specific preauth by id

  node src/run-orchestrator.js --id=preauth-1

- Demo HTTP endpoint (for quick testing):

  node src/server.js
  POST http://localhost:3000/preauth/preauth-1/process

What the sample shows

- Uses a singleton MongoClient (see src/db.js).
- Deterministic fallback logic for medical review when no OPENAI_API_KEY is provided.
- How to persist a generated submission document back to DocumentDB.

Security & PHI note

This sample includes only synthetic, non-PHI sample data. Do not run with real PHI unless you ensure compliance with applicable policies and secure your secrets. Never commit DOCUMENTDB_URI or OPENAI_API_KEY to source control.

Testing

The repository includes basic Jest tests that mock the database and agents so they can run without a live cluster:

npm test

Cleanup

Remove seeded data manually via the Azure Portal, az CLI, or a Mongo client if desired. The sample does not automatically delete data.
