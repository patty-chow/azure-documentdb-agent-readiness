Abandoned Cart Orchestrator (DocumentDB sample)

What this sample shows
- Connects to an Azure DocumentDB (MongoDB-compatible) cluster using the official mongodb driver.
- Seeds a small 'customers' and 'carts' dataset into database sample_retail_12.
- Runs a CLI orchestrator that finds carts abandoned > 2 hours and not yet processed, generates a personalized recovery message using OpenAI, and hands off to channel stubs (email or SMS) based on customer preference.
- Logs outcomes back to the cart document (deliveryLog) and marks carts processed.

Prerequisites
- Node.js >= 24
- An Azure DocumentDB connection string in environment variable DOCUMENTDB_URI (the run environment already provides this). Do NOT commit secrets.
- An OpenAI API key in OPENAI_API_KEY to enable message generation; the sample can run without it but will skip LLM generation.

Quickstart
1. Copy .env.example to .env and fill in DOCUMENTDB_URI and OPENAI_API_KEY (if you want real LLM output).
2. npm install
3. npm run seed    # idempotent: upserts sample customers and carts into sample_retail_12
4. npm start       # runs the orchestrator that processes pending carts once

Files
- src/db.js           MongoDB client singleton and index-creation helper
- src/seed.js         Idempotent data seeding (customers and carts)
- src/index.js        Orchestrator entrypoint: find abandoned carts, generate message, send via channel stub, update deliveryLog
- src/agents/copyGenerator.js  Uses OpenAI SDK to produce a personalized message (LLM can be disabled)
- src/agents/channelAgent.js    sendEmail/sendSMS stubs and delivery logging

Notes
- This sample uses simple stubs for sending messages. Replace channelAgent with real SendGrid/Twilio integration for production.
- Indexing: the seed step creates a compound index on { customerId:1, updatedAt:1, processedAt:1 } and a sparse index on processedAt to optimize the abandonment query.

Clean up
- The sample writes into the sample_retail_12 database. To remove sample data, drop the customers and carts collections manually or drop the database.

Limitations
- This is a minimal sample intended for learning orchestration and the DocumentDB driver patterns; it is not production-ready.
