Azure DocumentDB Medication Interaction Checker

This sample demonstrates a Node.js + Mongoose app that stores a small medication interaction knowledge base in Azure DocumentDB and uses a LangChain-powered LLM call to assess and rank interactions for a provided medication list.

NOT FOR CLINICAL USE: This is a demo sample only and must not be used for medical decision making.

Prerequisites
- Node.js 24+
- A reachable Azure DocumentDB cluster. The connection string must be set in DOCUMENTDB_URI in .env.
- (Optional) OPENAI_API_KEY if you want the LangChain LLM to run. If missing, the app will fall back to simple heuristics.

Setup
1. npm install
2. cp .env.example .env and set DOCUMENTDB_URI and OPENAI_API_KEY (if available)
3. npm run seed
4. npm start

Usage
- POST /check-interactions
  Payload: { "medications": ["aspirin", "ibuprofen"] }
  Returns: JSON array of interaction objects ranked by severity.

CLI
- npm run check will run a small CLI example that calls the same logic.

Cleanup
- Remove sample data by dropping the `interactions` collection in the `sample_healthcare_03` database using your preferred MongoDB tool.

Files
- src/: application source
- scripts/seed.js: idempotent upsert seed script
- scripts/check_sample.js: CLI runner that calls the API logic directly
- .env.example: placeholder environment variables

Security
- Do not commit secrets. The app reads DOCUMENTDB_URI and OPENAI_API_KEY from environment variables.

Notes
- The app uses a `normalizedPair` field (sorted drug names joined with '|') and an index on that field for efficient pair lookups.
