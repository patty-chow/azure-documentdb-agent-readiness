Abandoned Cart Recovery Orchestration — DocumentDB sample

What this sample shows
- A Node.js LangChain orchestration pipeline that:
  - Finds carts in Azure DocumentDB (MongoDB-compatible) abandoned for more than 2 hours
  - Uses a copy-generation agent (LangChain + OpenAI) to create a personalised recovery message per cart
  - Uses a channel agent to send the message via email or SMS (simulated in the sample)
  - Logs the send outcome back to DocumentDB in a `recovery_logs` collection

Prerequisites
- Node.js 24+ (available on the build host)
- An accessible Azure DocumentDB cluster (the environment this sample was built with already has one). Obtain the connection string and set it in DOCUMENTDB_URI.
- (Optional) OpenAI API key if you want real LLM-generated messages. Set OPENAI_API_KEY.

Security
- Never commit secrets. Use .env (gitignored) and fill values from .env.example.

Setup
1. Copy .env.example to .env and fill DOCUMENTDB_URI and optionally OPENAI_API_KEY
2. npm install
3. npm run seed  # idempotent seed that inserts sample customers and carts
4. npm start     # runs the pipeline once

Notes
- The sample simulates email/SMS sends. It prints send activity to stdout and writes a log document to the `recovery_logs` collection.
- The sample uses the `sample_retail_12` database and will not touch other databases.

How it works
- src/db.js: singleton MongoClient following documentdb-driver/documentdb-connection guidance
- src/seed.js: idempotent data loader (customers & carts)
- src/run.js: pipeline that queries carts older than 2 hours, generates messages via LangChain/OpenAI, calls channel agent, and writes logs
- src/agents/copyAgent.js: LangChain + OpenAI wrapper (keeps prompts simple for sample clarity)
- src/agents/channelAgent.js: simulated send adapter; shows where to wire Twilio/SendGrid

Testing
- Unit tests use Jest and are designed to run without a live cluster. Run `npm test`.

Cleanup
- Remove sample documents by deleting records where `sample: 'abandoned-cart-sample-12'` in customers and carts, and optionally drop `recovery_logs`.

Limitations & extensions
- This sample intentionally simulates sending. To integrate a real provider, modify src/agents/channelAgent.js to use Twilio (SMS) or SendGrid (email) SDKs and provide credentials via env.
- For production, add retries, idempotency markers on logs to avoid duplicate sends, and observability/metrics.
