DocumentDB Lead Scoring Agent (sample)

This sample demonstrates a Node.js LangChain-style agent that:
- Fetches a lead's activities, firmographics, and engagement signals from an Azure DocumentDB (MongoDB-compatible) cluster
- Uses an LLM to reason over the signals and assign a score (0-100) with a one-paragraph rationale
- Writes the score and rationale back to the leads collection

Prerequisites
- Node.js 24+ and npm
- A reachable Azure DocumentDB cluster (mongoClusters) and its MongoDB connection string in DOCUMENTDB_URI
- OpenAI API key in OPENAI_API_KEY (or change the code to use another LLM provider)

Quickstart
1. Copy .env.example to .env and fill in DOCUMENTDB_URI and OPENAI_API_KEY
2. npm install
3. npm run seed    # idempotent seed data and indexes
4. npm run score   # runs scorer CLI for lead-1
5. npm start       # start HTTP API on port 3000

API
POST /score-lead
Body: { "leadId": "lead-1" }
Response: { score: 0-100, rationale: "one paragraph" }

Design notes
- Uses a singleton MongoClient per documentdb-driver guidance
- Avoids vector indexes/embeddings for simplicity; reasoning happens in the LLM
- Database: sample_customer_360_09; collections: leads, activities, companies, engagement_signals

Cleanup
- Remove sample documents from the cluster or drop the database using your usual tools.

Security
- Never commit secrets. Use .env for local development and secret stores in production.
