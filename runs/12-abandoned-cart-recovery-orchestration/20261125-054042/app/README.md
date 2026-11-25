# Abandoned Cart Recovery - DocumentDB + LangChain Sample

What this sample shows
- Connect to an Azure DocumentDB (MongoDB-compatible) cluster using the official mongodb driver.
- Seed a small set of customers and shopping carts (idempotent seed script).
- Find carts abandoned for more than 2 hours.
- Use LangChain + OpenAI to generate a personalized recovery message per cart (copy agent).
- Dispatch via a channel agent that either simulates sending or uses SendGrid/Twilio if credentials are provided.
- Log each attempt/result back to DocumentDB.

Prerequisites
- Node.js 24+ installed.
- A reachable Azure DocumentDB cluster and its connection string set in DOCUMENTDB_URI env.
- (Optional) OPENAI_API_KEY to run the copy-generation agent.
- (Optional) SENDGRID_API_KEY / TWILIO_* to perform real sends; otherwise the sample simulates sending.

Quickstart
1. Install deps: npm install
2. Copy .env.example to .env and set DOCUMENTDB_URI and other optional keys.
3. Seed sample data: npm run seed
4. Run once: npm start

Files of interest
- src/seed.js  - idempotent sample-data loader
- src/run.js   - one-shot pipeline: query, generate, send, log
- src/db.js    - MongoDB client singleton
- src/copyAgent.js - LangChain/OpenAI wrapper to produce personalized copy
- src/channelAgent.js - pluggable send adapters (simulated, SendGrid, Twilio)

Testing
- Tests mock MongoDB and OpenAI calls so they run without a live cluster: npm test

Cleanup
- Manually remove the `sample_retail_12` database or use MongoDB tooling. The seed script will not delete data automatically.

Security
- Do not commit your .env with secrets. Secrets are read from environment variables at runtime.
