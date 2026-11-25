Invoice reconciliation sample for Azure DocumentDB

What this sample shows
- Connect to an Azure DocumentDB cluster (MongoDB-compatible) via Mongoose using DOCUMENTDB_URI from the environment.
- Seed a sample database with PurchaseOrder and Invoice documents.
- Run a one-shot reconciliation that: finds unmatched invoices, extracts structured fields (vendor, amount) using an LLM if configured or a fallback parser, searches for candidate POs by vendor and amount, scores candidates, and writes match results back to the invoices.
- A minimal Express HTTP surface exposes endpoints to trigger reconciliation and submit manual corrections that the in-process agent memory learns from within the session.

Prerequisites
- Node.js 24+ and npm
- A reachable Azure DocumentDB cluster. Put its connection string into DOCUMENTDB_URI.
- (Optional) An OpenAI API key in OPENAI_API_KEY to enable LLM-based extraction and embeddings. If not provided, the sample uses deterministic fallback extraction.

Quickstart
1. Install dependencies:
   npm install
2. Copy .env.example to .env and edit values.
3. Seed the database with sample data:
   npm run seed
4. Run the server (starts Express API):
   npm start
5. Or run a one-shot reconciliation from CLI:
   npm run reconcile

API
- POST /reconcile/run — trigger reconciliation immediately (returns results)
- POST /reconcile/manual-correction — body: { invoiceId, matchedPoId } — apply a manual correction and store it in session memory
- GET /reconcile/status — return last run summary and agent session corrections

Security
- Never commit secrets. Use .env or environment variables. This sample reads DOCUMENTDB_URI and OPENAI_API_KEY from the environment at runtime.

Notes and limitations
- Agent memory is ephemeral (in-process) and lasts only while the Node.js process runs.
- This sample intentionally avoids provisioning Azure resources; it expects DOCUMENTDB_URI to point to an existing cluster.

Files created
- src/: application source
- .env.example, README.md, package.json

