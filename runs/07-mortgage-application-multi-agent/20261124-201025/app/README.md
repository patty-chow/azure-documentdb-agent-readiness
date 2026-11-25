DocumentDB Mortgage Multi-Agent Sample

What this sample shows
- A minimal Node.js Express app that implements a LangChain-style multi-agent mortgage pipeline:
  - Orchestrator reads an application from Azure DocumentDB
  - Underwriting agent assesses affordability (simple rule-based logic; falls back to LLM if configured)
  - Compliance agent checks regulatory requirements (simple checks; LLM optional)
  - Comms agent drafts the decision letter (template-based; LLM optional)
  - The decision is written to the `decisions` collection in the `sample_banking_07` database

Prerequisites
- Node.js 24+, npm
- An Azure DocumentDB cluster reachable from this machine. Set DOCUMENTDB_URI in .env (SRV or standard connection string, include tls=true)
- Optional: OpenAI API key in OPENAI_API_KEY to enable real LLM-based agents. If not present, the sample uses deterministic rule-based agents.

Setup
1. cp .env.example .env and fill DOCUMENTDB_URI (and OPENAI_API_KEY if you want real LLM calls)
2. npm install

Seed sample data
- npm run seed
  This upserts a few sample mortgage applications into the `applications` collection in database `sample_banking_07`.

Run the pipeline
- Start the server: npm start
- Trigger a run via HTTP: POST http://localhost:3000/run/<applicationId>
  Or run once: npm run run-app -- <applicationId>

API surface
- POST /seed -> runs the seeder
- POST /run/:applicationId -> runs the multi-agent pipeline for the given application
- GET /applications/:id -> fetches application and any decision

Testing
- npm test
  Tests mock the DB and the LLM so they run without live credentials.

Cleanup
- Delete documents from the sample_banking_07 database or drop the database with your preferred admin tool. Do not run Azure resource deletion.

Notes
- This sample reads the connection string from DOCUMENTDB_URI and never writes secrets to disk.
- Indexes: the seed script creates applicationId and credit_score indexes appropriate for demo queries. Vector-index creation is documented but left as a manual step because it depends on the embedding model and cluster capabilities.
